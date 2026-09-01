# The §2.6 window is checked in closed form before anything is fitted

Three thresholds are declared as module constants in `rig/oracle.py`, and the
comment above them says what they are: measured breakpoints, not preferences.
`SATURATION_MAX = 0.2` (0.17 fits, 0.42 breaks), `MILDNESS_MAX = 0.05`, and
`C_ORACLE_TOL = 1.5`.

`saturation(p_edge, k_min)` is the closed-form upper bound, the mean of
`p**k_min + (1-p)**k_min` over edges — no sampling is needed to evaluate it.
`mildness(eps, grad_flow)` is the lower bound, the injected harmonic as a
fraction of gradient energy, which keeps the misspecification innocent;
it returns infinity when the gradient energy is zero rather than dividing.

`regime_report` evaluates all three and, with `strict=True`, raises
`RegimeViolation` naming which gates failed and with what values. The exception's
own docstring states the doctrine: a loud failure is the correct output here, not
a floor number. Outside this window `floor + c/k` does not fail to fit — it fits,
and silently misreports the floor, which is the failure mode a returned number
would hide.

The `c`-oracle gate is separate and weaker. `c_oracle_gate` reports whether the
fitted `c` sits within `C_ORACLE_TOL` of the delta-method prediction, and both
the code and the spec label it necessary but not sufficient: it passes at
`beta = 0.25` while the recovered floor is 1.86× wrong.
