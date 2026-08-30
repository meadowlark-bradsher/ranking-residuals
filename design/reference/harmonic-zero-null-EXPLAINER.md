# The harmonic-zero null: what the test is, and what we found

*A self-contained explainer for a reader who has not been following the work —
written to be handed over whole, not to be the record.*

**Provenance, and a warning.** Every figure here is **transcribed by hand**.
Most come from `design/methodology/experiments/harmonic-zero-null/RESULTS.md`,
which is generated from `results/*.json` by `probes.py` and is the authoritative
record. This document is a snapshot and **will go stale silently the next time
the probes are re-run**. If a number here disagrees with RESULTS.md, RESULTS.md
is right. Re-check before quoting any figure onward.

**One section is ahead of this branch.** The saturation window in "Where the test
is valid" comes from branch `seed-spread`, which is **not yet merged** — it
retracts a claim this document previously made, so it is stated here rather than
left to be discovered. Its figures cannot be checked against this branch's
RESULTS.md until that merge lands.

All measurements are on the known-answer rig: four pre-specified fixed graphs, 12
items, 24–33 edges — the deployment-realistic regime.

---

## The problem the test solves

The certificate takes a set of pairwise comparisons, decomposes the comparison
"flow" into gradient, curl, and harmonic parts, and reports the harmonic share —
the fraction of the flow that admits no consistent scalar ordering. Large
harmonic mass is the signature of a genuine cycle: A beats B beats C beats A, in
a way no ranking can explain away.

Used as a decision procedure, that number needs a threshold, and the threshold
cannot be read off the mathematics. On finite, noisy, sparsely sampled data a
*genuinely rankable* criterion still deposits harmonic mass. So "harmonic energy
> 0" is not evidence of anything until you can say what innocent data reads.

That makes it a hypothesis-testing problem: **is the harmonic component larger
than sampling noise would produce on its own?** Which requires a null.

## Why not Bradley–Terry

The obvious null is Bradley–Terry: assume a latent score per item, fit it, and
ask whether the residual harmonic mass is surprising. This is circular. A BT fit
assumes the criterion is rankable in order to test whether it is rankable, and it
forbids *everything* outside the gradient — curl included.

Curl is not a cycle. It is local inconsistency confined to small loops: the
comparator being noisy or context-sensitive on a few triples, without any global
obstruction to ranking. A certificate that fires on curl is not measuring what it
claims to measure.

**This is not a philosophical objection; the cost is total.** Fed flows carrying
curl but no genuine cycle, Bradley–Terry rejects **every single draw** — 1.000
across all four graphs, from a curl fraction of 0.45 upward. Curl-type
misspecification does not bias a BT null. It destroys it.

## The test

Widen the null to include curl. Let

- **D₀** = the gradient operator (differences of item scores)
- **D₁ᵀ** = the curl operator (flows around filled triangles)
- **S** = im D₀ ⊕ im D₁ᵀ — everything that is *not* a genuine cycle
- **harmonic** = S^⊥ — the genuine cycles, of dimension b₁

The null is

> **H₀ : logit p ∈ S** — the harmonic component of the true log-odds is exactly
> zero, with gradient and curl coordinates free.

Fit the model constrained to S; test whether what's left over points into the
harmonic directions.

**This is a classical Rao score test, and that matters.** It is not a new
statistical object needing its own theory. In the pre-specified fixed-graph case
it is χ² with b₁ degrees of freedom, and the geometry is exact rather than
approximate: the constrained fit's stationarity condition MᵀU = 0 forces the
leftover score orthogonal to S, hence *into* the harmonic subspace, by
construction — not by any projection we chose to apply. Measured on the rig,
that residual is at most 4.1×10⁻¹³ across all 40 cells: the true value is zero
and what remains is floating-point.

Practically: the certificate is a textbook test in disguise, so it is
referee-proof without new machinery.

## What the test buys

**Confirmed — it collapses to χ² as claimed.** Holds from k = 128 comparisons per
edge upward, across four fixed graphs, 2000 replicates per cell.

**Confirmed — it dominates Bradley–Terry, and not marginally.** Where BT rejects
1.000 on curl-carrying flows, the harmonic-zero null holds nominal size (never
above 0.058). All curl-type misspecification is absorbed; only harmonic content
drives rejection.

**Confirmed — size is governed by the harmonic projection of the error alone.**
An equal-norm perturbation placed *inside* S never moved size above 0.059, while
the same magnitude in a harmonic direction drove rejection to 0.967. So
misspecification in the wrong direction is genuinely free, which is the whole
point of widening the null.

The operational band:

| ‖P_h ε‖ | realised size across graphs |
| --- | --- |
| 0.05 | 0.051 – 0.057 |
| 0.10 | 0.059 – 0.080 |
| 0.20 | 0.071 – 0.141 |
| 0.40 | 0.223 – 0.452 |
| 0.80 | 0.757 – 0.981 |

**The null is usable with an empirically characterised size while ‖P_h ε‖ ≲ 0.1**
— worst cell 0.080 against a nominal 0.05. By 0.4 it reads 0.22–0.45 and is no
longer honest. Whether a real LLM comparator sits below 0.1 is not something a
synthetic rig can answer; that measurement has to come from the comparator work.

## Where the test is valid — the part that surprised us

Two failure modes bound the operating envelope, and neither is visible from the
statistic itself. Both are **topology-dependent**, so neither can be priced once
and reused.

**1. Separation is the binding practical limit, not distributional shape.** At
low k, some edge lands at 0 or k wins, the constrained fit diverges, and the
statistic is undefined. At k = 8 this costs 60–99.6% of draws. One graph still
loses 20.7% at k = 128 and 5.0% at k = 512.

