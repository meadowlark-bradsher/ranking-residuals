"""Harness rules: conclusions that need seeds before they are allowed to be drawn.

THE RULE THIS EXISTS FOR. No verdict may rest on a MOMENT RATIO from a low-df
cell measured once.

It is here because the same mistake was made five times in a row, always from the
same cell. b1 = 1 is simultaneously the DECISIVE cell -- it is where the
discrimination lives, so it is the one an author reaches for -- and the NOISIEST,
because chi2(1) has excess kurtosis 12. The relative sampling s.e. on varT/2df is

    sqrt((12/df + 2) / reps)

which at df = 1, reps = 2000 is 8.4% against a 15% gate: about seven draws in a
hundred clear it with nothing wrong. At df = 22 the same figure is 3.6%, the gate
sits 4.2 s.e. out, and a valid cell essentially never fails. So a single draw from
a df = 1 cell is not evidence, and the instinct to trust the cell that
discriminates most is exactly backwards.

What that produced, in order: a b1 floor, a fold-size floor, an interaction at
saturation 0.019, a flat 0.02 window, and an any-failure count that read 6 on one
seed family and 1 on another. Two of them cleared their gate by less than a
standard error; one cleared it by 0.0002. None survived reseeding.

WHY THE RULE IS NARROW, AND DELIBERATELY SO. It binds only on moment ratios, not
on every figure a low-df cell produces. A rejection rate is a binomial proportion
with s.e. sqrt(p(1-p)/reps) -- about 0.005 at p = 0.05 -- and that does not
degrade with df at all. `curl_freedom` and `harmonic_projected_eps` reach their
verdicts on rejection rates, so they are outside this rule even though both
report df = 1 cells. Widening it to "any low-df verdict" would flag them for a
hazard they do not have, and a rule that cries wolf is one that gets suppressed.

TWO WAYS TO SATISFY IT. Carry base seeds directly (`n_base`, or `n_base_seeds`
per row), or have a companion AUDIT that reseeds the same grid. The second exists
because reseeding costs (n_base + 1) x the probe, which would take the suite from
two minutes to twenty, and a suite that costs twenty minutes stops being run.
`chi2_collapse` is covered that way by `collapse_spread`.
"""

from __future__ import annotations

# df at or below which a moment ratio needs seeds. 2 rather than 1 because
# chi2(2) still carries excess kurtosis 6, and the gate is only 2.5 s.e. out.
DF_NEEDS_SEEDS = 2

# Enough base seeds to put the s.e. of the mean below the gate at df = 1:
# 8.4% / sqrt(5) = 3.8% against 15%.
MIN_BASE_SEEDS = 5

# probe -> the audit that reseeds its grid. An audit discharges the rule for the
# probe it names, which is why AUDITS is a separate registry rather than a tag.
AUDIT_FOR = {"chi2_collapse": "collapse_spread"}

# Fields that ARE moment ratios, i.e. the quantities whose sampling error scales
# with 12/df. Matched by SHAPE, not by an enumerated list.
#
# The first version enumerated exact names and missed collapse_spread entirely:
# that probe reports ref_var_ratio, var_ratio_med, var_ratio_max and se_var_ratio
# at row level, and keeps the bare mean_ratio/var_ratio one level down inside each
# row's "draws" list. None of those matched, so low_df_moment_rows() returned zero
# for it and the rule contributed nothing. It only LOOKED like it worked because
# collapse_spread carries n_base = 10 and is discharged as seeded anyway -- a
# probe of the same shape WITHOUT seeds would have sailed through unflagged, which
# is precisely the class this rule exists to catch.
#
# So: any key whose name contains a moment ratio, or which is a mean_/var_ prefixed
# measurement. Aggregates (_med, _max, se_, ref_) come along for free.
MOMENT_SUBSTRINGS = ("mean_ratio", "var_ratio")
MOMENT_PREFIXES = ("mean_", "var_")

# Reference constants, not measurements: chi2_mean is df and chi2_var is 2*df.
# They carry no sampling error and must not put a row in scope.
NOT_MOMENTS = ("chi2_",)

# Rows sometimes nest their per-draw values in a list of dicts (collapse_spread's
# "draws", seed_spread's "per_seed"). Those inner values are the ones actually
# carrying the 12/df error, so the scan descends one level to find them.
NESTED_KEYS_MAX_DEPTH = 1


def is_moment_key(key):
    if key.startswith(NOT_MOMENTS):
        return False
    return (any(sub in key for sub in MOMENT_SUBSTRINGS)
            or key.startswith(MOMENT_PREFIXES))


