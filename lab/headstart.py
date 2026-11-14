"""headstart - THE OLD DESK'S STORES AS A HEAD START (the operator's ask of 14 November 2026).
The free archive forgets a five-minute bar after sixty days; the old desk kept its own since
February 2026, and they are read here, once, into the one fast store. Its numbers are not
trusted, so no bar enters on the old desk's word:

- the line's own daily bar from the archive, cleaned by the one store, must vouch for it: the
  bar lies within that day's high and low, as far out as the store lets an open or a close
  sit (STRETCH). A day with no fresh daily bar vouches for nothing;
- a bar of a line priced in pounds that fits its day only as pence is read as pence, for the
  old stores quote some of London so and say nowhere which; no other unit is tried;
- then the fast store's own checks: trading hours, prices that can be, a wrong unit;
- the store must already hold, from another source, bars for some of the same moments, and
  at least half of those must agree: else nothing proves the line's bars are on the right
  clock and of the right instrument, and none is kept.

What enters is kept under its source's name and only fills moments that hold no bar: a fresh
bar, held already or arriving later, wins, and each bar that differs from one held is counted.

The old stores are read and never written, nor is anything written beside them. They were
two: per-line matrices of Stooq's bars, and the database mark_the_trend.db. Its parquet
folders (Stooq, IBKR) need a reader the desk does not have (docs/STATUS.md). Its indicators
are not read at all."""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import numpy as np

from desk import archive, bars, store, venues
from desk.bars import EPOCH, Five, Source
from desk.lines import LINES, Line
from desk.store import STRETCH, Bar, Refused

MARKET = {"LSE": "UK", "US": "US"}  #: the matrices' name for a line is its symbol and this
#: Stooq stamps a bar with the moment it starts on Warsaw's clock, and the matrices kept that
#: as if it were UTC (seen 14 November 2026: of SPY's bars 1 in 1,512 agreed with the
#: archive's for the same moment as stamped, and 2,170 in 2,184 two hours earlier, in
#: summer). Warsaw's clock is London's and an hour, summer and winter.
WARSAW = timedelta(hours=1)
PENCE = Decimal("0.01")
BARS = "SELECT ts, open, high, low, close, volume FROM ohlcv WHERE ticker = ? AND timeframe = '5m'"
NO_DAY = "on a day with no fresh daily bar to vouch for them"
OUTSIDE = "outside their day's fresh high and low"


def matrices(line: Line, folder: Path) -> tuple[Five, ...]:
    """A line's five-minute bars from the old desk's matrices in folder: one array of moments
    and one of opens, highs, lows, closes and volumes. A moment without a bar of five
    numbers has none."""
    name = f"{line.symbol}.{MARKET[line.venue]}_5m"
    stamps = np.load(folder / f"{name}_ts.npy").tolist()
    made = []
    for stamp, row in zip(stamps, np.load(folder / f"{name}_ohlcv.npy").T, strict=True):
        if not np.isfinite(row).all():
            continue
        wall = EPOCH + timedelta(milliseconds=stamp)
        ahead = WARSAW + venues.zone("LSE", wall.date()).utcoffset(None)
        made.append(Five(wall - ahead, *_priced(row[:4], Decimal(1)), int(row[4])))
    return tuple(made)


def database(line: Line, path: Path) -> tuple[Five, ...]:
    """A line's five-minute bars from the old desk's database at path, which names a line as
    the archive does and stamps a bar with the moment it starts, in UTC. It is opened
    read-only, as a file nobody writes any more: nothing is written to it or beside it, and
    one that is not there is not made. One whose log still holds changes is being written,
    and is refused; so is a line it holds no bar of."""
    ticker, log = line.symbol + archive.SUFFIX[line.venue], path.with_name(f"{path.name}-wal")
    if log.exists() and log.stat().st_size:
        raise ValueError(f"{path.name} is still being written: its log holds changes")
    with closing(sqlite3.connect(f"{path.as_uri()}?mode=ro&immutable=1", uri=True)) as old:
        rows = old.execute(BARS, (ticker,)).fetchall()
    if not rows:
        raise ValueError(f"{path.name} holds no five-minute bar of {ticker}")
    whole = (row for row in rows if None not in row)
    return tuple(
        Five(datetime.fromisoformat(at), *_priced(prices, Decimal(1)), int(volume))
        for at, *prices, volume in whole
    )


