"""headstart_hours - THE OLD STOOQ STORE'S HOURLY BARS (R-RUNNER-10, his ruling of 16 November 2026:
history keeps every timeframe). stooq_store's freq=h parquet, opened read-only, enters the history
database under Source.STOOQ_HOURLY. Stooq stamps an hourly bar by the hour it ends, on Stooq's
clock; the store names a bar by its start in UTC. Only rows the old store marks OK are read; a
bar its day's fresh daily bar does not vouch for (the unit and the range) or that the one store's
checks refuse is left and counted, and a moment already held keeps its bar. A line already in is
not read again, so a second run adds nothing (`python -m lab.headstart_hours`)."""

from __future__ import annotations

import os
import sqlite3
import sys
from collections.abc import Callable
from dataclasses import astuple
from datetime import timedelta
from pathlib import Path

import pyarrow.parquet as pq  # type: ignore[import-untyped]  # ships no stubs

from desk import bars
from desk.bars import Five, Source
from desk.lines import Line
from desk.spans import Timed
from lab import headstart, headstart_days

HOUR = timedelta(hours=1)
SPAN = "1h"
COLUMNS = (*headstart.PARQUET, "row_state")


def hours(line: Line, folder: Path) -> tuple[Five, ...]:
    """A line's OK hourly bars in stooq_store (freq=h/market=../ticker=SYM.MKT/part.parquet),
    each named by its start in UTC; none held is refused."""
    market = headstart.MARKET[line.venue]
    file = folder / f"freq=h/market={market.lower()}/ticker={line.symbol}.{market}/part.parquet"
    if not file.is_file():
        raise ValueError(f"{file.parent.name} holds no hourly bar of {line.symbol}")
    table = pq.ParquetFile(file).read(columns=list(COLUMNS))
    rows = zip(*(table[k].to_pylist() for k in COLUMNS), strict=True)
    return headstart._stamped(  # noqa: SLF001  # the one reading of Stooq's clock
        ((at - HOUR, *rest) for at, *rest, state in rows if state == "OK" and at is not None),
        True,
    )


def enter(
    line: Line, given: tuple[Five | Timed, ...], path: Path, span: str, source: Source
) -> str:
    """A line's old bars of a span into the history database at path's side, each vouched for by
    its day's fresh daily bar, and one line saying what came of them."""
    days = {bar.day: bar for bar in bars.daily(path, line)}
    judged = [headstart._vouched(line, b, days.get(b.start.date())) for b in given]  # noqa: SLF001
    sound = [b for b in judged if not isinstance(b, str)]
    kept, faults = bars.checked(line, sound)
    with bars.writing(path, source) as round_:
        filled = round_.timed(
            line, span, [b if isinstance(b, Timed) else Timed(span, *astuple(b)) for b in kept]
        )
    return (
        f"{line.symbol}: {filled} {span} bars filled; {len(given) - len(sound)} not vouched,"
        f" {len(faults)} faults"
    )


def held(path: Path, line: Line, span: str, source: Source) -> bool:
    """The line already holds bars of this span from this source: a second run reads nothing."""
    try:
        return source in bars.sources(path, line, span)
    except LookupError:
        return False  # the store never held a bar of the line's span: the first run


def one(line: Line, old: Path, path: Path) -> str:
    """A line's old hourly bars into the history database at path's side, and one line saying
    what came of them. The line's daily bars must be held: they vouch for the hours."""
    if held(path, line, SPAN, Source.STOOQ_HOURLY):
        return f"{line.symbol}: already in"
    return enter(line, hours(line, old), path, SPAN, Source.STOOQ_HOURLY)


def main(
    old: Path, path: Path, lines: list[Line], doing: Callable[[Line, Path, Path], str] = one
) -> str:
    """Every line's old hourly bars in turn, each its own round; one refused is said and the
    rest go on. Every line's fate is written as it is known, and all of it is returned."""
    said = []
    for line in lines:
        try:
            said.append(doing(line, old, path))
        except (ValueError, LookupError, sqlite3.Error) as reason:
            said.append(f"{line.symbol}: refused: {reason}")
        sys.stdout.write(said[-1] + "\n")
    return "\n".join(said)


if __name__ == "__main__":
    DATA = Path(os.environ.get("KESTREL2_DATA") or sys.exit("headstart_hours: no KESTREL2_DATA"))
    try:
        FOUND = headstart.imports(DATA.parent / "kestrel2_notes" / "data_register.md")
        OLDS = [p for p in FOUND if (p / "freq=h").is_dir()]
        OLDS or sys.exit("headstart_hours: the register tags no hourly store IMPORT")
        for OLD in OLDS:
            main(OLD, DATA / bars.LIVE, headstart_days.order())
    except (OSError, ValueError, sqlite3.Error, bars.NoRound) as reason:
        sys.exit(f"headstart_hours: {type(reason).__name__}: {reason}")
