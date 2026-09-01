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

## P4 conflicts with invariant 1, and the conflict is live

P4 scopes state-field rejection to "any depth **outside** `metadata`". Invariant 1
carries no such qualifier: a manifest "carries no `reviewed`/`understood`/
`verified`/`known` fields. Any such field is rejected at ingestion, not ignored."

Measured on the consumer side, which is what makes this worth recording rather
than arguing: because P3 closes every object in the schema, every state word is
already rejected as an unknown field wherever it can appear. P4 therefore changes
only the error message and never the outcome — **except inside `metadata`, the one
location it exempts, where nothing fires at all.** So P4 is redundant everywhere
it applies and disabled in the only place it would matter, and the exempted
location is the whole reachable surface.

This producer implements invariant 1 rather than P4: state keys are rejected
inside `metadata` too. The reasoning is that "opaque" is a claim about PREP not
*interpreting* metadata — the reading and the judge never see it — not about
declining to *validate* it at ingestion, and metadata is exactly where a state
field ends up when a producer is told only "not at the top level."

Both sides now read it the same way and neither has changed it: it is a contract
question, the contract wins by the build order's own rule, and 0.1 should either
delete P4's carve-out or add the qualifier to invariant 1.

The word list is a smaller version of the same thing. This side carries
`confidence` and `mastery`; P4 carries `mastered`. After P3 the difference only
decides which error message a producer sees, so it is worth pinning for message
quality and is not load-bearing.
