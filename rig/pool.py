"""Vertex pools (spec §1, §2.2, §5.2).

Two populations, one index space:
    integers  0 .. n_int-1                  -- the rankable population
    complex   n_int .. n_int+n_cplx-1       -- the unorderable population

Integer ids sort below complex ids, so every bridge edge (i,j) with i<j has i as
the integer and j as the complex vertex. That is relied on in rig.flows.
"""

from __future__ import annotations

import numpy as np


def integer_values(n_int: int) -> np.ndarray:
    """The rankable population: a genuine total order, as magnitudes not signs (§5.1)."""
    return np.arange(n_int, dtype=float)


def complex_angles(n_cplx: int, kind: str = "equal_spaced", rng=None) -> np.ndarray:
    """Angles theta_k for the complex pool. Equal spacing is divergence-free (§5.5)."""
    if n_cplx == 0:
        return np.zeros(0)
    if kind == "equal_spaced":
        return 2.0 * np.pi * np.arange(n_cplx) / n_cplx
    if kind == "random":
        if rng is None:
            raise ValueError("complex_pool='random' needs an rng")
        return np.sort(rng.uniform(0, 2 * np.pi, n_cplx))
    if kind == "surrogate_defeating":
        return surrogate_defeating_pool(n_cplx, rng)[0]
    raise ValueError(f"unknown complex_pool: {kind!r}")


def complex_points(angles: np.ndarray, radii: np.ndarray | None = None) -> np.ndarray:
    """The actual complex numbers. Default |z|=1 -- which is what defeats the
    magnitude surrogate: on the unit circle every magnitude ties (§5.2)."""
    r = np.ones_like(angles) if radii is None else radii
    return r * np.exp(1j * angles)


def _kendall_tau(a: np.ndarray, b: np.ndarray) -> float:
    """Kendall tau between two score vectors, via concordant/discordant pairs."""
    n = len(a)
    if n < 2:
        return 0.0
    con = dis = 0
    for i in range(n):
        for j in range(i + 1, n):
            s = np.sign(a[j] - a[i]) * np.sign(b[j] - b[i])
            if s > 0:
                con += 1
            elif s < 0:
                dis += 1
    tot = con + dis
    return (con - dis) / tot if tot else 0.0


def surrogate_defeating_pool(n_cplx: int, rng, n_candidates: int = 4000):
    """Points where real-part / magnitude / argument orders MUTUALLY disagree (§5.2).

    On the unit circle magnitude ties for everyone, which defeats the magnitude
    surrogate but says nothing about the others. A *richer* pool -- radii allowed to
    vary -- has to defeat all three at once, so search for the candidate minimising
    the worst pairwise Kendall tau among the three surrogate orders.

    Returns (angles, radii, max_abs_tau).
    """
    if rng is None:
        raise ValueError("surrogate_defeating needs an rng")
    best = None
    for _ in range(n_candidates):
        ang = rng.uniform(0, 2 * np.pi, n_cplx)
        rad = rng.uniform(0.5, 1.5, n_cplx)
        z = rad * np.exp(1j * ang)
        orders = (np.real(z), np.abs(z), np.angle(z) % (2 * np.pi))
        worst = max(
            abs(_kendall_tau(orders[i], orders[j]))
            for i in range(3) for j in range(i + 1, 3)
        )
        if best is None or worst < best[2]:
            best = (ang, rad, worst)
    return best


def rotational_winner(theta_i: float, theta_j: float) -> int:
    """The C-C rule (§2.2): j beats i iff 0 < (theta_j - theta_i) mod 2pi < pi.

    Returns +1 if j beats i, -1 if i beats j. Raises on the antipodal tie, which is
    why odd m is required for equal spacing (§2.2).
    """
    d = (theta_j - theta_i) % (2 * np.pi)
    if np.isclose(d, 0.0) or np.isclose(d, np.pi) or np.isclose(d, 2 * np.pi):
        raise ValueError(
            f"antipodal/degenerate complex pair (delta={d:.6f}): the rotational rule is "
            "undefined. Use odd m for equal spacing (§2.2)."
        )
    return 1 if 0 < d < np.pi else -1
