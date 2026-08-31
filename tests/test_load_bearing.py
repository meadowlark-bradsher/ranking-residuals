"""`.load-bearing/manifest.json` describes regions of this repo. A description that outlives what it describes is worse than none.

This is the same argument `test_readme_layout` makes about the README's tree,
made about a second document, and it is made here for the same reason: every
convention in this repo that survived got structural backing, and the ones that
drifted were the ones a person had to remember. The manifest is prose about
code, written by an agent, in a file no compiler reads. Nothing about it fails
when the code moves underneath it.

WHY THIS IS CHECKABLE AT ALL, when prose usually is not: every member carries
`anchors`, and an anchor is `path:start-end` plus the sha256 of exactly those
lines. The prose is not checkable; the claim that the prose is *about that code*
is, because the code is content-addressed. So this file never asks whether a
member says something true. It asks whether the region it says it about is still
there.

WHAT IT DOES NOT CHECK, stated rather than implied: coverage. A source file that
no member mentions does not fail. The manifest is a curated map and not an
inventory -- `rig/pool.py` and `rig/report.py` are deliberately absent -- and a
rule demanding completeness would be the permanently-red guard `test_readme_layout`
declined for exactly this reason. It catches the direction that actually drifts:
a member outliving the region it names.

THE TWO STALE STATES ARE NOT THE SAME FAILURE, and keeping them apart is the
point rather than a nicety. MOVED means the anchored bytes are intact at new line
numbers; nothing said about them has stopped being true, and `refresh.py
--relocate` repairs it in bulk. CHANGED means the anchored bytes are gone, so
the account may have gone with them, and `refresh.py --attest <id>` is per-member
and prints the diff. If both were one failure with one remedy, the remedy would
be a rehash, every member would go green, and the manifest would be fresh by hash
and wrong by meaning -- which is the only outcome here worse than being stale,
because a stale manifest at least announces itself.

THE FAILURE MODE THIS FILE MUST NOT HAVE is passing vacuously. A manifest with
zero members, a classifier that returns "fresh" for everything, or an importlib
load that silently picked up a different module would all leave a checker that
finds nothing, asserts nothing, and reports green. So the loader and the
classifier are asserted against fixtures before the real manifest is judged, and
each detector is pinned on an input it is known to catch.
"""

import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
LB_DIR = ROOT / ".load-bearing"

# `.load-bearing` is not an importable package name -- it is dotted and hyphenated
# by contract, and the contract fixes the directory name. Loaded by path so the
# gate, `verify.py` and `refresh.py` all run the same `lb`, which is what makes
# "stale" mean one thing in this repo.
_spec = importlib.util.spec_from_file_location("lb", LB_DIR / "lb.py")
lb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lb)


def _write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text.encode() if isinstance(text, str) else text)
    return p


def _anchor(root, rel, start, end):
    """An anchor pinned to the current contents of `rel`."""
    p = root / rel
    return {"path": rel, "start": start, "end": end, "blob": lb.blob_sha(p),
            "range_hash": lb.hash_slice(lb.lines_of(p), start, end)}


# --------------------------------------------------------------- vacuous-pass

def test_the_loader_actually_loaded_the_module_it_names():
    """Guards the importlib load: a wrong or stub module would pass everything."""
    assert lb.__file__ == str(LB_DIR / "lb.py")
    assert {lb.FRESH, lb.MOVED, lb.CHANGED, lb.MISSING} == {
        "fresh", "moved", "changed", "missing"}
    assert hasattr(lb, "classify_anchor") and hasattr(lb, "validate")


def test_the_manifest_has_members_and_anchors_to_check():
    """Guards against an empty or anchorless manifest satisfying the gate below."""
    manifest = lb.load()
    assert manifest["members"], "manifest.json declares no members; the gate is vacuous"
    for m in manifest["members"]:
        assert m["anchors"], f"member {m['id']} has no anchors; nothing pins its prose"
        for a in m["anchors"]:
            assert a["range_hash"], (
                f"member {m['id']} has an anchor with an empty range_hash -- an "
                f"unfilled anchor can never be stale, so it is never checked")


