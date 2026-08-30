"""Generate BEATS.md: the combined draft's argument, beat by beat.

build.py owns the reading ORDER and says that order "is the only editorial
content here, and it is the thing to argue with." This file is the argument --
what each section does for the reader, what it claims, and what carries it --
and it is keyed to ORDER so the two cannot drift. Reorder a section in build.py
and the beats reorder with it; add one without a beat, or leave a beat behind
after removing a section, and this exits loudly rather than emitting a document
that quietly disagrees with the one it describes.

ORDER is parsed out of build.py rather than imported, because importing build.py
would run the whole assembly as a side effect. The parse is asserted against
BEATS below, so a formatting change that breaks it fails here instead of
silently producing a short document.

Run: python beats.py
"""
import re
from pathlib import Path

HERE = Path(__file__).parent

# build.py retitles this one section when it lands in the combined document; the
# beat sheet describes the combined document, so it uses the combined title.
RETITLE = {("B", "Setting"): "The glued construction"}

# Act boundaries, given as the ORDER index (1-based) each act ENDS on. Acts are
# grouping for the reader, not structure in the document -- but where they fall
# is a claim about the argument, so they are here to be argued with too.
ACTS = [
    (2,  "Act I --- Why calibration is necessary at all"),
    (5,  "Act II --- What the construction forces before any run"),
    (11, "Act III --- The construction, the null, and the identity behind both"),
    (17, "Act IV --- The disciplines, and what they produced"),
    (19, "Act V --- Scope, and what is left open"),
]

THESIS = """The shape of every harmonic reading is available without running the
instrument; the constants are not; and the reason is the same topology-dependence
that forbids a universal threshold. The document earns that sentence by
alternating two lines of work -- what the glued construction *forces*, and what
the rig *measures* -- until they meet on one identity."""

