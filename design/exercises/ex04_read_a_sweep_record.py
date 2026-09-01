"""Exercise 4 — the same measurement at two budgets, and why one is unreadable.

Runs `rig.sweep` twice: once with --quick and once at the shipped defaults.
Both print a floor table. One of them is a result; the other is a run that
happened. Telling them apart from the numbers alone is the exercise.

Nothing is written into the repository -- both sweeps go to a temporary
directory, whose path is printed so you can read the JSONL yourself.

Run:  python design/exercises/ex04_read_a_sweep_record.py
Spec: 9 (outputs and the budget echo), 2.6 (the derived window), 8.5.
"""

import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from rig.config import RigConfig, quick
from rig.sweep import run

FIELDS = ("eps", "gamma", "floor_mean", "floor_ci_lo", "floor_ci_hi", "floor_oracle",
          "ci_covers_oracle", "c_ratio_median", "grid_insufficient",
          "fit_k_required", "seed_drop_rate")


def load_avg():
    """A runtime without its load average is not a measurement (see rig/sweep.py)."""
    try:
        return "%.2f %.2f %.2f" % os.getloadavg()
    except OSError:                                     # not available everywhere
        return "unavailable"


def show(bundle, label, elapsed):
    b = bundle["budget"]
    print(f"\n=== {label} ===")
    print(f"  budget: seeds={b['seeds']} reps={b['reps']} rho={b['rho']} "
          f"fit_k_min={b['fit_k_min']}")
    print(f"          k grid {b['k_grid']}")
    print(f"          fingerprint={b['config_fingerprint']}  quick={b['quick']}")
    print(f"  ran in {elapsed:.2f} s at load average {load_avg()}")
    print(f"\n  {'eps':>5} {'gam':>5} {'floor':>9} {'CI':>21} {'oracle':>8} "
          f"{'cov':>5} {'c_ratio':>8}  flags")
    n_cov = 0
    for r in bundle["floor"]:
        flags = []
        if r["grid_insufficient"]:
            flags.append(f"GRID SHORT (needed k>={r['fit_k_required']:.0f})")
        if r["seed_drop_rate"] > 0:
            flags.append(f"{r['seed_drop_rate']:.0%} seeds dropped")
        n_cov += bool(r["ci_covers_oracle"])
        ci = f"[{r['floor_ci_lo']:+.5f},{r['floor_ci_hi']:+.5f}]"
        print(f"  {r['eps']:>5} {r['gamma']:>5} {r['floor_mean']:9.5f} {ci:>21} "
              f"{r['floor_oracle']:8.5f} {str(r['ci_covers_oracle']):>5} "
              f"{r['c_ratio_median']:8.2f}  {'; '.join(flags)}")
    widths = [r["floor_ci_hi"] - r["floor_ci_lo"] for r in bundle["floor"]]
    print(f"\n  coverage {n_cov}/{len(bundle['floor'])} cells; "
          f"median CI width {np.median(widths):.5f}")
    return n_cov, len(bundle["floor"])


def main():
    out = Path(tempfile.mkdtemp(prefix="rig-ex04-"))
    try:
        cfg = RigConfig().validate()

        t0 = time.perf_counter()
        qb = run(quick(cfg), out / "quick", is_quick=True, figures=False)
        show(qb, "A. --quick", time.perf_counter() - t0)

        t0 = time.perf_counter()
        fb = run(cfg, out / "default", is_quick=False, figures=False)
        show(fb, "B. shipped defaults", time.perf_counter() - t0)

        print("\n=== one record, in full (spec 9: every record states its budget) ===")
        rec = json.loads((out / "default" / "floor.jsonl").read_text().splitlines()[4])
        for f in FIELDS:
            print(f"  {f:20s} {rec[f]}")
        print(f"  {'budget':20s} {rec['budget']}")
        # KEPT on success, deliberately: question 3 asks you to open floor.jsonl and
        # read a field this summary does not print. Removed only on failure, where
        # there is nothing to read.
        print(f"\n  full JSONL kept at: {out}")
        print("  (delete it yourself when done -- this script does not)")
    except Exception:
        shutil.rmtree(out, ignore_errors=True)
        raise

    print("\nRECORD")
    print("  1. Run A reports covers=True on most cells. Run B reports it too.")
    print("     Give the reason A's 'True' is worth nothing, in terms of one column.")
    print("  2. Every A cell with eps>0 is GRID SHORT. Read `fit_k_required` against")
    print("     A's k grid, and say which config field you would change and why not.")
    print("  3. B drops seeds too. Find `seed_drop_rate` and say what it counts --")
    print("     then say what B's CI would mean if you read it as coming from all 64.")
    print("  4. The two runs have different `config_fingerprint`s. Say what that")
    print("     buys you that a timestamp would not.")


if __name__ == "__main__":
    main()
