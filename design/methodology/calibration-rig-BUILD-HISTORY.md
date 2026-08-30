# Calibration rig — build history

How the rig in `rig/` was built: spec v2 through v7, six defects, and the three
findings that outlived the build. Folded in from
`design/reports/calibration-rig-build-report.html`, a hand-authored page that had
no regeneration path and went stale three times before it was dissolved.

**Nothing here is a live number.** Every measurement the original carried has
since been re-homed — identities and closed forms into `evidence/evidence.json`
(indexed in `evidence/PROVENANCE.md`), the residual into
`experiments/bias-of-bias/`, the `b1=0` rate into `experiments/b1-rate/`. Where a
figure appears below it is quoted as *what was measured at the time*, because the
sentence is about the defect it exposed, not about the value. Claim ids in
brackets point at the registry entry that owns the current number. Anything you
would cite, cite from there.

---

## What was built

A known-answer harness that manufactures comparison data with controlled
gradient, curl and harmonic structure, so the rankability certificate can be
checked against ground truth before an LLM judge is ever attached.

Two vertex populations: integers, which carry a genuine total order, and complex
numbers on the unit circle, which carry none — ℂ is not an orderable field. Edges
between them fall into three blocks with deliberately chosen Hodge signatures,
and the whole point is that the three stay separable.

| block | flow rule | signature | under more data |
|---|---|---|---|
| I–I | sparse noisy BTL log-odds, plus an injected misspecification `eps` | gradient + null | decays to a floor of exactly `eps²` |
| C–C | rotational rule on the circle | harmonic on `empty`, curl on `observed` | persists — this is the signal |
| I–C | the bridge: coin flip, or a fabricated surrogate order | variance or gradient, by mode | three reference lines |

Everything measuring those flows comes from `hodge.py` at the repo root,
byte-identical to `design/reference/hodge.py` — same SHA-256, so version control
itself is the proof that no operator, projector or entry point was forked. That
check still holds: both read `f9fccc811789d2a15687aee4d9747a85f2d24f16760f406b5d05d3e75a56a117`.

**Two entry points, two different tests** — not two ways to run one test.
`analyze_flow` (default `filling='empty'`) validates the decomposition on a flow
whose real values the rig knows. `analyze_comparisons` (default
`filling='observed'`) validates the round trip through the actual judgment-log
pipeline. Their defaults differ *by design*, which is exactly why the rig passes
`filling` explicitly to both and logs it, and never relies on a default.

## How the specification changed

The spec arrived at v2 and left at v7. Each revision was forced by a
measurement, and the order matters — later findings only became visible once
earlier ones were fixed.

| rev | what changed, and what forced it |
|---|---|
| v3 | Probed the instrument against its own documented oracles *before* designing. All held. §10 did not — see defect 1. |
| v4 | θ-asymmetry demoted from the floor axis to a robustness axis: `P_h·D0θ = 0` identically, so no γ can produce a budget-independent floor. Misspecification `eps` became the floor axis, with oracle `eps²`. [`gradient-annihilated`, `eps-squared-floor`] |
| v5 | Regime-validity preconditions added after the default `beta = 0.6` was found to saturate the clamp and produce a plausible-looking but wrong floor. [`saturation-gate`] |
| v6 | Reconciliation against the as-built code: derived fit window (Delta A), seed-drop reporting, an extended `k` grid (Delta D), strict xfail (Delta F). |
| v7 | `rho` optimised, which closed most of the residual. |

## The six defects

### 1 · spec · §10 — A single row per pair encodes nothing

Found before any rig code existed, by probing the instrument against its own
docstring. `analyze_comparisons` sets `clamp = 1/(2k)`; at `k = 1` that clips `p̂`
to exactly 0.5, and `log(0.5/0.5) = 0` on every edge. Measured
`total_mass = 0.000000`. The spec's prescription for emitting a ±1 rule silently
produced an empty flow.

**Fix.** Row counts floored at 2 with a loud error, never a silent default. The
floor turned out to be necessary and not sufficient — see defect 4.

### 2 · spec · §2.6 · §8.5 — The fit window, not the separation parameter

The spec's default `beta = 0.6` pushes edge probabilities to 0.0017, so wins
saturate at 0 or `k`, the clamp fires on 27% of edges at `k = 16`, and the emitted
flow grows as `log(2k)` instead of decaying. The fitted floor read 0.2591 against
a true 0.0900 — an entirely plausible number.

What caught it was the c-oracle: fitted 9.44 against a delta-method prediction of
70.07. That guard had been accepted into the spec one revision earlier and earned
its keep against the spec's own default before a line of rig code existed.

But lowering `beta` was the wrong repair. At `beta = 0.25` the c-oracle reads 1.01
— essentially perfect — while the floor is still 1.86× too high. **The guard is
necessary and not sufficient.** The variable that actually binds is which points
the fit is allowed to use: `floor + c/k` is a straight line in `1/k`, so the floor
is just the intercept, and fitting the whole grid lets the small-`k` end — where
the `O(1/k²)` logit-bias term lives — dominate the least squares.
[`guard-blind-spot`, `fit-window`]

