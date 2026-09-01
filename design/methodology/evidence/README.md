# evidence/

The data behind every number in the papers, and the machinery to check it.

| file | what it is |
|---|---|
| `generate.py` | rebuilds every cited quantity from the rig (~8 min) |
| `evidence.json` | the data: one record per claim, with its tolerance |
| `verify.py` | re-runs and checks each claim against `evidence.json` |
| `PROVENANCE.md` | generated index: claim → where cited → tolerance → test |
| `registry.py` | the payload digest: is this the file the generator wrote? |

```bash
python verify.py --fast   # identities and closed forms, seconds
python verify.py          # everything, ~8 min unloaded (measured 14:49 under load)
```

`verify.py` redoes the same computation as `generate.py`, so the two cost the
same; both were measured on this machine at 8:11 (generate, 350% CPU) and 14:49
(verify, 201% CPU) -- the difference is contention, not extra work.

Most of that time is `residual_exact`, which computes exact binomial
energies over 20 base seeds. It is slow because it is exact: the quantity it
measures has a standard error of 0.002 pt, some forty times narrower than the
sampled figure it is there to explain, and that resolution is the whole point.
`generate.py --fast` deliberately refuses to write `evidence.json` -- a partial
registry that verifies clean is worse than no registry.

`meta.claims_digest` is a hash of the `claims` payload, written by `generate.py`
and checked by `verify.py` and `tests/test_evidence_integrity.py`. It answers what
neither the fingerprint nor the tolerances can: `meta.source_fingerprint` hashes
this directory's *generator source*, so a registry edited by hand beside an
unchanged generator round-trips clean, and the 13 stochastic claims are compared
only within a tolerance wide enough to absorb a different numpy -- which a merge
resolved inside the registry usually is. Regeneration makes a stochastic claim
true; a tolerance check makes it within tolerance; the two coincide only when the
file came from a generator run. The digest covers `claims` alone, never `meta`,
so a new date or commit does not trip it.

Figures are built from `evidence.json` by `../make_figures.py`, so a figure can
never carry a number the evidence does not. `runs/` and the figure PDFs are build
products and are not committed.