Worse, the loss is *selective*: separation preferentially removes draws with
extreme scores, so the surviving test is **conservative**. That is the safe
direction to fail, but the power loss is invisible to anyone not tracking the
drop rate.

> **Deployment consequence.** Near this regime, a certificate reading "no cycle
> detected" may be reading a *truncated* statistic rather than an innocent graph.
> The drop rate must be reported alongside any verdict.

**2. The χ² approximation fails when edges get near-deterministic — and that is
checkable in closed form.** The reference distribution needs edges that are not
effectively decided before you look. The condition is on the *cell*, not the
draw, and it has a closed form the instrument already ships:

> **saturation** = E[ p^k + (1−p)^k ] — the expected fraction of edges landing at
> 0 or k wins. Judge it against a **b₁-indexed** window: the moments close at
> **0.03 for b₁ = 1** and **0.18 for b₁ = 22**.

No simulation. Computable from the design alone, before a single comparison is
collected, so a deployment can know in advance whether the χ² reference is
trustworthy at its own sample size.

Under matched saturation the moments hold everywhere tested — **48 of 48 cells at
every k, across b₁ = 1 to 22.** So saturation, not b₁, is what the failures track.

**There is no established flat bound, and the low-b₁ edge is not pinned.** A
universal 0.02 was proposed and withdrawn: its calibration rested on one draw per
cell, and reseeded ten ways an in-window cell at saturation 0.0161 with b₁ = 1
passes only 6 of 10. Treat that region as demonstrated-marginal, and expect the
true b₁ = 1 bound to be tighter than 0.03.

**And saturation is not a complete summary of a cell.** Two cells at the same
saturation but different flows behave differently — which is a real limit on any
single-number gate, and the reason the two figures above are a window rather than
a threshold.

*An earlier version of this document claimed the floor was a **b₁ floor** — that
χ² held only for b₁ ≥ 3 and broke at b₁ = 1. That was wrong, and the way it was
wrong is worth recording. The sweep that produced it varied the filling, which
changes the curl direction as well as b₁, so the injected flow's extremity
drifted along with it — saturation wandered from 0.0056 to 0.0436 and was not
monotone in b₁. Every low-b₁ cell carrying the finding was out of window. Rescale
each cell to matched saturation and the effect disappears entirely. The sweep was
measuring how extreme the flow was, not how many harmonic coordinates it had.*

*The two edges close by different mechanisms, and the mean tells them apart. At
b₁ = 1 the drop rate climbs and separation truncation drags the surviving mean
down — it closes by* losing draws, *so this failure and the separation one bite
together there rather than independently. At b₁ = 22 the drop rate stays at zero,
the mean never moves, and only the variance inflates — it closes by* low expected
counts, *which is what the precondition was built for.*

## The filling is not a tuning knob

Which triples count as "filled triangles" sets the boundary between curl and
harmonic. It ranges over a lattice: filling every observed triple gives the
smallest b₁; filling none gives the largest. We measured across it.

Two things came out.

**At the empty end, the test degenerates into Bradley–Terry.** With no triangles,
the curl space is trivial, S collapses to the gradient image, and the two nulls
become the *same test* — identical degrees of freedom (16, 13, 21, 22 on the four
graphs) and identical rejections on identical draws. Everything the wider null
buys evaporates there.

**And you cannot move the filling to buy statistical convenience.** Hold a
misspecification fixed and move the test's filling underneath it, and the flow
leaks into the harmonic subspace —
zero leakage at the filling where it was defined, 0.196 to 0.707 at every other
rung. Rejection goes to 1.000 against a nominal 0.05. The move that buys χ²
validity is exactly the move that reclassifies innocent curl as genuine
obstruction.

The reason is worth stating carefully, because it is not a bug. **The filling is
not a statistical parameter — it is the definition of what counts as innocent.**
Filling a triangle asserts that a 3-cycle among those three items is local
inconsistency rather than real obstruction. That is a claim about the domain.
Moving it changes the hypothesis, not the estimator, and it cannot be chosen for
convenience any more than a null can be chosen for its p-value.

So the filling has to be declared and defended up front, on grounds of what the
certificate is *for* — not selected after the fact.

## Summary

- The certificate needs a null; the obvious one (Bradley–Terry) is circular and
  fails catastrophically on curl.
- The harmonic-zero null fixes this, and is a **classical Rao score test** with
  χ²(b₁) reference — referee-proof, no new theory.
- It dominates Bradley–Terry completely, and its size is governed by the harmonic
  projection of the error alone, usable while ‖P_h ε‖ ≲ 0.1.
- Its validity is bounded by **two failures**: MLE separation (report the drop
  rate, and it is topology-dependent) and near-deterministic edges breaking the
  χ² reference — the latter checkable in closed form, before collecting data,
  via saturation against a b₁-indexed window.
- The filling that sets b₁ is a modelling declaration, not a knob.

## What this does not establish

- **The judge, only the instrument.** Everything above is synthetic ground truth.
  Whether a real comparator's harmonic deviation is *interpretable* — and whether
  it sits inside the ‖P_h ε‖ ≲ 0.1 band — is the next measurement, and it cannot
  come from a rig.
- **One data-generating process.** A single latent shape throughout; the four
  graphs vary the mask, not the latent.
- **One misspecification shape.** The leakage result uses an error shaped as curl
  under the fullest filling. A differently-shaped error would leak differently.
- **The post-selection case.** Everything here is the *pre-specified* fixed-graph
  regime. Choosing which loops to test *from the data* is a different problem and
  needs different machinery.
