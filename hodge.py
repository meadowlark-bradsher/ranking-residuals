"""
hodge.py — a small, hand-verifiable HodgeRank implementation.

Purpose: this is a REFERENCE implementation you check against, not a black box
you trust. Every operator is built explicitly so it matches a derivation you can
do by hand on a 4-node graph, and the correctness rests on the self_checks()
below — mathematical identities the code either satisfies or does not, with no
interpretation required.

Conventions (fix these; they are the ones to reproduce on paper)
----------------------------------------------------------------
Simplicial complex on a comparison graph:
    - vertices          = items (0-simplices)        -> C^0, "scores"
    - edges (i,j), i<j  = compared pairs (1-simplices)-> C^1, "flows"
    - triangles (i,j,k) = fully-observed triples     -> C^2, "circulations"

Coboundary operators (as dense matrices):
    D0 : C^0 -> C^1  ("grad"),  |E| x |V|
         row for edge (i,j) has -1 at col i, +1 at col j
         => (D0 @ s)[(i,j)] = s[j] - s[i]
    D1 : C^1 -> C^2  ("curl"),  |F| x |E|
         row for triangle (i,j,k) has +1 on (i,j), +1 on (j,k), -1 on (i,k)
         => (D1 @ Y)[(i,j,k)] = Y[(i,j)] + Y[(j,k)] - Y[(i,k)]
                              = Y_ij + Y_jk + Y_ki      (the discrete curl)

Fundamental identity (curl of grad is zero):  D1 @ D0 == 0.

Hodge decomposition of a flow Y in C^1 (orthogonal, spans C^1):
    Y = gradient  (in im D0)          # the rankable part; a scalar potential exists
      + curl      (in im D1^T)        # locally cyclic: nonzero around a triangle
      + harmonic  (in ker L1)         # globally cyclic: no triangle to blame

    L1 = D0 @ D0^T + D1^T @ D1   (the graph Helmholtzian; L0 = D0^T @ D0 one dim down)
    dim(harmonic) = |E| - rank(D0) - rank(D1) = first Betti number b1 (# of holes)

A flow with large harmonic mass has NO consistent scalar order, AND the failure
is invisible to any triangle-local statistic (see coefficient_of_consistency).
"""

import numpy as np
from itertools import combinations


