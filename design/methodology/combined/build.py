"""Assemble the combined draft from the two source papers.

This does NOT fork their text. It extracts sections by title and interleaves
them into a single reading order, so editing a source paper and re-running this
regenerates the draft. The ordering below is the only editorial content here,
and it is the thing to argue with.

Rationale for the order: the analytic material answers "what is forced?" and the
methodology answers "what did we measure?", so the forcing arguments are placed
immediately after the setting they constrain, and the measurements that confirm
them immediately after the constructions they test.
"""
import re
from pathlib import Path

HERE = Path(__file__).parent
METH = HERE.parent / "calibration-methodology.tex"
BRIDGE = HERE.parent / "bridge-invariance.tex"


def sections(path):
    """Split a document body into {title: latex}, preserving order."""
    s = path.read_text()
    body = s[s.index(r"\begin{document}"):s.index(r"\begin{thebibliography}")]
    body = re.sub(r"\\maketitle|\\begin\{document\}", "", body)
    body = re.sub(r"\\begin\{abstract\}.*?\\end\{abstract\}", "", body, flags=re.S)
    parts = re.split(r"(?m)^\\section\{", body)
    out = {}
    for p in parts[1:]:
        title, rest = p.split("}", 1)
        out[title] = rest
    return out


M, B = sections(METH), sections(BRIDGE)

# (source, section title, optional editorial note printed before the section)
ORDER = [
    (M, "The problem", None),
    (M, "Setting and conventions", None),
    (B, "Setting",
     "The next two sections introduce the glued construction and establish what "
     "it forces, before any measurement is taken."),
    (B, "Structure is forced by symmetry---except on the bridge", None),
    (M, "Known-answer construction", None),
    (B, "Bridge-invariance of the harmonic signal", None),
    (M, "The null, and why it must be injected", None),
    (M, "Estimation", None),
    (B, "The three bridge modes are three covariance sources", None),
    (B, "One identity behind the apparatus", None),
    (M, "Guard discipline", None),
    (M, "Reporting discipline", None),
    (M, "Validation protocol", None),
    (M, "Results", None),
    (B, "Numerical confirmation, and one correction to the mapping", None),
    (B, "What is purchased without experiment, and what is not", None),
    (M, "Scope: the threshold is topology-bound", None),
    (M, "What the method does not establish", None),
]

chunks = []
for src, title, note in ORDER:
    if title not in src:
        raise SystemExit(f"section not found: {title!r}")
    if note:
        chunks.append("\\begin{quote}\\small\\itshape\n%s\n\\end{quote}\n" % note)
    chunks.append("\\section{%s}%s" % (title, src[title]))

# the bridge paper cites the methodology paper; inside one document those become
# internal references, so strip the outward citations rather than leave [1] hanging
body = "\n".join(chunks)
# The bridge paper must stand alone, so it re-defines D_0, D_1, L_1 and P_h --
# all of which Part I has already given. In the combined document that paragraph
# is redundant except for the characterisation of ker L_1, which Lemma 1's proof
# uses, so it is replaced rather than dropped. The section is also retitled: it
# is not a second "Setting", it is the glued object.
body = body.replace("\\section{Setting}", "\\section{The glued construction}", 1)
body = body.replace(
    """Write $D_0\\in\\R^{E\\times V}$ for the coboundary (gradient) operator, in the
formulation of~\\cite{jiang2011}, and $D_1$ for the triangle coboundary, with the fundamental identity $D_1D_0=0$. The graph Helmholtzian is
\\[
L_1=D_0D_0^{\\top}+D_1^{\\top}D_1;
\\]
the harmonic space is $\\ker L_1=\\ker D_0^{\\top}\\cap\\ker D_1$, and $\\Ph$ is the orthogonal projector onto it. We use one standard fact repeatedly.""",
    """With $D_0$, $D_1$, $L_1$ and $\\Ph$ as in \\S\\ref{sec:problem}, we use throughout the
characterisation $\\ker L_1=\\ker D_0^{\\top}\\cap\\ker D_1$, and one standard fact.""")

body = body.replace(r"\cite[Principle 3]{bradsher2026}", "Principle~\\ref{prin:nouniversal}")
body = body.replace(r"\cite[\S3.2]{bradsher2026}", "\\S\\ref{subsec:bridgepc}")
body = body.replace(r"\cite[\S5]{bradsher2026}", "\\S\\ref{sec:estimation}")
body = body.replace(r"The calibration methodology~\cite{bradsher2026} validates",
                    "The methodology of Part~I validates")
(HERE / "combined-body.tex").write_text(body)
print(f"  wrote combined-body.tex: {len(ORDER)} sections, {len(body.splitlines())} lines")
print(f"  from methodology: {sum(1 for s,_,_ in ORDER if s is M)}   from bridge: {sum(1 for s,_,_ in ORDER if s is B)}")
