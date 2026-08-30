"""The wrapping-aware matcher, pinned in both directions.

A prose checker has two ways to be useless and they pull opposite ways. It can
miss a wrapped phrase, which is the bug this exists to fix. Or it can join text
that the document keeps apart -- two bullets, two table rows -- and report a
phrase nobody wrote, which is worse: a false positive costs someone a morning
and teaches them to switch the check off.

So the tests below come in pairs. `finds_what_grep_misses` and its siblings pin
the first direction against the real file. `does_not_join_*` pin the second
against constructed cases, because the tree may simply not contain the adjacency
that would expose an over-eager join.

THE VACUOUS PASS IS THE THIRD FAILURE, and the one test_readme_layout learned
the hard way: a parser that silently stops recognising input passes every
assertion about what it did not find. `test_the_helper_is_actually_joining`
asserts the joining happens before anything else asserts what it produced.
"""

import pathlib

import pytest

import prose

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = ROOT / "design/specs/calibration-rig-spec.md"

PHRASE = r"orders of magnitude"

# NO ABSOLUTE LINE NUMBER IS PINNED HERE, and that is a correction rather than a
# preference. The first draft asserted the wrapped instance sat at line 592. It
# did, on the commit the draft was written against; PR #16 added a paragraph to
# 13.1 and every line below it moved down nine, so the assertion was stale
# before it was ever pushed -- the same drift this module exists to catch, in
# the module catching it. What the tests below assert instead is the RELATION
# between what a line-wise scan sees and what the helper sees, which is the
# actual claim and survives the document moving underneath it.


def _grep_lines(text, phrase=PHRASE):
    """What a line-wise scan finds: the wrapping-blind baseline."""
    return {i + 1 for i, ln in enumerate(text.splitlines()) if phrase in ln}


def _spec():
    return SPEC.read_text()


def _live_wrapped_instance():
    """The spec's wrapped phrase, or None once someone repairs it.

    THE CORRECTNESS OF THE HELPER DOES NOT DEPEND ON THIS DEFECT SURVIVING, and
    the tests are split so that it cannot. `test_finds_what_grep_misses` proves
    the property on a fixture and always runs. The three tests below add that
    the property holds against a real document with real markup, which is worth
    having and is not worth blocking a spec fix for -- stream C is editing that
    file, and a test that fails when the tree gets better is the guard people
    switch off. They skip loudly rather than failing, so the reason survives.
    """
    hits = [h for h in prose.unwrap(_spec()).finditer(PHRASE) if h.wrapped]
    return hits[0] if hits else None


_needs_live = pytest.mark.skipif(
    _live_wrapped_instance() is None,
    reason=(f"calibration-rig-spec.md no longer wraps {PHRASE!r} across a line "
            f"break. The helper is still proven on fixtures; this test's "
            f"subject is gone."),
)


def test_the_helper_is_actually_joining():
    """Guards the vacuous pass: a no-op unwrap would satisfy every test below."""
    text = "alpha beta\ngamma delta\n"
    u = prose.unwrap(text)
    assert "beta gamma" in u.text, (
        "unwrap() is not joining soft-wrapped lines, so every other assertion "
        "in this module is vacuous")


def test_finds_what_grep_misses():
    """The property, on a fixture, so it holds whatever the tree does."""
    doc = "a claim spanning six orders of\nmagnitude in one sentence.\n"
    grep_count = sum(1 for ln in doc.splitlines() if PHRASE in ln)
    hits = prose.unwrap(doc).findall(PHRASE)
    assert grep_count == 0, "fixture no longer wraps; it is testing nothing"
    assert [h.wrapped for h in hits] == [True]


@_needs_live
def test_finds_the_wrapped_instance_in_the_real_spec():
    """Same property against real markup, where the failure was actually found."""
    text = _spec()
    grep = _grep_lines(text)
    hits = prose.unwrap(text).findall(PHRASE)
    assert len(hits) == len(grep) + 1, (
        f"helper found {len(hits)}, line-wise found {len(grep)}; expected "
        f"exactly one more. A larger gap means new wrapped instances have "
        f"appeared and are worth looking at, not silencing")
    wrapped = [h for h in hits if h.wrapped]
    assert len(wrapped) == 1, f"expected one wrapped instance, got {len(wrapped)}"
    assert wrapped[0].line not in grep, (
        f"line {wrapped[0].line} is already visible to a line-wise scan, so the "
        f"helper is not adding what this test claims it adds")


@_needs_live
def test_a_match_reports_the_line_a_reader_should_open():
    """Citability is the point. A hit that cannot be located is not a finding."""
    hit = _live_wrapped_instance()
    opened = _spec().splitlines()[hit.line - 1]
    assert "six orders of" in opened, (
        f"line {hit.line} does not contain the start of the match; the offset "
        f"map is wrong, which makes every reported line number untrustworthy")


@pytest.mark.parametrize("block,why", [
    ("- six orders of\n- magnitude here\n", "two bullets are not one sentence"),
    ("| six orders of |\n| magnitude |\n", "two table rows are not one sentence"),
    ("# six orders of\nmagnitude\n", "a heading does not run into the body"),
    ("six orders of\n\nmagnitude\n", "a blank line is a hard break"),
])
def test_does_not_join_across_a_real_boundary(block, why):
    """Inventing adjacency is the mirror of the bug, not a safer version of it."""
    assert not prose.unwrap(block).findall(PHRASE), why


def test_joins_inside_a_blockquote():
    """bias-of-bias/README.md carries its status block as a quote, and it wraps."""
    u = prose.unwrap("> six orders of\n> magnitude\n")
    hits = u.findall(PHRASE)
    assert len(hits) == 1 and hits[0].wrapped, (
        "quoted prose is still prose; if this stops joining, every wrapped "
        "phrase in a status block becomes invisible again")


def test_fenced_code_is_excluded_but_does_not_shift_line_numbers():
    """A reproduction that quotes a phrase is not the document claiming it."""
    text = ("intro line\n"
            "```\n"
            "grep 'orders of magnitude' file\n"
            "```\n"
            "six orders of\n"
            "magnitude\n")
    hits = prose.unwrap(text).findall(PHRASE)
    assert len(hits) == 1, "the fenced command should not count as a claim"
    assert hits[0].line == 5, (
        f"expected the prose hit at line 5, got {hits[0].line}; blanking a "
        f"fence must preserve line numbering")
    assert len(prose.unwrap(text, skip_fences=False).findall(PHRASE)) == 2


@_needs_live
def test_wrapped_only_isolates_the_difference_from_grep():
    """What the helper adds over grep, as a number a caller can assert on."""
    text = _spec()
    only = {h.line for h in prose.wrapped_only(text, PHRASE)}
    seen_by_helper = {h.line for h in prose.unwrap(text).findall(PHRASE)}
    assert only == seen_by_helper - _grep_lines(text), (
        "wrapped_only should be exactly the hits a line-wise scan cannot see")
    assert only, "no wrapped hits, so this asserts nothing"
