"""Exercise 1 — where harmonic mass is allowed to live.

Reads `b1` and the (g,c,h) split of ONE flow under both fillings, on complete
complex-only graphs of growing size. The flow never changes; only the 2-skeleton
does. Everything printed here is an exact identity, so it reproduces bit-for-bit.

Run:  python design/exercises/ex01_filling_and_b1.py
Spec: sec 4 (filling convention), 8.3, 8.4.  Claims: b1-rank-formula, equal-spaced-complex.
"""

import sys
from itertools import combinations
from pathlib import Path

import os

# --- BLAS/OpenMP thread pinning: MUST precede the numpy import below -------
# Same rule as every other entry point in this tree (rig/sweep.py carries the
# measurements). It matters here for a second reason: an exercise that reports a
# runtime is reporting a number, and an unpinned one moves 11x with ambient load.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")
# ---------------------------------------------------------------------------

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import hodge
from rig.pool import complex_angles

MS = (4, 5, 6, 7, 9)


def rotational_flow(angles, edges):
    """The C-C rule of spec 2.2: a rotation on the circle, no potential behind it."""
    return np.array([np.sin(angles[j] - angles[i]) for i, j in edges])


def main():
    print("The SAME flow, read under two 2-skeletons.\n")
    print(f"{'m':>3} {'edges':>6} {'filling':>9} {'b1':>4} "
          f"{'(m-1)(m-2)/2':>13} {'gradient':>10} {'curl':>10} {'harmonic':>10}")
    for m in MS:
        edges = list(combinations(range(m), 2))
        Y = rotational_flow(complex_angles(m, "equal_spaced"), edges)
        for filling in ("empty", "observed"):
            r = hodge.analyze_flow(m, edges, Y, filling=filling)
            f = r["fractions"]
            formula = (m - 1) * (m - 2) // 2 if filling == "empty" else ""
            print(f"{m:3d} {len(edges):6d} {filling:>9} {r['b1_holes']:4d} "
                  f"{str(formula):>13} {f['gradient']:10.6f} {f['curl']:10.6f} "
                  f"{f['harmonic']:10.6f}")
        print()

    print("RECORD")
    print("  1. Does b1 on 'empty' match (m-1)(m-2)/2 at every m?")
    print("  2. What is b1 on 'observed', and why is that the same number every time?")
    print("  3. The harmonic fraction moved from 1.0 to 0.0 without the flow changing.")
    print("     Name the thing that changed, and say whether the pool became rankable.")


if __name__ == "__main__":
    main()
