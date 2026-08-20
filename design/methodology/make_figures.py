"""Generate the methodology document's data figures as PDFs.

Data comes from figdata/*.json, produced by the runs recorded alongside. Styling
is deliberately quiet: serif to match the document, one accent, no chartjunk.
"""
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
D = json.load(open(HERE/"figdata"/"figures.json"))
G = json.load(open(HERE/"figdata"/"guard.json"))

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["DejaVu Serif"], "font.size": 9,
    "axes.linewidth": .7, "axes.edgecolor": "#444", "axes.labelsize": 9,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 7.6,
    "legend.frameon": False, "figure.dpi": 200,
})
INK, ACC, BAD, OK = "#222222", "#1F4E79", "#B0392C", "#2C6E49"


def fig_window():
    d = D["fit_window"]; k = np.array(d["k"], float); E = np.array(d["E"])
    fig, ax = plt.subplots(figsize=(5.4, 3.1))
    x = 1/k
    ax.axvspan(1/64, x.max()*1.08, color=BAD, alpha=.06)
    xs = np.linspace(0, x.max()*1.08, 200)
    ax.plot(xs, d["full"]["floor"] + d["full"]["c"]*xs, color=BAD, lw=1.5,
            label=f"fit on all $k$  $\\to$ {d['full']['floor']:.3f}")
    ax.plot(xs, d["window"]["floor"] + d["window"]["c"]*xs, color=ACC, lw=1.5,
            label=f"fit on $k\\geq 64$  $\\to$ {d['window']['floor']:.4f}")
    ax.axhline(d["true_floor"], color=OK, ls="--", lw=1.3,
               label=f"true floor $\\varepsilon^2$ = {d['true_floor']:.3f}")
    ax.plot(x, E, "o", color=INK, ms=4.5, zorder=5)
    ax.plot([0], [d["full"]["floor"]], "o", color=BAD, ms=7, zorder=6)
    ax.plot([0], [d["window"]["floor"]], "o", color=ACC, ms=7, zorder=6)
    ax.set_xlim(-0.002, x.max()*1.08); ax.set_ylim(-0.05, max(E)*1.05)
    ax.set_xlabel("$1/k$"); ax.set_ylabel(r"harmonic energy $\|P_h Y\|^2$")
    ax.text(1/64*1.06, max(E)*.93, "contaminated by\nthe $O(k^{-2})$ term",
            color=BAD, fontsize=7.4, va="top")
    ax.legend(loc="upper left", bbox_to_anchor=(.30, 1.02))
    fig.tight_layout(); fig.savefig(HERE/"fig-window.pdf"); plt.close(fig)


def fig_guard():
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 3.0), sharey=True)
    for ax, (name, pts) in zip(axes, G.items()):
        ax.axvspan(1/1.5, 1.5, color=OK, alpha=.10, lw=0)
        ax.axhspan(0.8, 1.25, color="#777", alpha=.10, lw=0)
        misses = []
        for q in pts:
            wrong = not (0.8 <= q["ratio"] <= 1.25)
            passes = 1/1.5 <= q["c_ratio"] <= 1.5
            ax.plot(q["c_ratio"], q["ratio"], "o", ms=3.6,
                    color=BAD if wrong else INK, alpha=.85, zorder=4)
            if wrong and passes:
                misses.append(q)
                ax.plot(q["c_ratio"], q["ratio"], "o", ms=9, mfc="none",
                        mec=BAD, mew=1.6, zorder=6)
        ax.axvline(1.0, color="#bbb", lw=.6, zorder=1)
        ax.axhline(1.0, color="#bbb", lw=.6, zorder=1)
        ax.set_title(name, fontsize=8.5, pad=7)
        ax.set_xlabel(r"$c_{\rm fit}/c_{\rm oracle}$")
        ax.set_xlim(0.45, 1.75); ax.set_xticks([0.5, 0.75, 1.0, 1.25, 1.5])
        # label the worst miss only, placed away from the point
        if misses:
            w = max(misses, key=lambda q: abs(q["ratio"] - 1))
            dy = -34 if w["ratio"] > 1 else 30
            ax.annotate(f"floor {w['ratio']:.2f}$\\times$, gate passes",
                        (w["c_ratio"], w["ratio"]), textcoords="offset points",
                        xytext=(0, dy), ha="center", fontsize=7.2, color=BAD,
                        arrowprops=dict(arrowstyle="-", color=BAD, lw=.7,
                                        shrinkA=0, shrinkB=7))
    axes[0].set_ylabel("floor / oracle"); axes[0].set_ylim(-0.12, 2.05)
    axes[0].text(0.50, 1.92, "grey: floor correct", fontsize=7, color="#666", va="top")
    axes[0].text(0.50, 1.76, "green: $c$ gate passes", fontsize=7, color=OK, va="top")
    fig.tight_layout(); fig.savefig(HERE/"fig-guard.pdf"); plt.close(fig)


