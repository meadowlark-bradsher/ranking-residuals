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
from rig import fit, flows, moments, oracle, provenance
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


# ---------------------------------------------------------------- residual mechanism
def _calibration_topology(n_int, gamma=2.0, eps=0.2, n_cplx=0, filling="observed"):
    """The first fittable mask of the floor path, reproduced exactly.

    Mirrors rig.sweep.floor_measurement's seed derivation rather than drawing a
    fresh mask: the coefficients below are properties of THAT graph, and a mask
    drawn any other way would give different -- equally correct -- numbers for a
    different topology.

    THE DEFAULTS ARE PART OF THAT CLAIM, and they were both wrong. n_cplx never
    enters the graph but DOES enter the config fingerprint, hence derive_seed --
    the previous docstring said exactly this and then carried n_cplx=5, while
    every floor measurement in the repo runs at n_cplx=0 (rig/sweep.py:234,
    sweeps() below, bias-of-bias/exact_energy.py). eps is hashed into the mask
    seed too, and 0.3 is not on the floor grid (0.0, 0.1, 0.2, 0.4) at all. The
    two together selected a mask no floor measurement ever draws: at n_int=12,
    seed 0 the floor path draws 34 edges with b1 = 4, this drew 25 edges with
    b1 = 7, and the cross-term shortfall these coefficients feed reads 0.202%
    on the off-path mask against 2.435% on the real one.

    Every claim built on this is topology-bound -- firth-localises-boundary says
    so in its own text -- so an off-path topology does not make the numbers
    wrong, it makes them answer a question nobody asked. Now on-path.
    """
    cfg = RigConfig().validate().with_(n_int=n_int, n_cplx=n_cplx)
    for s in range(cfg.seeds):
        mask = flows.sample_sparse_graph(
            n_int, cfg.btl.p, np.random.default_rng(cfg.derive_seed("floor_mask", gamma, eps, s)))
        if len(mask) < 3:
            continue
        D0, D1 = hodge.build_operators(n_int, mask, hodge.triangles_for_filling(mask, filling))
        _, _, Ph = hodge.hodge_projectors(D0, D1)
        try:
            h = flows.harmonic_unit(D0, D1)
        except ValueError:
            continue                                  # b1 = 0: nothing to inject into
        th = flows.latent_potential(n_int, cfg.btl, gamma,
                                    np.random.default_rng(cfg.derive_seed("theta", s)))
        lam = flows.misspecified_latent(D0, th, eps, h)
        return {"Ph": Ph, "pe": 1 / (1 + np.exp(-lam)), "lam": lam, "h": h,
                "eps": eps, "floor": float(lam @ Ph @ lam), "n_edges": len(mask)}
    raise RuntimeError(f"no fittable mask at n_int={n_int}")


