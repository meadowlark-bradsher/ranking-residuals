# Producer notes on `load-bearing/0.1`

What this repo pinned where the contract left a choice, and what it added on the
producer side that the contract does not describe. Written to be read back by
whoever revises the contract: everything here is a decision that wants either
ratifying into 0.1 or overruling.

The contract itself is vendored at [`CONTRACT.md`](CONTRACT.md) and the
consumer's pinned defaults at [`CONSUMER-PINS.md`](CONSUMER-PINS.md), so this
document no longer comments on a specification the repo does not contain. Where
they disagree, the contract wins.

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

**Whether `scores` is required when there is more than one criterion — pinned
by the consumer as P7, and this producer had it wrong.** The rule is per member:
a member that carries `scores` must score every declared criterion and every
component of any composite it scores; a member with no `scores` at all is valid
and is simply not orderable by criterion.

This repo originally read the contract's "required for every criterion if
present for any" across the whole manifest and rejected a partially scored one.
That was wrong, and wrong in the direction that matters. **A producer stricter
than the contract is not being conservative; it is refusing input the format
intends to be valid.** The consumer's fixture failing this validator was the
symptom, and it was read here as a fixture problem rather than as the bug it was.

Two things were available and neither was used. The contract's own Open list
says "currently optional per member", describing the status quo as the
per-member rule — so a strict reading of the field table makes it contradict the
Open item two sections down. And [`CONSUMER-PINS.md`](CONSUMER-PINS.md) P7 states
it outright; that document simply was not on this side until later. The first of
those is the one worth learning from: the answer was in the document already
held, and was missed by reading one table row without reconciling it against the
rest.

The rule now implemented is P7 as written. What survives of the original
argument is smaller and belongs to the author rather than the validator: scoring
every criterion keeps a composite ordering and its component orderings ranging
over the same members, so invariant 3's override compares like with like. That
is a reason to score, not a reason to reject.

**First producer.** `.claude/skills/load-bearing/SKILL.md` in this repo. The
repo owns the criteria (`correctness`, `provenance`, `trap-density`, and the
composite `identity`); the skill owns only the format, as the contract intends.

## Divergences from the reference consumer

Found by comparing implementations directly with the PREP session, not by
reading the contract. Both sides audited their own validator against the pins;
what follows is what survived that.

| | this producer | consumer pin | live? |
|---|---|---|---|
| trailing whitespace | kept | kept (P2) | agree |
| CRLF | folded to LF | folded to LF (P2) | agree |
| leading BOM | stripped | not handled (P2) | latent |
| bare CR | folded to LF | unmentioned by P2 | latent |

Both remaining divergences are latent, checked rather than assumed: every file
either side anchors today is clean LF with no BOM and no bare CR, so the two
implementations agree byte for byte on real input. They part company the moment
someone anchors a file an editor touched on Windows — and they will meet it as a
hash mismatch with no diff to explain it, which is the argument for pinning
rather than the merits, which are thin either way. Bare CR especially wants
pinning explicitly: P2 names only CRLF, and that silence is how this side came
to fold it without anyone deciding to.

**Three things previously recorded here as divergences were not.** `scores`
scope was this producer's error against P7, now conformed. Rejecting unknown
fields (P3) and refusing a `body_ref` that escapes (P6) were simply unimplemented
here — both in the *lax* direction, which is worse than being strict: a typo'd
key passed this validator silently and was rejected by the consumer, when the
producer is where a typo should die.

The pattern across all of them is the finding, and it is not that anyone was
careless. Two divergences trace to rules pinned in a document this side did not
have while the contract's own text said the matter was open. The rest trace to
reading one line of a specification without reconciling it against the rest of
the document. The second is harder to catch, because it produces a confident
justification rather than a visible gap — this document's first draft argued for
its wrong reading from a `.get` default in its own sort key.

Both remedies are contract-level: state the normalization rule in the contract
rather than the build order, and say per-member or across-manifest in the
sentence itself. A live conflict between P4 and invariant 1 is recorded in
[`CONSUMER-PINS.md`](CONSUMER-PINS.md) and belongs to the same revision.

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
- **Aspect scoping across composites — answered, and it was a bug.** Invariant 7
  says the judge sees aspects whose `criteria` include the active criterion, and
  the reference consumer implemented that literally: an aspect scoped to a
  component does *not* surface under a composite containing it. Its own manifest
  then showed a composite covering strictly less than either component, with one
  member getting no aspects at all and silently dropping to prose mode. The
  agreed fix is the union over the criterion and its declared components,
  transitively, which is what this repo already writes as if. Nothing here
  changes; 0.1 still has to say it, because the failure is silent — a member with
  no matching aspects does not error, it reads as fine.
- **Overlapping ranges in one file — answered: legal, and deliberate.** The
  consumer hashes each range independently, so two members over one file have
  independent freshness. Used here: `regime/preconditions` and
  `fit/derived-window` are adjacent regions of `rig/oracle.py`. Related and also
  confirmed: `blob` is never authoritative on its own, so a file edited outside a
  member's range leaves that member fresh.
