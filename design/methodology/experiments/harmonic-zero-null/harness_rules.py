"""This experiment's binding of the shared harness rules.

THE RULES MOVED TO rig/harness.py, and the argument is the one this file
already made for rule 3, one rule over. Rules 1 and 2 lived here and worked
here -- on the nine artifacts this directory owns. The repository has
seventeen result artifacts across three experiments plus two written outside
`experiments/` entirely, and on those eight there was no rule at all. That is
not a weaker rule; on them it is no rule, and it reads exactly like a green
one.

It cost something real. boundary_report.json carries four moment ratios at
b1 = 1 with no base-seed replication -- the exact hazard rule 1 exists for --
and no rule had ever read it, because the machinery sat in a directory it is
not written from.

WHAT STAYED HERE is the part that is genuinely this experiment's: AUDIT_FOR,
the registry of which probe is discharged by which audit. That is a fact about
these probes, not about the rule, so the shared module takes it as an argument
and this file binds it. Callers keep one name for the rule -- `violations`
here still means "violations under THIS experiment's audits".
"""

from __future__ import annotations

from rig.harness import (                                           # noqa: F401
    DF_NEEDS_SEEDS,
    MIN_BASE_SEEDS,
    MOMENT_PREFIXES,
    MOMENT_SUBSTRINGS,
    NESTED_KEYS_MAX_DEPTH,
    NOT_MOMENTS,
    carries_moments,
    comparable,
    current_constants,
    is_moment_key,
    is_seeded,
    low_df_moment_rows,
    recorded_constants,
    row_dfs,
    staleness,
    stale,
    uncheckable,
    walked_rows,
)
from rig import harness as _h

# probe -> the audit that reseeds its grid. An audit discharges the rule for the
# probe it names, which is why AUDITS is a separate registry rather than a tag.
# This is the one genuinely experiment-specific fact in the rule.
AUDIT_FOR = {"chi2_collapse": "collapse_spread"}


def violation(name, result, available=(), results=None, current=None):
    """This experiment's rule 1. See rig.harness.violation."""
    return _h.violation(name, result, available=available, results=results,
                        current=current, audit_for=AUDIT_FOR)


def violations(results, current):
    """{name: sentence} under THIS experiment's audits. See rig.harness.violations."""
    return _h.violations(results, current, audit_for=AUDIT_FOR)


def audit_is_current(probe_name, results, current):
    """See rig.harness.audit_is_current."""
    return _h.audit_is_current(probe_name, results, current, audit_for=AUDIT_FOR)


# ---------------------------------------------------------------------------
# THIRD RULE: a result may not be read as current if the CODE that produced it
# has changed meaning, whether or not any named constant moved.
#
# Rule 2 watches gate constants. It went silent when closes_at() was changed from
# testing var_ratio alone to testing both moments -- b1_1_closes_at moved 0.05 ->
# 0.03, a real change to a shipped number, and nothing mismatched because
# b1_one_boundary records only alpha. The change travelled through a PREDICATE,
# which constants cannot see.
#
# THE MACHINERY NOW LIVES IN rig/provenance.py. It was written here and it worked
# here -- on the nine artifacts this directory owns. The repository has nineteen,
# and the other ten wrote their JSON with a bare write_text and carried no
# fingerprint at all, so nothing could date them against the code in either
# direction. A rule that covers half the artifacts and is silent on the rest is
# not a weaker rule; on those ten it is no rule, and it reads exactly like a
# green one. Nothing about hashing source was specific to this experiment, so it
# moved to the shared layer every experiment already imports and every writer
# now stamps through it.
#
# Re-exported rather than re-implemented, so this module's callers -- and the
# tests that read them -- keep one name for the rule.

from rig.provenance import (                                       # noqa: E402
    FINGERPRINT_KEY,
    _module_level,
    _normalised_dump,
    _referenced,
    _sibling_modules,
    _strip_docstrings,
    module_fingerprint,
    recorded_fingerprint,
    semantic_fingerprint,
    stamp,
)
from rig.provenance import mismatch as fingerprint_mismatch        # noqa: E402
from rig.provenance import unfingerprinted                         # noqa: E402
