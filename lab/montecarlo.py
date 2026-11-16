"""montecarlo - THE LADDER'S MONTE CARLO RUNG: how bad could the same trades have run?

A trial's trades, each as its return on the equity it was taken with, are drawn again with
replacement PATHS times, as many to a path as the trial made, and each path is compounded.
What comes back is the spread of the drawdowns and of the returns those paths make. It
measures and never gates: no verdict reads it. The draw is seeded, so a trial run again is
resampled the same; a faster draw (a GPU) may stand behind `resample` only if it gives the
same answer.

`python -m lab.montecarlo` resamples every cell the ladder judged (its results file) and every
cell the grid holds, and keeps one record per cell under `montecarlo/` in the data folder,
keyed by what made it: a cell whose inputs have not changed is kept, not resampled again.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from functools import cache
from pathlib import Path
from typing import Any, BinaryIO

from desk.command import CAPITAL
from desk.lines import LINES, Line
from desk.orders import Settings
from lab import batch, cell, ladder, rung, sweep
from lab.cell import Cell, Record, Trade

ME = "lab.montecarlo"  #: this module as the cell knows it
FOLDER, RESULTS = "montecarlo", "results.jsonl"
PATHS = 1000
QUANTILES = (Decimal("0.05"), Decimal("0.5"), Decimal("0.95"))  #: the cuts reported


@dataclass(frozen=True)
class Spread:
    """A measure's value at each cut of QUANTILES, lowest cut first."""

    low: Decimal
    median: Decimal
    high: Decimal


@dataclass(frozen=True)
class Resampled:
    """The drawdowns (a fraction of the peak, never negative) and the total returns of the paths."""

    paths: int
    drawdown: Spread
    returns: Spread


def resample(trades: Sequence[Decimal], seed: int, paths: int = PATHS) -> Resampled:
    """The spread of drawdowns and returns over `paths` resamplings of the trades' returns."""
    if not trades:
        raise ValueError("montecarlo: no trades to resample")
    if paths < 1:
        raise ValueError(f"montecarlo: paths must be at least 1, got {paths}")
    if any(t <= -1 for t in trades):
        raise ValueError("montecarlo: a trade's return of -100% or worse leaves no equity")
    rng = random.Random(seed)  # noqa: S311 - a repeatable draw, not a secret
    drawdowns: list[Decimal] = []
    returns: list[Decimal] = []
    for _ in range(paths):
        drawdown, total = _path(rng.choices(trades, k=len(trades)))
        drawdowns.append(drawdown)
        returns.append(total)
    return Resampled(paths, _spread(drawdowns), _spread(returns))


def _path(drawn: Sequence[Decimal]) -> tuple[Decimal, Decimal]:
    """The deepest fall from a peak, and the total return, of one compounded path."""
    equity = peak = Decimal(1)
    deepest = Decimal(0)
    for t in drawn:
        equity *= 1 + t
        peak = max(peak, equity)
        deepest = max(deepest, 1 - equity / peak)
    return deepest, equity - 1


def _spread(values: list[Decimal]) -> Spread:
    ordered = sorted(values)
    low, median, high = (ordered[int(q * (len(ordered) - 1))] for q in QUANTILES)
    return Spread(low, median, high)


@dataclass(frozen=True)
class Job:
    """A cell to resample: where it came from, what made its trades, and the trades if held."""

    source: str  #: "ladder" or "grid"
    cell: Cell
    made: str  #: the key the source gave it: change that and the cell is resampled again
    trades: tuple[Trade, ...] | None  #: the grid's held trades; None for the ladder's own


#: a job's trades, each as its return after costs; or, as words, the desk's sizing refusing them
Gains = Callable[[Job], Sequence[Decimal] | str]


def _lines(path: Path) -> Iterator[dict[str, Any]]:
    """The whole lines of a results file, a last line cut short by a stop left out."""
    text = path.read_bytes() if path.exists() else b""
    yield from map(json.loads, text[: text.rfind(b"\n") + 1].splitlines())


def _cell(lines: Mapping[tuple[str, str], Line], row: Mapping[str, Any], start: str) -> Cell:
    """The cell a results line names, over the window from `start` to the line's own end."""
    strategy, symbol, venue, _, end = row["cell"]
    line = lines[symbol, venue]
    return Cell(strategy, line, date.fromisoformat(start), date.fromisoformat(end))


