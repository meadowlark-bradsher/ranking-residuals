# Thinning, reopened: is there a filling level where both gates hold?

*Branch `thinning-filling-window`, off `harmonic-zero-null` at `174f20b`.*

## Why this is open again

Comparison-level thinning was parked with three gates, the third failing:

1. within-edge exchangeability (RAN-29, unmeasured — needs logged comparisons)
2. per-graph separation cost at fold size (measured, topology-dependent)
3. χ² validity **at** fold size (measured, **failing** at k/2 = 64)

Gate 3 looked like a k problem, so the only remedies were "raise k" or "calibrate
the reference distribution at fold size and lose the referee-proof χ² claim."

`b1_ladder` (174f20b) shows it was never a k problem. Filling a triangle adds a
row to D₁, so S grows and b₁ shrinks — monotonically — and the two named
conventions are the two *pathological ends* of a lattice, not a binary choice.
On the mean, χ² holds wherever b₁ ≥ 3:

| k | cells with b₁ ≥ 3 within 10% of χ² | b₁ = 1 |
|---|---|---|
| 32 | 22 / 23 | 0.741 |
| 64 | **23 / 23** | 0.753 |
| 128 | 23 / 23 | 0.891 |

b₁ = 1 is the only failure at every k. And b₁ is reachable: six ladder levels per
graph, spanning 4–16, 3–13, 3–21, and 1–22 on graphs 0–3.

**So gate 3 has a third remedy that costs no data: fill fewer triangles.**

## The question this branch exists to answer

Filling fewer triangles raises b₁ — good for gate 3. But it moves toward `empty`,
where im D₁ᵀ = {0}, S = im D₀, and the harmonic-zero null *is* Bradley–Terry
(measured: identical df, 18 = 18 on a 29-edge graph). At that end the dominance
that motivated the null is gone entirely.

So the two requirements pull opposite ways along the same dial:

- **gate 3 wants b₁ ≥ 3** → fill *fewer* triangles → toward `empty`
- **dominance over BT wants 2-cells present** → fill *more* triangles → toward `observed`

> **Is there a filling level, at the deployment's own graph, where χ² holds at k/2
> *and* the null still meaningfully dominates Bradley–Terry?**
>
> If the two windows overlap, thinning is viable and the filling is how you buy
> it. If they do not overlap, thinning is dead for that topology and the answer
> is a property of the graph, not of the method.

## What is already measured, and the gap

Measured at the `observed` endpoint only (`curl_freedom`, k = 128, 1500 reps):
Bradley–Terry rejects **every** draw from a curl fraction of 0.45 upward, while
harmonic-zero never exceeds 0.058.

**That is the gap.** Dominance has been measured at one filling. Gate 3 has been
measured along the whole ladder. Nobody has measured dominance *as a function of
ladder level*, which is exactly the curve this question needs. That is the first
run to build here: `curl_freedom` swept over `b1_ladder`'s levels rather than
pinned to `observed`.

Separation (gate 2) also needs re-reading along the ladder — it was measured at
the endpoints too, and it is topology-dependent, so it may or may not move with
the filling. Cheap to collect in the same sweep.

## Answered (first run, `dominance_ladder`)

**The window is open on 4 of 4 graphs, and the tension this branch was opened to
resolve barely exists.** At the fold size k = 64, rho_curl = 1.0, 600 replicates
over 3 base seeds: every rung with at least one filled triangle has Bradley-Terry
rejecting **1.000** while the harmonic-zero null holds nominal size (0.038-0.067
across all rungs and graphs). Dominance does not decay as b1 rises. It is
essentially **binary in the filling**: undefined at m = 0, and full from m = 1.

Filling 2 of 15 triangles on graph 0 already gives BT 1.000 against harmonic-zero
0.067, at b1 = 14 -- far above the b1 >= 3 that gate 3 needs. So the dial has a
wide overlap rather than a narrow window, and choosing a filling to satisfy gate 3
costs nothing in dominance on these topologies.

**A second thing this settles.** The empty-end degeneracy was previously cited
from one case (18 = 18 on a 29-edge graph). It now holds on all four: b1 equals
the Bradley-Terry df exactly at every empty end -- 16, 13, 21, 22 -- and the two
nulls return identical rejection rates on identical draws, as they must when they
are the same test.

### The caveat that matters more than the result

`eta_in_S` scales the curl term to ||eta||, so the curl fraction is **fixed at
0.71 by construction** at every rung, not varied. What moves along the ladder is
*which subspace* the curl occupies, not how much there is. And the injected curl
is drawn from `im D1^T` **at the rung being tested**, so the null is absorbing
curl it was constructed to absorb. That is self-consistent, and it is not the
deployment case.

**The untested risk is the one the dial creates.** Moving the filling changes what
counts as curl versus harmonic. A *fixed* physical misspecification does not move
with it -- so a flow that is curl under `observed` can read as harmonic under a
partial filling, and be certified as genuine obstruction. This run cannot see
that, because it re-derives the injection from each rung.

