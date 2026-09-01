"""Match prose across soft line breaks, without losing the line number.

WHY THIS EXISTS. A phrase that wraps across a line break is invisible to a
line-wise `grep`, and the failure is not that the check goes quiet. On
2026-08-30 it bit four times -- `design/reports` in the README layout tree,
`half a percentage point`, `six orders of magnitude`, and one more -- and it is
live in the tree right now at `design/specs/calibration-rig-spec.md:630-631`,
where "six orders of" ends 630 and "magnitude" opens 631, inside spec 13.3's own
explanation of that failure mode.

That citation has drifted twice and this is its second correction: it was written
as 592-593, was already 614-615 by the time anyone looked again, and the spec's
v10 note pushed it to 630-631. Which is the module's own subject, one level up --
a line number in prose is an uncited number, and nothing here can check it, which
is exactly why `test_prose` pins the RELATION between a line-wise scan and this
helper rather than any absolute line. Locate it with `unwrap`, not by counting:

    prose.unwrap(SPEC.read_text()).finditer("orders of magnitude")

What the grep actually does there is the sharp part:

    grep -c "orders of magnitude" design/specs/calibration-rig-spec.md   # 5
    tr '\\n' ' ' < ... | grep -o "orders of magnitude" | wc -l           # 6

It returns 5 of 6, not 0. A zero-result grep invites suspicion -- you assume you
mistyped the pattern and look again. A partial result looks like it worked: the
hits are real, so you conclude you have seen every instance. The one you miss is
the only wrapped one, which is to say the only one a wrapping-blind tool could
ever miss. The failure mode is CONFIDENTLY INCOMPLETE, not silent, which is why
the fix is a helper rather than an instruction to grep more carefully.

That enumeration is itself the argument. The list of five was produced, by a
wrapping-blind grep, inside the analysis of wrapping-blindness, and came back one
short -- so this helper is a prerequisite for correctly SCOPING a prose check,
not merely for running one.

WHY LINE NUMBERS ARE THE HARD PART, and the reason this is not `text.replace()`.
Joining is trivial; a finding that cannot be cited is worthless. Spec 13.3's
entire content is "go and look at this exact place", so a checker that reports
"the phrase occurs somewhere in this file" would reproduce the defect it exists
to catch. Every match here carries the 1-based source line where the match
STARTS, which is the line a reader should open.

WHAT IT DOES NOT DO, stated rather than implied.

  * It does not join across a blank line, heading, fence, table row, list-item
    start, or horizontal rule. Joining everything would manufacture adjacency
    that is not in the document -- a phrase spanning two unrelated bullets would
    match -- and inventing hits is the mirror of the bug being fixed, not a
    conservative version of it.
  * It does not understand inline markup. `**six** orders of magnitude` does not
    match `six orders of magnitude`, here or in grep. Callers matching prose that
    may carry emphasis should say so in their pattern.
  * It does not resolve the semantics of a hit. It reports where a phrase is,
    not whether the sentence containing it is a claim, a quotation, or a rule
    forbidding that very phrasing -- spec 13.3 contains all three. Scoping is the
    caller's job and cannot be delegated here.
"""

from __future__ import annotations

import bisect
import re
from dataclasses import dataclass

# A line that begins a new logical line rather than continuing the previous one.
# Checked AFTER any blockquote prefix is stripped, so quoted prose (which is how
# bias-of-bias/README.md carries its status block) wraps like any other.
_BREAKS = re.compile(
    r"""^(?:
          \#{1,6}\s          # heading
        | [-*+]\s            # bullet
        | \d+[.)]\s          # ordered item
        | \|                 # table row
        | (?:[-*_]\s*){3,}$  # horizontal rule
        | >                  # a nested quote inside an already-stripped quote
    )""",
    re.VERBOSE,
)

# A line that both breaks and CLOSES: the line after it starts fresh rather than
# continuing it. A heading does not run into its body and a table row does not
# run into the paragraph below. Bullets are deliberately absent -- a wrapped
# bullet is one sentence and must still join.
_SELF_CLOSING = re.compile(
    r"""^(?:
          \#{1,6}\s          # heading
        | \|                 # table row
        | (?:[-*_]\s*){3,}$  # horizontal rule
    )""",
    re.VERBOSE,
)

_FENCE = re.compile(r"^\s*(?:```|~~~)")
_QUOTE = re.compile(r"^\s*(?:>\s?)+")


@dataclass(frozen=True)
class Hit:
    """One match, and the source line a reader should open to see it."""

    line: int
    text: str
    wrapped: bool  # the match spans a line break, so a line-wise grep misses it


class Unwrapped:
    """Prose with soft wrapping joined, plus the map back to source lines."""

    def __init__(self, text: str, joined: str, starts: list[int], lines: list[int]):
        self.source = text
        self.text = joined
        self._starts = starts  # offset in `joined` where each source line begins
        self._lines = lines  # the 1-based source line number for that offset

    def line_of(self, pos: int) -> int:
        """The 1-based source line containing offset `pos` of `self.text`."""
        if not self._starts:
            return 1
        return self._lines[bisect.bisect_right(self._starts, pos) - 1]

    def finditer(self, pattern, flags=0):
        """Every match, with its source line and whether it was wrapped."""
        for m in re.finditer(pattern, self.text, flags):
            start_line = self.line_of(m.start())
            yield Hit(
                line=start_line,
                text=m.group(0),
                wrapped=self.line_of(m.end() - 1) != start_line,
            )

    def findall(self, pattern, flags=0) -> list[Hit]:
        return list(self.finditer(pattern, flags))


def unwrap(text: str, *, skip_fences: bool = True) -> Unwrapped:
    """Join soft-wrapped prose lines, keeping every offset traceable to a line.

    `skip_fences` blanks fenced code rather than dropping it, so line numbers
    stay true. Fenced blocks are excluded by default because they hold commands
    and data -- a reproduction that quotes a forbidden phrase is not the document
    making that claim.
    """
    parts: list[str] = []
    starts: list[int] = []
    lines: list[int] = []
    offset = 0
    in_fence = False
    open_logical = False

    for i, raw in enumerate(text.splitlines()):
        lineno = i + 1

        if _FENCE.match(raw):
            in_fence = not in_fence
            open_logical = False
            continue
        if in_fence:
            if not skip_fences:
                chunk = ("\n" if open_logical else "") + raw
                starts.append(offset + (1 if open_logical else 0))
                lines.append(lineno)
                parts.append(chunk)
                offset += len(chunk)
                open_logical = False
            continue

        body = _QUOTE.sub("", raw).rstrip()
        if not body.strip():
            open_logical = False
            continue

        if open_logical and not _BREAKS.match(body):
            chunk = " " + body.lstrip()  # a soft break reads as a space
        else:
            chunk = ("\n" if parts else "") + body
        # The offset of the first real character of this source line.
        starts.append(offset + (1 if chunk[:1] in (" ", "\n") else 0))
        lines.append(lineno)
        parts.append(chunk)
        offset += len(chunk)
        open_logical = not _SELF_CLOSING.match(body)

    return Unwrapped(text, "".join(parts), starts, lines)


def wrapped_only(text: str, pattern, *, flags=0, skip_fences: bool = True) -> list[Hit]:
    """The hits a line-wise grep would miss: those spanning a line break.

    This is the difference between the two counts in the module docstring, and
    it is what a check should report when it wants to prove the helper earned
    its place rather than merely duplicating grep.
    """
    return [h for h in unwrap(text, skip_fences=skip_fences).finditer(pattern, flags)
            if h.wrapped]
