"""Spec §5 load-bearing invariants, plus the §2.4/§2.5/§2.6/§9/§10 rules.

These are the traps. Each one is a claim the spec makes that would silently corrupt a
result if it stopped holding, so each gets a test that fails loudly.
"""

import itertools

import numpy as np
import pytest

import hodge
from rig import flows, moments, oracle, pool
from rig.config import RigConfig
from rig.emit import EmissionCollapse, emit_assembly, emit_from_flow, emit_from_signs
from rig.graph import assemble
from rig.sweep import config_record, floor_measurement


# ---------------------------------------------------------------- §5.1
@pytest.mark.parametrize("n,expected", [(5, 0.200), (6, 0.2222)])
def test_5_1_pm1_of_a_transitive_order_is_not_a_gradient(n, expected):
    """A +-1 sign flow of a PERFECTLY transitive order deposits spurious harmonic.

    And the amount is n-dependent, not the constant 0.200 the spec once quoted.
    """
    edges = list(itertools.combinations(range(n), 2))
    val = np.arange(n, dtype=float)
    Yv = np.array([val[j] - val[i] for i, j in edges])

    assert hodge.analyze_flow(n, edges, Yv, filling="empty")["fractions"]["harmonic"] \
        == pytest.approx(0.0, abs=1e-12)
    h = hodge.analyze_flow(n, edges, np.sign(Yv), filling="empty")["fractions"]["harmonic"]
    assert h == pytest.approx(expected, abs=5e-4)


def test_5_1_rig_never_emits_pm1_for_integer_or_bias_bridge():
    """The rig's I-I and bias-bridge blocks must carry magnitude, never +-1."""
    cfg = RigConfig().validate().with_(mode_II="clean_gradient", bridge_mode="bias_rule")
    a = assemble(cfg)
    for name in ("ii", "ic"):
        mags = np.unique(np.abs(np.round(a.blocks[name].Y, 9)))
        assert len(mags) > 1, f"{name} block is +-1 -- §5.1 violated: {mags}"


# ---------------------------------------------------------------- §5.2
def test_5_2_unit_circle_ties_every_magnitude():
    z = pool.complex_points(pool.complex_angles(7, "equal_spaced"))
    assert len(np.unique(np.round(np.abs(z), 12))) == 1


def test_5_2_surrogate_defeating_pool_disagrees_on_all_three_orders():
    ang, rad, worst = pool.surrogate_defeating_pool(6, np.random.default_rng(0))
    z = rad * np.exp(1j * ang)
    orders = [np.argsort(np.real(z)), np.argsort(np.abs(z)),
              np.argsort(np.angle(z) % (2 * np.pi))]
    assert worst < 0.5
    for a, b in itertools.combinations(orders, 2):
        assert not np.array_equal(a, b)


# ---------------------------------------------------------------- §5.3
def test_5_3_fresh_decays_and_fixed_persists():
    """Fresh-per-comparison is variance; fixed-per-pair is systematic. Never confuse them."""
    edges = [(i, 8 + j) for i in range(8) for j in range(5)]
    s_int = np.arange(8, dtype=float)
    fresh = [flows.bridge_block(edges, 8, "variance_fresh", s_int, 1.0, R,
                                np.random.default_rng(R)).rms() for R in (4, 64, 1024)]
    fixed = [flows.bridge_block(edges, 8, "variance_fixed", s_int, 1.0, R,
                                np.random.default_rng(R)).rms() for R in (4, 64, 1024)]
    assert fresh[0] > fresh[-1] * 2, fresh          # decays
    assert fixed[-1] > fixed[0], fixed              # persists (grows as log(2R-1))


# ---------------------------------------------------------------- §5.4
def test_5_4_compare_fractions_not_raw_energy_across_topologies():
    """b1, projector and noise covariance all move with the graph, so raw energy is
    not comparable across fillings -- the fraction is."""
    cfg = RigConfig().validate().with_(n_int=0, n_cplx=5)
    a = assemble(cfg)
    e = a.analyze(filling="empty")
    o = a.analyze(filling="observed")
    assert e["total_mass"] == pytest.approx(o["total_mass"])   # same flow ...
    assert e["b1_holes"] != o["b1_holes"]                       # ... different topology
    assert e["fractions"]["harmonic"] != pytest.approx(o["fractions"]["harmonic"])


