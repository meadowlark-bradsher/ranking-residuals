# Exercises — operating the rig

Ten exercises for driving `hodge.py` and the calibration rig, in order. Each is a
script you run and then a set of questions you answer from its output. The answers
are in [`SOLUTIONS.md`](SOLUTIONS.md), which also gives the interpretation and, for
most of them, the wrong reading that the build history shows people actually reach
for.

They are ordered, and the order is the point: 1–3 are about what the instrument
computes, 4–7 about operating it, 8–10 about attributing what it reports and
knowing when to refuse. Later exercises assume earlier ones.

Every script is self-contained, writes nothing into the repository, and runs from
the repository root:

```bash
python design/exercises/ex01_filling_and_b1.py
```

All ten together took **5.5 s wall, 5.1 s CPU at load average 4.75** — quoted with
its load because an unpinned BLAS moved one of this repository's timings 11× with
ambient load, which is why every script here pins threads before importing numpy.
Exercise 4 is the only one that takes more than a second; it runs two full sweeps.

## Part I — what the instrument computes

| # | file | in one line |
|---|---|---|
| 1 | [`ex01_filling_and_b1.py`](ex01_filling_and_b1.py) | `b₁`, and how the 2-skeleton decides where harmonic mass may live |
| 2 | [`ex02_three_signatures.py`](ex02_three_signatures.py) | the two known-answer poles, and the oracle that pins them |
| 3 | [`ex03_pm1_quantization_trap.py`](ex03_pm1_quantization_trap.py) | a perfect ranking that reads as unrankable |

## Part II — operating the rig

| # | file | in one line |
|---|---|---|
| 4 | [`ex04_read_a_sweep_record.py`](ex04_read_a_sweep_record.py) | the same measurement at two budgets, and why one is unreadable |
| 5 | [`ex05_floor_recovery.py`](ex05_floor_recovery.py) | recover a floor whose answer is `eps²`, with a CI and a negative control |
| 6 | [`ex06_the_fit_window.py`](ex06_the_fit_window.py) | the floor is an intercept, so the fit window decides it |
| 7 | [`ex07_round_trip.py`](ex07_round_trip.py) | does the judgment-log pipeline reproduce what the rig put in |

## Part III — attribution, and refusing to answer

| # | file | in one line |
|---|---|---|
| 8 | [`ex08_bridge_attribution.py`](ex08_bridge_attribution.py) | three ways to get harmonic mass, and telling them apart |
| 9 | [`ex09_zeta_blindness.py`](ex09_zeta_blindness.py) | the baseline that calls unrankable data perfectly consistent |
| 10 | [`ex10_make_the_guards_fire.py`](ex10_make_the_guards_fire.py) | twelve deliberate misuses that must all raise |

## Two kinds of output, and the rule for quoting them

Every exercise here is **reproducible**: same code, same config, same numbers. The
rig derives its seeds from the config, so nothing depends on wall-clock time or an
un-set seed.

Reproducible is not the same as settled, and conflating the two is the mistake this
repository has made the most often. Exercises 1, 2, 3, 6, 9 and 10 print **exact
identities** — closed forms and machine-precision zeros. Quote those as they stand.
Exercises 4, 5, 7 and 8 print **one draw** from a distribution over base seeds. The
draw reproduces on your machine and will still differ from the next person's cell,
and from the shipped figure, by about what the spread says. Quote those with their
spread or by claim name, never as a point — spec §13.1, and the reason the root
README refuses to print its own residual.

When an exercise asks you to compare against a shipped number, get the number from
[`evidence.json`](../methodology/evidence/evidence.json) or its generated index
[`PROVENANCE.md`](../methodology/evidence/PROVENANCE.md), not from prose. Prose goes
stale quietly; the registry is re-run by `verify.py`.

```bash
cd design/methodology/evidence && python verify.py --fast
```

## What is pinned where

Each exercise names the spec sections it exercises and the registry claims it
touches, in its module docstring. Nothing in this directory is load-bearing for the
build: no test imports it, no figure reads it, and no claim is measured here. It is
a teaching surface over machinery that is pinned elsewhere, and it should stay that
way — an exercise that becomes the only place a number is checked has quietly become
part of the evidence chain without any of the guards that go with it.

The one thing that is enforced: each of these is run directly, so each is an entry
point that inherits no thread setting from a caller. Nine of the ten are listed in
`_PINNED_ENTRY_POINTS` in
[`tests/test_harness_rules.py`](../../tests/test_harness_rules.py), which checks
that the pin precedes the numpy import. Exercise 6 is the exception: it never names
numpy itself — `rig.fit` does — and that test matches a literal import, so its pin
is real, necessary, and unwatched. The comment at the pin says so.

## Adding an exercise

1. **It needs a known answer.** An exercise whose expected outcome is "some number
   comes out" teaches nothing and cannot go stale loudly. Either it is an identity,
   or it is pinned by a registry claim, or it is a deliberate failure.
2. **Run it and paste what it actually printed.** The expected outcome in
   `SOLUTIONS.md` is transcribed from a real run, not predicted. If you cannot run
   it, you cannot write its answer key.
3. **Say which kind of output it is.** If any printed quantity moves with a base
   seed, say so at the top of the answer and give it as a range or a claim name.
   The failure mode is not being wrong, it is being over-precise: a single draw
   quoted to four decimals reads as settled.
4. **Add the file to `_PINNED_ENTRY_POINTS`** in `tests/test_harness_rules.py` if it
   imports numpy, and pin the threads above the import. The suite will tell you if
   you forget the first; nothing but the pin itself catches the second.
5. **Number it, and add it to the table above and to `SOLUTIONS.md` in the same
   commit.** A table entry with no answer is worse than no entry.
6. **Do not measure anything new here.** If an exercise turns up a number worth
   citing, it belongs in the evidence registry with a tolerance and a test, and the
   exercise should then quote the claim.

   Exercise 3 is the worked example. Its `(n−2)/(3n)` closed form started as a
   derivation in `SOLUTIONS.md`; it is now claim `pm1-closed-form`, generated by
   `evidence/generate.py` and pinned by `test_5_1_pm1_mass_has_a_closed_form_in_n`.
   The exercise still spells the formula out rather than importing it — predicting
   the instrument's output is the exercise, and reading the prediction from the
   file that stores the answer would make it circular — but the formula is now
   checked in two places that are not this directory.
