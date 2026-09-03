# Provenance index

Every quantity cited in the papers, with the code that produces it, the
tolerance within which a re-run must reproduce it, and the test that pins it
where one does.

Generated 2026-09-03 from commit `d3a5777`
on Python 3.12 / numpy 1.26.4.

```bash
python generate.py     # rebuild evidence.json (~2 min)
python verify.py       # re-run and check every claim against it
python verify.py --fast  # structural claims only, seconds
```

## Reproducibility

Every RNG is seeded from a fixed constant, so on the same numpy every claim
reproduces **bit-exactly** — the last full run showed zero drift on all
37 claims. The tolerances below are the margin allowed for a
different numpy or platform, not slack in the measurement. `exact` claims are
identities or closed forms and are held to machine precision; `stochastic`
claims are Monte Carlo and carry a tolerance set from their measured spread.

## Claims

### Exact (identities and closed forms)

| id | asserts | cited in | tolerance | test |
|---|---|---|---|---|
| `pm1-trap` | A +-1 sign flow of a perfectly transitive order deposits spurious harmonic mass, and the amount is n-dependent, not a constant. | methodology sec 2, 'Magnitude, not sign' (as superseded history) | 1e-09 abs | `test_5_1_pm1_of_a_transitive_order_is_not_a_gradient` |
| `pm1-closed-form` | The spurious harmonic mass of the +-1 flow of a total order on the complete graph is exactly (n-2)/(3n), rising with n toward 1/3. | methodology sec 2, Observation 1 (The sign artefact); bridge sec 3.1, Proposition 2 (The sign of a gradient is not a gradient); spec 5.1; spec v10 revision note; exercises SOLUTIONS.md, exercise 3; exercises ex03_pm1_quantization_trap.py, closed_form() | 1e-09 abs | `test_5_1_pm1_mass_has_a_closed_form_in_n` |
| `clean-gradient-zero` | An all-integer value-difference flow reads zero harmonic under both fillings. | methodology sec 3.1 oracle table | 1e-12 abs | `test_8_2_clean_integer_pool_reads_zero_harmonic` |
| `equal-spaced-complex` | An equal-spaced complex pool is pure harmonic under the empty filling and pure curl under the observed one. | methodology sec 3.1 oracle table; methodology fig 1; bridge sec 6, Definition 1 (The certified quantity) | 1e-12 abs | `test_8_3_equal_spaced_complex_only` |
| `b1-rank-formula` | b1 of a complex-only pool under the empty filling is (m-1)(m-2)/2. | methodology sec 3.1 oracle table | exact | `test_8_4_b1_matches_rank_formula` |
| `eps-squared-floor` | The injected misspecification gives a budget-independent floor of exactly eps^2. | methodology sec 3.1 oracle table; methodology sec 4; methodology fig 2 | 1e-12 abs | `test_2_5_injected_floor_is_exactly_eps_squared` |
| `gradient-annihilated` | P_h annihilates D0.theta for every theta, so no latent shape can produce a budget-independent floor. | methodology sec 4, Observation 2 (The exact null has floor exactly zero); methodology fig 2 | 1e-09 abs | `test_5_6_theta_shape_can_never_produce_a_floor` |
| `bridge-invariance` | A potential-consistent bridge leaves the harmonic energy equal to the circle block's; a constant bridge does not. | methodology sec 3.2; bridge Theorem 1 (Bridge-invariance); bridge sec 8.1 | 1e-09 abs | `test_8_6_three_bridge_behaviours_are_correctly_labelled` |
| `surrogate-level-invariance` | Harmonic energy is invariant across the whole admissible bridge class, which is exactly a shift of the surrogate level, under both fillings and across a 2000x range. | bridge sec 8.1 table | 1e-09 abs | `test_bridge_invariance_under_surrogate_level` |
| `systematic-floors` | Only the potential-consistent bridge satisfies Corollary 1's hypothesis; the zero-centred coins carry a systematic floor. | bridge sec 8.2 table | 1e-09 abs | `test_zero_mean_bridge_leaves_a_persistent_bias` |
| `properness-hypothesis` | Theorem 1's properness clause needs Ph B_const != 0, and b1 > 0 does not supply it. Across sparse glued configurations under the observed filling, EVERY failure of the strict inequality has Ph B_const = 0 -- all of the b1 = 0 cases, where Ph annihilates every flow, and a minority of the b1 > 0 cases, where the non-gradient residual lies in im D1^T. No configuration with Ph B_const != 0 fails. | bridge sec 4, Theorem 1 (Bridge-invariance) | exact | — |
| `spread-scaling` | The persistent bias equals ||P_h (D0 s)|Eb||^2 and is exactly quadratic in the integer scale; at zero spread it is exactly zero. | bridge sec 8.3(i); bridge sec 8.3(ii) | 1e-09 abs | — |
| `fabricator-family-invisible` | A family of internally-gradient fabricators is invisible in every moment, not only the mean: range Cov(B) lies inside im D0, so tr(P_h Cov(B) P_h) is zero and both terms of the bias-variance identity are blind to the family. Measured on the operator, not only on the energy: the covariance's leakage out of im D0 is machine epsilon RELATIVE to its own spectral norm, no single realisation has nonzero harmonic part, and every energy sits within 1.4e-12 of the circle floor -- which bounds every central moment at once, not just the second. | bridge sec 6.1, Proposition 3 (Gradient families are invisible) | 1e-09 abs | `test_gradient_fabricators_are_invisible_in_every_moment` |
| `emit-saturation-count` | The count of edges whose target exceeds the emission headroom log(2*emit_k-1) is exact rather than a draw: under the default mode_II=null_btl the bias_rule bridge is handed theta_gamma, which takes no rng, so the count is a function of gamma and emit_k alone -- 15 at emit_k=8, 5 at 16, 0 from 32 up, and 25/15/15/10 across the gamma grid at emit_k=8. | rig/config.py, the emit_k note; exercises SOLUTIONS.md, exercise 7 part-2 table; exercises SOLUTIONS.md, exercise 7 answers 3 and 4 | exact | `test_8_10_saturation_count_is_exact_in_gamma_and_emit_k` |
| `filling-dependence` | b1 and c_oracle move by nearly an order of magnitude with the filling, so a fixed window calibrated under one is wrong under the other. | methodology sec 5.3 table | 0.02 rel | — |
| `c1-cross-term-completes` | The 1/k coefficient of the harmonic energy is tr(P_h V) + 2 eps (h.b), not tr(P_h V) alone. The cross term COMPLETES the delta-method oracle rather than refining it: measured/closed is 1.0 to 8 dp on both calibration topologies, while variance-only is off by 2.7% and 5.0%. | methodology sec 5.1; methodology sec 9 | 1e-06 rel | `test_7_c1_equals_variance_plus_cross` |
| `c2-variance-dominated` | The 1/k^2 coefficient is 88-95% the SECOND-ORDER VARIANCE of the logit and only 0.6-2.5% the mean-bias term b'P_h b. The natural expectation that the vector driving the 1/k correction also drives the 1/k^2 one is wrong by two orders of magnitude. | methodology sec 5.3; methodology sec 9 | 0.0001 rel | — |
| `v2-closed-forms` | The 1/k^2 variance coefficient has closed form v2 = 2/(pq) + (3/2)(2p-1)^2/(pq)^2 for the shipped clamped logit, and v2 = (1/2)(2p-1)^2/(pq)^2 for a per-edge continuity-corrected estimator. Both match the exact extraction to its own precision; the corrected form is zero at p = 1/2. | methodology sec 5.3; methodology sec 9 | 0.005 abs | — |
| `firth-localises-boundary` | A per-edge continuity-corrected estimator removes the c1 cross term exactly (c1_F = tr(P_h V)) and annihilates the 2/(pq) near-boundary term of v2, cutting the asymmetry term 3/2 -> 1/2. The resulting c2 ratio is bounded in (0, 1/3) and is set by the P_h-weighted edge-probability mix -- 13.5% on a mid-range topology, 22.7% on one whose edges reach p ~ 0.07. No universal reduction factor exists. | methodology sec 9 | 0.0001 rel | — |
| `adversarial-monotone` | The systematic floor follows m(m-1)/2 exactly, while the raw harmonic fraction moves far less, being diluted by per-block energy. | methodology sec 9 | 1e-06 abs | `test_8_7_systematic_floor_monotone_in_complex_fraction` |
| `zeta-blind` | On a 4-cycle beside a transitive triangle, zeta reports perfect consistency while a third of the energy is harmonic. | methodology sec 9 | 1e-09 abs | `test_8_8_zeta_misses_the_planted_harmonic` |

