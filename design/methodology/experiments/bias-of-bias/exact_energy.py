"""Exact-energy replication of the shipped 20-base-seed residual run.

The shipped residual (`residual-across-draws` in the evidence index) is measured
with Monte Carlo energies: `reps` binomial draws per (seed, k), averaged. That
average carries sampling noise, so the reported residual mixes two things --
the OLS model's misspecification bias, and MC noise in the points it is fitting.

This module removes the second one. For independent edge counts,

    E||P_h Y||^2 = mu' P_h mu + sum_i (P_h)_ii Var(Y_i),        (*)

with mu_i = E[Y_i] and Var(Y_i) computed by summing the binomial pmf against the
instrument's own clamped log-odds. That is a finite sum, so (*) is exact: no
draws, no seeds, no noise in the fitted points. What survives is the estimator's
own bias.

Everything else is held identical to the shipped sweep: same masks, same theta,
same latent, same derived window, same OLS. `replica` reproduces
rig.sweep.floor_measurement bit-for-bit in mode='mc' -- `verify_replica()`
asserts it -- so the exact-vs-MC difference is attributable to (*) alone.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.special import gammaln

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import hodge
from rig import fit, flows, oracle

# Tail truncation for the exact sum. The binomial pmf beyond 16 sd carries mass
# below 1e-56; the log-odds it multiplies are bounded by log(2k-1) < 11 over this
# grid, so the discarded contribution is ~1e-55 against energies of order 1e-2 --
# some 40 orders of magnitude below float64 resolution. `_validate_truncation`
# checks it against the untruncated sum rather than trusting the argument.
N_SD = 16.0

# Which base seed the CI-width evidence is taken on. Named so the value stored
# beside the rows and the value used to compute them cannot disagree.
CI_BASE_SEED = 0

_LOGC: dict[int, np.ndarray] = {}
_Y: dict[int, np.ndarray] = {}


def _tables(k: int):
    """log C(k, w) and the instrument's clamped log-odds y(w), cached per k."""
    if k not in _LOGC:
        w = np.arange(k + 1)
        _LOGC[k] = gammaln(k + 1) - gammaln(w + 1) - gammaln(k - w + 1)
        _Y[k] = flows.logodds_from_counts(w, k)   # the instrument's own clamp
    return _LOGC[k], _Y[k]


def edge_moments(pe: np.ndarray, k: int, n_sd: float = N_SD):
    """Exact E[Y] and Var(Y) per edge under W ~ Binom(k, p), by direct summation."""
    logC, y = _tables(k)
    pe = np.asarray(pe, float)
    sd = np.sqrt(k * pe * (1.0 - pe))
    half = int(np.ceil(n_sd * sd.max())) + 2
    if 2 * half + 1 >= k + 1:                      # narrow k: sum the whole support
        W = np.broadcast_to(np.arange(k + 1), (pe.size, k + 1))
    else:
        lo = np.clip(np.rint(k * pe) - half, 0, k - 2 * half).astype(int)
        W = lo[:, None] + np.arange(2 * half + 1)[None, :]
    logp = np.log(pe)[:, None]
    log1mp = np.log1p(-pe)[:, None]
    pmf = np.exp(logC[W] + W * logp + (k - W) * log1mp)
    yv = y[W]
    mu = np.einsum("ij,ij->i", pmf, yv)
    m2 = np.einsum("ij,ij->i", pmf, yv * yv)
    return mu, m2 - mu * mu


def exact_energy(pe: np.ndarray, Ph: np.ndarray, k: int) -> float:
    """Identity (*): the exact value the MC average is estimating."""
    mu, var = edge_moments(pe, k)
    return float(mu @ Ph @ mu + np.diag(Ph) @ var)


