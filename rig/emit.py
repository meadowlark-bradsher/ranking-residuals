"""Judgment-log emission (spec §10).

Schema: (winner, loser, position_shown, criterion, timestamp)

THE R>=2 RULE, AND WHY IT IS NOT ENOUGH. analyze_comparisons sets clamp = 1/(2k);
at k=1 that clips phat to exactly 0.5, so Y = 0 on EVERY edge. That is the §10
correction. But R>=2 alone does not save a +-1 rule pushed through the *quantized*
path: round(2 * sigmoid(1)) = 1, a 1-1 tie, which the clamp pins back to 0. So §10
prescribes THREE emission paths and they are not interchangeable:

    counts     replay the generator's own win counts            -> bit-exact
    sign       a +-1 RULE: emit all R rows one way              -> +-log(2R-1)
    magnitude  a real flow: w = round(k*sigmoid(Y))             -> residual REPORTED

Any nonzero target flow that quantizes to zero is an error, not a rounding detail.

Timestamps are a deterministic counter from a fixed epoch: same config + seed gives a
byte-identical log (§9). Never wall-clock.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import hodge
from rig.config import MIN_ROWS_PER_PAIR
from rig.flows import logodds_from_counts


class EmissionCollapse(Exception):
    """A nonzero target flow quantized to zero -- the §10 trap, one level down."""


@dataclass
class Log:
    rows: list
    residual_max: float = 0.0
    residual_l2: float = 0.0
    exact: bool = True
    paths: tuple = ()
    n_collapsed: int = 0     # edges lost to a tie by quantization (reported, not hidden)
    n_saturated: int = 0     # edges whose |target| exceeds the representable log(2k-1)

    def __len__(self):
        return len(self.rows)

    def comparisons(self):
        return [(r[0], r[1]) for r in self.rows]

    def analyze(self, n_items, filling="empty", flow="logodds"):
        """§8.10 round-trip: back through the REAL pipeline door (§6)."""
        return hodge.analyze_comparisons(n_items, self.comparisons(),
                                         filling=filling, flow=flow)


def _stamp(idx: int) -> str:
    d, rem = divmod(idx, 86400)
    h, rem = divmod(rem, 3600)
    m, sec = divmod(rem, 60)
    return f"2026-01-{1 + d:02d}T{h:02d}:{m:02d}:{sec:02d}"


def _rows_for_edge(i, j, wins_j, k, criterion, rng, counter, out):
    """wins_j rows where j wins, k-wins_j where i wins. position_shown is the item
    displayed first, randomised per row so order-effect tests later have signal."""
    for w, l in [(j, i)] * int(wins_j) + [(i, j)] * int(k - wins_j):
        first = w if rng.random() < 0.5 else l
        out.append((w, l, first, criterion, _stamp(counter[0])))
        counter[0] += 1


def _check_collapse(Y_target, wins, k, where):
    """Separate ORDINARY quantization loss from DESTRUCTION of the flow.

    An edge whose target is genuinely near a tie *should* emit a tie: at k rows the
    representable band around zero is |Y| <= log((k+1)/(k-1)), and losing an edge
    inside it is quantization loss, reported via the residual (§10).

    What must never pass silently is the flow being destroyed outright -- the §10 trap:
    a +-1 rule at k=2 rounds every edge to a 1-1 tie and the clamp pins the whole flow
    to zero. That is not rounding, it is emitting nothing.
    """
    Y_target = np.asarray(Y_target, dtype=float)
    achieved = logodds_from_counts(wins, k)
    dead = (np.abs(Y_target) > 1e-12) & (np.abs(achieved) < 1e-12)
    tgt_energy = float(Y_target @ Y_target)
    if tgt_energy > 0 and float(achieved @ achieved) == 0.0:
        band = np.log((k + 1) / (k - 1)) if k > 1 else np.inf
        raise EmissionCollapse(
            f"{where}: the ENTIRE flow quantized to zero at k={k} ({int(dead.sum())} of "
            f"{len(dead)} edges). At k rows the representable band around zero is "
            f"|Y| <= {band:.4f}, and every target falls inside it, so round(k*sigmoid(Y)) "
            f"gives a tie and the 1/(2k) clamp pins it to 0 -- the §10 trap one level "
            f"down. Use the 'sign' path for a +-1 rule, or raise emit_k."
        )
    return achieved - Y_target, int(dead.sum())


def emit_from_counts(edges, wins, k, criterion, rng) -> Log:
    """EXACT: replay the generator's own win counts (§10, noisy-BTL null)."""
    if k < MIN_ROWS_PER_PAIR:
        raise ValueError(f"k={k} < {MIN_ROWS_PER_PAIR}: the 1/(2k) clamp pins every flow to 0 (§10)")
    rows, counter = [], [0]
    for (i, j), w in zip(edges, wins):
        _rows_for_edge(i, j, w, k, criterion, rng, counter, rows)
    return Log(rows, 0.0, 0.0, exact=True, paths=("counts",))


