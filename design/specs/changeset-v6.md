# calibration-rig-spec.md — v5 → v6 change-set

**Status:** **APPLIED** at `48cb223`, which created this file and made the v6 revision in the same commit — so "draft for review" was never accurate, and the spec has since moved to v8. Retained as the record of what v6 changed and why, not as a live proposal. It was applied as a single v6 revision on the **canonical (Code-side) file**. The claude.ai side does not maintain a parallel spec (see the superseded-v3 incident); this is a patch spec, not a replacement document.

**Why v6 exists, in two lines:** the build overtook the v5 spec. The fit window and the emitter both became *more correct in code than in spec* during the build, and the ~10% residual the v5 note parked was mostly closed. v6 reconciles the spec to the as-built instrument and records what genuinely remains open.

**Markers:** **CONFIRM** = Code must check the shipped value before locking. **DECISION** = Meadowlark's call. Every delta cites its build evidence (now [`../methodology/calibration-rig-BUILD-HISTORY.md`](../methodology/calibration-rig-BUILD-HISTORY.md)); the Settled/Retracted discipline carries over.

---

## Delta A — §2.6 fit window: hardcoded `k ≥ 64` → derived window

**Locate:** the "Fit window (the binding control)" block, including `require fit_k_min >= 64`, and the default line `fit_k_min >= 64 (fitting)`.

**Change:** replace the fixed floor with a *derived* requirement.

> The fit window is derived, not declared:
> `required_fit_k_min = c_oracle / (ρ · floor)`
> with `c_oracle = tr(P_h · diag(1/(p_e(1−p_e))))` (§7) and `ρ` a resolvability margin.
> A `k` grid that cannot reach `required_fit_k_min` is flagged `grid_insufficient` and **not fitted** (loud) — never fitted anyway on a short grid.
> `fit_k_min = 64` is retained only as a floor for the default budget; the derived value governs.

**Why:** the constant 64 was itself calibrated on `filling='observed'`, so it is wrong under any filling with a different `c_oracle`. Measured on one graph, eps=0.3, true floor 0.090:

| filling | b₁ | c_oracle | floor @ k≥64 | floor @ k≥256 |
|---|---|---|---|---|
| observed | 2 | 17 | 0.0807 | 0.0850 |
| empty | 20 | 160 | 0.0156 | 0.0726 |

The derived window makes **both** fillings recover given a grid that reaches the requirement, which **dissolves the observed/empty "fork"** — no per-experiment filling commitment is needed for the floor. It **also closed the residual under-estimate the v5 top-note parked**: deriving the window took recovery from 0.87–0.95× to 0.94–1.01× (the fixed window was slightly short). Remainder in Delta D.

**Keep:** the full-grid vs `k≥64` vs `c₂/k²` comparison table and the "drop the low-k points, don't model the term" verdict — the `c₂/k²` row (0.68×–0.90×, drift → 28%, eats the intercept) still justifies *why* we truncate rather than add a quadratic. Reframe so `k≥64` reads as an *illustration on the observed graph*, not the rule.

**Evidence:** build report §2.6·§4, the derived-window fix.

---

## Delta B — §10 emission: `R ≥ 2` floor → three emission paths + collapse guard

**Locate:** the "Emission rules by generator" list and the v3 CORRECTION box (`R ≥ 2`).

**Change:** `R ≥ 2` is necessary but not sufficient. Specify three *paths*, chosen per block, plus a collapse guard.

- **counts** (noisy-BTL null): replay the generator's own win counts → **bit-exact** (measured diff 0.00e+00).
- **sign** (±1 rules — C–C rotational, `variance_fixed`): emit R rows one way → `±log(2R−1)`. Exact **only if the config is entirely a sign rule**; in a mixed config it rescales the C–C block against its neighbours (~2.7×) and *changes the mix being measured* — a 0.269 round-trip error that presents as a decomposition result. The rig **refuses the sign path in any non-sign-only config**.
- **magnitude** (clean-gradient I–I, `bias_rule` bridge): `w = round(k·σ(Y))`; **report the residual** `‖Y_achieved − Y_target‖`; exact only as `k → ∞`.

**Collapse guard:** flooring at R=2 is not enough — a ±1 rule through the quantized emitter at k=2 computes `round(2·σ(1)) = 1` (a 1–1 tie), which the clamp pins back to zero. The rig **raises when a whole flow quantizes away** and **counts edges lost to rounding**. `analyze_comparisons` derives k per pair, so mixed row counts are legal.

