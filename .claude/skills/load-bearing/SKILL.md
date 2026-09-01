---
name: load-bearing
description: Write, refresh, or repair a member in .load-bearing/manifest.json — the manifest of regions in this repo that bear load. Use when tests/test_load_bearing.py reports a MOVED, CHANGED or MISSING member; when a change has made some region load-bearing that was not before (a new gate, oracle, refusal, or fingerprint); when asked to add or score a member or write its aspects; and as the last step before calling work done, to check whether the regions you touched are described by a member whose account has now moved.
---

# Load-bearing members

`.load-bearing/manifest.json` is agent-authored prose about this repo, in a
format PREP reads. A **member** is a region of the software that bears load
along one or more named criteria, anchored to `path:start-end` plus a hash of
exactly those lines.

The full contract is `load-bearing/0.1`. The decisions this repo pinned where
the contract left them open are in
[`.load-bearing/CONTRACT-NOTES.md`](../../../.load-bearing/CONTRACT-NOTES.md).

## The three commands

```bash
python .load-bearing/verify.py                     # what is stale, and why
python .load-bearing/refresh.py --relocate         # repair MOVED, in bulk
python .load-bearing/refresh.py --attest <id>      # re-hash CHANGED, one at a time
```

`verify.py --criterion <id>` prints the ordering PREP would take under that
criterion. Run it against `identity` and against `trap-density` to see that they
genuinely differ — that difference is what invariant 3 exists to preserve.

## Repairing a stale member

**MOVED.** The bytes are intact and the line numbers slid. `--relocate`, commit,
done. Do not read anything; nothing changed.

**CHANGED.** The anchored code is different.

1. Run `refresh.py --attest <id>` once and read the diff it prints. It will
   refuse to write; that is expected on the first run.
2. Open the member's body (`.load-bearing/members/<slug>.md`) and read it
   *against that diff*. The question is narrow: **does this body still describe
   this code?** Not "is the body good" — only whether the change moved anything
   it says.
3. If it did, edit the body, then re-run `--attest <id>`. It will write.
4. If it genuinely did not — a renamed local, a reordered argument, a comment —
   re-run with `--unchanged "<why>"`. The reason goes into your commit message,
   not into the manifest.

Do not reach for `--unchanged` to get past a refusal quickly. It is the escape
hatch for edits that changed bytes and no meaning, and using it otherwise
converts this whole feature into a rehash.

**MISSING.** The file is gone. Repoint the anchor if the region moved to another
file, or delete the member if the region no longer exists. Deleting a member is
a normal outcome and does not need ceremony.

## Adding a member

Nothing prompts you to do this. Ask, after a change: *is there now a region here
that would be silently wrong?* If yes, it wants a member.

Good candidates in this repo look like the ones already there: a gate that
refuses (`regime/preconditions`), a derived quantity that was previously a
constant (`fit/derived-window`), a guard separating ordinary loss from
destruction (`emit/collapse-guard`), a mechanism that makes results attributable
(`provenance/semantic-fingerprint`).

Poor candidates: a module because it is large, a function because it is new,
anything whose failure a test would catch loudly and immediately.

### Anchors

Anchor the region, not the file. One member may carry several anchors, and
should when its claim spans them — `instrument/unforked` anchors both copies of
`hodge.py`, because the claim *is* their byte-identity, and either one drifting
alone is the event worth catching.

Pick boundaries that are stable and meaningful: a whole function including its
docstring, a block of constants with the comment that says what they are. Prefer
a slightly larger region with a clean edge over a tight one that will be
re-anchored on every edit. Anchoring from line 1 pulls in the module docstring,
which is right when that docstring carries the measured figures the code
depends on (`fit/floor-ols` does this).

### The body

`.load-bearing/members/<slug>.md`, referenced by `body_ref`. This is **raw
material**, not commentary: what the region does and why it is shaped that way,
in terms someone could check against the code. PREP generates a reading from
this body alone.

Write what the code establishes, with its numbers. "The window is
`c_oracle / (rho * floor_target)`, and on `filling='empty'` the same graph has
`b1 = 20` and `c ≈ 160`, so `k = 64` recovers 0.016 against a true 0.090" is
body. "This is one of the three findings the build had to fix" is `rationale` —
it is about the selection, not about the code.

Keep it to what you have actually read. A body that describes intent you inferred
is the thing this manifest exists to prevent.

### Scores

Three criteria, plus the composite. Score all four, always — a member missing a
score sorts at zero, ranked last by silence rather than by judgement, and
validation rejects it.

| criterion | the question it asks |
|---|---|
| `correctness` | If this is wrong, how far does the error travel before anything catches it? |
| `provenance` | Does this make a result attributable to the code that produced it? |
| `trap-density` | Does this exist to refuse — a measured breakpoint that must fail loudly? |

`identity` is the composite, weighted `0.5 / 0.3 / 0.2`. Compute it yourself and
write it in. PREP never applies the weights (invariant 2) — they document how you
arrived at the number, and the number is what gets sorted.

### Aspects

An aspect is one sentence stating what a correct account **must** include, in
terms a judge could check. `criteria` scopes it: list the criterion ids it
serves, or `[]` for "applies under every criterion."

Aspects are where the checkable claims go. If you find yourself wanting the body
to insist on something, that is an aspect:

```json
{ "id": "rho-has-no-default", "criteria": ["trap-density", "provenance"],
  "claim": "rho is required with no default because it is a shipped config field, and the docstring records the v6-to-v7 incident where a default here went stale unnoticed." }
```

Two to four per member is the working range. One is usually a body sentence
promoted without cause; six is usually the body restated.

### Then

```bash
python .load-bearing/refresh.py --stamp   # fills blob, hashes, source_tree
python -m pytest tests/test_load_bearing.py -q
```

A new member's anchors need their hashes filled. `--stamp` alone does not do it;
run `--attest <new-id>` once, which will write because the body is new.

## What not to put in a member

Anything about a *reader*: `reviewed`, `understood`, `verified`, `known`,
`confidence`. Validation rejects them at ingestion rather than ignoring them,
including nested inside `metadata`. The manifest is content; whether anyone has
read it is PREP's business and lives on PREP's side.
