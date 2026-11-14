"""day - THE DESK'S DAY: decide on the bars before it, size, send, and at its end reconcile
and publish one record. The same days run again from the same saved data give the same records."""

from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from dataclasses import astuple, dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from desk import book, halt, strategy, venues
from desk.broker import Broker
from desk.halt import Blocker, Stopped
from desk.lines import YARDSTICK, Line
from desk.orders import (
    Charges,
    Order,
    Refused,
    Sale,
    Settings,
    order_id_of,
    pennies,
    size,
    strategy_of,
)
from desk.store import Bar
from desk.strategy import Action, Decision

RECORDS = "records.csv"
MONEY = ("day", "profit", *Charges.__dataclass_fields__, "market", "worth", "counted")
HEADER = (*MONEY, "halted", "stopped", "differ")


@dataclass(frozen=True)
class Record:
    """One day, as published: pounds, each amount rounded once, to the penny, where the record
    is made. A day whose book is not the broker's names the lines and has no profit; no other
    day lacks one. With it, kept exact, what the next day's record carries on from. A day with
    a halt in force names it, and keeps its number. THE DAY'S VERDICT (NS-06): it counts only
    if its book was the broker's, no halt was in force, and its orders were sent, none of
    them stopped for a halt or the kill switch."""

    day: date
    #: The book's gain after every cost, since the last record that carried one: the day's
    #: own, unless days before it were withheld. None when the book is not the broker's.
    profit: Decimal | None
    costs: Charges  #: every cost behind that gain, line by line: none can be left out
    market: Decimal  #: what the capital would have earned simply holding the market those days
    mismatches: tuple[str, ...]  #: lines where the desk's book and the broker's differ
    worth: Decimal  #: what the book held at the day's end was worth: the next record opens here
    counted: int  #: the ledger's fills dated by the day, each counted by a record up to this one
    #: the halts in force that day, each by the moment it was called, as halt.kept stood. A
    #: record made without these two says nothing was sent, and does not count
    halted: tuple[datetime, ...] = ()
    stopped: int | None = None  #: signals the kill switch or a halt refused; None, none sent
    counts: bool = field(init=False)  #: the verdict

    def __post_init__(self) -> None:
        clear = self.profit is not None and not self.halted and self.stopped == 0
        object.__setattr__(self, "counts", clear)
        if (self.profit is None) != bool(self.mismatches):
            raise ValueError(
                f"{self.day}: a profit of {self.profit} with the book and the broker's "
                f"differing on {list(self.mismatches)}"
            )


def run(
    root: Path,
    archive: Mapping[Line, Sequence[Bar]],
    broker: Broker,
    settings: Settings,
    day: date,
    rates: Mapping[str, Decimal],
) -> Record:
    """A whole day from the data saved by its end, the day's own bars in it: its orders are
    decided on the bars before the day alone, and then its record is published."""
    seen = {line: tuple(bar for bar in bars if bar.day < day) for line, bars in archive.items()}
    trade(root, seen, broker, settings, day, rates)
    return publish(root, archive, broker, settings, day)


def publish(
    root: Path,
    archive: Mapping[Line, Sequence[Bar]],
    broker: Broker,
    settings: Settings,
    day: date,
) -> Record:
    """THE DAY'S RECORD, made at its end and kept (records). The book is set against the
    broker's as it stands when the record is made: lines that differ are named and the
    profit withheld. Else the profit is what the book gained since the last record that
    carried one: what it holds at the day's closes, less what that record kept it worth,
    with the money moved by the fills no such record has counted, after every cost of
    those fills. So the profits add up to the ledger's, whatever was withheld or learned
    late. Beside it, over the same days, what the capital would have gained in the
    yardstick (lines.YARDSTICK, quoted in pounds). Every session from the ledger's first
    fill has its own record, in order and once (_kept). The halts in force that day are read
    from their record (halt.on), so the day says so for as long as one is, and what the send
    path stopped from the morning's list (halt.stopped). A line held with no stop for all its
    shares goes on the day's list with the stop to put back (_bare)."""
    book_held, differ, unsure, stops = book.reckon(root, broker)
    kept = _kept(root, archive, day)
    start = (kept[0].day if kept else day) - timedelta(days=1)
    plain = ((r.day, r.worth, r.counted) for r in reversed(kept) if r.profit is not None)
    since, opened, counted = next(plain, (start, Decimal(0), 0))
    ledger = [fill.day for fill in book.fills(root) if fill.day <= day]
    cash, costs = book.dealt(root, archive, day, since, counted)
    worth = _worth(root, archive, day)
    market = _close(archive, YARDSTICK, day) / _close(archive, YARDSTICK, since) - 1
    profit = None if differ else pennies(worth - opened + cash - costs.total)
    held = pennies(settings.capital * market)
    halts = tuple(h.at for h in halt.on(root, day)), halt.stopped(root, day)
    record = Record(day, profit, costs.published(), held, differ, worth, len(ledger), *halts)
    if record.stopped is not None:  #: a day nobody sent for has no list (halt.morning)
        _bare(root, day, book_held, unsure, stops)
    book._write(root / RECORDS, [HEADER, *(_row(r) for r in (*kept, record))])
    return record


