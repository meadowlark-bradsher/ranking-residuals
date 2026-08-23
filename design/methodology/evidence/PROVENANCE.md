# Provenance index

Every quantity cited in the papers, with the code that produces it, the
tolerance within which a re-run must reproduce it, and the test that pins it
where one does.

Generated 2026-08-23 from commit `1df514e`
on Python 3.12 / numpy 1.26.4.

```bash
python generate.py     # rebuild evidence.json (~2 min)
python verify.py       # re-run and check every claim against it
python verify.py --fast  # structural claims only, seconds
```

## Reproducibility

Every RNG is seeded from a fixed constant, so on the same numpy every claim
reproduces **bit-exactly** — the last full run showed zero drift on all
23 claims. The tolerances below are the margin allowed for a
different numpy or platform, not slack in the measurement. `exact` claims are
identities or closed forms and are held to machine precision; `stochastic`
claims are Monte Carlo and carry a tolerance set from their measured spread.

## Claims

### Exact (identities and closed forms)

| id | asserts | cited in | tolerance | test |
|---|---|---|---|---|
| `pm1-trap` | A +-1 sign flow of a perfectly transitive order deposits spurious harmonic mass, and the amount is n-dependent, not a constant. | methodology sec 2, 'Magnitude, not sign' | 1e-09 abs | `test_5_1_pm1_of_a_transitive_order_is_not_a_gradient` |
| `clean-gradient-zero` | An all-integer value-difference flow reads zero harmonic under both fillings. | methodology sec 3.1 oracle table | 1e-12 abs | `test_8_2_clean_integer_pool_reads_zero_harmonic` |
| `equal-spaced-complex` | An equal-spaced complex pool is pure harmonic under the empty filling and pure curl under the observed one. | methodology sec 3.1 oracle table; methodology fig 1 | 1e-12 abs | `test_8_3_equal_spaced_complex_only` |
| `b1-rank-formula` | b1 of a complex-only pool under the empty filling is (m-1)(m-2)/2. | methodology sec 3.1 oracle table | exact | `test_8_4_b1_matches_rank_formula` |
| `eps-squared-floor` | The injected misspecification gives a budget-independent floor of exactly eps^2. | methodology sec 3.1 oracle table; methodology sec 4; methodology fig 2 | 1e-12 abs | `test_2_5_injected_floor_is_exactly_eps_squared` |
| `gradient-annihilated` | P_h annihilates D0.theta for every theta, so no latent shape can produce a budget-independent floor. | methodology sec 4, Observation 1; methodology fig 2 | 1e-09 abs | `test_5_6_theta_shape_can_never_produce_a_floor` |
| `bridge-invariance` | A potential-consistent bridge leaves the harmonic energy equal to the circle block's; a constant bridge does not. | methodology sec 3.2; bridge Theorem 1; bridge sec 8.1 | 1e-09 abs | `test_8_6_three_bridge_behaviours_are_correctly_labelled` |
| `surrogate-level-invariance` | Harmonic energy is invariant across the whole admissible bridge class, which is exactly a shift of the surrogate level, under both fillings and across a 2000x range. | bridge sec 8.1 table | 1e-09 abs | `test_bridge_invariance_under_surrogate_level` |
| `systematic-floors` | Only the potential-consistent bridge satisfies Corollary 1's hypothesis; the zero-centred coins carry a systematic floor. | bridge sec 8.2 table | 1e-09 abs | `test_zero_mean_bridge_leaves_a_persistent_bias` |
| `spread-scaling` | The persistent bias equals ||P_h (D0 s)|Eb||^2 and is exactly quadratic in the integer scale; at zero spread it is exactly zero. | bridge sec 8.3(i); bridge sec 8.3(ii) | 1e-09 abs | — |
| `fabricator-family-invisible` | A family of internally-gradient fabricators is invisible in every moment, not only the mean: Cov(B) lies inside im D0. | bridge sec 8.4, Proposition 3 | 1e-09 abs | — |
| `filling-dependence` | b1 and c_oracle move by nearly an order of magnitude with the filling, so a fixed window calibrated under one is wrong under the other. | methodology sec 5.3 table | 0.02 rel | — |
| `adversarial-monotone` | The systematic floor follows m(m-1)/2 exactly, while the raw harmonic fraction moves far less, being diluted by per-block energy. | methodology sec 9 | 1e-06 abs | `test_8_7_systematic_floor_monotone_in_complex_fraction` |
| `zeta-blind` | On a 4-cycle beside a transitive triangle, zeta reports perfect consistency while a third of the energy is harmonic. | methodology sec 9 | 1e-09 abs | `test_8_8_zeta_misses_the_planted_harmonic` |

### Stochastic (Monte Carlo)

| id | asserts | cited in | tolerance | test |
|---|---|---|---|---|
| `thrashing-does-not-wash-out` | The bridge block alone decays as 1/R, but the combined flow converges to the systematic floor, not to the circle floor. | bridge sec 8.2 table; bridge Remark 5 | 0.05 rel | `test_zero_mean_bridge_leaves_a_persistent_bias` |
| `fit-window` | Fitting the full k grid biases the intercept; restricting to k >= 64 recovers it. The floor is an intercept, so the window decides it. | methodology sec 5.3; methodology fig 3 | 0.05 rel | — |
| `delta-method-cross-term` | The 1/k coefficient omits the plug-in logit mean bias; including its cross term flattens the guard's drift in eps. | methodology sec 5.1 | 0.05 rel | — |
| `residual-across-draws` | The residual is real but small, and any single run lands anywhere in a band about a percentage point wide; coverage is typically 15/16. | methodology sec 9 table; methodology fig 5; methodology v7 note | 0.5 abs_pct | — |
| `rho-tradeoff` | The residual falls monotonically as rho falls, because a smaller rho demands a longer tail -- but cells become unfittable as the grid stops reaching the window, so rho and the grid must be tuned together. | methodology sec 9; methodology fig 6 left; methodology v7 note | 0.8 abs_pct | — |
| `b1-non-monotone` | The b1=0 rate is non-monotone in n with an interior minimum; past it, more items destroy the holes the certificate reads. | methodology sec 10, Observation 2; methodology fig 6 right | 0.02 abs | — |
| `kahle-finite-n` | The vanishing threshold decays as the theory requires, but the asymptotic exponent is not yet visible at these sizes. | methodology sec 10 footnote | 0.05 abs | — |
| `guard-blind-spot` | The c-oracle check is necessary but not sufficient: configurations exist that pass it while the floor is badly wrong. | methodology sec 6; methodology fig 4 | 0.1 rel | — |
| `saturation-gate` | beta=0.3 sits on the saturation gate; 0.25 clears it. | methodology sec 6; spec sec 2.6, Delta E | 0.02 abs | `test_2_6_saturation_gate_rejects_extreme_separation` |

## Reading the data

`evidence.json` holds each claim's full value under `claims.<id>.value`.
Figures are regenerated from it by `../make_figures.py`; the figure PDFs and
`runs/` are build products and are not committed.

A claim with no test is checked only by `verify.py`. A claim with a test is
checked twice: `verify.py` compares its value, and the test re-derives it
independently in the acceptance suite.
