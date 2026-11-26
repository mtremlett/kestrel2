"""lab.progress: the one progress number, plan boxes ticked on main in a window (CLAUDE.md)."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from lab import progress

BEFORE = """# The plan
## Phase 0
- [x] Done long ago
- [ ] Shared box, ticked in the window
### The data lane's book
- [ ] A data box, ticked {id: data-one; files: desk/store.py}
- [ ] A wrapped box whose note sits on its
  second line {id: data-two}
- [x] Ticked before, un-ticked in the window {id: data-back}
- [x] Ticked before, removed in the window {id: data-gone}
- [ ] Never ticked {id: data-open}
### The money lane's book
- [x] Ticked before and still ticked {id: money-kept}
- [ ] An umbrella
  - [ ] Its child, ticked {id: money-child}
## Phase 2
- [ ] Outside every book
"""

AFTER = """# The plan
## Phase 0
- [x] Done long ago
- [x] Shared box, ticked in the window
### The data lane's book
- [x] A data box, ticked {id: data-one; files: desk/store.py}
- [x] A wrapped box whose note sits on its
  second line, its words edited as it was ticked {id: data-two}
- [ ] Ticked before, un-ticked in the window {id: data-back}
- [ ] Never ticked {id: data-open}
- [x] A new box born ticked {id: data-born}
### The money lane's book
- [x] Ticked before and still ticked {id: money-kept}
- [ ] An umbrella
  - [x] Its child, ticked {id: money-child}
## Phase 2
- [ ] Outside every book
"""


def test_a_box_counts_once_when_it_is_ticked_inside_the_window() -> None:
    ticks = progress.ticked(BEFORE, AFTER)
    assert ticks.total == 5
    assert dict(ticks.lanes) == {"DATA": 3, "MONEY": 1, "OTHER": 1}


def test_nothing_changed_is_no_progress_and_an_empty_start_counts_every_tick() -> None:
    assert progress.ticked(AFTER, AFTER).total == 0
    assert progress.ticked("", AFTER).total == 7


def test_two_boxes_of_the_same_words_are_two_boxes() -> None:
    twice = "### The grid lane's book\n- [x] Same words\n- [x] Same words\n"
    once = twice.replace("- [x] Same words\n", "- [ ] Same words\n", 1)
    assert progress.ticked(once, twice).total == 1


def _git(home: Path, *args: str, when: str = "") -> str:
    env = {"GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when} if when else {}
    done = subprocess.run(  # noqa: S603
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],  # noqa: S607
        cwd=home,
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, **env},
    )
    return done.stdout.strip()


def test_the_window_reads_main_at_its_start_and_its_end(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _git(tmp_path, "init", "-q", "-b", "main")
    (tmp_path / "docs").mkdir()
    plan = tmp_path / "docs" / "PLAN.md"
    for text, when in ((BEFORE, "2026-11-25T08:00:00+00:00"), (AFTER, "2026-11-26T08:00:00+00:00")):
        plan.write_text(text, encoding="utf-8")
        _git(tmp_path, "add", "docs/PLAN.md")
        _git(tmp_path, "commit", "-q", "-m", "plan", when=when)
    at = datetime(2026, 11, 26, 9, tzinfo=UTC)
    seen = progress.window(tmp_path, "main", at, hours=24)
    assert (seen.ticked.total, seen.start != seen.end) == (5, True)
    assert progress.window(tmp_path, "main", at, hours=0.5).ticked.total == 0
    progress.main(["--repo", str(tmp_path), "--ref", "main", "--at", at.isoformat()])
    shown = json.loads(capsys.readouterr().out)
    assert (shown["ticked"], shown["lanes"]["DATA"], shown["hours"]) == (5, 3, 24)
