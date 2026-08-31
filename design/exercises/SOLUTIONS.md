# Answer key

Expected outcome, interpretation, and the wrong reading, for each exercise in
[`README.md`](README.md). Every number below was transcribed from a real run of the
script beside it, not predicted.

Each answer opens with a **kind** line, because it governs how you may quote the
result:

- **exact** — an identity or a closed form. Your output should match digit for
  digit. If it does not, something is wrong with the tree, not with your draw.
- **one draw** — deterministic given the config, so it reproduces on your machine,
  and still a single sample from a distribution over base seeds. Reproducing it is
  not the same as it being the quantity (spec §13.1).

---

## 1 — `b₁`, and where harmonic mass may live

**Kind: exact.**

### Expected

`b₁` on `empty` is `3, 6, 10, 15, 28` at `m = 4, 5, 6, 7, 9`, matching
`(m−1)(m−2)/2` in every row. `b₁` on `observed` is `0` everywhere. The same flow
reads `h = 1.000000` under `empty` and `c = 1.000000` under `observed`.

### Interpretation

1. Yes — this is claim `b1-rank-formula`, and the general statement is the rank
   formula `b₁ = E − rank(D0) − rank(D1)`. On the complete graph with no 2-cells,
   `D1` is empty, so every independent cycle survives as a harmonic direction.
2. `b₁ = 0` on `observed` because filling every triangle of a complete graph kills
   every cycle: `rank(D1)` grows to absorb exactly the cycle space. Harmonic
   dimension is zero, so `h` has nowhere to be.
3. What changed is the **2-skeleton** — a modelling choice, declared and logged
   (spec §4), not a property of the data. The pool did not become rankable. Under
   `observed` the identical cyclic structure is reported as *curl* rather than
   harmonic; it has been renamed, not removed. Whether it is a defect depends on
   whether you believe the missing triangles were genuinely unobservable.

### The wrong reading

That `observed` "resolves" the harmonic mass and the pool is fine. It resolves the
*label*. This is exactly why the rig calibrates on `empty` (§4): the harmonic
reading there is unambiguous, and the choice is made once and written down rather
than made per-experiment where it can be made to say either thing.

---

## 2 — the two known-answer poles

**Kind: exact.**

### Expected

| pole | filling | b₁ | g | c | h |
|---|---|---|---|---|---|
| A integers, value-difference | empty | 55 | 1.000000 | 0.000000 | `3.193e-31` |
| A integers, value-difference | observed | 0 | 1.000000 | 0.000000 | `1.165e-30` |
| B circle, rotational | empty | 6 | 0.000000 | 0.000000 | `1.000e+00` |
| B circle, rotational | observed | 0 | 0.000000 | 1.000000 | `5.128e-32` |

`self_checks` passes on all four, and measured-minus-oracle is at most `5.551e-16`.

### Interpretation

1. Pole A's harmonic reading is `1e-31`-ish under `empty` and `1e-30`-ish under
   `observed`: **machine zero, not small**. These are the two values in claim
   `clean-gradient-zero`. A value-difference flow *is* `D0v` for the potential `v`,
   and `P_h` annihilates every gradient identically, so the only thing left is
   floating-point dust. "Small" would be a measurement; this is an identity.
2. The certificate calibrates against the `empty` reading — spec §4 and §5.6. What
   §4 requires is that the choice be **declared, frozen, and logged**, so a config's
   `(g,c,h)` is never readable without knowing which 2-skeleton produced it. Both
   readings of pole B are correct answers to different questions.
3. `self_checks` verifies internal consistency: `D1·D0 = 0`, that the three
   components reconstruct `Y`, that they are mutually orthogonal, that the harmonic
   part is divergence- and curl-free, and that `dim(harmonic) = b₁`. It does **not**
   check that the flow you built is the flow you meant to build, that the filling is
   the right modelling choice, or that the decomposition answers your question. It
   passes just as happily on the ±1 flow of exercise 3.

### The wrong reading

Treating a passing `self_checks` as validation of the measurement. It validates the
arithmetic. Every trap in this exercise set passes `self_checks`.

---

## 3 — a perfect ranking that reads as unrankable

**Kind: exact.**

### Expected

Part 1, `empty` filling, complete graph, the same total order encoded two ways:

