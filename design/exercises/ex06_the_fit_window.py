"""Exercise 6 — the floor is an intercept, so the window decides it.

`floor + c/k` is fitted by OLS. The floor is the intercept, i.e. an
extrapolation to k = infinity, and the small-k points are exactly where the
O(1/k^2) term the model omits is largest. Include them and that term is absorbed
into the intercept.

This exercise is DETERMINISTIC. It refits one stored k-sweep -- the energies of
registry claim `fit-window`, whose true floor is known to be 0.090 -- at every
window, so nothing here moves with a seed and your output should match
SOLUTIONS.md digit for digit.

Run:  python design/exercises/ex06_the_fit_window.py
Spec: 2.6, 7, 8.5 step 2.  Claim: fit-window.
"""

import json
import sys
from pathlib import Path

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")
# This file never names numpy, but rig.fit does, so the pin above still has to run
# first -- and tests/test_harness_rules.py cannot see that, because its scan looks
# for a literal numpy import. Do not remove the block on the grounds that it is
# unreferenced here.

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from rig.config import RigConfig
from rig.fit import fit_floor_c
from rig.oracle import required_fit_k_min

REGISTRY = Path(__file__).resolve().parents[1] / "methodology/evidence/evidence.json"


def main():
    claim = json.loads(REGISTRY.read_text())["claims"]["fit-window"]
    ks, energies = claim["value"]["k"], claim["value"]["energies"]
    true_floor = claim["value"]["true_floor"]
    rho = RigConfig().rho

    print(f"stored sweep from claim `fit-window`; true floor = {true_floor}")
    print(f"  k        {ks}")
    print(f"  energy   {[round(e, 4) for e in energies]}\n")

    print(f"{'fit_k_min':>10} {'pts':>4} {'floor':>10} {'ratio':>8} {'c':>9} {'r2':>10}")
    fits = {}
    for kmin in (8, 16, 32, 64, 128, 256, 512, 1024, 2048):
        try:
            r = fit_floor_c(ks, energies, fit_k_min=kmin)
        except ValueError as e:
            print(f"{kmin:10d} {'--':>4} refused: {str(e).splitlines()[0][:52]}")
            continue
        fits[kmin] = r
        print(f"{kmin:10d} {r['n_fit_points']:4d} {r['floor']:10.5f} "
              f"{r['floor'] / true_floor:7.3f}x {r['c']:9.3f} {r['r2']:10.6f}")

    print(f"\nthe registry's own two numbers, for comparison:")
    print(f"  intercept on the full grid   {claim['value']['intercept_full_grid']:.5f}"
          f"   ({claim['value']['intercept_full_grid'] / true_floor:.3f}x)")
    print(f"  intercept on k >= 64         {claim['value']['intercept_windowed']:.5f}"
          f"   ({claim['value']['intercept_windowed'] / true_floor:.3f}x)")

    print(f"\nthe DERIVED window (spec 2.6): required_fit_k_min = c / (rho * floor)")
    c64 = fits[64]["c"]
    for r_ in (1.5, 3.0):
        need = required_fit_k_min(c64, true_floor, r_)
        reach = [k for k in ks if k >= need]
        print(f"  rho={r_:<4} -> k >= {need:7.1f}   grid points at or above it: "
              f"{reach if reach else 'NONE -- this is what grid_insufficient flags'}")
    print(f"  (shipped rho is {rho}; c taken from the k>=64 fit above)")

    print("\nRECORD")
    print("  1. The ratio column is not monotone in fit_k_min. Find where it turns,")
    print("     and say what is competing with what.")
    print("  2. Rank the windows by r2. Now rank them by |ratio - 1|. Explain the")
    print("     disagreement, and say which one you would ship on.")
    print("  3. fit_k_min=2048 fits two points. Give its r2 and say what that")
    print("     number is evidence of.")
    print("  4. Two windows are in play: the shipped constant 64 and the derived 185.")
    print("     Read rig/sweep.py:floor_measurement and say which one it fits on, and")
    print("     what it does when the k grid cannot reach that window.")
    print("  5. You want a shorter run, so you propose fit_k_min=32. Give the two")
    print("     things that stop you (one is a number above, one is in rig/config.py).")


if __name__ == "__main__":
    main()
