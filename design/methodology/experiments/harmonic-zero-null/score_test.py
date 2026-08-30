"""
The harmonic-zero null as a constrained-GLM score test (RAN-28, gating item 1).

    H0 :  logit p  in  S = im D0 (+) im D1^T = (harmonic)^perp

The harmonic component of the mean flow is exactly zero; the gradient AND curl
coordinates are free.

WHY THIS NULL AND NOT PURE BRADLEY-TERRY. It strictly dominates BT. Every
curl-type misspecification is absorbed into the free part of S, so a rejection
can only be driven by harmonic content. A BT null (S = im D0 alone) also rejects
on curl, which is not what the certificate claims to measure. `curl_freedom` in
probes.py is the check that this is real and not just asserted.

THE CLAIM UNDER TEST (RAN-27, structural result 1). In the pre-specified
fixed-graph case this score test IS a classical Rao score test -- chi-squared
with b1 degrees of freedom, in harmonic coordinates. If it holds, the
certificate is referee-proof on its own and DZW earns its keep only at
post-selection loop-choice and small n. If it does not, the collapse claim is
wrong and everything downstream of it moves.

THE ALGEBRA (why b1 df, and why "harmonic coordinates" is literal)
------------------------------------------------------------------
Each edge carries w_e successes out of k_e, independently, natural parameter
eta_e = logit p_e. The log-likelihood

    l(eta) = sum_e [ w_e * eta_e - k_e * log(1 + exp(eta_e)) ]

has score  U(eta) = w - k*p  and DIAGONAL Fisher information

    I(eta) = diag(k_e * p_e * (1 - p_e))

because the link is canonical and the edges are independent.

Write S = col(M), M orthonormal, dim S = E - b1. At the constrained MLE the
first-order condition is M^T (w - k*p0) = 0, so

    U(eta0)  is Euclidean-orthogonal to S,  hence  U(eta0) in S^perp,

and  S^perp = (im D0 + im D1^T)^perp = ker D0^T  intersect  ker D1 = HARMONIC.

The score at the constrained fit therefore lands in the harmonic subspace
exactly, by construction -- not approximately, and not after a projection we
chose to apply. That is what makes "the score test in harmonic coordinates"
literal. `score_off_harmonic` below measures it rather than trusting it.

The Rao statistic is

    T = U^T I^{-1} U          (I diagonal; a b1-dimensional quadratic form even
                               though U is carried in R^E)

Under H0, T -> chi2(b1). Sketch: put Utilde = I^{-1/2} U. Then Var(Utilde) =
I_E - P, with P the projector onto col(I^{1/2} M), rank E - b1. So I_E - P is
idempotent of rank b1 and Utilde^T Utilde = U^T I^{-1} U ~ chi2(b1).

Note I^{-1} does not preserve the harmonic subspace, so T is NOT ||U||^2
rescaled. The weighting carries the k_e and p_e dependence, and it is exactly
where PP4's small-edge-count worry lives.

THE INSTRUMENT IS NOT TOUCHED. S is derived from hodge.harmonic_basis -- the
same operator the certificate uses -- so the null is stated in the certificate's
own coordinates rather than in a parallel construction that could drift from it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import hodge

# |logit p| beyond ETA_CLIP is separation (some edge went w=0 or w=k), not
# signal: the constrained MLE is diverging and the score test is not defined on
# that draw. Legitimate eta here is O(1) -- beta=0.25 on a gamma theta -- so 15
# is far outside the signal and well inside where v = k*p*(1-p) is still
# representable. Draws that reach SEPARATED are COUNTED AND DROPPED, never
# silently kept: a clipped fit does not satisfy M^T U = 0, so its T is noise
# wearing the right units. (Same discipline as spec 8.5 seed accounting.)
ETA_CLIP = 15.0
SEPARATED = 14.0
MIN_INFO = 1e-10


def _sigmoid(x):
    """Clipped logistic: the IRLS iterate's numerical guard. NOT for drawing data."""
    return 0.5 * (1.0 + np.tanh(0.5 * np.clip(x, -ETA_CLIP, ETA_CLIP)))


def sigmoid(x):
    """Exact logistic -- the DATA-GENERATING link, deliberately unclipped.

    _sigmoid's clip keeps the fit's working weights representable; reusing it to
    draw data would silently simulate sigmoid(+-ETA_CLIP) instead of the eta the
    caller named, so an extreme cell would report on a flow it does not describe.
    Saturating to exactly 0 or 1 here is the honest answer: that edge really is
    deterministic under the eta it was handed, and the resulting draw separates
    and is dropped by the usual accounting.
    """
    return 0.5 * (1.0 + np.tanh(0.5 * np.asarray(x, dtype=float)))


