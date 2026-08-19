"""Graph assembly: edge typing, sparsity, block composition (spec §3, §4, §5.7).

Filling is delegated to hodge.triangles_for_filling -- never reimplemented (§6).

Block scale is RAW by default (all 1.0) and per-block RMS is logged on every config,
so the per-edge energy mismatch between log-odds I-I, +-1 C-C and +-1 bridge stays
visible rather than silently moving the harmonic fraction (§5.7).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

import numpy as np

import hodge
from rig import flows
from rig.pool import complex_angles, integer_values

II, CC, IC = "ii", "cc", "ic"


def edge_type(edge, n_int: int) -> str:
    i, j = edge
    if j < n_int:
        return II
    if i >= n_int:
        return CC
    return IC


@dataclass
class Assembly:
    """One fully-realised rig config: the graph, the observed flow, and the flow the
    oracle expects. Both are needed -- §7 compares measured against expected."""

    cfg: object
    gamma: float
    eps: float
    k: int
    seed: int
    edges: list = field(default_factory=list)
    Y: np.ndarray = None            # OBSERVED flow (what the instrument reads)
    Y_expected: np.ndarray = None   # EXPECTED flow (clean limit; the §7 oracle input)
    blocks: dict = field(default_factory=dict)
    values: np.ndarray = None
    theta: np.ndarray = None
    angles: np.ndarray = None
    directed: set = field(default_factory=set)
    ii_edges: list = field(default_factory=list)

    def block_rms(self) -> dict:
        """Per-block RMS AS IT ENTERED Y -- i.e. with block_scale applied.

        §5.7 wants this logged so the per-edge energy mismatch between blocks stays
        visible in the flow that was actually measured. Reporting the pre-scale RMS
        would describe a flow the instrument never saw. The raw value is recoverable:
        rms_x / block_scale_x.
        """
        scale = dict(zip((II, CC, IC), self.cfg.block_scale))
        out = {}
        for name in (II, CC, IC):
            b = self.blocks.get(name)
            out[f"rms_{name}"] = scale[name] * b.rms() if b is not None else 0.0
            out[f"n_edges_{name}"] = len(b) if b is not None else 0
            out[f"block_scale_{name}"] = scale[name]
        return out

    def analyze(self, filling=None):
        """Read the OBSERVED flow through the instrument (§6, analyze_flow door)."""
        return hodge.analyze_flow(self.cfg.n_vertices, self.edges, self.Y,
                                  filling=filling or self.cfg.filling)


def _thin(pairs, density, rng):
    return pairs if density >= 1.0 else [e for e in pairs if rng.random() < density]


def assemble(cfg, gamma: float = 1.0, eps: float = 0.0, k: int | None = None,
             seed_tag: str = "", mask=None) -> Assembly:
    """Build one config. `mask` lets a k-sweep reuse ONE graph across all k (§2.4)."""
    n_int, n_cplx, n = cfg.n_int, cfg.n_cplx, cfg.n_vertices
    k = k or cfg.btl.k[0]
    seed = cfg.derive_seed("assemble", gamma, eps, k, seed_tag)
    rng = np.random.default_rng(seed)

    values = integer_values(n_int)
    theta = flows.latent_potential(n_int, cfg.btl, gamma, rng) if n_int else np.zeros(0)
    angles = complex_angles(n_cplx, cfg.complex_pool, rng)

    # ---- edge sets ----------------------------------------------------
    if mask is not None:
        ii_edges = list(mask)
    else:
        mrng = np.random.default_rng(cfg.derive_seed("mask", gamma, seed_tag))
        ii_edges = (flows.sample_sparse_graph(n_int, cfg.btl.p, mrng)
                    if cfg.mode_II == "null_btl"
                    else list(combinations(range(n_int), 2)))
    ii_edges = _thin(ii_edges, cfg.edge_density, rng)
    cc_edges = _thin([(i, j) for i, j in combinations(range(n_int, n), 2)],
                     cfg.edge_density, rng)
    ic_edges = _thin([(i, j) for i in range(n_int) for j in range(n_int, n)],
                     cfg.edge_density, rng)

    blocks, expected = {}, {}

    # ---- I-I block ----------------------------------------------------
    if ii_edges:
        if cfg.mode_II == "clean_gradient":
            b = flows.clean_gradient_block(values, ii_edges)
            blocks[II], expected[II] = b, b.Y.copy()
        else:
            # eps injection uses the I-I subgraph's own harmonic direction under the
            # SAME filling the measurement will use (§2.5).
            sub_tris = hodge.triangles_for_filling(ii_edges, cfg.filling)
            sD0, sD1 = hodge.build_operators(n_int, ii_edges, sub_tris)
            latent = (flows.misspecified_latent(sD0, theta, eps,
                                                flows.harmonic_unit(sD0, sD1))
                      if eps else sD0 @ theta)
            pe = 1.0 / (1.0 + np.exp(-latent))
            wins = flows.btl_counts(pe, k, rng)
            Yii = flows.logodds_from_counts(wins, k)
            directed = {(j, i) if 2 * w >= k else (i, j)
                        for (i, j), w in zip(ii_edges, wins)}
            blocks[II] = flows.Block(list(ii_edges), Yii, wins=wins, k=k,
                                     directed=directed, encoding="counts")
            expected[II] = latent          # clean limit: what k -> infinity converges to

    # ---- C-C block ----------------------------------------------------
    if cc_edges:
        b = flows.rotational_block(angles, cc_edges, n_int)
        blocks[CC], expected[CC] = b, b.Y.copy()

    # ---- I-C bridge ---------------------------------------------------
    if ic_edges:
        s_int = theta if cfg.mode_II == "null_btl" else values
        b = flows.bridge_block(ic_edges, n_int, cfg.bridge_mode, s_int,
                               cfg.bridge_gap, cfg.bridge_R, rng)
        blocks[IC] = b
        # Expected value of the bridge field: fresh coin-flips average to 0; the fixed
        # draw and the deterministic rule are their own expectation (§5.3).
        expected[IC] = np.zeros_like(b.Y) if cfg.bridge_mode == "variance_fresh" else b.Y.copy()

    # ---- concatenate in a single sorted edge order ---------------------
    scale = dict(zip((II, CC, IC), cfg.block_scale))
    pairs = []
    for name, b in blocks.items():
        for r, e in enumerate(b.edges):
            pairs.append((e, name, r))
    pairs.sort(key=lambda t: t[0])

    edges = [e for e, _, _ in pairs]
    Y = np.array([scale[nm] * blocks[nm].Y[r] for _, nm, r in pairs])
    Y_exp = np.array([scale[nm] * expected[nm][r] for _, nm, r in pairs])
    directed = set().union(*(b.directed or set() for b in blocks.values())) if blocks else set()

    return Assembly(cfg=cfg, gamma=gamma, eps=eps, k=k, seed=seed, edges=edges,
                    Y=Y, Y_expected=Y_exp, blocks=blocks, values=values, theta=theta,
                    angles=angles, directed=directed, ii_edges=list(ii_edges))
