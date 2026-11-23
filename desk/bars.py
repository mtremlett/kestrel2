"""bars - THE ONE FAST STORE, for hot and deep bars alike: one SQLite file in WAL mode, with one
writer at a time and many readers (DAT-04, 13 November 2026). Three benchmarks, in
tests/unit/test_bars.py: a five-minute round for every line written in under a second, a
line's last week read in under 50 ms, a line's daily history in under 200 ms.

A writer works in rounds: what is written lands together when the round ends, forced to disk,
or none of it does. A reader reads the last whole round. A second writer waits its turn, and
is refused if it has not come within WAIT seconds (NoRound); a reader that must write behind
a held write ends in the named StoreWait (desk/bars_parts.py) after WAIT seconds.
A line is its venue and its symbol: one symbol can be two companies. A daily bar is named by
its session's day; a five-minute bar by its start, in UTC. Prices: the form of bars_form.py.

Five-minute bars are kept for good (DAT-11): the archive forgets them after sixty days, so
`keep` saves each evening's through the daily store's checks. No moment's bar is ever removed;
one the archive restates replaces the one held only by passing those checks. The last week
stays hot with every older bar archived beneath it in the same file.

Every bar is kept with its source, a round being one source's (Source). A fresh source, the
archive and the live session's IBKR, restate: a bar takes the place of what is held for that
moment or day, a changed day's old bar kept as a correction, and no day is ever deleted. Any
other (a store no longer kept, or the archive's backfill of a past day) only fills moments and
days that hold no bar, so a fresh bar always wins; where two sources' five-minute bars for
one moment differ, that is counted (`apart`)."""

from __future__ import annotations

import sqlite3
from collections.abc import Collection, Iterable, Iterator, Mapping
from contextlib import ExitStack, closing, contextmanager
from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from desk.bars_form import entered, judged, restated
from desk.bars_parts import CLOSES as CLOSES
from desk.bars_parts import NEWEST as NEWEST
from desk.bars_parts import OTHERS as OTHERS
from desk.bars_parts import READ as READ
from desk.bars_parts import RESTORE as RESTORE
from desk.bars_parts import SOURCES as SOURCES
from desk.bars_parts import WITHDRAW as WITHDRAW
from desk.bars_parts import StoreWait as StoreWait
from desk.bars_parts import checked as checked
from desk.bars_parts import named
from desk.bars_schema import ADD as ADD
from desk.bars_schema import FILL as FILL
from desk.bars_schema import HELD as HELD
from desk.bars_schema import HOLD as HOLD
from desk.bars_schema import MADE as MADE
from desk.bars_schema import PUT as PUT
from desk.bars_schema import SCHEMA as SCHEMA
from desk.bars_schema import SOURCED as SOURCED
from desk.bars_schema import Source as Source
from desk.compare import AGREE as AGREE
from desk.compare import Verdict, judge
from desk.lines import REFERENCE, TAG, Line
from desk.spans import DAILY as DAILY
from desk.spans import EPOCH as EPOCH
from desk.spans import FIVE as FIVE
from desk.spans import SPANS, Timed
from desk.spans import Five as Five
from desk.spans import _seconds as _seconds
from desk.store import Answer, Bar, Older, Refused

HISTORY, LIVE = "market_history.db", "market_live.db"  #: database long, database short (his ruling)
#: The seconds anyone waits for the file: a writer for the one before it, or SQLite's own log.
WAIT = 5.0


def files(live: Path) -> dict[str, Path]:
    """The store's two databases by the span each holds, given the short one: the long one,
    which holds the daily bars and every span from an hour up, is beside it."""
    return {DAILY: live.with_name(HISTORY), FIVE: live}


class NoRound(RuntimeError):
    """No round was begun, or the round is lost, for SQLite's own reason: "database is
    locked" is a store that stayed in another's hands for WAIT seconds."""


