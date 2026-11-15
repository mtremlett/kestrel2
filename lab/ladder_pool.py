"""ladder_pool - THE LADDER ON ALL THE PC'S CORES (R-RUNNER-110): `lab/ladder.py`'s cells judged
in `os.cpu_count() - 2` workers at below-normal priority. The rows are the serial run's, in its
order, written by the parent alone; a worker reads the bars itself and keeps its simulations as
tapes (`lab/tape.py`). A GROUP is a run of consecutive cells of one rule, pooled once for its
folds. A cell whose judging breaks in a worker is that cell's row (`error`), never the set's end.
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from collections.abc import Callable, Sequence
from concurrent.futures import ProcessPoolExecutor
from contextlib import ExitStack
from datetime import UTC, datetime
from itertools import groupby
from pathlib import Path
from typing import Any

from lab import batch, cell, ladder, tape, verdict
from lab.batch import Bars
from lab.cell import Cell
from lab.ladder import FIRST, Plan
from lab.rung import Rates

SPARE = 2  #: cores left to the rest of the PC
BELOW_NORMAL = 0x4000  #: Windows' BELOW_NORMAL_PRIORITY_CLASS
Task = tuple[list[Cell], list[Cell], tuple[int | str, int], list[verdict.Row | None], datetime]
_held: dict[str, Any] = {}  #: a worker's bars and rates, set once as it starts
_kept = ExitStack()  #: holds the worker's tape context open


def workers() -> int:
    """The pool's size: every core but two, and at least one."""
    return max(1, (os.cpu_count() or 1) - SPARE)


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


def run(
    home: Path,
    make_bars: Callable[[], Bars],
    pounds: Rates,
    todo: Sequence[Cell] | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    plan: Plan = FIRST,
    size: int | None = None,
) -> str:
    """`ladder.run` on the pool: the same register, results file and keys; one line of counts."""
    if cell.code_version(module=ladder.ME) != cell.RUNGS[ladder.ME]:
        raise RuntimeError("the code on disk has changed since this process loaded it")
    todo = ladder.cells() if todo is None else todo
    results, count = ladder.begun(home, todo, plan)
    whole = ladder._whole(results)
    last = ladder._last(whole)
    stamp = now()
    tasks: list[Task] = []
    for rule, run_of in groupby(todo, key=lambda c: c.strategy):
        group = list(run_of)
        mine = [c for c in todo if c.strategy == rule]
        before = [last.get(tuple(batch.row(c))) for c in group]
        tasks.append((group, mine, (plan.tag, count), before, stamp))
    tally: Counter[str] = Counter()
    tapes = home / ladder.FOLDER / tape.FOLDER
    pool = ProcessPoolExecutor(
        size or workers(), initializer=_begin, initargs=(make_bars, pounds, tapes)
    )
    with pool, results.open("ab") as out:
        out.truncate(len(whole))
        for task, rows in zip(tasks, pool.map(_group, tasks), strict=True):
            for made, was in zip(rows, task[3], strict=True):
                row = was if made == was else made  #: a row kept comes back a copy: it is `was`
                if row is not was:
                    out.write(json.dumps(row).encode() + b"\n")
                    out.flush()
                    os.fsync(out.fileno())
                ladder._count(tally, row, was)
    return (
        f"ladder set {plan.tag} on {size or workers()} cores: {len(todo)} cells, judged against "
        f"{count} trials: {tally['judged']} judged now, {tally['kept']} kept from before, "
        f"{tally['error']} could not be judged and are tried again next run, "
        f"{tally['refused']} refused by the desk's sizing."
    )