| n | h (value-difference) | h (±1 signs) | `(n−2)/(3n)` |
|---|---|---|---|
| 3 | `5.958e-32` | 0.1111111111 | 0.1111111111 |
| 5 | `2.386e-31` | 0.2000000000 | 0.2000000000 |
| 6 | `9.720e-32` | 0.2222222222 | 0.2222222222 |
| 8 | `2.824e-31` | 0.2500000000 | 0.2500000000 |
| 16 | `2.586e-31` | 0.2916666667 | 0.2916666667 |

Part 2: on the unanimous log all three encodings give `g = 0.777778, h = 0.222222`.
On the graded log, `logodds` gives `h = 0.000286`, `signed` gives `0.018236`, and
`pm1` gives `0.222222` — unchanged. ζ is `1.0` in all six rows.

### Interpretation

1. `h = 0.200` at `n = 5` and `h = 0.2222…` at `n = 6` are the two points pinned by
   claim `pm1-trap`, which states only that the mass is `n`-dependent.

   **The closed form.** For a total order on `K_n` the sign flow is the all-ones
   edge vector. Fitting `s` by least squares gives `s_i = (2/n)·i`, so the gradient
   energy is `(n²−1)/3` against a total mass of `n(n−1)/2`, and

   ```
   g = 2(n+1) / (3n)          h = (n−2) / (3n)  ->  1/3
   ```

   The script checks this at `n = 3…16` and the largest disagreement is `5.55e-17`.

   The formula is registry claim **`pm1-closed-form`**, pinned at those same eight
   `n` by `test_5_1_pm1_mass_has_a_closed_form_in_n`. It is a separate claim from
   `pm1-trap` rather than a widening of it: `pm1-trap` records two measured points
   at the precision the methodology paper prints them, and this one asserts an
   identity at every `n` to machine precision. Quote `pm1-trap` for "the mass is
   `n`-dependent", `pm1-closed-form` for the formula. Spec §5.1 states the
   identity as of v10 and keeps both measured points as instances of it.

2. **The data changed, not the decoder.** In the unanimous log every pair has the
   same win rate, so the log-odds of every edge is the same number and the decoded
   flow is a uniformly scaled all-ones vector — the ±1 flow again, up to a scale
   that fractions divide out. The sentence finishes: *logodds recovers magnitude
   only when the win rates carry it.* A magnitude-aware decoder cannot recover
   information the log does not contain.

3. `pm1` reads `0.222222` in both logs because it discards the win rates before the
   decomposition sees them. The `n`-dependent mass is therefore **manufactured by
   the encoding**, not carried by the data: it is a property of "all-ones on `K_n`",
   which is what any total order becomes once you throw away how far apart things
   are.

4. A ζ-only certificate would call this pool perfectly consistent and rankable —
   and on the underlying order it would be right, which is what makes the ±1 reading
   dangerous rather than merely wrong. See exercise 9 for the case where ζ says the
   same thing and is not right.

### The wrong reading

"`h ≈ 0.22`, so about a fifth of this pool is unrankable." Nothing about the pool is
unrankable; you quantized a total order and measured the quantization. The second
wrong reading is quoting `0.2222` without its `n` — at `n = 16` the same encoding
gives `0.2917`, and the number climbs toward `1/3` forever.

---

## 4 — the same measurement at two budgets

**Kind: one draw** (the floor tables). The budget echo and the config fingerprints
are exact.

### Expected

Run A (`--quick`, 8 seeds, 4 reps, `k ∈ [32…256]`) finishes in about 0.2 s and
reports `coverage 5/6 cells, median CI width 0.13802`. Its floor estimates include
`−0.05649` and `−0.03185` — negative numbers for a quantity whose oracle is `0.0100`
and which cannot be negative. Every cell with `eps > 0` is flagged `GRID SHORT`.

Run B (shipped defaults, 64 seeds, 16 reps, `k` to 16384) takes about 4 s and
reports `coverage 16/16, median CI width 0.00116`. Coverage of 16/16 is at the top
of the documented range; claim `residual-across-draws` gives coverage as typically
15 of 16, range 13–16 over 20 base seeds, so a run of yours showing 14/16 is the
system working, not a regression.

### Interpretation

