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
