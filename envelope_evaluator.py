"""Dependency-free operating-envelope evaluator for the harmonic-zero null.

An INDEPENDENT closed-form verification oracle, and the scope of that word is
worth stating precisely because it is what the agreement is worth.

INDEPENDENT: the operators, the harmonic subspace and the chi-squared tail are
rebuilt here from the repository's stated conventions, reaching no instrument
code. NumPy and the standard library only -- no scipy, statsmodels, sklearn, or
external optimiser. (`rig.provenance` is imported to stamp the output; it is
stdlib-only and touches nothing numerical.)

NOT INDEPENDENT: the data-generating path. `benchmark_topology` and `h0_eta`
call `rig.flows`, which imports `hodge` -- so the edge mask and the latent are
shared code, and this file DOES reach `hodge` transitively on every path main()
takes. That is deliberate: the draws have to match for a draw-for-draw
comparison to mean anything. But it makes the mask and eta common-mode, and an
error in either would be invisible to this oracle. An earlier version of this
paragraph said flatly "it does not import `hodge`", which a reader checking the
claim would find false.

WHAT IS TESTED
    H0 :  logit p  in  S = im D0 (+) im D1^T  =  harmonic^perp

The score of the binomial GLM at the true natural parameter is U = w - k*p with
diagonal Fisher information I = diag(k*p*(1-p)) (canonical link, independent
edges). Under H0 the harmonic coordinates of that score are pure noise, so with
H an orthonormal basis of ker(L1),

    s = H^T (w - k*p)          (b1 harmonic coordinates)
    T = s^T (H^T I H)^{-1} s   ->  chi2(b1)

which is exact in the Gaussian limit and needs no iteration -- the "closed form"
the specification asks for.

FOUR DEVIATIONS FROM THE SPECIFICATION AS DRAFTED. Each is a defect that would
have produced a well-formed but wrong number, which is the failure mode this
repository is built to refuse.

 1. `U_harmonic = Ph @ (w - k * p_emp)` with `p_emp = w / k` is identically the
    zero vector: k*p_emp == w by construction, so every draw scores T = 0 and
    the whole grid reports mean_T_ratio = 0, realized_size = 0. The residual
    must be taken against the NULL-implied mean, not the empirical one. Fixed to
    `w - k*p_true`.

 2. `T = U^T pinv(I) U` with `U = Ph z` is not chi2(b1). Writing z = I^(1/2) Z
    with Z standard, the form becomes Z^T (I^(1/2) Ph I^-1 Ph I^(1/2)) Z, whose
    matrix is idempotent only when I is constant across edges. The weighting
    used here inverts the information RESTRICTED to the harmonic coordinates,
    (H^T I H)^{-1}, which is the right normalisation FOR THIS SCORE POINT: at
    the true eta, Cov(z) = I exactly, so Cov(H^T z) = H^T I H and
    s^T (H^T I H)^{-1} s is chi2(b1).

    THIS IS A DIFFERENT QUADRATIC FORM FROM THE INSTRUMENT'S, and the earlier
    wording here -- "which is what the branch's own derivation uses" -- was
    wrong. score_test.py derives and computes T = U^T I^{-1} U at the
    CONSTRAINED MLE, where U lies in col(H), i.e. s'^T (H^T I^{-1} H) s'.
    (H^T I H)^{-1} and H^T I^{-1} H coincide only when M^T I H = 0, i.e. when I
    preserves the harmonic subspace -- which no real cell satisfies. Measured
    ||M^T I H||_F: 47.49 (graph 0, k=512), 5.77 (graph 2, k=128), 2.70
    (graph 3, k=64), and the two matrices differ by up to 29% relative.

    Both are valid score tests; they are simply not the same statistic, so the
    oracle-minus-instrument gap is NOT attributable to the refit alone. See the
    decomposition under VERIFICATION AGAINST THE PUBLISHED RUN below.

 3. The df >= 5 branch of `survival_function` returns a Wilson-Hilferty QUANTILE
    where a survival probability is required. Its value does not depend on x, so
    the Newton derivative is 0, the loop breaks on the first pass, and the
    routine silently returns its own starting guess. Replaced by a regularized
    incomplete gamma Q(df/2, x/2) (series + Lentz continued fraction) inverted by
    a bracketed bisection, which is accurate for every df including the b1 = 13
    to 22 cells the `empty` filling produces.

 4. Assertion 2's identity b1 = |E| - (n - 1) holds only on a CONNECTED graph.
    rank(D0) = n - c for c components, so the general statement is
    b1 = |E| - n + c. A sparse mask at p = 0.45 is not guaranteed connected, so
    the assertion is made against the component count it actually has.

 5. The boundary-condition detector tests the wrong condition, and this is the
    one that moves the published numbers. "Some edge has w = 0 or w = k" is
    UNCONSTRAINED per-edge saturation. Under H0 the natural parameter is
    confined to S, so a saturated cell is usually still fitted finitely -- the
    constraint pins it -- and divergence needs separation WITHIN the model
    subspace. Measured on graph 2 at k = 512: 28.65% of draws saturate somewhere,
    5.0% actually break the fit. Carried through the grid the drafted rule
    leaves 17 usable draws of 500 at k = 32, against 43% loss for the real one.
    Both rules ship (`separation_rule=`), defaulting to 'mle'.

VERIFICATION AGAINST THE PUBLISHED RUN. Seeding, masks and eta reproduce
branch harmonic-zero-null exactly (eta_absmax and p_min agree to 6 dp on all
four graphs), so the two runs see the SAME draws. With separation_rule='mle'
all sixteen observed-filling drop rates reproduce that run's exactly, and the
two rules agree DRAW BY DRAW: zero disagreements over all 32,000 draws of the
grid. mean_T_ratio then differs for TWO reasons, not one: this one is the
oracle score at the true eta weighted by (H^T I H)^{-1}, whose mean is exactly
b1 by construction; that one refits the constrained MLE per draw AND weights by
I^{-1} (deviation 2). The gap is largest where the drop rate is largest.

DO NOT READ THE GAP AS "THE REFIT". Decomposed on graph 3 at k = 64 over 600
draws (540 retained), meanT/df is

    0.9257   oracle:      score at true eta,   (H^T I H)^{-1}
    0.5474   intermediate: score at the refit, (H^T I H)^{-1}
    0.7869   instrument:  score at the refit,  I^{-1}       (score_test.py)

so the refit point contributes +0.378 and the change of quadratic form -0.240:
two large opposite-signed effects whose partial cancellation leaves a net
+0.139. An earlier version of this note read that net as "57% of the published
conservative drift in the REFIT", which books a weighting change larger than
the net gap into the refit. Separating the two requires the intermediate row
above; the drop-rate column alone cannot do it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
# stdlib-only (ast, hashlib, inspect, os, textwrap, types); reaches no instrument.
from rig import provenance                                       # noqa: E402

ALPHA = 0.05
N_ITEMS = 12
P_EDGE = 0.45
BETA, GAMMA = 0.25, 2.0
N_GRAPHS = 4
K_GRID = (512, 128, 64, 32)


# ---------------------------------------------------------------- topology
def build_d0_matrix(edges, n=None):
    """|E| x n incidence. Edge (i, j), i < j: -1 at column i, +1 at column j.
    Row order is the edge list's order -- it defines the flow index order."""
    edges = list(edges)
    if n is None:
        n = max((max(e) for e in edges), default=-1) + 1
    D0 = np.zeros((len(edges), n))
    for r, (i, j) in enumerate(edges):
        if not i < j:
            raise ValueError(f"edge {(i, j)} violates the i < j convention")
        D0[r, i] = -1.0
        D0[r, j] = +1.0
    return D0


