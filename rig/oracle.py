"""Known-answer oracles and the §2.6 regime gates.

Every projector here comes from hodge.hodge_projectors -- the oracle uses THIS
instrument's projectors, not a fork (§6, §7).
"""

from __future__ import annotations

import numpy as np

import hodge

# §2.6 gate thresholds. These are measured breakpoints, not preferences.
SATURATION_MAX = 0.2      # verified: 0.17 fits, 0.42 breaks
MILDNESS_MAX = 0.05       # eps^2/||D0 theta||^2 -- injection must stay INNOCENT
C_ORACLE_TOL = 1.5        # c_fit within this factor of the delta-method oracle


class RegimeViolation(Exception):
    """Raised when §8.5 is asked to fit outside the §2.6 window.

    A loud failure is the correct output here, not a floor number.
    """


def projector_split(n, edges, Y, filling="empty", triangles=None):
    """Exact (g,c,h) energies and fractions via the instrument's own projectors (§7)."""
    Y = np.asarray(Y, dtype=float)
    tris = hodge.triangles_for_filling(list(edges), filling, triangles)
    D0, D1 = hodge.build_operators(n, list(edges), tris)
    Pg, Pc, Ph = hodge.hodge_projectors(D0, D1)
    e = {"gradient": float(Y @ Pg @ Y), "curl": float(Y @ Pc @ Y),
         "harmonic": float(Y @ Ph @ Y)}
    tot = float(Y @ Y)
    fr = {k: (v / tot if tot else 0.0) for k, v in e.items()}
    b1 = len(edges) - np.linalg.matrix_rank(D0) - (np.linalg.matrix_rank(D1) if D1.shape[0] else 0)
    return {"energies": e, "fractions": fr, "total_mass": tot, "b1": int(b1),
            "D0": D0, "D1": D1, "P_harm": Ph, "filling": filling}


def deviation(measured: dict, oracle: dict) -> dict:
    """measured - oracle, per component (§7, §8.9)."""
    return {k: float(measured[k] - oracle[k]) for k in ("gradient", "curl", "harmonic")}


def floor_oracle(eps: float) -> float:
    """§2.5: the budget-independent floor is exactly eps^2 -- a known oracle."""
    return float(eps) ** 2


def c_oracle(P_harm: np.ndarray, p_edge: np.ndarray) -> float:
    """§7 delta-method: c = tr(P_h . diag(1/(p_e(1-p_e)))).

    The misspecification guard. Agreement is what licenses reading a fitted intercept
    as a floor rather than as fit misspecification -- but it is NECESSARY, NOT
    SUFFICIENT: it passes at beta=0.25 while the floor is 1.86x too high (§2.6).
    """
    p = np.asarray(p_edge, dtype=float)
    return float(np.trace(P_harm @ np.diag(1.0 / (p * (1.0 - p)))))


def saturation(p_edge: np.ndarray, k_min: int) -> float:
    """§2.6 upper bound, closed form -- no sampling needed."""
    p = np.asarray(p_edge, dtype=float)
    return float(np.mean(p ** k_min + (1.0 - p) ** k_min))


def mildness(eps: float, grad_flow: np.ndarray) -> float:
    """§2.6 lower bound: injected harmonic as a fraction of gradient energy."""
    g = float(np.asarray(grad_flow) @ np.asarray(grad_flow))
    return float(eps) ** 2 / g if g > 0 else np.inf


def regime_report(p_edge, k_min, eps, grad_flow, fit_k_min, strict=True) -> dict:
    """Check the §2.6 window in closed form BEFORE fitting anything."""
    sat = saturation(p_edge, k_min)
    mild = mildness(eps, grad_flow)
    rep = {
        "saturation": sat,
        "saturation_gate": SATURATION_MAX,
        "saturation_ok": sat < SATURATION_MAX,
        "mildness": mild,
        "mildness_gate": MILDNESS_MAX,
        "mildness_ok": mild < MILDNESS_MAX,
        "fit_k_min": int(fit_k_min),
        "fit_k_min_ok": int(fit_k_min) >= 64,
    }
    rep["ok"] = all(rep[k] for k in ("saturation_ok", "mildness_ok", "fit_k_min_ok"))
    if strict and not rep["ok"]:
        bad = [k for k in ("saturation_ok", "mildness_ok", "fit_k_min_ok") if not rep[k]]
        raise RegimeViolation(
            f"§2.6 preconditions failed: {bad}. saturation={sat:.3f} (<{SATURATION_MAX}), "
            f"mildness={mild:.5f} (<{MILDNESS_MAX}), fit_k_min={fit_k_min} (>=64). "
            "Refusing to fit: outside this window `floor + c/k` silently misreports the floor."
        )
    return rep


def required_fit_k_min(c_or: float, floor_target: float, rho: float) -> float:
    """Smallest k at which the variance term c/k has fallen to <= rho * floor.

    §2.6 pins fit_k_min at 64, but that number was MEASURED on filling='observed'
    (b1=2, c~17) -- and the window is not a constant, it is set by the ratio of the
    variance term to the floor being resolved. On filling='empty' the same graph has
    b1=20 and c~160, so k=64 leaves the variance term ~10x larger and the intercept is
    a small difference of large extrapolated numbers (measured floor 0.016 vs a true
    0.090).

    `rho` is REQUIRED and deliberately has no default: it is a shipped config field
    (RigConfig.rho, 1.5 since v7) and a default here would be a second place to set it.
    That is not hypothetical -- this signature defaulted to 3.0 from v6 onward while the
    config moved to 1.5 in v7, so the calibration claim in this docstring went stale and
    no caller noticed, because every real caller already passed rho explicitly.

    Choosing rho trades against grid reach: a smaller rho demands a longer, cleaner tail,
    so rho and the `k` grid move together. Measured over 20 base seeds (§ v7 note):
    rho=3.0 with k->4096 leaves a +1.6% +- 0.2% residual at coverage median 13/16;
    rho=1.5 with k->16384 gives +0.43% +- 0.09% at median 15/16 and no grid-short cells.
    rho=3.0 is where the window was first calibrated -- at observed/eps=0.3 it returns
    k_min ~ 64, the fixed window under which the 0.87x-0.95x recovery was established --
    which is provenance, not a recommended value.

    Returns inf when floor_target is 0 -- there is no floor to resolve, and the eps=0
    negative control is judged by whether its CI covers zero, not by this window.
    """
    if floor_target <= 0:
        return float("inf")
    return float(c_or) / (float(rho) * float(floor_target))


def c_oracle_gate(c_fit: float, c_or: float, tol: float = C_ORACLE_TOL) -> dict:
    """Necessary-not-sufficient gate (§2.6)."""
    ratio = c_fit / c_or if c_or else np.inf
    return {"c_fit": float(c_fit), "c_oracle": float(c_or), "c_ratio": float(ratio),
            "c_gate_tol": tol, "c_gate_ok": bool(1.0 / tol <= ratio <= tol)}