# ---------------------------------------------------------------- §5.5
def test_5_5_only_equal_spacing_reduces_to_pure_curl():
    cfg = RigConfig().validate()
    eq = assemble(cfg.with_(n_int=0, n_cplx=5, complex_pool="equal_spaced"))
    assert eq.analyze(filling="observed")["fractions"]["curl"] == pytest.approx(1.0, abs=1e-12)
    assert eq.analyze(filling="empty")["fractions"]["gradient"] == pytest.approx(0.0, abs=1e-12)

    uneven = assemble(cfg.with_(n_int=0, n_cplx=5, complex_pool="random"))
    f = uneven.analyze(filling="observed")["fractions"]
    assert f["gradient"] > 1e-6, "uneven spacing must leave a gradient part (partial order)"


# ---------------------------------------------------------------- §5.6
@pytest.mark.parametrize("gamma", [1.0, 1.5, 2.0, 3.0, 6.0])
def test_5_6_theta_shape_can_never_produce_a_floor(gamma):
    """P_h . (D0 theta) == 0 IDENTICALLY -- theta is a potential, D0 theta is a pure
    gradient, and the projector annihilates it. No gamma produces a floor."""
    n = 12
    rng = np.random.default_rng(7)
    mask = flows.sample_sparse_graph(n, 0.45, rng)
    D0, D1 = hodge.build_operators(n, mask, hodge.triangles_for_filling(mask, "observed"))
    _, _, Ph = hodge.hodge_projectors(D0, D1)
    lat = D0 @ flows.theta_gamma(n, 0.3, gamma)
    assert float(lat @ Ph @ lat) < 1e-9 * float(lat @ lat)


def test_5_6_the_null_is_comparable_not_the_bridge():
    """The innocent null lives on I-I edges; the bridge is a different distribution."""
    cfg = RigConfig().validate().with_(n_cplx=0, mode_II="clean_gradient")
    assert assemble(cfg).analyze(filling="empty")["fractions"]["harmonic"] \
        == pytest.approx(0.0, abs=1e-12)


# ---------------------------------------------------------------- §5.7
def test_5_7_block_scale_is_explicit_and_logged():
    cfg = RigConfig().validate()
    rec = config_record(cfg, with_log=False)
    for key in ("rms_ii", "rms_cc", "rms_ic", "total_mass", "b1_holes"):
        assert key in rec
    assert rec["rms_cc"] == pytest.approx(1.0)      # C-C is +-1 by construction

    scaled = assemble(cfg.with_(block_scale=(1.0, 4.0, 1.0)))
    base = assemble(cfg)
    assert scaled.block_rms()["rms_cc"] == pytest.approx(4.0 * base.block_rms()["rms_cc"])


# ---------------------------------------------------------------- §2.4
def test_2_4_gamma_one_reproduces_the_reference_contract():
    n, beta = 12, 0.3
    ref = beta * (n - 1 - np.arange(n, dtype=float))
    got = flows.theta_gamma(n, beta, 1.0)
    assert np.allclose(ref[:, None] - ref[None, :], got[:, None] - got[None, :], atol=1e-12)


def test_2_4_theta_std_is_held_across_gamma():
    stds = [flows.theta_gamma(12, 0.3, g).std() for g in (1.0, 1.5, 2.0, 3.0, 6.0)]
    assert max(stds) - min(stds) < 1e-12, stds


def test_2_4_fixed_mask_across_k_is_not_optional():
    from dataclasses import replace
    cfg = RigConfig().validate()
    with pytest.raises(ValueError, match="fixed_mask_across_k"):
        cfg.with_(btl=replace(cfg.btl, fixed_mask_across_k=False))


# ---------------------------------------------------------------- §2.5
@pytest.mark.parametrize("eps", [0.0, 0.1, 0.2, 0.4])
def test_2_5_injected_floor_is_exactly_eps_squared(eps):
    n = 12
    mask = flows.sample_sparse_graph(n, 0.45, np.random.default_rng(11))
    D0, D1 = hodge.build_operators(n, mask, hodge.triangles_for_filling(mask, "observed"))
    _, _, Ph = hodge.hodge_projectors(D0, D1)
    lat = flows.misspecified_latent(D0, flows.theta_gamma(n, 0.3, 2.0), eps,
                                    flows.harmonic_unit(D0, D1))
    assert float(lat @ Ph @ lat) == pytest.approx(eps ** 2, abs=1e-12)


