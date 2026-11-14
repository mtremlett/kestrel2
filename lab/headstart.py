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

The old stores are read and never written, nor is anything written beside them. Which they
are, the data register in the desk's notes says: every store it tags IMPORT, read by its form
(`python -m lab.headstart`, into market.db in the data folder). Two forms have a reader: the
per-line matrices of Stooq's bars, and the database mark_the_trend.db; any other is counted
as having none yet: parquet folders for want of a parquet library, raw Stooq zips for want of
a Source to keep them under. A store whose source the store
holds already is not read again. Its indicators are not read at all."""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
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
IMPORT = "| IMPORT |"  #: how a row of the data register naming a store to read in begins


def _named(line: Line) -> str:
    """The matrices' name for a line's five-minute bars."""
    return f"{line.symbol}.{MARKET[line.venue]}_5m"


def matrices(line: Line, folder: Path) -> tuple[Five, ...]:
    """A line's five-minute bars from the old desk's matrices in folder: one array of moments
    and one of opens, highs, lows, closes and volumes. A moment without a bar of five
    numbers has none."""
    name = _named(line)
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


def imports(register: Path) -> tuple[Path, ...]:
    """The old stores the data register tags IMPORT, in its order: such a row begins
    `| IMPORT |` and names its store's path between the first two backticks."""
    rows = register.read_text(encoding="utf-8").splitlines()
    tagged = [row for row in rows if row.startswith(IMPORT)]
    unnamed = [row for row in tagged if row.count("`") < 2]
    if unnamed or not tagged:
        raise ValueError(f"{register} tags no store IMPORT by its path: {unnamed}")
    return tuple(Path(row.split("`")[1]) for row in tagged)


def reader(where: Path) -> tuple[Source, Callable[[Line, Path], tuple[Five, ...]]] | None:
    """An old store's source and how it is read, judged by its form: a database file, or a
    folder holding some line's matrices. Any other store has no reader yet; one that is not
    there is refused, for the register names it wrongly or its drive is away."""
    if not where.exists():
        raise FileNotFoundError(f"{where}: the register tags it IMPORT, and it is not there")
    if where.suffix == ".db":
        return Source.DATABASE, database
    if any((where / f"{_named(line)}_ts.npy").is_file() for line in LINES):
        return Source.MATRICES, matrices
    return None


def held(path: Path, source: Source) -> bool:
    """The store at path holds five-minute bars from source already. An old store lands in
    one round, whole or not at all, so one that is held is in, and is not read again."""
    if not path.is_file():
        return False
    for line in LINES:
        try:
            if source in bars.sources(path, line, bars.FIVE):
                return True
        except LookupError:  # the store never held this line's five-minute bars: none of source
            continue
    return False


def fresh(path: Path, day: date) -> dict[Line, tuple[Bar, ...]]:
    """The archive's five-minute bars up to day into the store at path, for the old bars to be
    met with, and every line's fresh daily bars before day, cleaned by the one store, to vouch
    for them. An archive that gives no line's bars of either span proves nothing: refused."""
    fives = archive.gather(LINES, datetime.combine(day, time(), UTC), archive.fetch_five)
    answers = archive.gather(LINES, day, archive.fetch)
    for span, given in ("five-minute", fives), ("daily", answers):
        if all(isinstance(answer, Refused) for answer in given.values()):
            raise ValueError(f"the archive gave no line's {span} bars before {day}: none proves")
    bars.keep(path, fives)
    with tempfile.TemporaryDirectory() as scratch:
        store.prepare(Path(scratch), answers, day)
        return {line: store.read(Path(scratch), line.symbol) for line in LINES}


Reader = tuple[Path, Source, Callable[[Line, Path], tuple[Five, ...]]]


def planned(register: Path, path: Path) -> tuple[list[Reader], list[str], list[str]]:
    """The register's IMPORT stores to read, newest first (the order of Source), each a clock's
    proof for the next; those whose source the store holds already; those with no reader. A
    source is one store, so two stores of one form are refused: the second would be skipped."""
    todo: list[Reader] = []
    skipped: list[str] = []
    unread: list[str] = []
    for where in imports(register):
        how = reader(where)
        if how is None:
            unread.append(where.name)
        elif any(how[0] is source for _, source, _ in todo) or how[0].value in skipped:
            raise ValueError(f"{where}: a second store of the form of {how[0].value}")
        elif held(path, how[0]):
            skipped.append(how[0].value)
        else:
            todo.append((where, *how))
    return sorted(todo, key=lambda one: list(Source).index(one[1])), skipped, unread


def main(register: Path, path: Path, day: date) -> str:
    """Every old store the register tags IMPORT into the fast store at path, its bars met
    with the archive's five-minute bars up to day, which enter first, and vouched for by its
    daily bars before day. A store whose source is held already is skipped, so a run cut
    short is simply run again. What became of each line is said, then one line of counts,
    which is returned."""
    todo, skipped, unread = planned(register, path)
    daily = fresh(path, day) if todo else {}
    totals = Counter[str]()
    for where, source, read in todo:
        for line, got in adopt(path, source, archive.gather(LINES, where, read), daily).items():
            counts = f"filled {got.filled}, met {got.met}, differ {got.differ}"
            more = [f"and {len(got.faults) - 4} more"] * (len(got.faults) > 4)
            faults = "; ".join([*got.faults[:4], *more])
            sys.stdout.write(f"{source.value}: {line.symbol}: {counts}; {faults}\n")
            totals.update(filled=got.filled, met=got.met, differ=got.differ)
    read_in = f"{len(todo)} old stores read, {len(skipped)} already in"
    left = f"{len(unread)} with no reader yet ({', '.join(unread) or 'none'})"
    bars_in = f"bars filled {totals['filled']}, met {totals['met']}, differ {totals['differ']}"
    said = f"headstart: {read_in}, {left}; {bars_in}"
    sys.stdout.write(said + "\n")
    return said


if __name__ == "__main__":
    if not os.environ.get("KESTREL2_DATA"):
        sys.exit("headstart: KESTREL2_DATA names no data folder, so the store has no home")
    DATA = Path(os.environ["KESTREL2_DATA"])
    try:
        main(
            DATA.parent / "kestrel2_notes" / "data_register.md",
            DATA / "market.db",
            datetime.now(UTC).date(),
        )
    except (OSError, ValueError, sqlite3.Error, bars.NoRound) as reason:  # the one line, then out
        sys.exit(f"headstart: {type(reason).__name__}: {reason}")