def _kept(root: Path, archive: Mapping[Line, Sequence[Bar]], day: date) -> tuple[Record, ...]:
    """The records so far, the day being the next to have one. A day they have reached is
    refused: a record is made once. So is a day beyond a session with none: each has its
    own, from the day of the ledger's first fill. A session the desk missed gets its record
    from publish alone, its rates kept first (book.record_rates), never from a day run again."""
    kept = records(root)
    first = min((fill.day for fill in book.fills(root)), default=day)
    since = kept[-1].day if kept else min(first, day) - timedelta(days=1)
    if day <= since:
        raise ValueError(f"{day}: the records run to {since}, and one is never rewritten")
    traded = {on for line in archive for on in venues.sessions(line.venue, since, day)}
    if missed := sorted(traded - {since, day}):
        raise ValueError(f"{day}: no record yet for {missed}, and each session has its own")
    return kept


def _row(r: Record) -> tuple[object, ...]:
    """A record as it is kept: the lines that differ last, as many as there are."""
    money = (r.day, r.profit, *astuple(r.costs), r.market, r.worth, r.counted)
    return (*money, " ".join(h.isoformat() for h in r.halted), r.stopped, *r.mismatches)


def records(root: Path) -> tuple[Record, ...]:
    """Every day's record the desk has published, oldest first, as it was published. A file
    there whose first line is not the records' own names is an error, never a day short. A
    row that ends at its money is a record made without its halts: it does not count."""
    path = root / RECORDS
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8") as kept:
        rows = list(csv.reader(kept))
    if rows[:1] != [list(HEADER)]:
        raise ValueError(f"{path}: not the desk's records")
    return tuple(
        Record(
            date.fromisoformat(row[0]),
            Decimal(row[1]) if row[1] else None,
            Charges(*map(Decimal, row[2:7])),
            Decimal(row[7]),
            tuple(row[12:]),
            Decimal(row[8]),
            int(row[9]),
            tuple(map(datetime.fromisoformat, row[10].split())),
            int(row[11]) if row[11] else None,
        )
        for row in (kept if kept[10:] else [*kept, "", ""] for kept in rows[1:])
    )


def _worth(root: Path, archive: Mapping[Line, Sequence[Bar]], upto: date) -> Decimal:
    """What the book held at a day's end was worth, in pounds: each line at its close then,
    at the rate kept for that very day."""
    lines = {line.symbol: line for line in archive}
    return sum(
        (
            shares * _close(archive, lines[s], upto) * book.rate(root, lines[s].currency, upto)
            for s, shares in book.positions(root, upto).items()
        ),
        Decimal(0),
    )


def _close(archive: Mapping[Line, Sequence[Bar]], line: Line, upto: date) -> Decimal:
    """The line's close at a day's end: its newest bar's by then. A session of its venue
    since that bar, the line not suspended, is a bar owed: an error, never an older price."""
    bars = [bar for bar in archive.get(line, ()) if bar.day <= upto]
    since = venues.sessions(line.venue, bars[-1].day, upto) if bars else (upto,)
    owed = [on for on in since if not bars or (on > bars[-1].day and on not in line.suspended)]
    if owed:
        raise ValueError(f"{upto}: no close of {line.symbol} for {owed}, so the day has no record")
    return bars[-1].close


def trade(
    root: Path,
    archive: Mapping[Line, Sequence[Bar]],
    broker: Broker,
    settings: Settings,
    day: date,
    rates: Mapping[str, Decimal],
) -> tuple[book.Sent, ...]:
    """The day's orders, after the market opens: each rule's decision on the session before,
    its position read from the book; the sales first, then each buy sized from the book after
    the send before it. A line sold this morning, by its rule or its stop, is not bought
    again today. While the book is not the broker's the send path refuses every buy, and the
    sale of a line whose shares differ. rates are the day's pounds per unit of each currency.
    Nothing is sent for a day that is over: its record made, or a later fill in the ledger.
    Every buy and sale the rules ask for has its answer, and each not filled whole goes on
    the morning's list as it is answered, under its blocker (halt.morning), with the lines
    no rule could decide."""
    book.collect(root, broker)  #: the stops the open sold
    if later := max((fill.day for fill in book.fills(root) if fill.day > day), default=None):
        raise ValueError(f"{day}: the day is over, the ledger holding a fill of {later}")
    if made := [record.day for record in records(root) if record.day >= day]:
        raise ValueError(f"{day}: the day is over, the records running to {made[-1]}")
    book.record_rates(root, day, rates)
    held = book.positions(root)
    holders = {f.symbol: strategy_of(f.order_id) for f in book.fills(root) if f.quantity > 0}
    due = {line.symbol: line for line, bars in archive.items() if _due(line, bars, day)}
    unpriced = sorted({line.currency for line in due.values()} - set(rates))
    if unpriced:
        raise ValueError(f"{day}: no rate in pounds for {unpriced}; nothing sent")
    _unread(root, tuple(archive), due, day)
    decided = strategy.today(
        {symbol: archive[line] for symbol, line in due.items()},
        {symbol: holders[symbol] for symbol in held if symbol in due},
    )
    sent: list[book.Sent] = []
    for d in (d for d in decided if d.action is Action.SELL):  #: by the rule that holds it
        sale = Sale(order_id_of(d), due[d.symbol], held[d.symbol])
        sent.append(_answer(root, day, _send(root, broker, sale, settings)))
    for d in (d for d in decided if d.action is Action.BUY):
        line = due[d.symbol]
        price = archive[line][-1].close, rates[line.currency]
        sent.append(_answer(root, day, _buy(root, broker, d, line, price, settings, day)))
    return tuple(sent)