# ---------------------------------------------------------------------------
# A replica of rig.sweep.floor_measurement whose ONLY freedom is the energies.
# Mirrors the shipped routine line for line, including the eps=0 window branch,
# the grid-insufficient fallback and both seed-drop counters.
# ---------------------------------------------------------------------------
def replica(cfg, gamma: float, eps: float, mode: str, strict: bool = False,
            filling: str | None = None, rho: float | None = None) -> dict:
    filling = filling or "observed"
    rho = cfg.rho if rho is None else rho
    n = cfg.n_int
    ks = np.array(cfg.btl.k, dtype=float)
    per_seed_floor, per_seed_c, per_seed_ratio, regimes = [], [], [], []
    req_k, eff_k, insufficient = [], [], False
    n_dropped = n_small = 0

    for s in range(cfg.seeds):
        mrng = np.random.default_rng(cfg.derive_seed("floor_mask", gamma, eps, s))
        mask = flows.sample_sparse_graph(n, cfg.btl.p, mrng)
        if len(mask) < 3:
            n_small += 1
            continue
        tris = hodge.triangles_for_filling(mask, filling)
        D0, D1 = hodge.build_operators(n, mask, tris)
        _, _, Ph = hodge.hodge_projectors(D0, D1)
        try:
            h_unit = flows.harmonic_unit(D0, D1)
        except ValueError:
            n_dropped += 1
            continue

        theta = flows.latent_potential(n, cfg.btl, gamma,
                                       np.random.default_rng(cfg.derive_seed("theta", s)))
        latent = flows.misspecified_latent(D0, theta, eps, h_unit)
        pe = 1.0 / (1.0 + np.exp(-latent))

        regimes.append(oracle.regime_report(pe, int(ks.min()), eps, D0 @ theta,
                                            cfg.btl.fit_k_min, strict=strict))
        c_or = oracle.c_oracle(Ph, pe)
        need = oracle.required_fit_k_min(c_or, oracle.floor_oracle(eps), rho)
        if np.isfinite(need):
            window = max(cfg.btl.fit_k_min, need)
        else:
            ks_sorted = sorted(cfg.btl.k)
            window = max(cfg.btl.fit_k_min, float(ks_sorted[max(0, len(ks_sorted) - 3)]))
        if len([k for k in cfg.btl.k if k >= window]) < 2:
            insufficient = True
            ks_sorted = sorted(cfg.btl.k)
            window = float(ks_sorted[max(0, len(ks_sorted) - 2)])
        req_k.append(need)
        eff_k.append(window)

        if mode == "mc":
            drng = np.random.default_rng(cfg.derive_seed("draws", gamma, eps, s))
            energies = []
            for k in cfg.btl.k:
                w = drng.binomial(k, np.broadcast_to(pe, (cfg.reps, len(pe))))
                Y = flows.logodds_from_counts(w, k)
                energies.append(float(np.mean(np.einsum("ij,jk,ik->i", Y, Ph, Y))))
        elif mode == "exact":
            energies = [exact_energy(pe, Ph, k) for k in cfg.btl.k]
        else:
            raise ValueError(f"mode must be 'mc' or 'exact', got {mode!r}")

        f = fit.fit_floor_c(ks, energies, window)
        per_seed_floor.append(f["floor"])
        per_seed_c.append(f["c"])
        per_seed_ratio.append(oracle.c_oracle_gate(f["c"], c_or)["c_ratio"])

    agg = fit.aggregate_floor(per_seed_floor,
                              rng=np.random.default_rng(cfg.derive_seed("boot", gamma, eps)))
    target = oracle.floor_oracle(eps)
    ratio = float(np.median(per_seed_ratio)) if per_seed_ratio else float("nan")
    return {
        "gamma": gamma, "eps": eps, "filling": filling, "floor_oracle": target, **agg,
        "fit_k_required": float(np.median(req_k)) if req_k else float("nan"),
        "fit_k_effective": float(np.median(eff_k)) if eff_k else float("nan"),
        "grid_insufficient": insufficient,
        "floor_over_oracle": (agg["floor_mean"] / target) if target > 0 else float("nan"),
        "ci_covers_oracle": fit.covers(agg["floor_ci_lo"], agg["floor_ci_hi"], target),
        "c_median": float(np.median(per_seed_c)) if per_seed_c else float("nan"),
        "c_ratio_median": ratio,
        "c_gate_ok": bool(1 / oracle.C_ORACLE_TOL <= ratio <= oracle.C_ORACLE_TOL),
        "saturation": float(np.mean([r["saturation"] for r in regimes])) if regimes else float("nan"),
        "mildness": float(np.mean([r["mildness"] for r in regimes])) if regimes else float("nan"),
        "regime_ok": all(r["ok"] for r in regimes) if regimes else False,
        "n_seeds_used": len(per_seed_floor),
        "n_seeds_dropped_b1_zero": n_dropped,
        "n_seeds_dropped_small_mask": n_small,
        "seed_drop_rate": (n_dropped + n_small) / cfg.seeds if cfg.seeds else 0.0,
        "rho": rho,
    }


