"""THE LANES' GUARDS. Three lanes of unattended sessions build the desk side by side
(docs/PLAN.md). A rule in a session's prompt is a rule a confused session can break, so
these refuse it in the check, on GitHub, before anything merges:

- a lane's branch (named `lane/<lane>-...` by the runner: money, paper, data, grid,
  rungs) may change only its own lane's files, the shared documents, and add its own
  modules to the manifest; a branch naming a lane the manifest does not know fails;
- no branch grows `desk/` and `lab/` together by more than 300 lines in one change;
- up to twelve sessions run at once, so each lane session holds a claim: the files it
  may change, given it by the runner and written in its pull request as `Claim: ...`.
  The check reads the claim from the pull request on GitHub, or from KESTREL_CLAIM on
  the PC, and refuses a change outside it. A lane's pull request without one fails;
- every `{id: ...; files: ...; after: ...; waits: ...}` note on a book's box parses, its
  id is unique, each `after` names a box that exists, and each `waits` is a request
  number, a date or `operator`, so the runner can hand boxes out and hold back the rest.

Ruled 13 November 2026 (docs/DECISIONS.md).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tomllib
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LANE_BRANCH = re.compile(r"lane/([a-z]+)-")  #: every lane branch; an unknown lane fails
HEADING = re.compile(r"# the ([a-z]+) lane")
MODULE = re.compile(r'"([^"]+)" = ".*"')
#: Every lane writes in its own part of these (docs/PLAN.md says which part).
SHARED = ("docs/STATUS.md", "docs/PLAN.md", "docs/SCOREBOARD.md", "docs/DECISIONS.md")
MAX_NET_PRODUCT_LINES = 300
CLAIM_LINE = re.compile(r"^Claim:[ \t]*(.+?)[ \t]*\r?$", re.MULTILINE)
WHOLE_LANE = "*"  #: a claim of every file the lane owns: its serial work
NOTE = re.compile(r"\{((?:id|files|after|waits):[^{}]*)\}")
ID = re.compile(r"[a-z]+-[a-z0-9-]+")
#: what a box may wait on outside its lane: a request, a date, or the operator
WAIT = re.compile(r"R-[A-Z]+-\d+|\d{4}-\d\d-\d\d|operator")
BOX = re.compile(r"^- \[[ x]\] (.*(?:\n[ \t]+\S.*)*)", re.MULTILINE)  #: a box, wrapped lines too


def _git(*args: str) -> str:
    return subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def _branch() -> str:
    """The branch under test: GitHub names it for a pull request, then for a push."""
    for name in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME"):
        if os.environ.get(name, "").strip():
            return os.environ[name].strip()
    return _git("rev-parse", "--abbrev-ref", "HEAD").strip()


def _changes() -> dict[str, tuple[int, int]]:
    """Each file this branch changes against main, with its lines added and removed. No
    main to compare with is a failure, never a pass."""
    base = _git("merge-base", "HEAD", "origin/main").strip()
    changed: dict[str, tuple[int, int]] = {}
    for row in _git("diff", "--numstat", "--no-renames", base).splitlines():
        added, removed, path = row.split("\t")
        changed[path] = (
            int(added or 0) if added != "-" else 0,
            int(removed) if removed != "-" else 0,
        )
    return changed


def _owned(lane: str) -> list[str]:
    """A lane's files: its modules (under its heading in manifest.toml), their unit tests,
    and what manifest.toml's [lanes] table adds."""
    patterns: list[str] = []
    current = None
    for line in (ROOT / "manifest.toml").read_text(encoding="utf-8").splitlines():
        if heading := HEADING.fullmatch(line.strip()):
            current = heading[1]
        elif line.startswith("["):
            current = None
        elif (module := MODULE.fullmatch(line.strip())) and current == lane:
            stem = Path(module[1]).stem
            prefix = "test_lab_" if module[1].startswith("lab/") else "test_"
            patterns += [
                module[1],
                f"tests/unit/{prefix}{stem}.py",
                f"tests/unit/{prefix}{stem}_*.py",
            ]
    lanes = tomllib.loads((ROOT / "manifest.toml").read_text(encoding="utf-8"))["lanes"]
    assert lane in lanes, f"no lane called {lane!r} in manifest.toml's [lanes]: {sorted(lanes)}"
    return patterns + list(lanes[lane])


def _manifest_added_only(owned: list[str]) -> list[str]:
    """A lane may only add lines registering its own modules; any other edit is refused."""
    base = _git("merge-base", "HEAD", "origin/main").strip()
    wrong = []
    for line in _git("diff", "-U0", base, "--", "manifest.toml").splitlines():
        if not line.startswith(("+", "-")) or line.startswith(("+++", "---")) or line in "+-":
            continue  # only the lines added or removed, not git's headers
        module = MODULE.fullmatch(line[1:].strip())
        if line.startswith("-") or not module or not any(fnmatch(module[1], p) for p in owned):
            wrong.append(line)
    return wrong


