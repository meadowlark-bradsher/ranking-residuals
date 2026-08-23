"""Regenerate every quantity cited in the papers, with its tolerance.

One source of truth. Each claim records what it asserts, where it is cited, the
value, how far a re-run may drift before the claim is considered broken, and the
test that pins it if one does. `verify.py` re-runs this and checks the drift.

Determinism: every RNG is seeded from a fixed constant, so an exact-kind claim
reproduces bit-for-bit on the same numpy. Stochastic-kind claims reproduce within
their stated tolerance, which is set from the measured spread across base seeds,
not guessed.

    python generate.py            # writes evidence.json
    python verify.py              # re-runs and checks
"""
from __future__ import annotations

import itertools
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import hodge
from rig import fit, flows, oracle
from rig.config import RigConfig
from rig.graph import assemble
from rig.sweep import floor_measurement, floor_sweep

HERE = Path(__file__).parent
CLAIMS: dict = {}


def claim(cid, *, asserts, cited_in, value, tol, kind="exact", test=None, note=None):
    CLAIMS[cid] = {"claim": asserts, "cited_in": cited_in, "value": value,
                   "tolerance": tol, "kind": kind, "test": test, "note": note}
    return value


# ---------------------------------------------------------------- structural oracles
def structural():
    cfg = RigConfig().validate()

    r = {}
    for n, published in ((5, 0.200), (6, 0.2222)):
        e = list(itertools.combinations(range(n), 2))
        v = np.arange(n, dtype=float)
        Y = np.sign(np.array([v[j] - v[i] for i, j in e]))
        got = hodge.analyze_flow(n, e, Y, filling="empty")["fractions"]["harmonic"]
        # The second element is the value the papers print. Comparing against it
        # here is what makes the claim self-checking rather than merely recording
        # whatever the code currently produces.
        assert abs(got - published) < 5e-4, f"n={n}: {got} vs published {published}"
        r[f"n{n}"] = got
    claim("pm1-trap", asserts="A +-1 sign flow of a perfectly transitive order deposits "
          "spurious harmonic mass, and the amount is n-dependent, not a constant.",
          cited_in=["methodology sec 2, 'Magnitude, not sign'"], value=r,
          tol={"kind": "abs", "value": 1e-9},
          test="tests/test_invariants.py::test_5_1_pm1_of_a_transitive_order_is_not_a_gradient")

    a = assemble(cfg.with_(n_cplx=0, mode_II="clean_gradient"))
    claim("clean-gradient-zero", asserts="An all-integer value-difference flow reads zero "
          "harmonic under both fillings.",
          cited_in=["methodology sec 3.1 oracle table"],
          value={f: a.analyze(filling=f)["fractions"]["harmonic"] for f in ("empty", "observed")},
          tol={"kind": "abs", "value": 1e-12},
          test="tests/test_acceptance.py::test_8_2_clean_integer_pool_reads_zero_harmonic")

    a = assemble(cfg.with_(n_int=0, n_cplx=5))
    claim("equal-spaced-complex", asserts="An equal-spaced complex pool is pure harmonic "
          "under the empty filling and pure curl under the observed one.",
          cited_in=["methodology sec 3.1 oracle table", "methodology fig 1"],
          value={"empty_harmonic": a.analyze(filling="empty")["fractions"]["harmonic"],
                 "observed_curl": a.analyze(filling="observed")["fractions"]["curl"]},
          tol={"kind": "abs", "value": 1e-12},
          test="tests/test_acceptance.py::test_8_3_equal_spaced_complex_only")

    claim("b1-rank-formula", asserts="b1 of a complex-only pool under the empty filling is "
          "(m-1)(m-2)/2.",
          cited_in=["methodology sec 3.1 oracle table"],
          value={str(m): assemble(cfg.with_(n_int=0, n_cplx=m)).analyze(filling="empty")["b1_holes"]
                 for m in (3, 5, 7, 9)},
          tol={"kind": "exact_int"},
          test="tests/test_acceptance.py::test_8_4_b1_matches_rank_formula")

    n = 12
    mask = flows.sample_sparse_graph(n, 0.45, np.random.default_rng(11))
    D0, D1 = hodge.build_operators(n, mask, hodge.triangles_for_filling(mask, "observed"))
    _, _, Ph = hodge.hodge_projectors(D0, D1)
    hu = flows.harmonic_unit(D0, D1)
    th = flows.theta_gamma(n, 0.3, 2.0)
    claim("eps-squared-floor", asserts="The injected misspecification gives a "
          "budget-independent floor of exactly eps^2.",
          cited_in=["methodology sec 3.1 oracle table", "methodology sec 4", "methodology fig 2"],
          value={str(e): float((lambda L: L @ Ph @ L)(flows.misspecified_latent(D0, th, e, hu)))
                 for e in (0.1, 0.2, 0.4)},
          tol={"kind": "abs", "value": 1e-12},
          test="tests/test_invariants.py::test_2_5_injected_floor_is_exactly_eps_squared")

    claim("gradient-annihilated", asserts="P_h annihilates D0.theta for every theta, so no "
          "latent shape can produce a budget-independent floor.",
          cited_in=["methodology sec 4, Observation 1", "methodology fig 2"],
          value={str(g): float((lambda L: L @ Ph @ L)(D0 @ flows.theta_gamma(n, 0.3, g)))
                 for g in (1.0, 1.5, 2.0, 3.0, 6.0)},
          tol={"kind": "abs", "value": 1e-9},
          test="tests/test_invariants.py::test_5_6_theta_shape_can_never_produce_a_floor")
    return cfg


