"""Check the manifest against the working tree, and print the ordering PREP would take.

    python .load-bearing/verify.py                # validate + freshness
    python .load-bearing/verify.py --criterion correctness
    python .load-bearing/verify.py --json

Exits non-zero when the manifest is invalid or any member is not fresh. That
exit code is advisory here -- `tests/test_load_bearing.py` is what actually
gates -- but it is what a hook or a pre-push check would read, and it means the
same thing in both places because both call `lb.report`.

`--criterion` exists to make invariant 2 visible rather than merely asserted:
the ordering is a SORT of a declared `scores` field, never a computed blend, and
a reader who suspects otherwise can run it against two criteria and see the two
orderings the manifest already contains. `weights` is printed and not applied.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys

_spec = importlib.util.spec_from_file_location(
    "lb", pathlib.Path(__file__).resolve().parent / "lb.py")
lb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lb)

_MARK = {lb.FRESH: "ok  ", lb.MOVED: "MOVED", lb.CHANGED: "CHANGED", lb.MISSING: "MISSING"}

_REMEDY = {
    lb.MOVED: ("The anchored lines are intact but at new coordinates.\n"
               "    python .load-bearing/refresh.py --relocate"),
    lb.CHANGED: ("The anchored code changed, so what the member says about it may "
                 "no longer be true.\n    Read the member, edit its body if the "
                 "account has moved, then:\n"
                 "    python .load-bearing/refresh.py --attest <member-id>"),
    lb.MISSING: ("The anchored file is gone. Repoint the anchor, or drop the "
                 "member if the region no longer exists."),
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--criterion", help="print the member ordering under this criterion")
    ap.add_argument("--json", action="store_true", help="machine-readable report")
    args = ap.parse_args(argv)

    manifest = lb.load()
    errors = lb.validate(manifest)
    rows = lb.report(manifest) if not errors else []

    if args.json:
        print(json.dumps({"errors": errors, "members": rows}, indent=2))
        return 1 if errors or lb.stale(rows) else 0

    if errors:
        print(f"manifest.json is invalid ({len(errors)} problem"
              f"{'s' if len(errors) != 1 else ''}):\n")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"{manifest['contract']}  ·  {len(manifest['members'])} members  ·  "
          f"criteria: {', '.join(c['id'] for c in manifest['criteria'])}")

    # Informational only. Invariant 6: source_tree is the whole-snapshot marker
    # and range_hash is the freshness question, so a moved tree is a note and
    # never a refusal -- it is one commit out of date the instant this file is
    # committed, which is exactly why it cannot be a gate.
    try:
        head_tree = lb.git("rev-parse", "HEAD^{tree}")
        if head_tree != manifest["source_tree"]:
            print(f"note: source_tree is {manifest['source_tree'][:12]}, HEAD tree is "
                  f"{head_tree[:12]} — informational; freshness is per-member below")
    except Exception:
        pass
    print()

    for r in rows:
        print(f"  {_MARK[r['status']]:8} {r['id']}")
        for a in r["anchors"]:
            if a["status"] != lb.FRESH:
                print(f"           {a['path']}:{a['start']}-{a['end']} — {a['detail']}")

    covered = lb.anchored_paths(manifest)
    print(f"\nanchored files ({len(covered)}) — THIS IS THE WHOLE COVERAGE SURFACE;")
    print("a path named only in a body, rationale or metadata is not checked:")
    for path, ids in sorted(covered.items()):
        print(f"  {path}  ← {', '.join(sorted(set(ids)))}")

    bad = lb.stale(rows)
    if not bad:
        print(f"\nAll {len(rows)} members fresh.")
    else:
        print(f"\n{len(bad)} of {len(rows)} members are stale:")
        for status in (lb.MISSING, lb.CHANGED, lb.MOVED):
            hit = [r["id"] for r in bad if r["status"] == status]
            if hit:
                print(f"\n  {status.upper()}: {', '.join(hit)}\n    {_REMEDY[status]}")

    if args.criterion:
        cid = args.criterion
        declared = {c["id"]: c for c in manifest["criteria"]}
        if cid not in declared:
            print(f"\nno such criterion {cid!r}; declared: {sorted(declared)}")
            return 1
        c = declared[cid]
        print(f"\nordering under {cid!r}"
              + (f"  (composite of {', '.join(c['composed_of'])}; weights "
                 f"{c.get('weights')} are informational and NOT applied)"
                 if c.get("composed_of") else ""))
        fresh_ids = {r["id"] for r in rows if r["status"] == lb.FRESH}
        if len(fresh_ids) != len(rows):
            print("  (· marks a stale member: reported, but not eligible for "
                  "selection — invariant 6)")
        ranked = sorted(manifest["members"],
                        key=lambda m: m.get("scores", {}).get(cid, 0.0), reverse=True)
        for m in ranked:
            eligible = "  " if m["id"] in fresh_ids else " ·"  # stale = not selectable
            print(f"  {eligible} {m.get('scores', {}).get(cid, 0.0):>5.2f}  {m['id']}")

    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
