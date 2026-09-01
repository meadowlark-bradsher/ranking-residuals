"""Exercise 10 — the failures that are supposed to be loud.

Every earlier exercise produced a number. This one produces exceptions on
purpose. A rig whose guards can be walked past silently is a rig that reports a
floor from outside the window it is valid in, and spec 8.5 step 1 is explicit
that a loud failure is the correct OUTPUT there, not an obstacle to it.

Twelve deliberate misuses. Each should raise; a row reading NO ERROR is a
finding, not a pass.

Run:  python design/exercises/ex10_make_the_guards_fire.py
Spec: 2.6, 3, 5.1, 8.5 step 1, 10.  See also rig/oracle.py:RegimeViolation.
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
from rig import emit, fit, oracle
from rig.config import BTLConfig, RigConfig

RNG = lambda: np.random.default_rng(0)


def probe(label, fn):
    try:
        fn()
    except Exception as e:                                  # noqa: BLE001 -- the point
        first = str(e).replace("\n", " ").strip()
        print(f"  {label:38s} {type(e).__name__:18s} {first[:78]}")
        return True
    print(f"  {label:38s} {'NO ERROR':18s} <-- the guard did not fire")
    return False


def main():
    # A near-deterministic edge set: every p is 0.99, so at k=8 rows almost every
    # draw is unanimous and the logit saturates. This is the 2.6 saturation gate.
    p_sat = np.full(10, 0.99)

    print("Twelve deliberate misuses.\n")
    print(f"  {'what was asked for':38s} {'raised':18s} message")
    fired = [
        probe("fit_k_min = 32",
              lambda: RigConfig(btl=BTLConfig(fit_k_min=32)).validate()),
        probe("fixed_mask_across_k = False",
              lambda: RigConfig(btl=BTLConfig(fixed_mask_across_k=False)).validate()),
        probe("k grid starting at 1",
              lambda: RigConfig(btl=BTLConfig(k=(1, 64, 128))).validate()),
        probe("k grid that never reaches fit_k_min",
              lambda: RigConfig(btl=BTLConfig(k=(8, 16, 32))).validate()),
        probe("emit one row per pair",
              lambda: emit.emit_from_counts([(0, 1)], [1], 1, "x", RNG())),
        probe("sign rule at R = 2",
              lambda: emit.emit_from_signs([(0, 1)], [1.0], 2, "x", RNG())),
        probe("+-1 rule down the magnitude path, k=2",
              lambda: emit.emit_from_flow([(0, 1), (1, 2), (0, 2)],
                                          np.array([1.0, 1.0, -1.0]), 2, "x", RNG())),
        probe("bridge_R = 1",
              lambda: RigConfig(bridge_R=1).validate()),
        probe("fit a window with one point in it",
              lambda: fit.fit_floor_c([8, 16, 32], [1.0, 2.0, 3.0], fit_k_min=64)),
        probe("filling='custom', no triangles given",
              lambda: hodge.triangles_for_filling([(0, 1)], "custom")),
        probe("a filling that does not exist",
              lambda: hodge.triangles_for_filling([(0, 1)], "mostly")),
        probe("fit outside the 2.6 window",
              lambda: oracle.regime_report(p_sat, 8, 0.1, np.ones(10) * 0.3, 64,
                                           strict=True)),
    ]
    print(f"\n  {sum(fired)}/{len(fired)} guards fired")

    print("\nThe same regime check with strict=False -- a report, not an exception:\n")
    rep = oracle.regime_report(p_sat, 8, 0.1, np.ones(10) * 0.3, 64, strict=False)
    for k, v in rep.items():
        print(f"  {k:18s} {v}")

    print("\nRECORD")
    print("  1. Two rows above are about the same underlying mechanism as exercise 3.")
    print("     Find them and name the mechanism.")
    print("  2. `strict` turns the last guard from an exception into a dict. Find the")
    print("     call in rig/sweep.py that passes strict=False and say why that is not")
    print("     the same thing as switching the guard off.")
    print("  3. The saturation gate fired; the mildness gate did not. Say what each")
    print("     one protects, and which end of the eps range each is about.")
    print("  4. You need a floor from a config the gate rejects. Write down what you")
    print("     would report -- spec 8.5 step 1 has an opinion about this.")


if __name__ == "__main__":
    main()
