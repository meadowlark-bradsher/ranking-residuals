# evidence/

The data behind every number in the papers, and the machinery to check it.

| file | what it is |
|---|---|
| `generate.py` | rebuilds every cited quantity from the rig (~2 min) |
| `evidence.json` | the data: one record per claim, with its tolerance |
| `verify.py` | re-runs and checks each claim against `evidence.json` |
| `PROVENANCE.md` | generated index: claim → where cited → tolerance → test |

```bash
python verify.py --fast   # identities and closed forms, seconds
python verify.py          # everything, a few minutes
```

Figures are built from `evidence.json` by `../make_figures.py`, so a figure can
never carry a number the evidence does not. `runs/` and the figure PDFs are build
products and are not committed.
