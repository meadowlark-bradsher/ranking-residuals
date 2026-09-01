<!-- Excerpt, not authored here. Section 1 of PREP's build order for the 0.1
     slice, copied because these defaults are normative for this producer and
     because their absence on this side caused three divergences before anyone
     noticed. The rest of that document is PREP-internal (module paths, step
     ordering, its own test counts) and is deliberately not copied — it would go
     stale here and it governs work this repo does not do. -->

# Consumer-pinned defaults (`load-bearing/0.1`)

The contract leaves several things open and says to pin them. These are the pins,
from the consumer side. **The contract wins on any disagreement** — that
precedence is the build order's own rule, and where this excerpt and
[`CONTRACT.md`](CONTRACT.md) conflict, the conflict is reported rather than
resolved silently. One such conflict is live and recorded below.

**P2 and P4 below were superseded on 2026-09-01** and the table is the text as
excerpted, not as decided. See "Decided since this excerpt" at the end.

| # | Decision | Value in 0.1 |
|---|---|---|
| P1 | Where PREP reads a working tree | **CLI only.** `ManifestSource` needs filesystem access; the web route keeps its pasted-diff path and does not learn about manifests in 0.1. |
| P2 | `range_hash` | sha256 over the bytes of lines `start..end` inclusive (1-based), after normalizing CRLF→LF. No trailing-whitespace stripping, no BOM handling. PREP always recomputes and compares; `blob` is an optional short-circuit, never authoritative on its own. |
| P3 | Unknown fields | Reject anywhere in the manifest. `metadata` is the only opaque bag. |
| P4 | State-shaped fields | Reject by name at any depth outside `metadata`: `reviewed`, `understood`, `verified`, `known`, `mastered`, `status`. Case-insensitive. Rejection is an error with the field path, not a warning. |
| P5 | Structured verdict | When the region carries aspects, `missing_aspects` is a list of aspect ids. On `FAIL` it must be non-empty and a subset of the aspect ids the judge was given. |
| P6 | Body/body_ref | Exactly one. Both or neither → reject. `body_ref` resolves relative to `.load-bearing/` and must not escape it. |
| P7 | Scores | Optional per member. If any member has `scores`, it must score every declared criterion, and every composite's `composed_of` components must be declared criteria. Members with no `scores` are eligible only under PREP's own selectors, not `ManifestSelector`. |
| P8 | Stale members | Excluded from selection, listed in the launch output by id. Never a global refusal. |

Also normative and stated elsewhere in that document: **applying `weights` is out
of scope. Never.** That matches invariant 2.

## What this producer does with them

P1 and P5 are consumer-side and this repo implements neither. P8 is where the two
sides deliberately differ — see "Producer and consumer answer different questions
about staleness" in [`CONTRACT-NOTES.md`](CONTRACT-NOTES.md).

P2, P3, P6 and P7 govern `lb.py`. P3, P6 and P7 are implemented as written. P2 is
implemented with two deliberate additions, recorded as divergences in the notes:
this side strips a leading BOM and folds a bare CR, and P2 does neither. Both are
latent — no file either side anchors today has a BOM or a bare CR — and this
producer will conform to whatever 0.1 states.

## Decided since this excerpt — 2026-09-01

All three open questions were resolved by the contract's owner, and all three
landed on this producer's existing behaviour. **No code changed here**; what
changed is that these stop being divergences and become the rule.

**P2 normalization — this side's reading adopted.** Strip a leading BOM, fold
bare CR to LF along with CRLF, keep trailing whitespace. The two remaining
divergences recorded in [`CONTRACT-NOTES.md`](CONTRACT-NOTES.md) are closed by
this; the consumer changes rather than the producer. Bare CR is now pinned
explicitly, which was the specific silence that let the two implementations part
company without either side deciding anything.

**P4's carve-out dropped — invariant 1 stands unqualified.** State-shaped keys
are rejected inside `metadata` too. This is what this producer already did, and
the measurement is what settled it rather than either side's argument: because
P3 closes every object in the schema, every state word is already rejected as an
unknown field wherever it can appear, so P4 changed only the error message and
never the outcome — except inside `metadata`, the one location it exempted,
which is the entire reachable surface. A rule redundant everywhere it applies
and disabled where it would matter is not a narrower rule, it is an absent one.
Reproduced independently in both validators before the decision.

"Opaque" is therefore settled as a claim about PREP not *interpreting* metadata
— the reading generator and the judge never see it — and not about declining to
*validate* it at ingestion.

**Composite aspect scope — transitive union.** An aspect scoped to a component
criterion does surface under a composite containing it, transitively. This is
consumer-side and changes nothing in this repo, which already authors aspects as
if it were true. It closes a real defect: read literally, invariant 7 made a
composite cover strictly *less* than either of its components, and a member
could end up with no aspects at all under the default criterion and drop
silently to prose mode.

The contract text itself has not been revised yet, so [`CONTRACT.md`](CONTRACT.md)
still lists the first two as open. Its header records the gap.
