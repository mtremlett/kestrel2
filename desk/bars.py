"""bars - THE ONE FAST STORE, for hot and deep bars alike: one SQLite file in WAL mode, the
standard library's own, with one writer at a time and many readers (the operator's need of 13
November 2026, DAT-04). It is held to three benchmarks, in tests/unit/test_bars.py: a
five-minute round for every line written in under a second, a line's last week read in under
50 ms, a line's daily history read in under 200 ms.

A writer works in rounds. Everything written in a round lands together when the round ends,
forced to disk, or none of it does. A reader reads the last whole round while the next is
being written, and never part of one. A second writer waits its turn, and is refused if it
has not come within WAIT seconds (NoRound).

A line is its venue and its symbol: one symbol can be two companies. A daily bar is named by
its session's day; a five-minute bar by the moment it starts, in UTC. Prices are kept as the
exact decimals they were written as.

Five-minute bars are kept for good (DAT-11): the free archive forgets them after sixty days,
so `keep` saves each evening's through the checks the daily store makes. No moment's bar is
ever removed; one the archive restates takes the place of the one held only by passing those
checks, its unit judged against what is held. The last week stays hot with every older bar
archived beneath it in the same file: the benchmark reads a week from under a year of them,
for twenty lines.

Every bar is kept with its source, and a round is one source's (Source). A fresh source,
the archive, restates: its bar for a moment takes the place of whatever is held there. Any
other source, a store that is no longer kept, only fills the moments that hold no bar, so a
fresh bar always wins; where two sources' bars for one moment differ, that is counted
(`apart`)."""

from __future__ import annotations

import sqlite3
from collections.abc import Collection, Iterable, Iterator, Mapping, Sequence
from contextlib import closing, contextmanager
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from statistics import median_low
from typing import Any

from desk import venues
from desk.lines import Line
from desk.store import FAR, JUMP, STRETCH, Bar, Refused

DAILY, FIVE = "daily", "five-minute"  #: the two spans of bar the store holds
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
#: The seconds anyone waits for the file: a writer for the writer before it, and anyone while
#: SQLite opens or closes the file's log as the first comes to it or the last goes.
WAIT = 5.0
#: Two sources' bars for one moment agree when no price of the four is further from the
#: price held than this part of the price given: each vendor rounds its own way. Volumes are
#: not set side by side, for each vendor counts the trades of its own set of venues.
AGREE = Decimal("0.0001")


class Source(Enum):
    """Where a bar came from: a bar from anywhere else cannot be written."""

    ARCHIVE = "archive"  #: the free price archive; until 14 November 2026 the one source
    MATRICES = "old desk: Stooq matrices"  #: the old desk's two stores (lab/headstart.py)
    DATABASE = "old desk: mark_the_trend.db"

    @property
    def fresh(self) -> bool:
        """It is still asked, and so may restate a bar; an old store only fills."""
        return self is Source.ARCHIVE


#: Each bar under its line, its span and the start of its span: a daily bar's day as its
#: ordinal, a five-minute bar's start as seconds since EPOCH. `held` names every line and
#: span ever written, so that a line never written is not read as a line with no bars.
SCHEMA = (
    "CREATE TABLE IF NOT EXISTS bar (venue TEXT NOT NULL, symbol TEXT NOT NULL,"
    " span TEXT NOT NULL, at INTEGER NOT NULL, open TEXT NOT NULL, high TEXT NOT NULL,"
    " low TEXT NOT NULL, close TEXT NOT NULL, volume INTEGER NOT NULL,"
    " source TEXT NOT NULL, PRIMARY KEY (venue, symbol, span, at)) WITHOUT ROWID",
    "CREATE TABLE IF NOT EXISTS held (venue TEXT NOT NULL, symbol TEXT NOT NULL,"
    " span TEXT NOT NULL, PRIMARY KEY (venue, symbol, span)) WITHOUT ROWID",
)
#: A store made before sources were kept: every bar in it came from the archive.
SOURCED = f"ALTER TABLE bar ADD COLUMN source TEXT NOT NULL DEFAULT '{Source.ARCHIVE.value}'"
MADE = "SELECT 1 FROM sqlite_master WHERE name = 'held'"
HOLD = "INSERT OR IGNORE INTO held VALUES (?, ?, ?)"
HELD = "SELECT 1 FROM held WHERE venue = ? AND symbol = ? AND span = ?"
CLEAR = "DELETE FROM bar WHERE venue = ? AND symbol = ? AND span = ?"
ADD = "INSERT INTO bar VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
PUT, FILL = (ADD.replace("INSERT", f"INSERT OR {then}") for then in ("REPLACE", "IGNORE"))
OTHERS = (
    "SELECT at, open, high, low, close FROM bar WHERE venue = ? AND symbol = ? AND span = ?"
    " AND source != ? AND at >= ? AND at <= ?"
)
SOURCES = (
    "SELECT source, count(*) FROM bar"
    " WHERE venue = ? AND symbol = ? AND span = ? AND at >= ? AND at < ? GROUP BY source"
)
CLOSES = "SELECT close FROM bar WHERE venue = ? AND symbol = ? AND span = ? AND at >= ?"
READ = (
    "SELECT at, open, high, low, close, volume FROM bar"
    " WHERE venue = ? AND symbol = ? AND span = ? AND at >= ? AND at < ? ORDER BY at"
)