class Round:
    """One round of a writer, open: what it is given lands when the round ends, each bar
    kept with the round's one source."""

    def __init__(self, held: Mapping[str, sqlite3.Connection], source: Source) -> None:
        self._held, self._source = held, source

    def _write(
        self,
        put: str,
        line: Line,
        span: str,
        bars: Iterable[tuple[int, Bar | Five | Timed]],
    ) -> int:
        """One line's bars of one span, all of them or, if any is refused, none: the round is
        then as it was before, whether or not the caller ends it there. A round that SQLite
        itself has dropped (a full disk) takes no more, and nothing of it lands. It says how
        many bars landed. A daily bar a fresh source changes leaves its old value in `correction`.
        """
        held = self._held[SPANS[span].home]
        if not all(one.in_transaction for one in self._held.values()):
            raise NoRound(f"SQLite dropped this round: nothing of it lands, {line.symbol} too")
        key = (line.venue, line.symbol, span)
        prices = [(at, entered(b)) for at, b in bars]
        rows = [(*key, at, *price, self._source.value) for at, price in prices]
        given = len(rows)
        held.execute("SAVEPOINT line")
        try:
            held.execute(HOLD, key)
            if span == DAILY and put == PUT:
                rows = restated(held, self._source.value, key, prices, rows)
            landed = held.executemany(put, rows).rowcount
        except BaseException:
            if held.in_transaction:
                held.execute("ROLLBACK TO line")
            raise
        held.execute("RELEASE line")
        return landed + given - len(rows)

    def daily(
        self,
        line: Line,
        bars: Iterable[Bar],
        withdrawn: Iterable[date] = (),
        refused: Iterable[Bar] = (),
    ) -> None:
        """A line's daily bars from this source, joined by day into what the store holds, and
        none held is ever deleted (B3): a fresh source's bar takes the day of another's, the old
        value kept in `correction` if it differs. A day in `withdrawn` was judged untrue: its row
        stays, marked, unread until a bar is given for it again. A bar in `refused` was judged
        untrue: its day is withdrawn only if the row held is that very bar, else the held row
        stands. A day given twice is refused."""
        if not self._source.fresh:
            raise ValueError(f"{self._source.value} is no fresh source: it restates nothing")
        given = [(b.day.toordinal(), b) for b in bars]
        if len({at for at, _ in given}) < len(given):
            what = f"{line.symbol} on {line.venue}: its history gives a day twice; none kept"
            raise ValueError(what)
        key, held = (line.venue, line.symbol, DAILY), self._held[DAILY]
        self._write(PUT, line, DAILY, given)
        held.execute("SAVEPOINT marks")
        try:
            ours = {at for at, _ in given}
            bad = [
                (b.day.toordinal(), entered(b)) for b in refused if b.day.toordinal() not in ours
            ]
            drop, stand = judged(held, key, bad)
            held.executemany(RESTORE, ((*key, at) for at in (*ours, *stand)))
            gone = ({day.toordinal() for day in withdrawn} | set(drop)) - ours
            held.executemany(WITHDRAW, ((*key, at) for at in sorted(gone)))
        except BaseException:
            held.execute("ROLLBACK TO marks")
            raise
        held.execute("RELEASE marks")

    def days(self, line: Line, bars: Iterable[Bar]) -> int:
        """More daily bars, and how many landed: as `five`, but for days not moments."""
        put = PUT if self._source.fresh else FILL
        return self._write(put, line, DAILY, ((bar.day.toordinal(), bar) for bar in bars))

    def five(self, line: Line, bars: Iterable[Five]) -> int:
        """More of a line's five-minute bars, and how many landed. They only gather: from a
        fresh source a bar given again for a moment takes the place of the one held for it;
        from any other a bar lands only on a moment that holds none. No other bar is touched."""
        put = PUT if self._source.fresh else FILL
        return self._write(put, line, FIVE, ((_seconds(b.start), b) for b in bars))

    def timed(self, line: Line, span: str, bars: Iterable[Timed]) -> int:
        """More of a line's bars of any other span, and how many landed: as `five`."""
        put = PUT if self._source.fresh else FILL
        return self._write(
            put, line, span, ((_seconds(b.start), b) for b in bars if b.span == span)
        )

    def compare(self, line: Line, bars: Collection[Five]) -> Verdict:
        """How the bars meet the bars held from another source for their own moments (see
        desk.compare): agreeing, the adjusted form of the raw, or a real disagreement."""
        given = {_seconds(bar.start): bar for bar in bars}
        key = (line.venue, line.symbol, FIVE, self._source.value, min(given, default=0))
        rows = self._held[FIVE].execute(OTHERS, (*key, max(given, default=0)))
        return judge(
            line, [(given[at], [Decimal(p) for p in held]) for at, *held in rows if at in given]
        )

    def apart(self, line: Line, bars: Collection[Five]) -> tuple[int, int]:
        """How many of the bars meet a bar held from another source for their own moment, and
        how many of those are no form of it."""
        verdict = self.compare(line, bars)
        return verdict.met, len(verdict.differ)

    def closes(self, line: Line, since: datetime) -> list[Decimal]:
        """The closes of the line's five-minute bars held from since on, this round's too."""
        key = (line.venue, line.symbol, FIVE, _seconds(since))
        return [Decimal(close) for (close,) in self._held[FIVE].execute(CLOSES, key)]


