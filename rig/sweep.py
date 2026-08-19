"""Sweep harness: config enumeration, the §8.5 floor measurement, oracle deviation.

The floor measurement is the load-bearing routine and follows §2.4/§2.6/§7 exactly:
  * the sparsity mask is drawn ONCE per seed and held across the whole k-sweep, so
    P_h -- and therefore the true floor -- is a constant within the fit;
  * the OLS fit is restricted to k >= fit_k_min;
  * the §2.6 preconditions are checked in closed form BEFORE fitting;
  * the floor ships with a bootstrap CI across seeds, never as a point estimate.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

import hodge
from rig import fit, flows, oracle
from rig.config import RigConfig, budget_echo, quick
from rig.emit import emit_assembly
from rig.graph import assemble


def floor_measurement(cfg, gamma: float, eps: float, strict: bool = True,
                      filling: str | None = None, rho: float | None = None) -> dict:
    """§8.5: recover the budget-independent floor and compare it to the eps^2 oracle.

    `filling` defaults to 'observed' -- NOT to cfg.filling. §2.4's characterisation of
    the null and §2.6's fit window were both measured on 'observed'; on 'empty' the
    same graph carries ~10x the harmonic dimension, hence ~10x the variance term, and
    the k>=64 window is nowhere near enough (measured 0.016 against a true 0.090).
    The window is therefore DERIVED per config from c_oracle and the target floor, and
    a grid that cannot support it is flagged rather than silently fitted.
    """
    filling = filling or "observed"
    rho = cfg.rho if rho is None else rho
    n = cfg.n_int
    ks = np.array(cfg.btl.k, dtype=float)
    per_seed_floor, per_seed_c, per_seed_ratio, regimes = [], [], [], []
    req_k, eff_k, insufficient = [], [], False
    # Seeds leave this loop by two routes and BOTH are counted. The CI must not be read
    # as if it came from the full seed budget, so `seed_drop_rate` is the total loss --
    # counting only one route understates it (at n_int=4 that read 0.578 against a true
    # 0.953). n_seeds_used + every drop counter == cfg.seeds, always.
    n_dropped = 0     # masks with b1 = 0: no harmonic direction to inject into
    n_small = 0       # masks too small to carry a decomposition at all

    for s in range(cfg.seeds):
        mrng = np.random.default_rng(cfg.derive_seed("floor_mask", gamma, eps, s))
        mask = flows.sample_sparse_graph(n, cfg.btl.p, mrng)   # ONCE per seed (§2.4)
        if len(mask) < 3:
            n_small += 1
            continue
        tris = hodge.triangles_for_filling(mask, filling)
        D0, D1 = hodge.build_operators(n, mask, tris)
        _, _, Ph = hodge.hodge_projectors(D0, D1)
        try:
            h_unit = flows.harmonic_unit(D0, D1)
        except ValueError:
            n_dropped += 1        # b1 = 0: no harmonic direction on this mask
            continue

        theta = flows.latent_potential(n, cfg.btl, gamma,
                                       np.random.default_rng(cfg.derive_seed("theta", s)))
        latent = flows.misspecified_latent(D0, theta, eps, h_unit)
        pe = 1.0 / (1.0 + np.exp(-latent))

        rep = oracle.regime_report(pe, int(ks.min()), eps, D0 @ theta,
                                   cfg.btl.fit_k_min, strict=strict)
        regimes.append(rep)

        c_or = oracle.c_oracle(Ph, pe)
        need = oracle.required_fit_k_min(c_or, oracle.floor_oracle(eps), rho)
        if np.isfinite(need):
            window = max(cfg.btl.fit_k_min, need)
        else:
            # eps = 0: there is no floor to resolve, so there is no ratio to satisfy --
            # but the O(1/k^2) term still biases the intercept NEGATIVE (the energy decays
            # faster than 1/k, so a 2-parameter line extrapolates below zero). Use the
            # cleanest tail the grid supports so the negative control can honestly cover 0.
            # max(0, ...) rather than [-3]: a 2-element grid passes config validation
            # (it only needs >=1 k at or above fit_k_min), and a bare [-3] would raise
            # IndexError on the negative-control cell after the eps>0 cells had run.
            ks_sorted = sorted(cfg.btl.k)
            window = max(cfg.btl.fit_k_min,
                         float(ks_sorted[max(0, len(ks_sorted) - 3)]))
        usable = [k for k in cfg.btl.k if k >= window]
        if len(usable) < 2:                     # grid cannot support the needed window
            insufficient = True
            ks_sorted = sorted(cfg.btl.k)
            window = float(ks_sorted[max(0, len(ks_sorted) - 2)])
        req_k.append(need)
        eff_k.append(window)

        drng = np.random.default_rng(cfg.derive_seed("draws", gamma, eps, s))
        energies = []
        for k in cfg.btl.k:
            w = drng.binomial(k, np.broadcast_to(pe, (cfg.reps, len(pe))))
            Y = flows.logodds_from_counts(w, k)
            energies.append(float(np.mean(np.einsum("ij,jk,ik->i", Y, Ph, Y))))

        f = fit.fit_floor_c(ks, energies, window)
        gate = oracle.c_oracle_gate(f["c"], c_or)
        per_seed_floor.append(f["floor"])
        per_seed_c.append(f["c"])
        per_seed_ratio.append(gate["c_ratio"])

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


def floor_sweep(cfg, strict: bool = True) -> list:
    """floor vs (eps, gamma). eps is the floor axis; gamma must come out FLAT (§8.5.5)."""
    return [floor_measurement(cfg, g, e, strict=strict)
            for e in cfg.eps for g in cfg.btl.gamma]


def config_record(cfg, gamma=1.0, eps=0.0, k=None, filling=None, with_log=True) -> dict:
    """One assembled config: measured (g,c,h) vs the projector oracle, plus §9 fields."""
    a = assemble(cfg, gamma=gamma, eps=eps, k=k or cfg.btl.k[-1])
    filling = filling or cfg.filling
    meas = a.analyze(filling=filling)
    orc = oracle.projector_split(cfg.n_vertices, a.edges, a.Y_expected, filling)
    zeta, n_obs = hodge.coefficient_of_consistency(cfg.n_vertices, a.directed)
    rec = {
        "gamma": gamma, "eps": eps, "k": a.k, "filling": filling,
        "complex_fraction": cfg.complex_fraction,
        "bridge_mode": cfg.bridge_mode, "mode_II": cfg.mode_II,
        **{f"meas_{k_}": v for k_, v in meas["fractions"].items()},
        **{f"oracle_{k_}": v for k_, v in orc["fractions"].items()},
        **{f"dev_{k_}": v for k_, v in oracle.deviation(meas["fractions"], orc["fractions"]).items()},
        "total_mass": meas["total_mass"], "b1_holes": meas["b1_holes"],
        "oracle_h_energy": orc["energies"]["harmonic"],
        "zeta_hat": zeta, "observed_triples": n_obs,
        "self_checks_pass": meas["self_checks_pass"],
        **a.block_rms(),
        "seed": a.seed, "config_fingerprint": cfg.fingerprint(),
    }
    if with_log:
        lg = emit_assembly(a, criterion=f"g{gamma}_e{eps}_k{a.k}")
        rt = lg.analyze(cfg.n_vertices, filling="empty")
        internal = a.analyze(filling="empty")["fractions"]
        rec.update({
            "roundtrip_exact": lg.exact, "roundtrip_rows": len(lg),
            "roundtrip_residual_max": lg.residual_max,
            "roundtrip_n_collapsed": lg.n_collapsed,
            "roundtrip_n_saturated": lg.n_saturated,
            "roundtrip_max_dev": max(abs(internal[c] - rt["fractions"][c])
                                     for c in ("gradient", "curl", "harmonic")),
            "roundtrip_zeta": rt["zeta_hat"],
        })
    return rec


def adversarial_sweep(cfg, fractions=(0, 3, 5, 7, 9)) -> list:
    """§8.7: the k-independent floor vs complex fraction, at fixed block scale."""
    out = []
    for m in fractions:
        c = cfg.with_(n_cplx=m, eps=(0.0,), btl=cfg.btl)
        r = config_record(c, gamma=1.0, eps=0.0, with_log=False)
        r["systematic_floor_energy"] = r["oracle_h_energy"]
        r["n_cplx"] = m
        out.append(r)
    return out


def bridge_sweep(cfg, Rs=(2, 4, 8, 16, 32, 64, 128)) -> list:
    """§8.6: variance_fresh decays as 1/R, bias_rule adds none, variance_fixed persists."""
    out = []
    for mode in ("variance_fresh", "bias_rule", "variance_fixed"):
        for R in Rs:
            c = cfg.with_(bridge_mode=mode, bridge_R=R)
            a = assemble(c, gamma=1.0, eps=0.0)
            orc = oracle.projector_split(c.n_vertices, a.edges, a.Y_expected, "empty")
            ic = a.blocks.get("ic")
            sub = oracle.projector_split(c.n_vertices, a.edges,
                                         np.array([a.Y[r] if a.edges[r] in set(ic.edges) else 0.0
                                                   for r in range(len(a.edges))]), "empty") if ic else None
            out.append({"bridge_mode": mode, "bridge_R": R,
                        "h_energy_total": orc["energies"]["harmonic"],
                        "h_energy_bridge_only": sub["energies"]["harmonic"] if sub else 0.0,
                        "bridge_rms": ic.rms() if ic else 0.0})
    return out


def _json_safe(o):
    """Replace non-finite floats with null so the output is valid JSON.

    `fit_k_required` is legitimately inf on the eps=0 control (there is no floor to
    resolve), and several fields are NaN when a cell has no usable seeds. json.dumps
    would emit the bare tokens `Infinity`/`NaN`, which are not in the JSON grammar --
    Python reads them back, but jq, JSON.parse, encoding/json and serde_json all
    reject the line, and §9 makes these records the output contract.
    """
    if isinstance(o, dict):
        return {k: _json_safe(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_json_safe(v) for v in o]
    if isinstance(o, (float, np.floating)):
        v = float(o)
        return v if math.isfinite(v) else None
    return o


def run(cfg, out_dir="runs", is_quick=False, figures=True) -> dict:
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    budget = budget_echo(cfg, is_quick)
    bundle = {
        "budget": budget, "config": cfg.echo(),
        "floor": floor_sweep(cfg.with_(n_cplx=0, n_int=max(cfg.n_int, 12)), strict=False),
        "adversarial": adversarial_sweep(cfg),
        "bridge": bridge_sweep(cfg),
        "configs": [config_record(cfg, gamma=g, eps=e, filling=f)
                    for g in cfg.btl.gamma[:2] for e in cfg.eps[:2]
                    for f in ("empty", "observed")],
    }
    for name, rows in bundle.items():
        if isinstance(rows, list):
            with open(out / f"{name}.jsonl", "w") as fh:
                for r in rows:
                    fh.write(json.dumps(_json_safe({**r, "budget": budget}),
                                         default=float, allow_nan=False) + "\n")
    (out / "manifest.json").write_text(json.dumps(
        _json_safe({"budget": budget, "config": cfg.echo()}),
        indent=2, default=float, allow_nan=False))
    if figures:
        from rig import report
        # The floor sweep runs on the pure-null pool; the figures must describe it.
        report.build(bundle, cfg.with_(n_cplx=0, n_int=max(cfg.n_int, 12)), out_dir)
    return bundle


def main(argv=None):
    ap = argparse.ArgumentParser(description="Synthetic calibration rig sweep (spec §9)")
    ap.add_argument("--out", default="runs")
    ap.add_argument("--quick", action="store_true", help="fewer seeds, shorter k grid")
    ap.add_argument("--seeds", type=int, default=None)
    ap.add_argument("--no-figures", action="store_true")
    a = ap.parse_args(argv)
    cfg = RigConfig().validate()
    if a.seeds:
        cfg = cfg.with_(seeds=a.seeds)
    if a.quick:
        cfg = quick(cfg)
    b = run(cfg, a.out, a.quick, figures=not a.no_figures)
    print(f"wrote {a.out}/  budget={b['budget']}")
    for r in b["floor"]:
        # grid_insufficient says the fit fell back below its derived window, i.e. do not
        # trust this number. It has to appear on the default human-facing surface, not
        # only in the JSONL.
        flags = []
        if r["grid_insufficient"]:
            flags.append(f"GRID SHORT (needed k>={r['fit_k_required']:.0f})")
        if r["seed_drop_rate"] > 0:
            flags.append(f"{r['seed_drop_rate']:.0%} seeds dropped")
        print(f"  eps={r['eps']:<4} gamma={r['gamma']:<4} floor={r['floor_mean']:.5f} "
              f"CI[{r['floor_ci_lo']:.5f},{r['floor_ci_hi']:.5f}] oracle={r['floor_oracle']:.5f} "
              f"covers={r['ci_covers_oracle']} c_ratio={r['c_ratio_median']:.2f}"
              + (f"  <- {'; '.join(flags)}" if flags else ""))
    return b


if __name__ == "__main__":
    main()
