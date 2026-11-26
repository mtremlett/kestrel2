"""THE ONE PROGRESS NUMBER (CLAUDE.md, CANON Part C): plan boxes ticked on main in a window.

A box counts when it is `- [x]` in `docs/PLAN.md` at the window's end and was not ticked at
its start: a box ticked then un-ticked does not count, a box removed is not a tick, and a
box born ticked is one. A box is known by its note's id, else by its words. Every box
counts, umbrellas and boxes outside the lane books too (those under OTHER).

The pure core takes two plan texts; the edge reads them from git, main at the window's
start (its last first-parent commit before then) and at its end. The runner's Telegram,
STATUS and SCOREBOARD all read this one function:

    python -m lab.progress [--hours 24] [--ref origin/main] [--repo .] [--at ISO]

prints {"ticked": n, "lanes": {"DATA": n, ..., "OTHER": n}, "hours": h, "since": iso,
"at": iso, "start": sha or null, "end": sha} on one line. It never fetches.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

PLAN = "docs/PLAN.md"
OTHER = "OTHER"  #: the boxes outside every lane's book
HEADING = re.compile(r"^#{2,} ?(.*)$")
BOOK = re.compile(r"The (\w+) lane's book")
BOX = re.compile(r"^[ \t]*- \[([ x])\] (.*)$")
NOTE_ID = re.compile(r"\{id:\s*([^;}\s]+)")


@dataclass(frozen=True)
class Box:
    """One box of the plan: who knows it, whose book it sits in, and whether it is ticked."""

    key: str
    lane: str
    ticked: bool


@dataclass(frozen=True)
class Ticks:
    """Boxes ticked between two plans: the total and each lane's share, every lane named."""

    total: int
    lanes: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class Window:
    """The number over a window of main: its commits at the start (None: none yet) and end."""

    ticked: Ticks
    since: datetime
    at: datetime
    start: str | None
    end: str


def boxes(plan: str) -> list[Box]:
    """Every box of the plan, a wrapped box read whole, with the lane whose book holds it."""
    found: list[tuple[str, bool, list[str]]] = []
    lane = OTHER
    for line in plan.splitlines():
        if heading := HEADING.match(line):
            book = BOOK.match(heading[1])
            lane = book[1].upper() if book else OTHER
        elif box := BOX.match(line):
            found.append((lane, box[1] == "x", [box[2]]))
        elif found and line[:1] in (" ", "\t") and line.strip():
            found[-1][2].append(line)
    return [Box(_key(" ".join(" ".join(w).split())), lane, ticked) for lane, ticked, w in found]


def _key(text: str) -> str:
    note = NOTE_ID.search(text)
    return f"id:{note[1]}" if note else text


def ticked(before: str, after: str) -> Ticks:
    """The boxes ticked in `after` that `before` did not have ticked, counted per lane."""
    already = Counter(b.key for b in boxes(before) if b.ticked)
    lanes: Counter[str] = Counter({b.lane: 0 for b in boxes(after)})
    for box in (b for b in boxes(after) if b.ticked):
        if already[box.key]:
            already[box.key] -= 1
        else:
            lanes[box.lane] += 1
    return Ticks(sum(lanes.values()), tuple(sorted(lanes.items())))


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(  # noqa: S603 - fixed git arguments, no shell
        ["git", *args],  # noqa: S607
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout


def window(repo: Path, ref: str, at: datetime, hours: float = 24) -> Window:
    """Plan boxes ticked on `ref` in the `hours` before `at`, read from git."""
    since = at - timedelta(hours=hours)
    last = ("rev-list", "-1", "--first-parent")
    end = _git(repo, *last, f"--before={at.isoformat()}", ref).strip()
    start = _git(repo, *last, f"--before={since.isoformat()}", ref).strip()
    if not end:
        raise ValueError(f"{ref} has no commit at or before {at.isoformat()} in {repo}")
    before = _git(repo, "show", f"{start}:{PLAN}") if start else ""
    after = _git(repo, "show", f"{end}:{PLAN}")
    return Window(ticked(before, after), since, at, start or None, end)


def main(argv: list[str] | None = None) -> None:
    """Print the window's number as one line of JSON for the runner, STATUS and SCOREBOARD."""
    ask = argparse.ArgumentParser(prog="python -m lab.progress", description=__doc__)
    ask.add_argument("--hours", type=float, default=24)
    ask.add_argument("--ref", default="origin/main")
    ask.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    ask.add_argument("--at", type=datetime.fromisoformat, default=None)
    got = ask.parse_args(argv)
    if got.at is not None and got.at.tzinfo is None:
        ask.error("--at needs its timezone, e.g. 2026-11-26T09:00:00+00:00")
    at = got.at or datetime.now(UTC)
    seen = window(got.repo, got.ref, at, got.hours)
    hours = int(got.hours) if got.hours == int(got.hours) else got.hours
    shown = {"ticked": seen.ticked.total, "lanes": dict(seen.ticked.lanes), "hours": hours}
    edges = {"since": seen.since.isoformat(), "at": at.isoformat()}
    sys.stdout.write(json.dumps({**shown, **edges, "start": seen.start, "end": seen.end}) + "\n")


if __name__ == "__main__":
    main()
