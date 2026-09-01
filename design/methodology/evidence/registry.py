"""Does `evidence.json` still hold the numbers its generator wrote?

Nothing answered that until now, and the gap was specific rather than general.
`meta.source_fingerprint` hashes `generate.py`'s SOURCE, so it detects the
generator changing meaning and says nothing about the artifact's contents -- a
hand-edited registry beside an unchanged generator round-trips clean. No test
reads a claim value: two open `evidence.json` at all, one for `meta`, one for the
claim KEYS. And `verify.py`, which does re-run the claims, is not part of
`python -m pytest tests/ -q`.

So a registry edited by hand -- most plausibly by resolving a merge in it rather
than regenerating -- passed the whole suite green.

WHY A TOLERANCE CHECK IS NOT THE SAME CHECK, which is the part worth stating.
Of 33 claims, 13 are stochastic and are only compared within a tolerance wide
enough to absorb a different numpy: five at 5% relative, one at 10%. Regeneration
makes a stochastic claim TRUE; `verify.py` makes it WITHIN TOLERANCE; those
coincide only when the file actually came from the generator. Two nearby parents
of a merge usually differ by less than such a tolerance, so a merged registry is
close to the worst possible input for a tolerance check -- it is exactly the case
the tolerance was widened to forgive. The 20 exact claims are held to machine
precision and would fail loudly; the stochastic ones are the hole.

The digest closes the accidental case, which is the one that happens: a merge
resolution, a hand-tweaked number, a partially-applied regeneration. It does not
stop someone who edits a value and recomputes the digest, and it is not meant to
-- that is a different threat model and this repo does not have one.

Deliberately NOT a hash of the file. `meta` legitimately changes when nothing
measured has: `generated` moves with the date, `commit` with the tree. Hashing
the whole document would go stale on every regeneration and teach everyone to
ignore it. The digest covers `claims` alone, which is the part that must not
move without a generator run.
"""

from __future__ import annotations

import hashlib
import json

DIGEST_KEY = "claims_digest"


def canonical(claims) -> str:
    """The claims payload as one deterministic string.

    Dumped twice on purpose. The first pass sends numpy scalars through
    `default=float`, exactly as `generate.py` does when it writes the file; the
    second re-serializes the parsed result, so the producer -- holding numpy
    types in memory -- and any reader -- holding the floats that came back out
    of the file -- canonicalize to the same bytes. Without the round trip the
    digest would be written by one representation and checked against another.
    """
    once = json.dumps(claims, sort_keys=True, separators=(",", ":"), default=float)
    return json.dumps(json.loads(once), sort_keys=True, separators=(",", ":"))


def claims_digest(claims) -> str:
    return hashlib.sha256(canonical(claims).encode()).hexdigest()[:16]


def check(registry) -> str | None:
    """None when the payload matches its digest; a sentence when it does not.

    An ABSENT digest returns a sentence rather than None. An artifact with no
    digest is unverifiable, not in agreement -- the same reading `provenance`
    takes of a missing fingerprint, and for the same reason: silence must not be
    counted as passing.
    """
    recorded = registry.get("meta", {}).get(DIGEST_KEY)
    if recorded is None:
        return (f"evidence.json carries no meta.{DIGEST_KEY}, so its payload is "
                f"unverifiable. Regenerate with generate.py.")
    fresh = claims_digest(registry["claims"])
    if fresh == recorded:
        return None
    return (f"evidence.json's claims do not match meta.{DIGEST_KEY}: recorded "
            f"{recorded}, computed {fresh}. The payload changed without a "
            f"generator run -- most likely a merge resolved inside the registry, "
            f"or a value edited by hand. Re-run generate.py rather than updating "
            f"the digest; a tolerance check will NOT catch this for the 13 "
            f"stochastic claims, which is why the digest exists.")