def build_d1_matrix(triangles, edges):
    """|F| x |E| boundary. Triangle (i, j, k), i < j < k: +1 on (i,j), +1 on
    (j,k), -1 on (i,k) -- the last leg is traversed backwards round the loop."""
    edges = list(edges)
    index = {e: c for c, e in enumerate(edges)}
    tris = list(triangles)
    D1 = np.zeros((len(tris), len(edges)))
    for r, (i, j, k) in enumerate(tris):
        if not i < j < k:
            raise ValueError(f"triangle {(i, j, k)} violates the i < j < k convention")
        D1[r, index[(i, j)]] += 1.0
        D1[r, index[(j, k)]] += 1.0
        D1[r, index[(i, k)]] -= 1.0
    return D1


def observed_triangles(edges):
    """The 2-skeleton: every triple whose three edges are all present."""
    eset = set(map(tuple, edges))
    verts = sorted({v for e in edges for v in e})
    return [(i, j, k) for i, j, k in combinations(verts, 3)
            if (i, j) in eset and (j, k) in eset and (i, k) in eset]


def harmonic_basis(D0, D1):
    """Orthonormal basis of ker(L1), L1 = D0 D0^T + D1^T D1. Columns = holes."""
    E = D0.shape[0]
    L1 = D0 @ D0.T
    if D1.shape[0]:
        L1 = L1 + D1.T @ D1
    w, V = np.linalg.eigh(L1)
    tol = max(E, 1) * np.finfo(float).eps * (w.max() if w.size else 1.0) * 10
    return V[:, w <= tol]