def fig_draws():
    r = np.array(D["draws"]["ratios"]); hist = D["draws"]["historical_point_estimates"]
    fig, ax = plt.subplots(figsize=(5.4, 2.5))
    ax.axvline(1.0, color=OK, ls="--", lw=1.3, zorder=1)
    ax.text(1.001, 1.62, "oracle", color=OK, fontsize=7.5)
    ax.plot(r, np.full_like(r, 1.0), "o", color=ACC, ms=5, alpha=.75, zorder=4)
    m, se = r.mean(), r.std(ddof=1)/np.sqrt(len(r))
    ax.errorbar([m], [0.55], xerr=[1.96*se], fmt="s", color=INK, ms=5, capsize=3, zorder=5)
    ax.text(m, 0.30, f"mean {m:.4f}\n$\\pm${1.96*se:.4f} (95\\%)", ha="center", fontsize=7.4)
    for i, (lab, v) in enumerate(hist.items()):
        ax.plot([v], [1.45], "v", color=BAD, ms=6)
        ax.text(v, 1.55, lab, ha="center", fontsize=6.8, color=BAD)
    ax.set_yticks([]); ax.set_ylim(0.1, 1.85)
    ax.set_xlabel("floor / oracle, one point per independent base seed")
    for s in ("left", "right", "top"): ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(HERE/"fig-draws.pdf"); plt.close(fig)


def fig_rho_and_plateau():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.4, 2.7))
    R = D["rho"]; rho = [r["rho"] for r in R]
    b = [100*r["bias"] for r in R]; se = [100*r["se"] for r in R]
    a1.errorbar(rho, b, yerr=se, fmt="o-", color=ACC, ms=4, lw=1.4, capsize=2.5,
                label="residual bias")
    a1.set_xscale("log"); a1.set_xticks(rho); a1.set_xticklabels([str(r) for r in rho])
    a1.set_xlabel(r"$\rho$"); a1.set_ylabel("residual bias (\\%)"); a1.axhline(0, color="#aaa", lw=.6)
    a1b = a1.twinx()
    a1b.plot(rho, [r["short"] for r in R], "s--", color=BAD, ms=3.5, lw=1.1,
             label="unfittable cells")
    a1b.set_ylabel("unfittable cells", color=BAD, fontsize=8)
    a1b.tick_params(axis="y", colors=BAD, labelsize=7.5)
    h1, l1 = a1.get_legend_handles_labels(); h2, l2 = a1b.get_legend_handles_labels()
    a1.legend(h1+h2, l1+l2, loc="upper left")
    a1.set_title("smaller $\\rho$: less bias, less grid reach\n(grid to 4096)", fontsize=8.5)

    P = [q for q in D["plateau"] if q["filling"] == "observed"]
    n = [q["n"] for q in P]; rate = [100*q["rate"] for q in P]
    a2.plot(n, rate, "o-", color=ACC, ms=4, lw=1.5, label=r"\% with $b_1=0$")
    lo = int(np.argmin(rate))
    a2.plot([n[lo]], [rate[lo]], "o", ms=9, mfc="none", mec=BAD, mew=1.6)
    a2.annotate(f"minimum, $n={n[lo]}$", (n[lo], rate[lo]), textcoords="offset points",
                xytext=(-6, 20), fontsize=7.4, color=BAD)
    a2b = a2.twinx()
    a2b.plot(n, [q["mean_b1"] for q in P], "s--", color=OK, ms=3.5, lw=1.1)
    a2b.set_ylabel(r"mean $b_1$", color=OK, fontsize=8)
    a2b.tick_params(axis="y", colors=OK, labelsize=7.5)
    a2.set_xlabel("$n$ (items), edge retention fixed at $0.45$")
    a2.set_ylabel(r"\% of graphs with $b_1=0$")
    a2.set_title("more items eventually destroys the holes", fontsize=8.5)
    fig.tight_layout(); fig.savefig(HERE/"fig-rho-plateau.pdf"); plt.close(fig)


if __name__ == "__main__":
    fig_window(); fig_guard(); fig_draws(); fig_rho_and_plateau()
    for f in sorted(HERE.glob("fig-*.pdf")):
        print(f"  {f.name}  {f.stat().st_size/1024:.0f} KB")
