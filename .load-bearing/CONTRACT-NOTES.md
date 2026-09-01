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

## Divergences from the reference consumer — audited 2026-09-01

**This section said "there are none left". That was wrong when it was written,
and the way it was wrong is worth more than the row it missed.** The `scores`
row below records P7 scoping scores per member — which made a scoreless member
legal, which made `verify.py`'s `.get(cid, 0.0)` ordering fallback reachable for
the first time. The reference consumer filters such members; this side ranked
them last at `0.00`, asserting a score the manifest does not make. So the PR that
closed the list and the PR that reopened it were in the same merge train.

Compounding it: the justification for that fallback had already been struck one
PR earlier, on the correct grounds that the validator made it unreachable. The
same author then removed that validator rule without returning to the sentence
struck because of it. **A closure claim is a snapshot, and the change that
invalidates it may already be merged.** Fixed since; the ordering now excludes
unscored members and names them, pinned by
`test_a_scoreless_member_is_not_ranked_at_zero`.

Both sides audited their own validator against the pins, and every difference
that survived that audit has been decided — as of this writing, and no longer
asserted as permanent.

| | this producer | outcome |
|---|---|---|
| trailing whitespace | kept | agreed from the start |
| CRLF | folded to LF | agreed from the start |
| leading BOM | stripped | **ratified**; the consumer adopts it |
| bare CR | folded to LF | **ratified**, and now pinned explicitly |
| state keys in `metadata` | rejected | **ratified**; P4's carve-out dropped |
| `scores` scope | across the manifest | **this side was wrong**; now per member |
| unknown fields (P3) | not checked | **this side was lax**; now closed |
| `body_ref` escape (P6) | not checked | **this side was lax**; now checked |

The four ratified rows landed on this producer's behaviour and the consumer
changes. That is not a scoreboard worth keeping — the useful part is the shape
of how each one arose, because they were not the same kind of mistake and only
one kind was avoidable by being more careful.

**Two came from pins held in a document this side did not have** while the
contract's own text said the matter was open. Nobody was careless; the
information was not present. The remedy is that the rule belongs in the contract
rather than in a build order, which is now true of normalization.

**Three came from reading one line without reconciling it against the rest of
the document.** `scores` scope is the clearest: the contract's Open list already
said "currently optional per member", two sections below the field table that
was read strictly. P3 and P6 are the same failure with nothing to argue about —
pins that were simply not implemented, both in the lax direction, so a typo'd
key passed here and was rejected downstream.

That second kind is the harder one, and it does not announce itself. It produces
a confident justification instead of a visible gap: this document's first draft
argued for its wrong reading of `scores` from a `.get` default in its own sort
key, and the argument read well. None of the three was caught by the manifest
gate, which checks that prose stays attached to code and cannot check prose
against prose.

**One was decided by measurement rather than argument**, and is the exception
worth imitating. Both sides believed P4's `metadata` carve-out was wrong on the
merits, which would ordinarily be two opinions. Instead each validator was
probed: because P3 closes every object, every state word is already rejected as
an unknown field wherever it can appear, so P4 changed only the error message and
never the outcome — except inside `metadata`, the one location it exempted. A
rule redundant everywhere it applies and disabled where it would matter is not a
narrower rule but an absent one. Reproduced independently in both
implementations, which is what settled it.

The decisions themselves are recorded in
[`CONSUMER-PINS.md`](CONSUMER-PINS.md); [`CONTRACT.md`](CONTRACT.md) is a
verbatim copy that predates the revision and its header says so.

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
- **Aspect scoping across composites — decided 2026-09-01: transitive union.**
  An aspect scoped to a component criterion surfaces under a composite
  containing it, transitively. Read literally, invariant 7 made a composite
  cover strictly *less* than either of its components, and a member could get no
  aspects at all under the default criterion and drop silently to prose mode.
  Consumer-side; nothing changes here, which already authors aspects as if this
  were true. The contract text still needs it written down, because the failure
  it prevents is silent — a member with no matching aspects does not error.
- **Overlapping ranges in one file — answered: legal, and deliberate.** The
  consumer hashes each range independently, so two members over one file have
  independent freshness. Used here: `regime/preconditions` and
  `fit/derived-window` are adjacent regions of `rig/oracle.py`. Related and also
  confirmed: `blob` is never authoritative on its own, so a file edited outside a
  member's range leaves that member fresh.
