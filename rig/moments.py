"""Exact moments of the edge estimators, and the exact harmonic energy (§7).

Monte-Carlo estimation of E||P_h Y||^2 has a noise floor around 1e-5 at practical
replicate counts -- far too coarse to resolve the O(1/k^2) coefficient. It is also
unnecessary. Each edge carries an INDEPENDENT binomial, so with mu_e = E[Y_e]:

    E[Y' P_h Y] = sum_ef (P_h)_ef E[Y_e Y_f]
                = mu' P_h mu + sum_e (P_h)_ee Var(Y_e)

because the cross terms factorise. Each 1-D moment is then an exact sum over the
binomial pmf -- clamp included -- giving ~1e-16 instead of ~1e-5.

Two estimators live here. `clamped_logit` is the instrument's own encoding, byte
for byte what rig.flows.logodds_from_counts computes. `firth` is the per-edge
Jeffreys-penalised MLE, (w+1/2)/(k+1), used as a DIAGNOSTIC probe: it is the
drop-in replacement for a single edge, NOT Firth-penalised BTL on the joint
sparse design, whose penalty does not factorise over edges (§7).
"""

from __future__ import annotations

import numpy as np
from scipy.stats import binom

# Half-width of the pmf window, in standard deviations. The tail beyond 14 sd
# carries ~1e-44 of the mass, far under double precision relative to the peak,
# so truncating there is exact in float64 -- and it is ~10x faster than summing
# the full 0..k range at k = 16384. `_moments_full` is kept as the untruncated
# reference that tests/test_invariants.py checks this against.
N_SD = 14.0


def _y_values(w, k, estimator):
    """The estimator's flow value for win-counts `w` out of `k`."""
    if estimator == "clamped_logit":
        phat = np.clip(w / k, 1.0 / (2 * k), 1.0 - 1.0 / (2 * k))
    elif estimator == "firth":
        phat = (w + 0.5) / (k + 1)          # never 0 or 1: no clamp needed
    else:
        raise ValueError(f"unknown estimator: {estimator!r}")
    return np.log(phat / (1.0 - phat))


def _moments_full(p, k, estimator="clamped_logit"):
    """Untruncated reference: sums the whole 0..k range. O(E*k), slow at large k."""
    w = np.arange(k + 1)
    pm = binom.pmf(w, k, np.asarray(p, dtype=float)[:, None])
    y = _y_values(w, k, estimator)
    mu = pm @ y
    return mu, (pm @ (y * y)) - mu * mu


def edge_moments(p, k, estimator="clamped_logit"):
    """Exact (mean, variance) of the edge flow, per edge. Windowed but exact.

    The window is per-edge rather than a shared union: edge probabilities spread
    widely on a sparse graph (0.08 to 0.48 is typical at n=12), and one window
    covering all of them is barely narrower than the full range.
    """
    p = np.asarray(p, dtype=float)
    k = int(k)
    mu = np.empty(p.shape, dtype=float)
    var = np.empty(p.shape, dtype=float)
    for i, pi in enumerate(p.ravel()):
        centre, sd = k * pi, np.sqrt(k * pi * (1.0 - pi))
        lo = max(0, int(np.floor(centre - N_SD * sd)))
        hi = min(k, int(np.ceil(centre + N_SD * sd)))
        w = np.arange(lo, hi + 1)
        # The clamp lives at w = 0 and w = k. At small k those sit inside the
        # window anyway; at large k their mass is negligible -- but splicing them
        # in unconditionally means the clamped estimator is never silently
        # approximated by its unclamped self.
        if lo > 0:
            w = np.concatenate(([0], w))
        if hi < k:
            w = np.concatenate((w, [k]))
        pm = binom.pmf(w, k, pi)
        y = _y_values(w, k, estimator)
        m1 = float(pm @ y)
        mu.ravel()[i] = m1
        var.ravel()[i] = float(pm @ (y * y)) - m1 * m1
    return mu, var


def exact_energy(P_harm, p_edge, k, estimator="clamped_logit"):
    """E[Y' P_h Y] exactly, no sampling. Returns (energy, mu, var)."""
    mu, var = edge_moments(np.asarray(p_edge, dtype=float), k, estimator)
    return float(mu @ P_harm @ mu + np.diag(P_harm) @ var), mu, var


def series_coefficients(P_harm, p_edge, floor, ks=None, n_terms=4,
                        estimator="clamped_logit"):
    """Fit E[Y'P_hY] - floor = c1/k + c2/k^2 + ... on exact energies.

    The basis is scaled to u = k_min/k so the Vandermonde stays conditioned; an
    unscaled 1/k^j basis over a 128x range of k is not.
    """
    ks = np.array([2 ** j for j in range(10, 18)] if ks is None else ks, dtype=float)
    E = np.array([exact_energy(P_harm, p_edge, int(k), estimator)[0] for k in ks])
    kmin = float(ks[0])
    u = kmin / ks
    A = np.column_stack([u ** j for j in range(1, n_terms + 1)])
    a = np.linalg.lstsq(A, E - float(floor), rcond=None)[0]
    return [float(a[j - 1] * kmin ** j) for j in range(1, n_terms + 1)]


# ---------------------------------------------------------------------------
# Closed forms (§7). Verified in tests against `edge_moments` extraction.
# ---------------------------------------------------------------------------
def bias_vector(p):
    """b: E[Y] = logit(p) + b/k + O(k^-2), for the CLAMPED LOGIT.

    Note this is the logit-space bias. The p-space quantity (1-2p)/(2k) -- what a
    +1/2 continuity correction cancels -- reaches the flow multiplied by
    g'(p) = 1/(p(1-p)), and it is this product that enters P_h.
    """
    p = np.asarray(p, dtype=float)
    return (2 * p - 1) / (2 * p * (1 - p))


def v2(p, estimator="clamped_logit"):
    """v2: Var(Y) = 1/(p q k) + v2/k^2 + O(k^-3).

    The 2/(pq) term is the third-order delta method's g'g''' contribution -- the
    near-boundary tail. Firth annihilates it outright and cuts the asymmetry term
    from 3/2 to 1/2, which is why v2_firth vanishes at p = 1/2.
    """
    p = np.asarray(p, dtype=float)
    pq = p * (1 - p)
    s = (2 * p - 1) ** 2
    if estimator == "clamped_logit":
        return 2.0 / pq + 1.5 * s / pq ** 2
    if estimator == "firth":
        return 0.5 * s / pq ** 2
    raise ValueError(f"unknown estimator: {estimator!r}")


def c1_closed(P_harm, p_edge, eps, h_unit):
    """c1 = tr(P_h V) + 2 eps (h.b). The cross term COMPLETES the delta-method
    oracle rather than refining it: variance-only is off by 4.5% / 0.2% on the
    two calibration topologies."""
    p = np.asarray(p_edge, dtype=float)
    V = 1.0 / (p * (1 - p))
    return (float(np.trace(P_harm @ np.diag(V)))
            + 2.0 * float(eps) * float(np.asarray(h_unit) @ bias_vector(p)))
