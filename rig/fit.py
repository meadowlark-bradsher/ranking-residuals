"""Fitting the §2.5 floor: OLS on the §2.6 window, CI by bootstrap across seeds.

The model E||P_h Y||^2 = floor + c/k is linear in (floor, c) under x = 1/k, so OLS
is exact -- per seed, because the mask (hence P_h and the true floor) is fixed within
a seed (§2.4). The fit is restricted to k >= fit_k_min: the small-k points are where
the O(1/k^2) logit-bias term lives and a 2-parameter OLS absorbs it into the intercept
(measured floor bias 0.99x-2.30x on the full grid vs 0.92x-1.00x on k>=64 across
the §2.6 separations -- the `fit-window-bias-range` claim, which owns those digits).
"""

from __future__ import annotations

import numpy as np


def fit_floor_c(ks, energies, fit_k_min: int = 64) -> dict:
    """OLS of energy on 1/k, restricted to the §2.6 fit window."""
    ks = np.asarray(ks, dtype=float)
    energies = np.asarray(energies, dtype=float)
    sel = ks >= fit_k_min
    if sel.sum() < 2:
        raise ValueError(
            f"only {int(sel.sum())} k values >= fit_k_min={fit_k_min}; need >= 2 to fit. "
            "Extend the k grid upward rather than lowering fit_k_min (§2.6)."
        )
    K, E = ks[sel], energies[sel]
    A = np.column_stack([np.ones_like(K), 1.0 / K])
    (floor, c), *_ = np.linalg.lstsq(A, E, rcond=None)
    pred = A @ np.array([floor, c])
    ss_res = float(((E - pred) ** 2).sum())
    ss_tot = float(((E - E.mean()) ** 2).sum())
    return {"floor": float(floor), "c": float(c),
            "r2": 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0,
            "n_fit_points": int(sel.sum()), "fit_k_min": int(fit_k_min),
            "k_fitted": K.astype(int).tolist()}


def bootstrap_ci(values, alpha: float = 0.05, n_boot: int = 4000, rng=None) -> tuple:
    """Percentile bootstrap across seeds. The floor's job is to be distinguished from
    zero, so it never ships as a point estimate (§8.5)."""
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return (np.nan, np.nan)
    if v.size == 1:
        return (float(v[0]), float(v[0]))
    rng = rng or np.random.default_rng(0)
    idx = rng.integers(0, v.size, size=(n_boot, v.size))
    means = v[idx].mean(axis=1)
    return (float(np.percentile(means, 100 * alpha / 2)),
            float(np.percentile(means, 100 * (1 - alpha / 2))))


def aggregate_floor(per_seed_floors, alpha: float = 0.05, rng=None) -> dict:
    """Mean floor + CI across seeds, and whether it separates from zero."""
    v = np.asarray([f for f in per_seed_floors if np.isfinite(f)], dtype=float)
    lo, hi = bootstrap_ci(v, alpha=alpha, rng=rng)
    return {"floor_mean": float(v.mean()) if v.size else np.nan,
            "floor_sd": float(v.std(ddof=1)) if v.size > 1 else 0.0,
            "floor_ci_lo": lo, "floor_ci_hi": hi,
            "floor_n_seeds": int(v.size),
            "separates_from_zero": bool(np.isfinite(lo) and lo > 0.0)}


def covers(ci_lo: float, ci_hi: float, target: float) -> bool:
    """Does the CI cover the oracle value? (§8.5: floor must equal eps^2 within CI.)"""
    return bool(np.isfinite(ci_lo) and np.isfinite(ci_hi) and ci_lo <= target <= ci_hi)


def drift(values) -> float:
    """Relative spread, used for the gamma-invariance check (§8.5.5)."""
    v = np.asarray([x for x in values if np.isfinite(x)], dtype=float)
    if v.size < 2 or v.mean() == 0:
        return 0.0
    return float((v.max() - v.min()) / abs(v.mean()))