def residual_mechanism(cfg):
    """The 1/k and 1/k^2 coefficients of the harmonic energy, exactly (no sampling).

    These are the mechanism behind the floor residual. Everything here is a closed
    form or an exact binomial sum, so it is `exact`-kind: any drift at all means a
    changed code path, not a noisier draw.
    """
    T = {"nZ6": _calibration_topology(6), "nZ12": _calibration_topology(12)}

    c1, c2, comp = {}, {}, {}
    for tag, t in T.items():
        Ph, pe, eps, h = t["Ph"], t["pe"], t["eps"], t["h"]
        got = moments.series_coefficients(Ph, pe, t["floor"])
        V = 1.0 / (pe * (1 - pe))
        b = moments.bias_vector(pe)
        tr = float(np.trace(Ph @ np.diag(V)))
        cross = 2 * eps * float(h @ b)
        c1[tag] = {"measured": got[0], "tr_Ph_V": tr, "cross": cross,
                   "closed": tr + cross, "ratio_to_closed": got[0] / (tr + cross),
                   "ratio_to_var_only": got[0] / tr}
        # b2 is the 1/k^2 term of the MEAN; extracted the same way as c1/c2 so the
        # decomposition is checked against the same machinery it is meant to explain.
        ks = np.array([2 ** j for j in range(11, 18)], float)
        MU = np.array([moments.edge_moments(pe, int(k))[0] for k in ks])
        VA = np.array([moments.edge_moments(pe, int(k))[1] for k in ks])
        u = ks[0] / ks
        A = np.column_stack([u ** j for j in range(1, 5)])
        b2 = np.linalg.lstsq(A, MU - np.log(pe / (1 - pe)), rcond=None)[0][1] * ks[0] ** 2
        v2n = np.linalg.lstsq(A, VA, rcond=None)[0][1] * ks[0] ** 2
        parts = {"b_Ph_b": float(b @ Ph @ b), "cross_2nd": 2 * eps * float(h @ b2),
                 "variance": float(np.diag(Ph) @ v2n)}
        tot = sum(parts.values())
        c2[tag] = {"measured": got[1], "reconstructed": tot, "ratio": tot / got[1]}
        comp[tag] = {k: v / tot for k, v in parts.items()}

    claim("c1-cross-term-completes", asserts="The 1/k coefficient of the harmonic energy is "
          "tr(P_h V) + 2 eps (h.b), not tr(P_h V) alone. The cross term COMPLETES the "
          "delta-method oracle rather than refining it: measured/closed is 1.0 to 8 dp on "
          "both calibration topologies, while variance-only is off by 2.7% and 5.0%.",
          cited_in=["methodology sec 5.1", "methodology sec 9"], value=c1,
          tol={"kind": "rel", "value": 1e-6},
          test="tests/test_invariants.py::test_7_c1_equals_variance_plus_cross")

    claim("c2-variance-dominated", asserts="The 1/k^2 coefficient is 88-95% the SECOND-ORDER "
          "VARIANCE of the logit and only 0.6-2.5% the mean-bias term b'P_h b. The natural "
          "expectation that the vector driving the 1/k correction also drives the 1/k^2 one "
          "is wrong by two orders of magnitude.",
          cited_in=["methodology sec 5.3", "methodology sec 9"],
          value={"c2": c2, "composition": comp}, tol={"kind": "rel", "value": 1e-4},
          note="Decomposition reconstructs the measured c2 to ~1e-6 relative, so the three "
               "terms are the whole of it -- there is no unaccounted fourth contribution.")

    # Closed forms are checked against the extraction rather than asserted: a formula
    # that merely reproduces its own derivation is not evidence.
    ps = np.array([0.08, 0.15, 0.25, 0.35, 0.45, 0.55, 0.70, 0.80])
    ks = np.array([2 ** j for j in range(12, 19)], float)
    u = ks[0] / ks
    A = np.column_stack([u ** j for j in range(1, 5)])
    v2fit = {}
    for est in ("clamped_logit", "firth"):
        VA = np.array([moments.edge_moments(ps, int(k), est)[1] for k in ks])
        num = np.linalg.lstsq(A, VA, rcond=None)[0][1] * ks[0] ** 2
        closed = moments.v2(ps, est)
        v2fit[est] = {"max_abs_dev": float(np.abs(num - closed).max()),
                      "closed_at_p": {f"{p:.2f}": float(c) for p, c in zip(ps, closed)}}
    claim("v2-closed-forms", asserts="The 1/k^2 variance coefficient has closed form "
          "v2 = 2/(pq) + (3/2)(2p-1)^2/(pq)^2 for the shipped clamped logit, and "
          "v2 = (1/2)(2p-1)^2/(pq)^2 for a per-edge continuity-corrected estimator. Both "
          "match the exact extraction to its own precision; the corrected form is zero at "
          "p = 1/2.", cited_in=["methodology sec 5.3", "methodology sec 9"], value=v2fit,
          tol={"kind": "abs", "value": 5e-3},
          note="Tolerance is extraction-limited, not form-limited: the polynomial fit "
               "resolves v2 to ~1e-3 absolute at the extreme p, well inside the gap between "
               "these two forms. Independently derived by third-order delta method.")

    fir = {}
    for tag, t in T.items():
        Ph, pe, eps, h = t["Ph"], t["pe"], t["eps"], t["h"]
        raw = moments.series_coefficients(Ph, pe, t["floor"], estimator="clamped_logit")
        fth = moments.series_coefficients(Ph, pe, t["floor"], estimator="firth")
        tr = float(np.trace(Ph @ np.diag(1.0 / (pe * (1 - pe)))))
        fir[tag] = {"c1_raw": raw[0], "c1_firth": fth[0], "c1_firth_minus_trPhV": fth[0] - tr,
                    "c2_raw": raw[1], "c2_firth": fth[1], "c2_ratio": fth[1] / raw[1],
                    "p_edge_min": float(pe.min()), "p_edge_max": float(pe.max())}
    claim("firth-localises-boundary", asserts="A per-edge continuity-corrected estimator "
          "removes the c1 cross term exactly (c1_F = tr(P_h V)) and annihilates the 2/(pq) "
          "near-boundary term of v2, cutting the asymmetry term 3/2 -> 1/2. The resulting "
          "c2 ratio is bounded in (0, 1/3) and is set by the P_h-weighted edge-probability "
          "mix -- 13.5% on a mid-range topology, 22.7% on one whose edges reach p ~ 0.07. "
          "No universal reduction factor exists.",
          cited_in=["methodology sec 9"], value=fir, tol={"kind": "rel", "value": 1e-4},
          note="DIAGNOSTIC PROBE, not a recommended fix, and PER-EDGE only: this is the "
               "drop-in for logodds_from_counts, exactly (w+1/2)/(k+1) with no clamp "
               "needed. It is NOT Firth-penalised BTL on the joint sparse design, whose "
               "penalty does not factorise over edges and is untested. Do not write "
               "'Firth' unqualified.")
    return T


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


