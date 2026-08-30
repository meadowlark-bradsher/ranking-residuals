# Paper 2 — beat sheet

*Working outline. Not prose. Each beat says what work it does for the reader,
what it claims, and what evidence carries it. Sequel to the combined draft
(`combined/`), which is paper 1.*

**Working title.** *The null is the easy part: a subspace hypothesis test for a
harmonic rankability certificate, and the envelope it has to ship with.*

**Thesis (the one sentence the paper defends).** A subspace null makes the
certificate testable and turns out to be a classical Rao score test — but its
region of validity is set by the comparison graph's topology *and* by a
modelling choice, in two independent ways, neither of which is visible from the
statistic itself. A certificate of this kind is not deliverable without its
envelope.

**Why it generalizes.** The specific test is ours; the failure mode is not. Any
certificate that reports "no signal detected" from a fitted null on a small,
irregular design can be reporting a truncated statistic rather than a clean one.

---

## Act I — the null

### §1 The problem: a certificate with nothing to be certified against
**Beat.** Open on the gap paper 1 left, in paper 1's own words. It says a
Bradley–Terry null "assumes the criterion is rankable before testing whether it
is," names the gradient-and-curl subspace as the alternative, and says the
choice "has to be stated rather than defaulted." That is the paper's brief.
**Claim.** Measuring harmonic energy is not certifying it. Certification needs a
null, and which null is a modelling decision that paper 1 deliberately left open.
**Evidence.** Citation to paper 1 §"What the method does not establish."
**Work done.** Establishes this as a sequel with an inherited question, not a
new topic.

### §2 Why not Bradley–Terry — and it is not a philosophical objection
**Beat.** The obvious null is circular. Then show the circularity has a price,
and the price is total, not marginal.
**Claim.** BT forbids everything outside the gradient image, curl included, so
curl-type misspecification destroys its size completely.
**Evidence.** `curl_freedom`: fed H₀-true flows carrying curl, BT rejects **every
single draw** (1.0000, all four graphs) from a curl fraction of 0.45 upward,
while the harmonic-zero null never exceeds 0.058. 1500 replicates, k = 128.
**Work done.** Converts "BT is the wrong null" from an argument into a
measurement. This is the paper's first hard number and it should land early.

### §3 The construction
**Beat.** State the null and note it is unremarkable — deliberately.
**Claim.** H₀: logit p ∈ S = im D₀ ⊕ im D₁ᵀ = (harmonic)^⊥. A linear-subspace
constraint on the natural parameter of an exponential-family GLM. Gradient and
curl coordinates free; harmonic exactly zero.
**Work done.** Sets up §4's punchline by making the object look ordinary.

### §4 It is a classical Rao score test, and the score lands in harmonic
coordinates by construction
**Beat.** The turn from "our null" to "a textbook object." This is the paper's
credibility beat.
**Claim.** In the pre-specified fixed-graph case this *is* a Rao score test, χ²
with b₁ df. The constrained fit's stationarity condition MᵀU(η̂) = 0 forces the
leftover score orthogonal to S, hence into the harmonic subspace — exactly, with
no projection applied by us.
**Evidence.** Collapse confirmed from k ≥ 128, four fixed graphs, 24–33 edges,
2000 replicates. `score_off_harmonic` ≤ 4.1e-13 across all 40 cells: the true
value is 0 and the residue is floating point.
**Caveat to state here, not later.** I⁻¹ does not preserve the harmonic
subspace, so T is *not* ‖U‖² rescaled — the metric carries the k_e and p_e
dependence, and that is exactly where the small-sample problem will live (§7–8).
**Work done.** Makes everything downstream referee-proof, and narrows what the
post-selection machinery is *for*: it earns its keep only where the classical
route fails, i.e. data-chosen loops and small n.

---

## Act II — what it buys, and the catch

### §5 What the null buys
**Beat.** Deliver on §2's setup: state the two properties and show both measured.
**Claim.** (a) All curl-type misspecification is absorbed, so rejections are
driven only by harmonic content. (b) The size distortion under innocent
misspecification is governed by ‖P_h ε‖ alone, not total ε.
**Evidence.** Equal-norm control: a perturbation of identical magnitude placed
*inside* S never exceeds 0.059 across every graph and every ε up to 0.8, while
the harmonic direction drives rejection to 0.967. Usable band: size stays inside
2α while ‖P_h ε‖ ≲ 0.1 (worst cell 0.080 against nominal 0.05); by ‖P_h ε‖ = 0.4
it reads 0.223–0.452 and is no longer honest.
**Work done.** Establishes the null as usable *and* bounds where. The ≲ 0.1
number is the paper's headline operational figure.

### §6 The catch: none of that is filling-free
**Beat.** Pull the rug, deliberately and early. Better the paper says this than
a referee.
**Claim.** The 2-skeleton is a modelling choice, and it sets b₁. Under `empty`
there are no 2-cells, so im D₁ᵀ = {0}, S = im D₀, and the harmonic-zero null
*coincides with Bradley–Terry*. Everything §5 buys evaporates there.
**Evidence.** Identical df, 18 = 18, on a 29-edge graph. b₁ measured 4/3/3/1
under `observed` against 16/13/21/22 under `empty` on the same four graphs.
**Work done.** Converts the filling from background convention into a
first-class parameter of the test. Sets up §8, where it returns as a data
requirement.

---

## Act III — the operating envelope

