"""The semantic fingerprint: catching changes that move no named constant.

Rule 2 in harness_rules.py watches gate constants. It went silent when
`closes_at()` was changed from testing one moment to testing both -- the shipped
`b1_1_closes_at` moved 0.05 to 0.03 and nothing mismatched, because
b1_one_boundary records only alpha. The change travelled through a PREDICATE.

These tests pin the three properties that make the fingerprint worth having:

  sensitive to meaning       a predicate or constant in the closure changes it
  blind to presentation      comments, docstrings, wrapping, blank lines do not
  scoped to the probe        an unrelated function in the same file does not

The third is what keeps it from becoming the permanently-red guard this module
already had once. A check nobody can satisfy is a check someone switches off.
"""

import importlib.util
import json
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


# Results that predate the recording line. It landed in probes.py's writer, so
# every probe stamps its fingerprint from now on and this set shrinks to nothing
# as each is re-run. The ratchet fired the moment the first one landed and told
# me to narrow it, which is what it is for.
UNFINGERPRINTED = {"b1_ladder", "b1_one_boundary", "chi2_collapse",
                   "collapse_spread", "harmonic_projected_eps", "seed_spread"}


def test_the_unfingerprinted_set_is_exactly_the_results_predating_recording():
    """Equality, so it catches both directions: a new result arriving without a
    fingerprint fails, and a re-run one that gains a fingerprint also fails --
    telling whoever re-ran it to strike the name rather than letting the set rot
    into a list nobody trusts."""
    results = {p.stem: json.loads(p.read_text())
               for p in sorted(RESULTS.glob("*.json"))}
    if not results:
        pytest.skip("no results checked in")
    found = set(hr.unfingerprinted(results)) & set(results)
    expected = UNFINGERPRINTED & set(results)
    new = found - expected
    fixed = expected - found
    assert not new, (
        f"{sorted(new)} record no fingerprint but should -- the writer stamps "
        "every probe now, so a bare result means it was written by older code")
    assert not fixed, (
        f"{sorted(fixed)} now carries a fingerprint -- strike it from "
        "UNFINGERPRINTED so the ratchet keeps its grip")


def test_a_recorded_fingerprint_round_trips_against_the_live_module():
    """The recording line and the checker must agree on the real module, not just
    on synthetic ones -- the lesson from rule 1 sitting as a no-op while its
    synthetic controls passed."""
    spec = importlib.util.spec_from_file_location("probes_live", _EXP / "probes.py")
    live = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(live)
    except Exception:
        pytest.skip("probes.py not importable right now")
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
