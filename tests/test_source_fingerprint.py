"""The semantic fingerprint: catching changes that move no named constant.

Rule 2 in harness_rules.py watches gate constants. It went silent when
`closes_at()` was changed from testing one moment to testing both -- the shipped
`b1_1_closes_at` moved 0.05 to 0.03 and nothing mismatched, because
b1_one_boundary records only alpha. The change travelled through a PREDICATE.

These tests pin the three properties that make the fingerprint worth having:

  sensitive to meaning       a predicate or constant in the closure changes it
  blind to presentation      comments, docstrings, wrapping, blank lines do not
  scoped to the probe        an unrelated function in the same file does not
  placed by stamp()          no writer puts the key somewhere by hand

The third is what keeps it from becoming the permanently-red guard this module
already had once. A check nobody can satisfy is a check someone switches off.
"""

import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_EXP = (Path(__file__).resolve().parents[1] / "design" / "methodology" /
        "experiments" / "harmonic-zero-null")
_spec = importlib.util.spec_from_file_location("harness_rules",
                                               _EXP / "harness_rules.py")
hr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hr)

RESULTS = _EXP / "results"

BASE = '''
THRESHOLD = 0.15

def helper(x):
    return x > THRESHOLD

def unrelated(y):
    return y * 2

def probe():
    return helper(0.2)
'''

DOCUMENTED = '''
THRESHOLD = 0.15   # a comment that means nothing

def helper(x):
    """Now with a docstring."""
    return x > THRESHOLD

def unrelated(y):
    return y * 2

def probe():
    # explanatory comment
    """And here too."""
    return helper(0.2)
'''

REWRAPPED = '''
THRESHOLD = 0.15

def helper(x):
    return x > THRESHOLD

def unrelated(y):
    return y * 2

def probe():

    return helper(
        0.2,
    )
'''

_n = [0]


