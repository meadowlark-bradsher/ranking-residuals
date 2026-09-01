"""`cited_in` names numbered things in the papers. Nothing checked the numbers.

WHY THIS EXISTS, and it is not hypothetical three times over. `cited_in` is the
registry field that answers "if this value moves, what prose has to change", so
it carries strings like `bridge sec 6.1, Proposition 3` and
`methodology sec 4, Observation 2`. Those numbers are LaTeX counters. Nobody
writes them; TeX assigns them at build time, in document order. Insert one
environment above an existing one and every later number in that counter shifts,
silently, in a file the registry does not read.

On 2026-08-31 that happened three times in one afternoon:

  * `fabricator-family-invisible` said `bridge sec 8.4, Proposition 3`. There is
    no section 8.4 -- that subsection is 6.1 -- and it had drifted at some earlier
    restructuring and survived every review since. Its `Proposition 3` was wrong
    too, and then became right without anyone touching it, because the same day's
    insertion pushed that proposition from 2 to 3. A citation that repairs itself
    by accident is one nobody will ever re-read.
  * Adding an Observation to methodology section 2 renumbered the other two, so
    `gradient-annihilated` and `b1-non-monotone` pointed one place up the list.
    Both shipped to main and sat there.
  * Adding section 3.1 to the bridge paper broke
    `thrashing-does-not-wash-out`'s `Remark 5`. THE MECHANISM IS NOT THE OBVIOUS
    ONE, and the first draft of this docstring got it wrong: it said a Proposition
    had shifted the Remark counter. It cannot. Every `\\newtheorem` in these two
    papers declares its own counter, with no shared `[counter]` argument, so
    propositions and remarks advance independently -- checkable in the preamble,
    which is what should have been done before asserting it.

    What actually happened is duller and more useful: that subsection added a
    proposition AND a remark, and the remark is what moved the remark counter.
    The lesson is not about LaTeX's counters, it is that an edit renumbers every
    KIND of environment it introduces, including the ones that came along with the
    thing you set out to add and that you are therefore not thinking about.

The first of those is the argument for a test rather than more care: it was
introduced by a person, survived by a person, and was found only because someone
happened to compile the paper and count. The third is the argument for a test
rather than reasoning about it: the wrong mechanism gave the right answer here,
and would not have next time.

A NUMBER ALONE IS NOT ENOUGH, which the first draft of this file got wrong. It
checked only that `Proposition 3` exists. But the two methodology citations above
were broken into `Observation 1` and `Observation 2` -- numbers that still EXIST,
just naming the wrong observations -- so an existence check passes them, and did:
both were live on main when this was written. `Proposition 3` is the same failure
in the other direction, accidentally correct after an insertion that had nothing
to do with it.

So `cited_in` spells the environment's TITLE out beside the number, in
parentheses, and the number is checked against it. A title does not renumber. The
match is a normalised substring, so a citation may abbreviate a long title, and
neither side needs LaTeX escaped: `Observation 3 (non-monotone in the item count)`
resolves against `$b_1$ is non-monotone in the item count`.

WHAT IT STILL DOES NOT CHECK. A citation with no parenthetical is checked for
existence only -- the weaker guarantee, kept because not every reference has a
sensible short title and a rule nobody can satisfy is a rule that gets switched
off. It also says nothing about whether the cited passage supports the claim.
That is review, not a test.

NUMBERING IS RECOMPUTED FROM THE SOURCE, not read from a built PDF, so the check
runs with no LaTeX toolchain. That is the whole reason it is cheap enough to keep.
It mirrors what TeX does for these two documents specifically: every `\\newtheorem`
here is declared without a `[section]` reset, so each counter runs document-wide
from 1; `\\section` and `\\subsection` are all numbered (no starred forms), so
sections count from 1 and subsections reset within each. If either paper grows an
appendix, a starred heading, or a counter reset, this model stops matching and the
test must be taught the difference rather than deleted.
"""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "design/methodology/evidence/evidence.json"

# The prefix a `cited_in` string uses for each paper.
PAPERS = {
    "methodology": ROOT / "design/methodology/calibration-methodology.tex",
    "bridge": ROOT / "design/methodology/bridge-invariance.tex",
}

_ENV = re.compile(r"\\begin\{(lemma|proposition|theorem|corollary|definition|"
                  r"remark|observation|principle)\}(?:\[([^\]]*)\])?")
_SEC = re.compile(r"^\\(section|subsection)\{", re.M)

# "Observation 2", "Proposition 3", "Remark 6" -- the declaration kinds, capitalised
# as a citation would write them.
_REF = re.compile(r"\b(Lemma|Proposition|Theorem|Corollary|Definition|Remark|"
                  r"Observation|Principle)\s+(\d+)\b")
_SECREF = re.compile(r"\bsec\s+(\d+(?:\.\d+)?)\b")


def _numbering(path):
    """{(kind, number): title} and the set of section numbers, as TeX would assign them.

    One pass over the source in document order: each environment increments its
    own counter, `\\section` increments the section counter and resets the
    subsection one. Matches the two papers' preambles, which declare every
    `\\newtheorem` unreset and use no starred headings -- see the module docstring.
    """
    text = path.read_text()
    counters, envs = {}, {}
    sec, sub, sections = 0, 0, set()
    for m in sorted([*_ENV.finditer(text), *_SEC.finditer(text)],
                    key=lambda m: m.start()):
        if m.re is _SEC:
            if m.group(1) == "section":
                sec, sub = sec + 1, 0
                sections.add(str(sec))
            else:
                sub += 1
                sections.add(f"{sec}.{sub}")
            continue
        kind = m.group(1).capitalize()
        counters[kind] = counters.get(kind, 0) + 1
        envs[(kind, counters[kind])] = (m.group(2) or "").strip()
    return envs, sections


