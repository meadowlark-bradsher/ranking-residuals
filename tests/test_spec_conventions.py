"""Spec claims about the spec's own structure, checked rather than proofread.

Every convention in this repo that survived got structural backing:
`make_figures.py` reads `evidence.json`, `test_source_fingerprint` pins the
fingerprint, `test_readme_layout` pins the tree. The ones that drifted were the
ones a person had to remember.

Section 13's lead-in counts its own subsections in prose. It read "Two results"
while introducing three, and was corrected by hand in `c119efb` with nothing
watching it -- so the next subsection added puts it back out of step, silently,
and the sentence keeps reading fine. It is one line of prose asserting a fact
about the document that the document can be asked.

Read through `prose.unwrap` rather than line-wise: the lead-in wraps across
three source lines, so a line-wise pattern for the sentence would match nothing
and this file would pass by finding no claim to check. That is the failure mode
`prose` exists for, and using it here is not decoration.
"""

import json
import pathlib
import re
import subprocess

import pytest

import prose

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = ROOT / "design/specs/calibration-rig-spec.md"

_WORD_TO_INT = {
    "no": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}

# "Three results from building the rig generalise past it." The count is the
# capture; the tail anchors it to this specific claim rather than any sentence
# that happens to open with a number word.
_LEAD_IN = re.compile(
    r"\b(" + "|".join(_WORD_TO_INT) + r")\s+results?\s+from\s+building\s+the\s+rig",
    re.IGNORECASE,
)

_SUBSECTION = re.compile(r"^###\s+13\.(\d+)\b", re.MULTILINE)


def test_section_13_lead_in_counts_its_own_subsections():
    """The stated count and the actual number of 13.x subsections agree."""
    text = SPEC.read_text()

    hits = prose.unwrap(text).findall(_LEAD_IN)
    assert len(hits) == 1, (
        f"expected exactly one section-13 lead-in claim, found {len(hits)}; the "
        f"pattern has stopped matching the document, so this test is vacuous "
        f"rather than passing")

    stated_word = _LEAD_IN.search(hits[0].text).group(1).lower()
    stated = _WORD_TO_INT[stated_word]
    actual = len(set(_SUBSECTION.findall(text)))

    assert stated == actual, (
        f"section 13's lead-in at calibration-rig-spec.md:{hits[0].line} says "
        f'"{stated_word}" ({stated}) but the document has {actual} 13.x '
        f"subsections. Update the sentence, or the subsection that was added "
        f"without it.")


def test_the_subsections_are_numbered_without_gaps():
    """A count only means something if 13.1..13.n is what is actually there."""
    found = sorted(int(n) for n in _SUBSECTION.findall(SPEC.read_text()))
    assert found == list(range(1, len(found) + 1)), (
        f"section 13 subsections are numbered {found}; a gap or duplicate makes "
        f"the lead-in count ambiguous")


@pytest.mark.parametrize("stated,actual,should_pass", [
    ("Three", 3, True),
    ("Two", 3, False),
])
def test_the_check_would_catch_the_drift_it_was_written_for(stated, actual, should_pass):
    """Pins the detector, not the spec: the c119efb case, both directions.

    Without this a pattern that silently stopped matching would satisfy the
    test above by finding nothing to disagree with.
    """
    doc = (f"## 13. Carried forward\n\n{stated} results from building the rig\n"
           "generalise past it.\n\n"
           + "".join(f"### 13.{i} thing\n\nbody\n\n" for i in range(1, actual + 1)))
    hits = prose.unwrap(doc).findall(_LEAD_IN)
    assert hits, "the lead-in pattern no longer matches its own fixture"
    said = _WORD_TO_INT[_LEAD_IN.search(hits[0].text).group(1).lower()]
    assert (said == len(set(_SUBSECTION.findall(doc)))) is should_pass


# ---------------------------------------------------------------- spec 13.3
#
# "A margin is reported as the two quantities being compared, each in its own
# units. Not as a ratio between them, and not as a count of orders of magnitude
# derived from that ratio." The spec asks for this check in its own words -- a
# quoted tolerance is checkable by "a reader OR A TEST" -- because the registry
# owns `residual-exact.tolerance` and owns nothing derived from it.
#
# THIS CHECK IS DELIBERATELY NARROW, AND FINDS NOTHING TODAY. Measured across
# the tree when it was written: 20 occurrences of these phrases in tracked
# prose, of which 15 are legitimate -- measured ratios, sweep ranges, error
# magnitudes ("energy changes by a factor of 155"). 13.3 governs MARGINS, a
# quantity against its trigger, not every use of the words. Narrowing to
# occurrences adjacent to a registry-owned quantity leaves 4, and all 4 are
# 13.3 quoting itself.
#
# So this is a prospective guard with low recall by choice. A prose lint whose
# first run is a screen of false positives is one that gets switched off, and
# this repo has already lost two conventions that way. Zero unexempted hits is
# still an assertion worth holding: it is the state that changes when someone
# writes the next "inside tolerance by a factor of 3.9e+05".
#
# EXEMPTIONS ARE ANNOTATED AT THE SITE, NOT LISTED HERE, matching what stream A
# shipped for `provenance-exempt:`. A list encodes section numbers and breaks
# when a section moves -- which is exactly how this module's first draft broke,
# and what RAN-35's whole coverage argument is against. A marker in the prose
# survives the move and is visible to whoever edits the line.

