"""Tables and figures (spec §9).

Every figure carries the run budget in its caption, because a number without the
budget that produced it cannot be read (§3, §9). The floor is never plotted as a
point: it is plotted with its CI, against the eps^2 oracle.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import hodge
from rig import flows, oracle
from rig.config import budget_echo

_C = {"eps": "#1f4e79", "oracle": "#c0392b", "gamma": "#7d3c98", "band": "#a9c6e8"}


def _fig(title, budget, xlabel, ylabel, figsize=(7.2, 4.4)):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_title(title, fontsize=11, pad=12)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.grid(alpha=0.25, linewidth=0.6)
    fig.text(0.5, 0.005,
             f"seeds={budget['seeds']} reps={budget['reps']} k={budget['k_grid']} "
             f"fit_k_min={budget['fit_k_min']} quick={budget['quick']}",
             ha="center", fontsize=6.5, color="#555")
    return fig, ax


def fig_floor_vs_eps(rows, budget, out):
    """THE §8.5 figure: fitted floor vs eps, with CI band and the eps^2 oracle."""
    fig, ax = _fig("Recovered floor vs misspecification (§8.5)\n"
                   "eps is the floor axis; eps=0 is the negative control",
                   budget, "eps", "budget-independent floor")
    by = {}
    for r in rows:
        by.setdefault(r["eps"], []).append(r)
    e = sorted(by)
    mean = [np.mean([x["floor_mean"] for x in by[v]]) for v in e]
    lo = [np.mean([x["floor_ci_lo"] for x in by[v]]) for v in e]
    hi = [np.mean([x["floor_ci_hi"] for x in by[v]]) for v in e]
    grid = np.linspace(0, max(e), 200)
    ax.plot(grid, grid ** 2, "--", color=_C["oracle"], lw=1.6, label="oracle  floor = eps²")
    ax.fill_between(e, lo, hi, color=_C["band"], alpha=0.55, label="95% CI (bootstrap over seeds)")
    ax.plot(e, mean, "o-", color=_C["eps"], lw=1.8, ms=5, label="fitted floor")
    ax.axhline(0, color="#888", lw=0.8)
    ax.scatter([0], [mean[0]], s=110, facecolors="none", edgecolors=_C["oracle"],
               lw=1.6, zorder=5, label="negative control (CI must cover 0)")
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(out, dpi=150); plt.close(fig)
    return out


def fig_floor_vs_gamma(rows, budget, out):
    """Secondary axis: the floor must come out FLAT in gamma (§8.5.5)."""
    fig, ax = _fig("Recovered floor vs θ-asymmetry γ (§8.5.5)\n"
                   "γ shapes c and the O(1/k²) bias, never the floor — this must be flat",
                   budget, "γ  (1.0 = symmetric)", "budget-independent floor")
    by = {}
    for r in rows:
        by.setdefault(r["eps"], {}).setdefault(r["gamma"], []).append(r["floor_mean"])
    for eps in sorted(by):
        g = sorted(by[eps])
        v = [np.mean(by[eps][x]) for x in g]
        ax.plot(g, v, "o-", lw=1.6, ms=4, label=f"eps={eps}  (oracle {eps**2:.3f})")
        ax.axhline(eps ** 2, ls=":", lw=0.9, color="#999")
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(out, dpi=150); plt.close(fig)
    return out


def fig_null_decay(cfg, budget, out, eps_values=(0.0, 0.3)):
    """Harmonic energy vs k, one series per γ: the c/k decay onto the eps² floor."""
    fig, ax = _fig("Null decay: harmonic energy vs k (§2.4, §8.5)\n"
                   "the c/k term decays; what remains is the floor",
                   budget, "k  (comparisons per edge)", "harmonic energy  ‖P_h·Y‖²")
    n = cfg.n_int
    mask = flows.sample_sparse_graph(n, cfg.btl.p, np.random.default_rng(cfg.derive_seed("figmask")))
    D0, D1 = hodge.build_operators(n, mask, hodge.triangles_for_filling(mask, "observed"))
    _, _, Ph = hodge.hodge_projectors(D0, D1)
    hu = flows.harmonic_unit(D0, D1)
    for eps in eps_values:
        for gi, gamma in enumerate(cfg.btl.gamma):
            pe = 1 / (1 + np.exp(-flows.misspecified_latent(D0, flows.theta_gamma(
                n, cfg.btl.beta, gamma), eps, hu)))
            E = []
            for k in cfg.btl.k:
                rg = np.random.default_rng(cfg.derive_seed("fig", eps, gamma, k))
                w = rg.binomial(k, np.broadcast_to(pe, (128, len(pe))))
                Y = flows.logodds_from_counts(w, k)
                E.append(float(np.mean(np.einsum("ij,jk,ik->i", Y, Ph, Y))))
            ax.plot(cfg.btl.k, E, marker="o", ms=3, lw=1.3, alpha=0.85,
                    color=plt.cm.viridis(gi / max(len(cfg.btl.gamma) - 1, 1)),
                    ls="-" if eps else "--",
                    label=f"eps={eps} γ={gamma}")
        if eps:
            ax.axhline(eps ** 2, color=_C["oracle"], ls=":", lw=1.2)
            ax.text(cfg.btl.k[-1], eps ** 2, f"  eps²={eps**2:.3f}",
                    color=_C["oracle"], fontsize=7, va="center")
    ax.set_xscale("log", base=2); ax.set_yscale("log")
    ax.legend(fontsize=6.5, frameon=False, ncol=2)
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(out, dpi=150); plt.close(fig)
    return out


def fig_adversarial(rows, budget, out):
    """§8.7: the systematic floor vs complex fraction, stated on the floor."""
    fig, ax = _fig("Systematic floor vs adversarial proportion (§8.7)\n"
                   "claim is on the k-independent floor, not the raw harmonic fraction",
                   budget, "complex fraction  m/(n+m)", "harmonic energy (k-independent)")
    x = [r["complex_fraction"] for r in rows]
    ax.plot(x, [r["systematic_floor_energy"] for r in rows], "o-",
            color=_C["eps"], lw=1.8, ms=5, label="systematic floor (C–C)")
    ax2 = ax.twinx()
    ax2.plot(x, [r["meas_harmonic"] for r in rows], "s--", color="#999", lw=1.2, ms=4,
             label="raw harmonic fraction (confounded, §5.7)")
    ax2.set_ylabel("harmonic fraction", color="#999", fontsize=9)
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=8, frameon=False, loc="upper left")
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(out, dpi=150); plt.close(fig)
    return out


def fig_bridge(rows, budget, out):
    """§8.6: the three bridge behaviours as reference lines."""
    fig, ax = _fig("Bridge-mode reference lines (§8.6, §5.3)\n"
                   "thrash decays, surrogate adds nothing, stable bias persists",
                   budget, "R  (comparisons per bridge pair)", "harmonic energy from the bridge")
    style = {"variance_fresh": ("o-", "#c0392b", "variance_fresh — judge thrashes (decays 1/R)"),
             "bias_rule": ("s-", "#1f4e79", "bias_rule — judge fabricates an order (no harmonic)"),
             "variance_fixed": ("^-", "#7d3c98", "variance_fixed — stable bias (persists)")}
    by = {}
    for r in rows:
        by.setdefault(r["bridge_mode"], []).append((r["bridge_R"], r["h_energy_bridge_only"]))
    for mode, pts in by.items():
        pts.sort()
        m, c, lab = style[mode]
        ax.plot([p[0] for p in pts], [max(p[1], 1e-12) for p in pts], m, color=c,
                lw=1.6, ms=4, label=lab)
    ax.set_xscale("log", base=2); ax.set_yscale("log")
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(out, dpi=150); plt.close(fig)
    return out


def fig_zeta_vs_harmonic(rows, budget, out):
    """§8.8: where ζ and the harmonic certificate disagree."""
    fig, ax = _fig("ζ vs harmonic: the divergence region (§8.8)\n"
                   "ζ is a triad statistic; it cannot see harmonic where triangles are unfilled",
                   budget, "harmonic fraction (certificate)", "ζ  (Pokharel baseline)")
    h = [r["meas_harmonic"] for r in rows]
    z = [r["zeta_hat"] for r in rows]
    ax.scatter(h, z, s=44, color=_C["eps"], alpha=0.8, edgecolors="white", lw=0.6)
    ax.axhline(1.0, color=_C["oracle"], ls="--", lw=1.2)
    ax.text(0.02, 1.005, "ζ = 1  “perfectly consistent”", color=_C["oracle"], fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(out, dpi=150); plt.close(fig)
    return out


def floor_table(rows) -> str:
    hdr = (f"{'eps':>5} {'γ':>5} {'floor':>10} {'95% CI':>21} {'oracle':>8} "
           f"{'ratio':>6} {'covers':>7} {'c_fit/c_or':>11} {'sat':>6}")
    out = [hdr, "-" * len(hdr)]
    for r in sorted(rows, key=lambda x: (x["eps"], x["gamma"])):
        ratio = r["floor_over_oracle"]
        ci = "[{:.5f}, {:.5f}]".format(r["floor_ci_lo"], r["floor_ci_hi"])
        ratio_s = "  n/a" if ratio != ratio else "{:.2f}".format(ratio)
        out.append(
            f"{r['eps']:>5} {r['gamma']:>5} {r['floor_mean']:>10.5f} {ci:>21} "
            f"{r['floor_oracle']:>8.4f} {ratio_s:>6} {str(r['ci_covers_oracle']):>7} "
            f"{r['c_ratio_median']:>11.2f} {r['saturation']:>6.3f}")
    return "\n".join(out)


def build(bundle, cfg, out_dir="runs") -> list:
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    b = bundle["budget"]
    figs = [
        fig_floor_vs_eps(bundle["floor"], b, out / "floor_vs_eps.png"),
        fig_floor_vs_gamma(bundle["floor"], b, out / "floor_vs_gamma.png"),
        fig_null_decay(cfg, b, out / "null_decay.png"),
        fig_adversarial(bundle["adversarial"], b, out / "adversarial.png"),
        fig_bridge(bundle["bridge"], b, out / "bridge_modes.png"),
        fig_zeta_vs_harmonic(bundle["configs"], b, out / "zeta_vs_harmonic.png"),
    ]
    (out / "floor_table.txt").write_text(floor_table(bundle["floor"]) + "\n")
    return figs
