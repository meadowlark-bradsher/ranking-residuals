# bias-of-bias

> **Status: independent replication, not the cited source.**
>
> The exact-energy residual computed here (`report_exact.py` ->
> `results/exact_energy_residual.json`) and the registered claim `residual-exact`
> in `../../evidence/` are the same quantity measured twice over the same 20 base
> seeds. They agree to **six significant figures** and differ at the seventh
> (1.4e-07 relative, 2.6e-05 of one standard error) -- comfortably inside
> `residual-exact`'s own 0.02 pt tolerance, and far inside either standard error.
> The value is deliberately not restated here: read it from `residual-exact`,
> which is what the paper quotes and **the only one of the two that should ever
> travel**.
>
> They did not always agree, and why they did not is the part worth keeping. An
> earlier revision of this note recorded a fourth-decimal disagreement and
> explained it as two separately written implementations differing in cell
> handling. That explanation was wrong. The registry side was building its configs
> at `n_cplx=5` while this replication used `n_cplx=0` -- and `n_cplx` enters the
> config fingerprint, hence every mask seed, so the two were averaging over
> **disjoint topology ensembles** rather than disagreeing on a shared one. Both
> now run the floor path at `n_cplx=0`, matching `rig/sweep.py`.
>
> That is the stronger result rather than the weaker one: two independently
> written implementations of the same identity, on the same graphs, agreeing to
> the six significant figures above. The seventh-digit gap is summation order
> over 20 seeds x 16 cells, not a difference in what is computed.
>
> **The rule, with a trigger you can evaluate.** Treat a disagreement beyond
> `residual-exact`'s tolerance -- `{kind: abs, value: 0.02}` percentage points --
> as a signal that one implementation has drifted, and reconcile before
> publishing either. The current gap is ~5.1e-08 pt against that 0.02 pt
> trigger -- both inputs, no derived ratio (spec 13.3). An earlier revision
> quoted the ratio instead, as "six orders of magnitude"; it is 5.6, and that
> rounding is why the ratio is no longer quoted here at all. When it does fire,
> check the config fingerprint before the arithmetic: that is where it hid last
> time, and a mask-ensemble mismatch reads exactly like a numerical one.

Hunting the mechanism behind the residual in the floor estimator.

The name is literal. The floor the rig recovers *is* a bias term —
`‖P_h·bias‖²`, the harmonic energy that survives infinite data. Our estimator of
it carries a bias of its own: a small, stable under-read that survived both levers
we had (tuning ρ and lengthening the `k` grid). The registry owns the figure twice
over, and the two arms differ by about 20% — `residual-across-draws` sampled,
`residual-exact` with Monte Carlo removed — which is why no single gloss for it
belongs in this sentence. These probes ask what that second bias is made of.

## The five prongs

| probe | asks | status |
|---|---|---|
| `rho_squared` | does the residual scale as ρ², as pure curvature leak predicts? | here |
| *analytic logit-bias prediction* | does the closed-form `b_e` contribution predict 0.43%? | **worked analytically elsewhere** |
| `bias_corrected` | does correcting the plug-in logit bias collapse it? | here |
| `eps_dependence` | is it ε-independent (variance curvature) or ε-scaling (cross term)? | here |
| `richardson` | does the floor converge upward as the window tightens? | here |
| `joint_consistency` | are the two fixes one cause or two? | **added after the first run** |

The analytic prong is recorded so the set reads as five. It is the one that would
turn an empirical property into a theorem about the estimator; the others here
constrain which mechanism that theorem should be about.

`joint_consistency` was not planned. It exists because `bias_corrected` and
`richardson` each landed on zero, and two fixes that separately explain the whole
of one residual is a coincidence worth attacking rather than reporting.

See [RESULTS.md](RESULTS.md) for what they found. It is regenerated from
`results/*.json` by `probes.py`, so it cannot drift from the recorded data.

## Why these do not go through the config

`rho`, `fit_k_min` and `eps` are all config fields, so the obvious way to sweep
them is `cfg.with_(rho=...)`. That is wrong here. `derive_seed` hashes the config
fingerprint, so changing any field also redraws every mask — the sweep would vary
the axis **and** hand you a different graph ensemble, and the two effects are not
separable afterwards. The ρ scan recorded in the papers does exactly this and
averages over base seeds to wash it out.

`core.py` separates the stages the production path fuses:

```
mask_for(n, p, seed)     the graph -- depends on seed, n, p and nothing else
draw(...)                sampling  -- win counts per (k, rep) on that graph
energies(draw, corr)     encoding  -- counts -> flow -> harmonic energy
fit(ks, E, window)       estimation-- energies -> floor, at a chosen window
```

ρ and the window enter **only at the last stage**, so sweeping them needs no
resampling: draw once, refit many times. That makes `rho_squared`,
`richardson` and `joint_consistency` exact rather than noisy, and nearly free. ε enters at `draw` and
does need resampling — but the mask stays pinned, which the production path
would not do.

None of this changes the rig. `core.py` is an adapter for experimental control,
not a fork of the estimator.

## Why the correction is not a config flag

`bias_corrected` changes what the estimator computes. It would be natural to add
`bias_correct: bool = False` to `RigConfig` and sweep it — but a new field
changes the fingerprint even when inert, which reseeds every mask and moves every
stochastic number in the papers. Verified. So the correction lives in
`core.energies(..., correction="firth")` and touches nothing shipped.

If it turns out to work and we want it, adding it to the rig is a separate,
deliberate change that pays the reseed cost once, with a full re-verification and
a pass over the papers. That is when a branch is warranted; not before.

## Results

`results/*.json`, one per probe:

- `question` — what it asks
- `falsifies` — **what result would have changed the conclusion**, written before
  the run
- `verdict` — `supported` / `refuted` / `inconclusive`
- `value`, `config` — the numbers and the conditions

Recording `falsifies` up front is what stops a null result being reread as a
weaker positive afterwards.

**A refuted probe is a result.** It removes a mechanism from the list and saves
the next person the run. These stay out of `evidence.json`, which holds only what
the papers cite and must stay green; if a probe yields something a paper cites,
it graduates deliberately.

```bash
python probes.py                 # all of them, and regenerate RESULTS.md
python probes.py rho_squared     # one
```

## Check the power before trusting a verdict

The first run of these probes used 40 seeds × 32 reps. Every verdict it produced
was noise, and none of them looked like noise — they came with signs, magnitudes
and confident labels. The standard error on the bias scales as roughly
`41 / sqrt(seeds × reps)` percentage points, so that configuration carried
±1.14pp against an effect of about half a point.

`probes.py` now runs 220 × 384, for about ±0.14pp. If you change `SEEDS` or
`REPS`, recompute that number first and compare it against the effect you are
trying to see. This failure mode is silent: the probes will report verdicts at
any power, and under-powered verdicts are indistinguishable from findings
without doing this arithmetic.
