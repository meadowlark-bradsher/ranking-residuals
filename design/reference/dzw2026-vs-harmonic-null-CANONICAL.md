<!--
Relayed briefing artifact. Authored in the parallel paper thread against the full
Dharamshi-Zou-Witten (2026) paper; committed here so the analysis stops living
only in a chat log. Referenced by RAN-27 (prior-art read) by exactly this
filename; governs RAN-28 (harmonic-zero null on the rig), RAN-29 (within-edge
exchangeability audit) and RAN-30 (matcher conditioning).

Supersedes the from-summary and RESOLVED versions, per its own status line.
Paper elements are cited so any holder of the paper can re-check.
-->

# Dharamshi–Zou–Witten (2026) → Harmonic Rankability Null

**Canonical briefing (current)**

**Status.** Supersedes both prior versions (from-summary, and RESOLVED). Grounded in the actual paper via the verification pass, and incorporates the J1/J2 round-trip. This is the single artifact to carry between the reasoning thread, the verification thread, and the specialist conversation. Paper elements are cited so any holder of the paper can re-check. Open edges are marked as such.

## Headline

DZW triaged the null problem into three components and solved the two that are inference problems. The circular fit and the post-selection validity of a data-chosen hypothesis are solved outright. The third — ε-vs-cycle — is an identifiability problem, and the round-trip converted it from flat impossibility into a measurement problem with a named confound and a criterion-dependent scope. Two further structural results fell out: in the pre-specified fixed-graph case the certificate collapses to a classical score test — the collapse is confirmed on the rig, the equivalence to DZW's own fold is asserted pending RAN-31 — which demotes DZW from "the method" to "the method that earns its keep only at post-selection loop-choice and small n"; and comparison-level thinning likely replaces the noise-fission machinery entirely, at a topology-dependent separation cost measured since (RAN-28). Epic C's residual object is now small and precisely named.

## The three-way triage (Epic C's reshaped object)

**(1) The circular fit — inference — SOLVED.** The mechanism fits the conditional mean under the constraint of H₀ by construction (deliberately wrong when H₀ is false, so residual covariance carries power). Remark 5 states the double-dip exactly and is why a flexible learner can't be used: it orthogonalizes under both hypotheses and kills all power.

**(2) Post-selection validity — inference — SOLVED, with a design boundary.** A hypothesis selected from the data (which harmonic loops to test) on a fixed graph is covered by Algorithm 3: select the null on x⁽¹⁾, fit under it, test on x⁽²⁾. Needs only conditional-mean properties. Boundary: the design must be fixed conditional on the item set — see the matcher ACTION.

**(3) ε-vs-cycle — identifiability — REOPENED, not closed.** No orthogonalization separates "gradient + ε" from "gradient + cycle" at k→∞ within DZW's controlled setting (single judge, fixed graph). But J2 found a structural escape that survives scrutiny: replication across judges. The impossibility was never absolute — it was absolute along the axes the paper controls. Epic C's object is now "identifiability of cycle-vs-misspecification via judge-exchangeable ε, under a named confound, with a criterion-dependent scope" — not "build a better null."

## The null to run — harmonic-zero, NOT pure Bradley–Terry (J1's central result)

The "unit-level nuisance" version of the subspace null is vacuous, for a one-line reason: per edge the model is Binomial(k_e, p_e), a one-parameter family, so any per-edge nuisance ν_e in logit(p_e) = (D₀θ)_e + ν_e saturates the model — Θ₀ = Θ, H₀ constrains nothing. Misspecification here is not distributional (the binomial is exact if within-edge trials are iid); it is entirely mean-vector misspecification. Q1' as literally posed is dead.

The live construction, one notch weaker, is the right null:

> **H₀: logit p ∈ im D₀ ⊕ im δ₁ᵀ = (harmonic)^⊥** — the harmonic component of the mean flow is exactly zero, with the gradient and curl coordinates free.

