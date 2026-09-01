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
carry a score for every declared criterion. Validation rejects a partially
scored manifest.

The argument is that it forces an author to make the judgement rather than omit
it, and that it keeps a composite ordering and its component orderings ranging
over the same members, so the override invariant 3 exists to protect compares
like with like.

**A justification given here in the first draft has been struck, and the reason
is worth more than the sentence was.** It read: an unscored member "sorts at zero
under every criterion — ranked last by silence rather than by judgement." That
describes `verify.py`'s ordering, whose sort key defaults a missing score to
`0.0`, and it is unreachable — `lb.validate` rejects a partially scored manifest
before any ordering runs. So the claim was circular: a failure that exists only
without the rule, in an implementation that has the rule, generalised to the
format as though it were a property of the contract. It is a property of one
`.get` default.

Struck rather than quietly deleted because this document's whole job is to be
read back by whoever revises 0.1, and a wrong argument for the right rule is the
kind of thing that gets weighed.

**First producer.** `.claude/skills/load-bearing/SKILL.md` in this repo. The
repo owns the criteria (`correctness`, `provenance`, `trap-density`, and the
composite `identity`); the skill owns only the format, as the contract intends.

## Divergences from the reference consumer

Found by comparing implementations with the PREP session directly, not by
reading the contract. All three are places where 0.1 does not say, so both sides
resolved it and neither was careless.

| | this producer | reference consumer | live? |
|---|---|---|---|
| leading BOM | stripped | not handled | latent |
| bare CR | folded to LF | not handled | latent |
| `scores` scope | across the manifest | per member | **yes** |

The two hash rules are latent because every file either side currently anchors
is clean LF with no BOM and no bare CR, checked on both sides rather than
assumed — so the two implementations agree byte for byte on real input today.
They would diverge the moment anyone anchors a file an editor has touched on
Windows.

`scores` is live. The consumer's `ManifestSelector` filters unscored members out
rather than ranking them, so a partially scored manifest that this validator
rejects is one it accepts. The direction is safe — this producer is stricter, so
anything it emits the consumer will read — but a manifest written against the
consumer's reading fails here.

**What the three have in common is the finding.** Two of them trace to rules
pinned in a build document this side never had, while the contract's own text
said the matter was open. The third is worse: the sentence in 0.1 is genuinely
ambiguous between per-member and across-manifest, and each side disambiguated it
toward whatever it had already built, then wrote a justification describing its
own code — the consumer's from its selector, this one's from a sort key. That
produces confident reasoning on both sides instead of a visible gap, which is
harder to catch than a missing pin.

The remedy is the same for all three and it is a contract change, not a producer
one: 0.1 should state these rules in its own text rather than leave them to be
inferred, and the `scores` sentence should say per-member or across-manifest in
so many words.

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
