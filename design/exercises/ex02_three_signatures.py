"""Exercise 2 — the two known-answer poles, and the oracle that pins them.

The rig's calibration rests on two flows whose decomposition is known in closed
form before any measurement: a value-difference flow on integers (pure gradient,
h = 0 under BOTH fillings) and a rotational flow on the unit circle (pure
harmonic on 'empty', pure curl on 'observed'). This prints both, plus the
projector oracle they are checked against.

Run:  python design/exercises/ex02_three_signatures.py
Spec: sec 7 (oracle), 8.2, 8.3.  Claims: clean-gradient-zero, equal-spaced-complex.
"""

import sys
from itertools import combinations
from pathlib import Path

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import hodge
from rig import oracle
from rig.pool import complex_angles, integer_values

N_INT = 12
N_CPLX = 5


def show(label, n, edges, Y):
    """Measured (analyze_flow, lstsq) beside the oracle (projectors, pinv).

    Spec sec 6: these are two different routes through the instrument, and sec 7
    requires the second to check the first. Agreement is the point, not the
    individual number.
    """
    print(f"\n{label}")
    print(f"  {'filling':>9} {'b1':>4} {'gradient':>12} {'curl':>12} {'harmonic':>12}"
          f" {'checks':>7} {'max|meas-oracle|':>18}")
    for filling in ("empty", "observed"):
        m = hodge.analyze_flow(n, edges, Y, filling=filling)
        o = oracle.projector_split(n, edges, Y, filling)
        dev = max(abs(m["fractions"][c] - o["fractions"][c])
                  for c in ("gradient", "curl", "harmonic"))
        f = m["fractions"]
        print(f"  {filling:>9} {m['b1_holes']:4d} {f['gradient']:12.6f} "
              f"{f['curl']:12.6f} {f['harmonic']:12.3e} "
              f"{str(m['self_checks_pass']):>7} {dev:18.3e}")


def main():
    edges_i = list(combinations(range(N_INT), 2))
    values = integer_values(N_INT)
    show("A. Integers, value-difference flow  Y[i,j] = v[j] - v[i]   (spec 2.1)",
         N_INT, edges_i, np.array([values[j] - values[i] for i, j in edges_i], float))

    edges_c = list(combinations(range(N_CPLX), 2))
    ang = complex_angles(N_CPLX, "equal_spaced")
    show("B. Unit circle, rotational flow  Y[i,j] = sin(a[j] - a[i])   (spec 2.2)",
         N_CPLX, edges_c, np.array([np.sin(ang[j] - ang[i]) for i, j in edges_c]))

    print("\n  (the harmonic column is printed in scientific notation on purpose:")
    print("   pole A's answer is machine zero, and 0.000000 would hide whether it is)")

    print("\nRECORD")
    print("  1. Pole A's harmonic reading, as an order of magnitude, under each filling.")
    print("     Is it zero, or is it small?")
    print("  2. Pole B is 'unrankable' on one filling and 'perfectly consistent curl'")
    print("     on the other. Which reading does the certificate calibrate against, and")
    print("     what does spec sec 4 require you to do about the choice?")
    print("  3. Both poles pass self_checks. Name one thing self_checks does NOT check.")


if __name__ == "__main__":
    main()