def test_2_5_b1_zero_refuses_to_inject():
    """No harmonic direction to inject into is an error, not a silent zero."""
    edges = [(0, 1), (1, 2), (0, 2)]
    D0, D1 = hodge.build_operators(3, edges, hodge.triangles_for_filling(edges, "observed"))
    with pytest.raises(ValueError, match="b1 = 0"):
        flows.harmonic_unit(D0, D1)


# ---------------------------------------------------------------- §2.6
def test_2_6_saturation_gate_rejects_extreme_separation():
    """beta=0.25 clears the gate, beta=0.6 does not.

    Uses 0.25, not the old 0.3 default: at 0.3 the gate rejects 43.5% of masks
    (n=12, p=0.45, k_min=8, 2000 masks), so asserting it clears was true only for
    the one seed the test happened to pick.
    """
    n = 12
    mask = flows.sample_sparse_graph(n, 0.45, np.random.default_rng(7))
    D0, _ = hodge.build_operators(n, mask, [])
    pe_ok = 1 / (1 + np.exp(-(D0 @ flows.theta_gamma(n, 0.25, 2.0))))
    pe_bad = 1 / (1 + np.exp(-(D0 @ flows.theta_gamma(n, 0.6, 2.0))))
    assert oracle.saturation(pe_ok, 8) < oracle.SATURATION_MAX
    assert oracle.saturation(pe_bad, 8) > oracle.SATURATION_MAX


def test_2_6_fit_window_is_not_a_tuning_knob():
    from dataclasses import replace
    cfg = RigConfig().validate()
    with pytest.raises(ValueError, match="not a tuning knob"):
        cfg.with_(btl=replace(cfg.btl, fit_k_min=8))


def test_2_6_required_window_scales_with_c_over_floor():
    assert oracle.required_fit_k_min(160.0, 0.09) > oracle.required_fit_k_min(17.0, 0.09)
    assert oracle.required_fit_k_min(17.0, 0.0) == float("inf")


# ---------------------------------------------------------------- §10
def test_10_single_row_per_pair_destroys_the_flow():
    """The original §10 error, kept as a regression: R=1 yields Y=0 on every edge."""
    cfg = RigConfig().validate().with_(n_int=0, n_cplx=5)
    a = assemble(cfg)
    with pytest.raises(ValueError):
        emit_from_flow(a.edges, a.Y, 1, "cc", np.random.default_rng(0))
    with pytest.raises(EmissionCollapse):
        emit_from_flow(a.edges, a.Y, 2, "cc", np.random.default_rng(0))
    assert emit_from_signs(a.edges, a.Y, 3, "cc", np.random.default_rng(0)) \
        .analyze(5, filling="empty")["total_mass"] > 0


def test_10_row_counts_are_floored_at_two():
    cfg = RigConfig().validate()
    for kw in ({"bridge_R": 1}, {"emit_k": 1}):
        with pytest.raises(ValueError, match="§10"):
            cfg.with_(**kw)


# ---------------------------------------------------------------- §9
def test_9_same_config_and_seed_gives_identical_output():
    cfg = RigConfig().validate()
    a, b = (assemble(cfg, gamma=2.0, eps=0.2, k=32) for _ in range(2))
    assert np.array_equal(a.Y, b.Y) and a.edges == b.edges
    la = emit_assembly(a, "x").rows
    lb = emit_assembly(b, "x").rows
    assert la == lb, "emission is not reproducible"
    assert cfg.fingerprint() == RigConfig().validate().fingerprint()


def test_9_timestamps_are_deterministic_never_wall_clock():
    cfg = RigConfig().validate().with_(n_int=0, n_cplx=5)
    a = assemble(cfg)
    stamps = [r[4] for r in emit_assembly(a, "x").rows]
    assert stamps == [r[4] for r in emit_assembly(assemble(cfg), "x").rows]
    assert all(s.startswith("2026-01-") for s in stamps)


