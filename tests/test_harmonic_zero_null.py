"""Invariants of the harmonic-zero score test (RAN-28's score_test.py).

score_test.py is not importable as a package -- it lives beside the probes it
serves, under design/methodology/experiments/ -- so it is loaded by path here.
That is the only unusual thing about this file; everything below is an identity
the module's own docstring asserts, turned into a test that fails loudly.

These exist because the alternative way to notice a regression in the
constrained fit or the SVD complement is to re-run an 80,000-fit simulation and
eyeball RESULTS.md.
"""

import importlib.util
import itertools
from pathlib import Path

import numpy as np
import pytest

import hodge

_SRC = (Path(__file__).resolve().parents[1] / "design" / "methodology" /
        "experiments" / "harmonic-zero-null" / "score_test.py")
_spec = importlib.util.spec_from_file_location("score_test", _SRC)
st = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(st)


# Sparse enough that triangles do NOT fill every hole: b1 = 2 under 'observed'
# and 4 under 'empty', with 2 two-cells present. A denser mask closes the holes
# and b1 goes to 0, which is a different (and refused) case -- see the b1 = 0 test.
N, P_EDGE, GRAPH_SEED = 9, 0.35, 1


def _graph(n=N, p=P_EDGE, s=GRAPH_SEED):
    rng = np.random.default_rng(s)
    return [(i, j) for i, j in itertools.combinations(range(n), 2) if rng.random() < p]


def _ops(filling="observed", n=N):
    edges = _graph(n=n)
    tris = hodge.triangles_for_filling(edges, filling)
    D0, D1 = hodge.build_operators(n, edges, tris)
    return edges, D0, D1


def test_fixture_graph_actually_has_holes_under_both_fillings():
    """Guards every test below: if the mask stopped having holes they would all
    fail on the b1 = 0 refusal instead of on what they mean to check."""
    for filling in ("observed", "empty"):
        _, D0, D1 = _ops(filling)
        assert hodge.harmonic_basis(D0, D1).shape[1] >= 2
    assert _ops("observed")[2].shape[0] >= 1          # 2-cells really are present


# ---------------------------------------------------------------- the bases
@pytest.mark.parametrize("filling", ["observed", "empty"])
def test_M_is_orthonormal_and_complementary_to_H(filling):
    """S = col(M) must be the EXACT orthogonal complement of the harmonic space.

    The whole "score lands in harmonic coordinates by construction" argument is
    this identity. If M drifts off H^perp the score test is measuring something
    the certificate does not.
    """
    _, D0, D1 = _ops(filling)
    H, M = st.harmonic_zero_bases(D0, D1)
    E = D0.shape[0]
    assert H.shape[1] + M.shape[1] == E                       # dims partition R^E
    assert np.allclose(M.T @ M, np.eye(M.shape[1]), atol=1e-10)   # orthonormal
    assert np.allclose(M.T @ H, 0.0, atol=1e-10)                  # S _|_ harmonic
    assert np.allclose(H @ H.T + M @ M.T, np.eye(E), atol=1e-10)  # they span


@pytest.mark.parametrize("filling", ["observed", "empty"])
def test_harmonic_zero_df_is_b1(filling):
    """df must equal b1 -- and b1 is filling-dependent, which is the whole point."""
    _, D0, D1 = _ops(filling)
    H, _ = st.harmonic_zero_bases(D0, D1)
    assert H.shape[1] == hodge.harmonic_basis(D0, D1).shape[1]


def test_empty_filling_has_strictly_more_harmonic_directions():
    """b1 is not a property of the graph alone. With no 2-cells every non-gradient
    direction reads as harmonic, so 'empty' cannot have fewer than 'observed'."""
    _, D0o, D1o = _ops("observed")
    _, D0e, D1e = _ops("empty")
    assert st.harmonic_zero_bases(D0e, D1e)[0].shape[1] \
        > st.harmonic_zero_bases(D0o, D1o)[0].shape[1]


