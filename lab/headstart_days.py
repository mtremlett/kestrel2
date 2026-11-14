"""headstart_days - THE OLD DATABASE'S DAILY ROWS (R-RUNNER-37, 14 November 2026).
mark_the_trend.db holds SPY from 1993 and more, daily and intraday mixed. Only its table ohlcv's
rows of timeframe 1d are read, opened read-only; its quarantine and unit-drift tables never are.
Each line's rows pass the one store's checks, joined to the days the fast store holds, and enter
under Source.MTT_DB on the days that hold no bar: a fresh bar wins, and each held day that
differs is said. A line already in is not read again, so a run is resumable (`python -m
lab.headstart_days`). The yardsticks first, then the lines, then the research list."""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from desk import archive, bars, store
from desk.bars import Source
from desk.lines import LINES, Line
from desk.store import STRETCH, Bar
from lab import headstart, universe

ROWS = "SELECT ts, open, high, low, close, volume FROM ohlcv WHERE ticker = ? AND timeframe = '1d'"
YARDSTICKS = ("SPY", "QQQ", "ISF", "VUAG")
PENCE = Decimal("0.01")


def order() -> list[Line]:
    """The yardsticks, the other lines, then the research list, each once."""
    every = dict.fromkeys((*LINES, *universe.UNIVERSE))
    first = [line for line in LINES if line.symbol in YARDSTICKS]
    return [*first, *(line for line in every if line not in first)]


def rows(line: Line, old: Path) -> list[Bar]:
    """A line's daily rows in the old database, as it names the line; a row with a hole is left."""
    got = headstart.asked(old, ROWS, line.symbol + archive.SUFFIX[line.venue])
    cells = [(date.fromisoformat(at[:10]), *prices) for at, *prices in got]
    return [
        Bar(day, *(Decimal(str(p)) for p in prices[:4]), int(prices[4]))
        for day, *prices in cells
        if None not in prices
    ]


def _unit(line: Line, mine: list[Bar], held: list[Bar]) -> Decimal:
    """The number the old rows are multiplied by to be in the line's currency: a line quoted in
    pence may be kept in pounds or pence, which only the days both hold can tell."""
    if line.currency not in archive.PENCE:
        return Decimal(1)
    close = {bar.day: bar.close for bar in held}
    fits = {u: 0 for u in (Decimal(1), PENCE)}
    for bar in mine:
        for unit in fits:
            fits[unit] += (
                bar.day in close
                and abs(bar.close * unit - close[bar.day]) <= STRETCH * close[bar.day]
            )
    best = max(fits, key=lambda unit: fits[unit])
    if not fits[best]:
        raise ValueError(f"{line.symbol}: no day held to prove the unit of its old prices")
    return best


def _prices(bar: Bar) -> tuple[Decimal, ...]:
    return bar.open, bar.high, bar.low, bar.close


def _differ(kept: list[Bar], held: list[Bar]) -> str:
    """How many of the held days the old rows disagree on, any of the four prices further apart
    than the store lets two sources be."""
    old = {bar.day: _prices(bar) for bar in kept}
    pairs = [(old[b.day], _prices(b)) for b in held if b.day in old]
    far = sum(any(abs(x - y) > bars.AGREE * y for x, y in zip(a, b, strict=True)) for a, b in pairs)
    return f"{far} of {len(pairs)} days held differ"


def one(line: Line, old: Path, path: Path, day: date) -> str:
    """A line's old daily rows into the store at path, ready to trade on day, and one line
    saying what came of them; the store's checks may refuse it, and nothing is kept."""
    try:
        if Source.MTT_DB in bars.sources(path, line, bars.DAILY):
            return f"{line.symbol}: already in"
        held = list(bars.daily(path, line))
    except LookupError:
        held = []
    mine = rows(line, old)
    if not mine:
        raise ValueError(f"{line.symbol}: the old database holds no daily row of it")
    unit = _unit(line, mine, held)
    scaled = [Bar(b.day, *(p * unit for p in _prices(b)), b.volume) for b in mine]
    with tempfile.TemporaryDirectory() as scratch:
        store.shelve(Path(scratch), line, scaled)
        ready = day if held else scaled[-1].day + timedelta(1)
        parked = store.prepare(Path(scratch), {line: held}, ready)
        if parked:
            raise ValueError(f"{line.symbol}: the one store would park it: {parked[0].reason}")
        kept = store.read(Path(scratch), line.symbol)
    have = {bar.day for bar in held}
    with bars.writing(path, Source.MTT_DB) as round_:
        filled = round_.days(line, [bar for bar in kept if bar.day not in have])
    return f"{line.symbol}: {filled} days filled from {kept[0].day}; {_differ(scaled, held)}"


def main(old: Path, path: Path, lines: list[Line], day: date) -> str:
    """Every line's old daily rows in turn, each its own round; one refused is said and the rest
    go on. Every line's fate is written as it is known, and all of it is returned."""
    said = []
    for line in lines:
        try:
            said.append(one(line, old, path, day))
        except (ValueError, sqlite3.Error) as reason:
            said.append(f"{line.symbol}: refused: {reason}")
        sys.stdout.write(said[-1] + "\n")
    return "\n".join(said)


if __name__ == "__main__":
    DATA = Path(os.environ.get("KESTREL2_DATA") or sys.exit("headstart_days: no KESTREL2_DATA"))
    try:
        FOUND = headstart.imports(DATA.parent / "kestrel2_notes" / "data_register.md")
        OLD = next((p for p in FOUND if p.suffix == ".db"), None)
        OLD = OLD or sys.exit("headstart_days: the register tags no database IMPORT")
        main(OLD, DATA / "market.db", order(), datetime.now(UTC).date())
    except (OSError, ValueError, sqlite3.Error, bars.NoRound) as reason:
        sys.exit(f"headstart_days: {type(reason).__name__}: {reason}")
