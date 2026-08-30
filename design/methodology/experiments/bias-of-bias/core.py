"""Measurement primitive for the bias-of-bias probes.

The shipped `floor_measurement` is right for production and wrong for these
probes, for one reason: it derives the mask seed from the config fingerprint, so
`cfg.with_(rho=...)` varies rho AND hands you a different graph. Every axis we
want to sweep is entangled with the topology it should be held against.

So this module separates the three stages the production path fuses:

    mask_for(cfg, seed)      the graph -- depends on seed, n, p and NOTHING else
    draw(...)                sampling  -- win counts per (k, rep) on that graph
    energies(draw, corr)     encoding  -- counts -> flow -> harmonic energy
    fit(...)                 estimation-- energies -> floor, at a chosen window

rho and the fit window enter only at the last stage. Sweeping them therefore
needs no resampling at all: draw once, refit many times. That makes probes 1 and
4 exact rather than noisy, and nearly free. eps enters at `draw` (it changes the
latent) so it does need resampling -- but the mask stays pinned, which the
production path would not do.
"""
from __future__ import annotations

import itertools
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import hodge
from rig import flows, oracle


def mask_for(n, p, seed):
    """The graph. Depends on (n, p, seed) only -- never on rho, eps or the window."""
    rng = np.random.default_rng(90_000 + seed)
    return [(i, j) for i, j in itertools.combinations(range(n), 2) if rng.random() < p]


@dataclass
class Draw:
    seed: int
    eps: float
    ks: tuple
    wins: dict                 # k -> (reps, |E|) win counts
    pe: np.ndarray
    Ph: np.ndarray
    c_oracle: float
    n_edges: int
    b1: int


def draw(n, p, beta, gamma, eps, seed, ks, reps, filling="observed"):
    """Sample win counts on a pinned graph. Returns None if the graph carries no hole."""
    mask = mask_for(n, p, seed)
    if len(mask) < 3:
        return None
    D0, D1 = hodge.build_operators(n, mask, hodge.triangles_for_filling(mask, filling))
    basis = hodge.harmonic_basis(D0, D1)
    if basis.shape[1] < 1:
        return None
    _, _, Ph = hodge.hodge_projectors(D0, D1)
    h = basis[:, 0] / np.linalg.norm(basis[:, 0])
    latent = D0 @ flows.theta_gamma(n, beta, gamma) + eps * h
    pe = 1.0 / (1.0 + np.exp(-latent))
    rng = np.random.default_rng(500_000 + seed)
    wins = {k: rng.binomial(k, np.broadcast_to(pe, (reps, len(pe)))) for k in ks}
    return Draw(seed=seed, eps=eps, ks=tuple(ks), wins=wins, pe=pe, Ph=Ph,
                c_oracle=oracle.c_oracle(Ph, pe), n_edges=len(mask), b1=basis.shape[1])


def energies(d: Draw, correction=None):
    """Harmonic energy per k. `correction='firth'` applies the first-order logit
    bias correction to each edge before projecting."""
    out = []
    for k in d.ks:
        w = d.wins[k]
        phat = np.clip(w / k, 1.0 / (2 * k), 1.0 - 1.0 / (2 * k))
        Y = np.log(phat / (1.0 - phat))
        if correction == "firth":
            # E[logit(p^)] = logit(p) + (2p-1)/(2k p(1-p)) + O(k^-2); subtract the
            # plug-in estimate of that term.
            Y = Y - (2 * phat - 1) / (2 * k * phat * (1 - phat))
        out.append(float(np.mean(np.einsum("ij,jk,ik->i", Y, d.Ph, Y))))
    return out


def fit(ks, E, window):
    """OLS of energy on 1/k over the points at or above `window`."""
    ks = np.asarray(ks, float); E = np.asarray(E, float)
    sel = ks >= window
    if sel.sum() < 2:
        return None
    K = ks[sel]
    A = np.column_stack([np.ones_like(K), 1.0 / K])
    floor, c = np.linalg.lstsq(A, E[sel], rcond=None)[0]
    return {"floor": float(floor), "c": float(c), "n_points": int(sel.sum()),
            "window": float(window)}


def window_for(c_oracle, floor_target, rho, ks, fit_k_min=64):
    """The derived window, exactly as rig.sweep computes it."""
    if floor_target <= 0:
        return float(max(fit_k_min, sorted(ks)[-3]))
    return max(float(fit_k_min), c_oracle / (rho * floor_target))


def record(probe, question, falsifies, verdict, value, config, note=None):
    return {"probe": probe, "question": question, "falsifies": falsifies,
            "verdict": verdict, "value": value, "config": config, "note": note}