### 3 · spec · §2.6 · §4 — `fit_k_min = 64` was calibrated on the wrong filling

One layer deeper, the constant is itself not a constant. It was calibrated on
`filling='observed'`, while §4 makes `'empty'` the rig default — and on the same
graph `b1` and `c_oracle` move by nearly an order of magnitude between the two.
[`filling-dependence`]

**Fix (v6, Delta A).** The window is *derived*, not declared:
`required_fit_k_min = c_oracle / (rho · floor)`. `fit_k_min = 64` survives only as
a floor on the default budget, and a `k` grid that cannot reach the derived value
is flagged `grid_insufficient` rather than fitted anyway. This dissolves the
observed/empty fork — both fillings recover given a grid that reaches the
requirement — so no per-experiment filling commitment is needed for the floor.

### 4 · code · §10 — Three emission paths that are not interchangeable

Flooring row counts at 2 was not enough. Pushing a ±1 rule through the
*quantized* emitter at `k = 2` computes `round(2·σ(1)) = 1` — a 1–1 tie — which
the clamp pins straight back to zero. The same trap, one level down.

And the path that avoids it introduces its own. Emitting a ±1 rule as "all R rows
one way" produces `±log(2R−1)`. Mass fractions are scale-invariant, so that is
exact for a config that is *entirely* a sign rule — but in a mixed config it
rescales the C–C block against its neighbours by 2.7× and changes the very mix
being measured. That was a round-trip error of 0.269 masquerading as a
decomposition result.

**Both failure modes produce a well-formed decomposition rather than an
exception, which is what makes them dangerous.** The rig now raises when a whole
flow quantizes away, counts the edges lost to ordinary rounding, and refuses the
`sign` path in any config that is not entirely a sign rule.

### 5 · test · §8.8 — A test that asserted the wrong thing

The first §8.8 test claimed ζ would report perfect consistency on the
equal-spaced complex pool. It reads 0.0 — maximally *in*consistent. On a complete
graph every triple is observed, so ζ sees the cycles perfectly well; the harmonic
reading of 1 on `empty` is a filling choice, and the same flow is pure curl on
`observed`. ζ's blindness needs triangles that are **missing**. The test now
builds a 4-cycle beside a transitive triangle: ζ sees only the one triple it can,
finds it perfectly transitive, and reports 1.0 while a third of the flow's energy
is harmonic and unrankable. That is the claim §8.8 actually makes.
[`zeta-blind`]

**The rig was right and the test was wrong.** Worth recording, because a green
suite that asserts the wrong invariant is worse than a red one.

### 6 · code · §8.5 — Seeds were being dropped silently

A mask with `b1 = 0` has no harmonic direction to inject into, so
`floor_measurement` skipped it — quietly, at 5–16% of seeds. That is a real
reduction in sample size: a confidence interval computed from 54 seeds must not
be read as though it came from 64. `seed_drop_rate` now ships in every record
alongside `grid_insufficient`. Same class of defect as the ones the spec already
guards, and the same fix — report it rather than absorb it.

### A tally that did not survive the fold

The original masthead read "6 defects found … five of the six were in the
specification." Its own body tags say otherwise: spec, spec, code, test, code,
with the §2.6·§4 finding sitting untagged inside the second and Delta D's budget
shortfall untagged entirely. Three in the spec, two in the code, one in a test.
Recorded here rather than carried forward, because a summary tally is exactly the
kind of number that drifts away from the thing it summarises.

## Reconciling the spec to the build (v6)

The v6 change-set arrived with two values marked **CONFIRM** — check the shipped
code before locking. Both confirmed. One of the two proposed fixes turned out not
to do what it was expected to.

| default | claimed | measured | verdict |
|---|---|---|---|
| `beta` 0.3 → 0.25 | ~47% of masks rejected at 0.3; 0.25 gives 0% | 43.5% at 0.3; 0.5% at 0.25 | adopt |
| `n_int` 8 → 12 | 28.8% of masks have `b1=0`; 12 fixes it | 12 gives 10.8%; 14 gives 11.9% | adopt, **other reason** |

`beta` confirmed cleanly — 0.25 is not literally 0% rejection but 0.5%, and 0.22
would be zero. [`saturation-gate`]

`n_int` is the interesting one. No value of `n_int` drives the `b1=0` rate to
zero, and the floor measurement had already forced `n_int ≥ 12` — making the
change a no-op on the path it was meant to fix. What it *does* fix is a different
one: under the rig's own default `filling='empty'`, `n_int = 8` makes `assemble()`
raise on 1.75% of seeds, and 12 takes that to zero. **Adopted for that reason, not
the stated one.** [`b1-non-monotone`]

### Delta D — the `k` grid could not reach its own window

Delta A made the window derived, and the default grid then could not satisfy it.
At `eps = 0.1` the requirement is `k ≈ 516`; a grid topping out at 1024 had a
single point above that, so the fit fell back and raised `grid_insufficient`.
**The guard worked. The budget did not.** Extending to 4096 cost 1.7 s against
1.6 s and removed the insufficiency entirely (`grid_insufficient` 4/20 → 0/20,
worst γ-drift 38.0% → 11.8%). It did not fix CI coverage.

