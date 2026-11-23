"""ladder_pool - THE LADDER ON ALL THE PC'S CORES (R-RUNNER-110): `lab/ladder.py`'s cells judged
in workers at below-normal priority, as many as the cores and the FREE MEMORY allow
(R-RUNNER-203). The rows are the serial run's, in its order, written by the parent alone; a
worker reads the bars itself and keeps its simulations as tapes (`lab/tape.py`). A GROUP is a
run of consecutive cells of one rule, pooled once for its folds. A cell whose judging breaks in
a worker is that cell's row (`error`), never the set's end.

THE UNIT OF WORK (R-RUNNER-166) is a rule's line in one fold, never a whole line's history: the
simulations the folds need are WARMED, one task each (rule, line, fold year), kept as tapes, so
a group then reads tapes instead of simulating, and a pass spreads over every worker. The warm
runs `AHEAD` rules before the group that reads them, so a rule's rows are written as it ends.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from collections import Counter
from collections.abc import Callable, Iterator, Sequence
from concurrent.futures import Future, ProcessPoolExecutor
from contextlib import ExitStack
from datetime import UTC, date, datetime
from functools import partial
from itertools import groupby
from pathlib import Path
from typing import Any, BinaryIO

from lab import batch, cell, ladder, tape, tune, verdict
from lab.batch import Bars
from lab.cell import Cell
from lab.folds import YEARS
from lab.ladder import FIRST, Plan
from lab.rung import Rates

SPARE = 2  #: cores left to the rest of the PC
RESERVE = 0.2  #: the share of the PC's memory kept free of the pool
PEAK = 5 * 2**30  #: bytes one worker reaches at its peak, as measured overnight
BELOW_NORMAL = 0x4000  #: Windows' BELOW_NORMAL_PRIORITY_CLASS
Task = tuple[
    list[Cell],
    list[Cell],
    tuple[int | str, int],
    list[verdict.Row | None],
    datetime,
]
AHEAD = 2  #: rules warmed before the one whose group is being read
Unit = tuple[Cell, int | None]  #: a line's cell and one fold's year, or None for its whole window
_held: dict[str, Any] = {}  #: a worker's bars and rates, set once as it starts
_kept = ExitStack()  #: holds the worker's tape context open


STOP = "STOP"  #: the file the runner writes in the ladder's folder to ask a pass to end


def _asked(stop: Path, began: float) -> str | None:
    """Why the runner asked this pass to stop, or None. A STOP older than the pass's start is
    removed and ignored; one written after it is read and left for the pass to remove."""
    if not stop.exists():
        return None
    if stop.stat().st_mtime < began:
        stop.unlink()
        return None
    return stop.read_text(encoding="utf-8").strip() or "asked to stop"


def workers(total: int, free: int, cores: int | None = None) -> int:
    """The pool's size: every core but two, or as many as fit in the free memory beyond a
    reserve of RESERVE of the PC's (for the desk, the Gateway and lane sessions), each taking
    PEAK bytes; at least one."""
    return max(1, min((cores or os.cpu_count() or 1) - SPARE, fits(total, free)))


def fits(total: int, free: int) -> int:
    """How many workers the free memory beyond the reserve holds, at PEAK each; at least one."""
    return max(1, int((free - RESERVE * total) // PEAK))


def _memory() -> tuple[int, int]:
    """This PC's memory, in bytes: in all, and free."""
    machine = tune.windows()
    try:
        return machine.memory()
    finally:
        machine.close()


