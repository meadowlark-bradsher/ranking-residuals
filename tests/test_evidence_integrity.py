"""`evidence.json` must hold the numbers its generator wrote, and until now nothing asked.

The registry's whole purpose is that every cited number is reproducible. What
guarded that was narrower than it looked, and the gap was specific rather than
general:

  * `meta.source_fingerprint` hashes `generate.py`'s SOURCE. It is computed from
    the module and never touches the artifact, so a registry edited by hand
    beside an unchanged generator round-trips clean.
  * No test reads a claim value. Two tests open `evidence.json` at all --
    `test_source_fingerprint` for `meta`, `test_spec_conventions` for the claim
    KEYS to build a regex. Neither looks at a number.
  * `verify.py`, which does re-run every claim, is not part of
    `python -m pytest tests/ -q`.

So a registry whose numbers came from resolving a merge rather than from a
generator run passed the full suite green. That is the hole this file closes.

WHY THE TOLERANCE CHECK IS NOT THE SAME CHECK, which is the part that makes this
worth a separate guard rather than a note in `verify.py`. Of 33 claims, 13 are
stochastic and are compared only within a tolerance set wide enough to absorb a
different numpy -- six of them relative, one at 10%. Regeneration makes a
stochastic claim TRUE; a tolerance check makes it WITHIN TOLERANCE; the two
coincide only when the file actually came from the generator. Two nearby parents
of a merge usually differ by less than such a tolerance, so a merged registry is
close to the worst possible input for a tolerance check -- it is precisely the
case the tolerance was widened to forgive. `test_a_nudge_inside_tolerance_is_
invisible_to_drift_and_caught_by_the_digest` demonstrates exactly that, on a real
claim, rather than asserting it.

WHAT THIS DOES NOT CHECK, stated rather than implied. It does not stop someone
who edits a value and recomputes the digest; that is a different threat model and
this repo does not have one. It does not verify the numbers are CORRECT -- only
that they are the ones the generator emitted, which is what `verify.py` re-runs
and what the exact claims' machine-precision tolerances pin. And it says nothing
about `meta`, deliberately: `generated` and `commit` move when nothing measured
has, so a whole-file hash would go stale on every regeneration and be ignored
within a week.

THE FAILURE MODE THIS FILE MUST NOT HAVE is passing vacuously. A digest that was
absent, a `check` that returned None unconditionally, or a mutation that failed
to apply would all leave a checker asserting nothing. So the digest's presence is
asserted before it is used, and every detector is pinned on an input it is known
to catch -- including the mutation-applied guard, since two earlier attempts at
mutation testing in this repo silently did not apply and reported green.
"""

import copy
import importlib.util
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "design/methodology/evidence"

_spec = importlib.util.spec_from_file_location("registry", EVIDENCE / "registry.py")
registry = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(registry)


def _stored():
    return json.loads((EVIDENCE / "evidence.json").read_text())


