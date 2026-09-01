"""Reading and checking `.load-bearing/manifest.json` (contract `load-bearing/0.1`).

This module is the shared half: the CLIs (`verify.py`, `refresh.py`) and the
gate (`tests/test_load_bearing.py`) all import it, so there is exactly one
implementation of what "stale" means. It has no side effects on import and
writes nothing.

WHY A HASH AND NOT A LINE RANGE. An anchor is `path:start-end`, but line numbers
are the least stable thing about a file -- an import added at the top slides
every range below it without changing a byte of what those ranges describe. So
the range is where to look and `range_hash` is what was found there, and the two
failure modes get told apart:

    MOVED    the anchored bytes still exist in the file, at different lines.
             The manifest's coordinates are wrong; its prose is not.
    CHANGED  the anchored bytes are gone. Whatever the member says about this
             region was written about code that no longer reads that way.

That distinction is the whole point, because it is what stops the gate from
being satisfied by a rehash. `refresh.py --relocate` fixes MOVED in bulk and
needs no judgement; CHANGED is refused there and requires `--attest <id>`, one
member at a time, with the diff printed. A rule that let one command re-bless
every drifted member would be a rule that documents nothing, and this repo
already knows what happens to a convention a person merely remembers to follow.

NORMALIZATION IS PINNED HERE, and the contract's 0.1 leaves it open, so this is
a decision and not an inheritance:

  * UTF-8, with a leading BOM stripped -- an editor adding one has not changed
    the code.
  * CRLF and CR fold to LF -- a line ending is a checkout artifact, not an edit.
  * Trailing whitespace is KEPT. It is a real edit to a real byte, and this
    repo's own instrument is validated by `shasum` agreeing exactly; a hash that
    forgives whitespace is a hash that answers a slightly different question
    than the one it is being asked.
  * Every line in a slice is hashed with its terminating newline, including the
    last. A file that ends without a final newline therefore hashes the same as
    one that does, because the absence of a trailing newline at EOF is a
    property of the file, not of the region.

WHAT THIS MODULE DOES NOT DO, stated rather than implied: it never checks that
every source file is covered by some member. The manifest is a curated map and
not an inventory, exactly as the README's layout tree is, and a completeness
rule here would be the permanently-red guard `test_readme_layout` declined for
the same reason.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess

CONTRACT = "load-bearing/0.1"
CONTRACT_MAJOR = "0"

ROOT = pathlib.Path(__file__).resolve().parents[1]
LB_DIR = ROOT / ".load-bearing"
MANIFEST = LB_DIR / "manifest.json"

FRESH, MOVED, CHANGED, MISSING = "fresh", "moved", "changed", "missing"

#: Invariant 1 -- content, never state. These are the reader's business, and a
#: manifest that carries them is rejected at ingestion rather than ignored, so
#: the mistake surfaces at the producer instead of being silently dropped.
STATE_KEYS = frozenset({"reviewed", "understood", "verified", "known",
                        "status", "confidence", "mastery"})


# --------------------------------------------------------------- normalization

def normalize(raw: bytes) -> str:
    """Bytes -> text, under the pinned normalization above."""
    text = raw.decode("utf-8")
    if text.startswith("\ufeff"):
        text = text[1:]
    return text.replace("\r\n", "\n").replace("\r", "\n")


def lines_of(path: pathlib.Path) -> list[str]:
    """Text lines, without the empty string a terminating newline leaves behind.

    `"a\\nb\\n".split()` yields three elements, the last empty, which would let an
    anchor name line 3 of a two-line file and hash a phantom. Dropping exactly
    one trailing empty element -- not `rstrip` -- keeps a genuinely blank final
    line addressable.
    """
    lines = normalize(path.read_bytes()).split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def hash_slice(lines: list[str], start: int, end: int) -> str | None:
    """sha256 of lines `start..end`, 1-based inclusive. None if out of bounds.

    Out of bounds is None rather than a clamped hash: a range that runs past the
    end of a shrunken file has not "changed a little", it has stopped naming a
    region, and a clamped hash would quietly compare a prefix.
    """
    if start < 1 or end < start or end > len(lines):
        return None
    body = "".join(ln + "\n" for ln in lines[start - 1:end])
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def blob_sha(path: pathlib.Path) -> str:
    """The git blob SHA of the file, computed the way git computes it.

    Computed locally rather than shelled out to `git hash-object`, because this
    runs once per anchor and the format is three lines. Raw bytes, not
    normalized -- this is the file-level fast path, and git's own hash is what
    makes it comparable to anything else in the repo.
    """
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


# ------------------------------------------------------------------ classifying

def relocate(lines: list[str], want: str, span: int) -> tuple[int, int] | None:
    """Find `want` as a `span`-line window elsewhere in the file.

    Only equal-length windows are considered: a pure move preserves the slice
    exactly, and anything that changed length changed content, which is the
    CHANGED case and must not be repaired mechanically.
    """
    for start in range(1, len(lines) - span + 2):
        if hash_slice(lines, start, start + span - 1) == want:
            return start, start + span - 1
    return None


def classify_anchor(anchor: dict, root: pathlib.Path = ROOT) -> dict:
    """Status of one anchor against the working tree."""
    path = root / anchor["path"]
    out = {"path": anchor["path"], "start": anchor["start"], "end": anchor["end"]}
    if not path.is_file():
        return {**out, "status": MISSING, "detail": "file does not exist"}

    lines = lines_of(path)
    want = anchor["range_hash"]
    here = hash_slice(lines, anchor["start"], anchor["end"])
    if here == want:
        return {**out, "status": FRESH, "blob": blob_sha(path)}

    span = anchor["end"] - anchor["start"] + 1
    found = relocate(lines, want, span)
    if found:
        return {**out, "status": MOVED, "new_start": found[0], "new_end": found[1],
                "blob": blob_sha(path),
                "detail": f"identical {span} lines now at {found[0]}-{found[1]}"}

    if here is None:
        return {**out, "status": CHANGED, "blob": blob_sha(path),
                "detail": f"lines {anchor['start']}-{anchor['end']} run past "
                          f"the end of a {len(lines)}-line file"}
    return {**out, "status": CHANGED, "blob": blob_sha(path), "current_hash": here,
            "detail": "the anchored lines no longer hash to the recorded value"}


#: Worst-first, so a member's status is the worst of its anchors.
_SEVERITY = {FRESH: 0, MOVED: 1, CHANGED: 2, MISSING: 3}


def classify_member(member: dict, root: pathlib.Path = ROOT) -> dict:
    anchors = [classify_anchor(a, root) for a in member["anchors"]]
    worst = max(anchors, key=lambda a: _SEVERITY[a["status"]])["status"]
    return {"id": member["id"], "status": worst, "anchors": anchors}


def report(manifest: dict, root: pathlib.Path = ROOT) -> list[dict]:
    return [classify_member(m, root) for m in manifest["members"]]


def stale(rows: list[dict]) -> list[dict]:
    """Everything that is not fresh. MOVED counts: the manifest is wrong."""
    return [r for r in rows if r["status"] != FRESH]


# ------------------------------------------------------------------- validating

def _criterion_ids(manifest: dict) -> list[str]:
    return [c["id"] for c in manifest.get("criteria", [])]


def _state_keys_in(obj) -> list[str]:
    """Every STATE_KEYS key anywhere in a nested structure (invariant 1)."""
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in STATE_KEYS:
                found.append(k)
            found += _state_keys_in(v)
    elif isinstance(obj, list):
        for v in obj:
            found += _state_keys_in(v)
    return found


def validate(manifest: dict, lb_dir: pathlib.Path = LB_DIR) -> list[str]:
    """Every schema and invariant violation, as messages. Empty means valid.

    Returns a list rather than raising on the first problem: a producer fixing a
    hand-written manifest wants all of them, and a gate that reports one error
    per run trains people to fix one error per run.
    """
    errs: list[str] = []

    contract = manifest.get("contract")
    if not isinstance(contract, str) or "/" not in contract:
        errs.append(f"contract: missing or malformed ({contract!r})")
    elif contract.split("/")[1].split(".")[0] != CONTRACT_MAJOR:
        errs.append(f"contract: unknown major version {contract!r}; "
                    f"this reader speaks {CONTRACT}")

    if not isinstance(manifest.get("source_tree"), str):
        errs.append("source_tree: required, and must be a string")

    criteria = manifest.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        errs.append("criteria: required, and must hold at least one entry")
        criteria = []
    ids = _criterion_ids(manifest)
    if len(set(ids)) != len(ids):
        errs.append(f"criteria: duplicate ids in {ids}")

    for c in criteria:
        if not c.get("id"):
            errs.append("criteria: an entry has no id")
            continue
        # Invariant 3 -- a composite must declare what it is made of, and every
        # component must itself be a declared criterion, or the override path
        # the invariant exists to protect leads nowhere.
        for comp in c.get("composed_of", []):
            if comp not in ids:
                errs.append(f"criteria[{c['id']}].composed_of names {comp!r}, "
                            f"which is not a declared criterion")
        if "weights" in c and "composed_of" not in c:
            errs.append(f"criteria[{c['id']}]: weights without composed_of; "
                        f"weights are informational and belong to a composite")

    default = manifest.get("default_criterion")
    if default not in ids:
        errs.append(f"default_criterion {default!r} is not a declared criterion {ids}")

    members = manifest.get("members")
    if not isinstance(members, list) or not members:
        errs.append("members: required, and must hold at least one entry")
        members = []
    m_ids = [m.get("id") for m in members]
    if len(set(m_ids)) != len(m_ids):
        errs.append(f"members: duplicate ids in {m_ids}")

    # "Required for every criterion if present for any" -- read across the
    # manifest, which is the strict reading: partial scoring is what would let a
    # composite be authoritative while a component ordering silently ranked on
    # absent data.
    any_scored = any("scores" in m for m in members)

    for m in members:
        mid = m.get("id") or "<no id>"
        if not m.get("id"):
            errs.append("members: an entry has no id")

        has_body, has_ref = "body" in m, "body_ref" in m
        if has_body == has_ref:
            errs.append(f"members[{mid}]: exactly one of body / body_ref "
                        f"(got {'both' if has_body else 'neither'})")
        if has_ref:
            ref = lb_dir / m["body_ref"]
            if not ref.is_file():
                errs.append(f"members[{mid}].body_ref {m['body_ref']!r} does not resolve")
            elif not ref.read_text().strip():
                errs.append(f"members[{mid}].body_ref {m['body_ref']!r} is empty")

        anchors = m.get("anchors")
        if not isinstance(anchors, list) or not anchors:
            errs.append(f"members[{mid}]: anchors required, at least one")
            anchors = []
        for a in anchors:
            missing = [f for f in ("path", "start", "end", "blob", "range_hash")
                       if f not in a]
            if missing:
                errs.append(f"members[{mid}]: anchor missing {missing}")
            elif not (isinstance(a["start"], int) and isinstance(a["end"], int)
                      and 1 <= a["start"] <= a["end"]):
                errs.append(f"members[{mid}]: anchor {a['path']} has a "
                            f"non-positive or inverted range "
                            f"{a['start']}-{a['end']}")

        if any_scored:
            scores = m.get("scores")
            if not isinstance(scores, dict):
                errs.append(f"members[{mid}]: scores are present elsewhere in this "
                            f"manifest, so they are required here too")
            else:
                for cid in ids:
                    if cid not in scores:
                        errs.append(f"members[{mid}].scores is missing criterion {cid!r}")
                    elif not isinstance(scores[cid], (int, float)):
                        errs.append(f"members[{mid}].scores[{cid}] is not a number")
                for c in criteria:
                    comps = c.get("composed_of", [])
                    if c["id"] in scores and comps:
                        absent = [k for k in comps if k not in scores]
                        if absent:
                            errs.append(
                                f"members[{mid}] is scored on composite {c['id']!r} "
                                f"but not on its components {absent} (invariant 3)")

        seen_aspects = set()
        for asp in m.get("aspects", []):
            aid = asp.get("id")
            if not aid:
                errs.append(f"members[{mid}]: an aspect has no id")
            elif aid in seen_aspects:
                errs.append(f"members[{mid}]: duplicate aspect id {aid!r}")
            seen_aspects.add(aid)
            claim = asp.get("claim")
            if not isinstance(claim, str) or not claim.strip():
                errs.append(f"members[{mid}].aspects[{aid}]: claim is required, "
                            f"and must be a non-empty string")
            if "criteria" not in asp:
                errs.append(f"members[{mid}].aspects[{aid}]: criteria is required "
                            f"(use [] for 'applies under every criterion')")
            for cid in asp.get("criteria", []):
                if cid not in ids:
                    errs.append(f"members[{mid}].aspects[{aid}] names criterion "
                                f"{cid!r}, which is not declared")

        found_state = _state_keys_in(m)
        if found_state:
            errs.append(f"members[{mid}] carries reader state {sorted(set(found_state))}; "
                        f"invariant 1 rejects it at ingestion rather than ignoring it")

    return errs


# ------------------------------------------------------------------------ i/o

def load(path: pathlib.Path = MANIFEST) -> dict:
    return json.loads(path.read_text())


def dump(manifest: dict, path: pathlib.Path = MANIFEST) -> None:
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


def git(*args, root: pathlib.Path = ROOT) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True,
                          text=True, check=True).stdout.strip()
