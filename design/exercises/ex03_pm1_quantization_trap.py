"""Exercise 3 — a perfect ranking that reads as unrankable.

Takes the SAME total order as exercise 2 pole A and re-encodes it as +-1 signs.
Nothing about the order changed: every pair is still judged correctly, and the
tournament is still perfectly transitive. The harmonic reading is not zero, and
it grows with n.

This is spec 5.1, and it is the reason the rig never emits a sign flow for a
block whose magnitude is meaningful.

Run:  python design/exercises/ex03_pm1_quantization_trap.py
Spec: 5.1, 10 (flow encodings).  Claim: pm1-trap (pins n=5 and n=6).
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
from rig.pool import integer_values

NS = (3, 4, 5, 6, 7, 8, 12, 16)
ROWS_PER_PAIR = 8
GRADED_K = 64


def closed_form(n):
    """Predicted spurious harmonic fraction of the +-1 flow of a total order on K_n.

    DERIVED IN THIS EXERCISE, not taken from the registry -- the shipped claim
    `pm1-trap` pins two measured points (n=5, n=6) and states only that the mass
    is n-dependent. See SOLUTIONS.md for the derivation; the check below is what
    licenses quoting it.
    """
    return (n - 2) / (3 * n)


def main():
    print("Part 1 -- the same order, two encodings, read through analyze_flow.\n")
    print(f"{'n':>3} {'b1':>4} {'h (value-diff)':>16} {'h (+-1 signs)':>15} "
          f"{'(n-2)/(3n)':>12} {'|diff|':>10}")
    for n in NS:
        v = integer_values(n)
        edges = list(combinations(range(n), 2))
        Y_mag = np.array([v[j] - v[i] for i, j in edges], float)
        Y_pm1 = np.sign(Y_mag)
        h_mag = hodge.analyze_flow(n, edges, Y_mag, filling="empty")["fractions"]["harmonic"]
        r = hodge.analyze_flow(n, edges, Y_pm1, filling="empty")
        h_pm1 = r["fractions"]["harmonic"]
        print(f"{n:3d} {r['b1_holes']:4d} {h_mag:16.3e} {h_pm1:15.10f} "
              f"{closed_form(n):12.10f} {abs(h_pm1 - closed_form(n)):10.2e}")

    print(f"\n  limit as n -> infinity: {1/3:.10f}")

    print("\nPart 2 -- the same trap through the judgment-log door (spec 10).")
    print("  Two logs of the SAME order, decoded three ways each.\n")
    n = 6
    v = integer_values(n)

    # (a) UNANIMOUS: every pair judged the same way every time. Correct, and
    #     carries no information about how far apart the two items are.
    unanimous = []
    for i, j in combinations(range(n), 2):
        w, l = (j, i) if v[j] > v[i] else (i, j)
        unanimous += [(w, l)] * ROWS_PER_PAIR

    # (b) GRADED: the win RATE tracks the latent gap, which is what BTL means.
    #     Same winners, same tournament, same zeta -- more information.
    theta = np.linspace(-1.5, 1.5, n)
    graded = []
    for i, j in combinations(range(n), 2):
        p = 1.0 / (1.0 + np.exp(-(theta[j] - theta[i])))
        wins_j = int(round(GRADED_K * p))
        graded += [(j, i)] * wins_j + [(i, j)] * (GRADED_K - wins_j)

    for label, comps in (("(a) unanimous", unanimous), ("(b) graded win rates", graded)):
        print(f"  {label}")
        print(f"    {'flow':>9} {'gradient':>10} {'harmonic':>10} "
              f"{'total_mass':>12} {'zeta':>6}")
        for flow in ("logodds", "signed", "pm1"):
            r = hodge.analyze_comparisons(n, comps, filling="empty", flow=flow)
            print(f"    {flow:>9} {r['fractions']['gradient']:10.6f} "
                  f"{r['fractions']['harmonic']:10.6f} {r['total_mass']:12.4f} "
                  f"{r['zeta_hat']:6.1f}")
        print()

    print("RECORD")
    print("  1. Write down h at n=5 and n=6 from part 1. Compare them to claim")
    print("     `pm1-trap` in design/methodology/evidence/evidence.json.")
    print("  2. In log (a) all three encodings give the same fractions; in log (b)")
    print("     they do not. Which of the two changed, the decoder or the data?")
    print("     Then finish the sentence: 'logodds recovers magnitude only when ...'")
    print("  3. pm1's harmonic reading is identical in (a) and (b). Say what that")
    print("     tells you about where the +-1 mass comes from.")
    print("  4. zeta reads 1.0 in every row above. State, in one sentence, what a")
    print("     certificate built on zeta alone would conclude about this pool.")


if __name__ == "__main__":
    main()