def mod(body):
    """Import a synthetic module from source text."""
    _n[0] += 1
    tag = f"m{_n[0]}"
    path = Path(tempfile.mkdtemp()) / f"{tag}.py"
    path.write_text(body)
    spec = importlib.util.spec_from_file_location(tag, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def fp(body, entry="probe"):
    return hr.semantic_fingerprint(mod(body), entry)


# ---------------------------------------------------------------- blind to form
def test_comments_and_docstrings_do_not_change_it():
    """Documenting a probe must not invalidate its results, or nobody documents."""
    assert fp(BASE) == fp(DOCUMENTED)


def test_rewrapping_and_blank_lines_do_not_change_it():
    assert fp(BASE) == fp(REWRAPPED)


def test_it_is_deterministic():
    assert fp(BASE) == fp(BASE)


# ------------------------------------------------------------ sensitive to meaning
def test_a_predicate_change_in_a_called_helper_is_caught():
    """The closes_at case exactly: no constant moves, a helper's test changes."""
    changed = BASE.replace("return x > THRESHOLD",
                           "return x > THRESHOLD and x < 1.0")
    assert fp(BASE) != fp(changed)


def test_a_referenced_constant_change_is_caught():
    assert fp(BASE) != fp(BASE.replace("THRESHOLD = 0.15", "THRESHOLD = 0.20"))


def test_a_change_in_the_probe_body_is_caught():
    assert fp(BASE) != fp(BASE.replace("return helper(0.2)", "return helper(0.9)"))


# ---------------------------------------------------------------- scoped tightly
def test_an_unrelated_function_does_not_invalidate():
    """Hashing the file would make any edit invalidate every result. That is the
    failure mode this module already had once, from the other direction."""
    assert fp(BASE) == fp(BASE.replace("return y * 2", "return y * 3 + 1"))


def test_an_unknown_entry_point_returns_none():
    assert hr.semantic_fingerprint(mod(BASE), "no_such_probe") is None


# ------------------------------------------------------------------ the contract
def test_mismatch_fires_only_on_a_stale_hash():
    m = mod(BASE)
    good = {"value": {hr.FINGERPRINT_KEY: hr.semantic_fingerprint(m, "probe")}}
    assert hr.fingerprint_mismatch("probe", good, m) is None
    stale = {"value": {hr.FINGERPRINT_KEY: "deadbeefdeadbeef"}}
    assert hr.fingerprint_mismatch("probe", stale, m) is not None


def test_an_absent_fingerprint_is_unverifiable_not_agreement():
    """Same distinction rule 2 draws between a mismatch and a result recording no
    constants: absence is reported, never counted as passing."""
    m = mod(BASE)
    bare = {"value": {"rows": []}}
    assert hr.fingerprint_mismatch("probe", bare, m) is None
    assert "probe" in hr.unfingerprinted({"probe": bare})


# UNFINGERPRINTED is gone. It existed only to tolerate the migration from results
# written before the recording line to results written after, and that migration
# is complete. The ratchet earned its keep on the way -- it fired in BOTH
# directions, "this now carries one, strike it" as well as "this records none but
# should" -- but what it was standing in for is a property needing no list at all:
#
#     every result carries a fingerprint
#
# A list also carries a defect the property does not. It asserts a fact about
# ARTIFACTS in a working tree while living in SOURCE, so on a repo where results
# differ per branch it says different things depending on what is checked out. A
# strike request was correct on one branch and wrong on another at the same
# moment, and only checking before editing caught it. The property is true or
# false the same way everywhere.
#
# If a future migration genuinely needs tolerance, re-introduce a list
# DELIBERATELY with its reason attached, rather than leaving an empty one lying
# around to be appended to.


def test_every_result_carries_a_fingerprint():
    """The property the migration list was standing in for."""
    results = {p.stem: json.loads(p.read_text())
               for p in sorted(RESULTS.glob("*.json"))}
    if not results:
        pytest.skip("no results checked in")
    bare = hr.unfingerprinted(results)
    assert not bare, (
        f"{bare} record no fingerprint. The writer stamps every probe, so a bare "
        "result was written by code predating the recording line -- re-run it.")


def test_a_recorded_fingerprint_round_trips_against_the_live_module():
    """The recording line and the checker must agree on the real module, not just
    on synthetic ones -- the lesson from rule 1 sitting as a no-op while its
    synthetic controls passed."""
    spec = importlib.util.spec_from_file_location("probes_live", _EXP / "probes.py")
    live = importlib.util.module_from_spec(spec)
    # Deliberately unguarded. Swallowing the import error here turned the ONLY
    # non-synthetic exercise of rule 3 into a skip on exactly the tree states
    # where it matters most -- and this is the test whose docstring says it
    # exists because rule 1 "sat as a no-op while its synthetic controls
    # passed". A skip is that same no-op wearing a different colour.
    spec.loader.exec_module(live)
    checked = 0
    for path in sorted(RESULTS.glob("*.json")):
        result = json.loads(path.read_text())
        if (result.get("value") or {}).get(hr.FINGERPRINT_KEY) is None:
            continue
        checked += 1
        assert hr.fingerprint_mismatch(path.stem, result, live) is None, (
            f"{path.stem} was written by this module but reads as stale -- the "
            "writer and the checker disagree, which makes the rule useless")
    if not checked:
        pytest.skip("no fingerprinted results yet")


# ---------------------------------------------------------------------------
# The real fixture.
#
# Everything above uses synthetic modules, which prove the rule fires on code
# shaped the way the rule expects -- the exact reasoning error that let rule 1 sit
# as a no-op on collapse_spread while its synthetic controls passed. So this
# anchors to real history instead.
#
# 870764b is a commit where probes.py computes b1_1_closes_at = 0.03 while
# results/b1_one_boundary.json records 0.05, with alpha as the only gate constant
# either side. Rule 2 is structurally blind to it. Rule 3 is the reason it exists.
#
# Skips rather than fails when the commits are unreachable, so a fresh clone or a
# rewritten history does not turn a missing fixture into a false alarm.

PRODUCED_AT = "3467b9b"   # the code that generated the recorded 0.05
CHANGED_AT = "870764b"    # merged branch: closes_at now tests both moments
PROBES_REL = ("design/methodology/experiments/harmonic-zero-null/probes.py")


def _module_at(rev, tag):
    """Materialise probes.py at `rev` beside the real one, so its relative
    sys.path arithmetic still resolves, and import it under a unique name."""
    import subprocess
    proc = subprocess.run(["git", "-C", str(_EXP), "show", f"{rev}:{PROBES_REL}"],
                          capture_output=True, text=True)
    if proc.returncode != 0 or not proc.stdout:
        return None, None
    path = _EXP / f"_fixture_{tag}.py"
    path.write_text(proc.stdout)
    try:
        spec = importlib.util.spec_from_file_location(f"fixture_{tag}", path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m, path
    except Exception:
        path.unlink(missing_ok=True)
        return None, None


def test_rule_3_catches_the_predicate_change_rule_2_was_blind_to():
    paths = []
    try:
        produced, p1 = _module_at(PRODUCED_AT, "produced")
        paths.append(p1)
        current, p2 = _module_at(CHANGED_AT, "current")
        paths.append(p2)
        if produced is None or current is None:
            pytest.skip("fixture commits not reachable in this checkout")

        before = hr.semantic_fingerprint(produced, "b1_one_boundary")
        after = hr.semantic_fingerprint(current, "b1_one_boundary")
        assert before and after
        assert before != after, (
            "the closes_at predicate change did not move the fingerprint -- rule 3 "
            "would be blind to the case it was written for")

        # rule 2, on the same artifact, is silent: alpha is the only constant.
        recorded = {"value": {"alpha": 0.05}}
        assert hr.staleness("b1_one_boundary", recorded,
                            hr.current_constants(current)) is None, (
            "rule 2 now flags this -- if constants started being recorded, this "
            "test's premise needs revisiting")

        # and end to end, had the fingerprint been recorded at production time
        as_recorded = {"value": {hr.FINGERPRINT_KEY: before, "alpha": 0.05}}
        assert hr.fingerprint_mismatch(
            "b1_one_boundary", as_recorded, current) is not None

        # controls: probes untouched across the same pair must not move
        for name in ("curl_freedom", "harmonic_projected_eps"):
            assert (hr.semantic_fingerprint(produced, name)
                    == hr.semantic_fingerprint(current, name)), (
                f"{name} moved across a change that did not touch it")
    finally:
        for p in paths:
            if p is not None:
                p.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# COVERAGE: the rule must reach every result artifact, not the nine it grew up
# on. Ten of the repository's nineteen shipped with no fingerprint at all --
# b1_rate, all six bias-of-bias results, evidence.json and boundary_report.json
# -- because the machinery lived inside one experiment directory and the other
# writers could not reach it. That is not a weaker guarantee on those ten; it is
# none, and it reads identical to a green one. `p_at_or_above_0.672` sat in
# b1_rate.json for weeks with no writer anywhere in the tree, and nothing could
# ask what produced it.
#
# Stated as a PROPERTY over whatever is on disk rather than a list of files, for
# the reason the migration lists were dissolved: a list is true of one checkout.
_ROOT = Path(__file__).resolve().parents[1]


def _artifacts():
    """Every committed result artifact, found rather than enumerated."""
    found = {}
    for p in sorted((_ROOT / "design").rglob("results/*.json")):
        found[str(p.relative_to(_ROOT))] = p
    for extra in ("boundary_report.json", "design/methodology/evidence/evidence.json"):
        p = _ROOT / extra
        if p.exists():
            found[extra] = p
    return found


def test_every_result_artifact_carries_a_source_fingerprint():
    """The property. A new experiment cannot ship unfingerprinted by default."""
    arts = _artifacts()
    assert arts, "no result artifacts found -- the glob is wrong, not the tree"
    bare = sorted(name for name, p in arts.items()
                  if hr.recorded_fingerprint(json.loads(p.read_text())) is None)
    assert not bare, (
        "these artifacts record no source fingerprint, so nothing can date them "
        "against the code that made them:\n  " + "\n  ".join(bare)
        + "\nStamp them at the writer with rig.provenance.stamp().")


# artifact -> (module file, entry point or None for a module-wide fingerprint).
# A list of WRITERS, not of tolerated exceptions: it records where each artifact
# is produced, so the round-trip below can re-derive the hash the writer stored.
_WRITERS = {
    "boundary_report.json": ("envelope_evaluator.py", "main"),
    "design/methodology/evidence/evidence.json": (
        "design/methodology/evidence/generate.py", None),
    "design/methodology/experiments/b1-rate/results/b1_rate.json": (
        "design/methodology/experiments/b1-rate/b1_rate.py", "run"),
    "design/methodology/experiments/bias-of-bias/results/exact_energy_residual.json": (
        "design/methodology/experiments/bias-of-bias/exact_energy.py", "run"),
    # The checkpoint is an INPUT as well as an output -- run(resume=True) skips
    # every base seed it already holds -- so it needs the same provenance as a
    # result. Unstamped, a code change was silently ignored for all 20 seeds and
    # the "exact" residual would have been a stale number with a fresh timestamp.
    "design/methodology/experiments/bias-of-bias/results/exact_energy_checkpoint.json": (
        "design/methodology/experiments/bias-of-bias/exact_energy.py", "run"),
}
for _probe in ("rho_squared", "bias_corrected", "eps_dependence",
               "richardson", "joint_consistency"):
    _WRITERS[f"design/methodology/experiments/bias-of-bias/results/{_probe}.json"] = (
        "design/methodology/experiments/bias-of-bias/probes.py", _probe)


def _load(rel):
    """Import a writer by path, with its own directory importable.

    bias-of-bias/probes.py does a bare `import core`, which resolves only when
    its directory is on sys.path -- true when run as a script from there, not
    true for an importer. Adding the parent is what a script run does implicitly.
    """
    path = _ROOT / rel
    parent = str(path.resolve().parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    spec = importlib.util.spec_from_file_location(f"w_{path.stem}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("artifact", sorted(_WRITERS))
def test_each_writers_artifact_round_trips_against_its_live_module(artifact):
    """The recorded hash must be the one the live writer would compute.

    The coverage test above proves a fingerprint is PRESENT. This proves it is
    the RIGHT one -- the check that catches a writer stamping a different entry
    point from the one that produced the numbers, which a present-but-wrong hash
    would otherwise hide behind a green coverage test.
    """
    p = _ROOT / artifact
    if not p.exists():
        pytest.skip(f"{artifact} not present")
    rel, entry = _WRITERS[artifact]
    mod = _load(rel)
    assert hr.fingerprint_mismatch(artifact, json.loads(p.read_text()), mod,
                                   entry) is None, (
        f"{artifact} was written by {rel} but reads as stale -- re-run it, or the "
        "writer and this registry disagree about which entry point produced it")


# ---------------------------------------------------------------- placed by stamp()
#
# The two guards above answer "is a fingerprint present" and "is it the right
# one". Neither can see a writer that computes a CORRECT hash and puts it
# somewhere by hand, because the artifact then passes both -- which is exactly
# how two bypasses shipped: harmonic-zero-null/probes.py assigned through
# FINGERPRINT_KEY, and envelope_evaluator.py wrote the literal key into a dict
# literal. Both agreed with the reader by coincidence: _SHAPES happened to look
# where they happened to write.
#
# That coincidence is the whole problem. `stamp` and `recorded_fingerprint`
# share _SHAPES so a fingerprint cannot be written somewhere the reader does not
# look; a writer that places the key itself opts out of that guarantee while
# still looking green.

_EXEMPT = "provenance-exempt:"

# The implementation, and fixtures that build artifact-shaped dicts on purpose.
_PLACEMENT_SKIP = ("rig/provenance.py", "tests/")


def _tracked_py():
    """Tracked .py files, from git rather than a glob.

    git ls-files excludes .claude/worktrees/ and any untracked scratch by
    construction, so a sibling session's checkout cannot enter this scan and a
    new writer cannot avoid it by not being listed anywhere.
    """
    out = subprocess.run(["git", "ls-files", "*.py"], cwd=_ROOT,
                         capture_output=True, text=True, check=True)
    return [f for f in out.stdout.split()
            if not f.startswith(_PLACEMENT_SKIP)]


def _placements(path):
    """(line, form) for every hand-placement of the fingerprint key.

    Catches both shapes seen in the wild: the key as a dict-literal entry, and
    a subscript assignment through it. Spelled as the literal or through
    FINGERPRINT_KEY -- the constant is not a defence, since probes.py's bypass
    used it.
    """
    def is_key(n):
        if isinstance(n, ast.Constant) and n.value == hr.FINGERPRINT_KEY:
            return "literal"
        if isinstance(n, ast.Attribute) and n.attr == "FINGERPRINT_KEY":
            return "constant"
        if isinstance(n, ast.Name) and n.id == "FINGERPRINT_KEY":
            return "constant"
        return None

    found = []
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Dict):
            for k in node.keys:
                if k is not None and is_key(k):
                    found.append((k.lineno, "dict-key"))
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Subscript) and is_key(t.slice):
                    found.append((t.lineno, "subscript-assign"))
    return found


def _unexempted(rel):
    """Placements not annotated `provenance-exempt:` on their line or the one above.

    A two-line window on purpose. Widening it to accommodate a comment block
    further up would let one site's exemption silently cover a neighbouring
    placement, which is the failure this check exists to prevent, relocated.
    """
    path = _ROOT / rel
    lines = path.read_text().splitlines()
    out = []
    for lineno, form in _placements(path):
        window = lines[max(0, lineno - 2):lineno]
        if not any(_EXEMPT in ln for ln in window):
            out.append(f"{rel}:{lineno} ({form})")
    return out


def test_the_placement_scan_matches_real_code():
    """Guards against the vacuous pass, which is how both bypasses survived review.

    A scan that silently matches nothing asserts nothing and reports green --
    the failure this whole module exists to make impossible. So the detector
    must demonstrably fire on the tree as it stands: exempt placements count,
    because they prove the AST shapes are still the ones being written.
    """
    files = _tracked_py()
    assert files, "git ls-files matched no .py files -- the scan is broken, not the tree"
    total = sum(len(_placements(_ROOT / f)) for f in files)
    assert total, (
        "the placement scan found no fingerprint placements anywhere, including "
        "exempted ones. Either provenance moved off FINGERPRINT_KEY or this "
        "detector has stopped matching; it is not evidence that nothing bypasses.")


def test_no_writer_places_the_fingerprint_by_hand():
    """Every fingerprint reaches an artifact through stamp(), or says why not."""
    offenders = [o for f in _tracked_py() for o in _unexempted(f)]
    assert not offenders, (
        "these place the fingerprint key directly instead of calling "
        "rig.provenance.stamp():\n  " + "\n  ".join(offenders)
        + f"\nstamp() returns the artifact, so it wraps a dict literal as well as "
          f"following one. If a site genuinely is not an artifact, annotate it "
          f"`# {_EXEMPT} <reason>` on that line or the one directly above.")