# ======================================================================
# HANDOFF NOTE FOR THE CALIBRATION RIG BUILD  (read before extending)
# ======================================================================
# This file is the INSTRUMENT. The rig is a synthetic DATA SOURCE for it:
# import the operators/decomposition/entry points from here, never fork them.
#
# PUBLIC SURFACE the rig imports:
#   build_operators(n, edges, triangles)       -> D0 (grad), D1 (curl)
#   triangles_for_filling(edges, filling, ...)  -> 2-skeleton (empty|observed|custom)
#   hodge_decompose(Y, D0, D1)                  -> {gradient, curl, harmonic, scores}
#   hodge_projectors(D0, D1)                    -> P_grad, P_curl, P_harm  (spec §6)
#   analyze_flow(n, edges, Y, filling=...)      -> (g,c,h), b1 on a KNOWN flow   (§7 oracle path)
#   analyze_comparisons(n, comparisons, ...)    -> (g,c,h), zeta on a JUDGMENT LOG (§8.10 round-trip)
#   coefficient_of_consistency(n, directed)     -> zeta_hat  (the Pokharel baseline)
#   self_checks(...)                            -> math identities; fail loudly if broken
#
# Note the two doors are deliberate: analyze_flow validates the instrument on a
# known real-valued flow (magnitude meaningful); analyze_comparisons validates the
# judgment-log ROUND-TRIP. They are different tests — don't collapse them.
#
# TWO TRAPS — keep these as green acceptance tests; both are load-bearing:
#
#  (T1, spec §5.1)  A ±1 sign flow of even a PERFECTLY transitive order is NOT a
#     pure gradient: the ±1 quantization deposits spurious harmonic on the empty
#     filling. Verified here: integer order as ±1, empty fill -> h = 0.200 (not 0).
#     => integer edges and the bias bridge MUST use value-difference / log-odds,
#        never flow='pm1'. Use 'pm1' ONLY to read the tournament for zeta.
#
#  (T2, spec §4)  Filling is a MODELLING CHOICE, not intrinsic to the data — it
#     sets the curl/harmonic boundary. The SAME equal-spaced complex flow reads
#     h=1.0 on 'empty' and c=1.0 on 'observed'/full. analyze_comparisons defaults
#     to 'observed' (a real sparse arena); the RIG's calibration default is
#     'empty'. Always pass filling explicitly in the rig and LOG it; b1 is
#     reported on every config so provenance is recoverable.
#
# VERIFIED ORACLES (already pass against this file — keep them as regressions):
#   integer pool, value-diff flow:  h≈0 on empty AND observed              (§8.2)
#   equal-spaced complex-only:      empty h≈1 ; full c≈1                    (§8.3)
#   b1(complex-only, empty) == (m-1)(m-2)/2                                 (§8.4)
#   C–C round-trip via analyze_comparisons(filling='empty') -> h≈1         (§8.10)
#
# GAP IN THE SPEC — the STATISTICAL NULL is missing. The innocent integer pool is
# noise-LESS (h=0 by oracle). But the null the certificate's threshold is actually
# measured against is "genuinely rankable order + NOISY judge + sparse graph" =
# floor + c/R on COMPARABLE items, not the incomparable bridge. Add a comparator-
# noise knob on the I–I edges. Reference implementation belongs in rig/flows.py,
# NOT here — kept as a comment so it travels with the instrument:
#
#   def sample_sparse_btl_logodds(n, beta, p, k, rng):
#       """Sparse BTL, k comparisons/edge -> magnitude-aware log-odds flow.
#       Clean data is ~pure gradient; harmonic appears ONLY via sparsity (holes),
#       giving the floor+c/R null. This is the noisy-I–I comparator the rig lacks."""
#       theta = beta * (n - 1 - np.arange(n))
#       edges, Y, directed = [], [], set()
#       for i in range(n):
#           for j in range(i + 1, n):
#               if rng.random() < p:
#                   pj = 1 / (1 + np.exp(-(theta[j] - theta[i])))      # P(j beats i)
#                   wins_j = int(rng.binomial(k, pj))
#                   phat = np.clip(wins_j / k, 1 / (2 * k), 1 - 1 / (2 * k))
#                   edges.append((i, j)); Y.append(np.log(phat / (1 - phat)))
#                   directed.add((j, i) if 2 * wins_j >= k else (i, j))
#       return edges, np.array(Y), directed
#
# Demo 1 (the 4-cycle: h=1.0, zeta undefined) lives in fde.py — keep it as the
# minimal-topology regression test; no §8 pool exercises that bare harmonic case.
# ======================================================================


# ----------------------------------------------------------------------
# Operators
# ----------------------------------------------------------------------
def build_operators(n, edges, triangles):
    """Return dense D0 (|E| x n) and D1 (|F| x |E|). edges: list of (i,j) i<j.
    triangles: list of (i,j,k) i<j<k. Edge order defines the flow index order."""
    edge_index = {e: r for r, e in enumerate(edges)}
    E, F = len(edges), len(triangles)

    D0 = np.zeros((E, n))
    for r, (i, j) in enumerate(edges):
        D0[r, i] = -1.0
        D0[r, j] = +1.0

    D1 = np.zeros((F, E))
    for r, (i, j, k) in enumerate(triangles):
        D1[r, edge_index[(i, j)]] += 1.0
        D1[r, edge_index[(j, k)]] += 1.0
        D1[r, edge_index[(i, k)]] -= 1.0   # (i,k) traversed backwards in the loop
    return D0, D1


def observed_triangles(edges):
    """The 2-skeleton = every triple whose three edges are all observed.
    This is the honest modelling choice (matches 'fully observed triplets')."""
    eset = set(edges)
    verts = sorted({v for e in edges for v in e})
    tris = []
    for i, j, k in combinations(verts, 3):
        if (i, j) in eset and (j, k) in eset and (i, k) in eset:
            tris.append((i, j, k))
    return tris


