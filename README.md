# ranking-residuals

A synthetic **calibration rig** for the HodgeRank rankability certificate: a deterministic,
known-answer harness that manufactures comparison data with *controlled* Hodge structure
(gradient / curl / harmonic), so the certificate can be validated against ground truth
**before** any LLM judge is involved.

Spec: [`design/specs/calibration-rig-spec.md`](design/specs/calibration-rig-spec.md) (v10).

## The instrument is not forked

`hodge.py` at the repo root is **byte-identical** to `design/reference/hodge.py` — same
SHA-256, so `git` itself proves it. Every operator, projector, decomposition and entry
point comes from it. The rig is a *data source*, never a reimplementation.

```bash
shasum -a 256 hodge.py design/reference/hodge.py
```

## Quick start

```bash
python -m pytest tests/ -q
```

```bash
python -m rig.sweep --out runs
```

`--quick` shortens the seed count and `k` grid for smoke runs; `--no-figures` skips
matplotlib. Outputs land in `runs/`: one JSONL per sweep, `manifest.json`, a floor table,
and six figures. Every record carries its full config **and the run budget that produced
it**, so no number is readable without knowing what paid for it.

If you are learning to drive this rather than maintaining it, start at
[`design/exercises/`](design/exercises/README.md): ten scripts with known answers, in
order, from `b₁` and the filling convention through the floor measurement to the guards
that refuse to fit. The answer key is beside them, and it is explicit about which
outputs are identities and which are one draw.

```bash
python design/exercises/ex01_filling_and_b1.py
```

## The three sources of harmonic mass

They are kept apart deliberately, because conflating them is how a certificate gets a
false positive:

| source | generator | behaviour under more data |
|---|---|---|
| **systematic / adversarial** | C–C rotational rule on the unit circle | persists — *this is the signal* |
| **innocent null** | sparse noisy BTL on comparable items + `eps` misspecification | decays to a floor of exactly `eps²` |
| **incomparability** | I–C bridge (integer vs complex) | depends on mode; three reference lines |

## Three findings the build had to fix

**The floor axis is `eps`, not θ-shape.** `P_h · D0θ = 0` *identically* — θ is a potential,
`D0θ` is a pure gradient, and the projector annihilates it (measured `1.7e-13` at every γ
from 1 to 6). No θ asymmetry can produce a budget-independent floor. The floor is injected
directly (§2.5) and its oracle is exactly `eps²`.

**The fit window is derived, not fixed.** `floor + c/k` fitted over the full `k` grid biases
the floor by 0.83×–2.48×, because the `O(1/k²)` logit-bias term gets absorbed into the
intercept. The spec pins `fit_k_min = 64`, but that constant was measured on
`filling='observed'`; on `'empty'` the same graph has 10× the harmonic dimension, hence 10×
the variance term, and 64 is nowhere near enough (0.016 recovered against a true 0.090).
`rig.oracle.required_fit_k_min` derives the window from `c_oracle / (rho · floor)` instead,
and a `k` grid that cannot reach it is **flagged**, not silently fitted.

**Row counts below 3 destroy a ±1 rule.** `analyze_comparisons` clamps `p̂` to `1/(2k)`, so a
single row per pair yields `Y = 0` on every edge. Less obviously, pushing a ±1 rule through
the *quantized* emitter at `k=2` rounds it to a 1–1 tie and the clamp pins it back to zero.
Emission therefore has three non-interchangeable paths (`counts`, `sign`, `magnitude`) and
any flow that quantizes away entirely raises rather than returning nothing.

## Layout

```
hodge.py              THE INSTRUMENT — byte-identical to design/reference/hodge.py
conftest.py           puts the repo root on sys.path
envelope_evaluator.py dependency-free closed-form oracle for the harmonic-zero null
boundary_report.json  its shipped output, fingerprinted to the code that wrote it
rig/
  config.py           config schema + validation; every §2.6/§10 trap fails loudly
  pool.py             integer + complex pools (equal_spaced, random, surrogate_defeating)
  flows.py            clean gradient; BTL null + eps injection; rotational; three bridges
  graph.py            edge typing, block assembly, per-block RMS (scaled, per §5.7)
  oracle.py           projector oracles, delta-method c, the §2.6 regime gates
  moments.py          exact binomial moments; exact harmonic energy, no Monte Carlo (§7)
  fit.py              OLS floor+c/k on the derived window; bootstrap CI across seeds
  emit.py             judgment-log emission, three paths, collapse guard
  provenance.py       per-entry-point source fingerprints, stamped into every result
  sweep.py            config enumeration + run harness + CLI
  report.py           tables + figures
tests/
  test_acceptance.py          §8.1–§8.10 — the definition of done
  test_invariants.py          §5.1–§5.7 plus the §2.4/§2.5/§2.6/§9/§10 traps
  test_harmonic_zero_null.py  identities of the harmonic-zero score test
  test_harness_rules.py       enforces "no verdict on a moment ratio from a low-df cell"
  test_source_fingerprint.py  fingerprint is sensitive to meaning, blind to presentation
  test_readme_layout.py       the layout blocks below name only paths that exist
design/
  specs/              the spec (v10) and the v6 changeset that reconciled it to the build
  reference/          hodge.py, the explainers, the canonical comparison note
  methodology/        papers, evidence registry, experiments — see below
  exercises/          ten runnable exercises + their answer key; teaching only,
                      nothing here is load-bearing for the build
```

