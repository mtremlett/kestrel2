"""sweep - THE GRID'S PASS: every strategy at every setting on every ticker of a list, each
cell kept by the versions of the code and the bars that made it, so a second pass runs only
what a change has touched.

A setting is a strategy the desk's engine can make (`strategy.STRATEGIES`): the grid is
trusted only where it matches that engine, so the pass runs whatever is registered there, the
published five today, and a setting added there is swept with no change here.

The unit handed to the auto-tune (`lab/tune.py`) is a ticker, not a cell: a worker reads one
ticker's bars once, runs every strategy on them and lets them go, so no worker ever holds the
universe. The bars are read as research reads them (`universe.read`): a ticker the store has
parked for trading is studied too, on its longest run at one scale of price.

Each ticker has a journal of its own, in its venue's folder since one symbol can be two
companies, written by the batch service: one worker at a time holds a ticker, so one process
at a time works on a journal. A cell that fails is recorded with its error and tried again
on the next pass. A ticker whose worker dies is named, and its cells are counted as undone.
One pass at a time works on a folder of journals: a pass holds the folder's lock, which the
system lets go if the pass dies, and a second pass on it is refused.

The week (`python -m lab.sweep STORE KEPT DATA --days 7`) is pass after pass, one starting
each hour, each over the research list from the archive's first day to that day, and each in
a process of its own, so a pass runs the code on disk that hour and a pass that dies costs
the week only itself. Every pass is one line of `week.jsonl` in the data folder, its count
or the error that ended it, and `unbroken` reads from that log how long the grid has run
without stopping: seven days of it is the proof. A pass that failed, or held no cell at its
end, or started more than a pause after the one before it ended, is where a run stops.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from functools import lru_cache, partial
from pathlib import Path
from typing import IO, Any

from desk import archive
from desk.lines import Line
from desk.store import Bar
from desk.strategy import STRATEGIES
from lab import batch, tune, universe
from lab.cell import Cell

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

PAUSE = timedelta(hours=1)  #: from one pass's start to the next's, in the week
WEEK, LOCK = "week.jsonl", "pass.lock"
COUNTS = ("cells", "ran", "kept", "failed", "undone")


@dataclass(frozen=True)
class Pass:
    report: tune.Report[Line]  #: the auto-tune's: its peaks, and each ticker whose worker died
    cells: int
    ran: int  #: run in this pass, and their records kept
    kept: int  #: held already under their code and their bars, so not run again
    failed: int  #: recorded with their error, and run again on the next pass
    undone: int  #: on a ticker whose worker died: no outcome in this pass


def cells(line: Line, start: date, end: date) -> tuple[Cell, ...]:
    """Every strategy at every setting on one ticker, over one window."""
    return tuple(Cell(name, line, start, end) for name in STRATEGIES)


def journal(kept: Path, line: Line) -> Path:
    """Where a ticker's cells are kept: its venue's folder, as its bars are."""
    return kept / line.venue / f"{line.symbol}.jsonl"


def work(root: Path, kept: Path, start: date, end: date, lines: Sequence[Line]) -> None:
    """A worker's work: each ticker's bars read once from the research store at root, every
    strategy run on them, each outcome kept in the ticker's journal as it finishes."""

    @lru_cache(
        maxsize=1
    )  # one ticker's bars at a time; a read that fails is tried, and fails, for each cell
    def bars(line: Line) -> tuple[Bar, ...]:
        return universe.read(root, line).bars

    for line in lines:
        journal(kept, line).parent.mkdir(parents=True, exist_ok=True)
        batch.run(cells(line, start, end), bars, journal(kept, line))


def _tally(
    todo: dict[Line, tuple[Cell, ...]], kept: Path, before: Sequence[int], report: tune.Report[Line]
) -> Pass:
    """The pass counted from each cell's last line in its journal, which is its outcome
    now: failed, or a record, run in this pass unless the journal held it before. A cell the
    pass wrote no line for, on a ticker whose worker died, is undone; so is one with no line."""
    fates: Counter[str] = Counter()
    for (line, group), had in zip(todo.items(), before, strict=True):
        rows = batch.rows(journal(kept, line))
        held = {(*row["cell"], row["code"], row.get("data")) for row in rows[:had]}
        last = {tuple(row["cell"]): (n >= had, row) for n, row in enumerate(rows)}
        for name in (tuple(batch.row(todo)) for todo in group):
            new, row = last.get(name, (False, {}))
            if not row or (line in report.died and not new):
                fates["undone"] += 1
            elif "error" in row:
                fates["failed"] += 1
            else:
                known = (*name, row["code"], row["data"]) in held
                fates["kept" if known else "ran"] += 1
    return Pass(report, sum(map(len, todo.values())), *(fates[name] for name in COUNTS[1:]))