def harmonic_zero_bases(D0, D1):
    """(H, M): orthonormal bases for the harmonic subspace and its complement S.

    H spans ker(L1) -- b1 columns, the directions H0 forbids.
    M spans S = H^perp = im D0 (+) im D1^T -- E - b1 columns, the free directions.

    Both descend from the instrument's own harmonic_basis, so S is the exact
    complement of what the certificate measures. There is no second convention
    to drift.
    """
    H = hodge.harmonic_basis(D0, D1)
    b1 = H.shape[1]
    if b1 == 0:
        raise ValueError(
            "b1 = 0: this graph+filling has no harmonic direction, so H0 "
            "constrains nothing and the test has 0 df. Lower p, or use "
            "filling='empty'.")
    # S = ker(H^T), taken as the trailing left-singular vectors of H.
    Uh, _, _ = np.linalg.svd(H, full_matrices=True)
    return H, Uh[:, b1:]


def fit_constrained(w, k, M, tol=1e-11, max_iter=200):
    """Constrained MLE of the binomial GLM with eta = M beta, by IRLS.

    The link is canonical, so the working weights ARE the Fisher information:
    this is Fisher scoring and Newton-Raphson at once, and it converges
    quadratically unless an edge separates.
    """
    beta = np.zeros(M.shape[1])
    eta = M @ beta
    converged = False
    for it in range(1, max_iter + 1):
        p = _sigmoid(eta)
        v = np.maximum(k * p * (1.0 - p), MIN_INFO)     # working weights = I
        z = eta + (w - k * p) / v                        # working response
        Mv = M * v[:, None]
        beta = np.linalg.solve(Mv.T @ M, Mv.T @ z)
        eta_new = np.clip(M @ beta, -ETA_CLIP, ETA_CLIP)
        step = float(np.max(np.abs(eta_new - eta)))
        eta = eta_new
        if step < tol:
            converged = True
            break
    return eta, _sigmoid(eta), it, converged


def bradley_terry_bases(D0):
    """(H, M) for the pure Bradley-Terry null: S = im D0, gradient only.

    The comparison null, present so `curl_freedom` can measure the difference
    rather than assert it. BT forbids everything outside the gradient image --
    curl included -- so it rejects on curl-type misspecification that the
    harmonic-zero null absorbs into its free coordinates. Its df is therefore
    E - rank(D0) = b1 + rank(D1), not b1.
    """
    Ud, sd, _ = np.linalg.svd(D0, full_matrices=True)
    r = int((sd > max(D0.shape) * np.finfo(float).eps * sd.max()).sum())
    return Ud[:, r:], Ud[:, :r]


def score_statistic(w, k, bases):
    """Rao score statistic for H0: eta in col(M), plus its df.

    `bases` is the (H, M) pair naming the null -- harmonic_zero_bases for the
    certificate's null, bradley_terry_bases for the BT comparison. Build it once
    per graph and reuse across replicates: the collapse claim is about the
    PRE-SPECIFIED fixed-graph case, so the graph must not be redrawn inside the
    replicate loop.
    """
    H, M = bases
    eta0, p0, n_iter, converged = fit_constrained(w, k, M)
    U = w - k * p0
    v = np.maximum(k * p0 * (1.0 - p0), MIN_INFO)
    max_abs_eta = float(np.max(np.abs(eta0)))
    separated = max_abs_eta >= SEPARATED
    return {
        "T": float(U @ (U / v)),                  # U^T I^{-1} U
        "df": int(H.shape[1]),
        "n_iter": int(n_iter),
        "converged": bool(converged),
        # A separated draw has no finite constrained MLE. Reported so the caller
        # can drop it and say how often, rather than letting a 1e11 statistic
        # ride into a mean.
        "separated": bool(separated),
        "usable": bool(converged and not separated),
        # The first-order condition says the score is already orthogonal to S,
        # i.e. it already lives in H0's forbidden subspace. Measured, not
        # assumed: if this is not ~0 the fit did not converge and T is noise.
        "score_off_harmonic": float(np.linalg.norm(M.T @ U)),
        "score_norm": float(np.linalg.norm(U)),
        "max_abs_eta": max_abs_eta,
    }


def operators(n, edges, filling):
    """D0, D1 for a graph under a named filling -- via the instrument (RAN-7)."""
    tris = hodge.triangles_for_filling(edges, filling)
    return hodge.build_operators(n, edges, tris)


def operators_for_triangles(n, edges, triangles):
    """D0, D1 for an EXPLICIT 2-skeleton, routed through the instrument's own
    'custom' filling so a partial fill cannot drift from the named ones.

    'observed' and 'empty' are the two ENDPOINTS of a lattice, not a binary
    choice. Filling a triangle adds a row to D1, so im D1^T grows weakly, S grows,
    and b1 shrinks -- monotonically. Everything between the endpoints is reachable
    and, until now, unmeasured.
    """
    tris = hodge.triangles_for_filling(edges, "custom", list(triangles))
    return hodge.build_operators(n, edges, tris)