def jobs(home: Path) -> list[Job]:
    """Every ladder cell that traded and every grid cell held, the latest line of each."""
    found: dict[tuple[str, ...], Job] = {}
    stored = sweep.held(
        home / "grid" / "store"
    )  #: the grid's lines; the desk's own take precedence
    lines = {(x.symbol, x.venue): x for x in (*stored, *LINES)}
    for row in _lines(home / ladder.FOLDER / ladder.RESULTS):
        if row.get("trades") and "key" in row:
            found[("ladder", *row["cell"])] = Job(
                "ladder", _cell(lines, row, row["from"]), row["key"], None
            )
    for path in sorted((home / "grid" / "held").glob("*/*.jsonl")):
        for row in _lines(path):
            trades = tuple(
                Trade(date.fromisoformat(b), s and date.fromisoformat(s)) for b, s in row["trades"]
            )
            made = row["code"] + row["data"]
            found[("grid", *row["cell"])] = Job(
                "grid", _cell(lines, row, row["cell"][3]), made, trades
            )
    return [job for job in found.values() if job.trades is None or job.trades]


def _key(job: Job) -> str:
    """What made the resampling: its source's key and the code of this rung and all it reaches."""
    return hashlib.sha256(f"{job.made}\n{cell.RUNGS[ME]}\n{PATHS}".encode()).hexdigest()


def run(home: Path, gains: Gains) -> str:
    """Every job resampled and kept under home, a job kept already skipped: the line of counts."""
    results = home / FOLDER / RESULTS
    results.parent.mkdir(parents=True, exist_ok=True)
    kept = {tuple(row["id"]): row["key"] for row in _lines(results)}
    text = results.read_bytes() if results.exists() else b""
    tally = {"now": 0, "before": 0, "refused": 0, "failed": 0}
    with results.open("ab") as out:
        out.truncate(text.rfind(b"\n") + 1)
        for job in jobs(home):
            id_, key = [job.source, *batch.row(job.cell)], _key(job)
            if kept.get(tuple(id_)) == key:
                tally["before"] += 1
                continue
            try:
                made = gains(job)
                if isinstance(made, str):  #: the desk's sizing declined: a fact of the cell
                    _keep(out, {"id": id_, "key": key, "refused": made})
                    tally["refused"] += 1
                    continue
                got = resample(made, int(key[:16], 16))
            except ladder.FAILED as error:
                sys.stderr.write(f"montecarlo: {id_}: {error}\n")
                tally["failed"] += 1
                continue
            row = {"id": id_, "key": key, "trades": len(made), "paths": got.paths}
            row |= {"drawdown": _out(got.drawdown), "returns": _out(got.returns)}
            out.write(json.dumps(row).encode() + b"\n")
            out.flush()
            os.fsync(out.fileno())
            tally["now"] += 1
    done = f"{tally['now']} resampled now, {tally['before']} kept from before"
    done += f", {tally['refused']} refused by the desk's sizing" if tally["refused"] else ""
    return done + (f", {tally['failed']} could not be resampled" if tally["failed"] else "")


def _keep(out: BinaryIO, row: dict[str, Any]) -> None:
    """One result line, written whole and forced to disk."""
    out.write(json.dumps(row).encode() + b"\n")
    out.flush()
    os.fsync(out.fileno())


def _out(spread: Spread) -> list[str]:
    """A spread as the results file keeps it: each cut as exact decimal text, lowest cut first."""
    return [str(spread.low), str(spread.median), str(spread.high)]


def priced(home: Path) -> Gains:
    """The gains of a job from its line's bars in the data folder and the ladder's rates."""
    pounds = cache(lambda: ladder.rates(home=home))
    settings = Settings(CAPITAL)
    stores = {"ladder": ladder.stored(home), "grid": batch.stored(home / "grid" / "store")}

    def gains(job: Job) -> Sequence[Decimal] | str:
        bars = stores[job.source](job.cell.line)
        if job.trades is None:
            record = cell.run(job.cell, bars)
        else:
            now = cell.key(job.cell, bars)
            if now.code + now.data != job.made:
                raise ValueError(f"{job.cell}: the held trades were not made by this code and bars")
            record = Record(now, len(bars), job.trades)
        judged = rung.judge(record, bars, settings, pounds(), [])
        return judged.refusal if judged.refusal is not None else [p.gain for p in judged.trades]

    return gains


def main(env: Mapping[str, str]) -> int:
    """Resample the data folder named by KESTREL2_DATA and print the line of counts."""
    if not env.get("KESTREL2_DATA"):
        sys.exit("montecarlo: KESTREL2_DATA names no data folder, so there is nothing to resample")
    home = Path(env["KESTREL2_DATA"])
    sys.stdout.write(run(home, priced(home)) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(os.environ))
