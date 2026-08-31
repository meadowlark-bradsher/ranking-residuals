"""Exercise 9 — the baseline that says "perfectly consistent" about unrankable data.

zeta (Pokharel's coefficient of consistency) counts intransitive triples. It is a
good measure of what it measures, and what it measures is triads. Harmonic mass
lives exactly where there is no triangle to look at, so a graph can be maximally
harmonic and perfectly zeta-consistent at the same time.

Both graphs below are seven vertices and one flow each. Neither involves the rig's
sampling machinery, so the whole exercise is exact.

Run:  python design/exercises/ex09_zeta_blindness.py
Spec: 8.8 (and its Delta C construction note).  Claim: zeta-blind.
"""

import sys
from pathlib import Path

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import hodge
from rig.config import RigConfig
from rig.graph import assemble

# A 4-cycle 0-1-2-3-0 (no triangle anywhere in it) beside a transitive triangle
# 4-5-6 (every triple present). Spec 8.8 Delta C: the demonstration needs MISSING
# triangles, which is why the complete circle pool is the wrong graph for it.
EDGES = [(0, 1), (0, 3), (1, 2), (2, 3), (4, 5), (4, 6), (5, 6)]
Y = np.array([1.0, -1.0, 1.0, 1.0, 1.0, 2.0, 1.0])
DIRECTED = {(1, 0), (2, 1), (3, 2), (0, 3), (5, 4), (6, 5), (6, 4)}


def main():
    print("A. 4-cycle beside a transitive triangle  (7 vertices, 7 edges)\n")
    for filling in ("empty", "observed"):
        r = hodge.analyze_flow(7, EDGES, Y, filling=filling)
        f = r["fractions"]
        print(f"  filling={filling:9s} b1={r['b1_holes']}  g={f['gradient']:.4f} "
              f"c={f['curl']:.4f} h={f['harmonic']:.4f}  mass={r['total_mass']:.1f}")
    z, o = hodge.coefficient_of_consistency(7, DIRECTED)
    print(f"  zeta={z:.4f} over {o} observable triple(s)")
    print("  -> the certificate reads h=0.40 of the energy as unrankable;")
    print("     zeta reads 1.00, its perfect score.\n")

    print("B. The bare 4-cycle on its own  (4 vertices, 4 edges)\n")
    z2, o2 = hodge.coefficient_of_consistency(4, {(1, 0), (2, 1), (3, 2), (0, 3)})
    print(f"  zeta={z2} over {o2} observable triple(s)")
    print("  -> not wrong: undefined. There is nothing for zeta to read.\n")

    print("C. The control -- where triangles DO exist, zeta is not blind at all.\n")
    cfg = RigConfig().validate().with_(n_int=0, n_cplx=5)
    a = assemble(cfg)
    print(f"  equal-spaced circle, empty filling    h={a.analyze(filling='empty')['fractions']['harmonic']:.4f}")
    print(f"  equal-spaced circle, observed filling c={a.analyze(filling='observed')['fractions']['curl']:.4f}")
    z3, o3 = hodge.coefficient_of_consistency(5, a.directed)
    print(f"  zeta={z3:.4f} over {o3} observable triples")
    print("  -> maximally INCONSISTENT, and correctly so. Same rotational rule as A's")
    print("     4-cycle; the difference is that every triple here is observable.")

    print("\nRECORD")
    print("  1. Write down A's h and zeta side by side. Compare with claim")
    print("     `zeta-blind` in the evidence registry.")
    print("  2. A's harmonic fraction is the same under both fillings, unlike every")
    print("     earlier exercise. Say which edges are responsible and why filling")
    print("     cannot touch them.")
    print("  3. Case C reads zeta=0 and case A reads zeta=1, from the same kind of")
    print("     rule. In one sentence, state the property of the GRAPH -- not the")
    print("     data -- that decides which you get.")
    print("  4. You are handed a judgment log with zeta=0.98 and told the pool is")
    print("     rankable. Name the one number you would ask for before agreeing.")


if __name__ == "__main__":
    main()