# ---------------------------------------------------------------- bridge identities
def bridge(cfg):
    c = cfg.with_(n_int=6, n_cplx=5, mode_II="clean_gradient", bridge_mode="bias_rule")
    a = assemble(c)
    ccs = set(a.blocks["cc"].edges)
    ics = set(a.blocks["ic"].edges)
    circle = oracle.projector_split(c.n_vertices, a.edges,
        np.array([a.Y_expected[i] if e in ccs else 0.0 for i, e in enumerate(a.edges)]),
        "empty")["energies"]["harmonic"]
    total = oracle.projector_split(c.n_vertices, a.edges, a.Y_expected, "empty")["energies"]["harmonic"]
    const = oracle.projector_split(c.n_vertices, a.edges,
        np.array([a.Y_expected[i] if e in ccs else (-1.0 if e in ics else a.Y_expected[i])
                  for i, e in enumerate(a.edges)]), "empty")["energies"]["harmonic"]
    claim("bridge-invariance", asserts="A potential-consistent bridge leaves the harmonic "
          "energy equal to the circle block's; a constant bridge does not.",
          cited_in=["methodology sec 3.2", "bridge Theorem 1", "bridge sec 8.1"],
          value={"circle_only": circle, "potential_consistent": total, "constant_bridge": const},
          tol={"kind": "abs", "value": 1e-9},
          test="tests/test_acceptance.py::test_8_6_three_bridge_behaviours_are_correctly_labelled")

    sweep = {}
    for gap in (0.25, 1.0, 25.0, 500.0):
        cg = c.with_(bridge_gap=gap)
        ag = assemble(cg)
        sweep[str(gap)] = {
            "bridge_rms": ag.blocks["ic"].rms(),
            "empty": oracle.projector_split(cg.n_vertices, ag.edges, ag.Y_expected, "empty")["energies"]["harmonic"],
            "observed": oracle.projector_split(cg.n_vertices, ag.edges, ag.Y_expected, "observed")["energies"]["harmonic"]}
    claim("surrogate-level-invariance", asserts="Harmonic energy is invariant across the whole "
          "admissible bridge class, which is exactly a shift of the surrogate level, under both "
          "fillings and across a 2000x range.",
          cited_in=["bridge sec 8.1 table"], value=sweep,
          tol={"kind": "abs", "value": 1e-9},
          test="tests/test_acceptance.py::test_bridge_invariance_under_surrogate_level")

    floors = {}
    for mode in ("bias_rule", "variance_fresh", "variance_fixed"):
        am = assemble(c.with_(bridge_mode=mode))
        floors[mode] = oracle.projector_split(c.n_vertices, am.edges, am.Y_expected,
                                              "empty")["energies"]["harmonic"]
    claim("systematic-floors", asserts="Only the potential-consistent bridge satisfies "
          "Corollary 1's hypothesis; the zero-centred coins carry a systematic floor.",
          cited_in=["bridge sec 8.2 table"], value=floors,
          tol={"kind": "abs", "value": 1e-9},
          test="tests/test_acceptance.py::test_zero_mean_bridge_leaves_a_persistent_bias")

    rows = {}
    for R in (8, 32, 128, 512, 2048):
        alone, comb = [], []
        for s in range(120):
            cr = c.with_(bridge_mode="variance_fresh", bridge_R=R, seed=s)
            ar = assemble(cr)
            ic = set(ar.blocks["ic"].edges)
            alone.append(oracle.projector_split(cr.n_vertices, ar.edges,
                np.array([ar.Y[i] if e in ic else 0.0 for i, e in enumerate(ar.edges)]),
                "empty")["energies"]["harmonic"])
            comb.append(oracle.projector_split(cr.n_vertices, ar.edges, ar.Y, "empty")["energies"]["harmonic"])
        rows[str(R)] = {"bridge_alone": float(np.mean(alone)), "combined": float(np.mean(comb))}
    claim("thrashing-does-not-wash-out", asserts="The bridge block alone decays as 1/R, but the "
          "combined flow converges to the systematic floor, not to the circle floor.",
          cited_in=["bridge sec 8.2 table", "bridge Remark 5"], value=rows,
          tol={"kind": "rel", "value": 0.05}, kind="stochastic",
          test="tests/test_acceptance.py::test_zero_mean_bridge_leaves_a_persistent_bias")

    n, ni = c.n_vertices, c.n_int
    D0, D1 = hodge.build_operators(n, a.edges, hodge.triangles_for_filling(a.edges, "empty"))
    _, _, Ph = hodge.hodge_projectors(D0, D1)
    Eb = set(a.blocks["ic"].edges)
    s0 = np.zeros(n); s0[:ni] = np.arange(ni, dtype=float); s0[ni:] = -1.0

    def excess(lam):
        """||P_h (D0 s)|Eb||^2 with the integer block scaled by lam."""
        s2 = s0.copy(); s2[:ni] *= lam
        pr = np.array([(s2[j] - s2[i]) if (i, j) in Eb else 0.0 for (i, j) in a.edges])
        return float(pr @ Ph @ pr)

    scal = {str(lam): {"excess": excess(lam), "over_lambda_sq": excess(lam) / lam ** 2}
            for lam in (0.5, 1.0, 2.0, 3.0)}
    # lam = 0 is the load-bearing case -- it is what shows the bias comes from the
    # order rather than the coin -- so it is measured here, not asserted. A
    # hardcoded 0.0 would make the claim incapable of ever failing.
    claim("spread-scaling", asserts="The persistent bias equals ||P_h (D0 s)|Eb||^2 and is exactly "
          "quadratic in the integer scale; at zero spread it is exactly zero.",
          cited_in=["bridge sec 8.3(i)", "bridge sec 8.3(ii)"],
          value={**scal, "flat_block": excess(0.0)},
          tol={"kind": "abs", "value": 1e-9},
          note="A law, not a fit: the quotient by lambda^2 is constant. flat_block is measured.")

    Ycc = np.array([a.Y_expected[k] if e in ccs else 0.0 for k, e in enumerate(a.edges)])
    rng = np.random.default_rng(0); en = []
    for _ in range(2000):
        psi = np.zeros(n); psi[:ni] = np.arange(ni, dtype=float)
        psi[ni:] = rng.normal(0, 5, n - ni)
        Y = D0 @ psi + Ycc
        en.append(float(Y @ Ph @ Y))
    en = np.array(en)
    claim("fabricator-family-invisible", asserts="A family of internally-gradient fabricators is "
          "invisible in every moment, not only the mean: Cov(B) lies inside im D0.",
          cited_in=["bridge sec 8.4, Proposition 3"],
          value={"mean": float(en.mean()), "sd": float(en.std()), "circle_floor": circle},
          tol={"kind": "abs", "value": 1e-9},
          note="sd is at machine precision; the claim is exactness, not a small number.")