1. A's `covers=True` is worth nothing because of the **CI width**. A median width of
   0.138 against oracles of 0.01 and 0.04 is an interval that would cover almost any
   claim you cared to make, including zero and including negative floors. Coverage
   is only evidence when the interval is narrow enough to have excluded something.
   The two median widths on the same quantity are 0.13802 and 0.00116.
2. `fit_k_required` reads 1621, 912, 281, 441 against a grid topping out at 256, so
   the derived window is unreachable and the fit falls back to the top two grid
   points — which is what `grid_insufficient` announces. The field you would reach
   for is `fit_k_min`, and you must not lower it: below 64 the `O(1/k²)` logit-bias
   term is absorbed into the intercept (§2.6). The correct fix is to **extend the
   `k` grid upward**, which is what the default budget does.
3. `seed_drop_rate` counts seeds lost by **both** routes — masks with `b₁ = 0`, which
   have no harmonic direction to inject into, and masks too small to carry a
   decomposition at all. Reading B's CI as coming from all 64 seeds would overstate
   the evidence: at 9–16% drop it came from roughly 54–58. `rig/sweep.py` says why
   this is one number and not two: counting only one route once read 0.578 against a
   true 0.953.
4. `config_fingerprint` is a hash of the config, so it is **the same for two runs of
   the same configuration and different the moment any field moves** — including
   fields the measurement never reads. A timestamp tells you when a run happened; a
   fingerprint tells you whether two records are comparable.

### The wrong reading

Taking A as a fast preview of B. It is not a noisier version of the same
measurement — the fits fell back to a window the spec refuses, so the numbers are
outside the regime in which `floor + c/k` means anything. `--quick` is for checking
that the code runs.

---

## 5 — recovering a floor whose answer you know

**Kind: one draw.** This cell reproduces exactly on the same tree; it is one draw
from the base-seed distribution.

### Expected

At `gamma = 1.5`, 64 seeds, 16 reps, `rho = 1.5`:

| eps | oracle `eps²` | fitted floor | 95% CI | covers | ratio | `k` needed |
|---|---|---|---|---|---|---|
| 0.0 | 0.00000 | −0.00004 | [−0.00019, +0.00010] | True | — | inf |
| 0.1 | 0.01000 | 0.01017 | [+0.00979, +0.01056] | True | 1.0170 | 1004 |
| 0.2 | 0.04000 | 0.04001 | [+0.03928, +0.04077] | True | 1.0003 | 254 |
| 0.4 | 0.16000 | 0.15944 | [+0.15747, +0.16133] | True | 0.9965 | 75 |

Monotone in `eps²`, and the `eps = 0` control covers zero. These rows are exercise
4's run B at `gamma = 1.5`, and agree with it digit for digit — the script uses the
same config `rig.sweep.run()` hands its floor sweep.

### Interpretation

