# Working agreement

Orientation is in [README.md](README.md); the spec is
[`design/specs/calibration-rig-spec.md`](design/specs/calibration-rig-spec.md) (v10).
This file is the short list of things that are easy to leave undone.

## The definition of done

```bash
python -m pytest tests/ -q
```

That suite is the definition of done, and `tests/test_load_bearing.py` is part
of it. Green means the code passes *and* the documentation that describes its
load-bearing regions still describes them.

## Before you say something is done: the manifest

[`.load-bearing/manifest.json`](.load-bearing/manifest.json) names the regions of
this repo that bear load, and what a correct account of each one has to include.
Each member is anchored to `path:start-end` plus a hash of exactly those lines,
so the manifest cannot quietly stop being about the code it names.

If a member is stale, the work is not done. There are two kinds and they have
different remedies, because they are different failures:

**MOVED** — the anchored bytes are intact, at new line numbers. Nothing said
about them stopped being true. Repair in bulk, no judgement needed:

```bash
python .load-bearing/refresh.py --relocate
```

**CHANGED** — the anchored bytes are gone, so the account may have gone with
them. Read the member's body against the diff the tool prints, edit the body if
what it says has moved, then attest it by name:

```bash
python .load-bearing/refresh.py --attest <member-id>
```

Attesting a changed member whose body you have not touched is **refused**. That
refusal is the point of the whole feature: a manifest that is fresh by hash and
wrong by meaning is worse than one that is openly stale. If the account
genuinely still holds — you renamed a local, the prose is unaffected — say so
explicitly and carry the reason into the commit message:

```bash
python .load-bearing/refresh.py --attest <id> --unchanged "renamed a local; the account holds"
```

## Before you say something is done: is there a new member?

If your change made a region load-bearing that was not before — a new gate, a
new oracle, a new thing that would be silently wrong — add a member for it.

**Nothing will tell you to.** The manifest is a curated map and not an
inventory, deliberately: a coverage rule here would be the permanently-red guard
this repo already declined once, for the README's layout tree. So this is the
one part of the process that is a judgement rather than a gate, and it is the
part that decays first if it is skipped.

`/load-bearing` (`.claude/skills/load-bearing/SKILL.md`) walks the format:
choosing anchors, writing a body, scoring the three criteria, and what belongs
in `aspects` rather than in prose.

## Two house rules that predate this file

- **Seed-varying quantities ship with their spread, never as a point** (spec
  §13.1). Mean, standard error and range over independent base seeds. A single
  run is a draw, not the quantity.
- **A cited number belongs to the registry.** Quote the claim id from
  [`evidence.json`](design/methodology/evidence/evidence.json), not a copy of its
  digits, so one number travels.
