"""headstart - THE OLD DESK'S STORES AS A HEAD START (the operator's ask of 14 November 2026).
The archive forgets a five-minute bar after sixty days; the old desk kept its own since
February 2026, read here once into the fast store. Its numbers are not trusted, so no bar
enters on the old desk's word:

- the line's own daily bar from the archive, cleaned by the one store, must vouch for it: the
  bar lies within that day's high and low, as far out as the store lets an open or a close
  sit (STRETCH). A day with no fresh daily bar vouches for nothing;
- a bar of a line priced in pounds that fits its day only as pence is read as pence; then the
  fast store's own checks: hours, prices that can be, a wrong unit;
- the store must already hold, from another source, bars for some of the same moments, at
  least half agreeing: else nothing proves the clock and the instrument, and none is kept.

What enters is kept under its source's name and only fills moments that hold no bar: a fresh
bar, held or arriving later, wins, and each bar that differs from one held is counted.

The old stores are read and never written, nor is anything written beside them: every store
the data register in the desk's notes tags IMPORT, read by its form (`python -m lab.headstart`,
into the two databases of the data folder). Six forms have a reader: the matrices of Stooq's
bars, the database mark_the_trend.db, the parquet folders of ibkr_store (UTC) and stooq_store,
mark_the_trend's Stooq files and the raw Stooq zips (Stooq's clock); any other is counted as having
none yet. A source held already is not read again. Indicators are not read at all.

A line the archive gives no history of (3LGO) takes its daily history from the matrices
(`python -m lab.headstart --daily 3LGO`): the database's daily bars must agree on the days both
hold, the days up to the archive's come from its five-minute bars, and all of it passes the
one store's checks with the archive's, else nothing is kept. It is shelved in the store."""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal
from functools import partial
from pathlib import Path

from desk import archive, bars, store
from desk.bars import EPOCH, Five, Source
from desk.compare import doubt
from desk.lines import LINES, Line
from desk.store import STRETCH, Bar, Refused
from lab.headstart_parts import (  # noqa: F401  # the readers, still reached as lab.headstart.<name>
    MARKET as MARKET,
)
from lab.headstart_parts import (
    PARQUET as PARQUET,
)
from lab.headstart_parts import (
    PENCE as PENCE,
)
from lab.headstart_parts import (
    TREND as TREND,
)
from lab.headstart_parts import (
    WARSAW as WARSAW,
)
from lab.headstart_parts import (
    _ahead as _ahead,
)
from lab.headstart_parts import (
    _named as _named,
)
from lab.headstart_parts import (
    _priced as _priced,
)
from lab.headstart_parts import (
    _stamped as _stamped,
)
from lab.headstart_parts import (
    asked as asked,
)
from lab.headstart_parts import (
    database as database,
)
from lab.headstart_parts import (
    matrices as matrices,
)
from lab.headstart_parts import (
    matrix_days as matrix_days,
)
from lab.headstart_parts import (
    parquet as parquet,
)
from lab.headstart_parts import (
    raw as raw,
)

DAYS = "SELECT ts, close FROM ohlcv WHERE ticker = ? AND timeframe = '1d'"
RAW = "*/5_*_txt*.zip"  #: where Stooq's five-minute zips lie: a dated folder each
_ADJUSTED = "that are the adjusted form of the store's as-traded bars: not taken"
IMPORT = "| IMPORT |"  #: how a row of the data register naming a store to read in begins


def bridge(fives: Iterable[Five], after: date, before: date) -> list[Bar]:
    """A daily bar for each day between two, of that day's five-minute bars: the first open,
    the highest high, the lowest low, the last close, the volumes."""
    days: dict[date, list[Five]] = {}
    for five in sorted(fives, key=lambda bar: bar.start):
        if after < five.start.date() < before:
            days.setdefault(five.start.date(), []).append(five)
    return [
        Bar(
            day,
            got[0].open,
            max(b.high for b in got),
            min(b.low for b in got),
            got[-1].close,
            sum(b.volume for b in got),
        )
        for day, got in days.items()
    ]


