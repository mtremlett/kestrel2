"""headstart_parts - THE READERS OF THE HEAD START: how each old store of five-minute bars (and the
matrices' daily bars) is read into typed bars, read-only. What enters is judged in headstart.py."""

from __future__ import annotations

import math
import sqlite3
import zipfile
from collections.abc import Iterable
from contextlib import closing
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq  # type: ignore[import-untyped]  # ships no stubs

from desk import archive, venues
from desk.bars import EPOCH, Five, Source
from desk.lines import Line
from desk.store import Bar

MARKET = {"LSE": "UK", "US": "US"}  #: the matrices' name for a line is its symbol and this
#: Stooq stamps a bar's start on Warsaw's clock, kept in the matrices as if UTC (14 November
#: 2026: SPY's bars agreed with the archive's two hours earlier, in summer): London's and an hour.
WARSAW, PENCE = timedelta(hours=1), Decimal("0.01")
BARS = "SELECT ts, open, high, low, close, volume FROM ohlcv WHERE ticker = ? AND timeframe = '5m'"
PARQUET = ("ts", "open", "high", "low", "close", "volume")
TREND = ("DATE", "Open", "High", "Low", "Close", "Volume")  #: mark_the_trend's columns


def _named(line: Line, span: str = "5m") -> str:
    """The matrices' name for a line's bars of a span."""
    return f"{line.symbol}.{MARKET[line.venue]}_{span}"


def matrices(line: Line, folder: Path) -> tuple[Five, ...]:
    """A line's five-minute bars from the old desk's matrices in folder: an array of moments and
    one of opens, highs, lows, closes and volumes. A moment without five numbers has no bar."""
    name = _named(line)
    stamps = np.load(folder / f"{name}_ts.npy").tolist()
    rows = zip(stamps, np.load(folder / f"{name}_ohlcv.npy").T, strict=True)
    return _stamped(((EPOCH + timedelta(milliseconds=at), *row) for at, row in rows), True)


def _ahead(wall: datetime) -> timedelta:
    """How far Stooq's clock is ahead of UTC at wall."""
    return WARSAW + venues.zone("LSE", wall.date()).utcoffset(None)


def _stamped(rows: Iterable[tuple[Any, ...]], stooq: bool) -> tuple[Five, ...]:
    """Bars from rows of stamp, prices and volume, the stamp on Stooq's clock or UTC; a row
    with a hole or a number that is none is dropped."""
    return tuple(
        Five(at.replace(tzinfo=UTC) - _ahead(at) * stooq, *_priced(prices, Decimal(1)), int(volume))
        for at, *prices, volume in rows
        if None not in (at, *prices, volume) and all(math.isfinite(x) for x in (*prices, volume))
    )


def parquet(line: Line, folder: Path, source: Source) -> tuple[Five, ...]:
    """A line's bars from a parquet store of this source: ibkr_store and stooq_store keep
    freq=5/market=../ticker=../part.parquet, mark_the_trend <symbol>.5.parquet (<symbol>.L.5
    in London). Stamps are UTC in ibkr_store, Stooq's clock elsewhere. None held is refused."""
    market = MARKET[line.venue]
    file = folder / f"freq=5/market={market.lower()}/ticker={line.symbol}.{market}/part.parquet"
    columns = PARQUET
    if source is Source.TREND_STOOQ:
        file, columns = folder / f"{line.symbol}{archive.SUFFIX[line.venue]}.5.parquet", TREND
    if not file.is_file():
        raise ValueError(f"{file.parent.name} holds no five-minute bar of {line.symbol}")
    table = pq.ParquetFile(file).read(columns=list(columns))
    rows = zip(*(table[column].to_pylist() for column in columns), strict=True)
    return _stamped(rows, source is not Source.IBKR_STORE)


def raw(line: Line, folder: Path) -> tuple[Five, ...]:
    """A line's bars from the newest dated folder of Stooq's raw zips under folder: its one text
    file (<symbol>.uk.txt), rows of ticker, span, date, time, prices, volume, open interest."""
    market = MARKET[line.venue].lower()
    zips = sorted(folder.glob(f"*/5_{market}_txt*.zip"))
    if not zips:
        raise ValueError(f"{folder.name} holds no zip of {market} five-minute bars")
    with zipfile.ZipFile(zips[-1]) as opened:
        found = [m for m in opened.namelist() if m.endswith(f"/{line.symbol.lower()}.{market}.txt")]
        if len(found) != 1:
            raise ValueError(f"{zips[-1].name} holds {len(found)} files of {line.symbol}, not one")
        cells = [row.split(",") for row in opened.read(found[0]).decode().splitlines()[1:]]
    return _stamped(
        ((datetime.strptime(c[2] + c[3], "%Y%m%d%H%M%S"), *map(float, c[4:9])) for c in cells), True
    )


def asked(path: Path, ask: str, ticker: str) -> list[tuple[Any, ...]]:
    """What the old desk's database at path answers to a question about one ticker, opened
    read-only: nothing is written to it or beside it, and one not there is not made. One whose
    log still holds changes is being written, and is refused."""
    log = path.with_name(f"{path.name}-wal")
    if log.exists() and log.stat().st_size:
        raise ValueError(f"{path.name} is still being written: its log holds changes")
    with closing(sqlite3.connect(f"{path.as_uri()}?mode=ro&immutable=1", uri=True)) as old:
        return old.execute(ask, (ticker,)).fetchall()


def database(line: Line, path: Path) -> tuple[Five, ...]:
    """A line's five-minute bars from the old desk's database at path, which names a line as
    the archive does and stamps a bar with the moment it starts, in UTC. A line it holds no
    bar of is refused."""
    ticker = line.symbol + archive.SUFFIX[line.venue]
    rows = asked(path, BARS, ticker)
    if not rows:
        raise ValueError(f"{path.name} holds no five-minute bar of {ticker}")
    return _stamped(((datetime.fromisoformat(at), *rest) for at, *rest in rows), False)


def matrix_days(line: Line, folder: Path) -> tuple[Bar, ...]:
    """A line's daily bars from the old desk's matrices in folder, a day stamped as itself. A
    line quoted in pounds is read as pence, which the junction with the archive's proves."""
    name = _named(line, "1d")
    stamps = np.load(folder / f"{name}_ts.npy").tolist()
    unit = PENCE if line.currency in archive.PENCE else Decimal(1)
    return tuple(
        Bar((EPOCH + timedelta(milliseconds=stamp)).date(), *_priced(row[:4], unit), int(row[4]))
        for stamp, row in zip(stamps, np.load(folder / f"{name}_ohlcv.npy").T, strict=True)
        if np.isfinite(row).all()
    )


def _priced(prices: Iterable[object], unit: Decimal) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """A bar's open, high, low and close as exact decimals, in the line's currency."""
    open_, high, low, close = (Decimal(str(price)) * unit for price in prices)
    return open_, high, low, close