def _first_leaf_path(value):
    """(path, number) for the first float leaf, walking dicts in sorted order."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return [], value
    if isinstance(value, dict):
        for k in sorted(value):
            sub, leaf = _first_leaf_path(value[k])
            if sub is not None:
                return [k] + sub, leaf
    if isinstance(value, list):
        for i, v in enumerate(value):
            sub, leaf = _first_leaf_path(v)
            if sub is not None:
                return [i] + sub, leaf
    return None, None


def _set_leaf(value, path, new):
    node = value
    for k in path[:-1]:
        node = node[k]
    node[path[-1]] = new


# --------------------------------------------------------------- vacuous-pass

def test_the_loader_loaded_the_module_it_names():
    assert registry.__file__ == str(EVIDENCE / "registry.py")
    assert registry.DIGEST_KEY == "claims_digest"


def test_the_registry_carries_a_digest_to_check():
    """Without this, every assertion below could pass on an absent field."""
    stored = _stored()
    assert stored["claims"], "evidence.json has no claims; the check is vacuous"
    assert registry.DIGEST_KEY in stored["meta"], (
        f"evidence.json carries no meta.{registry.DIGEST_KEY}. Regenerate with "
        f"generate.py -- an absent digest is unverifiable, not agreement.")


# ------------------------------------------------------------------- the gate

def test_the_shipped_registry_matches_its_digest():
    """THE GATE. The payload is the one the generator wrote."""
    problem = registry.check(_stored())
    assert problem is None, problem


# ------------------------------------------------------- pinning the detectors

def test_a_changed_claim_value_is_caught():
    stored = _stored()
    cid = sorted(stored["claims"])[0]
    path, leaf = _first_leaf_path(stored["claims"][cid]["value"])
    assert path is not None, f"{cid} has no numeric leaf to mutate; pick another claim"
    _set_leaf(stored["claims"][cid]["value"], path, leaf + 1.0)
    assert registry.check(stored) is not None, "a changed claim value went undetected"


def test_an_absent_digest_is_a_problem_and_not_agreement():
    stored = _stored()
    del stored["meta"][registry.DIGEST_KEY]
    problem = registry.check(stored)
    assert problem is not None and "unverifiable" in problem


def test_meta_churn_does_not_trip_the_digest():
    """`generated` and `commit` move when nothing measured has.

    Pins the scope choice directly: a whole-file hash would fail here, go stale
    on every regeneration, and be ignored inside a week.
    """
    stored = _stored()
    stored["meta"]["generated"] = "1999-01-01"
    stored["meta"]["commit"] = "deadbee"
    stored["meta"]["numpy"] = "0.0.0"
    assert registry.check(stored) is None


def test_the_digest_survives_a_round_trip_through_the_file_format():
    """Producer holds numpy scalars, reader holds parsed floats. Same digest.

    This is what the double serialization in `canonical` is for; without it the
    digest is written by one representation and checked against another, and the
    gate above would fail on a registry that is perfectly fine.
    """
    stored = _stored()
    reparsed = json.loads(json.dumps(stored, indent=1, default=float))
    assert registry.claims_digest(reparsed["claims"]) == \
        registry.claims_digest(stored["claims"])


def test_key_order_does_not_change_the_digest():
    """Canonicalization is by sorted keys, so a reordered file is not a change."""
    stored = _stored()
    shuffled = {"claims": {k: stored["claims"][k] for k in sorted(stored["claims"],
                                                                 reverse=True)}}
    assert registry.claims_digest(shuffled["claims"]) == \
        registry.claims_digest(stored["claims"])


# ----------------------------------------------- the reason this file exists

def test_a_nudge_inside_tolerance_is_invisible_to_drift_and_caught_by_the_digest():
    """The demonstration, on a real stochastic claim rather than a fixture.

    Takes a claim whose tolerance is relative, moves one leaf by half of it, and
    asserts BOTH halves: `verify.py`'s own comparison reports the claim fine, and
    the digest reports the payload changed. If the first assertion ever fails,
    the tolerance narrowed and this file's argument needs rewriting; if the
    second fails, the digest has stopped covering claim values.
    """
    sys.path.insert(0, str(EVIDENCE))
    try:
        import verify                                   # imports generate; a few seconds
    finally:
        sys.path.pop(0)

    stored = _stored()
    cid = next(c for c, v in sorted(stored["claims"].items())
               if v["kind"] == "stochastic" and v["tolerance"].get("kind") == "rel")
    tol = stored["claims"][cid]["tolerance"]
    original = copy.deepcopy(stored["claims"][cid]["value"])

    path, leaf = _first_leaf_path(original)
    assert path is not None and leaf != 0, f"{cid} has no usable numeric leaf"
    nudged = copy.deepcopy(original)
    _set_leaf(nudged, path, leaf * (1 + tol["value"] / 2))
    assert nudged != original, "the mutation did not apply; this test would be vacuous"

    ok, _, drift_seen, mism = verify.drift(original, nudged, tol)
    assert ok and not mism, (
        f"{cid}: a nudge of half its {tol['value']} relative tolerance was expected "
        f"to pass the tolerance check, but drift={drift_seen} reported failure. The "
        f"tolerance narrowed and this file's premise needs revisiting.")

    stored["claims"][cid]["value"] = nudged
    assert registry.check(stored) is not None, (
        f"{cid} moved by half a tolerance, verify.py called it fine, and the digest "
        f"did not notice -- which is the entire hole this file exists to close.")
