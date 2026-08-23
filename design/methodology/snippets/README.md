# LaTeX snippets

Sections written to drop into the topological-bounds paper unchanged. Each is a
standalone `.tex` with no dependency on the methodology document's preamble or
private macros — plain `amsmath` notation only, so a snippet can be `\input` or
pasted without carrying anything with it.

## Compile-checking

`preview.tex` stubs the labels the snippets cite outward (e.g.
`sec:topological_bounds`) and `\input`s each snippet:

```bash
tectonic -X compile preview.tex
```

A clean build means the snippet typesets and its internal cross-references
resolve. It does **not** check the outward ones — those resolve only in the
target paper.

## Provenance of the numbers

Every quantitative claim traces to `design/specs/calibration-rig-spec.md` or to
`design/methodology/evidence/evidence.json`, where each is a registered claim
with an explicit tolerance and can be re-checked with `evidence/verify.py`. Where
a figure depends on a configuration
default, the default is named inline. That convention is not decoration: two
numbers in the first draft of `numerical-experiments.tex` had gone stale when a
default moved underneath them — the `±log(2R−1)` magnification factor (quoted as
`2.7×`, measured at `emit_k = 8`, now `4.84×` at the shipped default of 64) and
the rig's line count. A figure that silently depends on a default is a figure
that will be wrong later.

## Corrections applied to the first draft

| Claim as drafted | Correction |
|---|---|
| `k ≥ 64` recovers `0.94–1.01×` | `k ≥ 64` gives `0.87–0.95×`; the `0.94–1.01×` band comes from the *derived* window |
| Derived window "eliminates the need for a prior choice of simplicial representation" | It eliminates a *per-filling calibrated constant*. Filling still sets `b₁` and what the certificate measures, and convergence is conditional on the grid reaching `k_min` |
| "bit-exact magnitude replays (`w = round(k·σ(Y))`)" | Backwards. `counts` (native win replay) is bit-exact at `0.00e+00`; the magnitude path is approximate and reports a residual. Three paths are retained with a dispatch rule, not collapsed to one |
| "exactly `2.7×`" | `log(2R−1)`, so `R`-dependent: `2.708×` at `R=8`, `4.84×` at the current default `R=64` |
| `2,045` lines of execution code | `1,586` lines of rig plus `571` of acceptance tests |
| `c_oracle` used as the fitted slope | The fitted slope is `c`; `c_oracle` is its closed-form prediction. Keeping them distinct is what makes their agreement a usable guard |
