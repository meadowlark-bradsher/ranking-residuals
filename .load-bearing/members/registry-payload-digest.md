# Is this the file the generator wrote?

`design/methodology/evidence/registry.py` holds the registry's payload digest:
a sha256 over the `claims` object alone, recorded as `meta.claims_digest` by
`generate.py` and checked by `verify.py` and `tests/test_evidence_integrity.py`.

It exists because two guards that look like they cover this do not.
`meta.source_fingerprint` hashes the *generator's source*, so it detects the code
changing meaning and is computed from the module rather than the artifact — a
registry edited by hand beside an unchanged generator round-trips clean. And the
tolerances are not a second line either: 13 of 33 claims are stochastic and are
compared only within a margin wide enough to absorb a different numpy, six of
them relative. Regeneration makes a stochastic claim true; a tolerance check
makes it within tolerance; the two coincide only when the file actually came from
a generator run, which makes a merge resolved inside the registry close to the
worst possible input for a tolerance check.

`canonical` serializes with sorted keys and compact separators, and dumps twice.
The first pass sends numpy scalars through `default=float` exactly as
`generate.py` does when writing; the second re-serializes the parsed result, so
the producer holding numpy types and a reader holding the floats that came back
out of the file canonicalize to the same bytes. Without the round trip the digest
would be written by one representation and checked against another.

`check` returns None on agreement and a sentence otherwise, and an **absent**
digest returns a sentence rather than None — an artifact with no digest is
unverifiable, not in agreement. That is the same reading `rig/provenance.py`
takes of a missing fingerprint.

The digest covers `claims` and never `meta`, because `generated` and `commit`
move when nothing measured has. A whole-file hash would go stale on every
regeneration and be ignored within a week.
