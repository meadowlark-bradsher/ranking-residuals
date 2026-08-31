# The floor is an intercept, so the window decides it

`rig/fit.py` fits `E‖P_h Y‖² = floor + c/k`. The model is linear in
`(floor, c)` under `x = 1/k`, so OLS is exact, and it is run per seed because
the mask — hence `P_h` and the true floor — is fixed within a seed.

`fit_floor_c` restricts the fit to `k >= fit_k_min` before assembling the design
matrix. The small-`k` points are where the `O(1/k²)` logit-bias term lives, and
a two-parameter OLS has nowhere to put it except the intercept: measured floor
bias is 0.83×–2.48× on the full grid against 0.87×–0.95× on `k >= 64`. Fewer
than two points inside the window raises `ValueError` rather than fitting, and
the message says which direction to fix it in — extend the `k` grid upward,
do not lower `fit_k_min`.

The returned dict carries `n_fit_points`, `fit_k_min` and the actual `k_fitted`
list alongside the estimates, so a floor is never readable without the window
that produced it.

`bootstrap_ci` is a percentile bootstrap across seeds; `aggregate_floor` reports
mean, standard deviation, interval, seed count, and `separates_from_zero`. The
docstring states the reason the interval is not optional: the floor's job is to
be distinguished from zero, so it never ships as a point estimate. `covers`
answers the §8.5 question — does the interval contain `eps²` — and `drift` gives
the relative spread used for the γ-invariance check.