def daily(line: Line, data: Path, stores: tuple[Path, Path], day: date) -> str:
    """A line's daily history from the old desk's matrices and database (stores, in that order)
    into the daily store under data, ready to trade on day, and one line saying so. Refused,
    nothing kept, where the closes disagree on half the days both hold or the store parks it."""
    given = archive.fetch(line, day)
    if not given:
        raise ValueError(f"{line.symbol}: the archive gave no bar before {day} to join to")
    mine = matrix_days(line, stores[0])
    close = {bar.day: bar.close for bar in mine}
    got = asked(stores[1], DAYS, line.symbol + archive.SUFFIX[line.venue])
    theirs = [(date.fromisoformat(at[:10]), Decimal(str(c))) for at, c in got if c]
    met = [(d, c, close[d]) for d, c in theirs if d in close]
    differ = [d for d, c, kept in met if abs(c - kept) > bars.AGREE * kept]
    if (why := doubt(len(met), differ)) is not None:
        raise ValueError(f"{line.symbol}: {why}")
    fives = archive.fetch_five(line, datetime.combine(day, time(), UTC))
    older = [*mine, *bridge(fives, mine[-1].day, given[0].day)]
    store_ = data / "daily" / line.venue
    with tempfile.TemporaryDirectory() as scratch:
        store.shelve(Path(scratch), line, older)
        parked = store.prepare(Path(scratch), {line: given}, day)
    if parked:
        raise ValueError(f"{line.symbol}: the one store would park it: {parked[0].reason}")
    store.shelve(store_, line, older)
    store.prepare(store_, {line: given}, day)
    kept = store.read(store_, line.symbol)
    said = f"headstart: {line.symbol} daily: {len(kept)} bars from {kept[0].day}"
    return f"{said}; the database's closes agree on {len(met) - len(differ)} of {len(met)} days"


