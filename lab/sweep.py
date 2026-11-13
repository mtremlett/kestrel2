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
One pass at a time works on a folder of journals.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from functools import lru_cache, partial
from pathlib import Path

from desk.lines import Line
from desk.store import Bar
from desk.strategy import STRATEGIES
from lab import batch, tune, universe
from lab.cell import Cell


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

    @lru_cache(maxsize=1)  # one ticker's bars at a time; a failed read is every cell's error
    def bars(line: Line) -> tuple[Bar, ...]:
        return universe.read(root, line).bars

    for line in lines:
        journal(kept, line).parent.mkdir(parents=True, exist_ok=True)
        batch.run(cells(line, start, end), bars, journal(kept, line))


def _tally(
    todo: Sequence[Sequence[Cell]], kept: Path, before: Sequence[int], report: tune.Report[Line]
) -> Pass:
    """The pass counted from what it added to each journal: a cell's last outcome there, and
    for a cell with none, kept where its ticker's worker finished and undone where it died."""
    ran = failed = held = undone = 0
    for group, had in zip(todo, before, strict=True):
        line = group[0].line
        new = batch.rows(journal(kept, line))[had:]
        last = {tuple(row["cell"]): "error" in row for row in new}
        failed += sum(last.values())
        ran += len(last) - sum(last.values())
        if line in report.died:
            undone += len(group) - len(last)
        else:
            held += len(group) - len(last)
    return Pass(report, sum(len(group) for group in todo), ran, held, failed, undone)


def run(
    lines: Sequence[Line],
    root: Path,
    kept: Path,
    start: date,
    end: date,
    machine: tune.Machine,
    data: Path,
    threads: int,
) -> Pass:
    """One pass over the lines, whose bars the research store at root holds: every cell from
    start to end run under the auto-tune or found kept, in the journals under kept. The
    auto-tune's flag and log are written in data."""
    todo = [cells(line, start, end) for line in lines]
    before = [len(batch.rows(journal(kept, line))) for line in lines]
    report = tune.run(lines, partial(work, root, kept, start, end), machine, data, threads)
    return _tally(todo, kept, before, report)