class Yielding:
    """The pool that YIELDS MEMORY (R-RUNNER-273): at most `size` tasks run at once, and as each
    ends the free memory is read again and the number allowed set to what it holds (down to one,
    up to `size` once it returns). Queued tasks keep their order; every finished task keeps its
    result. The workers themselves stay up; the work given them is what shrinks."""

    def __init__(
        self, pool: ProcessPoolExecutor, size: int, memory: Callable[[], tuple[int, int]]
    ) -> None:
        self.pool, self.size, self.memory = pool, size, memory
        self.allowed, self.running = size, 0
        self.queue: list[tuple[Callable[[Any], Any], Any, Future[Any]]] = []
        self.lock = threading.Lock()

    def submit(self, fn: Callable[[Any], Any], arg: Any) -> Future[Any]:
        """Queue one task; its future is set when it ends."""
        mine: Future[Any] = Future()
        with self.lock:
            self.queue.append((fn, arg, mine))
        self._dispatch()
        return mine

    def _dispatch(self) -> None:
        with self.lock:
            sent = []
            while self.queue and self.running < self.allowed:
                sent.append(self.queue.pop(0))
                self.running += 1
        for fn, arg, mine in sent:
            try:
                self.pool.submit(fn, arg).add_done_callback(partial(self._end, mine=mine))
            except BaseException as error:  # noqa: BLE001 - handed on to the waiting future
                mine.set_exception(error)

    def _end(self, done: Future[Any], mine: Future[Any]) -> None:
        """One task ended: re-read the memory, set the number allowed, pass its result on."""
        if done.cancelled():
            mine.cancel()
        elif done.exception() is not None:
            mine.set_exception(done.exception())
        else:
            mine.set_result(done.result())
        try:
            total, free = self.memory()
        except OSError as error:  # the queued tasks are told, never left waiting for a read
            with self.lock:
                waiting, self.queue = self.queue, []
            for _, _, queued in waiting:
                queued.set_exception(error)
            return
        with self.lock:
            self.running -= 1
            self.allowed = min(self.size, fits(total, free))
        self._dispatch()

    def shutdown(self, wait: bool = True, cancel_futures: bool = False) -> None:
        """The pool's shutdown; tasks still queued here are dropped when asked to cancel."""
        if cancel_futures:
            with self.lock:
                self.queue.clear()
        self.pool.shutdown(wait=wait, cancel_futures=cancel_futures)


def _begin(make_bars: Callable[[], Bars], pounds: Rates, tapes: Path) -> None:
    """A worker's start: below normal priority, its own bars, its simulations kept as tapes."""
    if sys.platform == "win32":
        import ctypes

        kernel = ctypes.windll.kernel32
        kernel.SetPriorityClass(kernel.GetCurrentProcess(), BELOW_NORMAL)
    else:
        os.nice(10)
    _held.update(bars=make_bars(), pounds=pounds)
    _kept.enter_context(tape.on(tapes))  #: for the worker's whole life


def units(cells: Sequence[Cell]) -> list[Unit]:
    """A rule's cells cut to units: each cell's whole window, then one per fold year, which
    `lab/folds.py`'s `pool` takes as the last YEARS whole years before the cell's end."""
    out: list[Unit] = []
    for c in cells:
        last = c.end.year if c.end >= date(c.end.year, 12, 31) else c.end.year - 1
        out += [(c, None), *((c, y) for y in range(last - YEARS + 1, last + 1))]
    return out


def _parts(made: Cell, own: Sequence[Any], year: int | None) -> list[Cell]:
    """The cells a unit simulates, as `folds._stretch` cuts them: a year's in-sample (all before
    it) and out-of-sample (the year), each if the line has a bar in it."""
    if year is None:
        return [made]
    spans = ((None, date(year - 1, 12, 31)), (date(year, 1, 1), date(year, 12, 31)))
    parts = []
    for first, end in spans:
        begin = made.start if first is None else max(first, made.start)
        if begin <= end and any(begin <= bar.day <= end for bar in own):
            parts.append(Cell(made.strategy, made.line, begin, end))
    return parts


def _warm(unit: Unit) -> None:
    """One unit's simulations, kept as tapes by `_begin`'s context. A break is not told here: the
    group meets it again in its own cell and says it as that cell's row."""
    c, year = unit
    try:
        made, own, _ = ladder._resolve(c, _held["bars"])
        for part in _parts(made, own, year):
            cell.run(part, own)
    except Exception:  # noqa: BLE001 - the cell's group meets it and records it as its row
        return