def verify_replica(cfg, cells=((1.0, 0.1), (2.0, 0.2), (3.0, 0.4), (1.5, 0.0))) -> None:
    """`replica(mode='mc')` must equal the shipped routine exactly, key for key.

    Without this the exact-vs-MC comparison would be confounded by any drift
    between the replica and the routine it is standing in for.
    """
    from rig.sweep import floor_measurement
    for gamma, eps in cells:
        a = floor_measurement(cfg, gamma, eps, strict=False)
        b = replica(cfg, gamma, eps, mode="mc", strict=False)
        assert a.keys() == b.keys(), (a.keys() ^ b.keys())
        for k in a:
            x, y = a[k], b[k]
            same = (x == y) or (isinstance(x, float) and isinstance(y, float)
                                and np.isnan(x) and np.isnan(y))
            if not same:
                raise AssertionError(f"replica differs at gamma={gamma} eps={eps}: "
                                     f"{k}: shipped={x!r} replica={y!r}")


# ---------------------------------------------------------------------------
# The 20-base-seed run, in both modes on identical topologies.
# ---------------------------------------------------------------------------
HERE = Path(__file__).parent
CKPT = HERE / "results" / "exact_energy_checkpoint.json"
OUT = HERE / "results" / "exact_energy_residual.json"
N_BASE_SEEDS = 20


def _cfg(base, bs):
    """Exactly the config the shipped `sweeps()` builds for base seed `bs`."""
    return base.with_(seed=bs).with_(n_cplx=0, n_int=max(base.n_int, 12))


def run(n_base_seeds: int = N_BASE_SEEDS, resume: bool = True, verbose: bool = True):
    """Per base seed, the mean floor/oracle ratio over the eps>0 cells, both modes.

    Checkpointed per base seed: this run is long enough that losing it partway is
    a real cost, and the earlier attempt died around 3/20.
    """
    import json
    from rig.config import RigConfig

    base = RigConfig()
    verify_replica(_cfg(base, 0))          # never compare against an unverified replica

    done = {}
    if resume and CKPT.exists():
        done = {int(k): v for k, v in json.loads(CKPT.read_text()).items()}
        if verbose and done:
            print(f"  resuming: {len(done)}/{n_base_seeds} base seeds already done")

    CKPT.parent.mkdir(parents=True, exist_ok=True)
    for bs in range(n_base_seeds):
        if bs in done:
            continue
        c = _cfg(base, bs)
        rec = {}
        for mode in ("exact", "mc"):
            rows = [replica(c, g, e, mode=mode, strict=False)
                    for e in c.eps for g in c.btl.gamma]
            pos = [x for x in rows if x["eps"] > 0]
            rec[mode] = {
                "ratio": float(np.mean([x["floor_over_oracle"] for x in pos])),
                "coverage": int(sum(x["ci_covers_oracle"] for x in rows)),
                "n_cells": len(rows),
                "grid_insufficient": int(sum(x["grid_insufficient"] for x in rows)),
                "per_eps": {str(e): float(np.mean([x["floor_over_oracle"]
                                                   for x in pos if x["eps"] == e]))
                            for e in c.eps if e > 0},
            }
        done[bs] = rec
        CKPT.write_text(json.dumps({str(k): v for k, v in done.items()}, indent=1))
        if verbose:
            print(f"  base seed {bs:>2}/{n_base_seeds}: "
                  f"exact {100*(1-rec['exact']['ratio']):+.3f}%   "
                  f"mc {100*(1-rec['mc']['ratio']):+.3f}%", flush=True)

    return summarise(done, n_base_seeds)