# ---------------------------------------------------------------- residual, exact (slow)
def _exact_residual(cfg, estimator="clamped_logit", models=("2param",)):
    """One base seed's floor residual with Monte Carlo removed.

    Follows floor_measurement exactly -- same seeds, same derived window, same
    'observed' filling default -- and differs ONLY in that the energies are exact
    rather than averaged over `reps` draws. That is what makes the difference
    attributable to the fit model rather than to sampling.
    """
    ks = np.array(cfg.btl.k, dtype=float)
    out = {m: [] for m in models}
    for gamma in cfg.btl.gamma:
        for eps in cfg.eps:
            if eps <= 0:
                continue                      # no floor to resolve; not a ratio cell
            cell = {m: [] for m in models}
            for s in range(cfg.seeds):
                mask = flows.sample_sparse_graph(
                    cfg.n_int, cfg.btl.p,
                    np.random.default_rng(cfg.derive_seed("floor_mask", gamma, eps, s)))
                if len(mask) < 3:
                    continue
                D0, D1 = hodge.build_operators(
                    cfg.n_int, mask, hodge.triangles_for_filling(mask, "observed"))
                _, _, Ph = hodge.hodge_projectors(D0, D1)
                try:
                    h = flows.harmonic_unit(D0, D1)
                except ValueError:
                    continue
                th = flows.latent_potential(
                    cfg.n_int, cfg.btl, gamma,
                    np.random.default_rng(cfg.derive_seed("theta", s)))
                lam = flows.misspecified_latent(D0, th, eps, h)
                pe = 1 / (1 + np.exp(-lam))
                # The window rule passes c_oracle = tr(P_h V) -- variance only, NOT the
                # full c1. A continuity-corrected estimator leaves the leading variance
                # untouched, so k_min is bit-identical under it and the window channel
                # contributes nothing to any estimator comparison below.
                need = oracle.required_fit_k_min(oracle.c_oracle(Ph, pe),
                                                 oracle.floor_oracle(eps), cfg.rho)
                window = max(cfg.btl.fit_k_min, need)
                if len([k for k in cfg.btl.k if k >= window]) < 2:
                    window = float(sorted(cfg.btl.k)[-2])
                E = np.array([moments.exact_energy(Ph, pe, int(k), estimator)[0]
                              for k in cfg.btl.k])
                sel = ks >= window
                K, Es = ks[sel], E[sel]
                if "2param" in models:
                    cell["2param"].append(
                        fit.fit_floor_c(ks, E, window)["floor"] / eps ** 2)
                if "3param" in models and sel.sum() >= 3:
                    A3 = np.column_stack([np.ones_like(K), 1 / K, 1 / K ** 2])
                    cell["3param"].append(
                        np.linalg.lstsq(A3, Es, rcond=None)[0][0] / eps ** 2)
                if "c2sub" in models:
                    # c2 SUBTRACTED, not fitted: it is a closed form of the null the rig
                    # already constructs, so spending a fit parameter on it is spending
                    # variance to recover something already known.
                    c2 = float(np.diag(Ph) @ moments.v2(pe, estimator))
                    if estimator == "clamped_logit":
                        # The mean-bias piece is ~1% of c2 and is identically zero for a
                        # continuity-corrected estimator; adding it there would subtract
                        # a term that does not exist.
                        bv = moments.bias_vector(pe)
                        c2 += float(bv @ Ph @ bv)
                    A2 = np.column_stack([np.ones_like(K), 1 / K])
                    cell["c2sub"].append(
                        np.linalg.lstsq(A2, Es - c2 / K ** 2, rcond=None)[0][0] / eps ** 2)
            for m in models:
                if cell[m]:
                    out[m].append(float(np.mean(cell[m])))
    return {m: float(np.mean(v)) for m, v in out.items() if v}


