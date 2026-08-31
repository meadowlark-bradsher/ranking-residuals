# A claim reproduces within a stated tolerance, and the index cannot go stale quietly

`design/methodology/evidence/verify.py` re-runs every claim in `evidence.json`
and compares it to what is stored. Exit status is 0 only if every claim
reproduces.

`drift(stored, fresh, tol)` flattens both sides to leaf paths and compares them
pairwise under the claim's own tolerance kind and value. It returns
`(ok, worst_path, worst_drift, shape_mismatches)`, and the failure output names
the claim, the stored value, the fresh value and the drift — so a reader can see
whether the conclusion moved or only the digits did.

Structural change is reported separately from numerical drift. Paths present on
only one side are collected into `mismatched` and reported as a set rather than
returned at the first one, because a restructured claim should be diagnosable in
a single run; when there are any, the function returns infinite drift and the
first mismatched path rather than a tolerance verdict on the surviving overlap.

`check_provenance` closes the second gap. `PROVENANCE.md` is generated, so
nothing keeps it current except regeneration, and an index that silently
describes a previous claim set is exactly the unverified artifact this directory
exists to prevent. It parses the claim ids out of the table and compares them
against the registry's keys, reporting both directions — ids missing from the
index and ids the index still lists after removal — rather than trusting that
whoever edited `generate.py` also re-ran it.