# ----------------------------------------------------------------------
# Decomposition
# ----------------------------------------------------------------------
def hodge_decompose(Y, D0, D1):
    """Split flow Y into (gradient, curl, harmonic) by orthogonal projection.
    gradient = proj onto col(D0); curl = proj onto col(D1^T); harmonic = remainder.
    Returns a dict incl. the fitted potential s (the HodgeRank scores)."""
    # gradient: least-squares potential s minimising ||D0 s - Y||, then grad = D0 s
    s, *_ = np.linalg.lstsq(D0, Y, rcond=None)
    grad = D0 @ s
    # curl: least-squares onto column space of D1^T
    if D1.shape[0] > 0:
        c, *_ = np.linalg.lstsq(D1.T, Y, rcond=None)
        curl = D1.T @ c
    else:
        curl = np.zeros_like(Y)
    harmonic = Y - grad - curl
    return {"scores": s, "gradient": grad, "curl": curl, "harmonic": harmonic}


def mass_fractions(Y, comp):
    """Fraction of total squared L2 energy in each component."""
    tot = float(Y @ Y)
    if tot == 0:
        return {"gradient": 0.0, "curl": 0.0, "harmonic": 0.0}
    return {k: float(comp[k] @ comp[k]) / tot for k in ("gradient", "curl", "harmonic")}


def harmonic_basis(D0, D1):
    """Orthonormal basis for ker(L1) (the harmonic subspace). Columns = holes."""
    E = D0.shape[0]
    L1 = D0 @ D0.T + (D1.T @ D1 if D1.shape[0] else np.zeros((E, E)))
    w, V = np.linalg.eigh(L1)
    tol = max(E, 1) * np.finfo(float).eps * (w.max() if w.size else 1.0) * 10
    return V[:, w <= tol]


# ----------------------------------------------------------------------
# Self-checks: the trust anchor. These are identities, not opinions.
# ----------------------------------------------------------------------
def self_checks(Y, D0, D1, comp, atol=1e-9):
    E = D0.shape[0]
    checks = {}
    # 1. curl of grad is zero
    checks["D1@D0 == 0"] = (D1 @ D0 if D1.shape[0] else np.zeros((0, D0.shape[1]))).size == 0 \
        or np.allclose(D1 @ D0, 0, atol=atol)
    # 2. components reconstruct Y
    recon = comp["gradient"] + comp["curl"] + comp["harmonic"]
    checks["grad+curl+harm == Y"] = np.allclose(recon, Y, atol=atol)
    # 3. mutual orthogonality. A component with ~machine-zero norm is trivially
    #    orthogonal to everything; floor it so noise-vs-noise doesn't false-fail.
    g, c, h = comp["gradient"], comp["curl"], comp["harmonic"]
    def orth(u, v):
        nu, nv = np.linalg.norm(u), np.linalg.norm(v)
        if nu < 1e-10 or nv < 1e-10:
            return True
        return abs(float(u @ v)) < 1e-6 * nu * nv
    checks["grad _|_ curl"] = orth(g, c)
    checks["grad _|_ harm"] = orth(g, h)
    checks["curl _|_ harm"] = orth(c, h)
    # 4. harmonic really is curl-free and divergence-free (in ker L1)
    checks["harm is div-free (D0^T h == 0)"] = np.allclose(D0.T @ h, 0, atol=1e-7)
    checks["harm is curl-free (D1 h == 0)"] = D1.shape[0] == 0 or np.allclose(D1 @ h, 0, atol=1e-7)
    # 5. dim(harmonic) == b1 == |E| - rank(D0) - rank(D1)  (pure linear algebra)
    rk0 = np.linalg.matrix_rank(D0)
    rk1 = np.linalg.matrix_rank(D1) if D1.shape[0] else 0
    b1_formula = E - rk0 - rk1
    b1_nullspace = harmonic_basis(D0, D1).shape[1]
    checks[f"dim(harmonic)=={b1_nullspace}==b1=={b1_formula}"] = (b1_nullspace == b1_formula)
    return checks, b1_nullspace