def row_dfs(row):
    """Every degrees-of-freedom value a row reports, under any of its names."""
    out = []
    for key, val in row.items():
        if (key == "df" or key.endswith("_df")) and isinstance(val, int):
            out.append(val)
    return out


def carries_moments(row):
    """True when this row reports a moment ratio, at its own level or one below."""
    for key, val in row.items():
        if is_moment_key(key) and val is not None:
            return True
        if isinstance(val, list):
            for item in val:
                if isinstance(item, dict) and any(
                        is_moment_key(k) and v is not None for k, v in item.items()):
                    return True
    return False


def low_df_moment_rows(result):
    """Rows that report a moment ratio for a cell at or below DF_NEEDS_SEEDS."""
    rows = (result.get("value") or {}).get("rows") or []
    return [r for r in rows
            if carries_moments(r)
            and any(d <= DF_NEEDS_SEEDS for d in row_dfs(r))]


def is_seeded(result, min_seeds=MIN_BASE_SEEDS):
    """True when the result carries base-seed replication, per-probe or per-row."""
    value = result.get("value") or {}
    if (value.get("n_base") or 0) >= min_seeds:
        return True
    rows = value.get("rows") or []
    counts = [r.get("n_base_seeds") for r in rows if "n_base_seeds" in r]
    return bool(counts) and min(counts) >= min_seeds


def violation(name, result, available=(), results=None, current=None):
    """The rule, as a sentence or None.

    `available` is the set of result names present, so an audit that has not been
    run cannot silently discharge the probe it covers. `results` and `current`
    are what let the discharge also require the audit to be CURRENT.

    Presence alone was not enough and this function knew it: audit_is_current
    was written to close exactly this hole -- "AUDIT_FOR excuses chi2_collapse
    on the strength of a collapse_spread computed under a gate nobody uses any
    more" -- and then was never called from here, so it sat dead outside its own
    test while rule 1 quietly leaned on rule 2 being enforced somewhere else.

    FAILS CLOSED. Without `results` and `current` the currency of the audit
    cannot be established, and an audit that cannot be checked discharges
    nothing -- the same reading this module already applies to a result carrying
    no gate constant at all.
    """
    offenders = low_df_moment_rows(result)
    if not offenders:
        return None
    if is_seeded(result):
        return None
    audit = AUDIT_FOR.get(name)
    if audit and audit in available:
        if results is not None and current is not None:
            if audit_is_current(name, results, current):
                return None
            return (f"{name}: discharged by {audit}, but {audit} was computed under "
                    f"gate constants the module no longer has. Re-run {audit} "
                    f"before it can excuse anything.")
        return (f"{name}: {audit} is present but its currency was not checked, so "
                f"it cannot discharge this probe. Pass results= and current= to "
                f"violation(), or call violations(results, current).")
    dfs = sorted({d for r in offenders for d in row_dfs(r) if d <= DF_NEEDS_SEEDS})
    return (f"{name}: verdict {result.get('verdict')!r} rests on {len(offenders)} "
            f"moment-carrying cells at df {dfs} with no base seeds and no audit. "
            f"Add n_base >= {MIN_BASE_SEEDS}, or register an audit in AUDIT_FOR "
            f"that reseeds this grid.")


def violations(results, current):
    """{name: sentence} over a {name: result} mapping.

    `current` is current_constants(probes_module); it is required rather than
    optional because without it an audit's discharge cannot be checked, and a
    convenient default here is how the guard went quiet in the first place.
    """
    out = {}
    for name, result in sorted(results.items()):
        v = violation(name, result, available=set(results),
                      results=results, current=current)
        if v:
            out[name] = v
    return out


# ---------------------------------------------------------------------------
# SECOND RULE: a result may not be read as current if the gate constants it was
# computed under no longer match the code.
#
# The harness already refuses to regenerate RESULTS.md from a PARTIAL run. It has
# nothing to say about a COMPLETE run against stale code, and that is the failure
# that actually happened: a full sweep started at 21:16:32, probes.py was edited
# 18 seconds later, and RESULTS.md was written from source that no longer exists.
# Every probe reported success. The only reason anyone noticed is that a second
# session hashed the file before and after by hand.
#
# It is the same hole as the audit discharge above -- AUDIT_FOR asks whether
# collapse_spread EXISTS, never whether it was computed under the same gate -- so
# one check closes both.
#
# WHAT IT CANNOT DO. Gate constants are recorded unevenly: chi2_collapse,
# b1_ladder and collapse_spread carry saturation_max; b1_one_boundary,
# curl_freedom and harmonic_projected_eps carry only alpha; seed_spread records
# none at all. So absence is not agreement, and the two cases are reported
# separately -- a mismatch is a stale result, an absence is a result that cannot
# be checked at all, which is its own defect and should not be silently counted
# as passing.