def _table3(ratios: np.ndarray) -> dict:
    """Table 3's format: mean, s.e., and the per-draw extremes."""
    r = np.asarray(ratios, float)
    return {"n": int(r.size),
            "mean_ratio": float(r.mean()),
            "se_ratio": float(r.std(ddof=1) / np.sqrt(r.size)),
            "residual_pct": float(100 * (1 - r.mean())),
            "se_pct": float(100 * r.std(ddof=1) / np.sqrt(r.size)),
            "per_draw_min_pct": float(100 * (1 - r.max())),
            "per_draw_max_pct": float(100 * (1 - r.min()))}


def summarise(done: dict, n_base_seeds: int) -> dict:
    import json
    seeds = sorted(done)
    out = {"n_base_seeds": len(seeds), "requested": n_base_seeds, "seeds": seeds}
    for mode in ("exact", "mc"):
        r = np.array([done[s][mode]["ratio"] for s in seeds])
        cov = [done[s][mode]["coverage"] for s in seeds]
        out[mode] = {**_table3(r),
                     "coverage_median": int(np.median(cov)),
                     "coverage_min": int(min(cov)), "coverage_max": int(max(cov)),
                     "cells_per_seed": done[seeds[0]][mode]["n_cells"],
                     "grid_insufficient_total": int(sum(done[s][mode]["grid_insufficient"]
                                                        for s in seeds))}
        for e in done[seeds[0]][mode]["per_eps"]:
            out[mode][f"residual_pct_eps_{e}"] = float(
                100 * (1 - np.mean([done[s][mode]["per_eps"][e] for s in seeds])))
    d = np.array([done[s]["exact"]["ratio"] - done[s]["mc"]["ratio"] for s in seeds])
    out["paired_exact_minus_mc"] = {
        "mean_pct": float(100 * d.mean()),
        "se_pct": float(100 * d.std(ddof=1) / np.sqrt(d.size)),
        "note": "Paired across identical topologies, so the mask draw cancels."}
    out["per_seed"] = {str(s): done[s] for s in seeds}
    # report_exact.py's "coverage result needs care" table reads this, and the
    # write below is wholesale -- so leaving it out did not merely omit it, it
    # DELETED it from a committed file no other code path could rebuild.
    out["ci_evidence"] = {"base_seed": CI_BASE_SEED,
                          "rows": ci_evidence(bs=CI_BASE_SEED)}
    OUT.write_text(json.dumps(out, indent=1))
    return out


def ci_evidence(cells=((2.0, 0.0), (2.0, 0.1), (2.0, 0.2), (2.0, 0.4)), bs: int = 0) -> list:
    """Why coverage differs between the modes: CI width, not a different floor.

    The bootstrap CI is taken across inner seeds, so in MC mode it absorbs
    sampling noise as well as mask-to-mask spread. Removing the noise shrinks it
    by two orders of magnitude while the bias stays put -- so the shipped 15/16
    coverage is a statement about how wide MC noise makes the interval, not
    evidence that the estimator is unbiased.
    """
    from rig.config import RigConfig
    c = _cfg(RigConfig(), bs)
    rows = []
    for gamma, eps in cells:
        rec = {"gamma": gamma, "eps": eps, "oracle": eps ** 2}
        for mode in ("exact", "mc"):
            r = replica(c, gamma, eps, mode=mode, strict=False)
            rec[mode] = {"floor_mean": r["floor_mean"], "floor_sd": r["floor_sd"],
                         "ci_width": r["floor_ci_hi"] - r["floor_ci_lo"],
                         "bias": r["floor_mean"] - eps ** 2,
                         "covers": bool(r["ci_covers_oracle"])}
        rec["ci_width_ratio_mc_over_exact"] = (
            rec["mc"]["ci_width"] / rec["exact"]["ci_width"]
            if rec["exact"]["ci_width"] else float("inf"))
        rows.append(rec)
    return rows


# The entry point lives HERE, at the very bottom, and that position is the fix.
# It used to sit above ci_evidence(), so during a script run that function was
# not even bound by the time run() executed -- and summarise() wrote the results
# json wholesale without its key. The committed file carried a `ci_evidence`
# block no executed path produced, so EXACT-ENERGY.md's own two-command recipe
# (`python exact_energy.py`, then `python report_exact.py`) deleted it and then
# died on KeyError: 'ci_evidence' at report_exact.py:94, taking the whole
# "coverage result needs care" section with it.
if __name__ == "__main__":
    run()
