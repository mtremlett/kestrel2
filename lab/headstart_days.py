"""headstart_days - THE OLD DATABASE'S DAILY ROWS (R-RUNNER-37, 14 November 2026).
mark_the_trend.db holds SPY from 1993 and more, daily and intraday mixed. Only its table ohlcv's
rows of timeframe 1d are read, opened read-only; its quarantine and unit-drift tables never are.
Each line's rows pass the one store's checks, joined to the days the fast store holds, and enter
under Source.MTT_DB on the days that hold no bar: a fresh bar wins, and each held day that
differs is said. A line already in is not read again, so a run is resumable (`python -m
lab.headstart_days`). stooq_store's daily parquet (market=uk|us) enters the same way under
Source.STOOQ_DAILY, rows it marks OK only; stooq_store_matrix's 1d arrays likewise, under
Source.MATRIX_DAILY, a row with a hole left; ibkr_store's daily parquet (the same form, a
fetch record beside each file) under Source.IBKR_DAILY; mark_the_trend's Stooq files (a file a
line, <SYMBOL>.d.parquet or <SYMBOL>.L.parquet) under Source.TREND_DAILY. Old rows that are
the adjusted form of the as-traded days held are refused whole by the one store's check against
them, and said. The yardsticks first, then the lines, then the research list."""

from __future__ import annotations

import os
import sqlite3
import sys
import zipfile
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq  # type: ignore[import-untyped]  # ships no stubs

from desk import archive, bars, store
from desk.bars import Source
from desk.daily_local import stooq_rows
from desk.lines import LINES, Line
from desk.store import STRETCH, Bar
from lab import headstart, universe

ROWS = "SELECT ts, open, high, low, close, volume FROM ohlcv WHERE ticker = ? AND timeframe = '1d'"
YARDSTICKS = ("SPY", "QQQ", "ISF", "VUAG")
PENCE = Decimal("0.01")
Rows = Callable[[Line, Path], list[Bar]]


def order() -> list[Line]:
    """The yardsticks, the other lines, then the research list, each once."""
    every = dict.fromkeys((*LINES, *universe.UNIVERSE))
    first = [line for line in LINES if line.symbol in YARDSTICKS]
    return [*first, *(line for line in every if line not in first)]


def _d(x: float | str) -> Decimal:
    return Decimal(str(x))


def rows(line: Line, old: Path) -> list[Bar]:
    """A line's daily rows in the old database, as it names the line; a row with a hole is left."""
    got = headstart.asked(old, ROWS, line.symbol + archive.SUFFIX[line.venue])
    return [
        Bar(date.fromisoformat(at[:10]), _d(o), _d(h), _d(lo), _d(c), int(v))
        for at, o, h, lo, c, v in got
        if None not in (o, h, lo, c, v)
    ]


def matrix_rows(line: Line, folder: Path) -> list[Bar]:
    """A line's daily rows in the old desk's matrices (<SYMBOL>.<UK|US>_1d: an array of day
    stamps in milliseconds and one of opens, highs, lows, closes, volumes); a day by its stamp."""
    name = headstart._named(line, "1d")  # noqa: SLF001  # the matrices' one naming
    if not (folder / f"{name}_ts.npy").is_file():
        raise ValueError(f"{folder.name} holds no daily matrix of {line.symbol}")
    stamps = np.load(folder / f"{name}_ts.npy").tolist()
    table = np.load(folder / f"{name}_ohlcv.npy").T
    return [
        Bar(
            (bars.EPOCH + timedelta(milliseconds=at)).date(),
            _d(row[0]),
            _d(row[1]),
            _d(row[2]),
            _d(row[3]),
            int(row[4]),
        )
        for at, row in zip(stamps, table, strict=True)
        if np.isfinite(row).all()
    ]


def trend_rows(line: Line, folder: Path) -> list[Bar]:
    """A line's daily rows in mark_the_trend's Stooq folder (<SYMBOL>.d.parquet, <SYMBOL>.L.parquet
    in London: Open, High, Low, Close, Volume and the day's DATE); a row with a hole is left."""
    file = folder / f"{line.symbol}{archive.SUFFIX[line.venue] or '.d'}.parquet"
    if not file.is_file():
        raise ValueError(f"{folder.name} holds no daily file of {line.symbol}")
    columns = ("DATE", "Open", "High", "Low", "Close", "Volume")
    table = pq.ParquetFile(file).read(columns=list(columns))
    return [
        Bar(at.date(), _d(o), _d(h), _d(lo), _d(c), int(v))
        for at, o, h, lo, c, v in zip(*(table[k].to_pylist() for k in columns), strict=True)
        if None not in (o, h, lo, c, v)
    ]


