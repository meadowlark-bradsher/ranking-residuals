"""Exercise 5 — recovering a floor you already know the answer to.

The rig injects a misspecification of size `eps` (spec 2.5), which puts a
budget-independent floor of exactly eps^2 into the harmonic energy. Everything
else in the measured energy decays as c/k. So the measurement is: fit
`floor + c/k`, and see whether the intercept comes back as eps^2.

This is the Epic-C measurement in miniature, one gamma, four eps.

The eps=0 row is the negative control and is not optional: an estimator that
finds a floor everywhere is not measuring a floor.

Run:  python design/exercises/ex05_floor_recovery.py
Spec: 2.5, 2.6, 7 (the c oracle), 8.5.  Claim: eps-squared-floor.
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
from rig.sweep import floor_measurement

GAMMA = 1.5
EPSES = (0.0, 0.1, 0.2, 0.4)


def main():
    # The SAME config rig.sweep.run() hands to its floor sweep -- the floor lives on
    # the pure-null pool, so the complex block is removed. Not cosmetic: derive_seed
    # hashes the whole config, so a field the measurement never reads still moves
    # which masks are drawn. Match the shipped path and exercise 4's run B agrees
    # with this row for row; change it and you are measuring a different draw.
    cfg = RigConfig().validate()
    cfg = cfg.with_(n_cplx=0, n_int=max(cfg.n_int, 12))
    print(f"gamma={GAMMA}, seeds={cfg.seeds}, reps={cfg.reps}, rho={cfg.rho}")
    print(f"k grid {list(cfg.btl.k)}\n")

    print(f"{'eps':>5} {'oracle=eps^2':>13} {'fitted floor':>13} "
          f"{'95% CI':>23} {'covers':>7} {'ratio':>7} {'c_ratio':>8} {'k needed':>9}")
    rows = []
    for eps in EPSES:
        r = floor_measurement(cfg, gamma=GAMMA, eps=eps, strict=False)
        ci = f"[{r['floor_ci_lo']:+.5f},{r['floor_ci_hi']:+.5f}]"
        ratio = r["floor_mean"] / r["floor_oracle"] if r["floor_oracle"] else float("nan")
        need = "inf" if not np.isfinite(r["fit_k_required"]) else f"{r['fit_k_required']:.0f}"
        print(f"{eps:5.1f} {r['floor_oracle']:13.5f} {r['floor_mean']:13.5f} {ci:>23} "
              f"{str(r['ci_covers_oracle']):>7} {ratio:7.4f} {r['c_ratio_median']:8.2f} "
              f"{need:>9}")
        rows.append(r)

    print("\nmonotonicity in eps^2 (spec 8.5 step 4):")
    floors = [r["floor_mean"] for r in rows]
    print(f"  fitted floors  {[round(f, 5) for f in floors]}")
    print(f"  non-decreasing: {all(b >= a for a, b in zip(floors, floors[1:]))}")

    print("\nthe negative control:")
    z = rows[0]
    print(f"  eps=0 floor {z['floor_mean']:+.6f}  CI [{z['floor_ci_lo']:+.6f}, "
          f"{z['floor_ci_hi']:+.6f}]  covers zero: {z['ci_covers_oracle']}")

    print("\nRECORD")
    print("  1. The eps>0 ratios. Are they above or below 1, and is that consistent")
    print("     across the three cells? Compare with claim `residual-across-draws`.")
    print("  2. Quote your eps=0.2 floor to a colleague. Write the sentence you")
    print("     would actually send -- then check it against spec 13.1.")
    print("  3. `k needed` is inf on the eps=0 row. Say why that is correct rather")
    print("     than a missing value, and how the eps=0 row is judged instead.")
    print("  4. c_ratio is near 1 on every row. Name one failure this rules out and")
    print("     one it does not (spec 2.6 is explicit about the second).")


if __name__ == "__main__":
    main()