### Stochastic (Monte Carlo)

| id | asserts | cited in | tolerance | test |
|---|---|---|---|---|
| `thrashing-does-not-wash-out` | The bridge block alone decays as 1/R, but the combined flow converges to the systematic floor, not to the circle floor. | bridge sec 8.2 table; bridge Remark 6 (A thrashing judge does not wash out) | 0.05 rel | `test_zero_mean_bridge_leaves_a_persistent_bias` |
| `fabricator-mean-only-control` | The negative control for fabricator-family-invisible. A family that is gradient only IN MEAN leaves the AVERAGE harmonic energy at the circle floor too, so the energy check alone cannot tell the two apart. The operator measurements can: adding a zero-mean harmonic jitter takes the relative leakage of Cov(B) out of im D0 from machine epsilon to 7e-3, and lifts the mean energy from the floor to about 11.0 -- which is exactly tr(P_h Cov(B) P_h) entering the bias-variance identity. Without this arm the four machine zeros beside it could not be shown capable of failing. | bridge sec 6.1, Proposition 3 (Gradient families are invisible) | 1e-06 rel | `test_gradient_fabricators_are_invisible_in_every_moment` |
| `emit-roundtrip-deviation` | The magnitude path round-trips only as emit_k -> inf, and the deviation at a given emit_k is a single draw -- emit_k sits in the config fingerprint, so each row is its own assembly. residual_max falls monotonically where the deviation does not, and the seed-0 deviation at emit_k=8 is the top of its 20-seed range. | rig/config.py, the emit_k note; exercises SOLUTIONS.md, exercise 7 part-2 table; exercises SOLUTIONS.md, exercise 7 answers 2 and 4 | 0.05 rel | — |
| `fit-window` | Fitting the full k grid biases the intercept; restricting to k >= 64 recovers it. The floor is an intercept, so the window decides it. | methodology sec 5.3; methodology fig 3 | 0.05 rel | — |
| `fit-window-bias-range` | Across the separations sec 2.6 admits, fitting the full k grid recovers the floor at between 0.99x and 1.97x of its true value, while the k >= 64 window holds 0.94x to 1.01x. The full-grid error grows with beta and shrinks with gamma, so it is a range over the operating region and not a constant. | methodology sec 5.3; rig/fit.py, the module docstring | 0.05 rel | — |
| `delta-method-cross-term` | The 1/k coefficient omits the plug-in logit mean bias; including its cross term flattens the guard's drift in eps. | methodology sec 5.1 | 0.05 rel | — |
| `residual-across-draws` | The residual is real but small, and any single run lands anywhere in a band about a percentage point wide; coverage is typically 15/16. | methodology sec 7, the reporting-discipline example; methodology sec 9 table; methodology fig 5; methodology v7 note | 0.5 abs_pct | — |
| `rho-tradeoff` | The residual falls monotonically as rho falls, because a smaller rho demands a longer tail -- but cells become unfittable as the grid stops reaching the window, so rho and the grid must be tuned together. | methodology sec 9; methodology fig 6 left; methodology v7 note | 0.8 abs_pct | — |
| `b1-non-monotone` | The b1=0 rate is non-monotone in n with an interior minimum; past it, more items destroy the holes the certificate reads. | methodology sec 10, Observation 3 (non-monotone in the item count); methodology fig 6 right | 0.02 abs | — |
| `kahle-finite-n` | The vanishing threshold decays as the theory requires, but the asymptotic exponent is not yet visible at these sizes. | methodology sec 10 footnote | 0.05 abs | — |
| `fixed-window-fixture` | The retired fixed k >= 64 window, run against today's rig, reproduces the SHAPE of the sec 6 incident at the old default separation beta = 0.3: a floor about 12% low -- entirely plausible, and the reason it passed unexamined -- while the c-oracle disagrees by about 27%, which is what flagged it. Past beta = 0.5 the fixed window is worse than the derived one at every separation. The incident's own digits are NOT reproduced and are not recoverable: that run predates Delta A and Delta E and its configuration was never recorded. | methodology sec 6 | 0.05 rel | `test_retired_fixed_window_reproduces_the_guard_incident` |
| `guard-blind-spot` | The c-oracle check is necessary but not sufficient: configurations exist that pass it while the floor is badly wrong. | methodology sec 6; methodology fig 4 | 0.1 rel | — |
| `saturation-gate` | beta=0.3 sits on the saturation gate; 0.25 clears it. | methodology sec 6; spec sec 2.6, Delta E | 0.02 abs | `test_2_6_saturation_gate_rejects_extreme_separation` |
| `residual-exact` | With Monte Carlo removed (exact binomial energies) the two-parameter floor is under-read by +0.36% over 20 base seeds with a standard error of 0.002 pt. The shipped +-0.09 pt band is therefore almost entirely reps=16 sampling noise, not base-seed variation: the underlying quantity is near-deterministic. | methodology sec 9 table; methodology fig 5; methodology v8 note | 0.02 abs | — |
| `residual-fit-variants` | Because c2 is a closed form it can be subtracted rather than fitted. Subtracting it removes most of the residual; fitting it as a free third parameter removes essentially all of it on exact energies. Both are reported across base seeds -- these are topology-dependent, not single draws. | methodology sec 5.3; methodology sec 9 | 0.02 abs | — |
| `residual-tracks-c2` | Changing the edge estimator moves the residual in the proportion its c2 moves. A per-edge continuity-corrected estimator has 22.75% of the raw c2 on this topology and yields 22.88% of the raw residual -- agreement to under 0.2 pp, with no Monte Carlo on either side. Residual is proportional to c2. | methodology sec 9 | 0.05 rel | — |

## Reading the data

`evidence.json` holds each claim's full value under `claims.<id>.value`.
Figures are regenerated from it by `../make_figures.py`; the figure PDFs and
`runs/` are build products and are not committed.

A claim with no test is checked only by `verify.py`. A claim with a test is
checked twice: `verify.py` compares its value, and the test re-derives it
independently in the acceptance suite.
