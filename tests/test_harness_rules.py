"""The harness rule: no verdict on a moment ratio from a low-df cell, unseeded.

The rule and its rationale live in
design/methodology/experiments/harmonic-zero-null/harness_rules.py. This file is
the enforcement: it applies the rule to the shipped results and holds the set of
known violations at exactly one.

KNOWN_GAPS is a RATCHET, not a suppression. The test asserts the violation set
EQUALS it, so adding a violating probe fails, and fixing a listed one also fails
-- with a message telling you to strike it from the list. It cannot quietly grow.
"""

import copy
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


def test_violation_set_is_exactly_the_known_gaps(results, current):
    """The ratchet. Equality, not subset -- so it catches both directions."""
    found = set(hr.violations(results, current))
    new = found - KNOWN_GAPS
    fixed = KNOWN_GAPS - found
    assert not new, (
        "a probe now reaches a verdict on low-df moment ratios without seeds:\n  "
        + "\n  ".join(hr.violations(results, current)[n] for n in sorted(new)))
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


def test_an_audit_only_discharges_when_it_has_actually_run(results, current):
    """chi2_collapse is covered by collapse_spread. Drop the audit and the cover
    goes with it -- otherwise a registry entry excuses a probe nobody audited."""
    if "chi2_collapse" not in results:
        pytest.skip("chi2_collapse not present")
    assert hr.violation("chi2_collapse", results["chi2_collapse"],
                        available=set(results), results=results,
                        current=current) is None
    assert hr.violation("chi2_collapse", results["chi2_collapse"],
                        available={"chi2_collapse"}, results=results,
                        current=current) is not None


def test_a_stale_audit_does_not_discharge_its_probe(results, current):
    """Presence was never the question; currency is.

    violation() knew about audit_is_current and never called it, so a
    collapse_spread computed under a replaced gate went on excusing
    chi2_collapse. Asserted here on a deliberately staled copy rather than on
    whatever state the tree happens to be in.
    """
    if "chi2_collapse" not in results or "collapse_spread" not in results:
        pytest.skip("chi2_collapse/collapse_spread not both present")
    staled = copy.deepcopy(results)
    recorded = hr.recorded_constants(staled["collapse_spread"])
    assert recorded, "collapse_spread records no gate constant; cannot stale it"
    key = sorted(recorded)[0]
    staled["collapse_spread"]["value"][key] = "definitely-not-the-current-value"
    assert hr.staleness("collapse_spread", staled["collapse_spread"], current)
    assert not hr.audit_is_current("chi2_collapse", staled, current)
    assert hr.violation("chi2_collapse", staled["chi2_collapse"],
                        available=set(staled), results=staled,
                        current=current) is not None, (
        "a stale audit still discharges chi2_collapse")


def test_an_uncheckable_audit_does_not_discharge_either(results):
    """Fail closed: without results/current the discharge cannot be verified."""
    if "chi2_collapse" not in results:
        pytest.skip("chi2_collapse not present")
    assert hr.violation("chi2_collapse", results["chi2_collapse"],
                        available=set(results)) is not None


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
#
# KNOWN_STALE is gone, and its absence is the point.
#
# It existed to tolerate a migration: results predating a gate change, tolerated by
# name until they could be re-run. Both entries were struck as the sequencing
# cleared them, and once the last one went the list was an empty container inviting
# additions. The property it was standing in for -- NO RESULT IS STALE -- needs no
# list, and unlike a list it says the same thing on every branch.
#
# That last part matters more than the tidiness. A named list asserts a fact about
# artifacts in a working tree while living in source, so on a repo where results
# differ per branch it asserts different things depending on what is checked out.
# That bit us for real: a strike request was correct on one branch and wrong on
# another at the same moment. Dissolving the list dissolves the failure mode.
#
# If a future migration genuinely needs tolerance, re-introduce a list DELIBERATELY
# with the reason attached, rather than leaving an empty one lying around for
# someone to append to.

# KNOWN_UNCHECKABLE is gone, the third and last of the migration lists.
#
# It held seed_spread, which recorded no gate constant at all and so could not be
# dated against the code either way -- unverifiable rather than agreeing. f4's
# f30800f gave it saturation_target and this pass names its tail-shrink threshold,
# so every probe now records the constants its verdict turns on.
#
# The property, which needs no list: EVERY RESULT RECORDS AT LEAST ONE GATE
# CONSTANT. A probe recording none is not passing the check, it is escaping it.