def _open(file: Path) -> sqlite3.Connection:
    """The one opener, reader's or writer's: a store already made gains any newer table."""
    one = sqlite3.connect(file, timeout=WAIT, isolation_level=None)
    try:
        with named(file, WAIT):
            if one.execute(MADE).fetchone() is not None:
                for table in SCHEMA:
                    one.execute(table)
    except BaseException:
        one.close()
        raise
    return one


@contextmanager
def writing(path: Path, source: Source = Source.ARCHIVE) -> Iterator[Round]:
    """A source's next round on the store whose short database is at path (its long one beside
    it), made on its first round: the fresh archive's unless an old store is named. The round
    lands as the block ends in each database; if the block fails, nothing of it lands."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        held = {
            span: stack.enter_context(closing(_open(file))) for span, file in files(path).items()
        }
        try:
            for one in held.values():
                one.execute("PRAGMA journal_mode = WAL")
                one.execute("PRAGMA synchronous = FULL")
                one.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError as refusal:
            raise NoRound(f"{path}: no round begun: {refusal}") from refusal
        with held[DAILY], held[FIVE]:
            for one in held.values():
                for table in SCHEMA:
                    one.execute(table)
                if all(c[1] != "source" for c in one.execute("PRAGMA table_info(bar)")):
                    one.execute(SOURCED)
            yield Round(held, source)
            if not all(one.in_transaction for one in held.values()):
                for one in held.values():  # SQLite dropped one database's round: none lands
                    one.rollback()


def _read(
    path: Path, line: Line, span: str, first: int, end: int, what: str = READ
) -> list[tuple[Any, ...]]:
    """A line's rows of one span from first up to end, oldest first, read at one moment of the
    store: its last whole round."""
    key, path = (line.venue, line.symbol, span), files(path)[SPANS[span].home]
    if not path.is_file():
        raise FileNotFoundError(f"{path}: no store has been written there")
    with closing(_open(path)) as held:
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


def total_return(path: Path, line: Line) -> tuple[Bar, ...]:
    """A line's daily history with its dividends kept in (UNI-07): a reference series' adjusted
    twin, as the archive adjusts it; any other line as held (the yardstick VUAG accumulates)."""
    return daily(path, replace(line, symbol=line.symbol + TAG) if line in REFERENCE else line)


def five(path: Path, line: Line, since: datetime, until: datetime) -> tuple[Five, ...]:
    """A line's five-minute bars starting from since up to, not including, until, oldest
    first: its last week is the seven days up to now."""
    rows = _read(path, line, FIVE, _seconds(since), _seconds(until))
    return tuple(
        Five(EPOCH + timedelta(seconds=at), Decimal(o), Decimal(h), Decimal(lo), Decimal(c), v)
        for at, o, h, lo, c, v in rows
    )


def timed(path: Path, line: Line, span: str, since: datetime, until: datetime) -> tuple[Timed, ...]:
    """A line's bars of one span starting from since up to, not including, until, oldest first."""
    rows = _read(path, line, span, _seconds(since), _seconds(until))
    return tuple(
        Timed(
            span, EPOCH + timedelta(seconds=at), Decimal(o), Decimal(h), Decimal(lo), Decimal(c), v
        )
        for at, o, h, lo, c, v in rows
    )


