# Study note — the Rao score test, and why our harmonic-zero test is one

**Companion to** `dzw2026-vs-harmonic-null-CANONICAL.md`. **Serves** RAN-31.

**What this is.** An on-ramp. Before reading DZW §3.3.2 you need the Rao score
test to be a thing you *recognize*, not decode — because the whole point of the
DZW reading is to confirm their machinery reduces to this test, and you cannot
check a reduction if the target is a black box. Read this first; it makes DZW
smaller.

**How to use it.** Work the three rungs in order, then internalize the bridge
dictionary, then read DZW. Each rung says what to *extract* (one idea), not
"read the whole book." There are self-checks — if you cannot answer them, you
have not got the rung yet; that is information, not failure.

**Success criterion.** You own this when you can say [the target sentence](#the-target-sentence)
cold, in your own words, without notes. That sentence is the whole thing
compressed. Everything here is in service of being able to say it.

**Honest calibration.** This is a smaller lift than DZW, and it is genuinely
accessible — the score test is standard graduate material, written to be taught.
Doing it first is not a detour; it is the thing that makes the DZW reading
survivable. An afternoon on Rung 1, an hour on a slice of Rung 2, then the
bridge.

---

## The one idea, before you open anything

There are three classical ways to test a hypothesis, and you understand each by
contrast:

- **Wald** — fit the model *without* the constraint, then check whether the
  unconstrained estimate is far from what the null claims.
- **Likelihood ratio (LR)** — fit *both* the constrained and unconstrained
  models, compare how much likelihood the constraint costs.
- **Score / Rao / Lagrange-multiplier** (three names, one test) — fit the model
  **under the null only**, then look at the log-likelihood's gradient at that
  constrained fit, *in the directions the constraint forbids*. If the null is
  true, that gradient is just sampling noise. If the null is false, the model is
  straining to move into the forbidden directions, so the gradient there is
  large. Reject when it is large.

**Why you want the score test specifically, and not the other two:** it is the
one that **fits under the null**. That single feature is what matches DZW (whose
conditional mean is also estimated under $H_0$), and it is what produces the
"leftover score lands in the harmonic subspace by construction" geometry that
your rig measured at $4.1\times10^{-13}$. Wald fits the full model and you would
lose that geometry entirely. So whenever you meet the three together, tag the
score test as **"the constrained-fit one"** — that tag is why it is yours.

---

## Rung 1 — the score test in general

**What it says, precisely.** You have parameters split into two blocks,
$\theta = (\beta_1, \beta_2)$, and you test $H_0 : \beta_2 = 0$ (with $\beta_1$
a free nuisance). The recipe:

1. **Fit the restricted MLE:** maximize the likelihood with $\beta_2$ held at
   $0$, getting $\tilde\beta_1$. Call the whole restricted fit
   $\tilde\theta = (\tilde\beta_1, 0)$.

2. **Compute the score** $U(\theta) = \partial\ell/\partial\theta$ (the
   log-likelihood's gradient) at $\tilde\theta$. By stationarity of the
   restricted fit, the $\beta_1$-block of the score is $0$ at $\tilde\theta$ —
   you maximized over $\beta_1$, so its gradient vanishes. The $\beta_2$-block,
   $U_2$, is generally **not** zero. That is the signal.

3. **The statistic** is a quadratic form in that leftover score, with the Fisher
   information $I$ as the metric:

$$
T \;=\; U(\tilde\theta)^{\mathsf T}\, I(\tilde\theta)^{-1}\, U(\tilde\theta)
$$

   which — because the $\beta_1$-block is zero — reduces to a quadratic form in
   $U_2$ alone, using the $\beta_2\beta_2$ block of $I^{-1}$ (which correctly
   accounts for having estimated $\beta_1$).

4. **Under $H_0$,** $T \xrightarrow{d} \chi^2_{\,\dim(\beta_2)}$ — degrees of
   freedom = the number of constraints.

**Extract this one paragraph and move on:** the score test fits under the null,
computes *observed minus expected* in the forbidden directions, and checks
whether that leftover is bigger than the Fisher-information yardstick; the df is
the number of forbidden directions.

**References.**

- **Casella & Berger, *Statistical Inference* (2nd ed.), asymptotic-tests
  section (≈ §10.3).** Presents Wald, LR, and score together, which is the right
  first exposure — you learn each by its contrast with the others. *Primary
  reference for this rung.*
- **Agresti, *Categorical Data Analysis*.** If you want the score test in its
  logistic/binomial home turf (which is your setting), Agresti is gentler than
  the mathematical-statistics texts and the examples are pairwise/binary. Good
  complement.
- **Wasserman, *All of Statistics*.** Fine for the Wald test and the overall
  testing framework, but light on the score test specifically — do not rely on
  it for this rung.

**Self-check (Rung 1).**

1. Why is the $\beta_1$-block of the score zero at the restricted fit?
   *(Because you maximized over $\beta_1$ — stationarity.)*
2. In one sentence each, how does the score test differ from Wald and from LR?
3. Where do the degrees of freedom come from?

---

## Rung 2 — score tests in GLMs, i.e. "omitted directions"

"Omitted directions" is not textbook vocabulary — it is the geometric name for
testing that a subset of coefficients is zero in a GLM, which classically
appears as **testing a linear restriction** or **comparing nested GLMs** (the
score-test analogue of analysis of deviance). Same object, searchable under
those terms.

**The one fact that makes your case clean — do not skim it.** In a GLM with the
**canonical link**, the score has the tidy form

$$
U \;=\; y - \mu \;=\; \text{observed} - \text{expected}.
$$

For the binomial with the logit link (which *is* canonical), that is

$$
U_e \;=\; w_e - k_e\,p_e ,
$$

observed wins minus expected wins, per edge. The canonical link also makes the
Fisher information **diagonal** here,

$$
I \;=\; \operatorname{diag}\!\big(k_e\,p_e(1-p_e)\big),
$$

which keeps the quadratic form simple. If you read a treatment using a
non-canonical link, the score will not have this form and you will be confused
about why yours is so clean — yours is clean *precisely because* logit is
canonical for the binomial. Hold that as the reason.

**Extract this:** "test that these extra coefficients $\beta_2$ are zero, having
fit only $\beta_1$" is a GLM score test; under the canonical link the leftover
score is observed-minus-expected and lands in the $\beta_2$ directions; the df
is $\dim(\beta_2)$. That is structurally your test — your "$\beta_2$ directions"
are the harmonic directions.

**References.**

- **McCullagh & Nelder, *Generalized Linear Models*.** The standard. Dense; you
  need only the slice on the score test for added variables / nested models, and
  the canonical-link score form. Do not read all of it.
- **Agresti, *Categorical Data Analysis* (again).** Friendlier for the logistic
  case; look up "score test" and "residuals for GLMs / nested models."

**Self-check (Rung 2).**

1. Why does the canonical link give score = observed − expected?
2. If you tested "these 3 extra covariates are zero," what would the df be, and
   where would the leftover score live?
3. Why does a non-canonical link break the tidy form?

---

## The bridge — textbook → our construction

*This is the core. No book contains it.*

You will not find "harmonic-subspace score test" in any text, because you (and
effectively the field) just constructed it by **choosing the omitted directions
to be the harmonic subspace**. Here is the exact rename, line by line. When
these renames become automatic, the "novel scary object" collapses into "the
standard GLM score test, pointed at $\mathcal H$."

| Textbook GLM score test | Our harmonic-zero construction |
|---|---|
| natural parameter, coefficients split $(\beta_1,\beta_2)$ | log-odds flow $\eta \in \mathbb R^{E}$, Hodge-split into $S = \operatorname{im}D_0 \oplus \operatorname{im}D_1^{\mathsf T}$ (kept) and $\mathcal H$ = harmonic (tested-zero) |
| $H_0 : \beta_2 = 0$ | $H_0 : \eta \in S$, i.e. $P_{\mathcal H}\,\eta = 0$ — the harmonic component of the true log-odds is zero ("no genuine cycle") |
| fit under $H_0$ (only $\beta_1$) | constrained MLE $\hat\eta = M\hat\beta$, fit inside $S$ ($M$'s columns are a basis for $S$) |
| score $U = y - \mu$ (canonical link) | $U(\hat\eta) = w - k\,\sigma(\hat\eta) =$ observed − expected wins |
| $\beta_1$-block of score is $0$ at the restricted fit | stationarity of the constrained fit: $M^{\mathsf T}U(\hat\eta) = 0$ |
| leftover score lives in the $\beta_2$ directions | $U(\hat\eta) \perp S$, so $U(\hat\eta) \in \mathcal H$ — the harmonic subspace, exactly |
| $\chi^2$ with $\mathrm{df} = \dim(\beta_2)$ | $\chi^2$ with $\mathrm{df} = b_1 = \dim(\mathcal H)$ |

**The two framings are the same thing.** The textbook splits coordinates into
$(\beta_1,\beta_2)$. Yours parametrizes the kept subspace $S$ by $M$ and reads
off the orthogonal complement. They coincide:

$$
\beta_2 = 0 \iff \eta \in S \iff P_{\mathcal H}\,\eta = 0,
$$

and "leftover score in the $\beta_2$ directions" $\iff$ $U \perp S \iff U \in
\mathcal H$, because the Hodge decomposition is orthogonal, so $S^{\perp} =
\mathcal H$. Do not let the change of dress confuse you — it is a
reparametrization, not a different test.

**The by-construction harmonic landing, spelled out** (this is the
$4.1\times10^{-13}$ fact). The constrained fit satisfies
$M^{\mathsf T}U(\hat\eta) = 0$ — that is just "the gradient vanishes in the
directions you fit over." The columns of $M$ span $S$, so this says $U(\hat\eta)$
is orthogonal to **all** of $S$. Orthogonal-to-$S$ is, by the orthogonal Hodge
split, exactly $\mathcal H$. Therefore

$$
U(\hat\eta) \in \mathcal H \quad\text{exactly}
$$

— nobody applied a harmonic projection; the stationarity condition of the
constrained fit *forced* it there. The measured `score_off_harmonic`
$\le 4.1\times10^{-13}$ is the true value ($0$) plus floating-point residue.
That is the empirical confirmation that the geometry did what the geometry must.
"The test lives in harmonic coordinates" is **literal**: the object being tested
is always a vector in the $b_1$-dimensional harmonic space, and the whole test is
"is this harmonic vector bigger than binomial noise."

---

## Three things not to blur while reading

1. **Canonical link is load-bearing.** The clean observed − expected score *and*
   the clean orthogonal-complement landing both depend on the logit link being
   canonical for the binomial. If a source uses a different link, expect mess —
   and know it is not your case.

2. **Wald vs. score.** You will meet the three tests together and it is easy to
   walk away with a mush. Tag the score test as **"the constrained-fit one."**
   That is the one your construction uses, and "fit under the null" is precisely
   what makes the leftover-score geometry work. Wald would fit the full model and
   destroy the by-construction landing.

3. **$I^{-1}$ does not preserve $\mathcal H$, so $T$ is not $\|U\|^2$ rescaled.**
   The score lands in $\mathcal H$ exactly, but the metric does not respect that
   subspace: $I$ is diagonal in the *edge* basis, not in the $(S,\mathcal H)$
   split. So $T = U^{\mathsf T} I^{-1} U$ genuinely carries the $k_e$ and $p_e$
   dependence, and cannot be read as a rescaled norm of the harmonic component.
   This matters twice — it is where PP4's small-edge-count worry actually lives,
   and it is the step where a careless reading of DZW's studentization would
   "simplify" the statistic into something that is not this test.

---

## The target sentence

*Say this cold and you own it.*

> Our test is the classical **Rao score test for omitted coefficients in a
> canonical-link GLM**, where the omitted directions are chosen to be a basis for
> the harmonic subspace $\mathcal H$. We fit the log-odds under "no harmonic"
> ($\eta \in S$); the constrained fit's stationarity condition forces the
> leftover score $U = \text{observed} - \text{expected}$ to be orthogonal to $S$,
> hence into $\mathcal H$, **by construction** — not by any projection we
> applied. The statistic is the squared size of that harmonic score against the
> Fisher-information metric, $\chi^2$ with $b_1$ degrees of freedom.

When that sentence is yours without notes, RAN-31's score-test side is owned, and
DZW §3.3.2 becomes a matter of checking whether their fold arrives at the same
statistic.

---

## Then, and only then: DZW §3.3.2

You are checking **one identity**: that DZW §3.3.2, instantiated with

- $H_0 =$ the subspace constraint $\eta \in S$,
- the estimator $=$ the $S$-constrained MLE, and
- the test function $g =$ the harmonic directions,

produces this same score test. Line up four things as you read:

1. **their moment condition** — should be "residual $\perp g$"; with
   $g =$ harmonic, it is testing harmonic-direction signal;
2. **the estimator they plug in** — should be the constrained MLE, the same fit
   whose stationarity you now understand;
3. **the studentized statistic** — should reduce to a quadratic form in the
   held-out harmonic score;
4. **the df** — should come out $b_1$.

If those align, DZW in the fixed-graph case **is** the test above — "checking a
thing against itself" — and you can say so in your own words: both roads fit
under "no harmonic" and test the leftover harmonic signal against noise; the
score test does it in-sample via stationarity, DZW does it cross-fit via folds,
and in the fixed-graph case they are the same statistic.

**Where to stop — this is permission, not a limit.** There is a further piece in
DZW §4: the debiasing correction, the geometric-series $(I + B)^{-1}$ factor.
That is **not today's job**. It is for the case where the harmonic loops $g$ are
chosen *from the data* (adaptive / post-selection), where the score test is
invalid and the fold is what restores validity. That is the genuinely hard part,
it is the reason DZW matters beyond the fixed case, and it is the right question
to bring the specialist.

So if you follow §3.3.2 to the fixed-case identity and then hit the
$(I + B)^{-1}$ debiasing and lose the thread — **that is a finished, successful
reading.** You will have confirmed what RAN-31 needs for the fixed-graph claim
and located the exact boundary:

> "I follow it up to the debiasing correction for the selected case, and that's
> where I need you."

That sentence is the sharpest thing you could walk into the seminar with.

---

## Consolidated self-check

*The "advanced undergrad asking why" pass. If you can answer these without notes,
you are ready for DZW.*

1. **Why the score test and not Wald or LR?**
   *(Fits under the null → matches DZW, gives the by-construction geometry.)*
2. **Why is the leftover score orthogonal to $S$?**
   *(Constrained-fit stationarity: $M^{\mathsf T}U = 0$.)*
3. **Why is orthogonal-to-$S$ the same as harmonic?**
   *(The Hodge split is orthogonal, so $S^{\perp} = \mathcal H$.)*
4. **Why is the score observed − expected here?** *(Canonical/logit link.)*
5. **Why $\mathrm{df} = b_1$?** *($b_1 = \dim\mathcal H$ = number of omitted
   directions = codimension of the constraint.)*
6. **What is `score_off_harmonic` $\le 4.1\times10^{-13}$ confirming?**
   *(That $U(\hat\eta) \in \mathcal H$ is exact; the tiny number is
   floating-point residue, not a modeling choice.)*
7. **Why is $T$ not just the squared norm of the harmonic score?**
   *($I^{-1}$ does not preserve $\mathcal H$; the metric carries $k_e$, $p_e$.)*
8. **What are you checking in DZW §3.3.2, and where do you stop?**
   *(Whether their fold gives the same statistic; stop at the §4 selected-case
   debiasing.)*