### Answered (second run, `filling_leakage`)

**The dial is dead, and the reason is that it was never a statistical knob.**

Hold the misspecification fixed -- built once at `observed`, where it is exactly
H0-true -- and walk the test's filling down the ladder. Leakage is zero at the
observed end and nonzero at every other rung, 0.196 to 0.707. The sampled
consequence is total: rejection is **1.000** at every leaking rung (0.982 and
0.991 at graph 2's two smallest leaks), against nominal 0.047-0.056 at every
zero-leak rung. Section 3 puts the usable band at ||P_h eps|| around 0.1; the
smallest leak on the ladder is twice that, so the size is not inflated, it is gone.

Rungs that are simultaneously chi2-valid and safe:

| graph | b1 at `observed` | usable rungs |
|---|---|---|
| 0 | 4 | b1 = 4 (the observed end, and only it) |
| 1 | 3 | b1 = 3 (the observed end, and only it) |
| 2 | 3 | b1 = 3 (the observed end, and only it) |
| 3 | 1 | **none** -- safe only at b1 = 1, where chi2 fails |

So the answer to this branch's question is: the window `dominance_ladder` found is
**not usable**. Every rung it opened leaks. The only safe filling is the one you
started at.

### What this means for thinning, which is better than it sounds

Thinning never needed the dial on three of four graphs. At their own `observed`
filling, graphs 0, 1 and 2 sit at b1 = 4, 3, 3 and hold chi2 at k = 64
(meanT/df 1.044, 1.055, 0.972). Gate 3's original failure was graph 3 speaking
for the set, at b1 = 1.

That yields a **free pre-check**: b1 is a function of (edges, triangles) alone, so
a deployment can compute it before collecting a single comparison.

> **b1 >= 3 at your observed filling -> thinning is safe at k/2. b1 = 1 -> it is
> not, and no choice of filling rescues it.**

Cheaper and more decisive than the dial would have been, and it runs before the
money is spent.

### The result worth keeping

Note what `filling_leakage` assumes: it *defines* innocence at the `observed`
filling by constructing eta there. If you genuinely believed fewer triangles were
the right model, a flow that is curl under `observed` would be a real partial
obstruction, and the test would be correctly detecting something you had declared
to be signal -- not leaking.

So the finding is not "leakage is a bug." It is that **the filling is not a
statistical parameter at all -- it is the definition of what counts as innocent.**
Moving it changes the hypothesis, not the estimator. It cannot be tuned for chi2
convenience for the same reason a null cannot be tuned for a p-value.

That puts the filling fork back where the briefing said it belonged: coupled to
whose cycle the certificate certifies (RAN-3), and not settleable by rig time.
It is a declaration to be made and defended, not a trade-off to be measured.

### Scope, and the next run if there is one

Both runs use a misspecification shaped as curl under `observed`. That is the
worst case for the dial and the natural shape for a comparator whose local
inconsistencies sit on filled triangles, but a differently-shaped one would leak
differently. Nothing here measures that, and it is the only remaining way the
dial could be rehabilitated -- narrowly, for misspecifications of a shape a
deployment could actually argue for.

### Superseded

Inject a **fixed** flow -- curl under the `observed` filling, held constant -- and
sweep the *test's* filling level underneath it. Measure where it starts reading as
harmonic. That is the false-positive curve for using the filling as a dial, and it
is the question that decides whether the wide window above is usable or only
apparent.

## Two defects to respect while working here

Both surfaced in `174f20b` and neither is fixed:

- **`varT/2df` is not a usable diagnostic as computed.** One draw in 1984 with
  T = 661.7 (graph 2, b₁ = 10, k = 64) drives the ratio to 11.721 against a mean
  of 1.001; drop it and it reads 1.009. Its |η| is 10.64, under the `SEPARATED`
  cut of 14.0, so the guard never sees it — the missing condition is the
  classical one on expected cell counts, not a bound on |η|. **Judge the window
  on the mean until this is fixed**, and do not read the variance column.
- **The b₁ = 1 cell is not pinned down by one run.** The ladder reads 0.891 at
  k = 128 where `chi2_collapse` reads 1.024 — same b₁, same graph, different
  filling and seed stream. A 13% spread on one nominal quantity. Per the
  methodology paper's Principle 2, anything quoted from this branch ships as a
  distribution over base seeds, not as a number.

## Working agreement

This branch has its own worktree, so it does not disturb `harmonic-zero-null`.
`results/` and `runs/` are gitignored and per-worktree, so probe outputs cannot
collide between the two. The instrument (`hodge.py`) stays frozen; anything
needed from it goes through `score_test.operators_for_triangles`, which routes an
explicit 2-skeleton through the instrument's own `custom` filling.

One caution that is not about git: probe runs here are CPU-heavy. A full
`probes.py` pass saturated 12 cores for ~5 minutes and drove load average to 169,
which made an unrelated test suite read 92s against its usual ~5s. Two agents
running probes at once will produce timings neither can trust. Coordinate the
runs, not just the branches.