def _spread(vals):
    a = 100.0 * (1.0 - np.array(vals, dtype=float))         # ratio -> residual %
    return {"mean_pct": float(a.mean()),
            "se_pct": float(a.std(ddof=1) / np.sqrt(len(a))),
            "min_pct": float(a.min()), "max_pct": float(a.max()),
            "range_pct": float(a.max() - a.min()), "n_base_seeds": len(a)}


def residual_exact(cfg):
    """The residual with sampling noise removed, across base seeds.

    Base-seed count is the budget knob here: the quantity is deterministic given a
    mask, so the only stochasticity left is which topologies get drawn. 20 matches
    the shipped sweep's protocol so the two are comparable; the corrected-estimator
    arm uses 5, which is ample given its s.e. is ~0.001 pt.
    """
    # n_cplx=0, matching floor_sweep (rig/sweep.py:234) and the residual-across-
    # draws arm in sweeps() below. It was 5, which fingerprints differently and
    # therefore seeds a different mask for every (gamma, eps, s) -- so the
    # pairing against residual-across-draws that this claim's note relies on was
    # comparing disjoint topology ensembles, and the +-0.09 pt band could not be
    # attributed to reps=16 sampling noise on that evidence.
    base = RigConfig().validate().with_(n_int=12, n_cplx=0)
    raw = [_exact_residual(base.with_(seed=b), models=("2param", "3param", "c2sub"))
           for b in range(20)]
    fth = [_exact_residual(base.with_(seed=b), estimator="firth")["2param"]
           for b in range(5)]

    two = _spread([r["2param"] for r in raw])
    claim("residual-exact", asserts="With Monte Carlo removed (exact binomial energies) the "
          "two-parameter floor is under-read by +0.36% over 20 base seeds with a standard "
          "error of 0.002 pt. The shipped +-0.09 pt band is therefore almost entirely "
          "reps=16 sampling noise, not base-seed variation: the underlying quantity is "
          "near-deterministic.",
          cited_in=["methodology sec 9 table", "methodology fig 5", "methodology v8 note"],
          value=two, tol={"kind": "abs", "value": 0.02}, kind="stochastic",
          note="CANONICAL value for the exact residual; the paper quotes this one. "
               "Deterministic given the mask, so it reproduces bit-for-bit on fixed "
               "numpy; the residual stochasticity is topology draw only. Compare "
               "residual-across-draws, the same quantity measured at reps=16. "
               "An INDEPENDENT REPLICATION lives at design/methodology/experiments/"
               "bias-of-bias (report_exact.py -> results/exact_energy_residual.json) "
               "and reports +0.36349% +- 0.00199%, which this arm now MATCHES to "
               "every digit reported. The earlier disagreement was read as the two "
               "implementations having been written separately; it was not. This "
               "side was building its configs at n_cplx=5 while the replication "
               "used n_cplx=0, and n_cplx enters the config fingerprint and hence "
               "every mask seed -- so the two were averaging over disjoint topology "
               "ensembles. With both on the floor path they agree exactly, which is "
               "the stronger result: two separately written implementations of the "
               "same identity, on the same graphs, to the last digit. Cite this "
               "claim rather than that file so a single number travels.")

    claim("residual-fit-variants", asserts="Because c2 is a closed form it can be subtracted "
          "rather than fitted. Subtracting it removes most of the residual; fitting it as a "
          "free third parameter removes essentially all of it on exact energies. Both are "
          "reported across base seeds -- these are topology-dependent, not single draws.",
          cited_in=["methodology sec 5.3", "methodology sec 9"],
          value={"two_param": two,
                 "three_param": _spread([r["3param"] for r in raw]),
                 "c2_subtracted": _spread([r["c2sub"] for r in raw])},
          tol={"kind": "abs", "value": 0.02}, kind="stochastic",
          note="EVIDENCE for the mechanism, not a recommended remedy. The three-parameter "
               "figure is measured on EXACT energies; its behaviour at reps=16, where a "
               "third parameter may cost more variance than the bias it removes, is not "
               "measured here and is the original sec 5.3 objection.")

    f = _spread(fth)
    claim("residual-tracks-c2", asserts="Changing the edge estimator moves the residual in "
          "the proportion its c2 moves. A per-edge continuity-corrected estimator has "
          "22.75% of the raw c2 on this topology and yields 22.88% of the raw residual -- "
          "agreement to under 0.2 pp, with no Monte Carlo on either side. Residual is "
          "proportional to c2.",
          cited_in=["methodology sec 9"],
          # Read from the claim that MEASURES it, not typed in beside it. As a
          # literal, c2_ratio_nZ12 regenerated as 0.2119 against 0.2119 forever:
          # verify.py compares stored to fresh leaf by leaf, so its drift was
          # exactly zero under any tolerance and the coupling this claim exists
          # to test -- residual moves in proportion to c2 -- was not wired to
          # anything. If the topology, the estimator or moments.v2 moved, the
          # firth-localises-boundary claim would fail while this one went on
          # asserting the superseded number and reporting ok.
          value={"firth": f, "raw": two,
                 "residual_ratio": f["mean_pct"] / two["mean_pct"],
                 "c2_ratio_nZ12": CLAIMS["firth-localises-boundary"]["value"]["nZ12"]["c2_ratio"]},
          tol={"kind": "rel", "value": 0.05}, kind="stochastic",
          note="Ratio is taken against the 20-base-seed raw mean, so both arms are the "
               "quantity the paper quotes. Taking it against the 5-seed raw mean instead "
               "gives 22.94%; the c2-tracking claim survives either pairing. The corrected "
               "estimator is a DIAGNOSTIC PROBE and per-edge only -- see "
               "firth-localises-boundary.")


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
    residual_mechanism(cfg)
    if "--fast" not in sys.argv:
        sweeps(cfg)
        residual_exact(cfg)
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
    if "--fast" in sys.argv:
        print(f"  --fast: {len(CLAIMS)} fast claims OK, evidence.json NOT written "
              f"(it would drop every slow claim). Use `verify.py --fast` to check, or "
              f"run without --fast to regenerate.")
        raise SystemExit(0)
    # MODULE fingerprint, not a per-entry one: six functions contribute claims
    # to this one file, so there is no single entry to narrow to. It lands in
    # `meta`, beside commit/numpy/python, because that is where this file keeps
    # provenance. meta.commit records which commit ran; the fingerprint records
    # whether the code has changed MEANING since, which a sha cannot say once
    # the tree moves on -- and which is the whole reason evidence.json needed
    # one: it was the largest artifact in the repo with no way to date it.
    provenance.stamp(out, sys.modules[__name__])
    (HERE / "evidence.json").write_text(json.dumps(out, indent=1, default=float))
    write_provenance(out)
    print(f"  wrote evidence.json: {len(CLAIMS)} claims")
    for k, v in CLAIMS.items():
        print(f"    {k:34} {v['kind']:10} test={'yes' if v['test'] else 'NO '}")
