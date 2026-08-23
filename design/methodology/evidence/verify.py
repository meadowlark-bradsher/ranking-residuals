"""Re-run every claim and check it against the stored evidence, within tolerance.

    python verify.py            # full check, a few minutes
    python verify.py --fast     # skip the sweep-level claims

Exit status is 0 only if every claim reproduces. A failure prints the claim, the
stored value, the fresh value, and the drift, so a reader can see whether the
conclusion moved or only the digits did.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

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


def drift(stored, fresh, tol):
    """Return (ok, worst_path, worst_drift) for one claim."""
    a, b = flatten(stored), flatten(fresh)
    kind, lim = tol.get("kind"), tol.get("value", 0.0)
    worst, wpath = 0.0, ""
    for k in sorted(set(a) | set(b)):
        if k not in a or k not in b:
            return False, k, float("inf")
        x, y = a[k], b[k]
        if kind == "exact_int":
            d = 0.0 if x == y else float("inf")
        elif kind == "rel":
            d = abs(x - y) / max(abs(x), 1e-12)
        elif kind == "abs_pct":
            d = abs(x - y)
        else:
            d = abs(x - y)
        if d > worst:
            worst, wpath = d, k
    return worst <= lim, wpath, worst


def main():
    stored = json.loads((HERE / "evidence.json").read_text())
    generate.CLAIMS = {}
    cfg = generate.structural()
    generate.bridge(cfg)
    generate.estimator(cfg)
    if "--fast" not in sys.argv:
        generate.sweeps(cfg)
    fresh = generate.CLAIMS

    print(f"  stored {stored['meta']['generated']} on numpy {stored['meta']['numpy']}"
          f", commit {stored['meta']['commit']}")
    print(f"  checking {len(fresh)} claims against {len(stored['claims'])} stored\n")
    print(f"  {'claim':34} {'kind':11} {'tol':>10} {'worst drift':>12}  result")
    print("  " + "-" * 78)
    bad = 0
    for cid, f in fresh.items():
        if cid not in stored["claims"]:
            print(f"  {cid:34} {'':11} {'':>10} {'':>12}  NOT STORED"); bad += 1; continue
        st = stored["claims"][cid]
        ok, path, d = drift(st["value"], f["value"], st["tolerance"])
        tol = st["tolerance"]
        tl = f"{tol.get('value','exact')}"
        ds = "exact" if d == 0 else (f"{d:.3e}" if d < 1e-3 or d > 1e3 else f"{d:.5f}")
        print(f"  {cid:34} {st['kind']:11} {tl:>10} {ds:>12}  {'ok' if ok else 'DRIFTED at ' + path}")
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
    checked = len(fresh)
    print(f"  {checked - bad}/{checked} reproduce within tolerance"
          + (f"   ({len(missing)} skipped)" if fast and missing else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
