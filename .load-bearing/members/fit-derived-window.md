# The fit window is derived from rho, not fixed at 64

`required_fit_k_min(c_or, floor_target, rho)` in `rig/oracle.py` returns
`c_oracle / (rho * floor_target)`: the smallest `k` at which the variance term
`c/k` has fallen to at most `rho` times the floor being resolved.

The spec pins `fit_k_min = 64`, but that constant was measured on
`filling='observed'`, where the calibration graph has `b1 = 2` and `c ≈ 17`. The
window is not a constant — it is set by the ratio of the variance term to the
floor. On `filling='empty'` the same graph has `b1 = 20` and `c ≈ 160`, so at
`k = 64` the variance term is still about ten times larger and the intercept
becomes a small difference of large extrapolated numbers: a measured floor of
0.047 against a true 0.090. Both digits belong to the `filling-dependence`
claim, which gained the recovered floor for exactly this reason — the b₁ and `c`
that explain the failure were owned, and the floor that demonstrates it was not.

`rho` is a required positional parameter with no default, and the docstring
explains why that is deliberate rather than austere. It is a shipped config
field, `RigConfig.rho`, 1.5 since v7. A default here would be a second place to
set it — and that is not hypothetical: this signature carried `rho=3.0` from v6
onward while the config moved to 1.5 in v7, so the calibration claim in its own
docstring went stale and no caller noticed, because every real caller was
already passing `rho` explicitly.

Choosing `rho` trades against grid reach; a smaller `rho` demands a longer,
cleaner tail, so `rho` and the `k` grid move together. The function returns
infinity when `floor_target <= 0`: there is no floor to resolve, and the
`eps = 0` negative control is judged by whether its CI covers zero.