def test_the_classifier_distinguishes_fresh_from_stale_at_all(tmp_path):
    """A classifier that answered `fresh` unconditionally would pass the gate."""
    _write(tmp_path, "a.py", "one\ntwo\nthree\n")
    a = _anchor(tmp_path, "a.py", 1, 2)
    assert lb.classify_anchor(a, tmp_path)["status"] == lb.FRESH
    _write(tmp_path, "a.py", "ONE\ntwo\nthree\n")
    assert lb.classify_anchor(a, tmp_path)["status"] != lb.FRESH


# ---------------------------------------------------------------- the gate

def test_the_manifest_is_valid():
    """Schema and invariants, before freshness -- an invalid manifest has no members to judge."""
    errors = lb.validate(lb.load())
    assert not errors, (
        ".load-bearing/manifest.json is invalid:\n  " + "\n  ".join(errors))


def _member_ids():
    try:
        return [m["id"] for m in lb.load()["members"]]
    except Exception:
        return ["<manifest unreadable>"]


@pytest.mark.parametrize("member_id", _member_ids())
def test_member_is_fresh(member_id):
    """THE GATE. Nothing is done while a member it touched is stale.

    Parametrized per member so a failure names the one that drifted rather than
    a count, and so repairing one does not hide the rest.
    """
    manifest = lb.load()
    member = next(m for m in manifest["members"] if m["id"] == member_id)
    row = lb.classify_member(member)
    if row["status"] == lb.FRESH:
        return

    detail = "\n    ".join(
        f"{a['path']}:{a['start']}-{a['end']} — {a.get('detail', '')}"
        for a in row["anchors"] if a["status"] != lb.FRESH)
    remedy = {
        lb.MOVED: "python .load-bearing/refresh.py --relocate",
        lb.CHANGED: (f"read the member, update .load-bearing/{member.get('body_ref', '')} "
                     f"if its account has moved, then\n    "
                     f"python .load-bearing/refresh.py --attest {member_id}"),
        lb.MISSING: "repoint the anchor, or drop the member if the region is gone",
    }[row["status"]]
    pytest.fail(
        f"load-bearing member {member_id!r} is {row['status'].upper()}:\n    "
        f"{detail}\n  Fix:\n    {remedy}")


# -------------------------------------------------- pinning the detectors
#
# Each of these is an input the checker is known to catch. Without them a parse
# or a comparison that silently stopped working would satisfy every assertion
# above by finding nothing to disagree with.

def test_a_pure_line_shift_reads_as_moved(tmp_path):
    """The drift this file expects most often: an import added above the region."""
    _write(tmp_path, "m.py", "import os\n\ndef f():\n    return 1\n")
    a = _anchor(tmp_path, "m.py", 3, 4)
    _write(tmp_path, "m.py", "import os\nimport sys\n\ndef f():\n    return 1\n")
    got = lb.classify_anchor(a, tmp_path)
    assert got["status"] == lb.MOVED
    assert (got["new_start"], got["new_end"]) == (4, 5)


def test_a_content_change_reads_as_changed(tmp_path):
    """The drift that must not be repairable by --relocate."""
    _write(tmp_path, "m.py", "def f():\n    return 1\n")
    a = _anchor(tmp_path, "m.py", 1, 2)
    _write(tmp_path, "m.py", "def f():\n    return 2\n")
    assert lb.classify_anchor(a, tmp_path)["status"] == lb.CHANGED


def test_relocation_only_accepts_an_equal_length_window(tmp_path):
    """A region that grew or shrank changed; only an exact move is mechanical.

    Pins the choice directly, because a relocator that matched a prefix or a
    fuzzy window would turn CHANGED into MOVED and route real content drift to
    the remedy that needs no judgement.
    """
    _write(tmp_path, "m.py", "a\nb\nc\n")
    a = _anchor(tmp_path, "m.py", 1, 2)
    _write(tmp_path, "m.py", "x\na\nb\nEXTRA\nc\n")     # the two lines survive, contiguous
    assert lb.classify_anchor(a, tmp_path)["status"] == lb.MOVED
    _write(tmp_path, "m.py", "x\na\nEXTRA\nb\nc\n")      # split apart -- not a move
    assert lb.classify_anchor(a, tmp_path)["status"] == lb.CHANGED


def test_a_deleted_file_reads_as_missing(tmp_path):
    _write(tmp_path, "m.py", "a\nb\n")
    a = _anchor(tmp_path, "m.py", 1, 2)
    (tmp_path / "m.py").unlink()
    assert lb.classify_anchor(a, tmp_path)["status"] == lb.MISSING


