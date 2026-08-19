# ranking-residuals

A synthetic **calibration rig** for the HodgeRank rankability certificate: a deterministic,
known-answer harness that manufactures comparison data with *controlled* Hodge structure
(gradient / curl / harmonic), so the certificate can be validated against ground truth
**before** any LLM judge is involved.

Spec: [`design/specs/calibration-rig-spec.md`](design/specs/calibration-rig-spec.md) (v5).

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
hodge.py            THE INSTRUMENT — byte-identical to design/reference/hodge.py
conftest.py         puts the repo root on sys.path
rig/
  config.py         config schema + validation; every §2.6/§10 trap fails loudly
  pool.py           integer + complex pools (equal_spaced, random, surrogate_defeating)
  flows.py          clean gradient; BTL null + eps injection; rotational; three bridges
  graph.py          edge typing, block assembly, per-block RMS (scaled, per §5.7)
  oracle.py         projector oracles, delta-method c, the §2.6 regime gates
  fit.py            OLS floor+c/k on the derived window; bootstrap CI across seeds
  emit.py           judgment-log emission, three paths, collapse guard
  sweep.py          config enumeration + run harness + CLI
  report.py         tables + figures
tests/
  test_acceptance.py  §8.1–§8.10 — the definition of done
  test_invariants.py  §5.1–§5.7 plus the §2.4/§2.5/§2.6/§9/§10 traps
```

## Known residual

The recovered floor carries a small systematic **under**-estimate (~3–6% on the derived
window, vs ~10–13% on the fixed one). It is stable, not noise. At high seed counts the CI
is tight enough that this bias can push it just below the oracle. Characterising it — and
whether `rho` or a `k`-grid extension removes it — is post-build tuning work, flagged in
the spec's v5 revision note rather than papered over.