def raw_rows(line: Line, folder: Path) -> list[Bar]:
    """A line's daily rows in the newest dated folder of Stooq's raw zips under folder: its one
    text file (<symbol>.uk.txt) of ticker, span, date, time, prices, volume; a row with a hole
    or a number that is none is left."""
    market = headstart.MARKET[line.venue].lower()
    zips = sorted(folder.glob(f"*/d_{market}_txt*.zip"))
    if not zips:
        raise ValueError(f"{folder.name} holds no zip of {market} daily bars")
    with zipfile.ZipFile(zips[-1]) as opened:
        name = f"/{line.symbol.lower()}.{market}.txt"
        found = [m for m in opened.namelist() if m.endswith(name)]
        if len(found) != 1:
            raise ValueError(f"{zips[-1].name} holds {len(found)} files of {line.symbol}, not one")
        cells = [row.split(",") for row in opened.read(found[0]).decode().splitlines()[1:]]
    return [
        Bar(
            datetime.strptime(c[2], "%Y%m%d").date(),
            _d(c[4]),
            _d(c[5]),
            _d(c[6]),
            _d(c[7]),
            int(float(c[8])),
        )
        for c in cells
        if len(c) > 8 and all(c[2:9])
    ]


def _daily(where: Path) -> bool:
    """A folder of daily rows: stooq_store's, the matrices', mark_the_trend's or the raw zips'."""
    return (
        next(where.glob("*/d_*_txt*.zip"), None) is not None
        or (where / "freq=d").is_dir()
        or next(where.glob("*_1d_ts.npy"), None) is not None
        or next(where.glob("*.d.parquet"), None) is not None
    )


def form(where: Path) -> tuple[Source, Rows]:
    """An old store's daily source and reader by its form (database, Stooq, ibkr, matrices)."""
    if where.suffix == ".db":
        return Source.MTT_DB, rows
    if (where / "freq=d").is_dir():  # only ibkr_store keeps a fetch record beside its bars
        found = next((where / "freq=d").glob("*/*/fetch.json"), None)
        return (Source.IBKR_DAILY if found else Source.STOOQ_DAILY), stooq_rows
    if next(where.glob("*.d.parquet"), None) is not None:
        return Source.TREND_DAILY, trend_rows
    if next(where.glob("*/d_*_txt*.zip"), None) is not None:
        return Source.STOOQ_RAW, raw_rows
    if _daily(where):
        return Source.MATRIX_DAILY, matrix_rows
    raise ValueError(f"{where}: no daily reader for a store of this form")


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
    source, read = form(old)
    try:
        if source in bars.sources(path, line, bars.DAILY):
            return f"{line.symbol}: already in"
        held = list(bars.daily(path, line))
    except LookupError:
        held = []
    mine = read(line, old)
    if not mine:
        raise ValueError(f"{line.symbol}: the old store holds no daily row of it")
    unit = _unit(line, mine, held)
    scaled = [
        Bar(b.day, b.open * unit, b.high * unit, b.low * unit, b.close * unit, b.volume)
        for b in mine
    ]
    ready = day if held else scaled[-1].day + timedelta(1)
    kept, _, parked = store.judge(line, held, ready, shelf=scaled)
    if parked:
        raise ValueError(f"{line.symbol}: the one store would park it: {parked.reason}")
    have = {bar.day for bar in held}
    with bars.writing(path, source) as round_:
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
        OLDS = [p for p in FOUND if p.suffix == ".db" or _daily(p)]
        OLDS or sys.exit("headstart_days: the register tags no daily store IMPORT")
        for OLD in sorted(OLDS, key=lambda p: p.suffix != ".db"):  # the database first
            main(OLD, DATA / bars.LIVE, order(), datetime.now(UTC).date())
    except (OSError, ValueError, sqlite3.Error, bars.NoRound) as reason:
        sys.exit(f"headstart_days: {type(reason).__name__}: {reason}")