def _alone(kept: Path) -> IO[bytes]:
    """The folder of journals held for one pass, by a lock the system lets go if it dies."""
    kept.mkdir(parents=True, exist_ok=True)
    lock = (kept / LOCK).open("ab")
    try:
        if sys.platform == "win32":
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as held:
        lock.close()
        raise RuntimeError(f"another pass is at work on {kept}") from held
    return lock


def run(
    lines: Sequence[Line],
    root: Path,
    kept: Path,
    start: date,
    end: date,
    machine: tune.Machine,
    data: Path,
    threads: int,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> Pass:
    """One pass over the lines, whose bars the research store at root holds: every cell from
    start to end run under the auto-tune or found kept, in the journals under kept. The
    auto-tune's flag and log are written in data. A ticker listed twice is refused: two
    workers would hold its one journal; so is a pass on a folder another pass holds."""
    twice = [f"{line.symbol} on {line.venue}" for line, n in Counter(lines).items() if n > 1]
    if twice:
        raise ValueError(f"listed more than once: {', '.join(twice)}")
    todo = {line: cells(line, start, end) for line in lines}
    with _alone(kept):
        before = [len(batch.rows(journal(kept, line))) for line in lines]
        each = partial(work, root, kept, start, end)
        report = tune.run(lines, each, machine, data, threads, clock)
        return _tally(todo, kept, before, report)


def fresh(root: Path, kept: Path, data: Path) -> dict[str, Any]:
    """One pass in a process of its own, on the code then on disk: its count, or the error
    that ended it."""
    command = [sys.executable, "-m", "lab.sweep", str(root), str(kept), str(data)]
    home = Path(__file__).parents[1]
    done = subprocess.run(command, cwd=home, capture_output=True, text=True, check=False)  # noqa: S603
    if done.returncode:
        said = done.stderr.strip().splitlines() or [f"exit code {done.returncode}"]
        return {"error": said[-1]}
    counts: dict[str, Any] = json.loads(done.stdout.splitlines()[-1])
    return counts


def week(
    once: Callable[[], dict[str, Any]],
    data: Path,
    days: float,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    wait: Callable[[float], None] = time.sleep,
) -> None:
    """Pass after pass for that many days, one starting each PAUSE, or as the last ends if
    that is later; each is a line of the week's log in data, with its count or its error. A
    pass that fails is logged and the week carries on."""
    end = clock() + timedelta(days=days)
    while (started := clock()) < end:
        counts = once()
        ended = clock()
        times = {"started": started.isoformat(), "ended": ended.isoformat()}
        with (data / WEEK).open("a", encoding="utf-8") as log:
            log.write(json.dumps({**times, **counts}) + "\n")
        wait(max(0.0, (min(started + PAUSE, end) - ended).total_seconds()))


def unbroken(data: Path) -> timedelta:
    """The longest the week's log shows the grid running without stopping: from one pass's
    start to a later one's end, where no pass failed or ended holding no cell, and none
    started more than a PAUSE after the one before it ended."""
    best, last = timedelta(0), datetime.min.replace(tzinfo=UTC)
    first: datetime | None = None  #: where the run now being read began
    for row in batch.rows(data / WEEK):
        started, ended = (datetime.fromisoformat(row[at]) for at in ("started", "ended"))
        if "error" in row or not row["ran"] + row["kept"]:
            first = None
            continue
        if first is None or started - last > PAUSE:
            first = started
        best, last = max(best, ended - first), ended
    return best


def main(argv: Sequence[str]) -> None:
    """One pass over the research list from the archive's first day to today, its count
    written out; or, given a number of days, the week."""
    parser = argparse.ArgumentParser(description="the grid's pass, or its week")
    for name in ("store", "kept", "data"):  # absolute: a pass's process starts elsewhere
        parser.add_argument(name, type=lambda folder: Path(folder).resolve())
    parser.add_argument("--days", type=float, default=0)
    args = parser.parse_args(argv)
    if args.days:
        return week(partial(fresh, args.store, args.kept, args.data), args.data, args.days)
    window, threads = (archive.SINCE, datetime.now(UTC).date()), os.cpu_count() or 2
    folders = (args.store, args.kept)
    done = run(universe.UNIVERSE, *folders, *window, tune.windows(), args.data, threads)
    died = [f"{line.symbol} on {line.venue}" for line in done.report.died]
    counts = {name: getattr(done, name) for name in COUNTS}
    sys.stdout.write(json.dumps({**counts, "died": died}) + "\n")
    return None


if __name__ == "__main__":
    main(sys.argv[1:])