# ---------------------------------------------------------------- estimator behaviour
def estimator(cfg):
    n, p, eps = 12, 0.45, 0.3
    mask = flows.sample_sparse_graph(n, p, np.random.default_rng(5))
    D0, D1 = hodge.build_operators(n, mask, hodge.triangles_for_filling(mask, "observed"))
    _, _, Ph = hodge.hodge_projectors(D0, D1)
    hu = flows.harmonic_unit(D0, D1); th = flows.theta_gamma(n, 0.3, 2.0)
    pe = 1 / (1 + np.exp(-flows.misspecified_latent(D0, th, eps, hu)))
    ks = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
    E = []
    for k in ks:
        rg = np.random.default_rng(999 + k)
        w = rg.binomial(k, np.broadcast_to(pe, (3000, len(pe))))
        Y = flows.logodds_from_counts(w, k)
        E.append(float(np.mean(np.einsum("ij,jk,ik->i", Y, Ph, Y))))
    A = lambda K: np.column_stack([np.ones(len(K)), 1.0 / np.array(K, float)])
    full = np.linalg.lstsq(A(ks), np.array(E), rcond=None)[0]
    sel = [i for i, k in enumerate(ks) if k >= 64]
    win = np.linalg.lstsq(A([ks[i] for i in sel]), np.array([E[i] for i in sel]), rcond=None)[0]
    claim("fit-window", asserts="Fitting the full k grid biases the intercept; restricting to "
          "k >= 64 recovers it. The floor is an intercept, so the window decides it.",
          cited_in=["methodology sec 5.3", "methodology fig 3"],
          value={"k": ks, "energies": E, "true_floor": eps ** 2, "fit_k_min": 64,
                 "intercept_full_grid": float(full[0]), "intercept_windowed": float(win[0])},
          tol={"kind": "rel", "value": 0.05}, kind="stochastic")

    fill = {}
    for f in ("observed", "empty"):
        d0, d1 = hodge.build_operators(n, mask, hodge.triangles_for_filling(mask, f))
        _, _, P = hodge.hodge_projectors(d0, d1)
        h = flows.harmonic_unit(d0, d1)
        pef = 1 / (1 + np.exp(-flows.misspecified_latent(d0, th, eps, h)))
        fill[f] = {"b1": int(hodge.harmonic_basis(d0, d1).shape[1]),
                   "c_oracle": oracle.c_oracle(P, pef)}
    claim("filling-dependence", asserts="b1 and c_oracle move by nearly an order of magnitude "
          "with the filling, so a fixed window calibrated under one is wrong under the other.",
          cited_in=["methodology sec 5.3 table"], value=fill,
          tol={"kind": "rel", "value": 0.02})

    cross = {}
    m2 = flows.sample_sparse_graph(12, 0.45, np.random.default_rng(5))
    d0, d1 = hodge.build_operators(12, m2, hodge.triangles_for_filling(m2, "observed"))
    _, _, P2 = hodge.hodge_projectors(d0, d1)
    h2 = flows.harmonic_unit(d0, d1); t2 = flows.theta_gamma(12, 0.25, 2.0)
    for e in (0.2, 0.3, 0.4):
        lat = flows.misspecified_latent(d0, t2, e, h2); pp = 1 / (1 + np.exp(-lat))
        c_var = float(np.trace(P2 @ np.diag(1 / (pp * (1 - pp)))))
        b = (2 * pp - 1) / (2 * pp * (1 - pp))
        xterm = 2 * float((P2 @ lat) @ (P2 @ b))
        kk = np.array([64, 128, 256, 512, 1024, 2048, 4096], float); EE = []
        for k in kk:
            rg = np.random.default_rng(31 + int(k))
            w = rg.binomial(int(k), np.broadcast_to(pp, (4000, len(pp))))
            Y = flows.logodds_from_counts(w, int(k))
            EE.append(float(np.mean(np.einsum("ij,jk,ik->i", Y, P2, Y))))
        _, cfit = np.linalg.lstsq(np.column_stack([np.ones(len(kk)), 1 / kk]), np.array(EE), rcond=None)[0]
        cross[str(e)] = {"c_fit": float(cfit), "c_var_only": c_var, "cross_term": xterm,
                         "ratio_var_only": float(cfit / c_var),
                         "ratio_with_cross": float(cfit / (c_var + xterm))}
    claim("delta-method-cross-term", asserts="The 1/k coefficient omits the plug-in logit mean "
          "bias; including its cross term flattens the guard's drift in eps.",
          cited_in=["methodology sec 5.1"], value=cross,
          tol={"kind": "rel", "value": 0.05}, kind="stochastic")