def _citations():
    """(claim id, paper, text) for every cited_in entry naming one of the papers."""
    claims = json.loads(EVIDENCE.read_text())["claims"]
    for cid, c in claims.items():
        for entry in c["cited_in"]:
            for paper in PAPERS:
                if entry.startswith(paper):
                    yield cid, paper, entry


@pytest.fixture(scope="module")
def numbering():
    return {p: _numbering(path) for p, path in PAPERS.items()}


def test_the_scan_reads_both_papers(numbering):
    """Vacuous-pass guard: a parse that finds nothing asserts nothing."""
    for paper, (envs, sections) in numbering.items():
        assert envs, f"no theorem environments parsed from {paper}; the scan is broken"
        assert sections, f"no sections parsed from {paper}; the scan is broken"
    # And the citations side, which is the half that actually varies.
    cites = list(_citations())
    assert cites, "no cited_in entry names either paper -- the prefix match is broken"
    assert any(_REF.search(e) for _, _, e in cites), (
        "no cited_in entry names a numbered environment; either they all moved to "
        "titles (good, delete this) or the reference pattern stopped matching")
    # Without this the title check below passes by finding nothing to check, which
    # is the exact shape of the bug it was added to catch.
    assert sum(1 for _, _, e in cites if _TITLE.search(e) and _REF.search(e)) >= 4, (
        "fewer than four cited_in entries carry both a number and a title, so "
        "test_every_cited_title_matches_the_number_beside_it is close to vacuous. "
        "Either the parenthetical convention was dropped or _TITLE stopped matching")


def test_every_cited_environment_number_exists(numbering):
    """`Proposition 3` in a citation resolves to a proposition that is numbered 3."""
    bad = []
    for cid, paper, entry in _citations():
        envs, _ = numbering[paper]
        for kind, num in _REF.findall(entry):
            if (kind, int(num)) not in envs:
                have = sorted(n for k, n in envs if k == kind)
                bad.append(f"{cid}: {entry!r} -> {paper} has no {kind} {num} "
                           f"(it has {kind} {have or 'none'})")
    assert not bad, (
        "cited_in names environments that do not exist. TeX numbers these in "
        "document order, so inserting one above an existing one shifts every "
        "later number in that counter -- including counters you did not touch.\n  "
        + "\n  ".join(bad))


def test_every_cited_section_number_exists(numbering):
    """`sec 6.1` in a citation resolves to a section that exists."""
    bad = []
    for cid, paper, entry in _citations():
        _, sections = numbering[paper]
        for num in _SECREF.findall(entry):
            if num not in sections:
                bad.append(f"{cid}: {entry!r} -> {paper} has no section {num}")
    assert not bad, (
        "cited_in names sections that do not exist:\n  " + "\n  ".join(bad)
        + "\nThis is how `bridge sec 8.4` survived: the section was renumbered "
          "long before anyone read the citation again.")


def _norm(s):
    """Alphanumerics only, lowercased -- so LaTeX in a title does not have to be
    escaped in a citation, and `sec` vs `\\S` vs spacing cannot cause a miss."""
    return re.sub(r"[^a-z0-9]", "", s.lower())


# The parenthetical a citation ends with, which is where the title goes.
_TITLE = re.compile(r"\(([^()]*)\)\s*$")


def test_every_cited_title_matches_the_number_beside_it(numbering):
    """`Observation 2 (The exact null...)` must be the observation actually numbered 2.

    This is the half that catches a wrong-but-existing number, which is how the
    two methodology citations broke and how an existence check let them through.
    """
    bad = []
    for cid, paper, entry in _citations():
        m = _TITLE.search(entry)
        refs = _REF.findall(entry)
        if not m or not refs:
            continue                       # existence-only; see the module docstring
        want = _norm(m.group(1))
        envs, _ = numbering[paper]
        for kind, num in refs:
            got = envs.get((kind, int(num)))
            if got is None:
                continue                   # the existence test owns this failure
            if want and want not in _norm(got):
                bad.append(f"{cid}: {entry!r} -> {paper} {kind} {num} is "
                           f"{got!r}, which does not contain that title")
    assert not bad, (
        "cited_in names a title and a number that disagree. The number is the "
        "part that drifts, so trust the title and re-read the paper:\n  "
        + "\n  ".join(bad))


@pytest.mark.parametrize("kind,number,exists", [
    ("Proposition", 2, True),      # added 2026-08-31; the reason the counter moved
    ("Proposition", 99, False),
])
def test_the_check_would_catch_the_drift_it_was_written_for(numbering, kind,
                                                            number, exists):
    """Pins the detector itself, so a parse that silently stops matching fails here.

    Without this, a regex that matched nothing would make both checks above pass
    by finding no violations -- the failure mode every guard in this suite has
    hit at least once.
    """
    envs, _ = numbering["bridge"]
    assert ((kind, number) in envs) is exists
