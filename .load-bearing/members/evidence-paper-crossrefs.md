# A citation into the papers names a number nobody wrote, so the number is recomputed

`cited_in` answers "if this value moves, what prose has to change", and for the
two papers it does so by number: `methodology sec 4, Observation 2`,
`bridge sec 6.1, Proposition 3`. Those numbers are LaTeX counters. Nobody writes
them; TeX assigns them at build time, in document order. Insert one environment
above an existing one and every later number in that counter shifts, silently, in
a file the registry does not read.

`tests/test_paper_crossrefs.py` recomputes them. `_ENV` matches
`\begin{<kind>}[<title>]` for the eight declared environment kinds and `_SEC`
matches `\section{` / `\subsection{` at line start; `_numbering(path)` walks both
in source order and returns `{(kind, number): title}` together with the set of
section numbers, each environment advancing its own counter, `\section`
incrementing the section counter and resetting the subsection one.

**It reads the source, never a built PDF.** That is what lets the check run with
no LaTeX toolchain in the suite, and it is the whole reason the check is cheap
enough to keep. It is also the reason the model can be wrong: there is no
comparison against TeX's own output anywhere.

The model is exact for these two documents because of two properties of their
preambles, both of which are one grep:

- Every `\newtheorem` is declared **without** a `[section]` reset — six in
  `bridge-invariance.tex` (lemma, proposition, theorem, corollary, definition,
  remark) and two in `calibration-methodology.tex` (observation, principle) — so
  each counter runs document-wide from 1 and no counter is shared with another.
- Neither paper uses a starred heading: `\section*` and `\subsection*` occur zero
  times in both, so every heading is numbered and sections count from 1.

If either property stops holding — an appendix, a starred heading, a
`\newtheorem{...}{...}[section]` — the numbering goes wrong from that point on and
nothing says so. The tests above `_numbering` would keep passing, or fail against
the wrong baseline. The anchors therefore cover the preamble blocks as well as the
function: the claim is that the model and the declarations agree, and either one
moving alone is the event worth catching.

Two checks are built on the numbering, and the difference between them is the
substance. `test_every_cited_environment_number_exists` asks only that
`Proposition 3` exists. `test_every_cited_title_matches_the_number_beside_it` asks
that the environment numbered 3 is the one the citation names, matching a
normalised substring so a citation may abbreviate and neither side needs LaTeX
escaped: `Observation 3 (non-monotone in the item count)` resolves against
`$b_1$ is non-monotone in the item count`.

Existence alone is not enough, and that is measured rather than argued. On
2026-08-31 four references were wrong at once. Two of them —
`gradient-annihilated` at `Observation 1` and `b1-non-monotone` at
`Observation 2` — were wrong by exactly one, because a new Observation had been
inserted into methodology section 2 above them. Both numbers still existed. Both
passed an existence check, and both shipped to main and sat there. A third,
`fabricator-family-invisible`, named `sec 8.4`, which does not exist and had not
for some time; its `Proposition 3` was wrong too and then became right without
anyone touching it, because a later insertion pushed that proposition from 2 to 3.

So a numbered reference must carry its environment's title, per entry rather than
by a count of how many do. A count has a floor that the convention can decay
toward, and it does not bind the next entry added — which is the case that
produced the two defects. `sec`, `fig`, table and file references are exempt:
they have no title to match against.