Worth stating plainly: a first pass at a single γ suggested the extension had
closed both failing cells. Measured across all γ, it had not.

### Delta F — a strict exception that deleted itself

Delta F held the §8.5 criterion strict rather than widening the tolerance around
the known failing cells, and required any encoded exception to be
`xfail(strict=True)`. That paid off within the hour: once the `k` grid was
extended the exception XPASSed — which under strict is a failure — forcing it to
be deleted rather than carried on as a stale exemption nobody rechecks. A widened
tolerance would have absorbed the improvement silently and left the residual
invisible.

## Three findings that outlived the build

### Why figures are stated as distributions

The original report went stale twice on the same class of number, both times for
the same reason: a quantity that varies from run to run was quoted from a single
run. The residual was reported as "3–6%", then "~2.6%"; coverage as "15/16".
Re-measured over 20 independent base seeds, the residual was 1.6% ± 0.2% and
coverage typically 13/16 — so the earlier figures were not wrong so much as
over-precise, each one a draw from a distribution about a percentage point wide.

Adding `rho` to the config was what exposed it: `derive_seed` hashes the config
fingerprint, so a new field reseeds every mask, and numbers that looked settled
moved. That is the rig behaving correctly — the same estimator on a different
draw.

This is where the repository's convention comes from. A quantity that varies
across seeds is quoted with its mean, standard error and range over base seeds;
`experiments/harmonic-zero-null/results/seed_spread.json` is that rule applied to
the score test, and [`residual-exact`] is it applied at the limit, with Monte
Carlo removed entirely so the base-seed spread can be read directly.

**And the postscript this fold adds.** Stating the spread was not sufficient. The
report kept drifting because it had no regeneration path: nothing could re-derive
its numbers, and so nothing could tell you they had moved. That is the same
failure `rig/provenance.py` now catches for JSON artifacts, one medium over. The
fix for prose is different and simpler — don't keep the numbers in prose. Cite
the registry.

### The Epic-C topology problem, in miniature

Two findings here looked like separate nuisances and are the same object.
`n_int = 8 → 12` did not fix the `b1 = 0` rate, and extending the sweep showed why
it never could: the rate is non-monotone in `n`, with an interior minimum, not a
plateau. (An earlier revision of the report called it a plateau, on evidence that
stopped at `n = 14`. It rises.) And the `k ≥ 64` window, calibrated on `observed`,
under-read the floor on `empty` because `c_oracle` moved by nearly an order of
magnitude. [`b1-non-monotone`, `kahle-finite-n`, `filling-dependence`]

Both say the same thing: **`b1` is a property of the graph, not of the item
count**, so every constant derived from `P_h` — the floor, the variance term, and
therefore any threshold — is a function of the actual comparison topology. The
mechanism behind the rise: at fixed edge retention, more items means more
*observed triples*, and filling them destroys the very holes the certificate
reads. Past the optimum, collecting more data drives sensitivity toward zero.

**The consequence for Epic C.** A null calibrated on one topology does not
transfer to another, so there is no universal threshold to ship. What the rig
provides is a procedure: given a deployment's own comparison graph, generate the
matched null and derive the window for it. A live matcher's threshold has to be
recomputed whenever the comparison *pattern* shifts — not only when the item set
does.

### A guard is only as good as the thing it is allowed to fail

Three of the six defects share a shape. The c-oracle passed while the floor was
1.86× wrong; the two bad emission paths returned well-formed decompositions
rather than exceptions; the dropped seeds shrank the sample without shrinking the
reported `n`. In each case a check existed and reported success. What was missing
was not a guard but a *second, independent* quantity the guard could be
contradicted by — the derived window against the fitted one, the round-trip
residual against the internal `(g,c,h)`, `seed_drop_rate` against the seed budget.
That is the pattern the experiment layer inherited, and it is why every probe
ships its refusals alongside its verdicts.

---

## Where the original's numbers went

| the report carried | it now lives in |
|---|---|
| residual `+0.43% ± 0.09%` over 20 base seeds | `experiments/bias-of-bias/`; [`residual-exact`] |
| `b1=0` rate at `n = 6` and `n = 12` | `experiments/b1-rate/B1-RATE.md` |
| floor recovery vs `eps²`, the fit-window intercepts | [`eps-squared-floor`, `fit-window`] |
| the c-oracle blind spot, the saturation gate | [`guard-blind-spot`, `saturation-gate`] |
| the §8.1–§8.10 acceptance table | `tests/test_acceptance.py`, which *is* the table |
| the §5.1 ±1 correction (`0.200` at `n=5`, `0.2222` at `n=6`) | [`pm1-trap`] |
| a module/line-count inventory | dropped: line counts drift and nothing checked them |

Point-in-time record, generated against spec v7, 2026-08-19. Folded into
`design/methodology/` on 2026-08-30 and the `design/reports/` directory removed.
The HTML original is a total rewrite away, so `--follow` will not track it; read
it directly instead:

```bash
git show 7754e70:design/reports/calibration-rig-build-report.html
```
