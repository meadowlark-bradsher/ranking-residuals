# harmonic-zero-null

RAN-28 on the known-answer rig: is the harmonic-zero null a classical score test?

    H0 :  logit p  in  S = im D0 (+) im D1^T = (harmonic)^perp

The harmonic component of the mean flow is exactly zero; the gradient **and
curl** coordinates are free. The claim under test (RAN-27, structural result 1)
is that in the pre-specified fixed-graph case this test *collapses* to a
classical Rao score test — chi-squared with b1 degrees of freedom, in harmonic
coordinates. If it does, the certificate is referee-proof on its own and DZW
earns its keep only at post-selection loop-choice and small n.

## The three probes

| probe | asks | status |
|---|---|---|
| `chi2_collapse` | **[GATING]** Is the statistic chi2(b1) on a fixed graph? | confirmed for k ≥ 128 |
| `curl_freedom` | Does it absorb curl where Bradley–Terry rejects on it? | confirmed |
| `harmonic_projected_eps` | Is the size distortion governed by ‖P_h ε‖ alone? | confirmed |

See [RESULTS.md](RESULTS.md) for the numbers. It is regenerated from
`results/*.json` by `probes.py`, so it cannot drift from the recorded data.

```bash
python probes.py                 # all three, ~5 min
python probes.py chi2_collapse   # just the gate
```

## Why the score lands in harmonic coordinates by construction

The link is canonical, so the Fisher information is diagonal and the score is
`U = w − k·p`. At the constrained MLE the first-order condition is `Mᵀ U = 0`
where `col(M) = S` — so `U` is orthogonal to `S`, hence lies in

    S^perp = (im D0 + im D1^T)^perp = ker D0^T ∩ ker D1 = harmonic.

"The score test in harmonic coordinates" is therefore literal, not a metaphor
and not a projection anyone chose to apply. `score_off_harmonic` measures it on
every draw rather than trusting it; it reads ~1e-14.

## Three things worth knowing before using this

**The collapse is asymptotic in k, and k = 8 is nowhere near it.** Every cell's
KS test rejects at k = 8. From k = 128 the moments land within a few percent and
the realised size sits in 0.045–0.060.

**Separation, not distributional shape, is the binding practical limit.** On
`observed` at k = 8, 60–99.6% of draws have an edge at w=0 or w=k, the
constrained MLE diverges, and the statistic is undefined. Those draws are
counted and dropped, never averaged in — an earlier version of this run kept
them silently and reported a mean T of 7.3e11.

**On `filling='empty'` the harmonic-zero null IS the Bradley–Terry null.** With
no 2-cells `im D1^T = {0}`, so `S = im D0` and the two tests have identical df.
Everything the "strictly dominates BT" argument buys evaporates under that
filling. The choice is not free (cf. RAN-7, RAN-22).

## What is not here

DZW's own construction — symmetric-noise folds, orthogonalize under H0, test
residual orthogonality — is **not implemented**, so RAN-28's "and they AGREE"
half is untested. The canonical briefing
(`dzw2026-vs-harmonic-null-CANONICAL.md`) is not in the repo. What is tested is
the half that stands alone: if the collapse had failed, agreement would be moot.

## Why these do not go through RigConfig

Same reason as `bias-of-bias`: the sweep axes here are the null's own subspace
geometry, not rig budget knobs. Routing them through the production config would
misrepresent them as settings. The rig is used for what it is good at —
generating fixed graphs and BTL draws with known ground truth — and `hodge.py`
is untouched, so `S` is derived from the instrument's own `harmonic_basis` and
cannot drift from what the certificate measures.