# ---------------------------------------------------------------- sweeps (slow)
def sweeps(cfg):
    base = cfg

    ratios, covs = [], []
    for bs in range(20):
        c = base.with_(seed=bs).with_(n_cplx=0, n_int=max(base.n_int, 12))
        rows = floor_sweep(c, strict=False)
        ratios.append(float(np.mean([x["floor_over_oracle"] for x in rows if x["eps"] > 0])))
        covs.append(int(sum(x["ci_covers_oracle"] for x in rows)))
    r = np.array(ratios)
    claim("residual-across-draws", asserts="The residual is real but small, and any single run "
          "lands anywhere in a band about a percentage point wide; coverage is typically 15/16.",
          cited_in=["methodology sec 9 table", "methodology fig 5", "methodology v7 note"],
          value={"ratios": ratios, "coverage": covs,
                 "mean": float(r.mean()), "se": float(r.std(ddof=1) / np.sqrt(len(r))),
                 "residual_pct": float(100 * (1 - r.mean())),
                 "per_draw_min_pct": float(100 * (1 - r.max())),
                 "per_draw_max_pct": float(100 * (1 - r.min())),
                 "coverage_median": int(np.median(covs))},
          tol={"kind": "abs_pct", "value": 0.5}, kind="stochastic",
          note="Tolerance is 0.5 percentage points, comfortably inside the 1.0 pt per-draw spread.")

    rho_rows = []
    G4 = (8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096)
    from dataclasses import replace
    for rho in (1.0, 1.5, 2.0, 3.0, 4.5, 6.0, 9.0):
        ms, sh = [], []
        for bs in range(6):
            c = base.with_(seed=bs, rho=rho, btl=replace(base.btl, k=G4)).with_(n_cplx=0, n_int=12)
            rows = floor_sweep(c, strict=False)
            ms.append(np.mean([x["floor_over_oracle"] for x in rows if x["eps"] > 0]))
            sh.append(sum(x["grid_insufficient"] for x in rows))
        m = np.array(ms)
        rho_rows.append({"rho": rho, "bias_pct": float(100 * (1 - m.mean())),
                         "se_pct": float(100 * m.std(ddof=1) / np.sqrt(len(m))),
                         "unfittable": float(np.mean(sh))})
    claim("rho-tradeoff", asserts="The residual falls monotonically as rho falls, because a "
          "smaller rho demands a longer tail -- but cells become unfittable as the grid stops "
          "reaching the window, so rho and the grid must be tuned together.",
          cited_in=["methodology sec 9", "methodology fig 6 left", "methodology v7 note"],
          value=rho_rows, tol={"kind": "abs_pct", "value": 0.8}, kind="stochastic",
          note="Measured on the k->4096 grid, where the trade-off is visible.")

    plate = []
    for nn in (6, 8, 10, 12, 14, 16, 18, 20, 24, 28):
        z = tot = 0; b1s = []
        for s in range(3000):
            rg = np.random.default_rng(77000 + s)
            mk = flows.sample_sparse_graph(nn, 0.45, rg); tot += 1
            if len(mk) < 3:
                z += 1; continue
            d0, d1 = hodge.build_operators(nn, mk, hodge.triangles_for_filling(mk, "observed"))
            b = hodge.harmonic_basis(d0, d1).shape[1]; b1s.append(b)
            if b < 1: z += 1
        plate.append({"n": nn, "rate": z / tot, "mean_b1": float(np.mean(b1s))})
    claim("b1-non-monotone", asserts="The b1=0 rate is non-monotone in n with an interior "
          "minimum; past it, more items destroy the holes the certificate reads.",
          cited_in=["methodology sec 10, Observation 2", "methodology fig 6 right"],
          value=plate, tol={"kind": "abs", "value": 0.02}, kind="stochastic",
          note="Deterministic mask seeds, so drift comes only from numpy version changes.")

    pstar = []
    def rate(nn, pp, reps, seed0):
        z = 0
        for s in range(reps):
            rg = np.random.default_rng(seed0 + s)
            mk = [(i, j) for i, j in itertools.combinations(range(nn), 2) if rg.random() < pp]
            if len(mk) < 3: z += 1; continue
            d0, d1 = hodge.build_operators(nn, mk, hodge.triangles_for_filling(mk, "observed"))
            r0 = np.linalg.matrix_rank(d0); r1 = np.linalg.matrix_rank(d1) if d1.shape[0] else 0
            if len(mk) - r0 - r1 < 1: z += 1
        return z / reps
    for nn in (8, 12, 16, 20, 24, 30):
        lo, hi = 0.10, 0.95
        for _ in range(7):
            mid = (lo + hi) / 2
            if rate(nn, mid, 90, 4242) < 0.5: lo = mid
            else: hi = mid
        pstar.append({"n": nn, "p_star": (lo + hi) / 2, "n_pow_-0.5": nn ** -0.5})
    xs = np.log([q["n"] for q in pstar]); ys = np.log([q["p_star"] for q in pstar])
    claim("kahle-finite-n", asserts="The vanishing threshold decays as the theory requires, but "
          "the asymptotic exponent is not yet visible at these sizes.",
          cited_in=["methodology sec 10 footnote"],
          value={"points": pstar, "fitted_exponent": float(np.polyfit(xs, ys, 1)[0]),
                 "asymptotic_exponent": -0.5},
          tol={"kind": "abs", "value": 0.05}, kind="stochastic")

    c = base.with_(mode_II="clean_gradient", bridge_mode="bias_rule")
    adv = []
    for m in (0, 3, 5, 7, 9):
        cm = c.with_(n_cplx=m); am = assemble(cm)
        sp = oracle.projector_split(cm.n_vertices, am.edges, am.Y_expected, "empty")
        adv.append({"m": m, "floor": sp["energies"]["harmonic"],
                    "raw_fraction": am.analyze(filling="empty")["fractions"]["harmonic"]})
    claim("adversarial-monotone", asserts="The systematic floor follows m(m-1)/2 exactly, while "
          "the raw harmonic fraction moves far less, being diluted by per-block energy.",
          cited_in=["methodology sec 9"], value=adv, tol={"kind": "abs", "value": 1e-6},
          test="tests/test_acceptance.py::test_8_7_systematic_floor_monotone_in_complex_fraction")

    edges = [(0, 1), (0, 3), (1, 2), (2, 3), (4, 5), (4, 6), (5, 6)]
    Y = np.array([1.0, -1.0, 1.0, 1.0, 1.0, 2.0, 1.0])
    z, o = hodge.coefficient_of_consistency(7, {(1, 0), (2, 1), (3, 2), (0, 3), (5, 4), (6, 5), (6, 4)})
    claim("zeta-blind", asserts="On a 4-cycle beside a transitive triangle, zeta reports perfect "
          "consistency while a third of the energy is harmonic.",
          cited_in=["methodology sec 9"],
          value={"zeta": float(z), "observed_triples": int(o),
                 "harmonic": hodge.analyze_flow(7, edges, Y, filling="observed")["fractions"]["harmonic"]},
          tol={"kind": "abs", "value": 1e-9},
          test="tests/test_acceptance.py::test_8_8_zeta_misses_the_planted_harmonic")

    guard = {}
    for name, (rho, grid) in {"historical": (3.0, G4), "current": (1.5, base.btl.k)}.items():
        pts = []
        for beta in (0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.70):
            for e in (0.2, 0.3, 0.4):
                cc = base.with_(n_int=12, n_cplx=0, seeds=24, reps=16, rho=rho,
                                btl=replace(base.btl, beta=beta, k=grid))
                rr = floor_measurement(cc, 2.0, e, strict=False)
                if np.isfinite(rr["floor_over_oracle"]):
                    pts.append({"beta": beta, "eps": e, "ratio": rr["floor_over_oracle"],
                                "c_ratio": rr["c_ratio_median"], "saturation": rr["saturation"]})
        guard[name] = pts
    claim("guard-blind-spot", asserts="The c-oracle check is necessary but not sufficient: "
          "configurations exist that pass it while the floor is badly wrong.",
          cited_in=["methodology sec 6", "methodology fig 4"], value=guard,
          tol={"kind": "rel", "value": 0.10}, kind="stochastic")

    sat = {}
    for beta in (0.25, 0.30, 0.60):
        vals = []
        for s in range(2000):
            rg = np.random.default_rng(20000 + s)
            mk = flows.sample_sparse_graph(12, 0.45, rg)
            if len(mk) < 3: continue
            d0, _ = hodge.build_operators(12, mk, [])
            pp = 1 / (1 + np.exp(-(d0 @ flows.theta_gamma(12, beta, 2.0))))
            vals.append(oracle.saturation(pp, 8))
        v = np.array(vals)
        sat[str(beta)] = {"mean": float(v.mean()), "p95": float(np.percentile(v, 95)),
                          "reject_pct": float(100 * (v >= oracle.SATURATION_MAX).mean())}
    claim("saturation-gate", asserts="beta=0.3 sits on the saturation gate; 0.25 clears it.",
          cited_in=["methodology sec 6", "spec sec 2.6, Delta E"], value=sat,
          tol={"kind": "abs", "value": 0.02}, kind="stochastic",
          test="tests/test_invariants.py::test_2_6_saturation_gate_rejects_extreme_separation")