def emit_from_signs(edges, Y_sign, R, criterion, rng) -> Log:
    """SIGN path (§10): emit R rows all one way. Every edge gets +-log(2R-1) -- a
    uniformly scaled +-1 flow, and mass fractions are scale-invariant, so (g,c,h) is
    reproduced exactly."""
    if R < MIN_ROWS_PER_PAIR + 1:
        raise ValueError(
            f"R={R}: a sign rule needs R >= {MIN_ROWS_PER_PAIR + 1}. At R=2 the emitted "
            f"flow is +-log(3) only if all rows go one way; round-tripping a +-1 target "
            f"through quantization at R=2 yields a tie and Y=0 (§10)."
        )
    Y_sign = np.asarray(Y_sign, dtype=float)
    wins = np.where(Y_sign > 0, R, 0)
    rows, counter = [], [0]
    for (i, j), w in zip(edges, wins):
        _rows_for_edge(i, j, w, R, criterion, rng, counter, rows)
    return Log(rows, 0.0, 0.0, exact=True, paths=("sign",))


def emit_from_flow(edges, Y_target, k_emit, criterion, rng) -> Log:
    """MAGNITUDE path (§10): quantized; exactness is a k_emit -> inf limit and the
    residual is REPORTED, not absorbed into a loose tolerance."""
    if k_emit < MIN_ROWS_PER_PAIR:
        raise ValueError(f"k_emit={k_emit} < {MIN_ROWS_PER_PAIR} (§10)")
    Y_target = np.asarray(Y_target, dtype=float)
    wins = np.clip(np.round(k_emit / (1.0 + np.exp(-Y_target))).astype(int), 0, k_emit)
    resid, n_dead = _check_collapse(Y_target, wins, k_emit, "emit_from_flow")
    # Headroom: the largest representable magnitude at k rows is log(2k-1). Targets
    # beyond it saturate, and that is a k_emit problem, not noise -- so it is counted.
    n_sat = int((np.abs(Y_target) > np.log(2 * k_emit - 1) + 1e-12).sum())
    rows, counter = [], [0]
    for (i, j), w in zip(edges, wins):
        _rows_for_edge(i, j, w, k_emit, criterion, rng, counter, rows)
    return Log(rows, float(np.abs(resid).max()) if resid.size else 0.0,
               float(np.linalg.norm(resid)), exact=False, paths=("magnitude",),
               n_collapsed=n_dead, n_saturated=n_sat)


def emit_assembly(assembly, criterion="rig", rng=None) -> Log:
    """Emit a whole config, dispatching per block on its encoding (§10).

    analyze_comparisons derives k per pair from that pair's own row count, so blocks
    may legitimately use different row counts in one log.

    NOTE: count-replay reproduces the UNSCALED flow, so a non-unit block_scale (§5.7)
    forces the quantized path for every block.
    """
    cfg = assembly.cfg
    rng = rng or np.random.default_rng(cfg.derive_seed("emit", criterion))
    unit_scale = all(s == 1.0 for s in cfg.block_scale)

    if not unit_scale:
        return emit_from_flow(assembly.edges, assembly.Y, cfg.emit_k, criterion, rng)

    # The sign path emits +-log(2R-1) for a +-1 target. Mass fractions are scale
    # invariant, so that is exact for a config that is ENTIRELY a sign rule -- but in a
    # MIXED config it rescales the C-C block against the others and changes the very
    # mix being measured. So sign emission is used only when it cannot distort.
    sign_only = all(b.encoding == "sign" for b in assembly.blocks.values())

    rows, resid_max, resid_l2, paths, exact, n_dead, n_sat = [], 0.0, 0.0, [], True, 0, 0
    for name, b in sorted(assembly.blocks.items()):
        tag = f"{criterion}:{name}"
        if b.encoding == "counts":
            lg = emit_from_counts(b.edges, b.wins, b.k, tag, rng)
        elif b.encoding == "sign" and sign_only:
            lg = emit_from_signs(b.edges, b.Y, max(cfg.emit_k, 3), tag, rng)
        else:
            lg = emit_from_flow(b.edges, b.Y, cfg.emit_k, tag, rng)
        rows += lg.rows
        resid_max = max(resid_max, lg.residual_max)
        resid_l2 = float(np.hypot(resid_l2, lg.residual_l2))
        n_dead += lg.n_collapsed
        n_sat += lg.n_saturated
        paths.append(b.encoding)
        exact = exact and lg.exact
    return Log(rows, resid_max, resid_l2, exact=exact, paths=tuple(paths),
               n_collapsed=n_dead, n_saturated=n_sat)


def write_jsonl(log: Log, path):
    import json
    with open(path, "w") as fh:
        for w, l, pos, crit, ts in log.rows:
            fh.write(json.dumps({"winner": int(w), "loser": int(l),
                                 "position_shown": int(pos),
                                 "criterion": crit, "timestamp": ts}) + "\n")
    return path
