"""Bring `manifest.json` back in step with the tree -- deliberately, per kind of drift.

    python .load-bearing/refresh.py                     # dry run: what would change
    python .load-bearing/refresh.py --relocate          # repair MOVED anchors
    python .load-bearing/refresh.py --attest <id> ...   # re-hash CHANGED members
    python .load-bearing/refresh.py --stamp             # refresh source_tree/commit/at

THE TWO PATHS ARE SEPARATE ON PURPOSE, and this is the whole design.

`--relocate` repairs anchors whose bytes are unchanged and whose line numbers
moved. Nothing was said about that code that has stopped being true, so the
repair needs no judgement and is done in bulk.

`--attest` handles anchors whose CONTENT changed, one member at a time, by name.
It prints the diff of the anchored region before writing, and it refuses when
the member's body has not been touched in the working tree -- because the
failure this whole feature has to survive is the mechanical rehash: a command
that turns every stale member green while the prose describing them goes on
describing the previous version. A manifest that is fresh by hash and wrong by
meaning is worse than a stale one, which at least announces itself.

The refusal has an escape hatch, because it has to: renaming a local inside an
anchored region changes the bytes and leaves every word of the account true.
`--unchanged "<reason>"` takes that path, and the reason goes to stdout for the
commit message rather than into the manifest -- reader-facing state is exactly
what invariant 1 keeps out of this file, and "why I did not rewrite the body" is
a fact about an edit, which is what commit messages are for.
"""

from __future__ import annotations

import argparse
import datetime
import difflib
import importlib.util
import pathlib
import subprocess
import sys

_spec = importlib.util.spec_from_file_location(
    "lb", pathlib.Path(__file__).resolve().parent / "lb.py")
lb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lb)

MODEL = "claude-opus-5"