def compute_harmonic_projector(D0, D1):
    """P_h = H H^T, the orthogonal projector onto the harmonic subspace."""
    H = harmonic_basis(D0, D1)
    return H @ H.T, H


def n_components(D0, n):
    """Connected components, from the rank of the incidence matrix."""
    return int(n - np.linalg.matrix_rank(D0))


# ------------------------------------------------------- chi-squared tail
def _gammainc_q(a, x):
    """Regularized upper incomplete gamma Q(a, x). Series below the crossover,
    Lentz's continued fraction above it."""
    if a <= 0:
        raise ValueError("a must be positive")
    if x < 0:
        raise ValueError("x must be non-negative")
    if x == 0.0:
        return 1.0
    log_pref = -x + a * math.log(x) - math.lgamma(a)
    if x < a + 1.0:
        ap, term, total = a, 1.0 / a, 1.0 / a
        for _ in range(10000):
            ap += 1.0
            term *= x / ap
            total += term
            if abs(term) < abs(total) * 1e-17:
                break
        return 1.0 - total * math.exp(log_pref)
    tiny = 1e-300
    b = x + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b if abs(b) > tiny else 1.0 / tiny
    h = d
    for i in range(1, 10000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-17:
            break
    return h * math.exp(log_pref)


def chi2_sf(x, df):
    """P(chi2_df > x)."""
    if x <= 0:
        return 1.0
    return _gammainc_q(df / 2.0, x / 2.0)


_CRIT_CACHE = {}

# Closed forms at alpha = 0.05, retained from the specification as an independent
# check on the inversion; verified against it in self_test().
_EXACT_05 = {
    1: 3.841458820694124,
    2: 5.991464547107979,
    3: 7.814727903251179,
    4: 9.487729036781154,
}


def get_chi2_critical_value(df, alpha=ALPHA):
    """Upper-tail critical value: the x with P(chi2_df > x) = alpha."""
    if df <= 0:
        return 0.0
    key = (int(df), float(alpha))
    if key in _CRIT_CACHE:
        return _CRIT_CACHE[key]
    lo, hi = 0.0, max(2.0 * df, 10.0)
    while chi2_sf(hi, df) > alpha:
        hi *= 2.0
        if hi > 1e12:
            raise RuntimeError("failed to bracket the critical value")
    for _ in range(300):
        mid = 0.5 * (lo + hi)
        if chi2_sf(mid, df) > alpha:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-13 * max(1.0, hi):
            break
    out = _CRIT_CACHE[key] = 0.5 * (lo + hi)
    return out


# -------------------------------------------------------------- the engine
def seed(*parts):
    """Deterministic per-cell stream, matching the branch's scheme exactly so a
    cell here draws the SAME counts as the same cell there."""
    h = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return np.random.default_rng(int.from_bytes(h[:8], "big"))


def sigmoid(x):
    return 0.5 * (1.0 + np.tanh(0.5 * np.asarray(x, dtype=float)))


def constrained_mle_separates(w, k, M, eta_clip=15.0, separated=14.0,
                              tol=1e-11, max_iter=200):
    """True when the constrained MLE of the binomial GLM with eta = M beta
    diverges -- i.e. the draw on which a deployment's fit is undefined.

    This is NOT the same condition as "some edge has w = 0 or w = k". Under H0
    the natural parameter is confined to S = col(M), so a single saturated cell
    is usually still fitted finitely: the constraint pins it. Divergence needs
    separation WITHIN the model subspace, which is far rarer. On graph 2 at
    k = 512, 28.65% of draws saturate somewhere but only 5.0% break the fit.

    IRLS on a canonical link, so the working weights ARE the Fisher information
    and this is Fisher scoring and Newton-Raphson at once. Iterative, but pure
    NumPy linear algebra -- no external optimiser.

    THE TEST IS ON THE CONVERGED FIT, NOT ON THE ITERATES. An IRLS path can
    overshoot the cut and come back: on graph 3 at k = 32, draws 700 and 1683
    both reach |eta| = 14.15 and 14.08 at iteration 5, then settle to 13.61 and
    13.59 and converge finitely. A transient overshoot is not divergence, and
    bailing on the first crossing discards two draws whose constrained MLE
    exists. eta is therefore clipped to +/-eta_clip each pass -- which pins a
    genuinely diverging fit at the clip, where it converges and is then caught
    by the cut -- and separation is read off the fixed point, matching
    score_test.fit_constrained iterate for iterate.
    """
    beta = np.zeros(M.shape[1])
    eta = M @ beta
    converged = False
    for _ in range(max_iter):
        p = 0.5 * (1.0 + np.tanh(0.5 * np.clip(eta, -eta_clip, eta_clip)))
        v = np.maximum(k * p * (1.0 - p), 1e-10)
        z = eta + (w - k * p) / v
        try:
            beta_new = np.linalg.solve(M.T @ (v[:, None] * M), M.T @ (v * z))
        except np.linalg.LinAlgError:
            return True
        eta_new = M @ beta_new
        if not np.all(np.isfinite(eta_new)):
            return True
        eta_new = np.clip(eta_new, -eta_clip, eta_clip)
        step = np.max(np.abs(eta_new - eta))
        beta, eta = beta_new, eta_new
        if step < tol:
            converged = True
            break
    if not converged:
        return True                              # did not converge in max_iter
    return bool(np.max(np.abs(eta)) >= separated)


def run_envelope_evaluation(edges, triangles, k, true_lambda=None, eta=None,
                            num_replicates=2000, alpha=ALPHA, tag="cell",
                            check_stationarity=True, separation_rule="mle"):
    """Operating-envelope simulation on one (topology, k) cell.

    Supply either `true_lambda` (H0-true eta = D0 @ true_lambda, pure gradient)
    or `eta` directly -- the latter lets a curl component be carried, which is
    what separates this null from Bradley-Terry. Both satisfy P_h eta = 0.

    `separation_rule` selects the boundary-condition detector:
      'mle'       -- the constrained fit diverges. What a deployment faces.
      'saturated' -- any edge at w = 0 or w = k, as drafted. Over-drops badly.
    """
    edges = list(edges)
    n = max((max(e) for e in edges), default=-1) + 1
    D0 = build_d0_matrix(edges, n)
    D1 = build_d1_matrix(triangles, edges)
    Ph, H = compute_harmonic_projector(D0, D1)
    b1 = int(np.round(np.trace(Ph)))
    if b1 != H.shape[1]:
        raise AssertionError(f"trace(Ph)={np.trace(Ph)} disagrees with dim H={H.shape[1]}")

    if eta is None:
        if true_lambda is None:
            raise ValueError("supply true_lambda or eta")
        eta = D0 @ np.asarray(true_lambda, dtype=float)
    eta = np.asarray(eta, dtype=float)

    harm_leak = float(np.linalg.norm(Ph @ eta))
    if harm_leak > 1e-9 * max(1.0, float(np.linalg.norm(eta))):
        raise AssertionError(f"eta violates H0: ||P_h eta|| = {harm_leak:.3e}")

    p_true = sigmoid(eta)
    info_diag = k * p_true * (1.0 - p_true)
    A = H.T @ (info_diag[:, None] * H)          # H^T I H, the b1 x b1 information
    crit = get_chi2_critical_value(b1, alpha)
    eye_minus_ph = np.eye(len(edges)) - Ph
    # S = H^perp, taken as the trailing left-singular vectors of H.
    M = np.linalg.svd(H, full_matrices=True)[0][:, b1:]
    n_saturated = 0

    drop_count = 0
    T_stats = []
    rejections = 0
    max_off_harmonic = None

    for r in range(num_replicates):
        w = seed(tag, r).binomial(k, p_true)

        # Boundary-condition detector.
        saturated = bool(np.any(w == 0) or np.any(w == k))
        n_saturated += saturated
        if separation_rule == "saturated":
            dropped = saturated
        elif separation_rule == "mle":
            # Only a saturated draw can separate the constrained fit, so the
            # cheap test gates the expensive one.
            dropped = saturated and constrained_mle_separates(w, k, M)
        else:
            raise ValueError(f"unknown separation_rule {separation_rule!r}")
        if dropped:
            drop_count += 1
            continue

        z = w - k * p_true                      # score at the H0-true parameter
        s = H.T @ z                             # harmonic coordinates
        T_stat = float(s @ np.linalg.solve(A, s))
        T_stats.append(T_stat)
        if T_stat > crit:
            rejections += 1

        if check_stationarity:
            # The honest quantity: how much of the score lies OUTSIDE the
            # harmonic subspace. It is large and it is meant to be -- see
            # assert_stationarity for why this is a diagnostic, not a gate.
            off = float(np.linalg.norm(eye_minus_ph @ z))
            max_off_harmonic = off if max_off_harmonic is None else max(max_off_harmonic, off)

    total_valid = num_replicates - drop_count
    T_arr = np.asarray(T_stats)
    return {
        "E": len(edges),
        "b1": b1,
        "k": int(k),
        "n_replicates": int(num_replicates),
        "n_usable": int(total_valid),
        "n_dropped": int(drop_count),
        "drop_rate": drop_count / num_replicates if num_replicates else 0.0,
        "saturation_rate": n_saturated / num_replicates if num_replicates else 0.0,
        "separation_rule": separation_rule,
        # None, not 0.0: a cell with no usable draws MEASURED NOTHING, and 0.0
        # is a value a real cell can take. Coercing it to 0.0 made an empty cell
        # the smallest entry in any monotone-decreasing test, so a fully
        # truncated cell could carry assert_truncation_trend to a pass. Same
        # 0.0-as-measurement error as deviation 1, one layer out.
        "mean_T_ratio": float(T_arr.mean() / b1) if (b1 > 0 and T_arr.size) else None,
        "var_T_ratio": float(T_arr.var(ddof=1) / (2 * b1)) if (b1 > 0 and T_arr.size > 1) else None,
        "realized_size": rejections / total_valid if total_valid > 0 else None,
        "chi2_critical": crit,
        "max_score_off_harmonic": max_off_harmonic,
        "eta_absmax": float(np.max(np.abs(eta))),
    }


# ------------------------------------------------------- benchmark suite
def benchmark_topology(g, filling="observed"):
    """Graph g of the fixed four-mask benchmark, plus its 2-skeleton.

    The mask is drawn once and held across replicates: redrawing inside the loop
    would test the random-graph case, which is not what the collapse claim is
    about. Seeding matches the branch's scheme, so cell (filling, g, k) here
    draws the same counts as cell (filling, g, k) there.
    """
    from rig import flows
    edges = flows.sample_sparse_graph(N_ITEMS, P_EDGE, seed("graph", g))
    triangles = observed_triangles(edges) if filling == "observed" else []
    return edges, triangles


def h0_eta(edges, triangles, g, rho_curl=1.0):
    """A natural parameter satisfying H0 exactly: gradient + scaled curl.

    Both components lie in S, so ||P_h eta|| = 0 by construction and every
    rejection is a false one. The curl term is what separates this null from
    Bradley-Terry; at rho_curl = 0 the two see the same data.
    """
    from rig import flows
    D0 = build_d0_matrix(edges, N_ITEMS)
    D1 = build_d1_matrix(triangles, edges)
    eta = D0 @ flows.theta_gamma(N_ITEMS, BETA, GAMMA)
    if rho_curl and D1.shape[0]:
        c = seed("curl", g).normal(size=D1.shape[0])
        curl = D1.T @ c
        eta = eta + rho_curl * np.linalg.norm(eta) / np.linalg.norm(curl) * curl
    return eta


# Published values from design/methodology/experiments/harmonic-zero-null/
# results/chi2_collapse.json on branch harmonic-zero-null (2000 reps). That run
# fits the CONSTRAINED MLE per draw; this evaluator uses the closed-form oracle
# at the true eta. Drop rates should agree exactly -- the draws are identical
# and the separation rule is a function of w alone -- while T and size differ by
# the refit AND by the change of quadratic form (deviation 2).
#
# KEYED ON FILLING. Every (graph, k) pair exists TWICE in chi2_collapse.json,
# once per filling, and they are different cells with different b1. Keyed on
# (graph, k) alone, `--filling empty` printed the observed-filling numbers as
# the reference column for empty-filling rows -- e.g. graph 2's empty cell
# (b1 = 21) was compared against the observed cell's b1 = 3 figures. A missing
# key now prints "-" rather than the wrong cell.
REFERENCE = {
    ("observed", 0, 512): (0.000, 1.019, 0.053),
    ("observed", 1, 512): (0.000, 1.029, 0.050),
    ("observed", 2, 512): (0.050, 0.983, 0.046),
    ("observed", 2, 128): (0.207, 1.006, 0.059),
    ("observed", 2, 64): (0.293, 0.972, 0.052),
    ("observed", 2, 32): (0.435, 0.973, 0.062),
    ("observed", 3, 512): (0.000, 1.061, 0.054),
    ("observed", 3, 128): (0.0075, 1.024, 0.045),
    ("observed", 3, 64): (0.0915, 0.842, 0.039),
    ("observed", 3, 32): (0.430, 0.740, 0.030),
}


# ---------------------------------------------------- verification assertions
STATIONARITY_NOT_APPLICABLE = (
    "not applicable on this path: the oracle scores at the TRUE eta, where no "
    "first-order condition holds, so the score has no reason to lie in the "
    "harmonic subspace and max_score_off_harmonic is large by construction. "
    "The instrument's analogue -- score_test.score_off_harmonic, ||M^T U|| at "
    "the converged constrained fit -- is a real convergence check; this one has "
    "no content and is reported, not asserted.")


def assert_stationarity(cell, tol=5e-13):
    """4.1 -- WITHDRAWN. It measured a quantity that is identically zero.

    The check read ||(I - Ph)(Ph z)||. Ph = H H^T with H orthonormal is
    idempotent, so (I - Ph)Ph = 0 for every z: the assertion passed on any
    input, including a pure gradient (8.5e-17 against a 5e-13 tolerance) which
    lies entirely OUTSIDE the harmonic subspace and is exactly what 4.1 claimed
    to rule out. It could not fail, and boundary_report.json recorded its "pass"
    as evidence.

    Deleting it rather than repairing it is deliberate: the property 4.1 names
    does not hold on this code path at all, so there is nothing to repair. The
    honest quantity is now reported as `max_score_off_harmonic` and left
    unasserted. Kept as a named no-op so a caller cannot silently lose the
    reason.
    """
    return STATIONARITY_NOT_APPLICABLE


def assert_degeneracy(verbose=True):
    """4.2 -- with no 2-cells, b1 = E - rank(D0) = E - n + c.

    The drafted form E - (n - 1) assumes ONE component; a sparse mask at
    p = 0.45 is not guaranteed connected, so the component count is measured
    rather than assumed.
    """
    for g in range(N_GRAPHS):
        edges, _ = benchmark_topology(g, filling="empty")
        D0 = build_d0_matrix(edges, N_ITEMS)
        D1 = build_d1_matrix([], edges)
        _, H = compute_harmonic_projector(D0, D1)
        b1 = H.shape[1]
        c = n_components(D0, N_ITEMS)
        expected = len(edges) - N_ITEMS + c
        if b1 != expected:
            raise AssertionError(
                f"degeneracy g={g}: b1 = {b1}, expected E - n + c = {expected}")
        if verbose:
            drafted = len(edges) - (N_ITEMS - 1)
            note = ("matches drafted E-(n-1)" if drafted == expected
                    else f"drafted E-(n-1) = {drafted} is WRONG ({c} components)")
            print(f"  graph {g}: E = {len(edges):>2}, components = {c}, "
                  f"b1 = {b1:>2}  -- {note}")


def assert_truncation_trend(cells):
    """4.3 -- on the b1 = 1 topology, mean_T_ratio and realized_size both fall
    monotonically as k steps 128, 64, 32: separation preferentially removes
    extreme draws, so what survives is CONSERVATIVE."""
    ks = [128, 64, 32]
    have = [k for k in ks if k in cells]
    if len(have) < 2:
        raise AssertionError(f"truncation trend needs k in {ks}; have {sorted(cells)}")
    for field in ("mean_T_ratio", "realized_size"):
        vals = [cells[k][field] for k in have]
        # A cell that measured nothing cannot support a trend claim. It used to
        # arrive here as 0.0 and, being the smallest possible value, carried the
        # monotone test to a pass from the bottom of the ladder.
        empty = [k for k, v in zip(have, vals) if v is None]
        if empty:
            raise AssertionError(
                f"truncation trend: {field} is unmeasured at k={empty} "
                f"(no usable draws), so the trend is not readable there")
        if not all(a > b for a, b in zip(vals, vals[1:])):
            raise AssertionError(
                f"truncation trend: {field} not monotone decreasing over "
                f"k={have}: {[round(v, 4) for v in vals]}")
    return {k: {f: cells[k][f] for f in ("drop_rate", "mean_T_ratio", "realized_size")}
            for k in have}


def self_test():
    """Cross-check the pure-NumPy chi-squared tail against the closed forms."""
    print("chi-squared inversion vs closed forms (alpha = 0.05):")
    for df, exact in sorted(_EXACT_05.items()):
        got = get_chi2_critical_value(df, 0.05)
        err = abs(got - exact)
        if err > 1e-9:
            raise AssertionError(f"df={df}: {got!r} vs exact {exact!r} (err {err:.2e})")
        print(f"  df={df}: {got:.12f}  (closed form {exact:.12f}, err {err:.1e})")
    for df in (7, 13, 16, 21, 22):
        x = get_chi2_critical_value(df, 0.05)
        back = chi2_sf(x, df)
        if abs(back - 0.05) > 1e-12:
            raise AssertionError(f"df={df}: sf({x}) = {back}, expected 0.05")
        print(f"  df={df:>2}: {x:.10f}  (sf round-trip {back:.12f})")


# ------------------------------------------------------------------- driver
# An unmeasured cell carries None, not 0.0, all the way to the page: printing it
# as "--" keeps "we measured nothing here" visually distinct from "we measured
# zero", which is the distinction the 0.0 fallback destroyed.
def _r6(x):
    return None if x is None else round(x, 6)


def _f3(x, w):
    return f"{x:>{w}.3f}" if x is not None else f"{'--':>{w}}"


def main():
    ap = argparse.ArgumentParser(description="operating-envelope evaluator")
    ap.add_argument("--out", default="boundary_report.json")
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--filling", default="observed", choices=("observed", "empty"))
    ap.add_argument("--ks", type=int, nargs="+", default=list(K_GRID))
    ap.add_argument("--separation-rule", default="mle", choices=("mle", "saturated"),
                    dest="separation_rule",
                    help="'mle': the constrained fit diverges (what a deployment "
                         "faces). 'saturated': any edge at w=0 or w=k, as drafted.")
    args = ap.parse_args()

    print("=" * 82)
    print("SELF-TEST")
    print("=" * 82)
    self_test()
    print("\ndegeneracy (4.2), empty filling:")
    assert_degeneracy()
    degeneracy_status = "pass"          # only reachable if the assertion held

    print("\n" + "=" * 82)
    print(f"OPERATING ENVELOPE  --  filling={args.filling}, "
          f"{args.reps} replicates, alpha={ALPHA}")
    print("=" * 82)

    results = {}
    by_graph = {}
    for g in range(N_GRAPHS):
        edges, triangles = benchmark_topology(g, args.filling)
        eta = h0_eta(edges, triangles, g, rho_curl=1.0)
        cells = {}
        for k in args.ks:
            cell = run_envelope_evaluation(
                edges, triangles, k, eta=eta, num_replicates=args.reps,
                alpha=ALPHA, tag=f"c1|{args.filling}|{g}|{k}",
                separation_rule=args.separation_rule)
            cells[k] = cell
        by_graph[g] = cells
        first = cells[args.ks[0]]
        key = f"graph_{g}_{args.filling}"
        results[key] = {"b1": first["b1"], "E": first["E"]}
        for k in args.ks:
            results[key][f"k_{k}"] = {
                "drop_rate": round(cells[k]["drop_rate"], 6),
                "mean_T_ratio": _r6(cells[k]["mean_T_ratio"]),
                "realized_size": _r6(cells[k]["realized_size"]),
            }

        print(f"\ngraph {g}  (E = {first['E']}, b1 = {first['b1']})")
        print(f"  {'k':>5} {'drop%':>7} {'meanT/df':>9} {'size':>7} {'n_used':>7}"
              f"     {'ref drop%':>9} {'ref T/df':>9} {'ref size':>8}")
        for k in args.ks:
            c = cells[k]
            ref = REFERENCE.get((args.filling, g, k))
            if ref is None:
                rd = f"{'-':>9}"
                rt = f"{'-':>9}"
                rs = f"{'-':>8}"
            else:
                rd = f"{100 * ref[0]:>8.1f}%"
                rt = f"{ref[1]:>9.3f}"
                rs = f"{ref[2]:>8.3f}"
            print(f"  {k:>5} {100 * c['drop_rate']:>6.1f}% {_f3(c['mean_T_ratio'],9)} "
                  f"{_f3(c['realized_size'],7)} {c['n_usable']:>7}     {rd} {rt} {rs}")

    b1_one = [g for g, cells in by_graph.items() if cells[args.ks[0]]["b1"] == 1]
    print("\n" + "-" * 82)
    trend_status = "skipped"
    trend_detail = f"no benchmark graph has b1 = 1 under filling={args.filling}"
    if b1_one:
        g = b1_one[0]
        try:
            trend = assert_truncation_trend(by_graph[g])
            trend_status, trend_detail = "pass", ""
            print(f"4.3 truncation trend on graph {g} (b1 = 1): PASS -- "
                  "meanT/df and size both fall monotonically as k drops")
            for k, v in trend.items():
                print(f"    k={k:>4}: drop {100 * v['drop_rate']:>5.1f}%  "
                      f"meanT/df {_f3(v['mean_T_ratio'],5).strip()}  "
                      f"size {_f3(v['realized_size'],5).strip()}")
        except AssertionError as exc:
            trend_status, trend_detail = "fail", str(exc)
            print(f"4.3 truncation trend on graph {g} (b1 = 1): FAIL")
            print(f"    {exc}")
            used = {k: by_graph[g][k]["n_usable"] for k in (128, 64, 32)
                    if k in by_graph[g]}
            print(f"    usable draws per cell: {used}")
            if min(used.values(), default=0) < 200:
                print("    A cell this thin cannot support a trend claim either way:"
                      "\n    fix the separation rule before reading the trend.")
            else:
                print("    This oracle form has mean exactly b1 by construction"
                      "\n    (Cov(w) is exactly diag(k p (1-p))), so it does not"
                      "\n    inherit the shrinkage a refit on the surviving draws"
                      "\n    introduces. Expect a weaker decline than the fitted"
                      "\n    statistic shows -- and at low reps, none at all.")
    else:
        print(f"4.3 SKIPPED: {trend_detail}")

    payload = {
        "topology_test_suite": "2026_operating_envelope",
        "metrics_contract": ["drop_rate", "mean_T_ratio", "realized_size"],
        "config": {
            "n_items": N_ITEMS, "p_edge": P_EDGE, "beta": BETA, "gamma": GAMMA,
            "alpha": ALPHA, "filling": args.filling, "replicates": args.reps,
            "k_grid": list(args.ks),
            "statistic": "closed-form oracle Rao score in harmonic coordinates: "
                         "T = s^T (H^T I H)^-1 s with s = H^T (w - k p)",
            "separation_rule": args.separation_rule,
            "separation_rule_meaning": {
                "mle": "drop the draw when the constrained MLE diverges",
                "saturated": "drop the draw when any edge has w = 0 or w = k",
            }[args.separation_rule],
        },
        # What produced this file. `main` is the entry, so the fingerprint is
        # its closure -- which reaches the operators, the tail, the separation
        # rule and REFERENCE. boundary_report.json shipped with no fingerprint
        # and no gate constant, so the two numbers that actually select the
        # draws (the clip and the cut) were not recorded anywhere in it.
        "source_fingerprint": provenance.semantic_fingerprint(
            sys.modules[__name__], "main"),
        "assertions": {
            # Was the literal "pass" for a check that could not fail. Now says
            # what it is: no assertion runs here.
            "stationarity_4_1": STATIONARITY_NOT_APPLICABLE,
            # This one really does gate -- assert_degeneracy() raises above, so
            # reaching this line IS the pass. Derived rather than typed.
            "degeneracy_4_2": degeneracy_status,
            "truncation_trend_4_3": trend_status,
            "truncation_trend_detail": trend_detail,
        },
        "results": results,
    }
    Path(args.out).write_text(json.dumps(payload, indent=2) + "\n")
    print(f"\nwrote {args.out}")
    return 1 if trend_status == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