# ---------------------------------------------------------------- §7 exact energy
def _fixture(n=12, gamma=2.0, eps=0.3, seed=11):
    mask = flows.sample_sparse_graph(n, 0.45, np.random.default_rng(seed))
    D0, D1 = hodge.build_operators(n, mask, hodge.triangles_for_filling(mask, "observed"))
    _, _, Ph = hodge.hodge_projectors(D0, D1)
    h = flows.harmonic_unit(D0, D1)
    lat = flows.misspecified_latent(D0, flows.theta_gamma(n, 0.25, gamma), eps, h)
    return Ph, 1 / (1 + np.exp(-lat)), lat, h, eps


def test_7_exact_energy_matches_sampling():
    """The factorisation E[Y'PhY] = mu'Ph mu + sum (Ph)_ee Var(Y_e) relies on edges being
    INDEPENDENT. If a generator ever couples them the identity breaks silently, so it is
    checked against actual draws rather than trusted."""
    Ph, pe, *_ = _fixture()
    rng = np.random.default_rng(4)
    for k in (32, 512):
        exact = moments.exact_energy(Ph, pe, k)[0]
        w = rng.binomial(k, np.broadcast_to(pe, (200_000, len(pe))))
        Y = flows.logodds_from_counts(w, k)
        vals = np.einsum("ij,jk,ik->i", Y, Ph, Y)
        se = vals.std(ddof=1) / np.sqrt(vals.size)
        assert abs(vals.mean() - exact) < 5 * se, f"k={k}: {vals.mean()} vs exact {exact}"


def test_7_windowed_moments_equal_untruncated():
    """rig.moments windows the pmf for speed. If the window ever became too tight the
    error would be silent and small -- exactly the kind that survives review."""
    p = np.array([0.079, 0.15, 0.30, 0.483, 0.72])
    for k in (8, 64, 4096):
        for est in ("clamped_logit", "firth"):
            mu, var = moments.edge_moments(p, k, est)
            mu0, var0 = moments._moments_full(p, k, est)
            assert np.abs(mu - mu0).max() < 1e-13
            assert np.abs(var - var0).max() < 1e-12


def test_7_c1_equals_variance_plus_cross():
    """The 1/k coefficient is tr(Ph V) + 2 eps (h.b). Variance-only is the delta-method
    oracle the guard uses; this pins that the cross term is a real omission, not noise."""
    Ph, pe, lat, h, eps = _fixture()
    floor = float(lat @ Ph @ lat)
    c1 = moments.series_coefficients(Ph, pe, floor)[0]
    assert c1 == pytest.approx(moments.c1_closed(Ph, pe, eps, h), rel=1e-6)
    var_only = float(np.trace(Ph @ np.diag(1.0 / (pe * (1 - pe)))))
    assert abs(c1 / var_only - 1.0) > 1e-4, "cross term vanished: check P_h lam = eps*h"


def test_7_v2_closed_forms_match_extraction():
    """Both closed forms, against the exact moments they are meant to describe."""
    ps = np.array([0.08, 0.20, 0.35, 0.50, 0.65, 0.80])
    ks = np.array([2 ** j for j in range(12, 18)], dtype=float)
    u = ks[0] / ks
    A = np.column_stack([u ** j for j in range(1, 5)])
    for est in ("clamped_logit", "firth"):
        VA = np.array([moments.edge_moments(ps, int(k), est)[1] for k in ks])
        got = np.linalg.lstsq(A, VA, rcond=None)[0][1] * ks[0] ** 2
        assert np.abs(got - moments.v2(ps, est)).max() < 5e-3
    assert moments.v2(np.array([0.5]), "firth")[0] == pytest.approx(0.0, abs=1e-12)


def test_7_firth_removes_the_cross_term():
    """The probe's whole diagnostic value is that it zeroes the mean bias exactly."""
    Ph, pe, lat, h, eps = _fixture()
    floor = float(lat @ Ph @ lat)
    c1_f = moments.series_coefficients(Ph, pe, floor, estimator="firth")[0]
    var_only = float(np.trace(Ph @ np.diag(1.0 / (pe * (1 - pe)))))
    assert c1_f == pytest.approx(var_only, rel=1e-6)