# (source, title) -> beat. `note` records something a reader or editor should
# know about the beat that is not part of the argument itself.
BEATS = {
("M", "The problem"): dict(
    role="Establish that the certificate cannot be used as a decision procedure "
         "without a calibrated threshold, and that the threshold is not available "
         "from the mathematics.",
    claim="On finite, noisy, sparsely sampled data a genuinely rankable criterion "
          "still deposits harmonic mass. So a reading above zero is not evidence "
          "of non-rankability until you know what innocent data reads.",
    evidence="The HodgeRank decomposition and the finite-sample argument; no "
             "measurement needed yet.",
    note="Sets the whole document's problem. Everything downstream is either "
         "manufacturing the innocent reading or bounding what it transfers to."),

("M", "Setting and conventions"): dict(
    role="Fix two load-bearing choices in advance, rather than discovering them "
         "per experiment.",
    claim="Filling is a modelling choice, not a detail: which triples count as "
          "2-cells sets the curl/harmonic boundary. Under the empty filling the "
          "curl space is trivial and all non-gradient mass reads as harmonic.",
    note="This is the beat paper 2 attaches to. Its filling caveat -- that the "
         "harmonic-zero null degenerates to Bradley-Terry under `empty` -- is a "
         "consequence of exactly this convention."),

("B", "What this note establishes, and what it does not"): dict(
    role="The pivot. Announce that a prior question is about to interrupt the "
         "methodology, and say why it earns the interruption.",
    claim="Some of the rig's known answers are theorems about the construction, "
          "derivable before any measurement; others are genuinely empirical. "
          "Which is which changes what the rig's numbers are for.",
    note="build.py inserts an editorial note before this section, the only such "
         "note in the document. It exists because this is the seam a reader is "
         "most likely to experience as a non-sequitur."),

("B", "Setting"): dict(
    role="Introduce the object the forcing arguments are about.",
    claim="The union graph splits into an integer block carrying a total order, "
          "a circle block carrying none, and a bridge joining them. The bridge is "
          "where incomparability lives.",
    note="build.py strips this section's re-derivation of D_0, D_1, L_1 and P_h, "
         "which the bridge paper needs to stand alone and the combined document "
         "has already given. Only the ker L_1 characterisation survives, because "
         "Lemma 1's proof uses it."),

("B", "Structure is forced by symmetry---except on the bridge"): dict(
    role="First forcing result. Show that most of the construction had no freedom.",
    claim="The two homogeneous blocks have their Hodge type fixed by their "
          "symmetry group -- order forces a gradient, rotation forces a harmonic. "
          "The bridge is the one block symmetry does not constrain, and that "
          "absence is the entire content of 'incomparability'.",
    evidence="Proposition 1, analytic.",
    note="The payoff sentence of the whole analytic line: the bridge is a "
         "modelling choice rather than a derivation, and now it is clear why."),

("M", "Known-answer construction"): dict(
    role="Return to the rig and build the data whose answer is known.",
    claim="Two vertex populations and three edge blocks with deliberately chosen "
          "signatures, arranged so three distinct sources of harmonic mass stay "
          "separable.",
    note="Placed after the forcing arguments so the reader already knows which "
         "features of the construction were available to choose."),

("B", "Bridge-invariance of the harmonic signal"): dict(
    role="The analytic line's central theorem, delivered immediately after the "
         "construction it constrains.",
    claim="If the bridge flow is a global gradient, the harmonic energy does not "
          "depend on the bridge at all; under the empty filling it equals the "
          "full intrinsic circle harmonic energy.",
    evidence="Theorem 1, with a properness clause on the class of gradients."),

("M", "The null, and why it must be injected"): dict(
    role="The negative result that forces the rig's design. A beat the document "
         "would be dishonest without.",
    claim="The natural null -- a Bradley-Terry latent with a genuine total order "
          "on a sparse graph -- has floor exactly zero, so it cannot calibrate "
          "anything. The null has to be injected.",
    evidence="Observation: the clean-limit flow is a pure gradient."),

("M", "Estimation"): dict(
    role="State the model everything downstream fits.",
    claim="E||P_h Y||^2 = floor + c/k + O(k^-2), with the variance term "
          "predictable rather than fitted.",
    note="The two-term shape here is what Act III converges on: the bridge "
         "paper's corollary turns out to be the same identity."),

("B", "The three bridge modes are three covariance sources"): dict(
    role="Promote Theorem 1 from a first-moment statement to a second-moment one.",
    claim="The rig's three bridge modes -- fresh coin, persistent coin, "
          "deterministic surrogate -- are three covariance sources in a single "
          "formula, and the rig's whole classification reads off the second moment.",
    evidence="Corollary 1."),

("B", "One identity behind the apparatus"): dict(
    role="THE HINGE. The two lines of work meet, and the document stops being "
         "two papers.",
    claim="Corollary 1 and the rig's injected-null model are instances of one "
          "bias-plus-variance identity on the harmonic projector, because "
          "tr(P_h Sigma) = tr(P_h Sigma P_h) for the idempotent P_h.",
    note="If a reader is going to be convinced the fusion was worth doing, it "
         "happens here. Everything before this is two arguments taking turns; "
         "everything after is one."),

("M", "Guard discipline"): dict(
    role="Say how the estimator fails, before showing what it produced.",
    claim="Three rules. Preconditions are checked in closed form before fitting, "
          "because saturation is computable without sampling. And a guard may be "
          "necessary without being sufficient.",
    evidence="The saturation pre-filter E[p^k + (1-p)^k]; the misspecification "
             "catch where a plausible floor of 0.2591 against a true 0.0900 was "
             "revealed only by fitted c = 9.44 against predicted c = 70.07; and "
             "the counter-case where the same guard reads 1.01 while the floor is "
             "still 1.86x too high.",
    note="The necessary-not-sufficient pair is the strongest methodological beat "
         "in the paper: a guard that catches a real error and then demonstrably "
         "misses another."),

("M", "Reporting discipline"): dict(
    role="Second of the three generalisable failures.",
    claim="Any figure that moves with the seed ships as a distribution -- mean, "
          "standard error, and per-draw range over independent base seeds. A "
          "single run's value is a draw, not the quantity.",
    evidence="Arrived at by getting the same number wrong three times."),

("M", "Validation protocol"): dict(
    role="Show that acceptance is mechanised rather than asserted.",
    claim="Acceptance is a numbered list of claims, each with a test against the "
          "real instrument; negative controls carry equal weight.",
    note="Rescoped, and my first reading of this was wrong. 70 is still the "
         "right count for what the sentence claims -- the instrument's own "
         "acceptance suite, measured at exactly 70. The repository now runs 82, "
         "because paper 2 added a suite for a module built ON the instrument, "
         "which was never part of this acceptance. So the fix was to say which "
         "suite is meant, not to bump a number. The timing was dropped rather "
         "than restated: it could not be re-measured honestly (load average 169 "
         "on 12 cores at the time), and an unverified number is worse than none."),

("M", "Results"): dict(
    role="Deliver: the instrument reproduces every known answer.",
    claim="Every known answer recovered, and the synthetic adversarial sweep "
          "behaves as predicted.",
    evidence="Systematic floor following m(m-1)/2 exactly -- measured 0, 3, 10, "
             "21, 36 -- under the empty filling with equal spacing."),

("B", "Numerical confirmation, and one correction to the mapping"): dict(
    role="Close the analytic line honestly: the rig cannot confirm a theorem, but "
         "it can check the steps the proof calls load-bearing.",
    claim="Theorem 1 holds in a stronger form than stated, and the mode-to-"
          "implementation mapping in the earlier table needed correcting.",
    note="A beat that reports a correction to its own paper. Worth keeping "
         "visible rather than folding silently into the table it fixes."),

("B", "What is purchased without experiment, and what is not"): dict(
    role="State the analytic line's payoff as a proposition, so it can be cited.",
    claim="Shape is analytic; constants are topological. The invariance, the "
          "constant-bridge floor, and the 1/R decay are theorems of the "
          "construction; the values they take are functionals of P_h.",
    note="This is the setup for the next beat: if the constants are functionals "
         "of the projector, they cannot transfer between topologies."),

("M", "Scope: the threshold is topology-bound"): dict(
    role="The document's most consequential limit, framed as a fact about the "
         "object rather than a defect of the method.",
    claim="A null calibrated on one topology does not transfer to another. The "
          "deliverable is a procedure, not a number.",
    evidence="b_1 is non-monotone in the item count: at fixed edge retention 0.45 "
             "under the observed filling, the fraction of graphs with b_1 = 0 "
             "falls from 64.7% at n=6 to 11.4% at n=12, then rises again.",
    note="Paper 2 rediscovers this principle independently in two further "
         "quantities (separation cost, chi-squared validity floor), which is "
         "stronger support than the original evidence."),

("M", "What the method does not establish"): dict(
    role="The honest close: name what remains, precisely enough to be picked up.",
    claim="The rig validates the instrument, not the judge. And a narrower second "
          "gap: a deployment must estimate its null from data, which forces a "
          "choice of which flows the fitted null may contain.",
    note="FIXED. The second gap was stated as open when it is not, and the "
         "paragraph now points at the measurement. Two things it gained: the "
         "cost of defaulting to the gradient is destruction rather than the "
         "misstatement of degree originally implied, and the choice of subspace "
         "is not separable from the choice of filling -- with no 2-cells the two "
         "nulls coincide and the distinction the paragraph draws disappears. "
         "That collapse is Principle 3 reaching a quantity it was not written "
         "for, so the beat now closes on the same note the document opened."),
}


