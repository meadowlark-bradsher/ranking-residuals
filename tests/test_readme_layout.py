"""The README's layout blocks are a map of the tree. A map that lies is worse than none.

Proposed in review of PR #12, where the Layout tree had drifted far enough to
predate `design/methodology/` entirely and nothing failed. It was repaired by
hand in that PR, and two of its lines were still wrong against its own base.

The argument for a test rather than more care is structural, and the README
makes it itself two sections earlier: "a figure cannot carry a number the
evidence does not" is true because `make_figures.py` reads `evidence.json`, and
the `generate.py` rewrap is assertable because `test_source_fingerprint` checks
it. The layout tree had no such backing -- `grep -rl README tests/` returned
nothing -- so it drifted silently for four revisions.

WHY THIS IS CHECKABLE AT ALL, when prose usually is not: every non-glob entry
in those blocks is a path relative to the repo root, so the block is data
wearing a description.

WHAT IT DOES NOT CHECK, stated rather than implied: the reverse direction. A
file that exists but is unlisted does not fail, because the tree is a curated
map and not an inventory -- `rig/__init__.py` is deliberately absent, and a rule
demanding completeness would be the permanently-red guard this repo already
learned to avoid once. It catches the direction that actually drifted: entries
outliving the paths they name.

THE FAILURE MODE THIS TEST MUST NOT HAVE is passing vacuously. A README edit
that renames a fence, re-indents the tree, or drops the blocks entirely would
leave a checker that finds nothing, asserts nothing missing, and reports green
-- the exact shape of the hand-grep that missed `reports/` during review. So the
parse is asserted before its results are: no blocks, or a block with no entries,
is a failure and not a quiet pass.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"

# Every layout entry is `<indent><name>` and optionally two-or-more spaces then
# prose. Names are paths, so they are one token of path characters; a `*` makes
# it a glob, which is checked by matching rather than skipped.
_ENTRY = re.compile(r"^(?P<indent> *)(?P<name>[A-Za-z0-9_.*/-]+)(?:  +\S.*)?$")

# Description text wraps onto its own deeply-indented line (see the
# BUILD-HISTORY entry). Those carry no path and must not be read as entries.
_ENTRY_INDENTS = (0, 2)


def _layout_blocks():
    """The untagged fenced blocks that are trees, with their opening-fence line.

    Untagged is what separates them from the ```bash blocks; containing an
    unindented directory entry is what separates a tree from any other
    untagged block.

    Walked rather than regex-paired, because `^```` also matches the first three
    characters of "```bash" -- a pattern pairing fences that way silently joins
    one block's CLOSING fence to the next block's OPENING one and captures the
    prose between them. That bug shipped in the first draft of this file and the
    vacuous-pass guard below is what caught it.
    """
    lines, out, i = README.read_text().splitlines(), [], 0
    while i < len(lines):
        if not lines[i].strip().startswith("```"):
            i += 1
            continue
        info, start = lines[i].strip()[3:].strip(), i + 1
        j = start
        while j < len(lines) and lines[j].strip() != "```":
            j += 1
        body = lines[start:j]
        if not info and any(ln.rstrip().endswith("/") and not ln.startswith(" ")
                            for ln in body):
            out.append((i + 1, body))
        i = j + 1
    return out


def _entries(lines):
    """(path, is_dir) for every entry, resolved against its unindented parent.

    A block may be rooted at the repo (`hodge.py`, `rig/`, ...) or at a prefix
    (`design/methodology/` and its children). Both work the same way: an
    unindented name that ends in `/` becomes the prefix for what follows.
    """
    prefix, out = "", []
    for ln in lines:
        if not ln.strip():
            continue
        m = _ENTRY.match(ln)
        if not m or len(m.group("indent")) not in _ENTRY_INDENTS:
            continue                      # wrapped description, not an entry
        name = m.group("name")
        if not ln.startswith(" "):
            prefix = name if name.endswith("/") else ""
            out.append((name, name.endswith("/")))
        else:
            out.append((prefix + name, name.endswith("/")))
    return out


def test_the_readme_actually_has_layout_blocks_to_check():
    """Guards against the vacuous pass. Two blocks: the repo tree and design/methodology/."""
    blocks = _layout_blocks()
    assert len(blocks) >= 2, (
        f"found {len(blocks)} layout blocks in README.md; the parse has stopped "
        f"matching the document, so every other assertion here is vacuous")
    for line_no, lines in blocks:
        assert _entries(lines), f"layout block at README.md:{line_no} yielded no entries"


@pytest.mark.parametrize("line_no,lines", _layout_blocks(),
                         ids=lambda v: f"L{v}" if isinstance(v, int) else "")
def test_layout_tree_names_only_paths_that_exist(line_no, lines):
    """Every non-glob entry resolves; every glob matches at least one file."""
    missing = []
    for target, is_dir in _entries(lines):
        rel = target.rstrip("/")
        if "*" in rel:
            parent = (ROOT / rel).parent
            if not any(parent.glob(Path(rel).name)):
                missing.append(f"{target} (glob matches nothing)")
            continue
        path = ROOT / rel
        if not path.exists():
            missing.append(target)
        elif is_dir and not path.is_dir():
            missing.append(f"{target} (named as a directory, is a file)")
        elif not is_dir and path.is_dir():
            missing.append(f"{target} (named as a file, is a directory)")
    assert not missing, (
        f"README.md:{line_no} layout block names paths that do not exist: {missing}")


def test_the_check_would_have_caught_the_drift_it_was_written_for():
    """The `reports/` line PR #12 shipped against a base that had deleted it.

    Pins the detector rather than the README: a parse that silently stopped
    recognising entries would pass every test above and fail nobody.
    """
    block = ["design/",
             "  specs/              the spec",
             "  reports/            the build report"]
    resolved = dict(_entries(block))
    assert "design/reports/" in resolved, "the parser stopped resolving nested entries"
    assert not (ROOT / "design/reports").exists(), (
        "design/reports/ is back; if that is deliberate, this test's premise needs updating")