def _group(task: Task) -> list[verdict.Row]:
    """One group's rows, each cell's as `ladder._one` makes it."""
    group, rule_cells, tagged, was, now = task
    shared = ladder.Shared(rule_cells)
    rows: list[verdict.Row] = []
    for c, before in zip(group, was, strict=True):
        try:
            rows.append(ladder._one(c, _held["bars"], _held["pounds"], tagged, before, shared, now))
        except Exception as error:  # noqa: BLE001 - a cell's break is its row, not the set's end
            head: dict[str, Any] = {"set": tagged[0], "cell": batch.row(c), "trials": tagged[1]}
            rows.append(
                head | {"error": f"{type(error).__name__}: {error}", "tried": now.isoformat()}
            )
    return rows


def _read(pool: Yielding, tasks: Sequence[Task]) -> Iterator[tuple[Task, list[verdict.Row]]]:
    """Each task's rows, in the tasks' order, as its group ends: a rule's units are warmed
    `AHEAD` rules early, and its group is asked once all of them are done."""
    warm: dict[int, list[Future[None]]] = {}

    def start(n: int) -> None:
        if n < len(tasks):
            warm[n] = [pool.submit(_warm, u) for u in units(tasks[n][1])]

    for n in range(AHEAD):
        start(n)
    for n, task in enumerate(tasks):
        for done in warm.pop(n):
            done.result()
        asked = pool.submit(_group, task)
        start(n + AHEAD)
        yield task, asked.result()


def _write(
    pool: Yielding,
    tasks: Sequence[Task],
    out: BinaryIO,
    tally: Counter[str],
    asking: tuple[Path, float],
) -> str | None:
    """Write each group's new rows as it ends; if the runner has asked, stop after that group
    (the rows so far written), drop the unstarted warm-ups and the STOP file, and say why."""
    for task, rows in _read(pool, tasks):
        for made, was in zip(rows, task[3], strict=True):
            row = was if made == was else made  #: a row kept comes back a copy: it is `was`
            if row is not was:
                out.write(json.dumps(row).encode() + b"\n")
                out.flush()
                os.fsync(out.fileno())
            ladder._count(tally, row, was)
        why = _asked(*asking)
        if why:
            pool.shutdown(wait=False, cancel_futures=True)
            asking[0].unlink()
            return why
    return None


def run(
    home: Path,
    make_bars: Callable[[], Bars],
    pounds: Rates,
    todo: Sequence[Cell] | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    plan: Plan = FIRST,
    size: int | None = None,
    memory: Callable[[], tuple[int, int]] = _memory,
) -> str:
    """`ladder.run` on the pool: the same register, results file and keys; one line of counts."""
    if cell.code_version(module=ladder.ME) != cell.RUNGS[ladder.ME]:
        raise RuntimeError("the code on disk has changed since this process loaded it")
    todo = ladder.cells() if todo is None else todo
    results, count = ladder.begun(home, todo, plan)
    last = ladder.Kept(results)
    stamp = now()
    stop, began = home / ladder.FOLDER / STOP, time.time()
    _asked(stop, began)  #: a stale STOP goes now, before the first unit
    tasks: list[Task] = []
    for rule, run_of in groupby(todo, key=lambda c: c.strategy):
        group = list(run_of)
        mine = [c for c in todo if c.strategy == rule]
        before = [last.get(tuple(batch.row(c))) for c in group]
        tasks.append((group, mine, (plan.tag, count), before, stamp))
    tally: Counter[str] = Counter()
    tapes = home / ladder.FOLDER / tape.FOLDER
    size = size or workers(*memory())
    inner = ProcessPoolExecutor(size, initializer=_begin, initargs=(make_bars, pounds, tapes))
    with inner, results.open("ab") as out:
        out.truncate(last.end)
        why = _write(Yielding(inner, size, memory), tasks, out, tally, (stop, began))
    if why:
        return f"stopped after a unit: {why}"
    return (
        f"ladder set {plan.tag} on {size} cores: {len(todo)} cells, judged against "
        f"{count} trials: {tally['judged']} judged now, {tally['kept']} kept from before, "
        f"{tally['error']} could not be judged and are tried again next run, "
        f"{tally['refused']} refused by the desk's sizing."
    )