def order_from_build_py():
    """Parse ORDER out of build.py. Importing it would run the assembly."""
    bp = (HERE / "build.py").read_text()
    try:
        blk = bp[bp.index("ORDER = ["):bp.index("]\n\ndef must_replace")]
    except ValueError:
        raise SystemExit(
            "beats.py: could not locate the ORDER block in build.py. It was "
            "probably reformatted; update the delimiters in order_from_build_py.")
    found = [(m.group(1), m.group(2))
             for m in re.finditer(r'\((M|B),\s*"((?:[^"\\]|\\.)*)"', blk)]
    if not found:
        raise SystemExit("beats.py: parsed the ORDER block but found no entries.")
    return found


order = order_from_build_py()
missing = [k for k in order if k not in BEATS]
extra = [k for k in BEATS if k not in order]
if missing or extra:
    raise SystemExit(
        "beats.py: BEATS and build.py's ORDER disagree.\n"
        + "".join(f"  no beat for section: {s}:{t}\n" for s, t in missing)
        + "".join(f"  beat for a section not in ORDER: {s}:{t}\n" for s, t in extra)
        + "  Add or remove the beat so the sheet describes the document as built.")

L = ["# Paper 1 (combined draft) --- beat sheet", "",
     "*Generated by `beats.py` from `build.py`'s ORDER; do not edit by hand.*",
     "*Each beat says what the section does for the reader, what it claims, and*",
     "*what carries it. The order here IS the document's order, by construction.*",
     "", "## Thesis", "", THESIS.strip(), "",
     f"{len(order)} sections: {sum(1 for s,_ in order if s=='M')} from the "
     f"calibration methodology, {sum(1 for s,_ in order if s=='B')} from the "
     "bridge-invariance note, interleaved so each forcing argument sits beside "
     "the construction it constrains.", ""]

src_name = {"M": "methodology", "B": "bridge"}
# An act opens at the index just after the previous act's last section.
opens_act = {1: ACTS[0][1]}
for j in range(1, len(ACTS)):
    opens_act[ACTS[j - 1][0] + 1] = ACTS[j][1]

for i, key in enumerate(order, 1):
    if i in opens_act:
        L += ["---", "", f"## {opens_act[i]}", ""]
    b = BEATS[key]
    title = RETITLE.get(key, key[1])
    L += [f"### {i}. {title}", "", f"*Source: {src_name[key[0]]}*", "",
          f"- **Role.** {b['role']}",
          f"- **Claim.** {b['claim']}"]
    if b.get("evidence"):
        L += [f"- **Evidence.** {b['evidence']}"]
    if b.get("note"):
        L += [f"- **Note.** {b['note']}"]
    L += [""]

(HERE / "BEATS.md").write_text("\n".join(L) + "\n")
print(f"  wrote BEATS.md: {len(order)} beats, {len(ACTS)} acts")
