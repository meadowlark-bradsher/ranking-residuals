# Synthetic Calibration Rig — Design Specification (v6)

**Revision note (v6):** reconciles the spec to the as-built rig. The build overtook v5 — the fit window and the emitter both became more correct in code than in spec — so this revision brings the document up to the instrument, and records what genuinely remains open. Deltas A–D applied as drafted; E resolved by measurement; F held strict.

- **A — derived fit window** (§2.6). The hardcoded `k ≥ 64` is retained only as a floor on the default budget; `required_fit_k_min = c_oracle/(ρ·floor)` governs. This **dissolves the observed/empty fork** — no per-experiment filling commitment is needed for the floor.
- **B — three emission paths** (§10). `R ≥ 2` is necessary but not sufficient. `counts` / `sign` / `magnitude`, chosen per block, plus a collapse guard.
- **C — ζ test construction** (§8.8). The claim stands; the construction is now specified, because the first test asserted it on a graph where ζ is *not* blind.
- **D — the parked residual, re-measured.** See below; the open question is now narrower and partly answered.
- **E — config defaults, CONFIRMed against the shipped code.** `beta 0.3 → 0.25`, `n_int 8 → 12`. One of the two proposed fixes did **not** do what the change-set expected — see §2.6.
- **F — §8.5 criterion held strict** (the change-set's recommendation). The alternative was explicitly gated on ρ being optimised first, which has not happened.

**Also in v6, from the reconciliation itself:** the default `k` grid was extended past 1024. The derived window of Delta A needs `k ≈ 516` at `eps = 0.1`, which the old grid could not reach — so the fit fell back and flagged `grid_insufficient`. Measured over 48 seeds × 4 γ, extending to 4096 takes `grid_insufficient` from **4/20 to 0/20** and worst γ-drift from **38.0% to 11.8%**, at a cost of 1.7 s vs 1.6 s.

**Residual (post-build, re-measured):** a stable **~2.0–2.4%** negative bias remains — down from the 3–6% of the v5 note, itself down from 10–13% before the window was derived. Each narrowing came from the same mechanism (window length), which is evidence it is not yet exhausted. **It is not closed:** over 48 seeds × 4 γ, `ci_covers_oracle` holds in **16/20** cells — the bias is small but systematic, and a tighter CI at a higher seed budget still excludes the oracle. At the §8 test config (32 seeds, γ=2.0) all four cells cover. Tuning **ρ** is the remaining lever; it is *justified, not optimised*. Post-build tuning, not a blocker.

**Revision note (v5):** §2.6 added — regime-validity preconditions for §8.5 — after an independent reproduction of the v4 saturation finding. Three corrections were forced by measurement during the insert; each is marked *(Correction, v5)* at its site:
1. **The `c`-oracle gate is necessary but NOT sufficient.** It catches catastrophic misspecification (`beta=0.6`: `c_fit/c_oracle ≈ 0.2`) but is blind to a 2× floor bias: at `beta=0.25` it reads `c_fit/c_oracle = 1.01` — essentially exact — while the recovered floor is **1.86×** the true value.
2. **The binding fix is the FIT WINDOW, not `beta`.** Fitting `floor + c/k` over the full `k` grid biases the floor by 0.83×–2.48× and drifts 15–21% with γ. Restricting the fit to **`k ≥ 64`** gives 0.87×–0.95× and γ-drift ≤ 7% at *every* `beta` in [0.15, 0.30]. `beta` then genuinely stops mattering, as intended.
3. **"High γ can trip the saturation precondition" is false given θ-standardization.** Holding `std(theta)` fixed is precisely what stops skew from changing the extremes: saturation is flat at 0.165 → 0.151 across γ ∈ {1, 1.5, 2, 3, 4, 6}.

Also settled in v5: the clamp is **not** widened (it is the instrument's estimator contract; tuning it to widen the rig's fitting window would be tuning the instrument to pass its own test). The saturation artefact — near-deterministic edges producing `log(2k)`-growing flow — is **parked as its own characterisation**, out of scope for §8.5.

**Known residual (v5, superseded by the v6 note above):** on the fixed `k ≥ 64` window the floor carried a stable ~10% *under*-estimate (0.87×–0.95×). It was characterised during the build: most of it was the fixed window being short, and deriving the window (Delta A) plus extending the `k` grid took it to ~2.0–2.4%.

**Revision note (v4):** §2.5 added — the misspecification knob, the *actual* floor source — and §8.5 rewritten around it. Four items carried as provisional in v3 are now **settled, not open**:
- **(f) potential-consistent `bias_rule`** — confirmed by algebra and by measurement. Settled: the bridge is `Y[i,c] = s[c] − s[i]` against the shared potential, full stop.
- **§7 `c`-oracle** (`c = tr(P_h·diag(1/(p(1−p))))`, delta method) — settled; it is the misspecification guard that licenses reading the fitted intercept as a floor at all.
- **§2.4 θ-standardization and fixed-mask-across-`k`** — both necessary. Settled.
- **"bias bridge: harmonic = C–C floor exactly"** — challenged on review, confirmed on measurement. Now stated with no hedge (§2.3, §7).

**Consequence of §2.5, propagated through the document (v4).** Since `P_h · D0θ = 0` *identically* for any potential θ — measured `‖P_h·D0θ‖² ≈ 1.7e-13` (machine zero) at γ ∈ {1, 1.5, 2, 3, 6} — the γ axis cannot produce a budget-independent floor at **any** γ, not merely at γ=1. γ is therefore **demoted from the primary Epic-C probe to a secondary shape knob**: it still moves `p_e`, hence the §7 `c` and the `O(1/k²)` finite-k bias, but it is not the floor axis. **`eps` (§2.5) is the floor axis.** Sections updated to match: §2.4, §3 (axes + schema), §5.6, §9, and the closing summary.

**Revision note (v3):** reconciled against a live probe of `hodge.py` before implementation. Changes from v2:
(a) **§10 corrected — it was wrong.** "Emit a single deterministic row" for ±1 rules yields `Y = 0` *exactly*, not ±1: `analyze_comparisons` sets `clamp = 1/(2k)`, so at `k=1` it clips `phat` to exactly `0.5` and `log(0.5/0.5) = 0`. Measured `total_mass = 0.000000`. Emission now requires `R ≥ 2`.
(b) **"asymmetric `theta`" replaced by a continuous γ axis** with `γ=1` as the symmetric negative control, θ standardized across γ and held fixed across each `k`-sweep (§2.4, §3, §5.6).
(c) **§8.7's monotonicity claim restated** on the fitted `k`-independent floor at fixed block scale, not on the raw harmonic fraction; `block_scale` added as an explicit, logged knob (§3, §5.7).
(d) **§8.5's floor now requires a confidence interval**, not a point estimate — its job is to be distinguished from zero (§7, §8.5, §9).
(e) **§5.1's `h ≈ 0.200` marked `n`-dependent** (it is 0.200 at `n=5`, 0.2222 at `n=6`).
(f) **§2.3's `bias_rule` bridge tightened** to potential-consistency with the I–I block — a *constant* bridge flow does **not** satisfy §7's "harmonic = C–C floor exactly" whenever the I–I block carries its own gradient.

**Revision note (v2):** reconciled against the real `hodge.py` reference implementation. Two substantive changes from v1: (a) the **statistical null** is now a first-class generator — genuinely-rankable-but-*noisy-and-sparse* data on comparable items (`sample_sparse_btl_logodds`), because the noiseless integer pool reads `h = 0` exactly and is not the distribution the threshold is calibrated against; (b) the **I–C bridge is reclassified** as an incomparability/connectivity axis, explicitly *not* the innocent null. API surface aligned to the actual module.

**Purpose:** a deterministic, known-answer harness that manufactures comparison data with *controlled* Hodge structure (gradient / curl / harmonic), so the harmonic rankability certificate can be validated against ground truth **before** any LLM judge is involved. It generalizes the A1 "pin BTL→0 on synthetic data" discipline (and subsumes A4's positive-control-cycle recovery). The rig is a **synthetic data source for the existing instrument** (`hodge.py`), not a reimplementation.

`hodge.py` is a **single-file module** (not a package). The rig imports it directly (`import hodge`) and must never fork its operators, projectors, or entry points.

---

## 1. Core model

Vertices are **numbers**, in two populations:

- **Integers** — the *rankable* population. A real total order exists.
- **Complex numbers on the unit circle** — the *unorderable* population (ℂ is not an orderable field).

Comparisons are edges, of three types, each with a deliberately chosen Hodge signature:

| Edge type | Pair | Flow rule | Signature | Under replication |
|-----------|------|-----------|-----------|-------------------|
| **I–I** | integer × integer | value-difference **or** sparse noisy-BTL log-odds | gradient (+ the **null**) | clean→persists; noisy→decays as c/R |
| **C–C** | complex × complex | rotational rule on the circle | **harmonic** (empty fill) → **curl** (observed/full) | persists (systematic) |
| **I–C** | integer × complex ("bridge") | coin flip **or** rule | variance **or** gradient | coin flip decays; rule persists |

**Three distinct sources of harmonic mass — keep them separate:**

1. **Systematic / adversarial** (C–C cyclic): genuine non-rankability. Persists under any amount of data. *This is the signal the certificate must detect.*
2. **The innocent statistical null** (noisy + sparse I–I): a genuinely rankable order, judged noisily on a sparse graph, deposits small harmonic that decays ~`c/R`, possibly over a `logit-bias floor`. *This is the distribution the threshold is calibrated against.* It is NOT zero — the noiseless pool (`h=0`) is an idealization.
3. **Incomparability** (I–C bridge coin flip): variance from mixed, unorderable pairs. A secondary, connectivity-related axis — **do not conflate with the null (2).**

---

## 2. Edge-flow specifications

Flow convention: for edge `(i,j)`, `i<j`, `Y[i,j]` is the signed advantage of `j` over `i`.

### 2.1 I–I edges — two modes
- **Clean gradient** (idealization / oracle path): `Y[i,j] = value[j] - value[i]`. Value-difference, **never ±1 sign** (see §5.1). Reads `h = 0` exactly.
- **Statistical null** (the operating null — see §2.4): sparse, noisy BTL log-odds via `sample_sparse_btl_logodds`. Reads small, `c/R`-decaying harmonic. **This is the load-bearing innocent generator.**

### 2.2 C–C edges — rotational harmonic
Complex numbers on the unit circle at angles `θ_k`; rotational rule:
```
j beats i  ⇔  0 < ((θ_j - θ_i) mod 2π) < π ;   Y[i,j] = +1 if j beats i else -1
```
- **Equal spacing** (`θ_k = 2πk/m`) ⇒ divergence-free ⇒ pure harmonic on `empty`, pure curl on `observed`/full. The canonical clean state.
- **Uneven spacing** ⇒ gradient + curl (partial order). Support both; equal-spaced is default. Use **odd `m`** to avoid antipodal ties, else pass a tiebreak flag.

### 2.3 I–C edges — the bridge (incomparability axis, NOT the null)
Integer-vs-complex is unorderable; there is no natural rule. Bridge mode is a config axis:
- **`variance_fresh`** (coin-flip bridge): fresh fair ±1 per *comparison* → variance, decays as `1/R`. Models a judge that *flails* on incomparable pairs.
- **`bias_rule`** (gradient bridge): deterministic surrogate, default `int_over_complex` (integers stacked above complex, consistent with a potential) → **no harmonic**, clean connective tissue. Models a judge that *fabricates a surrogate order*.
  **Potential-consistency requirement (load-bearing, see §7):** the bridge flow must be `Y[i,c] = s[c] − s[i]` using the **same potential `s` the I–I block is generated from** (`s[i] =` the integer values under `clean_gradient`, the latent `theta` under `null_btl`), with `s[c] = min(s[i]) − bias_gap` constant across the complex block. A *constant* bridge flow is only a global gradient when the I–I block is flat; as soon as I–I carries its own gradient, a constant bridge stops being `D0 s` for any `s` and deposits harmonic of its own, breaking §7's "bias bridge: harmonic = C–C floor exactly" and §8.6. **Settled, not a conjecture** — measured on `n_int=6, n_cplx=5, empty`: C–C block alone `= 10.0000`; potential-consistent bridge `= 10.0000` (equal to machine precision); constant bridge `= 57.7273`. The *excess* a constant bridge leaves is config-dependent (13.75 vs 10.00 in the original review run); the *equality* under potential-consistency is not. Note this also makes the bias bridge magnitude-carrying, as §5.1 requires.
- **`variance_fixed`** (stable-bias bridge): ±1 drawn once per *pair*, reused → **persistent** random field. Only use deliberately (see §5.3).

`variance_fresh` and `bias_rule` are the two LLM failure modes (thrash vs surrogate) as controllable reference lines. **The bridge is not the innocent null** — that lives on comparable I–I edges (§2.4).

### 2.4 The statistical null generator (noisy + sparse, comparable)
The certificate's threshold is calibrated against what a *genuinely rankable* criterion reads when judged noisily on a sparse graph — not against the noiseless pool. Reference contract (implement in `rig/flows.py`, verified against the real instrument):
```
sample_sparse_btl_logodds(n, beta, p, k, rng) -> (edges, Y_logodds, directed)
  theta_i = beta * (n-1-i)            # a genuine total order (pure gradient in the limit)
  each pair kept w.p. p               # sparsity -> holes -> b1 > 0 (room for harmonic)
  k Bernoulli comparisons per kept edge; Y = clamped empirical log-odds
```
Behaviour (confirmed against `hodge.py`, `filling='observed'`): clean-limit flow is ~pure gradient (`h→0`); at finite `k`, harmonic fraction is **nonzero and decays ~`c/R`** (measured: 0.045 at k=2 → 0.00086 at k=512, `n=12, p=0.45`, 40 seeds). Whether a nonzero **logit-bias floor** persists is the open Epic C question.

**θ-asymmetry is a continuous axis, not a flag — but it is NOT the floor axis (see §2.5).** v2 said "use asymmetric `theta`" without defining the shape. Defining it exposed why the shape cannot carry the Epic-C quantity: `theta` is a **potential**, so the clean-limit flow `D0·theta` is a pure gradient and `P_h` annihilates it *exactly*, at every shape. Measured `‖P_h·D0θ‖² ≈ 1.7e-13` (machine zero) for γ ∈ {1, 1.5, 2, 3, 6}. **No γ produces a budget-independent floor**; the floor comes from `eps` (§2.5). γ survives as a secondary knob because it moves `p_e`, hence the §7 `c` and the `O(1/k²)` finite-k logit bias. Shape definition:
```
theta_i(gamma) ∝ ((n-1-i)/(n-1)) ** gamma      # gamma >= 1, monotone total order throughout
  gamma = 1  -> reduces EXACTLY to the reference contract theta_i = beta*(n-1-i).
               Reflection-symmetric about its mean.
  gamma > 1  -> progressively skewed.
  NOTE: P_h . (D0 theta) == 0 at EVERY gamma (measured ~1.7e-13). Skewing theta does
        not defeat the projector -- there was never a symmetry to break. Gamma changes
        p_e, hence c (SS7) and the O(1/k^2) finite-k bias; it does not change the floor.
```
Two normalizations are **required**, not optional, or the axis does not measure what it claims:
- **Standardize θ across γ.** *(Settled.)* Rescale so `std(theta)` matches the γ=1 reference value `beta*sqrt((n^2-1)/12)` at every γ. Without this, raising γ shrinks the spread and the floor falls for a reason that has nothing to do with asymmetry — signal strength and symmetry would be confounded along the one axis meant to isolate symmetry. (The mean is immaterial; only differences `theta_j - theta_i` enter the flow.)
- **Hold the sparsity mask fixed across the `k`-sweep, within a seed.** *(Settled.)* The floor is a function of the *graph* — under §2.5 it is `eps²` measured against that graph's own harmonic basis — and `P_h` moves with the edge set. If the mask were redrawn per `k`, `floor` would not be a constant across the sweep and the `floor + c/k` fit of §8.5 would not be well-posed. Draw the mask once per seed; vary only the Bernoulli comparison outcomes with `k`. Report the fitted floor **vs `eps`** with a CI (§8.5), and γ as a secondary series — where the floor must come out **invariant** in γ (§8.5.5), which is the check that θ-shape is not leaking into the floor.

A secondary `theta_shape: random` (sorted draws from a skewed distribution, redrawn per seed) is retained as a **robustness check marginal over shapes** — not the primary probe, because a nonzero floor there cannot be attributed to any specific asymmetry.

### 2.5 Misspecification knob (the actual floor source)

The exact-BTL null of §2.4 has a *budget-independent* floor of exactly zero: with an
exact-gradient latent, harmonic mass is pure finite-k estimation error and → 0 as k → ∞
(verified: energy 20.8 → 0.02 across k, well-specified). So §8.5 run on §2.4 alone
recovers floor ≈ 0 and validates nothing. The floor the certificate must not false-flag
comes from *mild model misspecification* — a criterion that is mostly rankable but whose
latent log-odds surface has a small non-gradient component that survives infinite data.

Generate it directly and by known amount:

    latent_flow = D0 @ theta  +  eps * h_unit        # on the fixed-mask edge set
      theta   : the standardized gamma-shaped potential of §2.4 (held fixed per seed)
      h_unit  : a UNIT harmonic direction of the SAME graph AND THE SAME FILLING,
                = hodge.harmonic_basis(D0, D1)[:, 0]   (recompute per mask; needs b1 >= 1)
                -- the floor is eps^2 only if injection and measurement share a filling;
                   inject against 'empty' and read on 'observed' and the mass reclassifies
      eps     : misspecification strength (the knob)
    p_e = sigmoid(latent_flow);   then sample k Bernoulli/edge as in §2.4

Because P_h @ h_unit = h_unit, the **budget-independent floor is exactly eps^2** — a known
oracle (§7). *(Verified to machine precision: eps = 0.1 / 0.2 / 0.4 give ||P_h.latent||^2 =
0.010000 / 0.040000 / 0.160000.)* eps = 0 is the exact-BTL negative control (floor 0). eps > 0 is the
innocent-but-slightly-incoherent criterion; the threshold must sit above its floor.

This is INNOCENT mild incoherence on a comparable graph — distinct from the C–C block
(full non-rankability) and from the finite-k logit bias (a separate O(1/k^2) term, §7).

Config: `eps: [0.0, 0.1, 0.2, 0.4]`  (0.0 = negative control).
Note: direct h-injection is the *calibration* knob (exact floor); realistic misspecification
models (intransitive-BTL, blade-chest) are validation targets, out of scope for v1.

### 2.6 Regime validity — preconditions for §8.5 (fail loudly, don't fit through them)

`floor + c/k` holds only in a bounded (beta, eps, k, n) window; outside it the fit
silently misreports the floor. Check the window in closed form (no sampling) and refuse
to fit outside it.

**Fit window (the binding control).** *(Delta A, v6 — the window is DERIVED, not declared.)*
Sample the full `k` grid, but fit the floor only on a window computed per config:

    required_fit_k_min = c_oracle / (rho * floor)          # rho = resolvability margin
      c_oracle = tr(P_h . diag(1/(p_e(1-p_e))))            # §7, closed form
      rho      = 3.0 by default -- JUSTIFIED, NOT OPTIMISED (see the v6 residual note)

    A k grid that cannot reach required_fit_k_min is flagged `grid_insufficient` and
    NOT fitted. Never fit anyway on a short grid.
    fit_k_min = 64 is retained ONLY as a floor on the default budget; the derived
    value governs.

Why derived: the constant 64 was itself calibrated on `filling='observed'`, so it is
wrong under any filling with a different `c_oracle`. Measured on one graph, `eps=0.3`,
true floor 0.090:

    filling     b1    c_oracle   floor @ k>=64   floor @ k>=256
    observed     2          17          0.0807           0.0850
    empty       20         160          0.0156           0.0726

**This dissolves the observed/empty fork.** With a derived window both fillings recover,
given a grid that reaches the requirement — so no per-experiment filling commitment is
needed for the floor. It also closed most of the parked residual: deriving the window
took recovery from 0.87x-0.95x to 0.94x-1.01x.

The following comparison is retained as an ILLUSTRATION ON THE OBSERVED GRAPH — it is
what justifies truncating rather than modelling the contaminating term, and that verdict
stands regardless of where the window falls:

    fit floor+c/k on k=[8..1024]   -> floor bias 0.83x .. 2.48x, gamma-drift 15-21%
    fit floor+c/k+c2/k^2           -> 0.58x .. 0.90x, drift up to 28%  (ill-conditioned;
                                      the extra term eats the intercept -- do NOT use)
    fit floor+c/k on k>=64 ONLY    -> 0.87x .. 0.95x, gamma-drift <= 7%

Drop the low-`k` points; do not model the term.

**Upper bound — clamp saturation.** At extreme separation `p_e -> 0/1`, wins saturate at 0
or `k`, the clamp forces `Y = ∓log(2k−1)` — a distortion that GROWS as `log(2k)`, breaking
the model.

    saturation = mean_e[ p_e**k_min + (1−p_e)**k_min ]           # cheap pre-filter
    require saturation < 0.2     (verified: 0.17 fits, 0.42 breaks)
The clamp is NOT widened to fix this — it is the instrument's estimator contract.
Characterising the saturation artefact (near-deterministic edges) is PARKED, out of scope.
*(Correction, v5 — measured: saturation does NOT grow with γ once θ is standardized per
§2.4, measured flat at 0.165 → 0.151 for γ ∈ {1, 1.5, 2, 3, 4, 6}. Fixed `std(theta)` is
exactly what stops skew from moving the extremes.)*

**Lower bound — mildness.** The injection must stay INNOCENT, not adversarial:

    require eps**2 / ‖D0θ‖**2 < 0.05      # injected harmonic is a small fraction of gradient
Note this gate is slack for the default grid (`eps=0.4, beta=0.3` gives 0.0029, ~17x inside
the bound); it binds only against grossly adversarial `eps`. Report it; do not rely on it.

**`c`-oracle agreement — necessary, NOT sufficient.** *(Correction, v5 — measured.)* Fit
`floor + c/k`, then require the fitted `c` to agree with the §7 delta-method oracle
`c = tr(P_h·diag(1/(p_e(1−p_e))))` within ~1.5×. Disagreement ⇒ the fit is misspecified,
NOT a floor. This caught `beta=0.6` (`c_fit/c_oracle ≈ 0.2`) where the floor alone looked
entirely plausible. **But it does not bind on floor accuracy:** at `beta=0.25` it reads
`c_fit/c_oracle = 1.01` while the floor is **1.86×** too high, and at `beta=0.30` the 95%
CI `[0.111, 0.273]` *excludes* the true `0.09` — a confident wrong answer that passes this
gate. Keep it as a necessary condition; the fit window above is what actually protects the
floor.

**Defaults (Delta E, v6 — CONFIRMed against the shipped code, with one correction).**
`beta = 0.25`, `n_int = 12`, `eps <= 0.4`, `k_min >= 8` (sampling), `fit_k_min >= 64`
(floor on the derived window).

- **`beta`: 0.3 → 0.25. Confirmed.** At 0.3 the saturation gate rejects **43.5%** of masks
  (n=12, p=0.45, k_min=8, 2000 masks) and `strict=True` raises. At 0.25: **0.5%** rejection,
  p95 saturation 0.178. *(The change-set estimated 47% and "0% rejection"; measured 43.5%
  and 0.5%. Use `beta = 0.22` for literally 0%.)*
- **`n_int`: 8 → 12. Confirmed as a problem — but the fix does NOT do what was expected.**
  At `n_int=8` under `filling='observed'`, **28.8%** of masks have `b1 = 0`. Moving to 12
  gives **10.8%**, not 0 — and `n_int=14` gives 11.9%, so **it plateaus; no `n_int` drives
  it to zero.** What the change actually fixes is a different path: under the rig's own
  default `filling='empty'`, `n_int=8` makes `assemble()` raise on **1.75%** of seeds, and
  `n_int=12` takes that to **0.0%**. Adopt 12 for that reason, not the stated one.
- **Masks with `b1 = 0` are dropped, and the drop is REPORTED.** `floor_measurement` skips
  them — there is no harmonic direction to inject into — at ~9-11% under `observed`. That is
  a real reduction in sample size, so `n_seeds_dropped_b1_zero` and `seed_drop_rate` ship in
  every record: **a CI must not be read as if it came from the full seed budget.**

Report `saturation`, `eps²/‖D0θ‖²`, `c_fit / c_oracle`, `fit_k_required`, `fit_k_effective`,
`grid_insufficient`, and `seed_drop_rate` in every §8.5 record.

---

## 3. Sweep axes & config schema

1. **Null strength** — `k` (comparisons/edge) and `p` (edge-retention / sparsity) on the noisy-BTL generator. Sweeps the innocent null: prediction `harmonic = floor + c/k` (floor possibly zero; that is what we are measuring). θ fixed across the whole `k`-sweep (§2.4).
2. **Adversarial proportion** — `m/(n+m)` complex fraction. Sweeps the systematic harmonic floor upward.
3. **Bridge mode** — `{variance_fresh, bias_rule, variance_fixed}`, optionally swept.
4. **Filling / topology** — `{empty, observed, custom}` and edge sparsity. Controls `b₁` and the curl/harmonic split.
5. **θ-asymmetry (γ)** — the latent-scale shape exponent of §2.4. **Secondary**, not the floor axis: `P_h·D0θ = 0` at every γ. Sweeps `c` (§7) and the `O(1/k²)` finite-k bias.
6. **Misspecification (`eps`)** — §2.5, **the floor axis**. Known oracle `floor = eps²`; `eps = 0` is the negative control whose floor CI must cover 0. Primary output: **fitted floor vs `eps`, with CI.**

```yaml
n_int: 8
n_cplx: 5
mode_II: null_btl              # clean_gradient | null_btl
btl:
  beta: 0.3                    # §2.6; anywhere in [0.15,0.30] works on the k>=64 window
  p: 0.45
  k: [8,16,32,64,128,256,512,1024]   # SAMPLING grid (k_min >= 8, §2.6)
  fit_k_min: 64                # FITTING window -- floor fitted on k >= 64 ONLY (§2.6).
                               # Not a tuning knob: below this the O(1/k^2) bias of §7
                               # is absorbed into the intercept (0.83x-2.48x floor bias).
  theta_shape: gamma           # gamma | random   (gamma is the primary probe, §2.4)
  gamma: [1.0, 1.5, 2.0, 3.0]  # 1.0 == symmetric NEGATIVE CONTROL
  standardize_theta: true      # REQUIRED: match std to the gamma=1 reference (§2.4)
  fixed_mask_across_k: true    # REQUIRED: P_h must not move with k (§2.4)
eps: [0.0, 0.1, 0.2, 0.4]      # §2.5 MISSPECIFICATION = THE FLOOR AXIS; oracle floor = eps^2
                               # 0.0 = negative control (floor must be 0; CI must cover 0)
complex_pool: equal_spaced     # equal_spaced | random | surrogate_defeating
bridge_mode: bias_rule         # variance_fresh | bias_rule | variance_fixed
bridge_gap: 1.0                # bias_rule offset below min(s_int)              (§2.3)
bridge_R: 8                    # comparisons per bridge pair; MUST be >= 2      (§10)
filling: empty                 # empty | observed | custom     (rig default: empty)
mixed_triangles_filled: false
edge_density: 1.0
block_scale: {ii: 1.0, cc: 1.0, ic: 1.0}   # RAW by default; logged, never implicit (§5.7)
emit_k: 8                      # rows per pair in the judgment log; MUST be >= 2 (§10)

# --- run budget: pinned, and echoed into every output record (§9) ---
seeds: 64                      # replicates for the §8.5 floor CI
seed: 0                        # base seed; per-config seed = f(seed, config hash)
# --quick reduces `seeds` and shortens the `k` grid for smoke runs; the default
# budget is whatever makes the floor's CI meaningful enough to separate from zero.
```

---

## 4. Topology / filling convention (declared, frozen, logged)

The curl/harmonic boundary is a **modelling choice**, set by which triangles are 2-cells. Names match `triangles_for_filling`:
- **`empty`** — no 2-cells; curl space trivial; all non-gradient mass is harmonic. **Rig calibration default** (unambiguous harmonic reading).
- **`observed`** (alias **`full`** on a complete graph) — every triple whose three edges are present. Collapses harmonic where triangles exist. This is `analyze_comparisons`'s default (matches a real sparse arena).
- **`custom`** — explicit triangle list.
- **`mixed_triangles_filled`** — bridge triangles `(int,int,complex)` / `(int,complex,complex)`; filling them reclassifies bridge variance harmonic→curl. Keep explicit.

`b₁ = |E| − rank(D0) − rank(D1)` is reported for every config. Note: on `empty`, `b₁` can be large (holes) yet an exact gradient still reads `h = 0` — the holes are *room*, not occupancy.

---

## 5. Load-bearing invariants (must enforce)

**5.1 — Integer / bias-bridge flow must be magnitude, never ±1.** A ±1 sign flow of even a perfectly transitive order is *not* a pure gradient — quantization deposits spurious harmonic on `empty`. The spurious mass is **`n`-dependent, not a constant**: verified `h = 0.200` at `n=5` and `h = 0.2222` at `n=6` (complete graph). Quote it with its `n`. Use value-difference or log-odds. `flow='pm1'` is for reading the tournament for ζ only.

**5.2 — Unit circle defeats the magnitude surrogate; richer pools defeat all surrogates.** On `|z|=1` all magnitudes tie. For `surrogate_defeating` pools, place points so real-part / magnitude / argument orders mutually disagree.

**5.3 — Coin flip: fresh-per-comparison = variance (decays); fixed-per-pair = systematic (persists).** Never let `variance_fixed` happen by accident.

**5.4 — Topology-normalize across configs.** `b₁`, projector, and noise covariance move with the graph. Compare the harmonic *fraction* (report the `(g,c,h)` simplex + total mass + `b₁`), never raw energy across different topologies.

**5.5 — Equal spacing for the "reduces to all curls" state.** Only the divergence-free (equal-spaced, `grad=0`) C–C block reduces to *pure* curl under filling.

**5.6 — The innocent null is noisy-sparse-*comparable*, not the noiseless pool and not the bridge.** Calibrate the threshold on `sample_sparse_btl_logodds` (§2.4). The noiseless pool (`h=0`) understates it; the bridge (§2.3) is incomparability, a different distribution. Sweep the θ-asymmetry exponent γ rather than asserting one "asymmetric" shape — but do **not** expect γ to produce the floor: `P_h·D0θ = 0` identically, at every γ (§2.4, measured). The floor is the `eps` of §2.5, whose negative control is `eps = 0`, not `γ = 1`.

**5.7 — Block scale is explicit, logged, and factored out of the claims.** I–I log-odds (magnitude ~0.5–3), C–C ±1, and bridge ±1 carry different per-edge energy, so the harmonic *fraction* of a mixed config moves with the block scale as well as the item mix. Generate raw (`block_scale` all 1.0) and **log per-block RMS, total mass, and `b₁` on every config**. State §8.7's monotonicity on the `k`-independent fitted floor at fixed block scale (§8.7) — never on the raw harmonic fraction, which would confound "more complex items" with "complex edges carry more energy".

---

## 6. Instrument API (import from `hodge.py`; do not fork)

Public surface the rig calls:
```
build_operators(n, edges, triangles)        -> D0 (grad), D1 (curl)
triangles_for_filling(edges, filling, tris) -> 2-skeleton (empty|observed|custom)
hodge_decompose(Y, D0, D1)                  -> {gradient, curl, harmonic, scores}   (lstsq)
hodge_projectors(D0, D1)                     -> P_grad, P_curl, P_harm                (pinv; for oracle)
analyze_flow(n, edges, Y, filling='empty')   -> {(g,c,h), b1, total_mass, ...}        (KNOWN real flow)
analyze_comparisons(n, comps, filling='observed', flow='logodds') -> {..., zeta_hat}  (JUDGMENT LOG)
coefficient_of_consistency(n, directed)      -> zeta_hat                              (Pokharel baseline)
self_checks(...)                             -> math identities; fail loudly
```
The **two doors are different tests**: `analyze_flow` validates the internal `(g,c,h)` on a known real-valued flow (magnitude meaningful, §7 oracle); `analyze_comparisons` validates the judgment-log **round-trip** (§8.10). Different default fillings by design (`empty` vs `observed`) — always pass `filling` explicitly from the rig and log it.

Flow encodings in `analyze_comparisons`: **`logodds`** (default, magnitude-aware — a clean order reconstructs as a near-exact gradient), `signed` (`2·winrate−1`), `pm1` (majority sign — the §5.1 trap; ζ-reading only). Repeated `(winner,loser)` rows aggregate, so magnitude survives.

---

## 7. Known-answer oracle

Per config, compute the exact expected decomposition (using `hodge_projectors`) and report `measured − oracle`:
- **All-integer, clean gradient**: `h = 0` (both fillings). *(verified)*
- **Equal-spaced complex-only**: `empty h=1, g=0`; `observed c=1, h=0`. *(verified)*
- **`b₁`(complex-only, empty)** `= (m−1)(m−2)/2`; generally the rank formula. *(verified)*
- **Statistical null (noisy sparse BTL)**: `E‖P_h·Y‖² = ‖P_h·bias‖² + tr(P_h Σ)/k` = `floor + c/k`; harmonic fraction decays with `k`. Floor magnitude is the measurable unknown (Epic C). The variance term is predictable, so `c` is an oracle too, not just a fitted nuisance: by the delta method on `logit(p̂_e)`, `Σ = (1/k)·diag(1/(p_e(1−p_e)))`, giving `c = tr(P_h · diag(1/(p_e(1−p_e))))` with `p_e = σ(theta_j − theta_i)`. Report fitted `c` against this predicted `c` — agreement is what licenses reading the intercept as a floor rather than as fit misspecification. *(Settled: this is the misspecification guard, not an optional diagnostic.)* Because the model is linear in `(floor, c)` under `x = 1/k`, fit by OLS **per seed** (the mask, hence `P_h` and the true floor, is fixed within a seed by §2.4), then aggregate across seeds — **restricted to `k >= fit_k_min`, since this `O(1/k^2)` term is precisely what contaminates the intercept at small `k` (§2.6).**
- **Misspecified null (§2.5)**: budget-independent floor `= eps²` exactly, against the same graph *and filling* the injection used. *(verified to machine precision)*
- **Variance bridge**: `‖P_h·fixed‖² + tr(P_h Σ_bridge)/R`.
- **Bias bridge**: harmonic `=` C–C floor **exactly** — not approximately, and not "up to the bridge's contribution". *(verified: `10.0000` vs `10.0000` at `n_int=6, n_cplx=5, empty`; a constant bridge instead reads `57.7273`.)* Requires the potential-consistency of §2.3.

---

## 8. Acceptance tests (definition of done)

1. `self_checks` all pass on every generated config (`D1@D0=0`, reconstruction, orthogonality, div/curl-free harmonic, `dim(harmonic)=b₁`).
2. All-integer clean pool → `h ≈ 0` on `empty` and `observed`. *(verified)*
3. Equal-spaced complex-only → `empty h≈1,g≈0`; `observed c≈1,h≈0`. *(verified)*
4. `b₁` matches `(m−1)(m−2)/2` (complex-only empty) and the rank formula generally. *(verified)*
5. **Floor recovery (the Epic-C measurement):** sweep `eps` (§2.5) and recover the
   budget-independent floor as `eps^2` (oracle), with a **CI across seeds** — a point
   estimate is not acceptable. Procedure, in order; each step is a gate, not advice:
   1. **Assert the §2.6 preconditions before fitting anything.** Refuse to fit outside the
      window; a loud failure is the correct output, not a floor number.
   2. **Fit `floor + c/k` on `k >= fit_k_min` (default 64) only** (§2.6). Do *not* fit the
      full sampling grid, and do *not* add a `c2/k^2` term — both are measured to be worse.
   3. **Report the floor only when the `c`-oracle gate passes** (§7, within ~1.5×) — but
      treat that as necessary, not sufficient (§2.6): it passes at `beta=0.25` while the
      floor is 1.86× wrong.
   4. **Floor must equal `eps^2` within its CI**, and be **monotone in `eps^2`**.
      `eps = 0` is the negative control: its floor CI must cover 0.
      **(Delta F, v6 — HELD STRICT.)** The criterion is deliberately not loosened. Widening
      the tolerance would hide exactly the residual that tuning ρ is meant to remove. Known
      exceptions are *documented*, not tolerated: over 48 seeds × 4 γ coverage is 16/20, and
      the failing cells are recorded in the v6 residual note. Any exception encoded in the
      suite must be `xfail(strict=True)`, so it flips to a **failure** the moment the bias
      closes and forces this clause to be revisited rather than carrying a stale exemption.
      *(This is not hypothetical: the two exceptions Delta D recorded went stale as soon as
      the `k` grid was extended, and the strict marker is what surfaced it.)*
   5. **Floor must be invariant across γ** — γ shapes `c` and the `O(1/k^2)` bias, never the
      floor (§2.4). Require drift `< 15%` across the γ grid. *(This is satisfiable only on
      the `k >= 64` window: measured drift 0.8–7.1% there vs 15–21% on the full grid.)*
   Report floor-vs-`eps` with CI, and the §2.6 diagnostics alongside every number.
6. `variance_fresh` bridge decays as `1/R`; `bias_rule` bridge adds no harmonic; `variance_fixed` persists — three correctly-labelled behaviours.
7. Adversarial-proportion sweep: the **`k`-independent fitted floor, at fixed default block scale**, is monotone non-decreasing in complex fraction, and is separable from the null's decaying term by its `k`-independence. **State the claim on the fitted floor, not on the raw harmonic fraction** — the fraction also moves with the per-block energy mismatch of §5.7, so a monotone fraction would not be evidence of a monotone systematic floor. Per-block RMS is logged alongside, so the mismatch stays visible even though it is factored out of the claim.
8. ζ (`coefficient_of_consistency`) reads curl / triad-consistency and **misses** the harmonic the rig plants where triangles are unfilled (the divergence region).

   **Construction guidance (Delta C, v6).** The claim is correct; the *demonstration* is easy to
   build on the wrong graph. It requires **missing triangles**. Do **not** use the equal-spaced
   complete complex pool: there every triple is observed, so ζ reads the C–C cycles correctly
   (**ζ = 0.0**, maximally inconsistent), and the harmonic reading of 1 exists only under the
   `empty` filling *choice* — the same flow is pure curl on `observed` (§8.3). Construct instead
   a **4-cycle beside a transitive triangle**: ζ sees only the one triple it can, finds it
   perfectly transitive, and reports **ζ = 1.0** — "perfectly consistent" — while **h > 0.3** of
   the flow's energy is harmonic and unrankable. *(The first §8.8 test asserted ζ-perfect-
   consistency on the complete pool and was simply wrong. A green suite asserting the wrong
   invariant is worse than a red one.)*
9. All measured `(g,c,h)` within tolerance of the oracle (§7).
10. **Round-trip:** the emitted judgment log, fed to `analyze_comparisons(filling='empty')`, reproduces the rig's internal `(g,c,h)`. Validates the *actual* pipeline.

---

## 9. Outputs

Sweep harness over `(null-strength × adversarial-proportion × bridge-mode × filling × γ × eps)`; per-config record of `(g,c,h)`, total mass, **per-block RMS (ii / cc / ic)**, `b₁`, ζ, oracle value, deviation, fitted `floor` **with CI** and fitted `c` vs its §7 prediction, seed, full config echo, and the **run-budget echo** (seed count, `k` grid, axis ranges, `--quick` on/off) so any record states the budget that produced it. Figures: harmonic energy vs `k` (null decay, one series per γ); **fitted floor vs `eps` with CI band and the `eps²` oracle overlaid, `eps=0` marked as the negative control**; fitted floor vs γ (secondary, expected flat); fitted `c` vs its §7 delta-method oracle; systematic floor vs adversarial proportion; bridge-mode reference lines; ζ-vs-harmonic divergence. Reproducibility: seed + filling + all params logged; same config+seed ⇒ identical output.

---

## 10. Integration with the existing pipeline

Emit synthetic comparisons in the real judgment-log schema:
```
(winner, loser, position_shown, criterion, timestamp)
```
Repeats aggregate inside `analyze_comparisons`, and `flow='logodds'` recovers magnitude — so to reproduce an intended real-valued flow, emit per-comparison win/loss outcomes whose empirical win-rate matches it.

> **CORRECTION (v3). v2 said "for ±1 rules emit a single deterministic row". That is wrong and silently destroys the round-trip.** `analyze_comparisons` sets `clamp = 1/(2k)`; at `k=1` that clips `p̂` to exactly `0.5`, so `Y = log(0.5/0.5) = 0` on **every** edge. Measured: `total_mass = 0.000000`, all fractions zero. Emission must use **`R ≥ 2` rows per pair**, floored at 2 in §3 with a loud error.

> **CORRECTION (v6, Delta B). `R ≥ 2` is necessary but NOT sufficient.** A ±1 rule pushed
> through the *quantized* path at `k = 2` computes `round(2·σ(1)) = 1` — a 1–1 tie — which the
> clamp pins straight back to zero. The same trap, one level down. Emission therefore has
> **three paths, chosen per block, and they are not interchangeable.**

| path | used by | operation | result |
|---|---|---|---|
| **`counts`** | noisy-BTL null, variance bridges | replay the generator's own win counts | **bit-exact** (measured diff `0.00e+00`) |
| **`sign`** | ±1 rules: C–C rotational, `variance_fixed` | emit `R` rows one way → `±log(2R−1)` | exact **only if the config is entirely a sign rule** |
| **`magnitude`** | clean-gradient I–I, `bias_rule` bridge | `w = round(k·σ(Y))` | residual **reported**; exact only as `k_emit → ∞` |

**The `sign` path is gated.** Mass fractions are scale-invariant, so `±log(2R−1)` against a
`±1` target is exact for a sign-only config — but in a **mixed** config it rescales the C–C
block against its neighbours by ~2.7× and *changes the very mix being measured*. Measured: a
round-trip error of **0.269** presenting as a decomposition result. The rig **refuses the sign
path in any config that is not sign-only**; gated, the same config reads 0.0024 and falls
monotonically with `emit_k` (0.0374 → 0.00014 from `emit_k` 8 → 2048).

**Collapse guard.** Distinguish *ordinary quantization loss* from *destruction of the flow*.
An edge whose target lies inside the representable band `|Y| ≤ log((k+1)/(k−1))` should emit a
tie, and that loss is reported via the residual. What must never pass silently is the whole
flow quantizing to zero: the rig **raises** in that case, and **counts** the edges lost to
rounding otherwise. `analyze_comparisons` derives `k` per pair, so mixed row counts across
blocks are legal.

**Why this is load-bearing:** both failure modes produce a *well-formed decomposition* rather
than an exception. That is exactly what makes them dangerous — nothing downstream can tell that
the number it received is meaningless.

Tag `criterion` with the condition (`null_k16_gamma2`, `adversarial_equal_spaced`, `bridge_bias`, …). Pass `filling='empty'` for round-trip checks. `position_shown` supports later order-effect tests.

---

## 11. Suggested module layout

```
hodge.py       # THE INSTRUMENT, at the repo root, byte-identical to
               # design/reference/hodge.py (same sha256 -- git proves no fork)
conftest.py    # puts the repo root on sys.path so `import hodge` / `import rig` work
rig/
  config.py    # config dataclass + YAML load + defaults + run-budget echo
  pool.py      # integer + complex generators (equal_spaced, random, surrogate_defeating)
  flows.py     # I-I clean gradient; sample_sparse_btl_logodds (the NULL) + gamma theta;
               #   C-C rotational; bridge modes
  graph.py     # edge typing, sparsity, block assembly + per-block RMS;
               #   filling delegated to hodge.triangles_for_filling
  oracle.py    # analytic (g,c,h)/b1 via hodge.hodge_projectors; floor + c/k model
  fit.py       # OLS floor+c/k per seed; bootstrap CI across seeds (SS8.5)
  sweep.py     # config enumeration + run harness + oracle deviation
  emit.py      # write judgment-log schema for hodge.analyze_comparisons() (R >= 2!)
  report.py    # tables + figures
  # hodge.py is IMPORTED (single-file module placed on path), never reimplemented
tests/         # SS8.1-8.10 acceptance + SS5.1-5.7 invariants; must stay fast (~30s)
```

---

## 12. Out of scope (future phases — do not build yet)

- **LLM comparator axis:** swap the synthetic comparator for a real LLM; read its harmonic deviation against the two synthetic bridge reference lines (thrash vs surrogate) to classify failure mode. Held until §8 passes.
- **Multi-block partitions:** integer-partition (not Bell) enumeration of block sizes; `total harmonic dim = Σ (kᵢ−1)(kᵢ−2)/2`; direct-sum (no cross-block cycles) unless bridged.
- **Representation-theory slab:** decompose harmonic mass by Sₙ irreducible type for a *shaped* adversarial alternative (RAN-18, route 3).

---

**One-line summary for the implementer:** generate integer/complex/bridge edges with known gradient/harmonic/variance signatures — with the innocent **null** carried by *noisy, sparse, comparable* BTL data (not the noiseless pool, not the bridge) — sweep null-strength × adversarial-proportion × bridge-mode × filling × θ-asymmetry (γ) × misspecification (`eps`, the floor axis), and prove via §8 that the existing `hodge.py` recovers the planted structure (and that ζ misses the harmonic) before any LLM is introduced.