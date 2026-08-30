"""Source fingerprints: what code produced this artifact.

Lifted out of `design/methodology/experiments/harmonic-zero-null/harness_rules.py`,
where it was written and where it worked -- on nine of the repository's nineteen
result artifacts. The other ten wrote their JSON with a bare `write_text` and
carried no fingerprint at all, so nothing could date them against the code in
either direction. That is not a smaller version of the same guarantee; it is no
guarantee, and it reads identical to a green one. The machinery was never
harmonic-zero-null-specific -- it hashes source, not probes -- so it lives here,
beside the rest of the shared layer every experiment already imports.

WHY NOT HASH THE FILE. Any edit then invalidates every result, comments included.
That is a permanently-red guard, and a guard nobody can satisfy is one that gets
switched off, taking the genuine flags with it. So the fingerprint is per ENTRY
POINT and blind to anything that does not change meaning.

WHAT IT COVERS. The entry's own body, plus the transitive closure of module-level
functions it calls and module-level constants it reads, plus every module-level
name of any SIBLING module -- one imported from the same directory. Comments never
reach the AST; docstrings are stripped explicitly; positions are excluded, so
reindenting or rewrapping changes nothing.

WHAT IT DOES NOT COVER, stated rather than solved. Dynamic calls (getattr, a name
resolved at run time) are invisible to a static walk. A THIRD-PARTY or cross-tree
module -- numpy, scipy, hodge, rig.flows -- is out of scope: this answers "did OUR
code change", not "did the world". And a semantically neutral refactor, extracting
a helper without altering behaviour, WILL move the fingerprint. That direction is
the safe one: it costs a re-run nobody needed rather than hiding one that was.

STALE BYTECODE IS THE ONE THAT BITES SILENTLY, and it is worth spelling out
because it defeats this whole mechanism in the wrong direction. `inspect.getsource`
reads the .py; the interpreter may be running a .pyc. Python invalidates a cache
on (mtime, size), so a script that rewrites a file and restores it WITHIN ONE
SECOND, changing no byte count, leaves a stale .pyc that Python accepts as valid.
Observed here, not imagined: a check that flipped `SEPARATED = 14.0` to `13.0`
and back -- same length, same second -- left the 13.0 bytecode live, and a full
probe re-run silently measured a separation cut the repository does not contain.
Every recorded fingerprint agreed with its source the whole time, because the
source was never wrong; only the bytecode was.

So the fingerprint answers "has the SOURCE changed meaning", never "is the source
what actually ran". Nothing here can close that -- the gap is between the file and
the interpreter, below where this module looks. The defence is operational: run
regenerations with PYTHONDONTWRITEBYTECODE=1, or clear __pycache__ after any
scripted edit to a module a run will import.

TWO GRANULARITIES, and the choice is about what the artifact is.

    semantic_fingerprint(module, entry)  -- one artifact per entry point, so a
        change to probe A does not invalidate probe B's result. Use it wherever
        the writer loops over named probes.
    module_fingerprint(module)           -- one artifact from the whole module,
        with no single entry to narrow to. `evidence.json` is the case: six
        functions contribute claims to one file.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import os
import textwrap
import types

# The key an artifact carries its fingerprint under. Writers record it; readers
# only read it. Nested under `value` where the artifact has one (the probe record
# shape), at top level otherwise -- see `stamp`.
FINGERPRINT_KEY = "source_fingerprint"


def _strip_docstrings(tree):
    """Docstrings reach the AST as Expr nodes; comments never do. Drop them so
    documenting a probe does not invalidate its results."""
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
            continue
        body = getattr(node, "body", None)
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            node.body = body[1:] or [ast.Pass()]
    return tree


def _normalised_dump(source):
    tree = _strip_docstrings(ast.parse(textwrap.dedent(source)))
    # include_attributes=False drops lineno/col_offset, so moving code or
    # rewrapping a line is not a change.
    return ast.dump(tree, annotate_fields=True, include_attributes=False)


def _module_level(module):
    """{name: source} for module-level functions and simple constant bindings."""
    try:
        tree = ast.parse(inspect.getsource(module))
    except (OSError, TypeError):
        return {}
    out = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = ast.dump(_strip_docstrings(node),
                                      annotate_fields=True, include_attributes=False)
        elif isinstance(node, ast.Assign):
            dump = ast.dump(node, annotate_fields=True, include_attributes=False)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    out[target.id] = dump
                elif isinstance(target, ast.Tuple):
                    for elt in target.elts:
                        if isinstance(elt, ast.Name):
                            out[elt.id] = dump
    return out


def _referenced(dump_text, known):
    return {n for n in known if f"id='{n}'" in dump_text or f"name='{n}'" in dump_text}


def _sibling_modules(module):
    """{local alias: module} for modules `module` imports from its OWN directory.

    numpy, scipy and hodge are the world: out of scope by design, and hashing
    them would turn the fingerprint into a version stamp that any upgrade
    invalidates. A module in the same directory is not the world. It is written
    and edited alongside this one, and its constants can decide the result --
    score_test.py's ETA_CLIP and SEPARATED decide which draws every harmonic-zero
    probe keeps, so editing it invalidated all nine results while every rule
    reported clean. `_module_level` walks tree.body for FunctionDef and Assign
    and has no branch for Import, so an imported name could never enter a closure
    by reference-following; siblings have to be added deliberately.

    Keyed by the LOCAL ALIAS (`st`, not `score_test`) because that is the name a
    body actually references, and reachability is decided on the alias -- see
    `_sibling_parts`.
    """
    f0 = getattr(module, "__file__", "") or ""
    if not f0:
        return {}
    here = os.path.dirname(os.path.abspath(f0))
    out = {}
    for alias, obj in vars(module).items():
        if not isinstance(obj, types.ModuleType) or obj is module:
            continue
        f = getattr(obj, "__file__", None)
        if f and os.path.dirname(os.path.abspath(f)) == here:
            out[alias] = obj
    return out


def _sibling_parts(module, reached=None):
    """Sibling source, entered WHOLE -- but only for siblings the entry can reach.

    Whole, because there is no closure to narrow a sibling to: a constant like
    SEPARATED is read inside the sibling's own functions, never from the entry
    body, so reference-following from the entry would never find it.

    Only the reachable ones, because otherwise a module that produces no numbers
    re-stamps every artifact beside it. `probes.py` imports both `score_test` and
    `harness_rules` from its directory. `score_test` is called by the probe
    bodies and decides the measurements. `harness_rules` is touched only by the
    __main__ writer -- it is the rule, not the experiment -- so editing a rule
    would have invalidated nine results that no rule change can alter. That is
    the false-positive direction, and a guard that cries wolf is one that gets
    switched off.

    `reached` is the set of names in the entry's closure. None means "no entry to
    narrow by" (module_fingerprint), and then every sibling counts.
    """
    parts = []
    for alias, sib in sorted(_sibling_modules(module).items()):
        if reached is not None and alias not in reached:
            continue
        lv = _module_level(sib)
        # Keyed by module __name__, not by the alias: the identity of the code is
        # what is being hashed, and renaming an import already moves the
        # referencing body's own dump.
        parts += [f"{sib.__name__}.{n}::{lv[n]}" for n in sorted(lv)]
    return parts


def _digest(parts):
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[:16]


def semantic_fingerprint(module, entry, _max_depth=12):
    """A hash of `entry` and everything in this module it transitively depends on.

    Stable across comments, docstrings, blank lines and reindentation. Changes
    when any body or constant in the closure changes meaning. Returns None when
    the module has no module-level definition by that name.
    """
    level = _module_level(module)
    if entry not in level:
        return None
    aliases = set(_sibling_modules(module))
    known = set(level) | aliases          # a sibling alias is not a module-level
    seen, frontier = set(), {entry}       # binding, so add it to what counts as
    reached = set()                       # referenced
    for _ in range(_max_depth):
        new = set()
        for name in sorted(frontier):
            if name in seen or name in aliases:
                reached.add(name) if name in aliases else None
                continue
            seen.add(name)
            hits = _referenced(level[name], known) - seen
            reached |= hits & aliases
            new |= hits - aliases
        if not new:
            break
        frontier = new
    return _digest([f"{n}::{level[n]}" for n in sorted(seen)]
                   + _sibling_parts(module, reached))


def module_fingerprint(module):
    """A hash of EVERY module-level definition, plus siblings.

    For an artifact the whole module produces, where no single entry point owns
    it. Coarser than `semantic_fingerprint` on purpose: any change anywhere in
    the module re-stamps the artifact, which is the correct reading when the
    artifact is the module's collected output.
    """
    level = _module_level(module)
    return _digest([f"{n}::{level[n]}" for n in sorted(level)] + _sibling_parts(module))


# The three shapes artifacts in this repo actually have, in the order `stamp`
# and `recorded_fingerprint` consider them. Writer and reader share this list so
# a fingerprint cannot be written somewhere the reader does not look -- which is
# how evidence.json first came back reading "unfingerprinted" while carrying one.
#
#   value  the probe-record shape: {probe, question, verdict, value: {...}}
#   meta   the registry shape: evidence.json keeps provenance in `meta`, beside
#          commit, numpy and python, and that is where it belongs
#   top    a plain results dict, which should not have to invent a wrapper
_SHAPES = ("value", "meta")


def stamp(artifact, module, entry=None):
    """Record the fingerprint into `artifact`, and return it.

    One line at every writer, so a new result cannot be added unfingerprinted by
    forgetting a step -- and so the reader below always knows where to look.
    """
    fp = module_fingerprint(module) if entry is None else semantic_fingerprint(module, entry)
    for shape in _SHAPES:
        if isinstance(artifact.get(shape), dict):
            artifact[shape][FINGERPRINT_KEY] = fp
            return artifact
    artifact[FINGERPRINT_KEY] = fp
    return artifact


def recorded_fingerprint(artifact):
    """The fingerprint an artifact carries, wherever `stamp` put it, or None."""
    for shape in _SHAPES:
        sub = artifact.get(shape)
        if isinstance(sub, dict) and FINGERPRINT_KEY in sub:
            return sub[FINGERPRINT_KEY]
    return artifact.get(FINGERPRINT_KEY)


_ENTRY_IS_NAME = object()


def mismatch(name, artifact, module, entry=_ENTRY_IS_NAME):
    """A sentence when this artifact was produced by code that has since changed
    meaning, None when it agrees, and None when it carries no fingerprint --
    an absent one is unverifiable, not agreement, and is reported separately by
    `unfingerprinted` so it cannot be counted as passing.

    `entry` defaults to `name`, which is the probe-suite case: the artifact is
    named for the entry that produced it. Pass `entry=None` EXPLICITLY for an
    artifact stamped module-wide. The sentinel exists so that a plain `None`
    default could not silently reinterpret every existing call as module-wide --
    which would have compared each probe's stored per-entry hash against a
    whole-module one and reported all nine stale for no reason.
    """
    recorded = recorded_fingerprint(artifact)
    if recorded is None:
        return None
    if entry is _ENTRY_IS_NAME:
        entry = name
    current = (module_fingerprint(module) if entry is None
               else semantic_fingerprint(module, entry))
    if current is None:
        return (f"{name}: records a source fingerprint but the module no longer "
                f"defines an entry point by that name.")
    if recorded != current:
        return (f"{name}: produced by code that has since changed meaning "
                f"(fingerprint {recorded} -> {current}). No named constant need "
                f"have moved -- a predicate is enough. Re-run it.")
    return None


def unfingerprinted(artifacts):
    """Artifacts carrying no fingerprint: unverifiable, not agreeing."""
    return sorted(n for n, a in artifacts.items() if recorded_fingerprint(a) is None)