def _vouched(line: Line, bar: Five, day: Bar | None) -> Five | str:
    """The bar in the line's currency, if its day's fresh daily bar vouches for it; else why
    it does not."""
    if day is None:
        return "on a day with no fresh daily bar to vouch for them"
    low, high = day.low * (1 - STRETCH), day.high * (1 + STRETCH)
    for unit in (Decimal(1), PENCE) if line.currency in archive.PENCE else (Decimal(1),):
        if low <= bar.low * unit and bar.high * unit <= high:
            prices = (bar.open, bar.high, bar.low, bar.close)
            return Five(bar.start, *_priced(prices, unit), bar.volume)
    return "outside their day's fresh high and low"


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
    moments that hold none. A bar's day is its start's in UTC: both venues trade within one."""
    adopted: dict[Line, Adopted] = {}
    with bars.writing(path, source) as round_:
        for line, given in answers.items():
            if isinstance(given, Refused):
                adopted[line] = Adopted(0, 0, 0, (f"{source.value} gave nothing: {given.reason}",))
                continue
            days = {bar.day: bar for bar in daily.get(line, ())}
            judged = [_vouched(line, bar, days.get(bar.start.date())) for bar in given]
            sound = [bar for bar in judged if isinstance(bar, Five)]
            since = min((bar.start for bar in sound), default=EPOCH)
            kept, found = bars.checked(line, sound, round_.closes(line, since))
            unvouched = Counter(why for why in judged if isinstance(why, str))
            faults = [f"{count} bars {why}" for why, count in sorted(unvouched.items())] + found
            verdict = round_.compare(line, kept)
            if kept and (why := doubt(verdict.met, verdict.differ)):
                faults.append(why)
                kept = []
            raw = [bar for bar in kept if bar.start.date() not in verdict.factors]
            if len(raw) < len(kept):
                faults.append(f"{len(kept) - len(raw)} bars on days {_ADJUSTED}")
            adopted[line] = Adopted(
                round_.five(line, raw), verdict.met, len(verdict.differ), tuple(faults)
            )
    return adopted


def imports(register: Path) -> tuple[Path, ...]:
    """The old stores the register tags IMPORT: a row `| IMPORT |` and a path in backticks."""
    rows = register.read_text(encoding="utf-8").splitlines()
    tagged = [row for row in rows if row.startswith(IMPORT)]
    if not tagged or any(row.count("`") < 2 for row in tagged):
        raise ValueError(f"{register} tags no store IMPORT by its path: {tagged}")
    return tuple(Path(row.split("`")[1]) for row in tagged)


def reader(where: Path) -> tuple[Source, Callable[[Line, Path], tuple[Five, ...]]] | None:
    """An old store's source and how it is read, judged by its form: a database file, a
    folder of some line's matrices, parquet files or Stooq's zips. Any other store has no reader
    yet; one that is not there is refused: the register names it wrongly or its drive is away."""
    if not where.exists():
        raise FileNotFoundError(f"{where}: the register tags it IMPORT, and it is not there")
    if where.suffix == ".db":
        return Source.DATABASE, database
    if any((where / f"{_named(line)}_ts.npy").is_file() for line in LINES):
        return Source.MATRICES, matrices
    if any(where.glob(RAW)):
        return Source.STOOQ_RAW, raw
    if any(where.glob("*.5.parquet")):  # a file a line, mark_the_trend's
        return Source.TREND_STOOQ, partial(parquet, source=Source.TREND_STOOQ)
    if (where / "freq=5").is_dir():  # only ibkr_store keeps a fetch record beside its bars
        found = next((where / "freq=5").glob("*/*/fetch.json"), None)
        source = Source.IBKR_STORE if found else Source.STOOQ_STORE
        return source, partial(parquet, source=source)
    return None


def held(path: Path, source: Source) -> bool:
    """The store at path holds five-minute bars from source already. An old store lands in
    one round, whole or not at all, so one that is held is in, and is not read again."""
    for line in LINES if path.is_file() else ():
        with suppress(LookupError):  # the store never held this line's five-minute bars
            if source in bars.sources(path, line, bars.FIVE):
                return True
    return False


def fresh(path: Path, day: date) -> dict[Line, tuple[Bar, ...]]:
    """The archive's five-minute bars up to day into the store at path, for the old bars to be
    met with, and every line's fresh daily bars before day, cleaned by the one store, to vouch
    for them. An archive giving no line's bars of either span proves nothing: refused."""
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
    """The register's IMPORT stores to read, in the order of Source, each a clock's proof for the
    next; those whose source is held already; those with no reader. A second store of one form
    is refused: it would be skipped."""
    todo: list[Reader] = []
    skipped, unread = list[str](), list[str]()
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
    """Every old store the register tags IMPORT into the fast store at path, met with the
    archive's five-minute bars up to day (which enter first) and vouched for by its daily bars
    before day; one held already is skipped. Each line's fate is said, then one line of counts."""
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
    left = f"{len(unread)} with no reader yet ({', '.join(unread) or 'none'})"
    bars_in = f"bars filled {totals['filled']}, met {totals['met']}, differ {totals['differ']}"
    said = f"headstart: {len(todo)} old stores read, {len(skipped)} already in, {left}; {bars_in}"
    sys.stdout.write(said + "\n")
    return said


def olds(register: Path, line: Line) -> tuple[Path, Path]:
    """The register's IMPORT stores that hold a line's daily matrices, and its database."""
    found = imports(register)
    folder = next((p for p in found if (p / f"{_named(line, '1d')}_ts.npy").is_file()), None)
    old = next((p for p in found if p.suffix == ".db"), None)
    if folder is None or old is None:
        raise ValueError(f"{register}: IMPORT tags no daily matrices of {line.symbol} or database")
    return folder, old


if __name__ == "__main__":
    DATA = Path(os.environ.get("KESTREL2_DATA") or sys.exit("headstart: KESTREL2_DATA is unset"))
    REGISTER, TODAY = DATA.parent / "kestrel2_notes" / "data_register.md", datetime.now(UTC).date()
    try:
        if sys.argv[1:2] == ["--daily"] and len(sys.argv) == 3:
            ONE = next((x for x in LINES if x.symbol == sys.argv[2]), None)
            ONE = ONE or sys.exit(f"headstart: {sys.argv[2]} is no line of the desk")
            sys.stdout.write(daily(ONE, DATA, olds(REGISTER, ONE), TODAY) + "\n")
        else:
            main(REGISTER, DATA / bars.LIVE, TODAY)
    except (OSError, ValueError, sqlite3.Error, bars.NoRound) as reason:  # the one line, then out
        sys.exit(f"headstart: {type(reason).__name__}: {reason}")
