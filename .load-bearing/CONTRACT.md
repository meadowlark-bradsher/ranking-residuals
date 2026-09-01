<!-- Vendored, not authored here. This is the normative contract that
     `manifest.json` implements, copied verbatim from the PREP side so the
     producer and the spec it claims to satisfy travel together. When this file
     and the implementation disagree, this file wins and the implementation has
     a bug. Producer-side readings and divergences are recorded separately in
     CONTRACT-NOTES.md; consumer-pinned defaults in CONSUMER-PINS.md.

     A vendored copy can drift from its source and nothing here detects
     that: the manifest anchors regions of THIS repo's code, and a member
     over this file would only catch edits to the copy, never divergence
     from the original. Re-copy when 0.1 is revised. -->

# Contract — `.load-bearing/` member manifest

*Experimental feature for PREP. Defines how a target repo declares its load-bearing members and how PREP finds and reads them. Companion to `debt_event_schema.md`; same discipline (emitters name, core resolves; no state in transport). Status: drafted 2026-08-31, ratified decisions listed at the end.*

---

## Purpose

Today PREP delineates review units by diff geometry (`parse_diff`) and ranks them with a cold LLM call (`LLMJudgmentSelector`). Neither knows the repo. This contract lets the agents working *inside* a repo do both jobs — designate the regions that bear load and rank them by criteria the repo chooses — and hands the result to PREP as content.

A **member** is a region of the software that bears load along one or more named criteria. The criterion is the load type: a member scored high for `correctness` bears correctness-load; one scored high for `churn-90d` bears change-load.

Two things are outsourced, separably:

