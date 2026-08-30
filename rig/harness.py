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
AUDIT_FOR = {}   # bound per experiment; see design/.../harness_rules.py

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
        # b1 IS the df: the statistic is chi2 with b1 degrees of freedom, so an
        # artifact that names it b1 and never writes "df" was invisible to this
        # rule. boundary_report.json is that artifact. Verified additive -- all
        # nine harmonic-zero-null results report df explicitly alongside b1, so
        # no existing verdict moves.
        elif key == "b1" and isinstance(val, int):
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


def walked_rows(obj, inherited_dfs=(), _depth=0, _max_depth=4):
    """Synthetic rows for an artifact that is not shaped `value.rows`.

    WHY THIS EXISTS. `low_df_moment_rows` read exactly one shape -- the probe
    record this experiment happens to write. Every artifact written any other
    way returned NO ROWS, so the rule reported no violation by never looking.
    That is a vacuous pass, and it is this rule's own failure mode relocated
    into the rule: a guard that covers the artifacts it was written beside and
    is silent on the rest is not a weaker guard, it reads exactly like a green
    one. boundary_report.json sat outside it for that reason while carrying
    four moment ratios at b1 = 1 with no replication.

    A cell is any dict that carries a moment ratio. Its df is whatever df-ish
    value is in scope at its own level or an enclosing one -- boundary_report
    puts b1 on the graph and the moments one level below it, so neither is
    readable without the other.
    """
    out = []
    if not isinstance(obj, dict) or _depth > _max_depth:
        return out
    here = tuple(inherited_dfs) + tuple(row_dfs(obj))
    if carries_moments(obj) and here:
        # Flattened so carries_moments/row_dfs apply unchanged. "df" is a
        # synthetic key: the walk resolved it, the artifact need not name it.
        out.append({**{k: v for k, v in obj.items() if not isinstance(v, dict)},
                    "df": min(here)})
    for val in obj.values():
        if isinstance(val, dict):
            out += walked_rows(val, here, _depth + 1, _max_depth)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict):
                    out += walked_rows(item, here, _depth + 1, _max_depth)
    return out


def low_df_moment_rows(result):
    """Rows that report a moment ratio for a cell at or below DF_NEEDS_SEEDS.

    Falls back to `walked_rows` when the artifact is not the probe-record
    shape, so an experiment that writes its results differently is covered
    rather than silently exempt.
    """
    rows = (result.get("value") or {}).get("rows")
    if not rows:
        rows = walked_rows(result)
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


def violation(name, result, available=(), results=None, current=None,
              audit_for=None):
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
    audit = (AUDIT_FOR if audit_for is None else audit_for).get(name)
    if audit and audit in available:
        if results is not None and current is not None:
            if audit_is_current(name, results, current, audit_for=audit_for):
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


def violations(results, current, audit_for=None):
    """{name: sentence} over a {name: result} mapping.

    `current` is current_constants(probes_module); it is required rather than
    optional because without it an audit's discharge cannot be checked, and a
    convenient default here is how the guard went quiet in the first place.
    """
    out = {}
    for name, result in sorted(results.items()):
        v = violation(name, result, available=set(results),
                      results=results, current=current, audit_for=audit_for)
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
    SATURATION_WINDOW is keyed by b1 as an int -- comes back with those keys as
    strings, {"1": ..., "22": ...}, and a naive != then reports every result stale
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


def audit_is_current(probe_name, results, current, audit_for=None):
    """An audit discharges its probe only while it agrees with the code.

    Without this, AUDIT_FOR excuses chi2_collapse on the strength of a
    collapse_spread computed under a gate nobody uses any more -- which is the
    state the tree is in as this is written.
    """
    audit = (AUDIT_FOR if audit_for is None else audit_for).get(probe_name)
    if not audit or audit not in results:
        return False
    return staleness(audit, results[audit], current) is None

