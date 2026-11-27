"""THE LANES' GUARDS. Three lanes of unattended sessions build the desk side by side
(docs/PLAN.md). A rule in a session's prompt is a rule a confused session can break, so
these refuse it in the check, on GitHub, before anything merges:

- a lane's branch (named `lane/<lane>-...` by the runner: money, paper, data, grid,
  rungs) may change only its own lane's files (its decisions in `docs/lanes/<lane>.md`
  among them), the shared documents, and add its own modules to its own manifest file,
  `manifest/<lane>.toml`, or remove the line of one it owned on main (folding it away,
  R-RUNGS-29); `manifest.toml` itself and another lane's file are refused; a branch
  naming a lane the manifest does not know fails;
- no branch grows `desk/` and `lab/` together by more than 300 lines in one change;
- up to twelve sessions run at once, so each lane session holds a claim: the files it
  may change, given it by the runner and written in its pull request as `Claim: ...`.
  The check reads the claim from the pull request on GitHub, or from KESTREL_CLAIM on
  the PC, and refuses a change outside it. A lane's pull request without one fails;
- every `{id: ...; files: ...; after: ...; waits: ...; check: ...}` note on a book's box
  parses, its id is unique, each `after` names a box that exists, and each `waits` is a
  request number, a date or `operator`, so the runner can hand boxes out and hold back the
  rest; every open box of a lane's book names its `check:`, the test that proves it.

Ruled 13 November 2026 (docs/DECISIONS.md).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from fnmatch import fnmatch
from pathlib import Path

from test_guards import manifest

ROOT = Path(__file__).resolve().parents[2]
LANE_BRANCH = re.compile(r"lane/([a-z]+)-")  #: every lane branch; an unknown lane fails
MODULE = re.compile(r'"([^"]+)" = ".*"')
#: Every lane writes in its own part of these (docs/PLAN.md says which part).
SHARED = ("docs/STATUS.md", "docs/PLAN.md", "docs/SCOREBOARD.md", "docs/DECISIONS.md")
MAX_NET_PRODUCT_LINES = 300
CLAIM_LINE = re.compile(r"^Claim:[ \t]*(.+?)[ \t]*\r?$", re.MULTILINE)
WHOLE_LANE = "*"  #: a claim of every file the lane owns: its serial work
NOTE = re.compile(r"\{((?:id|files|after|waits|check):[^{}]*)\}")
KEYS = ("id", "files", "after", "waits", "check")
ID = re.compile(r"[a-z]+-[a-z0-9-]+")
#: what a box may wait on outside its lane: a request, a date, or the operator
WAIT = re.compile(r"R-[A-Z]+-\d+|\d{4}-\d\d-\d\d|operator")
BOX = re.compile(r"^- \[[ x]\] (.*(?:\n[ \t]+\S.*)*)", re.MULTILINE)  #: a box, wrapped lines too
#: a lane book's item at any depth, its wrapped lines (never a nested box's) read with it
ITEM = re.compile(r"^([ \t]*)- \[([ x])\] (.*(?:\n[ \t]+(?!- \[)\S.*)*)", re.MULTILINE)
#: a check is a pytest node id: a test file under tests/ and its test function
CHECK = re.compile(r"tests/[a-z0-9_/]+\.py::test_[a-z0-9_]+")


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


def _owned(lane: str, at: str = "") -> list[str]:
    """A lane's files: its modules (those in manifest/<lane>.toml), their unit tests, its own
    decisions (docs/lanes/<lane>.md) and what manifest.toml's [lanes] table adds; read from
    the commit `at` when given (main's, so a module the lane folds away is still its own),
    else from the working tree. Its manifest file is its own only through the line check."""
    spec = manifest(at)
    lanes = spec["lanes"]
    assert lane in lanes, f"no lane called {lane!r} in manifest.toml's [lanes]: {sorted(lanes)}"
    patterns: list[str] = []
    for module in sorted(m for m, owner in spec["owner"].items() if owner == lane):
        stem = Path(module).stem
        prefix = "test_lab_" if module.startswith("lab/") else "test_"
        patterns += [module, f"tests/unit/{prefix}{stem}.py", f"tests/unit/{prefix}{stem}_*.py"]
    return [*patterns, f"docs/lanes/{lane}.md", *lanes[lane]]


def _module_lines_only(fragment: str, base: str) -> list[str]:
    """A lane may only add or remove module lines in its own manifest file (registering one,
    or folding one away, R-RUNGS-29, his yes 22 Nov); any other edit is refused. Its lines are
    its modules by where they sit, and a module another lane lists fails the loader."""
    wrong = []
    for line in _git("diff", "-U0", base, "--", fragment).splitlines():
        if not line.startswith(("+", "-")) or line.startswith(("+++", "---")) or line in "+-":
            continue  # only the lines added or removed, not git's headers
        if not MODULE.fullmatch(line[1:].strip()):
            wrong.append(line)
    return wrong


def test_a_lane_changes_only_its_own_files() -> None:
    """SPRAWL, across lanes. With every permission granted, a confused run could edit
    another lane's code, a guard, or the runner's prompt. The check refuses it."""
    lane = LANE_BRANCH.match(_branch())
    if lane is None:
        return  # not a lane's branch: a session the operator started, under his eye
    base = _git("merge-base", "HEAD", "origin/main").strip()
    owned, was, fragment = _owned(lane[1]), _owned(lane[1], base), f"manifest/{lane[1]}.toml"
    foreign = sorted(
        path
        for path in _changes()
        if path not in SHARED
        and path != fragment
        and not any(fnmatch(path, p) for p in (*owned, *was))
    )
    assert not foreign, (
        f"the {lane[1]} lane may not change {foreign}: another lane's, or no lane's "
        "(docs/PLAN.md). Write the need in your lane's section of docs/STATUS.md instead."
    )
    if fragment in _changes():
        wrong = _module_lines_only(fragment, base)
        assert not wrong, f"the {lane[1]} lane may only register or fold away modules: {wrong}"


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
        named = ROOT / ".claim"  # a '*' session names its files here; the runner is its last writer
        if WHOLE_LANE in [part.strip() for part in text.split(",")] and named.exists():
            text = ",".join(
                [p for p in text.split(",") if p.strip() != WHOLE_LANE]
                + named.read_text(encoding="utf-8").splitlines()
            )
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
        if path != f"manifest/{lane[1]}.toml" and not any(fnmatch(path, p) for p in patterns)
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
            assert sep and key.strip() in KEYS, f"bad note {{{note}}}"
            fields[key.strip()] = [v.strip() for v in value.split(",") if v.strip()]
        assert len(fields.get("id", [])) == 1 and ID.fullmatch(
            fields["id"][0]
        ), f"a note needs one id like money-kill: {{{note}}}"
        assert fields.get("files"), f"a note names the files its box changes: {{{note}}}"
        bad = [w for w in fields.get("waits", []) if not WAIT.fullmatch(w)]
        assert not bad, f"a box waits on a request, a date or operator, not {bad}: {{{note}}}"
        odd = [c for c in fields.get("check", []) if not CHECK.fullmatch(c)]
        assert not odd, f"a check is a test id, tests/<file>.py::test_<name>, not {odd}: {{{note}}}"
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


def test_every_open_request_has_its_own_box() -> None:
    """A request written inside another's line rides that line's box: the runner reads one
    request per `- [ ]` line, so a run-on is handed out as met or never (failure pattern 22).
    Each `R-X-n (later` or `(blocking` in STATUS opens its own line."""
    text = (ROOT / "docs" / "STATUS.md").read_text(encoding="utf-8")
    asks = re.compile(r"R-[A-Z]+-\d+ \((?:later|blocking)")
    loose = [
        m[0]
        for ln in text.splitlines()
        for m in asks.finditer(ln)
        if not re.match(r"- \[[ x]\] $", ln[: m.start()])
    ]
    assert not loose, f"requests inside another's line; give each its own `- [ ]` line: {loose}"


def _open_work(plan: str) -> dict[str, list[str]]:
    """Each lane's open boxes, as the runner reads its books (`slots.boxes`): every item under
    `### The <lane> lane's book` up to the next heading, at any depth, its wrapped lines
    joined; a box with boxes under it is an umbrella, not work."""
    work: dict[str, list[str]] = {}
    for book in re.finditer(r"^### The ([a-z]+) lane's book.*$", plan, re.MULTILINE):
        rest = plan[book.end() :]
        end = re.search(r"^##", rest, re.MULTILINE)
        items = list(ITEM.finditer(rest[: end.start()] if end else rest))
        work[book[1]] = [
            " ".join(item[3].split())
            for item, after in zip(items, [*items[1:], None], strict=True)
            if item[2] == " " and not (after and len(after[1]) > len(item[1]))
        ]
    return work


def test_every_open_box_names_its_check() -> None:
    """THE BOX IS THE CARD (the operator's 'Yes, all of it', 27 Nov). The runner runs an open
    box's `check:` on main before it spends a session: green is a tick, never a hand-out. A
    box with no check is work nobody can prove done, handed out again and again (failure
    patterns 12 and 22). The check is a test id the box's own files may hold, so the session
    can write it."""
    plan = (ROOT / "docs" / "PLAN.md").read_text(encoding="utf-8")
    unproven = []
    for lane, boxes in _open_work(plan).items():
        for text in boxes:
            note = NOTE.search(text)
            fields = (
                {k.strip(): v for k, _, v in (p.partition(":") for p in note[1].split(";"))}
                if note
                else {}
            )
            checks = [c.strip() for c in fields.get("check", "").split(",") if c.strip()]
            files = [f.strip() for f in fields.get("files", "").split(",") if f.strip()]
            outside = [c for c in checks if not any(fnmatch(c.split("::")[0], f) for f in files)]
            if not checks or outside:
                unproven.append(f"{lane}: {fields.get('id', text[:60]).strip()} {outside or ''}")
    assert not unproven, (
        "every open box of a lane's book names `check: tests/<file>.py::test_<name>` in its "
        "note, the test that proves it, in a file the box may change (a test it will write is "
        f"named before it exists): {unproven}"
    )
