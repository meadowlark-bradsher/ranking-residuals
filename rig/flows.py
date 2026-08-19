"""Edge-flow generators (spec §2.1-§2.6).

Three signatures, deliberately kept apart (§1):
  I-I clean gradient  -> pure gradient, h=0 exactly
  I-I noisy BTL       -> the statistical null; harmonic decays as c/k
  I-I + eps*h_unit    -> the MISSPECIFIED null (§2.5); floor = eps^2 exactly
  C-C rotational      -> harmonic on 'empty', curl on 'observed'
  I-C bridge          -> variance (decays) | gradient (no harmonic) | fixed (persists)

Nothing here decomposes a flow. All operators come from hodge.py (§6).
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np

import hodge
from rig.pool import rotational_winner


@dataclass
class Block:
    """One block of edges plus everything needed to emit an exact judgment log.

    `encoding` drives emission (§10) and the three paths are NOT interchangeable:
      "counts"    -- the generator has native win counts; replay them, exact.
      "sign"      -- a +-1 RULE; emit all R rows one way. Quantizing a sign rule
                     through round(k*sigmoid(Y)) collapses to a tie at small k.
      "magnitude" -- a real-valued flow; quantized, residual reported.
    """

    edges: list[tuple[int, int]]
    Y: np.ndarray
    wins: np.ndarray | None = None   # wins of the HIGHER-indexed vertex j, per edge
    k: int | None = None             # comparisons per edge behind `wins`
    directed: set | None = None      # (winner, loser) pairs, for zeta
    encoding: str = "magnitude"

    def __len__(self) -> int:
        return len(self.edges)

    def rms(self) -> float:
        return float(np.sqrt(np.mean(self.Y ** 2))) if len(self.Y) else 0.0


# ----------------------------------------------------------------------
# Latent potentials (§2.4)
# ----------------------------------------------------------------------
def theta_gamma(n: int, beta: float, gamma: float, standardize: bool = True) -> np.ndarray:
    """theta_i ∝ ((n-1-i)/(n-1))**gamma, standardized to the gamma=1 reference std.

    At gamma=1 this reproduces the reference contract theta_i = beta*(n-1-i) exactly
    up to an additive constant -- and only differences theta_j - theta_i enter the
    flow, so 'up to a constant' is 'exactly' (§2.4).

    Standardization is REQUIRED: without it, raising gamma shrinks the spread and the
    floor would fall for a reason that has nothing to do with asymmetry.
    """
    if n < 2:
        return np.zeros(n)
    x = ((n - 1 - np.arange(n)) / (n - 1)) ** float(gamma)
    if not standardize:
        return beta * (n - 1) * x
    ref = beta * (n - 1 - np.arange(n, dtype=float))
    xc = x - x.mean()
    if xc.std() == 0:
        return np.zeros(n)
    return xc / xc.std() * ref.std()


def theta_random(n: int, beta: float, rng) -> np.ndarray:
    """Secondary robustness shape (§2.4): sorted skewed draws, same std as the reference."""
    draws = np.sort(rng.lognormal(0.0, 1.0, n))[::-1]
    ref = beta * (n - 1 - np.arange(n, dtype=float))
    d = draws - draws.mean()
    return d / d.std() * ref.std() if d.std() else np.zeros(n)


def latent_potential(n: int, btl, gamma: float, rng=None) -> np.ndarray:
    if btl.theta_shape == "gamma":
        return theta_gamma(n, btl.beta, gamma, btl.standardize_theta)
    if btl.theta_shape == "random":
        return theta_random(n, btl.beta, rng)
    raise ValueError(f"unknown theta_shape: {btl.theta_shape!r}")


# ----------------------------------------------------------------------
# Sparse graph + BTL sampling (§2.4)
# ----------------------------------------------------------------------
def sample_sparse_graph(n: int, p: float, rng) -> list[tuple[int, int]]:
    """Draw the edge mask ONCE per seed. It must NOT be redrawn per k (§2.4):
    P_h moves with the edge set, so the floor would stop being a constant."""
    return [(i, j) for i, j in combinations(range(n), 2) if rng.random() < p]


def logodds_from_counts(wins_j: np.ndarray, k: int) -> np.ndarray:
    """Clamped empirical log-odds -- byte-for-byte the instrument's own encoding.

    The clamp is 1/(2k); it is the instrument's estimator contract and is NOT widened
    to make the rig's fitting window more comfortable (§2.6).
    """
    phat = np.clip(np.asarray(wins_j, dtype=float) / k, 1.0 / (2 * k), 1.0 - 1.0 / (2 * k))
    return np.log(phat / (1.0 - phat))


def btl_counts(p_edge: np.ndarray, k: int, rng) -> np.ndarray:
    """k Bernoulli comparisons per edge; returns wins of the higher-indexed vertex."""
    return rng.binomial(k, p_edge)


def saturation(p_edge: np.ndarray, k: int) -> float:
    """§2.6 pre-filter, closed form: expected fraction of edges hitting the clamp."""
    p = np.asarray(p_edge, dtype=float)
    return float(np.mean(p ** k + (1.0 - p) ** k))


def sample_sparse_btl_logodds(n, beta, p, k, rng, theta=None):
    """The reference contract from hodge.py's handoff note, signature preserved.

    Sparse BTL, k comparisons/edge -> magnitude-aware log-odds flow. Clean data is
    ~pure gradient; harmonic appears ONLY via sparsity (holes).
    """
    if theta is None:
        theta = beta * (n - 1 - np.arange(n, dtype=float))
    edges, Y, directed = [], [], set()
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                pj = 1 / (1 + np.exp(-(theta[j] - theta[i])))
                wins_j = int(rng.binomial(k, pj))
                phat = np.clip(wins_j / k, 1 / (2 * k), 1 - 1 / (2 * k))
                edges.append((i, j))
                Y.append(np.log(phat / (1 - phat)))
                directed.add((j, i) if 2 * wins_j >= k else (i, j))
    return edges, np.array(Y), directed


# ----------------------------------------------------------------------
# The misspecification knob (§2.5) -- the actual floor source
# ----------------------------------------------------------------------
def harmonic_unit(D0: np.ndarray, D1: np.ndarray) -> np.ndarray:
    """A unit harmonic direction of THIS graph and THIS filling (§2.5).

    The floor is eps^2 only if injection and measurement share a filling: inject
    against 'empty' and read on 'observed' and the mass reclassifies.
    """
    basis = hodge.harmonic_basis(D0, D1)
    if basis.shape[1] < 1:
        raise ValueError(
            "b1 = 0: this graph+filling has no harmonic direction to inject into. "
            "Increase sparsity (lower p) or use filling='empty' (§2.5)."
        )
    h = basis[:, 0]
    return h / np.linalg.norm(h)


def misspecified_latent(D0, theta, eps: float, h_unit: np.ndarray) -> np.ndarray:
    """latent = D0 @ theta + eps * h_unit  (§2.5).

    P_h annihilates D0@theta exactly (it is a pure gradient) and fixes h_unit, so the
    budget-independent floor is exactly eps^2 -- a known oracle, not a fitted quantity.
    """
    return D0 @ theta + float(eps) * h_unit


def null_block(edges, D0, D1, theta, eps, k, rng) -> Block:
    """One draw of the (possibly misspecified) statistical null on a FIXED graph."""
    latent = misspecified_latent(D0, theta, eps, harmonic_unit(D0, D1)) if eps else D0 @ theta
    pe = 1.0 / (1.0 + np.exp(-latent))
    wins = btl_counts(pe, k, rng)
    Y = logodds_from_counts(wins, k)
    directed = {(j, i) if 2 * w >= k else (i, j) for (i, j), w in zip(edges, wins)}
    return Block(list(edges), Y, wins=wins, k=k, directed=directed, encoding="counts")


# ----------------------------------------------------------------------
# I-I clean gradient (§2.1)
# ----------------------------------------------------------------------
def clean_gradient_block(values: np.ndarray, edges) -> Block:
    """Y[i,j] = value[j] - value[i]. Magnitude, never +-1 (§5.1). Reads h=0 exactly."""
    Y = np.array([values[j] - values[i] for i, j in edges], dtype=float)
    directed = {(j, i) if Y[r] > 0 else (i, j) for r, (i, j) in enumerate(edges)}
    return Block(list(edges), Y, directed=directed, encoding="magnitude")


# ----------------------------------------------------------------------
# C-C rotational (§2.2)
# ----------------------------------------------------------------------
def rotational_block(angles: np.ndarray, edges, n_int: int) -> Block:
    """The adversarial block: +-1 by the rotational rule. Its +-1-ness is intrinsic to
    the rule, not a quantization of a magnitude order -- §5.1 does not apply here."""
    Y, directed = [], set()
    for i, j in edges:
        s = rotational_winner(angles[i - n_int], angles[j - n_int])
        Y.append(float(s))
        directed.add((j, i) if s > 0 else (i, j))
    return Block(list(edges), np.array(Y), directed=directed, encoding="sign")


# ----------------------------------------------------------------------
# I-C bridge (§2.3)
# ----------------------------------------------------------------------
def bridge_block(edges, n_int: int, mode: str, s_int: np.ndarray,
                 gap: float, R: int, rng) -> Block:
    """Bridge edges are always (integer, complex) with the integer first (rig.pool)."""
    if R < 2:
        raise ValueError(f"bridge_R={R} < 2: the clamp would pin every flow to 0 (§10)")

    if mode == "bias_rule":
        # POTENTIAL-CONSISTENT with the I-I block (§2.3). A *constant* bridge is only a
        # global gradient when I-I is flat; against a sloped I-I it deposits harmonic of
        # its own and breaks §7's "harmonic = C-C floor exactly".
        s_c = float(np.min(s_int)) - float(gap)
        Y = np.array([s_c - s_int[i] for i, _ in edges], dtype=float)
        directed = {(j, i) if Y[r] > 0 else (i, j) for r, (i, j) in enumerate(edges)}
        return Block(list(edges), Y, directed=directed, encoding="magnitude")

    if mode == "variance_fresh":
        # Fresh fair +-1 per COMPARISON -> variance, decays as 1/R (§5.3).
        wins = rng.binomial(R, 0.5, size=len(edges))
    elif mode == "variance_fixed":
        # +-1 drawn once per PAIR and reused -> persistent random field (§5.3).
        wins = np.where(rng.random(len(edges)) < 0.5, R, 0)
    else:
        raise ValueError(f"unknown bridge_mode: {mode!r}")

    Y = logodds_from_counts(wins, R)
    directed = {(j, i) if 2 * w >= R else (i, j) for (i, j), w in zip(edges, wins)}
    return Block(list(edges), Y, wins=wins, k=R, directed=directed, encoding="counts")
