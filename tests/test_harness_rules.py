"""The harness rule: no verdict on a moment ratio from a low-df cell, unseeded.

The rule and its rationale live in
design/methodology/experiments/harmonic-zero-null/harness_rules.py. This file is
the enforcement: it applies the rule to the shipped results and holds the set of
known violations at exactly one.

KNOWN_GAPS is a RATCHET, not a suppression. The test asserts the violation set
EQUALS it, so adding a violating probe fails, and fixing a listed one also fails
-- with a message telling you to strike it from the list. It cannot quietly grow.
"""

import importlib.util
import json
from pathlib import Path

import pytest

_EXP = (Path(__file__).resolve().parents[1] / "design" / "methodology" /
        "experiments" / "harmonic-zero-null")
_spec = importlib.util.spec_from_file_location("harness_rules",
                                               _EXP / "harness_rules.py")
hr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hr)

RESULTS = _EXP / "results"

# The one probe that currently reaches a verdict on df = 1 moment ratios without
# seeds. It is the probe that produced three of the five withdrawn findings, so it
# is the right thing to be holding a light on. Reseeding it inline would cost
# 10x its runtime; the fix is a companion audit, as chi2_collapse has, registered
# in harness_rules.AUDIT_FOR. Tracked on RAN-29.
KNOWN_GAPS = {"b1_ladder"}


def _load():
    return {p.stem: json.loads(p.read_text()) for p in sorted(RESULTS.glob("*.json"))}


@pytest.fixture(scope="module")
def results():
    r = _load()
    if not r:
        pytest.skip("no results/*.json checked in; run `python probes.py`")
    return r


def test_violation_set_is_exactly_the_known_gaps(results):
    """The ratchet. Equality, not subset -- so it catches both directions."""
    found = set(hr.violations(results))
    new = found - KNOWN_GAPS
    fixed = KNOWN_GAPS - found
    assert not new, (
        "a probe now reaches a verdict on low-df moment ratios without seeds:\n  "
        + "\n  ".join(hr.violations(results)[n] for n in sorted(new)))
    assert not fixed, (
        f"{sorted(fixed)} no longer violates the rule -- strike it from KNOWN_GAPS "
        "so the ratchet keeps its grip")


def test_seeded_probes_are_recognised_as_seeded(results):
    """The rule must not flag the probes that already do the right thing."""
    for name in ("seed_spread", "b1_one_boundary", "collapse_spread"):
        if name in results:
            assert hr.is_seeded(results[name]), f"{name} carries seeds but reads unseeded"


def test_rejection_rate_probes_are_out_of_scope(results):
    """curl_freedom and harmonic_projected_eps decide on binomial proportions,
    whose s.e. does not degrade with df. Flagging them would be a false positive,
    and a rule that cries wolf gets suppressed."""
    for name in ("curl_freedom", "harmonic_projected_eps"):
        if name in results:
            assert not hr.low_df_moment_rows(results[name]), (
                f"{name} now reports moment ratios; it is in scope for the rule "
                "and this test's premise needs revisiting")


def test_an_audit_only_discharges_when_it_has_actually_run(results):
    """chi2_collapse is covered by collapse_spread. Drop the audit and the cover
    goes with it -- otherwise a registry entry excuses a probe nobody audited."""
    if "chi2_collapse" not in results:
        pytest.skip("chi2_collapse not present")
    assert hr.violation("chi2_collapse", results["chi2_collapse"],
                        available=set(results)) is None
    assert hr.violation("chi2_collapse", results["chi2_collapse"],
                        available={"chi2_collapse"}) is not None


