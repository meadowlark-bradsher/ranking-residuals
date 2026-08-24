"""Is the b1=0 rate one statistic measured twice, or two different statistics?

Two numbers were in circulation for n=6 under filling='observed', p=0.45: the
spec/paper's 64.7% (Sec 10, Observation 2) and a 67.2% measured during the
build. This settles which of three things they are.

The two paths differ only in how the mask RNG is seeded:

  (a) the Sec 10 recipe      default_rng(77000 + s)
  (b) the floor path         default_rng(cfg.derive_seed("floor_mask", gamma, eps, s))

Both then call flows.sample_sparse_graph(n, 0.45, rng), so they are nominally
the same ensemble. (b) additionally takes gamma and eps into the seed hash, so
if the rate moved with them the mask draw would not be independent of the
latent -- worth knowing, and it is the thing this script is built to detect.

Both counting conventions are reported, because they are not the same number
and the disagreement could live entirely there:

  marginal     (small masks + b1=0) / N     <- what Sec 10 and seed_drop_rate use
  conditional  b1=0 / (N - small masks)     <- the rate among fittable masks

At n=6 a G(6, 0.45) draw has only 15 candidate edges, so |E| < 3 is common and
the two conventions can differ a lot. At n=12 it is negligible.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import hodge
from rig import flows
from rig.config import RigConfig

HERE = Path(__file__).parent
OUT = HERE / "results" / "b1_rate.json"
N_SEEDS = 5000
P = 0.45
FILLING = "observed"


def classify(n: int, rng) -> str:
    """'small' | 'b1_zero' | 'has_hole' for one mask draw."""
    mk = flows.sample_sparse_graph(n, P, rng)
    if len(mk) < 3:
        return "small"
    d0, d1 = hodge.build_operators(n, mk, hodge.triangles_for_filling(mk, FILLING))
    return "has_hole" if hodge.harmonic_basis(d0, d1).shape[1] >= 1 else "b1_zero"


def tally(n: int, seeder, n_seeds: int = N_SEEDS) -> dict:
    """Counts and binomial standard errors for both conventions."""
    c = {"small": 0, "b1_zero": 0, "has_hole": 0}
    for s in range(n_seeds):
        c[classify(n, seeder(s))] += 1
    N = n_seeds
    fittable = N - c["small"]
    marg = (c["small"] + c["b1_zero"]) / N
    cond = c["b1_zero"] / fittable if fittable else float("nan")
    return {"n": n, "n_seeds": N, **c,
            "marginal_rate": marg,
            "marginal_se": float(np.sqrt(marg * (1 - marg) / N)),
            "conditional_rate": cond,
            "conditional_se": (float(np.sqrt(cond * (1 - cond) / fittable))
                               if fittable else float("nan")),
            "small_rate": c["small"] / N}


def path_a(n, n_seeds=N_SEEDS):
    """The Sec 10 recipe, seed for seed. The first 3000 reproduce the shipped claim."""
    return tally(n, lambda s: np.random.default_rng(77000 + s), n_seeds)


def path_b(n, gamma, eps, base_seed=0, n_seeds=N_SEEDS):
    """The floor path's mask generation, extracted verbatim from rig.sweep."""
    cfg = RigConfig().with_(seed=base_seed).with_(n_cplx=0, n_int=n)
    return tally(n, lambda s: np.random.default_rng(
        cfg.derive_seed("floor_mask", gamma, eps, s)), n_seeds)


def two_proportion_z(a: dict, b: dict, key="marginal") -> float:
    """Pooled two-proportion z. |z| > ~2.5 across several cells is a real gap."""
    ra, rb = a[f"{key}_rate"], b[f"{key}_rate"]
    na = a["n_seeds"] if key == "marginal" else a["n_seeds"] - a["small"]
    nb = b["n_seeds"] if key == "marginal" else b["n_seeds"] - b["small"]
    pool = (ra * na + rb * nb) / (na + nb)
    se = np.sqrt(pool * (1 - pool) * (1 / na + 1 / nb))
    return float((ra - rb) / se) if se > 0 else float("nan")


CELLS = ((1.0, 0.1), (2.0, 0.1), (2.0, 0.4), (3.0, 0.2))


def run(n_seeds: int = N_SEEDS) -> dict:
    out = {"n_seeds": n_seeds, "p": P, "filling": FILLING,
           "gamma_eps_cells": [list(c) for c in CELLS], "by_n": {}}
    for n in (6, 12):
        rec = {"path_a_sec10": path_a(n, n_seeds),
               "path_b_floor": {f"gamma={g},eps={e}": path_b(n, g, e, n_seeds=n_seeds)
                                for g, e in CELLS}}
        bs = list(rec["path_b_floor"].values())
        for key in ("marginal", "conditional"):
            rates = [b[f"{key}_rate"] for b in bs]
            # Chi-square for homogeneity across the (gamma, eps) cells.
            if key == "marginal":
                k = [b["small"] + b["b1_zero"] for b in bs]; tot = [b["n_seeds"] for b in bs]
            else:
                k = [b["b1_zero"] for b in bs]
                tot = [b["n_seeds"] - b["small"] for b in bs]
            pool = sum(k) / sum(tot)
            chi2 = float(sum((ki - ti * pool) ** 2 / (ti * pool * (1 - pool))
                             for ki, ti in zip(k, tot)))
            rec[f"{key}_across_cells"] = {
                "rates": rates, "spread_pp": float(100 * (max(rates) - min(rates))),
                "chi2": chi2, "dof": len(bs) - 1,
                "homogeneous": bool(chi2 < 12.84)}     # chi2(3) 0.5% upper tail
            rec[f"{key}_a_vs_b_pooled_z"] = [
                two_proportion_z(rec["path_a_sec10"], b, key) for b in bs]
        out["by_n"][str(n)] = rec
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    run()