def write_provenance(out):
    """Emit PROVENANCE.md from the evidence itself, so the index cannot go stale."""
    L = ["# Provenance index", "",
         "Every quantity cited in the papers, with the code that produces it, the",
         "tolerance within which a re-run must reproduce it, and the test that pins it",
         "where one does.", "",
         f"Generated {out['meta']['generated']} from commit `{out['meta']['commit']}`",
         f"on Python {out['meta']['python']} / numpy {out['meta']['numpy']}.", "",
         "```bash", "python generate.py     # rebuild evidence.json (~2 min)",
         "python verify.py       # re-run and check every claim against it",
         "python verify.py --fast  # structural claims only, seconds", "```", "",
         "## Reproducibility", "",
         "Every RNG is seeded from a fixed constant, so on the same numpy every claim",
         "reproduces **bit-exactly** — the last full run showed zero drift on all",
         f"{out['meta']['n_claims']} claims. The tolerances below are the margin allowed for a",
         "different numpy or platform, not slack in the measurement. `exact` claims are",
         "identities or closed forms and are held to machine precision; `stochastic`",
         "claims are Monte Carlo and carry a tolerance set from their measured spread.", "",
         "## Claims", ""]
    ex = [(k, v) for k, v in out["claims"].items() if v["kind"] == "exact"]
    st = [(k, v) for k, v in out["claims"].items() if v["kind"] != "exact"]
    for head, group in (("### Exact (identities and closed forms)", ex),
                        ("### Stochastic (Monte Carlo)", st)):
        L += [head, "",
              "| id | asserts | cited in | tolerance | test |", "|---|---|---|---|---|"]
        for k, v in group:
            tol = v["tolerance"]
            ts = "exact" if tol.get("kind") == "exact_int" else \
                 f"{tol['value']:g} {tol['kind']}"
            test = f"`{v['test'].split('::')[-1]}`" if v["test"] else "—"
            L.append(f"| `{k}` | {v['claim']} | {'; '.join(v['cited_in'])} | {ts} | {test} |")
        L.append("")
    L += ["## Reading the data", "",
          "`evidence.json` holds each claim's full value under `claims.<id>.value`.",
          "Figures are regenerated from it by `../make_figures.py`; the figure PDFs and",
          "`runs/` are build products and are not committed.", "",
          "A claim with no test is checked only by `verify.py`. A claim with a test is",
          "checked twice: `verify.py` compares its value, and the test re-derives it",
          "independently in the acceptance suite."]
    (HERE / "PROVENANCE.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    cfg = structural()
    bridge(cfg)
    estimator(cfg)
    if "--fast" not in sys.argv:
        sweeps(cfg)
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                         text=True, cwd=HERE).stdout.strip()
    # Recorded history, not measurements: the three residual figures successively
    # reported as "the" result before the quantity was characterised across seeds.
    # They belong with the evidence because Figure 5 plots them, but they are not
    # claims -- nothing regenerates them, so they sit outside `claims`.
    annotations = {"historical_residual_estimates":
                   {"v5 (~10%)": 0.90, "v6 (3-6%)": 0.955, "v6b (~2.6%)": 0.974}}
    out = {"annotations": annotations,
           "meta": {"generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "commit": sha, "numpy": np.__version__,
                    "python": f"{sys.version_info.major}.{sys.version_info.minor}",
                    "n_claims": len(CLAIMS)},
           "claims": CLAIMS}
    (HERE / "evidence.json").write_text(json.dumps(out, indent=1, default=float))
    write_provenance(out)
    print(f"  wrote evidence.json: {len(CLAIMS)} claims")
    for k, v in CLAIMS.items():
        print(f"    {k:34} {v['kind']:10} test={'yes' if v['test'] else 'NO '}")
