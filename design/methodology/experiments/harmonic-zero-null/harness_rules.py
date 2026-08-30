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
# with 12/df. A row carrying any of these at low df is in scope.
MOMENT_FIELDS = ("mean_T", "var_T", "mean_ratio", "var_ratio",
                 "trimmed_mean_ratio")


def row_dfs(row):
    """Every degrees-of-freedom value a row reports, under any of its names."""
    out = []
    for key, val in row.items():
        if (key == "df" or key.endswith("_df")) and isinstance(val, int):
            out.append(val)
    return out


def carries_moments(row):
    return any(row.get(f) is not None for f in MOMENT_FIELDS)


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


def violation(name, result, available=()):
    """The rule, as a sentence or None.

    `available` is the set of result names present, so an audit that has not been
    run cannot silently discharge the probe it covers.
    """
    offenders = low_df_moment_rows(result)
    if not offenders:
        return None
    if is_seeded(result):
        return None
    audit = AUDIT_FOR.get(name)
    if audit and audit in available:
        return None
    dfs = sorted({d for r in offenders for d in row_dfs(r) if d <= DF_NEEDS_SEEDS})
    return (f"{name}: verdict {result.get('verdict')!r} rests on {len(offenders)} "
            f"moment-carrying cells at df {dfs} with no base seeds and no audit. "
            f"Add n_base >= {MIN_BASE_SEEDS}, or register an audit in AUDIT_FOR "
            f"that reseeds this grid.")


def violations(results):
    """{name: sentence} over a {name: result} mapping."""
    out = {}
    for name, result in sorted(results.items()):
        v = violation(name, result, available=set(results))
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
               for k in recorded if recorded[k] != current[k]}
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