def _probes_module():
    """Load probes.py by path.

    This used to catch bare Exception and return None, which the fixture below
    turned into a skip "tolerating a session mid-edit". A SyntaxError, a missing
    scipy, or any import-time failure in probes.py therefore disarmed four
    guards at once -- the staleness test, the audit-discharge test, the
    false-positive test and (through the same pattern in
    test_source_fingerprint.py) the fingerprint round-trip -- and CI stayed
    green. A green run became indistinguishable from a run in which nothing was
    checked, which is the failure harness_rules.py's own docstring names: "a
    guard nobody can satisfy is one that gets switched off -- taking the genuine
    flags with it." An unimportable probes.py is a broken tree, not a reason to
    stop looking. Let it raise.
    """
    spec = importlib.util.spec_from_file_location("probes_mod", _EXP / "probes.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def current():
    return hr.current_constants(_probes_module())


def test_no_result_is_stale_against_the_code(results, current):
    """The property, not a list of exceptions to it."""
    flagged = hr.stale(results, current)
    assert not flagged, (
        "a result is out of step with the gate constants in probes.py -- re-run "
        "it rather than recording the disagreement:\n  "
        + "\n  ".join(flagged[n] for n in sorted(flagged)))


def test_every_result_records_at_least_one_gate_constant(results):
    """The property the third migration list stood in for.

    A result recording nothing is not agreeing with the code -- it is escaping the
    comparison, and will read as current forever.
    """
    bare = hr.uncheckable(results)
    assert not bare, (
        f"{bare} record no gate constant, so nothing can date them against the "
        "code. Give the probe its constants rather than tolerating the gap.")


def test_an_audit_discharges_exactly_when_it_is_present_and_current(results, current):
    """The hole this rule closed, stated as a property rather than a snapshot.

    AUDIT_FOR excuses chi2_collapse because collapse_spread exists. It must stop
    excusing it the moment that audit falls out of step with the code. This was
    first written as "the discharge must be OFF", which was true of the tree that
    day and false the moment collapse_spread was re-run -- the same snapshot
    mistake as naming probes in the stale test. Both directions are asserted now.
    """
    for probe, audit in hr.AUDIT_FOR.items():
        if probe not in results:
            continue
        present_and_current = (audit in results
                               and hr.staleness(audit, results[audit], current) is None)
        assert hr.audit_is_current(probe, results, current) is present_and_current, (
            f"{probe}'s discharge disagrees with whether {audit} is present and "
            "current")
        # a missing audit never discharges, whatever its state
        assert not hr.audit_is_current(probe, {probe: results[probe]}, current)


def test_staleness_fires_on_a_dropped_constant():
    """Direct exercise, independent of what is on disk."""
    old = {"verdict": "confirmed", "value": {"saturation_max": 0.02, "rows": []}}
    assert hr.staleness("x", old, {"saturation_window": {1: 0.019}}) is not None
    assert hr.staleness("x", old, {"saturation_max": 0.02}) is None
    changed = {"verdict": "c", "value": {"saturation_max": 0.02, "rows": []}}
    assert hr.staleness("x", changed, {"saturation_max": 0.05}) is not None
    bare = {"verdict": "c", "value": {"rows": []}}
    assert hr.staleness("x", bare, {"saturation_max": 0.02}) is None


# ---------------------------------------------------------------------------
# Detection, not just absence of false positives.
#
# The first version of MOMENT_FIELDS enumerated exact names and saw ZERO
# moment rows in collapse_spread, which reports ref_var_ratio / var_ratio_med /
# var_ratio_max at row level and keeps bare mean_ratio / var_ratio one level down
# inside "draws". The rule contributed nothing for that probe and nobody noticed,
# because the existing tests only checked that it did not fire where it should
# not. A rule with no positive-detection test is a rule that can quietly become a
# no-op.
MUST_DETECT = {
    "b1_ladder": "mean_T / var_T at row level",
    "chi2_collapse": "mean_T / var_T at row level",
    "b1_one_boundary": "mean_ratio / var_ratio aggregates",
    "seed_spread": "aggregates at row level, bare names in per_seed",
    "collapse_spread": "aggregates at row level, bare names in draws",
}


def test_the_rule_actually_detects_where_moments_are_reported(results):
    """Positive control. Each of these ships moment ratios on df<=2 cells."""
    for name, where in sorted(MUST_DETECT.items()):
        if name not in results:
            continue
        found = hr.low_df_moment_rows(results[name])
        assert found, (
            f"{name} reports moment ratios ({where}) but the rule sees none -- "
            "it is a no-op on this probe. Check MOMENT_SUBSTRINGS / "
            "MOMENT_PREFIXES and the nested descent in carries_moments().")


def test_nested_per_draw_moments_are_reached():
    """The descent specifically -- a probe that keeps moments ONLY one level down
    must still be in scope, since those per-draw values carry the 12/df error."""
    nested_only = {"verdict": "confirmed", "value": {"rows": [
        {"df": 1, "draws": [{"base": 0, "var_ratio": 1.4},
                            {"base": 1, "var_ratio": 0.9}]}]}}
    assert hr.low_df_moment_rows(nested_only)
    assert hr.violation("made_up", nested_only) is not None


def test_reference_constants_are_not_mistaken_for_measurements():
    """chi2_mean is df and chi2_var is 2*df. They carry no sampling error, so a
    row holding only those is not in scope."""
    refs_only = {"verdict": "confirmed",
                 "value": {"rows": [{"df": 1, "chi2_mean": 1, "chi2_var": 2}]}}
    assert not hr.low_df_moment_rows(refs_only)
    assert hr.violation("made_up", refs_only) is None


def test_rate_fields_are_not_matched_by_shape():
    """The shape matcher must not widen into proportions -- that is the
    false-positive the rule was deliberately kept narrow to avoid."""
    for key in ("reject_rate", "drop_rate", "pass_rate", "harmonic_reject",
                "bradley_terry_drop_rate", "in_S_control_reject"):
        assert not hr.is_moment_key(key), f"{key} must stay out of scope"
    for key in ("mean_T", "var_T", "mean_ratio", "var_ratio", "ref_var_ratio",
                "var_ratio_med", "var_ratio_max", "se_var_ratio",
                "trimmed_mean_ratio"):
        assert hr.is_moment_key(key), f"{key} must be in scope"


def test_dict_constants_survive_a_json_round_trip():
    """JSON object keys are always strings. SATURATION_WINDOW is keyed by b1 as an
    int, so without normalisation every result reads stale against the module that
    produced it -- and a guard no run can satisfy is one that gets switched off,
    taking the genuine flags with it."""
    module = {"saturation_window": {1: 0.019, 22: 0.120}}
    from_json = {"verdict": "confirmed", "value": {
        "saturation_window": {"1": 0.019, "22": 0.120}, "rows": []}}
    assert hr.staleness("x", from_json, module) is None
    really_changed = {"verdict": "confirmed", "value": {
        "saturation_window": {"1": 0.019, "22": 0.200}, "rows": []}}
    assert hr.staleness("x", really_changed, module) is not None


def test_a_flag_always_corresponds_to_a_real_disagreement(results, current):
    """Every stale flag must be traceable to a constant that actually differs.

    Written first as "chi2_collapse and b1_ladder must never be flagged", which
    was wrong: after the low anchor moved to 0.0017 those results legitimately
    disagreed with the module and SHOULD have flagged. Naming probes made the test
    assert a snapshot rather than the property. It now checks the property, so it
    survives the anchor moving again.
    """
    flagged = hr.stale(results, current)
    for name, msg in flagged.items():
        recorded = hr.recorded_constants(results[name])
        gone = [k for k in recorded if k not in current]
        differs = [k for k in recorded
                   if k in current
                   and hr.comparable(recorded[k]) != hr.comparable(current[k])]
        assert gone or differs, (
            f"{name} is flagged but every constant it records matches the module: "
            f"{msg}. That is a false positive -- check comparable().")
    for name, result in results.items():
        if name in flagged:
            continue
        recorded = hr.recorded_constants(result)
        for key, val in recorded.items():
            assert key in current and hr.comparable(val) == hr.comparable(current[key]), (
                f"{name} is NOT flagged but its {key} disagrees with the module")