# recorded json key -> the module attribute that produced it
GATE_CONSTANTS = {
    "saturation_max": "SATURATION_MAX",
    "saturation_window": "SATURATION_WINDOW",
    "saturation_target": "SATURATION_TARGET",
    "mtol": "MOMENT_MTOL",
    "vtol": "MOMENT_VTOL",
    "binom_alpha": "BINOM_ALPHA",
    "alpha": "ALPHA",
    "tail_shrink_factor": "TAIL_SHRINK_FACTOR",
}


def current_constants(probes_module):
    """{recorded_key: value} for every gate constant the module still defines.

    A constant the module has DROPPED is absent here, which is what makes a
    result recording it detectable as stale rather than merely different.
    """
    return {key: getattr(probes_module, attr)
            for key, attr in GATE_CONSTANTS.items()
            if hasattr(probes_module, attr)}


def recorded_constants(result):
    value = result.get("value") or {}
    return {k: value[k] for k in GATE_CONSTANTS if k in value}


def comparable(v):
    """A gate constant reduced to a form that survives a round trip through JSON.

    JSON object keys are ALWAYS strings. A constant that is a dict in the module --
    SATURATION_WINDOW is {1: 0.019, 22: 0.120}, keyed by b1 as an int -- comes back
    as {"1": 0.019, "22": 0.120}, and a naive != then reports every result stale
    against the very module that produced it. Every gate constant before this one
    was a scalar, which is why the comparison looked sound.

    That failure mode is worse than a false alarm. A guard no run can satisfy is a
    guard someone switches off, and the genuine flag sitting beside it -- here,
    collapse_spread really was computed under a constant the module has dropped --
    goes out with the noise. So keys are normalised to strings on both sides
    before comparing, values left alone.
    """
    if isinstance(v, dict):
        return {str(k): comparable(val) for k, val in v.items()}
    if isinstance(v, (list, tuple)):
        return [comparable(x) for x in v]
    return v


def staleness(name, result, current):
    """A sentence when this result was computed under constants the code no
    longer has, or holds a value the code has changed. None when it agrees."""
    recorded = recorded_constants(result)
    if not recorded:
        return None
    gone = [k for k in recorded if k not in current]
    if gone:
        return (f"{name}: records {gone} which the module no longer defines, so it "
                f"was computed under a gate that has since been replaced. Re-run it.")
    differs = {k: (recorded[k], current[k])
               for k in recorded
               if comparable(recorded[k]) != comparable(current[k])}
    if differs:
        pairs = ", ".join(f"{k}: result {r!r} vs code {c!r}"
                          for k, (r, c) in sorted(differs.items()))
        return f"{name}: computed under different gate constants -- {pairs}. Re-run it."
    return None


def uncheckable(results):
    """Results recording no gate constant at all. Not stale -- unverifiable."""
    return sorted(n for n, r in results.items() if not recorded_constants(r))


def stale(results, current):
    """{name: sentence} for every result out of step with the running code."""
    out = {}
    for name, result in sorted(results.items()):
        v = staleness(name, result, current)
        if v:
            out[name] = v
    return out


def audit_is_current(probe_name, results, current):
    """An audit discharges its probe only while it agrees with the code.

    Without this, AUDIT_FOR excuses chi2_collapse on the strength of a
    collapse_spread computed under a gate nobody uses any more -- which is the
    state the tree is in as this is written.
    """
    audit = AUDIT_FOR.get(probe_name)
    if not audit or audit not in results:
        return False
    return staleness(audit, results[audit], current) is None


# ---------------------------------------------------------------------------
# THIRD RULE: a result may not be read as current if the CODE that produced it
# has changed meaning, whether or not any named constant moved.
#
# Rule 2 watches gate constants. It went silent when closes_at() was changed from
# testing var_ratio alone to testing both moments -- b1_1_closes_at moved 0.05 ->
# 0.03, a real change to a shipped number, and nothing mismatched because
# b1_one_boundary records only alpha. The change travelled through a PREDICATE,
# which constants cannot see. That is the third blind spot found in this file
# tonight, and unlike the other two it is not a bug: rule 2 is doing exactly what
# it says.
#
# WHY NOT HASH THE FILE. Any edit then invalidates every result, comments
# included. That is the permanently-red failure this module already had once, and
# a guard nobody can satisfy is one that gets switched off -- taking the genuine
# flags with it. So the fingerprint is per PROBE and blind to anything that does
# not change meaning.
#
# WHAT IT COVERS. The probe's own body, plus the transitive closure of
# module-level functions it calls and module-level constants it reads. Comments
# never reach the AST at all; docstrings are stripped explicitly; positions are
# excluded, so reindenting or rewrapping a line changes nothing.
#
# WHAT IT DOES NOT COVER, and these are stated rather than solved. Calls made
# dynamically (getattr, a name looked up at run time) are invisible to a static
# walk. Behaviour that depends on a THIRD-PARTY or cross-tree module -- hodge,
# rig.flows, numpy -- is out of scope: this answers "did OUR code change", not
# "did the world". Modules in THIS DIRECTORY are ours and are covered whole; see
# _sibling_modules for why score_test.py had to stop counting as the world. And a
# semantically neutral refactor, extracting a helper without altering behaviour,
# WILL change the fingerprint. That direction is the safe one: it costs a re-run
# nobody needed rather than hiding one that was.

