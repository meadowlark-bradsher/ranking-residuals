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