_MARGIN = [r"orders of magnitude", r"by a factor of"]
_EXEMPT = "margin-exempt:"

# A file that says it is generated is a build product, not authored prose: it
# cannot carry a hand-written marker, because the next regeneration drops it.
# Detected from the file's own header rather than a path list, so a new
# generated document is excluded by saying so and not by being remembered here.
_GENERATED = re.compile(r"generated (on |by |\d)|do not edit by hand", re.I)


def _registry_terms():
    """What the registry owns: its claim ids, plus the word `tolerance`."""
    reg = json.loads((ROOT / "design/methodology/evidence/evidence.json").read_text())
    return re.compile(
        r"\btolerance\b|" + "|".join(re.escape(c) for c in reg["claims"]), re.I)


def _authored_prose():
    """Tracked prose, from git rather than a glob, minus build products."""
    out = subprocess.run(["git", "ls-files", "*.md", "*.tex"], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    for rel in out.stdout.split():
        text = (ROOT / rel).read_text()
        if not _GENERATED.search("\n".join(text.splitlines()[:12])):
            yield rel, text


def _margin_hits(text):
    """Margin phrases sitting next to something the registry owns."""
    reg, lines = _registry_terms(), text.splitlines()
    u = prose.unwrap(text)
    seen = set()
    for pat in _MARGIN:
        for h in u.finditer(pat):
            if h.line in seen:
                continue
            if reg.search(" ".join(lines[max(0, h.line - 4):h.line + 3])):
                seen.add(h.line)
                yield h


def _unexempted(rel, text):
    """Hits with no `margin-exempt:` marker ON THE HIT'S OWN LINE.

    A's placement scan allows the line above as well, because a Python comment
    cannot always sit at the end of the statement it describes. Prose has no
    such constraint -- an inline `<!-- -->` is legal at the end of any line and
    renders as nothing -- so the allowance buys nothing here and costs the thing
    it was chosen to protect. Consecutive lines are the normal case in a
    paragraph, so a two-line window lets one sentence's exemption silently cover
    the next sentence's claim. That is this check's own failure mode relocated,
    which is the reason A kept its window narrow in the first place; the same
    reasoning gives a narrower answer on this input.
    """
    lines = text.splitlines()
    return [f"{rel}:{h.line}  {lines[h.line - 1].strip()[:70]}"
            for h in _margin_hits(text)
            if _EXEMPT not in lines[h.line - 1]]


def test_the_margin_scan_is_actually_reading_prose():
    """Vacuous-pass guard: a scan that reads nothing asserts nothing."""
    files = list(_authored_prose())
    assert len(files) > 10, f"only {len(files)} prose files found; the walk is broken"
    assert any(_margin_hits(t) for _, t in files), (
        "no margin phrases found anywhere, including spec 13.3's own statement "
        "of the rule -- the scan has stopped matching and every assertion below "
        "it is vacuous")


def test_no_margin_is_quoted_as_a_ratio():
    """Spec 13.3, held across authored prose."""
    offenders = [row for rel, text in _authored_prose() for row in _unexempted(rel, text)]
    assert not offenders, (
        "spec 13.3: report the two quantities being compared, not a ratio or a "
        "count of orders of magnitude derived from them. The registry owns the "
        "inputs and owns nothing derived from them.\n  "
        + "\n  ".join(offenders)
        + "\nIf an occurrence is legitimate -- quoting the rule, or a measured "
          "ratio that is not a margin -- annotate the line with "
          "'<!-- margin-exempt: why -->' rather than widening this check.")


def test_an_exemption_does_not_cover_its_neighbour():
    """Pins the two-line window, which is the whole reason A chose one."""
    doc = ("`residual-exact` tolerance discussion.\n"
           "clears it by six orders of magnitude. <!-- margin-exempt: quoting the rule -->\n"
           "and again by a factor of 3.9e+05 here.\n")
    left = _unexempted("fixture.md", doc)
    assert len(left) == 1 and ":3" in left[0], (
        f"the line-2 exemption should not reach line 3; got {left}")