1. On this draw the ratios are 1.0170, 1.0003, 0.9965 — **above, then level, then
   below**. They are not consistent in sign, and that is the expected behaviour, not
   a puzzle: claim `residual-across-draws` reports the per-draw spread as about a
   percentage point wide. The systematic part is a surviving **under**-read of
   `+0.435% ± 0.088` (spec's v7 note and §8.5, owned by the same claim), which is
   around a third of the per-cell sampling spread and below what one sweep can
   resolve. Three cells cannot see it.
2. The sentence to send is something like: *"At the shipped config the fitted floor
   at `eps = 0.2` covered its `eps²` oracle, CI [0.0393, 0.0408] over 64 seeds on one
   base seed. The systematic offset is registry claim `residual-across-draws`; don't
   quote my cell for it."* What §13.1 forbids is "the floor is 1.0003× the oracle" —
   a single draw of a quantity whose spread is wider than the effect, stated as
   though it were settled.
3. `required_fit_k_min = c_oracle / (rho · floor)` is `inf` at `eps = 0` because the
   floor being resolved is zero and there is no ratio to satisfy. It is a correct
   answer, and `rig/sweep.py` writes it out as JSON `null` rather than the bare
   `Infinity` token, which is not in the JSON grammar. The `eps = 0` row is judged
   instead by whether its CI **covers zero**, and by nothing else.
4. `c_ratio ≈ 1` rules out **fit misspecification**: the `1/k` term is behaving as
   the delta method predicts, so the intercept is being read off a model that fits.
   It does **not** rule out the floor being wrong. Spec §2.6 is explicit and gives
   the counterexample: at `beta = 0.25` the gate reads `c_fit/c_oracle = 1.01` while
   the recovered floor is 1.86× the true value. Necessary, not sufficient.

### The wrong reading

"The floor came back at 1.0003× the oracle, so the estimator is unbiased." One cell,
one draw, and the systematic term is smaller than the spread you just sampled from.
Also wrong in the other direction: seeing a 1.7% miss in a single cell and reporting
a regression.

---

## 6 — the floor is an intercept

**Kind: exact.** Deterministic — it refits stored energies from claim `fit-window`,
whose true floor is 0.090. Your output matches this table exactly.

### Expected

| `fit_k_min` | points | floor | ratio | c | r² |
|---|---|---|---|---|---|
| 8 | 10 | 0.18637 | 2.071 | 8.786 | 0.889871 |
| 16 | 9 | 0.14405 | 1.601 | 12.862 | 0.900572 |
| 32 | 8 | 0.10054 | 1.117 | 20.219 | 0.983247 |
| 64 | 7 | 0.08422 | 0.936 | 24.980 | 0.998696 |
| 128 | 6 | 0.08748 | 0.972 | 23.374 | 0.999386 |
| 256 | 5 | 0.08846 | 0.983 | 22.576 | 0.998471 |
| 512 | 4 | 0.08945 | 0.994 | 21.288 | 0.995644 |
| 1024 | 3 | 0.09015 | 1.002 | 19.895 | 0.975601 |
| 2048 | 2 | 0.08705 | 0.967 | 28.977 | 1.000000 |

The first and fourth rows reproduce the registry's own `intercept_full_grid`
(0.18637) and `intercept_windowed` (0.08422). The derived window at `rho = 1.5` is
`k ≥ 185`.

### Interpretation

1. The ratio improves from 2.071 down to 1.002 at `fit_k_min = 1024`, then gets
   **worse** at 2048. Two effects compete. Raising the window drops the small-`k`
   points where the omitted `O(1/k²)` term lives, which removes bias. It also drops
   points, which raises the variance of an extrapolation to `k = ∞`. The turn is
   where the second overtakes the first.
2. By r² the ranking puts `fit_k_min = 2048` first (r² = 1.000000) and 1024 seventh.
   By `|ratio − 1|` it is almost reversed: 1024 first, 2048 seventh. r² measures how
   well the line passes through the points you kept; the floor is where that line
   hits an axis far outside them. **Ship on the window derived from `c/(rho·floor)`**,
   which is a statement about resolving the floor against the variance term, not
   about fit quality.
3. r² = 1.000000 at two points is evidence of **nothing**. A straight line through
   two points is exact by construction. It is the highest r² in the table and the
   second-worst floor.
4. `rig.sweep.floor_measurement` fits on `window = max(fit_k_min, required_fit_k_min)`
   — so the derived 185 governs and the constant 64 acts as a floor beneath it. When
   the `k` grid cannot supply two points at or above that window, it sets
   `grid_insufficient = True`, falls back to the top two grid points, and reports the
   flag on the human-facing table as well as in the JSONL. It does not silently fit.
5. Two things stop `fit_k_min = 32`. From the table, it recovers 1.117× the true
   floor — an 11.7% error you would carry into every downstream number. And
   `rig/config.py` refuses the value outright: `BTLConfig.validate` raises on
   anything below `MIN_FIT_K = 64`, with the reason in the message. It is not a
   tuning knob.

### The wrong reading

Choosing the window by fit quality. Every instinct trained on regression says take
the highest r², and here that gives you the two-point fit. The window is set by what
you are trying to resolve, and `required_fit_k_min` says so in one line of algebra.

---

## 7 — does the pipeline reproduce what went in

**Kind: one draw** for the mixed rows (they depend on a sampled assembly); the
counts and sign paths are exact by construction.

### Expected

Part 1: the `counts` path round-trips with max deviation `0.000e+00`, the `sign`
path with `2.220e-16`, and the mixed config — which dispatches `sign`, `magnitude`
and `counts` in one log — with `1.870e-03` and `residual_max 2.157e-01`.

Part 2, mixed config, as `emit_k` grows:

| `emit_k` | headroom `log(2k−1)` | rows | deviation | `residual_max` | saturated |
|---|---|---|---|---|---|
| 8 | 2.7081 | 1056 | `4.012e-02` | `9.417e-01` | 15 |
| 16 | 3.4340 | 1552 | `1.311e-02` | `4.818e-01` | 5 |
| 32 | 4.1431 | 2768 | `3.175e-04` | `2.441e-01` | 0 |
| 64 | 4.8442 | 4944 | `1.870e-03` | `2.157e-01` | 0 |
| 128 | 5.5413 | 9520 | `7.837e-04` | `8.000e-02` | 0 |
| 256 | 6.2364 | 18448 | `9.544e-04` | `8.000e-02` | 0 |

### Interpretation

1. The **magnitude** path is the inexact one. `emit_from_flow` emits
   `round(k·σ(Y))` wins per edge, and a count is an integer: the target flow is
   representable only up to that rounding. Exactness is a `k → ∞` limit, which is
   why the path reports `residual_max` rather than asserting a tolerance. The other
   two are exact because `counts` replays the generator's own win counts and `sign`
   emits all `R` rows one way, giving `±log(2R−1)` — a uniformly scaled ±1 flow,
   and mass *fractions* are scale-invariant.
2. Gate on **`residual_max`** (with `n_saturated`), which falls monotonically:
   0.9417, 0.4818, 0.2441, 0.2157, 0.0800, 0.0800. The deviation column does not —
   `3.175e-04` at `emit_k = 32` is better than `1.870e-03` at 64. It is a difference
   between two projections of two nearby flows, and small differences of large
   quantities are not monotone in the input's accuracy. `residual_max` is the actual
   per-edge emission error; the deviation is a downstream consequence of it that can
   improve by luck.
3. The largest `|Y|` in the mixed assembly is `3.6497`, on the bridge (`ic`) block —
   the exercise does not print it, so measure it:

   ```python
   a = assemble(RigConfig().validate(), gamma=2.0, eps=0.2, k=16)
   {n: float(abs(b.Y).max()) for n, b in a.blocks.items()}
   # {'cc': 1.0, 'ic': 3.6497..., 'ii': 3.4340...}
   ```

   Saturation ends between `emit_k = 16` (headroom 3.4340, still below it) and
   `emit_k = 32` (headroom 4.1431, above it) — exactly where the column goes to
   zero. The `ii` block's 3.4340 is `log(2·16−1)` from the BTL generator at `k = 16`
   and is never counted as saturated, correctly: the `counts` path replays those win
   counts exactly, so it has no headroom problem to report.
4. `rig/config.py`'s note beside `emit_k = 64` claims two things: deviation "~2e-3"
   at 64 and "~4e-2" at 8. **Both reproduce** — `1.870e-03` and `4.012e-02`. The
   same note says "5 bridge edges exceed `log(2k−1)`" at `emit_k = 8`; the measured
   count at 8 is **15**, and 5 is the `emit_k = 16` figure. The note does not state
   the `(gamma, eps, k)` of its assembly, but no combination on the default grid
   gives 5 at `emit_k = 8`, so this is not a parameter mismatch on your side. Report
   it; do not fix it here.

### The wrong reading

Reading `exact=False` as a failure. It is a declaration of which path was used. The
failure mode the round-trip exists to catch is the §10 trap — a flow that quantizes
away to *nothing* — and that raises `EmissionCollapse` rather than returning a small
number (exercise 10).

---

## 8 — three ways to get harmonic mass

**Kind: mixed.** The `bias_rule` rows and part 3 are exact identities; the
`variance_fresh` bridge-only column is one draw.

### Expected

The C–C block alone carries harmonic energy `10.0000000000`.

`bias_rule`: `h(total) = 10.000000` at every `R` from 2 to 128, and bridge RMS fixed
at 3.8944. `variance_fresh`: `h(total) = 57.727273` at every `R` (the coin flip has
expectation zero, so the oracle flow has no bridge in it), while `h(bridge only)`
falls 14.70 → 32.31 → 14.18 → 2.90 → 3.55 → 1.78 → 0.71. `variance_fixed`:
`h(total)` climbs from 76.11 to 887.68, with bridge RMS 1.0986, 1.9459, 2.7081,
3.4340, 4.1431, 4.8442, 5.5413.

Part 3: potential-consistent bridge `10.0000000000`, constant bridge
`57.7272727273`, circle alone `10.0000000000`.

### Interpretation

1. `bias_rule`, and 10.000000 is the harmonic energy of the **C–C block alone**.
   This is claim `bridge-invariance` and spec §7's "bias bridge: harmonic = C–C
   floor exactly" — exactly, not approximately. The bridge is built as
   `Y[i,c] = s[c] − s[i]` against the *shared* potential, so it is a gradient, and
   `P_h` annihilates gradients identically.
2. From `R = 16` the bridge-only column halves roughly as `R` doubles — 2.90, 3.55,
   1.78, 0.71 — which is the `1/R` decay. `R = 2…8` reads 14.70, 32.31, 14.18, which
   is not a decay curve and should not be read as one: these are **single draws** of
   a variance term, and at small `R` the sampling spread is comparable to the term
   itself. Averaging over seeds is what makes the decay visible there; one draw does
   not.
3. `variance_fixed`'s bridge RMS equals `log(2R−1)` in every row, to four decimals.
   So it does not persist at constant size — it **grows**, because a fixed rule
   produces unanimous outcomes and the log-odds of a unanimous edge is pinned by the
   `1/(2R)` clamp at `log(2R−1)`. "Persists" is right about the contrast with
   `variance_fresh` (it does not wash out) and wrong as a description of the
   magnitude. The same clamp is behind exercises 3, 7 and 10.
4. The constant bridge lacks **potential-consistency with the I–I block**. A
   constant offset is a global gradient only when the integer side is flat; against
   a sloped I–I block it is not the difference of any potential, and it deposits
   harmonic of its own — 57.73 against the 10.00 that should be there.
5. The bridge carries 47.73 of harmonic energy measured on its own and contributes
   exactly 0 to the total, because **`P_h` is a property of the whole graph, not of a
   block**. Restricted to the bridge edges and zero elsewhere, the flow is not a
   gradient of anything and projects onto the harmonic space; embedded in the full
   config it is one piece of a global gradient, which projects to nothing. The
   consequence for attribution is direct: you cannot apportion harmonic mass by
   measuring blocks in isolation and adding up. The energies are not additive across
   blocks, and the sub-projection is a diagnostic, not a share.

### The wrong reading

"The bridge carries 47.7 of harmonic energy, so the bridge is the problem." It
carries none in the configuration you are measuring. The mirror error is reading
`variance_fresh`'s flat `h(total) = 57.73` as proof the coin flip is harmless — that
column is the *oracle*, the infinite-data limit, and the coin flip is invisible to it
by definition. What you would actually observe at finite `R` is the other column.

---

## 9 — ζ says perfectly consistent

**Kind: exact.**

### Expected

Case A, the 4-cycle beside a transitive triangle: `h = 0.4000` under **both**
fillings, `mass = 10.0`, `b₁ = 2` on `empty` and `1` on `observed`. ζ = `1.0000`
over **1** observable triple.

Case B, the bare 4-cycle: ζ = `nan` over 0 observable triples.

Case C, the complete equal-spaced circle: `h = 1.0000` on `empty`, `c = 1.0000` on
`observed`, ζ = `0.0000` over 10 triples.

### Interpretation

1. `h = 0.40` beside ζ = `1.0` over one triple: this is claim `zeta-blind`. Note
   that the claim's own prose says "a third of the energy" while its recorded value
   is 0.4 — quote the value, not the sentence.
2. The harmonic fraction is filling-invariant here because the mass lives on the
   **4-cycle** `0-1-2-3-0`, and that subgraph contains no triangle at all. `observed`
   fills the one triangle that exists, `4-5-6`, which was carrying pure gradient and
   no harmonic — so `b₁` drops from 2 to 1 and the harmonic reading does not move.
   Filling can only kill cycles that bound a filled triangle, and this one bounds
   nothing.
3. The property is **whether the cycles carrying the flow have observable triples**.
   Same rotational-style rule in both cases; in C every triple is present, so ζ sees
   the intransitivity and reports 0.0 — correctly. In A the intransitivity lives in a
   4-cycle, ζ has exactly one triple to look at, that triple is transitive, and ζ
   reports its perfect score. This is why spec §8.8's Delta C note insists the
   demonstration be built on a graph with **missing** triangles: the first version of
   the test asserted the claim on the complete pool and was simply wrong.
4. Ask for **`b₁`** — or equivalently the number of observable triples against the
   number of independent cycles. ζ = 0.98 over 3 triples on a graph with `b₁ = 40`
   is not evidence about 40 dimensions; it is evidence about 3 triples. The harmonic
   fraction is the number that reads the rest.

### The wrong reading

That ζ is broken or superseded. It measures triad consistency accurately. The error
is applying it to a sparse graph and reading its output as a statement about the
whole pool — the divergence region, where the harmonic mass lives, is precisely the
region ζ has no triples in.

---

## 10 — the failures that are supposed to be loud

**Kind: exact.** All twelve raise.

### Expected

`12/12 guards fired`: ten `ValueError`s, one `EmissionCollapse`, one
`RegimeViolation` — covering `fit_k_min = 32`, `fixed_mask_across_k = False`, a `k`
grid starting at 1, a grid that never reaches `fit_k_min`, one row per pair, a sign
rule at `R = 2`, a ±1 rule down the magnitude path at `k = 2`, `bridge_R = 1`, a fit
window with one point, `filling='custom'` with no triangles, an unknown filling, and
a fit outside the §2.6 window.

Then the same regime check with `strict=False` returns a dict:
`saturation 0.9227` against a gate of 0.2 (`saturation_ok False`), `mildness 0.0111`
against 0.05 (`mildness_ok True`), `fit_k_min_ok True`, `ok False`.

### Interpretation

1. **"emit one row per pair"** and **"±1 rule down the magnitude path, k=2"**. Both
   are the `1/(2k)` clamp of exercise 3 and 7. At `k = 1` the clamp pins `p̂` to
   exactly 0.5 and `log(0.5/0.5) = 0` on every edge — the v3 correction, measured
   `total_mass = 0.000000`. At `k = 2` a ±1 target rounds to a 1–1 tie and the clamp
   pins it back to zero, which is the same failure one level down (Delta B). `R ≥ 2`
   is necessary and not sufficient, which is why there are three emission paths.
2. `rig.sweep.run()` calls `floor_sweep(..., strict=False)`. That is not switching
   the guard off: `floor_measurement` still calls `regime_report`, and still records
   `saturation`, `mildness` and `regime_ok` into **every** output record. What
   `strict` changes is whether a cell outside the window aborts the sweep or is
   surveyed and labelled. The sweep covers a grid that deliberately includes edge
   cells, and each record states whether it was inside the window — so the
   information survives, in the JSONL, per cell. Switching the guard off would mean
   not computing it.
3. **Saturation** protects the *upper* end: near-deterministic edges (`p` close to 0
   or 1) produce unanimous draws whose logit is pinned by the clamp and grows like
   `log(2k)`, so the flow stops being the flow you modelled. The gate is 0.2, and
   0.17 fits while 0.42 breaks. **Mildness** protects the *lower* end of the
   injection: `eps²` as a fraction of the gradient energy must stay under 0.05, so
   the misspecification stays *innocent* — a large `eps` would make the injected
   direction the dominant signal rather than a floor beneath a decaying null. One is
   about the data being too certain, the other about the injection being too big.
4. Report the refusal. Spec §8.5 step 1: *"Assert the §2.6 preconditions before
   fitting anything. Refuse to fit outside the window; a loud failure is the correct
   output, not a floor number."* You would report that the config falls outside the
   validity window, which gate failed and by how much against its threshold, and no
   floor. A number produced outside the window is not a worse number, it is a
   misreported one — §2.6 records `c_fit/c_oracle = 1.01` alongside a floor that was
   1.86× wrong, so the diagnostics do not save you either.

### The wrong reading

Treating the guards as friction, and reaching for `strict=False` or a lower
`fit_k_min` when one fires. Both of those are in the tree for specific, narrow
reasons that are written down at their call sites. The guard firing *is* the
measurement's output in that regime.