class NoRound(RuntimeError):
    """No round was begun, or the round is lost, for SQLite's own reason: "database is
    locked" is a store that stayed in another's hands for WAIT seconds."""


def _seconds(moment: datetime) -> int:
    """The first whole second since EPOCH at or after a moment in UTC, so that a bar starts
    at or after a moment exactly when its second does. A moment in no zone, or at any
    distance from UTC, is refused."""
    if moment.utcoffset() != timedelta(0):
        raise ValueError(f"{moment!r} is not a moment in UTC")
    return -((EPOCH - moment) // timedelta(seconds=1))


@dataclass(frozen=True)
class Five:
    """A five-minute bar, named by the moment it starts."""

    start: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    def __post_init__(self) -> None:
        if _seconds(self.start) % 300 or self.start.microsecond:
            raise ValueError(f"{self.start!r} is not a five-minute mark in UTC")


class Round:
    """One round of a writer, open: what it is given lands when the round ends, each bar
    kept with the round's one source."""

    def __init__(self, held: sqlite3.Connection, source: Source) -> None:
        self._held, self._source = held, source

    def _write(
        self, put: str, line: Line, span: str, bars: Iterable[tuple[int, Bar | Five]]
    ) -> int:
        """One line's bars of one span, all of them or, if any is refused, none: the round is
        then as it was before, whether or not the caller ends it there. A round that SQLite
        itself has dropped (a full disk) takes no more, and nothing of it lands. It says how
        many bars landed."""
        if not self._held.in_transaction:
            raise NoRound(f"SQLite dropped this round: nothing of it lands, {line.symbol} too")
        key = (line.venue, line.symbol, span)
        rows = (
            (*key, at, *map(str, (b.open, b.high, b.low, b.close)), b.volume, self._source.value)
            for at, b in bars
        )
        self._held.execute("SAVEPOINT line")
        try:
            self._held.execute(HOLD, key)
            if put == ADD:
                self._held.execute(CLEAR, key)
            landed = self._held.executemany(put, rows).rowcount
        except BaseException:
            if self._held.in_transaction:
                self._held.execute("ROLLBACK TO line")
            raise
        self._held.execute("RELEASE line")
        return landed

    def daily(self, line: Line, bars: Iterable[Bar]) -> None:
        """A line's daily history, whole: it takes the place of the history held before, for
        an archive restates the past, so only a fresh source may give one. A history that
        gives a day twice is refused."""
        if not self._source.fresh:
            raise ValueError(f"{self._source.value} is no fresh source: it restates no history")
        try:
            self._write(ADD, line, DAILY, ((b.day.toordinal(), b) for b in bars))
        except sqlite3.IntegrityError as twice:
            what = f"{line.symbol} on {line.venue}: its history gives a day twice; none kept"
            raise ValueError(what) from twice

    def five(self, line: Line, bars: Iterable[Five]) -> int:
        """More of a line's five-minute bars, and how many landed. They only gather: from a
        fresh source a bar given again for a moment takes the place of the one held for it;
        from any other a bar lands only on a moment that holds none. No other bar is touched."""
        put = PUT if self._source.fresh else FILL
        return self._write(put, line, FIVE, ((_seconds(b.start), b) for b in bars))

    def apart(self, line: Line, bars: Collection[Five]) -> tuple[int, int]:
        """How many of the bars meet a bar held from another source for their own moment, and
        how many of those differ from it."""
        given = {_seconds(bar.start): bar for bar in bars}
        key = (line.venue, line.symbol, FIVE, self._source.value, min(given, default=0))
        met = differ = 0
        for at, *held in self._held.execute(OTHERS, (*key, max(given, default=0))):
            if at in given:
                bar = given[at]
                prices = zip(held, (bar.open, bar.high, bar.low, bar.close), strict=True)
                differ += any(abs(Decimal(was) - now) > AGREE * now for was, now in prices)
                met += 1
        return met, differ

    def closes(self, line: Line, since: datetime) -> list[Decimal]:
        """The closes of the line's five-minute bars held from since on, this round's too."""
        key = (line.venue, line.symbol, FIVE, _seconds(since))
        return [Decimal(close) for (close,) in self._held.execute(CLOSES, key)]


@contextmanager
def writing(path: Path, source: Source) -> Iterator[Round]:
    """A source's next round on the store at path, which is made on its first round. The
    round lands whole as the block ends; if the block fails, nothing of it lands."""
    with closing(sqlite3.connect(path, timeout=WAIT, isolation_level=None)) as held:
        try:
            held.execute("PRAGMA journal_mode = WAL")
            held.execute("PRAGMA synchronous = FULL")
            held.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError as refusal:
            raise NoRound(f"{path}: no round begun: {refusal}") from refusal
        with held:
            for table in SCHEMA:
                held.execute(table)
            if all(column[1] != "source" for column in held.execute("PRAGMA table_info(bar)")):
                held.execute(SOURCED)
            yield Round(held, source)


def _read(
    path: Path, line: Line, span: str, first: int, end: int, what: str = READ
) -> list[tuple[Any, ...]]:
    """A line's rows of one span from first up to, not including, end, oldest first, read
    at one moment of the store: its last whole round."""
    key = (line.venue, line.symbol, span)
    if not path.is_file():
        raise FileNotFoundError(f"{path}: no store has been written there")
    with closing(sqlite3.connect(path, timeout=WAIT, isolation_level=None)) as held:
        held.execute("BEGIN")
        if held.execute(MADE).fetchone() is None:
            raise FileNotFoundError(f"{path}: no round of the store has landed there")
        rows: list[tuple[Any, ...]] = held.execute(what, (*key, first, end)).fetchall()
        if not rows and held.execute(HELD, key).fetchone() is None:
            raise LookupError(
                f"{path}: the store never held {span} bars for {line.symbol} on {line.venue}"
            )
    return rows


def daily(path: Path, line: Line) -> tuple[Bar, ...]:
    """A line's whole daily history, oldest first."""
    rows = _read(path, line, DAILY, 0, date.max.toordinal() + 1)
    return tuple(
        Bar(date.fromordinal(at), Decimal(o), Decimal(h), Decimal(lo), Decimal(c), volume)
        for at, o, h, lo, c, volume in rows
    )


def five(path: Path, line: Line, since: datetime, until: datetime) -> tuple[Five, ...]:
    """A line's five-minute bars starting from since up to, not including, until, oldest
    first: its last week is the seven days up to now."""
    rows = _read(path, line, FIVE, _seconds(since), _seconds(until))
    return tuple(
        Five(EPOCH + timedelta(seconds=at), Decimal(o), Decimal(h), Decimal(lo), Decimal(c), v)
        for at, o, h, lo, c, v in rows
    )


def sources(path: Path, line: Line, span: str) -> dict[Source, int]:
    """How many of a line's bars of one span the store holds from each source."""
    return {Source(name): count for name, count in _read(path, line, span, 0, 2**62, SOURCES)}


def _entered(line: Line, bar: Five) -> Five | str:
    """The bar as it enters the store, or why it cannot be true on its own: the daily store's
    checks, made at five minutes. A bar belongs to a session's continuous trading: one that
    starts before the open, or at the close or after it, is no bar of that session."""
    prices, at = (bar.open, bar.high, bar.low, bar.close), f"{bar.start:%Y-%m-%d %H:%M}"
    known = bar.start.year in venues.KNOWN
    session = venues.open_at(line.venue, bar.start) if known else None
    if bar.start.date() in line.suspended:
        return f"{at} has a bar, yet {line.symbol} records the day as suspended"
    if session is None or bar.start >= session.close:
        return f"{at} is outside the trading hours of the {line.venue} calendar"
    if not all(p.is_finite() and p > 0 for p in prices) or bar.volume < 0:
        return f"{at} has a price or volume that cannot be"
    ends = (bar.open, bar.close)
    reach = (bar.low * (1 - STRETCH), bar.high * (1 + STRETCH))
    if not bar.low <= bar.high or not reach[0] <= min(ends) <= max(ends) <= reach[1]:
        return f"{at} has an open or close outside its high and low"
    return replace(bar, high=max(bar.high, *ends), low=min(bar.low, *ends))


def _near(bar: Five, other: Five) -> bool:
    """The bar's whole range lies within a market's move of the other's close."""
    return other.close / JUMP <= bar.low and bar.high <= other.close * JUMP


def checked(
    line: Line, bars: Iterable[Five], held: Sequence[Decimal] = ()
) -> tuple[list[Five], list[str]]:
    """The bars of one line that can be true, oldest first, and every fault found on the way.
    A moment given twice differently keeps neither bar. A bar a hundredfold from the middle
    of the closes held, or with none held the middle close of all that was given, is in a
    wrong unit, and is not kept. Any other move further
    than the store believes a market makes may be real: its bar is kept, and the move is a
    fault. Five minutes in which nothing traded have no bar, and that is no fault."""
    faults: list[str] = []
    given: dict[datetime, set[Five]] = {}
    for bar in bars:
        given.setdefault(bar.start, set()).add(bar)
    sound: list[Five] = []
    for start, said in sorted(given.items()):
        entered = _entered(line, next(iter(said))) if len(said) == 1 else None
        if isinstance(entered, Five):
            sound.append(entered)
        else:
            faults.append(entered or f"{start:%Y-%m-%d %H:%M} given {len(said)} ways; none kept")
    if not sound:
        return [], faults
    middle = median_low(held or [bar.close for bar in sound])
    kept: list[Five] = []
    for bar in sound:
        at = f"{bar.start:%Y-%m-%d %H:%M}"
        if any(p >= middle * FAR or p * FAR <= middle for p in (bar.high, bar.low)):
            faults.append(f"{at} is a hundredfold from the bars around it: a wrong unit")
            continue
        if kept and not (_near(bar, kept[-1]) and _near(kept[-1], bar)):
            faults.append(f"{at} moved from {kept[-1].close} to {bar.close}")
        kept.append(bar)
    return kept, faults


def keep(
    path: Path, answers: Mapping[Line, Iterable[Five] | Refused]
) -> dict[Line, tuple[str, ...]]:
    """An evening's answers from the archive into the store at path, in one round: each line's
    bars that pass the checks, their unit judged against the bars held from the same days,
    and every line's faults. A line the archive refused adds nothing this evening. A bar held
    stays unless a bar for its own moment passes the checks, and takes its place; where it
    was held from another source and differs, that is counted among the line's faults."""
    faults: dict[Line, tuple[str, ...]] = {}
    with writing(path, Source.ARCHIVE) as round_:
        for line, bars in answers.items():
            if isinstance(bars, Refused):
                faults[line] = (f"the archive refused it: {bars.reason}",)
                continue
            given = list(bars)
            since = min((bar.start for bar in given), default=EPOCH)
            kept, found = checked(line, given, round_.closes(line, since))
            differ = round_.apart(line, kept)[1]
            round_.five(line, kept)
            gave = [f"{differ} bars held from another source differ, and gave way"] * (differ > 0)
            faults[line] = (*found, *gave)
    return faults