def _head_text(path: str) -> str | None:
    """The file as of HEAD, or None if it is not tracked there."""
    try:
        return subprocess.run(["git", "show", f"HEAD:{path}"], cwd=lb.ROOT,
                              capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return None


def _dirty(path: str) -> bool:
    """Has `path` been modified relative to HEAD (staged or not)?"""
    out = subprocess.run(["git", "status", "--porcelain", "--", path], cwd=lb.ROOT,
                         capture_output=True, text=True, check=True).stdout
    return bool(out.strip())


def _body_touched(member: dict) -> bool:
    """Has this member's prose been edited in the working tree?

    `body_ref` is a file, so git answers directly. An inline `body` lives in
    manifest.json alongside everything else, so the file's dirtiness says
    nothing -- the previous value has to come out of HEAD and be compared.
    """
    if "body_ref" in member:
        return _dirty(f".load-bearing/{member['body_ref']}")
    head = _head_text(".load-bearing/manifest.json")
    if head is None:
        return True                      # nothing to compare against yet
    import json
    was = {m["id"]: m.get("body") for m in json.loads(head).get("members", [])}
    return was.get(member["id"]) != member.get("body")


def _anchor_diff(anchor: dict, new_start: int, new_end: int) -> list[str]:
    """Unified diff of the anchored region, HEAD -> working tree."""
    head = _head_text(anchor["path"])
    before = (lb.normalize(head.encode()).split("\n")[anchor["start"] - 1:anchor["end"]]
              if head is not None else [])
    after = lb.lines_of(lb.ROOT / anchor["path"])[new_start - 1:new_end]
    return list(difflib.unified_diff(
        before, after, fromfile=f"HEAD:{anchor['path']}:{anchor['start']}-{anchor['end']}",
        tofile=f"    +:{anchor['path']}:{new_start}-{new_end}", lineterm="", n=2))


def _rehash(anchor: dict, start: int, end: int) -> None:
    path = lb.ROOT / anchor["path"]
    anchor["start"], anchor["end"] = start, end
    anchor["blob"] = lb.blob_sha(path)
    anchor["range_hash"] = lb.hash_slice(lb.lines_of(path), start, end)


def _stamp(manifest: dict) -> None:
    manifest["source_tree"] = lb.git("rev-parse", "HEAD^{tree}")
    manifest["source_commit"] = lb.git("rev-parse", "HEAD")
    manifest.setdefault("generated_by", {}).update({
        "agent": "claude-code", "model": MODEL,
        "at": datetime.datetime.now(datetime.timezone.utc)
                      .replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    })


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--relocate", action="store_true",
                    help="repair anchors whose bytes are unchanged but whose lines moved")
    ap.add_argument("--attest", nargs="+", metavar="ID", default=[],
                    help="re-hash these members after their content changed")
    ap.add_argument("--unchanged", metavar="REASON",
                    help="attest without editing the body; say why")
    ap.add_argument("--stamp", action="store_true",
                    help="refresh source_tree / source_commit / generated_by.at")
    args = ap.parse_args(argv)

    manifest = lb.load()
    errors = lb.validate(manifest)
    if errors:
        print("manifest.json is invalid; fix these before refreshing:\n")
        for e in errors:
            print(f"  - {e}")
        return 1

    by_id = {m["id"]: m for m in manifest["members"]}
    rows = {r["id"]: r for r in lb.report(manifest)}
    unknown = [i for i in args.attest if i not in by_id]
    if unknown:
        print(f"no such member: {unknown}\ndeclared: {sorted(by_id)}")
        return 1

    dry = not (args.relocate or args.attest or args.stamp)
    wrote = False

    # ------------------------------------------------------------- relocate
    moved = [r for r in rows.values() if r["status"] == lb.MOVED]
    if moved:
        print(f"{len(moved)} member{'s' if len(moved) != 1 else ''} moved "
              f"(bytes intact, coordinates stale):")
        for r in moved:
            for a, cur in zip(by_id[r["id"]]["anchors"], r["anchors"]):
                if cur["status"] == lb.MOVED:
                    print(f"  {r['id']}: {a['path']} "
                          f"{a['start']}-{a['end']} -> {cur['new_start']}-{cur['new_end']}")
                    if args.relocate:
                        _rehash(a, cur["new_start"], cur["new_end"])
                        wrote = True
        if not args.relocate:
            print("  (--relocate to apply)")
        print()

    # --------------------------------------------------------------- attest
    changed = [r for r in rows.values() if r["status"] == lb.CHANGED]
    if changed and not args.attest:
        print(f"{len(changed)} member{'s' if len(changed) != 1 else ''} changed content. "
              f"Read each, update its body if the account has moved, then attest by name:")
        for r in changed:
            print(f"  python .load-bearing/refresh.py --attest {r['id']}")
        print()

    for mid in args.attest:
        r, member = rows[mid], by_id[mid]
        if r["status"] == lb.FRESH:
            print(f"{mid} is already fresh; nothing to attest.")
            return 1
        if r["status"] == lb.MOVED:
            print(f"{mid} only MOVED -- the bytes are intact and nothing it says has "
                  f"stopped being true.\n  python .load-bearing/refresh.py --relocate")
            return 1
        if r["status"] == lb.MISSING:
            print(f"{mid}: an anchored file is gone. Repoint the anchor or drop the "
                  f"member; --attest cannot invent a region.")
            return 1

        print(f"=== {mid} ===")
        for a, cur in zip(member["anchors"], r["anchors"]):
            if cur["status"] == lb.FRESH:
                continue
            start = cur.get("new_start", a["start"])
            end = cur.get("new_end", a["end"])
            diff = _anchor_diff(a, start, end)
            print("\n".join(diff) if diff else
                  f"  (no diff against HEAD for {a['path']}; new or untracked)")

        if not _body_touched(member):
            if not args.unchanged:
                print(f"\nREFUSED. {mid}'s anchored code changed and its body did not.\n"
                      f"  Read the diff above against what the member says. If the "
                      f"account has moved, edit the body and re-run.\n"
                      f"  If it genuinely still holds, say so:\n"
                      f"    python .load-bearing/refresh.py --attest {mid} "
                      f"--unchanged \"<why the account still holds>\"")
                return 1
            print(f"\nattesting with an unchanged body: {args.unchanged}")
            print("  ^ carry that into the commit message; it is not stored here")

        for a, cur in zip(member["anchors"], r["anchors"]):
            if cur["status"] != lb.FRESH:
                _rehash(a, cur.get("new_start", a["start"]), cur.get("new_end", a["end"]))
        wrote = True
        print(f"attested {mid}\n")

    if wrote or args.stamp:
        _stamp(manifest)
        lb.dump(manifest)
        print(f"wrote manifest.json (source_tree {manifest['source_tree'][:12]})")
    elif dry:
        if not moved and not changed:
            print("Nothing to refresh; every member is fresh.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