# ----------------------------------------------------------------------
# Coefficient of consistency (Kendall; Pokharel Eq. 1, 6, 7)
# ----------------------------------------------------------------------
def coefficient_of_consistency(n_items, directed):
    """zeta over the fully-observed triples of a (possibly sparse) tournament.
    `directed` is a set of ordered pairs (a,b) meaning 'a beats b'.
    Returns (zeta_hat, n_observed_triples). zeta_hat is NaN if no triple is
    fully observed -- i.e. the statistic is *blind* on that graph.
    A triple is circular iff each of the three items has in-triple out-degree 1."""
    beats = directed
    verts = sorted({v for pair in beats for v in pair})
    def observed(a, b):
        return (a, b) in beats or (b, a) in beats
    O = 0
    T_obs = 0
    for a, b, c in combinations(verts, 3):
        if not (observed(a, b) and observed(b, c) and observed(a, c)):
            continue
        O += 1
        outdeg = {a: 0, b: 0, c: 0}
        for x, y in ((a, b), (b, c), (a, c)):
            if (x, y) in beats:
                outdeg[x] += 1
            else:
                outdeg[y] += 1
        if set(outdeg.values()) == {1}:      # {1,1,1} -> circular
            T_obs += 1
    if O == 0:
        return float("nan"), 0
    r = T_obs / O                            # inconsistency rate (Pokharel Def 2.3)
    n = n_items
    from math import comb
    if n % 2:
        Tmax = n * (n**2 - 1) / 24
    else:
        Tmax = n * (n**2 - 4) / 24
    scaling = comb(n, 3) / Tmax if Tmax > 0 else 0.0
    zeta = 1.0 - r * scaling                  # Eq. (5)/(7)
    return zeta, O


# ----------------------------------------------------------------------
# From comparison outcomes to a flow + a tournament (same data, two lenses)
# ----------------------------------------------------------------------
def flow_and_tournament(edges, winner):
    """edges: list of (i,j) i<j. winner: dict edge->winning vertex (single comp/edge).
    Returns (Y, directed): Y[r] = +1 if j beats i else -1 on edge (i,j)=edges[r];
    directed = set of (winner, loser) ordered pairs for zeta."""
    Y = np.zeros(len(edges))
    directed = set()
    for r, (i, j) in enumerate(edges):
        w = winner[(i, j)]
        loser = i if w == j else j
        directed.add((w, loser))
        Y[r] = +1.0 if w == j else -1.0
    return Y, directed


# ----------------------------------------------------------------------
# Filling convention + explicit projectors (for the calibration rig)
# ----------------------------------------------------------------------
def triangles_for_filling(edges, filling="observed", triangles=None):
    """The 2-skeleton is a MODELLING CHOICE that sets the curl/harmonic boundary.
    Expose it; never hard-wire it.
        "empty"    -> [] : no 2-cells. Curl space trivial; all non-gradient mass
                     reads as harmonic. Cleanest, unambiguous harmonic reading.
        "observed" -> every triple whose 3 edges are present (== "full" on a
                     complete graph). Collapses harmonic where triangles exist.
        "custom"   -> the explicit `triangles` list you pass in.
    """
    if filling == "empty":
        return []
    if filling in ("observed", "full"):
        return observed_triangles(edges)
    if filling == "custom":
        if triangles is None:
            raise ValueError("filling='custom' requires an explicit triangles list")
        return list(triangles)
    raise ValueError(f"unknown filling: {filling!r}")


def hodge_projectors(D0, D1):
    """Explicit orthogonal projectors onto the three subspaces, matching the rig
    spec: P_grad = D0 pinv(D0), P_curl = D1^T pinv(D1^T), P_harm = I - the two.
    On empty filling D1 is 0xE and P_curl = 0. Provided so the rig's oracle
    (e.g. tr(P_harm Sigma)/R) uses THIS instrument's projectors, not a fork."""
    E = D0.shape[0]
    P_grad = D0 @ np.linalg.pinv(D0)
    if D1.shape[0] > 0:
        P_curl = D1.T @ np.linalg.pinv(D1.T)
    else:
        P_curl = np.zeros((E, E))
    P_harm = np.eye(E) - P_grad - P_curl
    return P_grad, P_curl, P_harm