This is a linear-subspace constraint on the natural parameter of an exponential-family GLM. The constrained MLE exists, is asymptotically linear and efficient under standard conditions, so §3.3.2 applies cleanly, Supplement B.2's eigenvalue condition is met, and with discrete noise Remark 8 gives exact N, D. Under a filling that retains 2-cells (`observed`) it strictly dominates the pure-BT null: all curl-type misspecification is absorbed into the null, rejections are driven only by harmonic content, and the size distortion under innocent ε is governed by ‖P_h ε‖ alone, not total ε (confirmed on the rig, RAN-28: an equal-norm perturbation placed inside S never exceeded 0.059 while the harmonic direction drove rejection to 0.967). The rig experiment sharpens accordingly: measure Type-I inflation as a function of harmonic-projected ε, not raw ε.

**⚠ Filling caveat (RAN-28 correction).** The dominance is not filling-free — an imprecision in the earlier draft, now corrected. Under `empty` there are no 2-cells, so im δ₁ᵀ = {0}, S = im D₀, and the harmonic-zero null coincides with Bradley–Terry (measured: identical df, 18 = 18 on a 29-edge graph). Everything "strictly dominates BT" buys evaporates there. All claims in this section hold under `observed`; under `empty` this null reduces to pure-BT.

Two consequences worth sitting with:

- **In the pre-specified, fixed-graph case, DZW collapses to a classical score test — under `observed`.** "Test b₁ omitted directions in a logistic regression" is a Rao score test, χ² with b₁ degrees of freedom, in the harmonic coordinates. b₁, and therefore the df, is filling-dependent (measured: 2 under `observed` vs 21 under `empty` on the same 32-edge graph), so the collapse must be stated with its filling — it is not filling-free. Under `observed` the certificate, under this null, is a score test, and that is referee-proof for the discriminant-validity demonstration. (Confirmed on the rig, RAN-28: the collapse holds from k ≥ 128; the score lands in the harmonic subspace by construction — the canonical link makes the Fisher information diagonal, so the constrained MLE's first-order condition forces the score into ker D₀ᵀ ∩ ker D₁ = harmonic, with no chosen projection. The low-k limit is MLE separation, not distributional shape.) DZW's machinery then earns its keep only where the classical route fails: post-selection (which loops, chosen from data — Algorithm 3) and the small-n regime. Cleaner division of labor than earlier framing.

**Verification status (RAN-31 — ownership gate).** Two claims here are distinct and must stay distinct.
(i) *The harmonic-zero test collapses to a classical Rao score test* — **CONFIRMED** on the rig (RAN-28: the χ² null held from k ≥ 128; the score lands in the harmonic subspace by construction — diagonal Fisher information from the canonical link, `score_off_harmonic` at most 4.1e-13 across all 40 cells).
(ii) *This classical test coincides with DZW's own symmetric-noise-fold construction, so the fold need not be implemented* — **ASSERTED** from this paper's framework, **not** independently verified.
Claim (ii) is what let RAN-28 skip building DZW's fold, and it rests on *this briefing* rather than a firsthand read of DZW §3.3.2. It is **deferred to RAN-31** and must be treated as unconfirmed, not settled. Downstream work that uses DZW's post-selection machinery (Algorithm 3, data-chosen loops) inherits claim (ii) and is gated on RAN-31. The fixed-graph score test rests on claim (i) alone and is not gated.

**Filling fork — sharpened, not resolved (RAN-28).** These filling facts collide with the certificate's signal requirement. The harmonic signal wants loops left open so cyclic obstruction reads as harmonic (empty-ish); the dominance over BT and the score-test collapse want 2-cells present (`observed`). This is the original observed/empty fork returning: the derived window dissolved it for floor recovery, but it reappears here for the hypothesis-test object and is not resolved. Which filling the deployed certificate uses is a live decision, coupled to whose-cycle (RAN-3) and the matcher (RAN-30) — not settled by this run.

- **Confirmed obstruction (a result for the author):** the §3.3.3 assumption-free character cannot be preserved for any heterogeneous null, structured or not — its estimator pools across units sharing a distribution, and here every edge is its own distribution with effectively one observation. Nothing to average over. Standardized residuals restore approximate exchangeability only asymptotically in k, which surrenders the exactness that made §3.3.3 attractive. So Q1' resolves as: construction exists (harmonic-zero null via §3.3.2), but §3.3.3's assumption-free strength is provably out of reach for this data shape.

## Thinning likely replaces noise fission — but simplifies the architecture, not the regime (J1's second result + one caveat; ⚠ corrected by RAN-28 — see below)

Binomial(k_e, p_e) splits exactly at the trial level: randomly assign within-edge comparisons to two folds and X⁽¹⁾_e, X⁽²⁾_e are independent binomials with the same p_e. This is data thinning, available for free because the logging seam holds the raw Bernoullis. It gives exact fold independence — no conditional CLT, no (I+B)⁻¹, no Remark 13 weakening. Select loops on fold 1, fit the H₀-constrained model on fold 1, test orthogonality on fold 2 as a genuinely pre-specified hypothesis. The DZW architecture (fit-under-the-null carries the power; Remark 5 avoided because the fit is constrained to the null class) transfers wholesale, with simpler theory.

**Caveat (do not let this read as "PP4 resolved").** Thinning removes the fission machinery, but each fold now carries half the k, and the small-n problem is in the edge count, not the within-edge trials. PP4 was never about the within-edge CLT — it was the CLT over ~27 edges, which thinning does not touch. So thinning simplifies the architecture without improving the regime; the rig-as-coverage-harness stays mandatory.

**⚠ Correction (RAN-28, k=64 run).** "Simplifies the architecture, not the regime" is right about the edge-count CLT but **wrong about separation**, and the two are distinct effects. Thinning splits an edge's k into two folds of k/2, and the constrained-MLE separation rate is **worse than neutral** under thinning — measured on `observed`: graph 3 goes 0.8% → 9.2% (11×) at k 128→64, graph 2 20.7% → 29.3%, while graphs 0 and 1 effectively do not move (≤ 0.1%). The separation cost is **topology-dependent**: it cannot be priced once and reused, only measured per deployment graph — the same shape as the no-universal-threshold result. So thinning is neutral on the CLT-over-edges *and adds a topology-dependent separation cost*; the rig-as-coverage-harness stays mandatory and must now also measure per-graph separation under thinning.

**⚠ Third gate, and it is closed form (RAN-28, third pass — supersedes a withdrawn claim).** Separation is not the only thing that degrades at k/2, but the second failure is not what an earlier pass of this note said it was. That pass claimed the χ² approximation fails below k = 64 because b₁ gets too small, and **that claim is withdrawn.** It rested on a confounded sweep: filling a triangle changes the curl direction as well as b₁, so the injected flow got more extreme as b₁ fell, and the sweep varied both at once. Holding the flow's extremity fixed and sweeping b₁ alone, **every level passes** — b₁ = 1 through 22, four graphs, meanT/df within 5.4% of χ². There is no b₁ floor.

What the failures actually track is **saturation**, E[pᵏ + (1−p)ᵏ] — the expected fraction of edges landing at w = 0 or w = k. It is the instrument's own precondition (`rig.flows.saturation`, spec §2.6), it needs no sampling, and on the measured grid every cell inside a window of 0.02 satisfies both moment checks while no in-window cell fails. Saturation rises as k falls, which is why the failures *looked* like a k effect: graph 3 goes 0.0161 at k = 128 to 0.0309 at k = 64, crossing out of the window. Graph 3 is the case thinning pushes out; graph 2 was already outside at full k.

**The window looks b₁-independent, and getting there took three corrections — all of the same kind.** Sweeping saturation from 0.010 to 0.019 at b₁ = 1 with ten base seeds per level, the median variance ratio is flat: 1.059, 0.998, 1.025, 1.019, 1.003, 0.974. It never closes. The b₁ = 22 control is flat too (0.973 to 1.025, s.e. ≈ 0.01 throughout). An earlier pass of this note claimed b₁ and saturation *interact* — that b₁ = 1 hit 3.44 at the window edge while b₁ = 22 was untouched — and **that claim is withdrawn as well**: 3.44 was one heavy-tailed draw, and at the same level ten seeds give a median of 0.974 with 10/10 passing.

What is real, and what produced three false findings in a row, is that at b₁ = 1 the reference is χ²(1), whose excess kurtosis is 12. The relative sampling s.e. on the variance ratio is then ≈ 8.4% at 2000 replicates against a 15% gate, so one or two seeds in ten exceed it at almost every saturation level — purely from the tail, with no trend in saturation at all. At b₁ = 22 (kurtosis 0.55) the same quantity has s.e. ≈ 1%, and 10/10 seeds pass everywhere. **A single-run varT/2df at b₁ = 1 is not a usable diagnostic**; it is the noisiest cell on the grid by a factor of eight, and it is also the decisive one, which is how it manufactured a b₁ floor, then a fold-size floor, then an interaction. None survived replication.

So the third gate on thinning is what it looked like before the detour: evaluate E[pᵏ + (1−p)ᵏ] at k/2 and check the window, with no b₁ index needed across the range tested. Two caveats it should carry: the window's upper edge is unpinned above 0.019, and in deployment the gate consumes p̂ rather than a known p, so it inherits that estimate's error.

**Precondition (auditable, not a leap):** thinning requires within-edge exchangeability — no position drift, criterion mixing, or time trend inside an edge. Position and criterion are in the seam, so this is an auditable check. It is the **first of three** gates on whether thinning-replaces-fission is real; the second is the per-graph separation measurement at fold size, and the third is the saturation window at that fold size — closed form, and b₁-independent across the range measured, though its upper edge is unpinned (see the corrections above). A clean audit alone does not greenlight thinning.

## Pressure points, resolved (compressed)

- **PP1 — counts — DISSOLVED.** Remark 1 (Skellam / discrete-uniform noise), Remark 8 (exact N, D with discrete noise). Edge win counts fit the heterogeneity device; Proposition 2's closed form survives; nothing moves to log-odds.
- **PP2 — the ε-floor — mismatch branch, and the paper forces it.** §3.3.3's assumption-free route needs iid-under-H₀; "flow is a gradient" is maximally heterogeneous with no recoverable exchangeability, so you are pushed to §3.3.2 — but to the harmonic-zero null above, not pure-BT. Enriching H₀ with flexible ε reruns Remark 5 inside the estimator (a class flexible enough to absorb unknown misspecification absorbs the harmonic alternative; power dies). ε is not absorbed — it is not an inference object.
- **PP3 — g = the harmonic projection — GIFT, two caveats.** µₙ lives in the harmonic subspace by construction, so g = P_h is the principled collinear choice. (a) Post-selection theory (Theorem 3, Proposition 6, (I+B)⁻¹) is scalar-g; b₁ > 1 needs a scalar reduction (dominant harmonic direction) or a vector-g extension of Section 4 — real work. (b) g = P_h has power against ε too, since innocent misspecification lives in the same subspace — so it maximizes power against "not pure gradient," not "cyclic specifically." This is the identifiability problem reappearing in the power geometry.
- **PP4 — asymptotic, and worse than priced.** Remark 13: convergence in probability, asymptotic. n is the edge count, not the comparison count. ~27 edges against their smallest tested n=200 — an order of magnitude below range. Thinning does not fix this. The rig coverage-harness is the only way to know if the guarantee means anything at your scale.
- **(I+B)⁻¹ cost — mostly moot.** Supplement B.2 ties the eigenvalue condition to θ̂ efficiency; the BT-gradient MLE is efficient, so for this null it is well-defined near-free — and thinning removes the need for it entirely in the pre-specified case.

**Deployment-validity caveat — silent conservative power loss near the separation regime (RAN-28).** MLE separation does not drop draws at random: it preferentially removes draws with extreme scores, so the *surviving* test is **conservative** (it loses power), and the loss is topology-dependent and invisible unless the drop rate is tracked. Measured on graph 3 (b₁ = 1), drop rate and conditional mean move together — k=128: 0.8% / meanT-over-df 1.024; k=64: 9.2% / 0.842; k=32: 43.0% / 0.740 — with realised size falling 0.045 → 0.039 → 0.030. Sharpest at b₁ = 1 (truncating the single harmonic coordinate truncates the statistic directly); at b₁ = 3 the mean stays near 1.0 despite heavier loss. **Consequence for deployment:** near the separation regime, a certificate reading "no cycle detected" may be reading a *truncated* statistic, not an innocent graph. The certificate's honest operating envelope must report the per-graph separation/drop rate alongside any "no obstruction" verdict; a low-k reading without it is not trustworthy. Belongs in the operating-envelope spec, not only the thinning detail (RAN-29).

## J2 — the identifiability question, opened (the reframe)

The impossibility is airtight along every axis the paper controls: single judge, fixed graph, k→∞. Dead axes: a magnitude bound ‖P_h ε‖ ≤ δ re-imports the floor as an axiom (begs the question); the k-sweep (both survive); graph resampling — subtle — both a genuine cycle and stable misspecification are properties of the underlying comparison function, so both replicate across sparse graphs over the same items; resampling separates stable-anything from session noise, not cycle from ε.

**The escape that survives: replication across judges.** A genuine cycle is a property of the item set under the criterion; misspecification is a property of the judge. With J judges, decompose each judge's harmonic-projected flow into a common component and judge-idiosyncratic components. Under

> **(A) judge-exchangeable misspecification** — the ε_j are independent across judges with mean zero in the harmonic subspace —

the common harmonic component identifies the cycle and the cross-judge variance identifies ε. This is a mixed-model decomposition, it is exactly the structural resource LLM arenas have in abundance (a heterogeneous judge panel is the defining feature), and it composes with the harmonic-zero null: per-judge score statistics in harmonic coordinates, then common-vs-idiosyncratic partitioning.

**Named confound (where (A) can rot):** LLM judges share training distributions, so their misspecifications are correlated — verbosity, position, self-preference are near-universal. (A) fails precisely for the biases most likely to exist. Defensible weakening: condition out everything modelable from logged covariates first (position and criterion are already in the seam — the seam contract paying off), demand architectural diversity in the panel, and name the residual confound explicitly: a universal bias with a harmonic footprint that survives covariate adjustment. Partial test: include human raters as one judge class — a harmonic component shared by humans and models is much harder to attribute to LLM-common bias.

**The whose-cycle fork — criterion-dependent, not binary.** The fork is not the binary "certifies the judge's cycle or the world's." There is a third reading: the certificate certifies whether the items resist ordering under this criterion, as estimated through a judge as measurement instrument, with the judge's idiosyncratic ε as measurement error you are seeing past. That is neither "the judge's intransitivity is the real cycle" nor "the world has a Platonic cycle" — it is the standard structure of a measurement problem, and it is the reading where judge-replication does its natural job (averaging out instrument error to estimate a latent property), so (A) is an assumption, not a redefinition. Whether the third reading is available is criterion-dependent:

- "which summary is more accurate" → plausibly a latent orderability estimated through noisy judges → measurement framing applies, (A) is an assumption.
- "which is funnier" → possibly no criterion-independent fact → the fork bites, and the object collapses to "the judge's cycle," at which point judge-replication answers a different (also valuable) question than the certificate asks.

So the fork is not one scoping decision — it is per-criterion. That is §13.2's signature a third time: the answer is per-criterion, not universal.

**J2 verdict:** not a clean no. Exactly one defensible structural assumption (judge-exchangeable ε after covariate adjustment), a named residual confound (shared LLM bias), and a criterion-dependent definitional scope. A research direction with its own falsification surface — richer and more defensible than an enshrined impossibility, and considerably more work.

## ACTION — the matcher-conditioning constraint (unchanged, and the one paper-independent decision)

DZW's post-selection framework covers hypotheses selected from x⁽¹⁾ on a fixed design, not data-dependent designs. An adaptive matcher that chooses edge t+1 from the outcomes of 1..t makes the η_i data-dependent, violating the independence structure before the noise-split. You cannot fission out of a sequentially chosen design. So §13.2 bifurcates: choosing which loops to test on a given graph is covered (Algorithm 3); the matcher having chosen which edges exist by looking at wins is outside the framework.

**Determining fact (code-level):** does plant-ledger next-pair selection read wins/losses, or only position / criterion / coverage?

- **Conditions on outcomes** → outside the guarantees. Either make the deployment matcher outcome-independent (batch / position / criterion / coverage-driven) — cheap now, expensive to retrofit — or condition on the realized design and treat that as part of the selection event (Q2', open, for the author).
- **Already outcome-independent** → inside the framework; preserve deliberately, and don't let the LLM axis drift into outcome-conditioning without re-checking.

A constraint flowing backward from the inference method to the data-collection policy. Settle before the LLM axis hardens around a matcher.

## The buildable path this month (rig-shaped)

Run the harmonic-zero null (a score test in the fixed-graph case), and use the known-answer harness to measure Type-I inflation as a function of harmonic-projected ε on the actual topologies at the actual edge counts. If inflation is small at ε realistic for LLM judges, the null is usable with an empirically characterized size — and the same run doubles as the PP4 coverage check (does the asymptotic guarantee hold at ~27 edges). Use comparison-level thinning only if the within-edge exchangeability audit passes, **and** the per-graph separation cost at fold size is acceptable, **and** the χ² approximation still holds at that fold size — RAN-28 makes the audit necessary but well short of sufficient, and at k/2 = 64 the third condition currently fails. No new theory required.

## Specialist conversation — revised hierarchy

The math is now worked; this is a peer conversation, not a help request (two-thirds of the null is a solved theorem plus a classical score test).

- **Framing question, above all others:** whose cycle does the certificate certify — the judge's, the world's, or the items-through-a-measurement-instrument reading — and is that criterion-dependent? This determines what everything below is for.
- **Q1' — RESOLVED** (harmonic-zero null via §3.3.2; §3.3.3 assumption-free strength provably out of reach). Carry as a result. Residual check: does her framework offer a better subspace-null estimator than the constrained GLM MLE?
- **Q2' — OPEN, for her:** does the framework extend to sequentially adaptive designs (outcome-dependent η_i), or is conditioning on the realized design the right move? (The matcher question.)

## Bottom line

The from-summary verdict — "vocabulary and mechanism, not drop-in" — held, and the resolution is cleaner than it hoped and harsher than it feared, then the round-trip made it richer. DZW solves the circularity and the post-selection problem; the pre-specified certificate collapses to a referee-proof score test (the collapse confirmed on the rig, the equivalence to DZW's own fold asserted pending RAN-31); thinning likely replaces the fission machinery, at a topology-dependent separation cost. What remains for Epic C is one criterion-dependent framing question (whose cycle), one identifiability research direction (judge-exchangeable ε under a named confound), a design constraint on the matcher, and a buildable coverage-and-size experiment this month. That is a materially stronger position than "build a better null": most of the wall is now someone else's solved theorem, the classical fallback is trivial and referee-proof, and the remaining piece is named precisely enough to either close or carry to its author — as a peer.