def _priced(prices: Iterable[object], unit: Decimal) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """A bar's open, high, low and close as exact decimals, in the line's currency."""
    open_, high, low, close = (Decimal(str(price)) * unit for price in prices)
    return open_, high, low, close


def _vouched(line: Line, bar: Five, day: Bar | None) -> Five | str:
    """The bar in the line's currency, if its day's fresh daily bar vouches for it; else why
    it does not."""
    if day is None:
        return NO_DAY
    low, high = day.low * (1 - STRETCH), day.high * (1 + STRETCH)
    for unit in (Decimal(1), PENCE) if line.currency in archive.PENCE else (Decimal(1),):
        if low <= bar.low * unit and bar.high * unit <= high:
            prices = (bar.open, bar.high, bar.low, bar.close)
            return Five(bar.start, *_priced(prices, unit), bar.volume)
    return OUTSIDE


def _doubt(met: int, differ: int) -> str | None:
    """Why a line's bars that passed every check are still not kept, if they are not."""
    if not met:
        return "no bar is held for any of their moments to prove their clock; none kept"
    if differ * 2 > met:
        held = f"{differ} of the {met} bars already held for the same moments differ"
        return f"{held}: another clock or another instrument; none kept"
    return None


@dataclass(frozen=True)
class Adopted:
    """What became of one line's bars from an old store."""

    filled: int  #: bars that entered: each passed every check, on a moment that held none
    met: int  #: bars that passed, on a moment the store already held from another source
    differ: int  #: of those met, the ones that differ from the bar held, which stays
    faults: tuple[str, ...]  #: why the others did not enter


def adopt(
    path: Path,
    source: Source,
    answers: Mapping[Line, Iterable[Five] | Refused],
    daily: Mapping[Line, Sequence[Bar]],
) -> dict[Line, Adopted]:
    """An old store's bars into the fast store at path under its source's name, in one round:
    for each line the bars its fresh daily bars vouch for and the store's checks pass, on the
    moments that hold none. A line the old store could not be read for adds nothing. A bar's
    day is its start's in UTC: London and New York both trade within one UTC day."""
    adopted: dict[Line, Adopted] = {}
    with bars.writing(path, source) as round_:
        for line, given in answers.items():
            if isinstance(given, Refused):
                nothing = f"{source.value} gave nothing: {given.reason}"
                adopted[line] = Adopted(0, 0, 0, (nothing,))
                continue
            days = {bar.day: bar for bar in daily.get(line, ())}
            judged = [_vouched(line, bar, days.get(bar.start.date())) for bar in given]
            sound = [bar for bar in judged if isinstance(bar, Five)]
            since = min((bar.start for bar in sound), default=EPOCH)
            kept, found = bars.checked(line, sound, round_.closes(line, since))
            unvouched = Counter(why for why in judged if isinstance(why, str))
            faults = [f"{count} bars {why}" for why, count in sorted(unvouched.items())] + found
            met, differ = round_.apart(line, kept)
            doubt = _doubt(met, differ) if kept else None
            if doubt:
                faults.append(doubt)
                kept = []
            adopted[line] = Adopted(round_.five(line, kept), met, differ, tuple(faults))
    return adopted


def main(old_matrices: Path, old_database: Path, path: Path, day: date) -> None:
    """Both old stores into the fast store at path, the matrices first, each line's bars
    vouched for by the archive's daily bars before day; what became of each line is said."""
    with tempfile.TemporaryDirectory() as scratch:
        store.prepare(Path(scratch), archive.gather(LINES, day, archive.fetch), day)
        daily = {line: store.read(Path(scratch), line.symbol) for line in LINES}
    for source, where, read in (
        (Source.MATRICES, old_matrices, matrices),
        (Source.DATABASE, old_database, database),
    ):
        for line, got in adopt(path, source, archive.gather(LINES, where, read), daily).items():
            counts = f"filled {got.filled}, met {got.met}, differ {got.differ}"
            more = [f"and {len(got.faults) - 4} more"] * (len(got.faults) > 4)
            faults = "; ".join([*got.faults[:4], *more])
            sys.stdout.write(f"{source.value}: {line.symbol}: {counts}; {faults}\n")


if __name__ == "__main__":
    main(
        Path(sys.argv[1]),
        Path(sys.argv[2]),
        Path(os.environ["KESTREL2_DATA"]) / "bars.db",
        datetime.now(UTC).date(),
    )