def sources(path: Path, line: Line, span: str) -> dict[Source, int]:
    """How many of a line's bars of one span the store holds from each source."""
    return {Source(name): count for name, count in _read(path, line, span, 0, 2**62, SOURCES)}


def newest(path: Path, line: Line, span: str) -> tuple[int, Source] | None:
    """A line's newest bar of one span as the store holds it: its moment (a daily bar's day as an
    ordinal, else seconds since EPOCH) and the source it came from; none if it holds no bar."""
    got = _read(path, line, span, 0, 2**62, NEWEST)
    return (got[0][0], Source(got[0][1])) if got else None


def keep(
    path: Path,
    answers: Mapping[Line, Iterable[Five] | Refused],
    source: Source = Source.ARCHIVE,
) -> dict[Line, tuple[str, ...]]:
    """A source's answers (the archive's unless named) into the store at path, in one round:
    each line's bars that pass the checks, their unit judged against the bars held from the
    same days, and every line's faults. A line the source refused adds nothing this round. A
    bar held stays unless a bar for its own moment passes the checks, and takes its place; where it
    was held from another source and differs, that is counted among the line's faults."""
    faults: dict[Line, tuple[str, ...]] = {}
    with writing(path, source) as round_:
        for line, bars in answers.items():
            if isinstance(bars, Refused):
                faults[line] = (f"the {source.value} refused it: {bars.reason}",)
                continue
            given = list(bars)
            since = min((bar.start for bar in given), default=EPOCH)
            kept, found = checked(line, given, round_.closes(line, since))
            differ = round_.apart(line, kept)[1]
            round_.five(line, kept)
            gave = [f"{differ} bars held from another source differ, and gave way"] * (differ > 0)
            faults[line] = (*found, *gave)
    return faults


def bridge(fives: Iterable[Five], after: date, before: date) -> list[Bar]:
    """A daily bar for each day between two, of that day's five-minute bars: the first open,
    the highest high, the lowest low, the last close, the volumes."""
    days: dict[date, list[Five]] = {}
    for five_ in sorted(fives, key=lambda bar: bar.start):
        if after < five_.start.date() < before:
            days.setdefault(five_.start.date(), []).append(five_)
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


def bridged(path: Path, line: Line, day: date, shelf: Older, *given: Answer | None) -> Older:
    """The shelf with a daily bar bridged from the five-minute bars held, for each session of the
    thirty days before day that the shelf and every answer given lack (a line that trades too
    thinly for any daily source to hold each day: 3LGO). Nothing held: the shelf as it was."""
    held = {b.day for b in shelf or ()}
    held |= {b.day for one in given if one and not isinstance(one, Refused) for b in one}
    first = day - timedelta(30)
    try:
        fives = five(
            path, line, datetime.combine(first, time(), UTC), datetime.combine(day, time(), UTC)
        )
    except (LookupError, FileNotFoundError):
        return shelf  # no five-minute bar was ever kept for the line
    fills = [b for b in bridge(fives, first - timedelta(1), day) if b.day not in held]
    return [*(shelf or ()), *fills] if fills else shelf


def rolled_day(path: Path, line: Line, day: date) -> Answer:
    """The day's bar built from the five-minute bars held for it, or why none can be."""
    start = datetime.combine(day, time(), UTC)
    try:
        fives = five(path, line, start, start + timedelta(1))
    except (LookupError, FileNotFoundError):
        return Refused("no five-minute bar was ever kept for the line")
    return bridge(fives, day - timedelta(1), day + timedelta(1)) or Refused(
        "no five-minute bar held for the day"
    )