def test_a_range_past_the_end_is_changed_and_not_clamped(tmp_path):
    """A shrunken file must not be compared on the prefix that survived."""
    _write(tmp_path, "m.py", "a\nb\nc\nd\n")
    a = _anchor(tmp_path, "m.py", 1, 4)
    _write(tmp_path, "m.py", "a\nb\n")
    got = lb.classify_anchor(a, tmp_path)
    assert got["status"] == lb.CHANGED
    assert "past the end" in got["detail"]


# --------------------------------------------------- pinning the normalization
#
# lb.py pins these; the contract's 0.1 leaves them open. They are asserted here
# so a later change to the normalization is a visible decision rather than a
# silent re-interpretation of every range_hash already written.

def test_line_endings_do_not_change_a_hash(tmp_path):
    """CRLF and CR are checkout artifacts, not edits."""
    lf = _write(tmp_path, "lf.txt", "alpha\nbeta\n")
    crlf = _write(tmp_path, "crlf.txt", "alpha\r\nbeta\r\n")
    cr = _write(tmp_path, "cr.txt", "alpha\rbeta\r")
    h = lb.hash_slice(lb.lines_of(lf), 1, 2)
    assert lb.hash_slice(lb.lines_of(crlf), 1, 2) == h
    assert lb.hash_slice(lb.lines_of(cr), 1, 2) == h


def test_a_leading_bom_does_not_change_a_hash(tmp_path):
    plain = _write(tmp_path, "p.txt", "alpha\nbeta\n")
    bom = _write(tmp_path, "b.txt", "﻿alpha\nbeta\n")
    assert lb.hash_slice(lb.lines_of(bom), 1, 2) == lb.hash_slice(lb.lines_of(plain), 1, 2)


def test_trailing_whitespace_does_change_a_hash(tmp_path):
    """Kept deliberately: it is a real edit to a real byte.

    This repo's own instrument is validated by `shasum` agreeing exactly, and a
    hash that forgives whitespace answers a slightly different question than the
    one it is asked.
    """
    clean = _write(tmp_path, "c.txt", "alpha\nbeta\n")
    trailing = _write(tmp_path, "t.txt", "alpha   \nbeta\n")
    assert lb.hash_slice(lb.lines_of(trailing), 1, 2) != lb.hash_slice(lb.lines_of(clean), 1, 2)


def test_a_terminating_newline_does_not_add_an_addressable_line(tmp_path):
    """A two-line file has two lines, and line 3 is out of bounds.

    `split("\\n")` on text ending in a newline leaves a trailing empty element,
    which would make an anchor of 1-3 on a two-line file legal and hash a
    phantom. The tail is dropped once rather than stripped, so a genuinely blank
    final line stays addressable -- checked below.
    """
    _write(tmp_path, "t.py", "a\nb\n")
    assert len(lb.lines_of(tmp_path / "t.py")) == 2
    assert lb.hash_slice(lb.lines_of(tmp_path / "t.py"), 1, 3) is None
    _write(tmp_path, "blank.py", "a\nb\n\n")            # a real empty line at the end
    assert len(lb.lines_of(tmp_path / "blank.py")) == 3
    assert lb.hash_slice(lb.lines_of(tmp_path / "blank.py"), 1, 3) is not None


def test_a_missing_final_newline_does_not_change_a_hash(tmp_path):
    """Absence of a trailing newline is a property of the file, not of the region."""
    with_nl = _write(tmp_path, "n.txt", "alpha\nbeta\n")
    without = _write(tmp_path, "w.txt", "alpha\nbeta")
    assert lb.hash_slice(lb.lines_of(without), 1, 2) == lb.hash_slice(lb.lines_of(with_nl), 1, 2)


# ------------------------------------------------------- pinning the invariants

def _fixture_manifest(tmp_path, **over):
    _write(tmp_path, "src.py", "def f():\n    return 1\n")
    base = {
        "contract": "load-bearing/0.1",
        "source_tree": "0" * 40,
        "criteria": [{"id": "correctness"}, {"id": "churn"},
                     {"id": "identity", "composed_of": ["correctness", "churn"],
                      "weights": {"correctness": 0.5, "churn": 0.5}}],
        "default_criterion": "identity",
        "members": [{
            "id": "m/one", "body": "an account",
            "anchors": [_anchor(tmp_path, "src.py", 1, 2)],
            "scores": {"correctness": 0.5, "churn": 0.5, "identity": 0.5},
            "aspects": [{"id": "a", "criteria": ["correctness"], "claim": "it returns 1"}],
        }],
    }
    base.update(over)
    return base