def test_a_lane_changes_only_its_own_files() -> None:
    """SPRAWL, across lanes. With every permission granted, a confused run could edit
    another lane's code, a guard, or the runner's prompt. The check refuses it."""
    lane = LANE_BRANCH.match(_branch())
    if lane is None:
        return  # not a lane's branch: a session the operator started, under his eye
    owned = _owned(lane[1])
    foreign = sorted(
        path
        for path in _changes()
        if path not in SHARED
        and path != "manifest.toml"
        and not any(fnmatch(path, p) for p in owned)
    )
    assert not foreign, (
        f"the {lane[1]} lane may not change {foreign}: another lane's, or no lane's "
        "(docs/PLAN.md). Write the need in your lane's section of docs/STATUS.md instead."
    )
    if "manifest.toml" in _changes():
        wrong = _manifest_added_only(owned)
        assert not wrong, f"the {lane[1]} lane may only register its own modules: {wrong}"


def test_no_change_grows_the_product_by_more_than_300_lines() -> None:
    """BLOAT, per change. The phase ceiling caps the total; this caps the step, so a big
    change is split into pieces each with its own test and review."""
    net = sum(
        added - removed
        for path, (added, removed) in _changes().items()
        if path.startswith(("desk/", "lab/"))
    )
    assert net <= MAX_NET_PRODUCT_LINES, (
        f"this change adds {net} net lines to desk/ and lab/; at most "
        f"{MAX_NET_PRODUCT_LINES} at once. Split it."
    )


def _claim() -> list[str] | None:
    """The session's claim: from its pull request on GitHub (a pull_request event), from
    KESTREL_CLAIM on the PC; None where there is none to read (a push, a session the
    operator runs). A pull request with no claim, or two, fails."""
    if os.environ.get("GITHUB_EVENT_NAME") == "pull_request":
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
        lines = CLAIM_LINE.findall(event["pull_request"].get("body") or "")
        assert (
            len(lines) == 1
        ), f"a lane's pull request carries exactly one 'Claim: ...' line; it has {len(lines)}"
        text = lines[0]
    elif os.environ.get("KESTREL_CLAIM", "").strip():
        text = os.environ["KESTREL_CLAIM"]
    else:
        return None
    return [part.strip() for part in text.split(",") if part.strip()]


def test_a_lane_changes_only_what_it_claimed() -> None:
    """SPRAWL, inside a lane. Up to twelve sessions run at once; two that edit the same
    file collide. The runner gives each session a claim that overlaps no running one,
    and this refuses any change outside it ('*' is the lane's own files, one at a time)."""
    lane = LANE_BRANCH.match(_branch())
    if lane is None:
        return
    claim = _claim()
    if claim is None:
        return
    owned = _owned(lane[1])
    patterns = [p for part in claim for p in (owned if part == WHOLE_LANE else [part])]
    outside = sorted(
        path
        for path in _changes()
        if path != "manifest.toml" and not any(fnmatch(path, p) for p in patterns)
    )
    assert not outside, (
        f"the {lane[1]} lane's session claimed {claim} and may not change {outside}. "
        "Put the narrative, ticks and requests in the pull request's description: the "
        "lane's scribe folds them into the shared documents."
    )


def _notes(plan: str) -> list[dict[str, list[str]]]:
    """Every runner note on a box of a book: {id: x; files: a, b; after: y}. Only a box's
    own text (its wrapped lines included) is read, as the runner reads it; prose may show
    a note as an example."""
    notes = []
    for note in (n for box in BOX.findall(plan) for n in NOTE.findall(" ".join(box.split()))):
        fields: dict[str, list[str]] = {}
        for part in note.split(";"):
            key, sep, value = part.partition(":")
            assert sep and key.strip() in ("id", "files", "after", "waits"), f"bad note {{{note}}}"
            fields[key.strip()] = [v.strip() for v in value.split(",") if v.strip()]
        assert len(fields.get("id", [])) == 1 and ID.fullmatch(
            fields["id"][0]
        ), f"a note needs one id like money-kill: {{{note}}}"
        assert fields.get("files"), f"a note names the files its box changes: {{{note}}}"
        bad = [w for w in fields.get("waits", []) if not WAIT.fullmatch(w)]
        assert not bad, f"a box waits on a request, a date or operator, not {bad}: {{{note}}}"
        notes.append(fields)
    return notes


def test_the_books_notes_can_be_handed_out() -> None:
    """A box the runner cannot read, or one waiting for a box that does not exist, would
    sit unworked with nobody told. Each note parses, each id is unique, and each `after`
    names an id in the plan."""
    notes = _notes((ROOT / "docs" / "PLAN.md").read_text(encoding="utf-8"))
    ids = [n["id"][0] for n in notes]
    twice = sorted({i for i in ids if ids.count(i) > 1})
    assert not twice, f"two boxes share the ids {twice}"
    missing = sorted({a for n in notes for a in n.get("after", []) if a not in ids})
    assert not missing, f"boxes wait for ids no box has: {missing}"
    after = {n["id"][0]: n.get("after", []) for n in notes}
    for start in after:
        seen, todo = set(), list(after[start])
        while todo:
            box = todo.pop()
            assert box != start, f"{start} waits, through its afters, for itself"
            if box not in seen:
                seen.add(box)
                todo += after.get(box, [])