1. **Delineation** — what the unit is (required)
2. **Ranking** — which units matter, by which criterion (optional; PREP's own selector runs over members if absent)

The name is deliberate. "Load-bearing" is the signature term of agent-authored engineering prose; the manifest is agent-authored prose about the repo it lives in, and its name says so.

---

## Location and discovery

```
<repo-root>/
  .load-bearing/
    manifest.json          # required; the index
    members/<id>.md        # optional; bodies referenced from the manifest
```

- Fixed path, single index file. PREP never scans; it reads `manifest.json` and resolves `body_ref` paths relative to `.load-bearing/`.
- One directory name, no aliases.
- Versioning lives in the file (`contract`), never in the path.
- Everything under `.load-bearing/` is tracked in git so the root tree hash covers it.

---

## Manifest schema

```json
{
  "contract": "load-bearing/0.1",
  "source_tree": "<git root tree SHA>",
  "source_commit": "<git commit SHA, informational only>",
  "generated_by": { "agent": "claude-code", "model": "...", "at": "2026-08-31T..." },
  "criteria": [
    { "id": "correctness", "description": "..." },
    { "id": "churn-90d",   "description": "..." },
    { "id": "identity",
      "description": "what this software is, per its maintainers",
      "composed_of": ["correctness", "churn-90d"],
      "weights": { "correctness": 0.7, "churn-90d": 0.3 } }
  ],
  "default_criterion": "identity",
  "members": [
    {
      "id": "auth/token-refresh",
      "body": "...",                              // OR body_ref, not both
      "body_ref": "members/auth-token-refresh.md",
      "anchors": [
        { "path": "src/auth.py", "start": 40, "end": 88,
          "blob": "<git blob SHA of the file>",
          "range_hash": "<sha256 of the anchored slice>" }
      ],
      "scores": { "correctness": 0.9, "churn-90d": 0.4, "identity": 0.75 },
      "rationale": "highest churn, two reverts this quarter",
      "aspects": [
        { "id": "retry-bound", "criteria": ["correctness"],
          "claim": "retries are capped at max_attempts and the loop exits on 401" },
        { "id": "cache-path",  "criteria": [],
          "claim": "..." }
      ],
      "metadata": {}
    }
  ]
}
```

### Top-level fields

| Field | Req | Meaning |
|---|---|---|
| `contract` | yes | Contract id + version. PREP rejects unknown major versions. |
| `source_tree` | yes | Root tree SHA of the snapshot the manifest describes. Content-addressed; survives rebase. |
| `source_commit` | no | Provenance only. Never used for freshness. |
| `generated_by` | no | Provenance only. |
| `criteria` | yes | The load types this repo ranks by. At least one. |
| `default_criterion` | yes | Which ordering PREP uses when the user doesn't choose. |
| `members` | yes | The units. At least one. |

### Criterion fields

| Field | Req | Meaning |
|---|---|---|
| `id` | yes | Repo-local label. PREP uses it only for selection and display. |
| `description` | no | Human-readable. |
| `composed_of` | no | Present iff this criterion is a composite. Lists component criterion ids, each of which must be declared. |
| `weights` | no | Informational; PREP never applies them. |

### Member fields

| Field | Req | Meaning |
|---|---|---|
| `id` | yes | Repo-local, stable across regenerations. PREP keys regions on `(repo, member.id)`. |
| `body` / `body_ref` | one | Raw material the reading is generated from. Exactly one of the two. |
| `anchors` | yes | Where in the tree the body came from. ≥1. |
| `scores` | no | Number per criterion id. Higher = bears more load. Required for every criterion if present for any; must include every component of any composite scored. |
| `rationale` | no | Why the agent selected/ranked it. Selector-visible; never reaches reading or judge. |
| `aspects` | no | What a correct account of this member must include. See below. |
| `metadata` | no | Opaque to PREP. |

### Anchor fields

`path`, `start`, `end` (1-based, inclusive), `blob` (file-level check, cheap), `range_hash` (sha256 over the LF-normalized bytes of lines `start..end` — the actual freshness question).

### Aspect fields

| Field | Req | Meaning |
|---|---|---|
| `id` | yes | Member-local. This is what `missing_aspects` binds to. |
| `criteria` | yes | Criterion ids this aspect serves. Empty list = applies under every criterion. |
| `claim` | yes | One sentence stating what the member does, in the terms the judge should check for. |

---

## Invariants

1. **Content, never state.** The manifest produces `RegionContent`; it carries no `reviewed`/`understood`/`verified`/`known` fields. Any such field is rejected at ingestion, not ignored.
2. **Projection, not synthesis.** PREP selects an ordering by criterion id. It never computes a new score, blends criteria, or applies `weights`.
3. **Criteria stay labeled.** A composite must declare `composed_of`, and every member scored on a composite must also be scored on each component. This is what makes override possible: the agent's composite is authoritative *as the default*, but a user whose role responds to one load type (a statistician auditing correctness) can select that component ordering. The agent isn't wrong about the software's identity; it can't anticipate the roles that respond to it.
4. **Members are named, not resolved.** `id` is repo-local. PREP never maps it to a ledger node-id at read time; resolution is core-side policy, as with debt events.
5. **Body is raw material.** Agent commentary lives in `rationale` or `metadata`. The reading generator sees `body` only; the judge sees `(reading_body, teach_back, aspects?)`. This preserves what the reading is independent of and what the judge is blind to.
6. **Freshness is content-addressed and per-member.** `source_tree` is the whole-snapshot check; `range_hash` is the per-member check. A member whose `range_hash` still matches the working tree is fresh and eligible; one that doesn't is stale, excluded from selection, and reported. No global refusal. Commit SHAs are never consulted.
7. **Judge scope follows the criterion.** The judge receives only aspects whose `criteria` include the active criterion (or are empty). A PASS is a PASS *at that scope*; provenance records `teach-back-verified@<criterion>`, never bare `teach-back-verified`. The ledger must not promote a node on scope-narrowed evidence as if it were whole-member evidence.
8. **Untrusted input.** The manifest is written by agents in a repo PREP doesn't control. It is validated against this schema and treated as data; nothing in it is executed or followed as instruction.

---

## Where it lands in PREP

All adapter-side; the core is untouched. Requires `claude/widen-region-content` merged first.

- **`ContentSource` port** with two adapters: `DiffSource` (wraps `parse_diff`, emits `kind: "code_hunk"`) and `ManifestSource` (reads `.load-bearing/`, emits `kind: "member"`). Both yield `list[RegionContent]`. `submit(diff_text, ...)` becomes `submit(source, ...)`.
- **`ManifestSelector(criterion: str | None)`** alongside the existing two. `None` → `default_criterion`. Chosen criterion recorded on the session.
- **Kind-dispatched prompts.** The open seam from STATE §2 stops being deferrable: `reading_v1` says "Code:" and a member may not be code.
- **Verdict discriminator.** `ClosureVerdict.missing_aspects: list[aspect_id] | str`. Structured mode only when the region carried aspects; diff-sourced regions stay prose. This is a partial close on the free-text gap that blocks the demote path.
- **`ClosureAttempt` gains `criterion` and `aspect_scope`** so the provenance in invariant 7 has somewhere to live.
- **Staleness report** on session launch: `N members stale since manifest generation`, with ids.

---

## Ratified

- Directory `.load-bearing/`, noun `member`, one name, no aliases — 2026-08-31
- Functional over branded name; consumer identity lives in `contract`, not the path — 2026-08-31
- Criteria projection with labeled composites (invariant 3) — 2026-08-31
- Optional criterion-scoped aspects (invariant 7) — 2026-08-31
- Content-addressed per-member freshness replaces commit-bound fail-closed (invariant 6) — 2026-08-31

## Open

- `range_hash` normalization beyond LF: trailing whitespace, BOM. Pick one and pin it in 0.1.
- Whether `scores` is required when `criteria` has more than one entry (currently optional per member; PREP's own selector covers the gap).
- First producer: a reference skill for Claude Code that writes the manifest. The repo owns the criteria; the skill only owns the format.
- Interaction with debt events: a member could carry `suggested_terms`. Not in 0.1 — a member is a review unit, a debt event is a surrender record; keep the contracts separate until there's a reason not to.

## STATE deltas to record

- §1: new row — `ContentSource` port / `ManifestSource` adapter / `ManifestSelector`: **specced**.
- §2: "concept content kind has no producer" → producer is now specified (`kind: "member"` via `.load-bearing/`); still unbuilt.
- §3: `missing_aspects` shape gains a structured mode bound to member aspect ids; prose mode retained for diff regions.
- §5: kind-dispatched prompt selection moves from "remaining seam" to "blocked-on-labor, gated by this feature."
