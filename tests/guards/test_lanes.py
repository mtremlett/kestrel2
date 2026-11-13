"""THE LANES' GUARDS. Three lanes of unattended sessions build the desk side by side
(docs/PLAN.md). A rule in a session's prompt is a rule a confused session can break, so
these refuse it in the check, on GitHub, before anything merges:

- a lane's branch (named `lane/money-...`, `lane/data-...`, `lane/ladder-...` by the
  runner) may change only its own lane's files, the shared documents, and add its own
  modules to the manifest;
- no branch grows `desk/` and `lab/` together by more than 300 lines in one change.

Ruled 13 November 2026 (docs/DECISIONS.md).
"""

from __future__ import annotations

import os
import re
import subprocess
import tomllib
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LANE_BRANCH = re.compile(r"lane/(money|data|ladder)-")
HEADING = re.compile(r"# the (money|data|ladder) lane")
MODULE = re.compile(r'"([^"]+)" = ".*"')
#: Every lane writes in its own part of these (docs/PLAN.md says which part).
SHARED = ("docs/STATUS.md", "docs/PLAN.md", "docs/SCOREBOARD.md", "docs/DECISIONS.md")
MAX_NET_PRODUCT_LINES = 300


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
    return patterns + list(lanes[lane])


def _manifest_added_only(owned: list[str]) -> list[str]:
    """A lane may only add lines registering its own modules; any other edit is refused."""
    base = _git("merge-base", "HEAD", "origin/main").strip()
    wrong = []
    for line in _git("diff", "-U0", base, "--", "manifest.toml").splitlines():
        if line.startswith(("---", "+++", "@@")) or line in ("+", "-"):
            continue
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