### §7 First failure: separation, and it biases what survives
**Beat.** The practical limit is not the one the theory suggests.
**Claim.** The binding constraint at deployment scale is MLE separation, not
distributional shape — and the loss is not neutral, it is selective.
**Evidence.** On `observed` at k = 8, 60.3–99.6% of draws put some edge at w = 0
or w = k; the constrained MLE diverges and the statistic is undefined. Graph 2
still loses 20.7% at k = 128 and 5.0% at k = 512. Separation preferentially
removes draws with extreme scores, so the surviving test is **conservative**:
on the b₁ = 1 graph, drop rate and conditional mean move together (0.8% / 1.024
at k = 128; 9.2% / 0.842 at k = 64; 43.0% / 0.740 at k = 32) with realised size
falling 0.045 → 0.039 → 0.030.
**Deployment consequence — state it bluntly.** Near this regime a certificate
reading "no cycle detected" may be reading a *truncated* statistic rather than
an innocent graph. The drop rate has to be reported alongside any verdict; it is
invisible in the statistic.
**Work done.** The paper's most transferable warning, and the one a practitioner
will remember.

### §8 Second failure: χ² validity — and it is really a b₁ gate
**Beat.** The technical heart. A second, independent failure that looks like the
first and is not.
**Claim.** The first two moments track χ²(b₁) from k = 128 up and fail at
k ≤ 64 — and the failure is driven by b₁, not by the drop rate.
**Evidence.** The contrast is the proof: graph 2 loses **29.3%** of draws at
k = 64 with meanT/df = 0.972 (intact); graph 3 loses only **9.2%** with
meanT/df = 0.842 (broken). Mechanism: at b₁ = 1, truncating the single harmonic
coordinate truncates the statistic directly; at b₁ ≥ 3 the remaining coordinates
absorb it.
**The sharp consequence.** b₁ is set by the filling (§6). So a modelling choice
determines how much data the test needs. Under `empty`, where b₁ runs 13–22,
every cell sits at meanT/df ≈ 1.00 at k = 64 — the χ² gate is free there. Under
`observed` with low b₁, it is not.
**Work done.** Ties Act II's catch to Act III's envelope. This is the result
that is genuinely new rather than measured-confirmation of something expected.

### §9 Both failures are topology-bound
**Beat.** Zoom out; connect to paper 1's Principle 3.
**Claim.** Neither failure can be priced once and reused. Both depend on the
deployment's own comparison graph, so the deliverable is a procedure, not a
number — the same shape paper 1 established for the threshold, now recurring in
two further quantities.
**Evidence.** Separation at k 128→64 moves graph 3 by 11× and graph 1 not at
all; the χ² floor is b₁-dependent and b₁ varies 1–4 across four graphs of
comparable size (24–33 edges).
**Work done.** Makes the paper a genuine sequel: the same principle, independently
rediscovered in a new quantity, is stronger evidence for it than the original.

---

## Act IV — consequence, and what is open

### §10 Worked consequence: comparison-level thinning
**Beat.** Show the envelope doing real work by killing a proposal that looked free.
**Claim.** Trial-level thinning gives exact fold independence and would replace
the noise-fission machinery — but it halves k, so it must clear both envelope
gates at the fold size, plus an exchangeability precondition. Three gates, and
for the configuration thinning was proposed for, the third currently fails.
**Evidence.** A k = 128 deployment does its inference at k = 64. Separation:
graph 3 0.8% → 9.2%, graph 2 20.7% → 29.3%, graphs 0 and 1 unmoved. χ² validity:
fails at 64 on the b₁ = 1 graph. Remedies differ per gate — raise k, or calibrate
the reference distribution at the fold size (which costs the referee-proofness
§4 bought).
**Work done.** Demonstrates the envelope is not bookkeeping. Also the honest
form of a negative result: the method is still attractive, the price is now known.

### §11 What this does not establish
**Beat.** Close by naming what is open, precisely enough to be picked up.
- **The filling fork is unresolved.** The harmonic signal wants loops left open
  so cyclic obstruction reads as harmonic; dominance over BT (§5) and the low
  data requirement (§8) point opposite ways. This paper measures the trade and
  does not settle it. It is coupled to what the certificate is *for* — whose
  cycle it certifies — which is not a statistical question.
- **Agreement with the post-selection framework is asserted, not verified.** The
  fixed-graph collapse is measured; that this classical test coincides with the
  cross-fit construction is argued from a secondhand reading and is deferred.
- **Post-selection needs vector-g.** The available theory is scalar-g; b₁ > 1 in
  seven of eight measured cells, so the caveat binds in essentially every
  realistic case — and precisely on the path where the classical route fails.
- **One data-generating process.** Gamma-shaped θ throughout; the four graphs
  vary the mask, not the latent. A different θ shape could move the small-k
  behaviour.

---

## Structural notes

- **Depends on paper 1's rig, not on its glued construction.** The probes use
  sparse BTL graphs — no bridge, no circle block. Cite paper 1 for the
  instrument and the topology-bound principle; do not inherit its object.
- **Terminology collision to resolve before any merge.** Paper 1 uses
  "separation" for latent spread; this paper uses it for the event where the
  constrained MLE diverges. Paper 1 already describes the same *event* ("wins
  land at 0 or k") and carries a closed-form pre-filter for it,
  E[p^k + (1−p)^k]. Either rename here, or adopt paper 1's pre-filter and
  explain how the two notions relate.
- **The order is load-bearing.** §2 before §3: the reader must want the null
  before being handed it. §6 before §7: the filling has to be a live parameter
  before the b₁ result in §8 can land.
- **Everything numeric here is regenerated from `results/*.json`** via
  `experiments/harmonic-zero-null/probes.py`; the prose numbers derive from the
  same rows as the tables.