import ast
import hashlib
import inspect
import os
import textwrap
import types


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
    """Modules `module` imports that live BESIDE it -- ours, not the world.

    numpy, scipy and hodge are the world: out of scope by design, and hashing
    them would turn the fingerprint into a version stamp that any upgrade
    invalidates. score_test.py is NOT the world. It sits in this directory, it
    is written and edited here, and its ETA_CLIP, SEPARATED and fit_constrained
    decide `usable` for every draw in every probe -- so editing it invalidates
    all nine results while moving no gate constant and no probe body, leaving
    stale(), fingerprint_mismatch() and uncheckable() all reporting clean. That
    was rule 3's own blind spot, one file over from the one it was written to
    close: _module_level walks tree.body for FunctionDef and Assign and has no
    branch for Import, so an imported name could never enter the closure.

    Siblings enter WHOLE rather than per-probe. There is no closure to narrow
    them to: a constant like SEPARATED is read inside score_test's own functions,
    not from the probe body, so reference-following from the probe would never
    reach it. The cost is that a change anywhere in a sibling re-stamps every
    probe -- the same conservative direction the module already accepts for a
    neutral refactor, costing a re-run nobody needed rather than hiding one that
    was.
    """
    f0 = getattr(module, "__file__", "") or ""
    if not f0:
        return {}
    here = os.path.dirname(os.path.abspath(f0))
    out = {}
    for obj in vars(module).values():
        if not isinstance(obj, types.ModuleType) or obj is module:
            continue
        f = getattr(obj, "__file__", None)
        if f and os.path.dirname(os.path.abspath(f)) == here:
            out[obj.__name__] = obj
    return out


def semantic_fingerprint(module, entry, _max_depth=12):
    """A hash of `entry` and everything in this module it transitively depends on.

    Stable across comments, docstrings, blank lines and reindentation. Changes
    when any body or constant in the closure changes meaning.
    """
    level = _module_level(module)
    if entry not in level:
        return None
    seen, frontier = set(), {entry}
    for _ in range(_max_depth):
        new = set()
        for name in sorted(frontier):
            if name in seen:
                continue
            seen.add(name)
            new |= _referenced(level[name], set(level)) - seen
        if not new:
            break
        frontier = new
    parts = [f"{n}::{level[n]}" for n in sorted(seen)]
    for mname, sib in sorted(_sibling_modules(module).items()):
        lv = _module_level(sib)
        parts += [f"{mname}.{n}::{lv[n]}" for n in sorted(lv)]
    payload = "\n".join(parts)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


# The key a result carries its fingerprint under. Probes record it; this module
# only reads it. The recording line belongs in probes.py's __main__ writer:
#
#     r.setdefault("value", {})["source_fingerprint"] = \
#         harness_rules.semantic_fingerprint(sys.modules[__name__], name)
#
FINGERPRINT_KEY = "source_fingerprint"


def fingerprint_mismatch(name, result, module):
    """A sentence when this result was produced by code that has since changed
    meaning, None when it agrees, and None when the result predates the field --
    an absent fingerprint is unverifiable, not agreement, and is reported by
    unfingerprinted() so it cannot be counted as passing."""
    recorded = (result.get("value") or {}).get(FINGERPRINT_KEY)
    if recorded is None:
        return None
    current = semantic_fingerprint(module, name)
    if current is None:
        return (f"{name}: records a source fingerprint but the module no longer "
                f"defines a probe by that name.")
    if recorded != current:
        return (f"{name}: produced by code that has since changed meaning "
                f"(fingerprint {recorded} -> {current}). No named constant need "
                f"have moved -- a predicate is enough. Re-run it.")
    return None


def unfingerprinted(results):
    """Results carrying no fingerprint: unverifiable by this rule, not agreeing."""
    return sorted(n for n, r in results.items()
                  if (r.get("value") or {}).get(FINGERPRINT_KEY) is None)
