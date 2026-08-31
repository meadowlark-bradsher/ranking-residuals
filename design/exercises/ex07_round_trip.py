"""Exercise 7 — does the pipeline reproduce what the rig put in?

Everything before this exercise reads a flow the rig hands the instrument
directly. Real judge data does not arrive as a flow; it arrives as rows of
(winner, loser). So the rig emits a judgment log, feeds it back through
`analyze_comparisons`, and checks that the (g,c,h) survives the trip.

Three emission paths, and they are not interchangeable (spec 10, Delta B):
  counts     replay the generator's own win counts    -- exact
  sign       R rows all one way, giving +-log(2R-1)   -- exact up to a scale
  magnitude  round(k * sigmoid(Y)) rows               -- exact only as k -> inf

Run:  python design/exercises/ex07_round_trip.py
Spec: 8.10, 10.  Related: exercise 3 (why sign is not free) and 10 (the guards).
"""

import sys
from pathlib import Path

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from rig.config import RigConfig
from rig.emit import emit_assembly
from rig.graph import assemble

GAMMA, EPS, K = 2.0, 0.2, 16
EMIT_KS = (8, 16, 32, 64, 128, 256)


def trip(cfg, gamma=GAMMA, eps=EPS, k=K):
    a = assemble(cfg, gamma=gamma, eps=eps, k=k)
    log = emit_assembly(a, "ex07")
    rt = log.analyze(cfg.n_vertices, filling="empty")["fractions"]
    internal = a.analyze(filling="empty")["fractions"]
    dev = max(abs(internal[c] - rt[c]) for c in ("gradient", "curl", "harmonic"))
    return a, log, internal, rt, dev


def main():
    cfg = RigConfig().validate()

    print("Part 1 -- one config per path.\n")
    for label, c in (("counts    (noisy-BTL null, integers only)",
                      cfg.with_(n_cplx=0, mode_II="null_btl")),
                     ("sign      (rotational circle, complex only)",
                      cfg.with_(n_int=0, n_cplx=5)),
                     ("mixed     (both blocks plus the bridge)", cfg)):
        a, log, internal, rt, dev = trip(c)
        print(f"  {label}")
        print(f"    paths={log.paths}  rows={len(log)}  exact={log.exact}")
        print(f"    internal   g={internal['gradient']:.6f} c={internal['curl']:.6f} "
              f"h={internal['harmonic']:.6f}")
        print(f"    round-trip g={rt['gradient']:.6f} c={rt['curl']:.6f} "
              f"h={rt['harmonic']:.6f}")
        print(f"    max deviation {dev:.3e}   residual_max {log.residual_max:.3e}   "
              f"collapsed={log.n_collapsed} saturated={log.n_saturated}\n")

    print("Part 2 -- the mixed config as emit_k grows.")
    print("  headroom at k rows is log(2k-1): a target above it cannot be emitted.\n")
    print(f"  {'emit_k':>7} {'headroom':>9} {'rows':>7} {'deviation':>11} "
          f"{'residual_max':>13} {'saturated':>10}")
    for ek in EMIT_KS:
        _, log, _, _, dev = trip(cfg.with_(emit_k=ek))
        print(f"  {ek:7d} {np.log(2 * ek - 1):9.4f} {len(log):7d} {dev:11.3e} "
              f"{log.residual_max:13.3e} {log.n_saturated:10d}")

    print("\nRECORD")
    print("  1. Two paths reproduce the fractions to machine precision and one does")
    print("     not. Name it, and say why that is a property of the path rather than")
    print("     a bug to fix.")
    print("  2. In part 2, deviation does not fall monotonically with emit_k. Say")
    print("     which column you would actually gate a release on, and why not this one.")
    print("  3. Saturation disappears somewhere in the emit_k column. Find the")
    print("     largest |Y| in the mixed assembly and check it against the headroom.")
    print("  4. The shipped default is emit_k=64. Read the note beside it in")
    print("     rig/config.py and reproduce both figures it quotes.")


if __name__ == "__main__":
    main()
