"""bars - THE ONE FAST STORE, for hot and deep bars alike: one SQLite file in WAL mode, the
standard library's own, with one writer and many readers (the operator's need of 13 November
2026, DAT-04). It is held to three benchmarks, in tests/unit/test_bars.py: a five-minute
round for every line written in under a second, a line's last week read in under 50 ms, a
line's daily history read in under 200 ms.

The writer works in rounds. Everything written in a round lands together when the round
ends, forced to disk, or none of it does; a reader is never made to wait and sees whole
rounds only. A second writer is refused at once, never queued.

A line is its venue and its symbol: one symbol can be two companies. A daily bar is named by
its session's day; a five-minute bar by the moment it starts, in UTC. Prices are kept as the
exact decimals they were written as."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from desk.lines import Line
from desk.store import Bar

DAILY, FIVE = "daily", "five-minute"  #: the two spans of bar the store holds
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
#: Each bar under its line, its span and the start of its span: a daily bar's day as its
#: ordinal, a five-minute bar's start as seconds since EPOCH. `held` names every line and
#: span ever written, so that a line never written is not read as a line with no bars.
SCHEMA = (
    "CREATE TABLE IF NOT EXISTS bar (venue TEXT NOT NULL, symbol TEXT NOT NULL,"
    " span TEXT NOT NULL, at INTEGER NOT NULL, open TEXT NOT NULL, high TEXT NOT NULL,"
    " low TEXT NOT NULL, close TEXT NOT NULL, volume INTEGER NOT NULL,"
    " PRIMARY KEY (venue, symbol, span, at)) WITHOUT ROWID",
    "CREATE TABLE IF NOT EXISTS held (venue TEXT NOT NULL, symbol TEXT NOT NULL,"
    " span TEXT NOT NULL, PRIMARY KEY (venue, symbol, span)) WITHOUT ROWID",
)
HOLD = "INSERT OR IGNORE INTO held VALUES (?, ?, ?)"
HELD = "SELECT 1 FROM held WHERE venue = ? AND symbol = ? AND span = ?"
CLEAR = "DELETE FROM bar WHERE venue = ? AND symbol = ? AND span = ?"
ADD = "INSERT INTO bar VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
PUT = "INSERT OR REPLACE INTO bar VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
READ = (
    "SELECT at, open, high, low, close, volume FROM bar"
    " WHERE venue = ? AND symbol = ? AND span = ? AND at >= ? AND at < ? ORDER BY at"
)


class Busy(RuntimeError):
    """Another writer holds the store. It has one writer; a second is refused, not queued."""


def _seconds(moment: datetime) -> int:
    """A moment in UTC as whole seconds since EPOCH; one in no zone, or another, is refused."""
    if moment.utcoffset() != timedelta(0):
        raise ValueError(f"{moment!r} is not a moment in UTC")
    return (moment - EPOCH) // timedelta(seconds=1)


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
    """One round of the one writer, open: what it is given lands when the round ends."""

    def __init__(self, held: sqlite3.Connection) -> None:
        self._held = held

    def _write(
        self, how: str, line: Line, span: str, bars: Iterable[tuple[int, Bar | Five]]
    ) -> None:
        key = (line.venue, line.symbol, span)
        self._held.execute(HOLD, key)
        rows = (
            (*key, at, str(b.open), str(b.high), str(b.low), str(b.close), b.volume)
            for at, b in bars
        )
        self._held.executemany(how, rows)

    def daily(self, line: Line, bars: Iterable[Bar]) -> None:
        """A line's daily history, whole: it takes the place of the history held before, for
        an archive restates the past. A day given twice is refused, and the round with it."""
        self._held.execute(CLEAR, (line.venue, line.symbol, DAILY))
        self._write(ADD, line, DAILY, ((b.day.toordinal(), b) for b in bars))

    def five(self, line: Line, bars: Iterable[Five]) -> None:
        """More of a line's five-minute bars. They only gather: a bar given again for a moment
        takes the place of the one held for it, and no other bar is touched."""
        self._write(PUT, line, FIVE, ((_seconds(b.start), b) for b in bars))


@contextmanager
def writing(path: Path) -> Iterator[Round]:
    """The one writer's next round on the store at path, which is made on its first round.
    The round lands whole as the block ends; if the block fails, nothing of it lands."""
    with closing(sqlite3.connect(path, timeout=0, isolation_level=None)) as held:
        try:
            held.execute("PRAGMA journal_mode = WAL")
            held.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError as refusal:
            if refusal.sqlite_errorcode != sqlite3.SQLITE_BUSY:
                raise
            raise Busy(f"{path}: another writer holds the store") from refusal
        with held:
            for table in SCHEMA:
                held.execute(table)
            yield Round(held)


def _read(path: Path, line: Line, span: str, first: int, end: int) -> list[tuple[int, ...]]:
    """A line's rows of one span from first up to, not including, end, oldest first."""
    if not path.is_file():
        raise FileNotFoundError(f"{path}: no store has been written there")
    key = (line.venue, line.symbol, span)
    with closing(sqlite3.connect(path)) as held:
        rows: list[tuple[int, ...]] = held.execute(READ, (*key, first, end)).fetchall()
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
        Five(datetime.fromtimestamp(at, UTC), Decimal(o), Decimal(h), Decimal(lo), Decimal(c), v)
        for at, o, h, lo, c, v in rows
    )