def test_bradley_terry_df_is_E_minus_rank_D0():
    """BT forbids everything outside im D0, so its df is E - rank(D0) = b1 + rank(D1)."""
    _, D0, D1 = _ops("observed")
    H, M = st.bradley_terry_bases(D0)
    r = np.linalg.matrix_rank(D0)
    assert H.shape[1] == D0.shape[0] - r
    assert np.allclose(M.T @ M, np.eye(M.shape[1]), atol=1e-10)
    b1 = st.harmonic_zero_bases(D0, D1)[0].shape[1]
    assert H.shape[1] == b1 + np.linalg.matrix_rank(D1)


def test_b1_zero_raises_rather_than_returning_a_zero_df_test():
    """A complete graph filled with all its triangles has no holes. A 0-df test is
    not a test; it must refuse, not return an empty statistic."""
    n = 5
    edges = list(itertools.combinations(range(n), 2))
    D0, D1 = hodge.build_operators(n, edges, hodge.triangles_for_filling(edges, "observed"))
    with pytest.raises(ValueError, match="b1 = 0"):
        st.harmonic_zero_bases(D0, D1)


# ---------------------------------------------------------------- the fit
def test_score_is_orthogonal_to_S_at_a_converged_fit():
    """The first-order condition M^T U = 0 is what makes 'in harmonic coordinates'
    literal rather than metaphorical. Measured, not assumed."""
    _, D0, D1 = _ops("observed")
    bases = st.harmonic_zero_bases(D0, D1)
    rng = np.random.default_rng(0)
    eta = D0 @ rng.normal(size=D0.shape[1]) * 0.3
    w = rng.binomial(256, st.sigmoid(eta))
    s = st.score_statistic(w, 256, bases)
    assert s["converged"] and s["usable"]
    assert s["score_off_harmonic"] < 1e-8 * max(s["score_norm"], 1.0)


def test_separated_draw_is_flagged_not_returned_as_a_statistic():
    """Every edge at w=0 drives the constrained fit to the clip. Such a draw has no
    finite MLE, so it must come back marked unusable rather than as a huge T."""
    _, D0, D1 = _ops("observed")
    bases = st.harmonic_zero_bases(D0, D1)
    w = np.zeros(D0.shape[0], dtype=int)
    s = st.score_statistic(w, 32, bases)
    assert s["separated"] and not s["usable"]


def test_statistic_mean_tracks_df_under_H0():
    """T ~ chi2(b1) means E[T] = b1. A coarse check, but it fails loudly if the
    weighting, the df, or the fit stops being what the docstring claims."""
    _, D0, D1 = _ops("observed")
    bases = st.harmonic_zero_bases(D0, D1)
    H, _ = bases
    eta = D0 @ np.linspace(-0.5, 0.5, D0.shape[1])
    p = st.sigmoid(eta)
    rng = np.random.default_rng(11)
    T = [st.score_statistic(rng.binomial(512, p), 512, bases) for _ in range(400)]
    T = np.array([t["T"] for t in T if t["usable"]])
    assert len(T) > 350
    assert T.mean() == pytest.approx(H.shape[1], rel=0.15)


# ---------------------------------------------------------------- the two links
def test_generating_link_is_not_the_fitters_clip():
    """_sigmoid clips at ETA_CLIP as a numerical guard for the IRLS iterate.
    Reusing it to DRAW data would simulate sigmoid(+-ETA_CLIP) instead of the eta
    the caller named -- silently reporting on a flow the row does not describe."""
    far = st.ETA_CLIP + 25.0
    assert st._sigmoid(far) == st._sigmoid(far + 100.0)     # clipped: insensitive
    assert st.sigmoid(far) > st._sigmoid(far)               # exact: still moving
    assert st.sigmoid(0.0) == pytest.approx(0.5)
    assert 0.0 <= st.sigmoid(-1e4) <= 1.0                   # saturates, never nan
