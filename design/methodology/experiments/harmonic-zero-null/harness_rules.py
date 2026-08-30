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
