# evidence/

The data behind every number in the papers, and the machinery to check it.

| file | what it is |
|---|---|
| `generate.py` | rebuilds every cited quantity from the rig (~8 min) |
| `evidence.json` | the data: one record per claim, with its tolerance |
| `verify.py` | re-runs and checks each claim against `evidence.json` |
| `PROVENANCE.md` | generated index: claim → where cited → tolerance → test |

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

Figures are built from `evidence.json` by `../make_figures.py`, so a figure can
never carry a number the evidence does not. `runs/` and the figure PDFs are build
products and are not committed.
