"""Re-run every claim and check it against the stored evidence, within tolerance.

    python verify.py            # full check, a few minutes
    python verify.py --fast     # skip the sweep-level claims

Exit status is 0 only if every claim reproduces. A failure prints the claim, the
stored value, the fresh value, and the drift, so a reader can see whether the
conclusion moved or only the digits did.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import os

# --- BLAS/OpenMP thread pinning: MUST precede the numpy import below -------
# This workload is many small operations, not large matrix products, so extra
# threads are spawn-and-sync overhead rather than speedup. Measured on
# envelope_evaluator (identical output at every setting):
#
#     threads=1   5.2 s wall     5.1 s CPU
#     threads=8   8.9 s wall    70.1 s CPU
#     unset      29.3 s wall   312.7 s CPU   (idle machine)
#     unset     374.4 s wall  3481.8 s CPU   (load ~20-24)
#
# Unset also made every timing on a shared machine uninterpretable: the CPU
# figure moved 11x with ambient load, because oversubscribed threads spin
# rather than work. setdefault, so an explicit outer value still wins -- that
# is how the table above was measured.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")
# ---------------------------------------------------------------------------

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import generate


def flatten(v, prefix=""):
    """Reduce nested claim values to {path: number} so any shape can be compared."""
    out = {}
    if isinstance(v, dict):
        for k, x in v.items():
            out.update(flatten(x, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(v, (list, tuple)):
        for i, x in enumerate(v):
            out.update(flatten(x, f"{prefix}[{i}]"))
    elif isinstance(v, (int, float)) and not isinstance(v, bool):
        out[prefix] = float(v)
    return out


def _pair_drift(x, y, kind):
    """Drift between two numbers, with non-finite values handled explicitly.

    NaN is the shape a degenerate measurement takes -- an empty seed list, a
    division by zero, a cell with no usable data. Left to ordinary arithmetic it
    would slip through: abs(x-y) is NaN, every comparison against NaN is False,
    so the value never becomes the worst drift and the claim reports as
    reproducing. So non-finite values are compared by identity and anything else
    is an outright failure, not a small number.
    """
    fx, fy = math.isfinite(x), math.isfinite(y)
    if not (fx and fy):
        if math.isnan(x) and math.isnan(y):
            return 0.0                      # both degenerate the same way
        if x == y:
            return 0.0                      # both the same infinity
        return float("inf")
    if kind == "exact_int":
        return 0.0 if x == y else float("inf")
    if kind == "rel":
        return abs(x - y) / max(abs(x), 1e-12)
    return abs(x - y)


def drift(stored, fresh, tol):
    """Return (ok, worst_path, worst_drift, shape_mismatches) for one claim."""
    a, b = flatten(stored), flatten(fresh)
    kind, lim = tol.get("kind"), tol.get("value", 0.0)
    worst, wpath = 0.0, ""
    # Collect every path present on one side only rather than returning at the
    # first: a restructured claim should be diagnosable in one run.
    mismatched = sorted((set(a) | set(b)) - (set(a) & set(b)))
    for k in sorted(set(a) & set(b)):
        d = _pair_drift(a[k], b[k], kind)
        if d > worst:
            worst, wpath = d, k
    if mismatched:
        return False, mismatched[0], float("inf"), mismatched
    return worst <= lim, wpath, worst, []


def check_provenance(stored):
    """The index is generated, so nothing keeps it current except regeneration.

    An index that silently describes a previous claim set is exactly the
    unverified artefact this directory exists to prevent, so check it here rather
    than trusting that whoever edited generate.py also re-ran it.
    """
    path = HERE / "PROVENANCE.md"
    if not path.exists():
        print("  NOTE PROVENANCE.md missing -- run generate.py"); return
    listed = set(re.findall(r"\| `([a-z0-9-]+)` \|", path.read_text()))
    ids = set(stored["claims"])
    if listed != ids:
        miss, extra = sorted(ids - listed), sorted(listed - ids)
        print(f"  NOTE PROVENANCE.md is stale -- run generate.py"
              + (f"; missing {miss}" if miss else "")
              + (f"; lists removed {extra}" if extra else ""))


def main():
    stored = json.loads((HERE / "evidence.json").read_text())
    check_provenance(stored)
    generate.CLAIMS = {}
    cfg = generate.structural()
    generate.bridge(cfg)
    generate.emission(cfg)
    generate.estimator(cfg)
    generate.residual_mechanism(cfg)
    if "--fast" not in sys.argv:
        generate.sweeps(cfg)
        generate.residual_exact(cfg)
    fresh = generate.CLAIMS

    print(f"  stored {stored['meta']['generated']} on numpy {stored['meta']['numpy']}"
          f", commit {stored['meta']['commit']}")
    # The tolerances exist to absorb a different numpy or platform, so say when
    # that is what a reader is looking at -- otherwise drift is unattributable.
    if stored["meta"]["numpy"] != np.__version__:
        print(f"  NOTE running numpy {np.__version__}, evidence recorded on "
              f"{stored['meta']['numpy']} -- drift within tolerance may be the library, "
              f"not the code")
    print(f"  checking {len(fresh)} claims against {len(stored['claims'])} stored\n")
    print(f"  {'claim':34} {'kind':11} {'tol':>10} {'worst drift':>12}  result")
    print("  " + "-" * 78)
    bad = 0
    for cid, f in fresh.items():
        if cid not in stored["claims"]:
            print(f"  {cid:34} {'':11} {'':>10} {'':>12}  NOT STORED"); bad += 1; continue
        st = stored["claims"][cid]
        ok, path, d, mism = drift(st["value"], f["value"], st["tolerance"])
        tol = st["tolerance"]
        tl = f"{tol.get('value','exact')}"
        ds = "exact" if d == 0 else (f"{d:.3e}" if d < 1e-3 or d > 1e3 else f"{d:.5f}")
        if mism:
            note = f"SHAPE CHANGED ({len(mism)} path{'s' if len(mism) > 1 else ''}, first {mism[0]})"
        else:
            note = "ok" if ok else "DRIFTED at " + path
        print(f"  {cid:34} {st['kind']:11} {tl:>10} {ds:>12}  {note}")
        bad += (not ok)
    missing = set(stored["claims"]) - set(fresh)
    fast = "--fast" in sys.argv
    for cid in sorted(missing):
        # in --fast mode the sweep claims are deliberately not rebuilt; that is a
        # skip, not a failure. Without --fast a missing claim is a real problem.
        label = "skipped (--fast)" if fast else "NOT REGENERATED"
        print(f"  {cid:34} {'':11} {'':>10} {'':>12}  {label}")
        bad += (not fast)
    print()
    # Count the two failure modes separately. Folding missing claims into a
    # denominator that excludes them understates the result: rename one claim and
    # a full run would report 21/22 when all 22 regenerated claims reproduced.
    regenerated = len(fresh)
    failed = bad - (0 if fast else len(missing))
    print(f"  {regenerated - failed}/{regenerated} regenerated claims reproduce within tolerance")
    if missing:
        print(f"  {len(missing)} stored claim(s) "
              + ("skipped (--fast)" if fast else "NOT REGENERATED -- renamed or removed?"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