## Evidence and methodology

`design/methodology/` holds the papers and, load-bearingly, the **evidence registry**:
the machinery that keeps every cited number reproducible.

```
design/methodology/
  evidence/           generate.py → evidence.json → verify.py, indexed by PROVENANCE.md
  experiments/        the probes behind the claims, each with its own RESULTS.md
  snippets/           standalone .tex sections, no preamble dependency
  combined/           paper 1 draft + its generated beat sheet
  make_figures.py     figures are built FROM evidence.json, never from a fresh run
  *.tex               the methodology and bridge-invariance papers
  *-PAPER-BEATS.md    paper 2's working outline (paper 1's lives in combined/)
  calibration-rig-BUILD-HISTORY.md
                      the build's decision record: Delta A-F, the six defects,
                      and why figures are stated as distributions
```

Every quantity the papers cite is one record in
[`evidence.json`](design/methodology/evidence/evidence.json) carrying its tolerance and
the test that pins it, and
[`PROVENANCE.md`](design/methodology/evidence/PROVENANCE.md) is the generated index of
claim → where cited → tolerance → test.

```bash
cd design/methodology/evidence && python verify.py --fast
```

`verify.py` re-runs each claim and checks it against the registry — `--fast` covers the
identities and closed forms in seconds, the full pass takes minutes. Because
`make_figures.py` reads `evidence.json`, **a figure cannot carry a number the evidence
does not.**

## Known residual

The recovered floor carries a small, stable systematic **under**-estimate. It is not
noise, and at high seed counts the CI is tight enough that it can sit just below the
oracle — so §8.5 documents the residual rather than widening its tolerance. At the
shipped config all four cells cover; it is at higher seed budgets, where the CI
tightens, that some still exclude the oracle.

**The figure is not quoted here.** It moves with the seed, and this section has been
wrong about it three times over — `~10%`, then `3–6%`, then `~2.0–2.4%`, with coverage
as `16/20` (spec §13.1 lists them). Not all of that drift was sampling: the first two
straddle the fit window becoming derived, so the estimator moved underneath them. The
rest was single draws quoted as settled. Its owner is the **`residual-exact`** claim
in the registry, measured over 20 base seeds with Monte Carlo removed and reported
there with its standard error and range. Read it from
[`evidence.json`](design/methodology/evidence/evidence.json) or
[`PROVENANCE.md`](design/methodology/evidence/PROVENANCE.md); the convention it follows
is §13.1 of the spec, "Seed-varying quantities ship with their spread, never as a
point", which restates "Why figures are stated as distributions" in
[`calibration-rig-BUILD-HISTORY.md`](design/methodology/calibration-rig-BUILD-HISTORY.md).

**Both levers were tried, and neither removes it.** Lengthening the `k` grid cleared the
`grid_insufficient` flag and closed the two cells Delta D recorded, but a tighter CI at a
higher seed budget still excludes the oracle in some — *Delta D* in
[`calibration-rig-BUILD-HISTORY.md`](design/methodology/calibration-rig-BUILD-HISTORY.md).
Lowering `rho` reduces the residual monotonically but costs grid reach, so the two have
to move together — the spec's v7 revision note, and the `rho-tradeoff` claim. What
replaced the open question is a mechanism: the residual tracks `c2`
(`residual-tracks-c2`), and
subtracting or fitting `c2` removes most or essentially all of it on exact energies
(`residual-fit-variants`).

An independent replication of the exact figure lives in
[`design/methodology/experiments/bias-of-bias/`](design/methodology/experiments/bias-of-bias/).
Cite `residual-exact` rather than that directory, so a single number travels.