def _bare(
    root: Path,
    day: date,
    held: Mapping[str, int],
    unsure: set[str],
    stops: Sequence[book.Difference],
) -> None:
    """A HOLDING WITH NO STOP: each line whose shares the broker holds as the book does, with
    fewer of them under a stop resting there, goes on the day's list under the stop it is due
    (its newest buy's, at the level kept for it, book.levels), saying what to put back."""
    kept = book.levels(root)
    due = {f.symbol: f"{f.order_id}-stop" for f in book.fills(root) if f.quantity > 0}
    resting = {d.name: d.broker for d in stops}
    level = {s: kept.get(due[s], "a level never kept, so set one by hand") for s in held}
    bare = [
        halt.Blocked(
            due[s],
            Blocker.BOOK,
            0,
            f"{s}: {n} shares held, {resting[s]} under a stop at"
            f" the broker; put back {due[s]}, selling {n} at {level[s]}",
        )
        for s, n in held.items()
        if s in resting and s not in unsure and resting[s] < n
    ]
    halt.note(root, day, bare)


def _unread(root: Path, lines: Sequence[Line], due: Mapping[str, Line], day: date) -> None:
    """Open the morning's list with the lines no rule could decide: its venue trades today
    and its bars do not end at the session before. A line read now leaves the list."""
    late = [s.symbol for s in lines if s.symbol not in due and venues.sessions(s.venue, day, day)]
    why = f"no bar for the session before {day}, so no rule decided"
    unread = [halt.Blocked(symbol, Blocker.UNREAD, 0, f"{symbol}: {why}") for symbol in late]
    halt.note(root, day, unread, (line.symbol for line in lines))


def _answer(root: Path, day: date, sent: book.Sent) -> book.Sent:
    """An order's answer, put on the morning's list if it was blocked and taken off if not."""
    if sent.blocker is None or sent.reason is None:
        halt.note(root, day, (), (sent.order_id,))
    else:
        blocked = halt.Blocked(sent.order_id, sent.blocker, sent.filled, sent.reason)
        halt.note(root, day, (blocked,))
    return sent


def _buy(
    root: Path,
    broker: Broker,
    d: Decision,
    line: Line,
    price: tuple[Decimal, Decimal],
    settings: Settings,
    day: date,
) -> book.Sent:
    """One rule's buy, sized from the book as the send before it left it, at the line's last
    close and the day's rate. A line held, or sold this morning, is not bought: said so."""
    now, name = book.positions(root), order_id_of(d)
    sold = {f.symbol for f in book.fills(root) if f.day == day and f.quantity < 0}
    if d.symbol in now or d.symbol in sold:
        why = "is held already" if d.symbol in now else "was sold this morning"
        return book.Sent(name, 0, f"{name}: not sent, {d.symbol} {why}", Blocker.HELD)
    try:
        order = size(d, line, *price, settings, now)
    except Refused as refused:  #: the gate's answer, kept with the day's others
        return book.Sent(name, 0, str(refused), Blocker.GATE)
    return _send(root, broker, order, settings)


def _send(root: Path, broker: Broker, order: Order | Sale, settings: Settings) -> book.Sent:
    """Send through the one door; its refusal is the order's answer, kept with the day's
    under the blocker the send path names; one it does not name is the broker's own door's."""
    try:
        return book.send(root, broker, order, settings)
    except Stopped as stopped:
        return book.Sent(order.order_id, 0, str(stopped), stopped.blocker)
    except Refused as refused:
        return book.Sent(order.order_id, 0, str(refused), Blocker.BROKER)


def _due(line: Line, bars: Sequence[Bar], day: date) -> bool:
    """The line's venue trades on day and its last bar is the session before: decisions
    dated any other day are not acted on."""
    return bool(bars) and venues.sessions(line.venue, bars[-1].day, day) == (bars[-1].day, day)