def test_the_fixture_manifest_is_valid_before_anything_is_broken(tmp_path):
    """Otherwise every test below passes by rejecting the fixture, not the fault."""
    assert lb.validate(_fixture_manifest(tmp_path), tmp_path) == []


@pytest.mark.parametrize("state_key", ["reviewed", "understood", "verified", "known"])
def test_reader_state_is_rejected_at_ingestion(tmp_path, state_key):
    """Invariant 1: content, never state -- rejected, not ignored.

    Checked nested inside `metadata` as well as at the top level, because
    `metadata` is opaque to PREP and is exactly where a state field would end up
    if the producer were merely told not to put one at the top.
    """
    m = _fixture_manifest(tmp_path)
    m["members"][0]["metadata"] = {"origin": {state_key: True}}
    errs = lb.validate(m, tmp_path)
    assert any("invariant 1" in e for e in errs), errs


def test_a_composite_scored_without_its_components_is_rejected(tmp_path):
    """Invariant 3: the override path has to lead somewhere.

    A member scored on `identity` alone would rank under the default ordering
    and vanish from every component ordering, which is the case the invariant
    exists to make impossible.
    """
    m = _fixture_manifest(tmp_path)
    m["members"][0]["scores"] = {"identity": 0.5}
    errs = lb.validate(m, tmp_path)
    assert any("invariant 3" in e for e in errs), errs


def test_a_composite_component_must_itself_be_declared(tmp_path):
    m = _fixture_manifest(tmp_path)
    m["criteria"][2]["composed_of"] = ["correctness", "not-a-criterion"]
    errs = lb.validate(m, tmp_path)
    assert any("not a declared criterion" in e for e in errs), errs


def test_weights_without_composed_of_are_rejected(tmp_path):
    """Weights are informational and belong to a composite; elsewhere they imply
    a computation PREP is forbidden to do (invariant 2)."""
    m = _fixture_manifest(tmp_path)
    m["criteria"][0]["weights"] = {"correctness": 1.0}
    assert any("weights without composed_of" in e for e in lb.validate(m, tmp_path))


def test_partial_scoring_across_the_manifest_is_rejected(tmp_path):
    """"Required for every criterion if present for any", read strictly.

    A member with no scores beside members that have them would sort at zero
    under every criterion -- ranked last by silence rather than by judgement.
    """
    m = _fixture_manifest(tmp_path)
    second = json.loads(json.dumps(m["members"][0]))
    second["id"], second["scores"] = "m/two", None
    del second["scores"]
    m["members"].append(second)
    assert any("required here too" in e for e in lb.validate(m, tmp_path))


def test_default_criterion_must_be_declared(tmp_path):
    m = _fixture_manifest(tmp_path, default_criterion="nope")
    assert any("default_criterion" in e for e in lb.validate(m, tmp_path))


@pytest.mark.parametrize("mutate,expect", [
    (lambda m: m["members"][0].update(body_ref="members/x.md"), "exactly one of body"),
    (lambda m: m["members"][0].pop("body"), "exactly one of body"),
    (lambda m: m["members"][0].update(anchors=[]), "anchors required"),
    (lambda m: m["members"][0]["aspects"][0].update(criteria=["nope"]), "not declared"),
    (lambda m: m["members"][0]["aspects"][0].update(claim="  "), "claim is required"),
    (lambda m: m["members"][0]["aspects"][0].update(claim=None), "claim is required"),
    (lambda m: m.update(contract="load-bearing/9.0"), "unknown major version"),
])
def test_schema_faults_are_reported(tmp_path, mutate, expect):
    m = _fixture_manifest(tmp_path)
    mutate(m)
    assert any(expect in e for e in lb.validate(m, tmp_path)), lb.validate(m, tmp_path)


def test_validation_reports_every_fault_and_not_only_the_first(tmp_path):
    """A gate that reports one error per run trains one fix per run."""
    m = _fixture_manifest(tmp_path, default_criterion="nope")
    m["members"][0]["scores"] = {"identity": 0.5}
    assert len(lb.validate(m, tmp_path)) >= 2


# ------------------------------------------- pinning the refusal, end to end
#
# The rest of this file checks that staleness is DETECTED. This checks that it
# cannot be cleared without reading anything -- which is the discipline the
# feature exists for, and the only part of it that lives in refresh.py rather
# than in lb.py.

