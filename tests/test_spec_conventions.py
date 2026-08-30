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

import pathlib
import re

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
