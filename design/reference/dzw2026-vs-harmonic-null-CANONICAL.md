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

DZW triaged the null problem into three components and solved the two that are inference problems. The circular fit and the post-selection validity of a data-chosen hypothesis are solved outright. The third — ε-vs-cycle — is an identifiability problem, and the round-trip converted it from flat impossibility into a measurement problem with a named confound and a criterion-dependent scope. Two further structural results fell out: in the pre-specified fixed-graph case **the certificate** collapses to a classical score test — confirmed on the rig; DZW's own fold is **not** that test and is not needed there (dominance, not identity — relationship derivation: RAN-31), which demotes DZW to "the method that earns its keep only at post-selection loop-choice and small n"; and comparison-level thinning likely replaces the noise-fission machinery entirely, at a topology-dependent separation cost measured since (RAN-28). Epic C's residual object is now small and precisely named.

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

- **In the pre-specified, fixed-graph case, the testing problem collapses to a classical score test — under `observed`.** "Test b₁ omitted directions in a logistic regression" is a Rao score test, χ² with b₁ degrees of freedom, in the harmonic coordinates. b₁, and therefore the df, is filling-dependent (measured: 2 under `observed` vs 21 under `empty` on the same 32-edge graph), so the collapse must be stated with its filling — it is not filling-free. Under `observed` the certificate, under this null, is a score test, and that is referee-proof for the discriminant-validity demonstration. (Confirmed on the rig, RAN-28: the collapse holds from k ≥ 128; the score lands in the harmonic subspace by construction — the canonical link makes the Fisher information diagonal, so the constrained MLE's first-order condition forces the score into ker D₀ᵀ ∩ ker D₁ = harmonic, with no chosen projection. The low-k limit is MLE separation, not distributional shape.) DZW's machinery then earns its keep only where the classical route fails: post-selection (which loops, chosen from data — Algorithm 3) and the small-n regime. Cleaner division of labor than earlier framing.

**Verification status (RAN-31 — ownership gate).** Two claims here are distinct and must stay distinct.
(i) *The harmonic-zero test collapses to a classical Rao score test* — **CONFIRMED** on the rig (RAN-28: the χ² null held from k ≥ 128; the score lands in the harmonic subspace by construction — diagonal Fisher information from the canonical link, `score_off_harmonic` at most 4.1e-13 across all 40 cells).
(ii) *~~This classical test coincides with DZW's own symmetric-noise-fold construction~~* — **RETIRED AS POSED** (provenance audit 2026-08-30: no identity stated in the paper or derived in this briefing; the session analysis argues it is false exactly, with the fold and score tests sharing null, estimator, and df under g = P_h but not the statistic). Replacement: the fold need not be implemented pre-specified because the classical test **dominates** there. Firsthand derivation of the relationship = RAN-31; until it closes, the dominance statement carries the same relayed-not-owned tag this claim did.
Nothing needs rework: the fold was never built, and nothing downstream used claim (ii) except the skip-the-fold justification, which dominance now carries. Downstream work that uses DZW's post-selection machinery (Algorithm 3, data-chosen loops) is where the fold is load-bearing, and is gated on RAN-31. The fixed-graph score test rests on claim (i) alone and is not gated.

**Filling fork — sharpened, not resolved (RAN-28).** These filling facts collide with the certificate's signal requirement. The harmonic signal wants loops left open so cyclic obstruction reads as harmonic (empty-ish); the dominance over BT and the score-test collapse want 2-cells present (`observed`). This is the original observed/empty fork returning: the derived window dissolved it for floor recovery, but it reappears here for the hypothesis-test object and is not resolved. Which filling the deployed certificate uses is a live decision, coupled to whose-cycle (RAN-3) and the matcher (RAN-30) — not settled by this run.

- **Confirmed obstruction (a result for the author):** the §3.3.3 assumption-free character cannot be preserved for any heterogeneous null, structured or not — its estimator pools across units sharing a distribution, and here every edge is its own distribution with effectively one observation. Nothing to average over. Standardized residuals restore approximate exchangeability only asymptotically in k, which surrenders the exactness that made §3.3.3 attractive. So Q1' resolves as: construction exists (harmonic-zero null via §3.3.2), but §3.3.3's assumption-free strength is provably out of reach for this data shape.

## Thinning likely replaces noise fission — but simplifies the architecture, not the regime (J1's second result + one caveat; ⚠ corrected by RAN-28 — see below)

Binomial(k_e, p_e) splits exactly at the trial level: randomly assign within-edge comparisons to two folds and X⁽¹⁾_e, X⁽²⁾_e are independent binomials with the same p_e. This is data thinning, available for free because the logging seam holds the raw Bernoullis. It gives exact fold independence — no conditional CLT, no (I+B)⁻¹, no Remark 13 weakening. Select loops on fold 1, fit the H₀-constrained model on fold 1, test orthogonality on fold 2 as a genuinely pre-specified hypothesis. The DZW architecture (fit-under-the-null carries the power; Remark 5 avoided because the fit is constrained to the null class) transfers wholesale, with simpler theory.

**Caveat (do not let this read as "PP4 resolved").** Thinning removes the fission machinery, but each fold now carries half the k, and the small-n problem is in the edge count, not the within-edge trials. PP4 was never about the within-edge CLT — it was the CLT over ~27 edges, which thinning does not touch. So thinning simplifies the architecture without improving the regime; the rig-as-coverage-harness stays mandatory.

**⚠ Correction (RAN-28, k=64 run).** "Simplifies the architecture, not the regime" is right about the edge-count CLT but **wrong about separation**, and the two are distinct effects. Thinning splits an edge's k into two folds of k/2, and the constrained-MLE separation rate is **worse than neutral** under thinning — measured on `observed`: graph 3 goes 0.8% → 9.2% (11×) at k 128→64, graph 2 20.7% → 29.3%, while graphs 0 and 1 effectively do not move (≤ 0.1%). The separation cost is **topology-dependent**: it cannot be priced once and reused, only measured per deployment graph — the same shape as the no-universal-threshold result. So thinning is neutral on the CLT-over-edges *and adds a topology-dependent separation cost*; the rig-as-coverage-harness stays mandatory and must now also measure per-graph separation under thinning.

**⚠ Third gate (RAN-28, fourth pass — supersedes two withdrawn claims).** Separation is not the only thing that degrades at k/2, but the second failure is not what an earlier pass of this note said it was. That pass claimed the χ² approximation fails below k = 64 because b₁ gets too small, and **that claim is withdrawn.** It rested on a confounded sweep: filling a triangle changes the curl direction as well as b₁, so the injected flow got more extreme as b₁ fell, and the sweep varied both at once. Holding the flow's extremity fixed and sweeping b₁ alone, **every level passes** — b₁ = 1 through 22, four graphs, meanT/df within 5.4% of χ². There is no b₁ floor *at fixed extremity*. Keep that qualifier: b₁ turns out to govern how much extremity is survivable, which is a different claim and is established two paragraphs down.

What the failures actually track is **saturation**, E[pᵏ + (1−p)ᵏ] — the expected fraction of edges landing at w = 0 or w = k. It is the instrument's own precondition (`rig.flows.saturation`, spec §2.6), and it needs no sampling. On the original unmatched grid every cell inside 0.02 satisfied both moment checks and no in-window cell failed — that is where the 0.02 figure came from. **⚠ It does not survive reseeding, and the flat bound is withdrawn.** That calibration ran one draw per cell; `chi2_collapse` carries no base index. Rerun under ten base seeds, `observed|g3|k128` — saturation 0.0161, comfortably inside 0.02 — passes only 6 of 10 seeds against the 0.926 its df predicts, binomial p = 0.0045. So the window's sufficiency rested on which seed was drawn. 24 of 25 in-window cells are stable; the one that is not is b₁ = 1, and by df it is 5/5 at df ∈ {16, 21, 22} against 1 of 5 at df = 1. Saturation rises as k falls, which is why the failures *looked* like a k effect: graph 3 goes 0.0161 at k = 128 to 0.0309 at k = 64, crossing out of the window. Graph 3 is the case thinning pushes out; graph 2 was already outside at full k.

**The window is b₁-dependent, by a factor of six — and every number here needs its criterion attached.** Sweeping saturation from 0.010 to 0.25 with ten base seeds at each level gives three different "where it closes" figures for b₁ = 1, and an earlier pass of this note quoted one of them without saying which:

| criterion | b₁ = 1 | b₁ = 22 |
|---|---|---|
| last rung passing BOTH mean and variance | **0.019** | **0.120** |
| first rung failing the combined gate | 0.030 | 0.180 |
| first rung failing variance alone | 0.050 | 0.180 |

The **last-passing** row is the one an admission limit must use: a first-failing value admits the saturation the sweep measured to fail. The 0.03/0.18 pair quoted earlier is the middle row, and it is also mixed — 0.030 is a mean-driven closure while 0.180 is variance-driven, so the pair was not even internally consistent. Worse, `b1_one_boundary` exports `b1_1_closes_at = 0.05`, because `closes_at()` tests the variance alone: the probe ships a different number than its own write-up quoted. That is a defect in the probe, not a difference of reading, and it is why the criterion is now stated with every figure. An earlier pass of this note claimed the same interaction on the strength of a single draw reading 3.44 at saturation 0.019; that draw was withdrawn, correctly — at 0.019 ten seeds give a median of 0.974 and 10/10 passing for b₁ = 1. The interaction is real, but it lives six times further out than the draw that first suggested it, and nothing about it was visible until the range was extended.

**Two different mechanisms close the window, and they are told apart by the mean.** At b₁ = 1 the drop rate climbs steeply with saturation — 0.4%, 1.9%, 7.8%, 29.2%, 65.4% — and separation truncation drags the surviving mean down with it (meanT/df 1.038, 0.964, 0.838, 0.676, 0.505). At b₁ = 22 the drop rate stays at 0.0% until far higher, and the mean never moves (1.008 to 1.012 throughout) while the variance alone inflates (1.028, 1.085, 1.137, 1.351, 2.102). So low b₁ closes by *losing draws*, high b₁ by *low expected counts*. That the constrained fit at b₁ = 1 has E − 1 free directions, and so can drive individual edges to separation, while b₁ = 22 leaves it only 11, is the plausible reason.

**Why this took four passes to get right.** At b₁ = 1 the reference is χ²(1), excess kurtosis 12, so the relative sampling s.e. on the variance ratio is ≈ 8.4% at 2000 replicates against a 15% gate — the noisiest cell on the grid by a factor of eight, and simultaneously the decisive one. Single draws from it produced, in order, a b₁ floor, a fold-size floor, and an interaction at 0.019; the first two were false and the third was right about the phenomenon and wrong about the threshold by a factor of six. **A single-run varT/2df at b₁ = 1 is not a diagnostic.** Every claim resting on that cell needs seeds, and needs a range wide enough to contain the effect.

**⚠ Shipped shape (later than the paragraph below).** What is in the code is a
refusal, not a bare high-b₁ rule: `saturation_window()` returns **None** below
b₁ = 3, and callers record those cells as *unclassifiable* rather than
out-of-window — so the artifact says a judgement was declined instead of implying
a measurement. Above it, the interpolated window runs to 0.120 at b₁ = 22. The
reasoning in the paragraph below is what produced that shape and is unchanged; the
form it takes in the code is the refusal.

**The gate, and it ships for high b₁ only.** Evaluate E[pᵏ + (1−p)ᵏ] at k/2 and compare against **0.120 at b₁ = 22** — the largest rung passing both moment checks, and safe to ship because the high-b₁ cells were uniformly stable under reseeding (5/5 at df ∈ {16, 21, 22}). There is no flat bound: 0.02 was withdrawn above, and it would be two errors at once anyway, too loose at b₁ = 1 and far too strict at b₁ = 22.

**⚠ At b₁ = 1 no saturation limit is shippable, and lowering the number does not fix it.** An earlier version of this paragraph proposed 0.019, the last matched rung to pass. That admits `observed|g3|k128`, which sits at saturation **0.0161 — inside 0.019 — and fails 40% of its base seeds** (6/10 against the 0.926 its df predicts, binomial p = 0.0045). Admitting a cell measured to fail is the exact error this section already charges against first-failing limits; 0.019 commits it via a cell the matched sweep never visited.

The reason is not a badly chosen threshold but that **saturation does not determine the outcome at b₁ = 1.** The matched sweep scales η to hit a target at fixed k = 64; the natural grid lets saturation fall out of k. Scaled η at k = 64 and saturation 0.019 passes, while natural η at k = 128 and saturation **0.0161 — lower** — fails. And the failures are not one kind but four, across five cells on one graph: k = 512 clean; **k = 128 failing with no median signature at all** — both moments pass (mean 0.996, variance 1.084, comfortably inside their gates) while 4 of 10 base seeds fail; k = 64 mean-only and *below* (0.858, with variance 0.905 still inside); k = 32 both below; k = 8 both above. One threshold on one statistic was never going to hold that.

**The k = 128 cell is the sharpest argument for seeding that this note contains.** It reads healthy on every moment a single run would report, and it is the cell a 0.019 window would admit. An unseeded diagnostic does not merely mismeasure it — it sees nothing wrong at all. That is also why the failure cannot be chased into the variance, where an earlier version of this paragraph sent the reader: the variance median is fine. Both figures are medians over the ten independent base seeds with the reference draw excluded. That is not bookkeeping: the reference is the draw `chi2_collapse` shipped for this cell and the one the window was calibrated against, and it is the calmest of the eleven at variance 0.974 — including it pulls the median toward 1 using the very draw whose representativeness is the question.

This is consistent with the note above that at low b₁ the binding constraint is separation and the moment check only registers it downstream — separation depends on k and on the flow, not on saturation alone.

So the b₁ = 1 bound is left open, bracketed by measurement to **(0.0017, 0.0161]** with nothing tested inside it. One caveat on that bracket: every b₁ = 1 cell on the grid is graph 3, so the whole low-edge evidence base is a single topology. Two caveats either way: at b₁ = 1 separation and χ² validity close at essentially the same saturation (drop rate passes 5% at 0.03 too), so the window is not the independent constraint there that it is at high b₁; and in deployment the gate consumes p̂ rather than a known p, so it inherits that estimate's error.

**Precondition (auditable, not a leap):** thinning requires within-edge exchangeability — no position drift, criterion mixing, or time trend inside an edge. Position and criterion are in the seam, so this is an auditable check. It is the **first of three** gates on whether thinning-replaces-fission is real; the second is the per-graph separation measurement at fold size, and the third is the saturation window at that fold size — closed form, with 0.02 safe for every b₁ measured and up to 0.18 available at high b₁ (see the corrections above). A clean audit alone does not greenlight thinning.

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

The from-summary verdict — "vocabulary and mechanism, not drop-in" — held, and the resolution is cleaner than it hoped and harsher than it feared, then the round-trip made it richer. DZW solves the circularity and the post-selection problem; the pre-specified certificate collapses to a referee-proof score test (confirmed on the rig; the fold is not that test and is unnecessary there — dominance, not identity; RAN-31 derives the relationship); thinning likely replaces the fission machinery, at a topology-dependent separation cost. What remains for Epic C is one criterion-dependent framing question (whose cycle), one identifiability research direction (judge-exchangeable ε under a named confound), a design constraint on the matcher, and a buildable coverage-and-size experiment this month. That is a materially stronger position than "build a better null": most of the wall is now someone else's solved theorem, the classical fallback is trivial and referee-proof, and the remaining piece is named precisely enough to either close or carry to its author — as a peer.