def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.fixture
def seeded_repo(tmp_path):
    """A committed repo with one member, its body, and the two CLIs."""
    repo = tmp_path / "r"
    (repo / ".load-bearing" / "members").mkdir(parents=True)
    for name in ("lb.py", "refresh.py", "verify.py"):
        shutil.copy(LB_DIR / name, repo / ".load-bearing" / name)
    _write(repo, "src.py", "def f():\n    return 1\n")
    _write(repo, ".load-bearing/members/one.md", "f returns 1.\n")
    manifest = {
        "contract": "load-bearing/0.1", "source_tree": "0" * 40,
        "criteria": [{"id": "correctness"}], "default_criterion": "correctness",
        "members": [{"id": "m/one", "body_ref": "members/one.md",
                     "anchors": [_anchor(repo, "src.py", 1, 2)],
                     "scores": {"correctness": 0.9}}],
    }
    _write(repo, ".load-bearing/manifest.json", json.dumps(manifest, indent=2))
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "seed")
    _write(repo, "src.py", "def f():\n    return 2\n")      # the anchored code changes
    return repo


def _attest(repo, *extra):
    return subprocess.run(
        [sys.executable, ".load-bearing/refresh.py", "--attest", "m/one", *extra],
        cwd=repo, capture_output=True, text=True)


def test_attest_refuses_a_rehash_when_the_body_was_not_touched(seeded_repo):
    """THE CENTRAL REFUSAL. Without it the remedy for CHANGED is a rehash.

    A one-command re-bless of every drifted member is how this document would
    become fresh by hash and wrong by meaning, which is the failure the whole
    MOVED/CHANGED split exists to prevent.
    """
    got = _attest(seeded_repo)
    assert got.returncode == 1, got.stdout
    assert "REFUSED" in got.stdout
    assert "return 2" in got.stdout, "the diff must be shown, not just the refusal"
    after = json.loads((seeded_repo / ".load-bearing/manifest.json").read_text())
    assert after["members"][0]["anchors"][0]["range_hash"] == \
        json.loads(subprocess.run(["git", "show", "HEAD:.load-bearing/manifest.json"],
                                  cwd=seeded_repo, capture_output=True, text=True,
                                  check=True).stdout)["members"][0]["anchors"][0]["range_hash"], \
        "a refused attestation must not have written anything"


def test_attest_proceeds_once_the_body_has_been_edited(seeded_repo):
    _write(seeded_repo, ".load-bearing/members/one.md", "f returns 2.\n")
    got = _attest(seeded_repo)
    assert got.returncode == 0, got.stdout
    assert "attested m/one" in got.stdout


def test_attest_takes_an_explicit_reason_instead_of_a_body_edit(seeded_repo):
    """The escape hatch has to exist: renaming a local changes bytes and no words."""
    got = _attest(seeded_repo, "--unchanged", "renamed a local; the account holds")
    assert got.returncode == 0, got.stdout
    assert "renamed a local" in got.stdout
    assert "commit message" in got.stdout, (
        "the reason is not stored in the manifest, so the tool has to say where it goes")


def test_attest_on_a_merely_moved_member_redirects_to_relocate(seeded_repo):
    """A pure line shift must not be routed through the path that needs judgement.

    Without this, `--attest` on a MOVED member reaches the body-edit refusal and
    asks for prose changes to describe code that did not change -- which teaches
    the reflex the refusal exists to prevent.
    """
    _write(seeded_repo, "src.py", "# added above\ndef f():\n    return 1\n")
    got = _attest(seeded_repo)
    assert got.returncode == 1
    assert "--relocate" in got.stdout and "REFUSED" not in got.stdout, got.stdout


def test_relocate_does_not_clear_a_content_change(seeded_repo):
    """--relocate is the no-judgement path and must never reach a CHANGED member."""
    got = subprocess.run([sys.executable, ".load-bearing/refresh.py", "--relocate"],
                         cwd=seeded_repo, capture_output=True, text=True)
    assert got.returncode == 0
    verify = subprocess.run([sys.executable, ".load-bearing/verify.py"],
                            cwd=seeded_repo, capture_output=True, text=True)
    assert verify.returncode == 1, "relocate cleared a content change"
    assert "CHANGED" in verify.stdout
