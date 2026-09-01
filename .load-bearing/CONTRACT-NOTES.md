# Producer notes on `load-bearing/0.1`

What this repo pinned where the contract left a choice, and what it added on the
producer side that the contract does not describe. Written to be read back by
whoever revises the contract: everything here is a decision that wants either
ratifying into 0.1 or overruling.

## Closed from the contract's Open list

**`range_hash` normalization.** The contract asks for one choice, pinned. This
repo hashes the LF-joined slice with every line terminated, after:

| input | treated as |
|---|---|
| leading UTF-8 BOM | stripped — an editor adding one has not changed the code |
| CRLF, CR | folded to LF — a line ending is a checkout artifact |
| trailing whitespace | **kept** — a real edit to a real byte |
| missing final newline at EOF | invisible — a property of the file, not of the region |

Trailing whitespace is the only one that could go either way. It is kept because
this repo's central instrument is validated by `shasum` agreeing exactly, and a
hash that forgives whitespace answers a slightly different question than the one
it is being asked. `tests/test_load_bearing.py` pins all four so a later change
is a visible decision and not a silent reinterpretation of every hash already
written.

**Whether `scores` is required when there is more than one criterion.** Read
strictly, across the manifest: if any member carries `scores`, every member must
carry a score for every declared criterion. The loose reading lets a member with
no scores sit beside members that have them, where it sorts at zero under every
criterion — ranked last by silence rather than by judgement. Validation rejects
it.

**First producer.** `.claude/skills/load-bearing/SKILL.md` in this repo. The
repo owns the criteria (`correctness`, `provenance`, `trap-density`, and the
composite `identity`); the skill owns only the format, as the contract intends.

## Added on the producer side

The contract describes how PREP *reads* a manifest. It does not describe how the
repo keeps one true, and that turned out to need one distinction the contract
does not make.

**MOVED and CHANGED are different failures.** `range_hash` answers one question —
does the anchored slice still hash to this? — but a mismatch has two causes with
nothing in common:

- the bytes are intact and the line numbers slid, because something above them
  grew. Nothing said about that region stopped being true.
- the bytes are gone. The account may have gone with them.

Collapsing them gives a single remedy, and the only available single remedy is a
rehash. A command that re-blesses every drifted member at once produces a
manifest that is **fresh by hash and wrong by meaning**, which is worse than an
openly stale one — a stale manifest at least announces itself, and PREP's
invariant 6 is built to handle it.

So the producer tooling splits them. `refresh.py --relocate` repairs MOVED in
bulk and requires no judgement, because an equal-length window elsewhere in the
file hashing to the recorded value *is* proof that nothing changed.
`refresh.py --attest <id>` handles CHANGED one member at a time, prints the diff
of the anchored region, and refuses when the member's body has not been edited
in the working tree. The refusal takes an explicit `--unchanged "<reason>"`,
because renaming a local changes bytes and leaves every word true; the reason
goes to stdout for the commit message and never into the manifest, since a fact
about an edit is what commit messages are for and reader-facing state is what
invariant 1 keeps out of this file.

This costs the contract nothing. It is entirely producer-side, and PREP sees only
a manifest whose `range_hash` values are current.

**Producer and consumer answer different questions about staleness.** Invariant 6
is right for PREP: a stale member is excluded from selection and reported, and
there is no global refusal. But the same tolerance in the producing repo is what
lets the manifest rot — so here, a stale member fails `pytest`, and the suite is
this repo's definition of done. Tolerant on read, strict on write. Worth stating
in the contract, because a producer that inherits invariant 6's tolerance will
inherit nothing that keeps the file honest.

**`source_tree` is never a gate here.** It is one commit out of date the instant
the manifest is committed, which is exactly why it cannot gate anything.
`verify.py` prints it as a note. Freshness is per-member, always.

## What counts as coverage

`members[].anchors[].path` and nothing else. A file named in a body, a
`rationale`, or a `metadata` value is prose or is opaque to PREP; neither is
compared against anything, and neither makes that file covered.

This is worth stating because it has already been got wrong twice, in both cases
by scanning a serialized member for a filename and matching one that appeared in
its prose. `evidence/tolerance-and-drift` is the member that invites it: its body
discusses `evidence.json` and its `metadata.registry` names the path, but its one
anchor is `design/methodology/evidence/verify.py:84-119`. The registry's numbers
are not anchored by anything here.

The error runs in the dangerous direction. Believing the manifest covers a file
invites skipping a guard that was never present — concluding a stale registry
would be caught by the gate, when what actually guards it is
`test_source_fingerprint` round-tripping the generator's semantic fingerprint and
`verify.py` re-running claims. So `verify.py` prints the anchored-file inventory
on every run and `lb.anchored_paths` makes it a function, rather than leaving it
to be inferred from the JSON.

A member is documentation. The gate checks that documentation stays attached to
the code it describes. It does not read a value, re-run a computation, or assert
anything about behaviour, and no member should be written as though it did.

## Left open

- **`suggested_terms` on a member.** Not adopted, per the contract's own reading:
  a member is a review unit and a debt event is a surrender record.
- **Aspect scoping across composites.** Invariant 7 says the judge sees aspects
  whose `criteria` include the active criterion. It does not say what happens
  when the active criterion is a *composite*: does an aspect scoped to
  `correctness` surface under `identity`, which is composed of it? This repo
  writes aspects as if the answer is yes, and nothing here depends on it, but
  0.1 should say.
- **Two members anchoring overlapping ranges in one file.** Allowed here and used
  (`regime/preconditions` and `fit/derived-window` are adjacent regions of
  `rig/oracle.py`). Non-overlapping in practice; the contract does not say
  whether overlap is legal.
