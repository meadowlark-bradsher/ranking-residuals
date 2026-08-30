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


def test_every_shipped_result_is_currently_unfingerprinted():
    """A ratchet. Probes do not record the fingerprint yet -- the recording line
    belongs in probes.py's writer and that file is held by another session. When
    it lands, this fails and tells whoever landed it to narrow the assertion."""
    results = {p.stem: json.loads(p.read_text())
               for p in sorted(RESULTS.glob("*.json"))}
    if not results:
        pytest.skip("no results checked in")
    assert set(hr.unfingerprinted(results)) == set(results), (
        "a result now carries a source fingerprint -- good. Narrow this test to "
        "the ones that still do not, so the ratchet keeps its grip.")