def test_the_rule_fires_on_a_constructed_unseeded_low_df_verdict():
    """Direct exercise, so the rule is tested even with no results checked in."""
    bad = {"verdict": "confirmed",
           "value": {"rows": [{"df": 1, "mean_T": 1.05, "var_T": 2.3}]}}
    assert hr.violation("made_up", bad) is not None
    seeded = {"verdict": "confirmed",
              "value": {"n_base": hr.MIN_BASE_SEEDS,
                        "rows": [{"df": 1, "mean_T": 1.05, "var_T": 2.3}]}}
    assert hr.violation("made_up", seeded) is None
    high_df = {"verdict": "confirmed",
               "value": {"rows": [{"df": 22, "mean_T": 1.05, "var_T": 2.3}]}}
    assert hr.violation("made_up", high_df) is None
    no_moments = {"verdict": "confirmed",
                  "value": {"rows": [{"df": 1, "reject_rate": 0.05}]}}
    assert hr.violation("made_up", no_moments) is None


# ---------------------------------------------------------------------------
# The staleness rule. Live state as this is written: a full sweep ran at
# 21:16:32 against source that was edited 18 seconds later, so every result
# recording saturation_max was computed under a flat window the module has since
# replaced with a b1-dependent one. Every probe reported success; nothing in the
# output said otherwise.
#
# These names are here to make that visible, not to excuse it. Re-running the
# suite under the committed window clears them, and the equality assertion then
# fails until they are struck -- same ratchet as KNOWN_GAPS.
KNOWN_STALE = {"b1_ladder", "chi2_collapse", "collapse_spread"}

# Results recording no gate constant at all cannot be checked either way. That is
# a defect in the probe, not in the checker: a result nobody can date is one that
# will be read as current forever.
KNOWN_UNCHECKABLE = {"seed_spread"}


def _probes_module():
    """Load probes.py by path, tolerating a session mid-edit."""
    spec = importlib.util.spec_from_file_location("probes_mod", _EXP / "probes.py")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return None
    return mod


@pytest.fixture(scope="module")
def current():
    mod = _probes_module()
    if mod is None:
        pytest.skip("probes.py not importable right now (another session editing?)")
    return hr.current_constants(mod)


def test_stale_result_set_is_exactly_the_known_stale(results, current):
    found = set(hr.stale(results, current))
    new = found - KNOWN_STALE
    fixed = KNOWN_STALE - found
    assert not new, (
        "a result is now out of step with the gate constants in probes.py:\n  "
        + "\n  ".join(hr.stale(results, current)[n] for n in sorted(new)))
    assert not fixed, (
        f"{sorted(fixed)} now agrees with the code -- strike it from KNOWN_STALE")


def test_uncheckable_results_are_exactly_the_known_ones(results):
    found = set(hr.uncheckable(results))
    assert found == KNOWN_UNCHECKABLE, (
        f"results recording no gate constants changed: {sorted(found)}. A probe "
        "that records none cannot be dated against the code and will be read as "
        "current forever; give it its constants or add it here deliberately.")


def test_a_stale_audit_does_not_discharge_its_probe(results, current):
    """The hole this rule was written to close.

    AUDIT_FOR excuses chi2_collapse because collapse_spread exists. It should stop
    excusing it the moment that audit is out of step with the code -- which is the
    tree's state right now, so this asserts the guard actually fires.
    """
    assert not hr.audit_is_current("chi2_collapse", results, current), (
        "collapse_spread now agrees with the code; if the suite was re-run, strike "
        "it from KNOWN_STALE and invert this assertion")


def test_staleness_fires_on_a_dropped_constant():
    """Direct exercise, independent of what is on disk."""
    old = {"verdict": "confirmed", "value": {"saturation_max": 0.02, "rows": []}}
    assert hr.staleness("x", old, {"saturation_window": {1: 0.019}}) is not None
    assert hr.staleness("x", old, {"saturation_max": 0.02}) is None
    changed = {"verdict": "c", "value": {"saturation_max": 0.02, "rows": []}}
    assert hr.staleness("x", changed, {"saturation_max": 0.05}) is not None
    bare = {"verdict": "c", "value": {"rows": []}}
    assert hr.staleness("x", bare, {"saturation_max": 0.02}) is None