# ----------------------------------------------------------------------
# Entry points
# ----------------------------------------------------------------------
def analyze_flow(n_items, edges, Y, filling="empty", triangles=None):
    """Decompose a KNOWN real-valued flow Y on a KNOWN edge set. This is the
    instrument applied directly, bypassing any win/loss encoding -- use it to
    validate the rig's internal (g,c,h) against the oracle (spec section 7),
    where the flow magnitude is meaningful (value-differences etc.).
        edges: list of (i,j), i<j, aligned with Y.
    Returns fractions, b1, self-check status, and the fitted potential."""
    edges = list(edges)
    Y = np.asarray(Y, dtype=float)
    tris = triangles_for_filling(edges, filling, triangles)
    D0, D1 = build_operators(n_items, edges, tris)
    comp = hodge_decompose(Y, D0, D1)
    fr = mass_fractions(Y, comp)
    checks, b1 = self_checks(Y, D0, D1, comp)
    return {"fractions": fr, "b1_holes": b1, "total_mass": float(Y @ Y),
            "scores": comp["scores"], "self_checks_pass": all(checks.values()),
            "filling": filling}


def analyze_comparisons(n_items, comparisons, filling="observed", triangles=None,
                        flow="logodds", clamp=None):
    """The judgment-log entry point. THIS is what real judge data (and the rig's
    emitted log, spec section 10) flows through.

    comparisons: iterable of (winner_item, loser_item), 0-indexed. MAY repeat a
      pair: repeats are aggregated and the edge flow is reconstructed from the
      empirical win rate -- so magnitude survives (a single row is only +/-1).

    flow: how an aggregated edge becomes a scalar. DEFAULT 'logodds' is
      magnitude-aware; BTL is linear in log-odds, so a clean order reconstructs
      as a near-exact gradient. 'signed' = 2*winrate-1. 'pm1' = majority sign.
      *** TRAP (spec 5.1): 'pm1' of even a perfectly transitive order is NOT a
      pure gradient -- it deposits spurious harmonic on the empty filling. Use
      'pm1' only to read the tournament, never to reproduce a magnitude flow. ***

    filling: see triangles_for_filling. NOTE the default here is 'observed' to
      match a real sparse arena; the RIG's calibration default is 'empty'
      (unambiguous harmonic). Pass filling='empty' for rig round-trip checks.
    """
    # aggregate repeats per unordered pair
    wins = {}      # (i,j) i<j -> [wins_i, wins_j]
    for w, l in comparisons:
        i, j = (w, l) if w < l else (l, w)
        rec = wins.setdefault((i, j), [0, 0])
        if w == j:
            rec[1] += 1
        else:
            rec[0] += 1
    edges = sorted(wins)
    Y = np.zeros(len(edges))
    directed = set()
    for r, (i, j) in enumerate(edges):
        wi, wj = wins[(i, j)]
        k = wi + wj
        directed.add((j, i) if wj >= wi else (i, j))     # majority, for zeta
        if flow == "pm1":
            Y[r] = 1.0 if wj >= wi else -1.0
        elif flow == "signed":
            Y[r] = 2.0 * wj / k - 1.0
        elif flow == "logodds":
            c = clamp if clamp is not None else 1.0 / (2 * k)
            phat = min(max(wj / k, c), 1.0 - c)
            Y[r] = np.log(phat / (1.0 - phat))
        else:
            raise ValueError(f"unknown flow: {flow!r}")

    tris = triangles_for_filling(edges, filling, triangles)
    D0, D1 = build_operators(n_items, edges, tris)
    comp = hodge_decompose(Y, D0, D1)
    fr = mass_fractions(Y, comp)
    checks, b1 = self_checks(Y, D0, D1, comp)
    zeta, O = coefficient_of_consistency(n_items, directed)
    return {"fractions": fr, "zeta_hat": zeta, "observed_triples": O,
            "b1_holes": b1, "total_mass": float(Y @ Y), "scores": comp["scores"],
            "self_checks_pass": all(checks.values()), "filling": filling,
            "flow": flow}