**Why:** both failure modes produce a *well-formed* decomposition rather than an exception — that is exactly what makes them dangerous.

**Evidence:** build report §10 CODE defect.

---

## Delta C — §8.8 ζ-blindness: add test-construction guidance

**Locate:** the §8.8 acceptance clause ("ζ … misses the harmonic … where triangles are unfilled").

**Change:** the *claim* is correct and stays. Add construction guidance so the test is not built on the wrong graph:

> The ζ-blindness demonstration requires **missing triangles**. Do **not** use the equal-spaced complete complex pool: on a complete graph every triple is observed, so ζ reads the C–C cycles correctly (ζ = 0.0 there), and the harmonic reading of 1 exists only under the `empty` filling choice — the same flow is pure curl on `observed` (§8.3: observed c = 1.0). Construct a **4-cycle beside a transitive triangle**: ζ sees only the triple it can, reports 1.0, while ≥ ⅓ of the flow's energy is harmonic and unrankable (measured ζ = 1.0 while h > 0.3).

**Why:** a green suite asserting the wrong invariant is worse than a red one; the first §8.8 test asserted ζ-perfect-consistency on the complete pool and was wrong.

**Evidence:** build report §8.8 TEST defect.

---

## Delta D — update the parked "~10% residual" note

**Locate:** the v5 top-note "Known residual: … stable ~10% under-estimate … To be characterised during the build."

**Change:** it was partly characterised and mostly closed. Rewrite:

> **Residual (post-build):** a stable **3–6%** negative bias remains (down from 10–13% once the window became derived — plausibly the same mechanism, not fully removed). At 64 seeds the CI is tight enough that this can push it just below the oracle: `ci_covers_oracle` is false in **two cells**, **eps = 0.1** (resolvability — near the grid's reach) and **eps = 0.4** (the residual bias against a tight CI). Open: whether tuning **ρ** or lengthening the `k` grid removes it — ρ is currently *justified, not optimised*. All of `grid_insufficient`, `floor_over_oracle`, `c_ratio_median`, `saturation` ship in every record. **Post-build tuning, not a blocker.**

**Evidence:** build report "What remains open."

---

## Delta E — config defaults (**CONFIRM** before locking v6)

**Locate:** the §2.6 default line and the config schema (§3).

The build report does not state the final shipped `beta` / `n_int` defaults; the ratification snapshot had:

- `beta = 0.3` — sits on the saturation line (~47% of masks ≥ 0.2 at n=12 → regime rejection). **CONFIRM**; if unchanged, move default to **0.25** (0% rejection, p95 saturation 0.175).
- `n_int = 8` — under `observed`, ~29.5% of masks have b₁ = 0 → `flows.harmonic_unit` raises. **CONFIRM**; if unchanged, move default to **12**.

The suite is green because §8 tests pass *explicit* good configs; a bare `python -m rig.sweep` may still hit these. Fix in `config.py` and the spec default line together.

**Evidence:** ratification findings; build inventory (`config.py`, "every trap fails loudly").

---

## Delta F — §8.5 acceptance criterion (**DECISION**: keep strict)

**Locate:** the §8.5 criterion "floor CI must cover eps²."

**Recommendation:** **keep it strict.** The two failing cells (Delta D) are visible and flagged; loosening the criterion would hide exactly the residual ρ-tuning is meant to remove. Document the known exceptions in §8.5 rather than widening the tolerance — this matches Code's stance in the report ("recorded in the spec rather than smoothed over").

**Meadowlark's call:** hold strict + document, or set a stated tolerance tied to the characterised residual (only *after* ρ is optimised).

---

## Optional — consolidate revision history

The v2→v5 notes have become a palimpsest with retractions. v6 could fold them into a single "History" appendix (net state + what each revision retired) so the head of the file states the *current* model without the reader reconstructing it. Cosmetic; do only if the clean iteration is worth the churn.

---

## To finalise v6

Resolve **Delta E** (two CONFIRMs) and **Delta F** (one decision); Deltas A–D are ready as written. Hand to Code to apply as one revision on the canonical file, and reconcile against the as-built tree (the code already leads the spec on A, B, and C).