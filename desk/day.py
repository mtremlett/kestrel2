"""day - THE DESK'S DAY: decide on the bars before it, size, send, and at its end reconcile
and publish one record. The same days run again from the same saved data give the same records."""

from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from dataclasses import astuple, dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from desk import book, strategy, venues
from desk.broker import Broker
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
from desk.strategy import Action

RECORDS = "records.csv"
HEADER = ("day", "profit", *Charges.__dataclass_fields__, "market", "mismatches")


@dataclass(frozen=True)
class Record:
    """One day, as published: pounds, each amount rounded once, to the penny, where the record
    is made. A day whose book is not the broker's names the lines and has no profit; no other
    day lacks one."""

    day: date
    profit: Decimal | None  #: the book's gain after every cost; None when it is not the broker's
    costs: Charges  #: every cost of the day's fills, line by line: none can be left out
    market: Decimal  #: what the same capital would have earned simply holding the market
    mismatches: tuple[str, ...]  #: lines where the desk's book and the broker's differ

    def __post_init__(self) -> None:
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
    broker's: lines that differ are named and the profit withheld. Else the profit is what
    the book gained: what it holds at the day's closes, less what it held at the closes
    before, with the money the day's fills moved, after every cost of those fills. Beside
    it, what the capital would have gained in the yardstick (lines.YARDSTICK, quoted in
    pounds) from its close before to the day's. Every session has its record, in order: one
    the desk missed is named, and published first, once its rates are kept."""
    kept = {record.day: record for record in records(root)}
    last = max((on for on in kept if on < day), default=day)
    markets = {line.venue for line in archive}
    traded = {on for venue in markets for on in venues.sessions(venue, last, day)}
    if missed := sorted(traded - {last, day}):
        raise ValueError(f"{day}: no record yet for {missed}, and each session has its own")
    differ = book.reconcile(root, broker)
    cash, costs = book.dealt(root, archive, day)
    eve = day - timedelta(days=1)
    gained = _worth(root, archive, day) - _worth(root, archive, eve) + cash
    market = _close(archive, YARDSTICK, day) / _close(archive, YARDSTICK, eve) - 1
    profit = None if differ else pennies(gained - costs.total)
    kept[day] = Record(day, profit, costs.published(), pennies(settings.capital * market), differ)
    rows = (
        (on, r.profit, *astuple(r.costs), r.market, *r.mismatches) for on, r in sorted(kept.items())
    )
    book.write(root / RECORDS, [HEADER, *rows])
    return kept[day]


def records(root: Path) -> tuple[Record, ...]:
    """Every day's record the desk has published, oldest first, as it was published."""
    path = root / RECORDS
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8") as kept:
        rows = list(csv.reader(kept))[1:]
    return tuple(
        Record(
            date.fromisoformat(row[0]),
            Decimal(row[1]) if row[1] else None,
            Charges(*map(Decimal, row[2:7])),
            Decimal(row[7]),
            tuple(row[8:]),
        )
        for row in rows
    )


def _worth(root: Path, archive: Mapping[Line, Sequence[Bar]], upto: date) -> Decimal:
    """What the book held at a day's end was worth, in pounds: each line at its close then,
    and the newest rate kept on or before that day."""
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
    sale of a line whose shares differ. rates are the day's pounds per unit of each currency."""
    book.collect(root, broker)  #: the stops the open sold
    book.record_rates(root, day, rates)
    held = book.positions(root)
    holders = {f.symbol: strategy_of(f.order_id) for f in book.fills(root) if f.quantity > 0}
    due = {line.symbol: line for line, bars in archive.items() if _due(line, bars, day)}
    unpriced = sorted({line.currency for line in due.values()} - set(rates))
    if unpriced:
        raise ValueError(f"{day}: no rate in pounds for {unpriced}; nothing sent")
    decided = strategy.today(
        {symbol: archive[line] for symbol, line in due.items()},
        {symbol: holders[symbol] for symbol in held if symbol in due},
    )
    sent = [
        _send(root, broker, Sale(order_id_of(d), due[d.symbol], held[d.symbol]), settings)
        for d in decided
        if d.action is Action.SELL  #: only the rule the book holds the line for can sell
    ]
    for d in (d for d in decided if d.action is Action.BUY):
        now, line = book.positions(root), due[d.symbol]
        sold = {f.symbol for f in book.fills(root) if f.day == day and f.quantity < 0}
        if d.symbol in now or d.symbol in sold:
            continue
        try:
            order = size(d, line, archive[line][-1].close, rates[line.currency], settings, now)
        except Refused as refused:  #: the gate's answer, kept with the day's others
            sent.append(book.Sent(order_id_of(d), 0, str(refused)))
            continue
        sent.append(_send(root, broker, order, settings))
    return tuple(sent)


def _send(root: Path, broker: Broker, order: Order | Sale, settings: Settings) -> book.Sent:
    """Send through the one door; its refusal is the order's answer, kept with the day's."""
    try:
        return book.send(root, broker, order, settings)
    except Refused as refused:
        return book.Sent(order.order_id, 0, str(refused))


def _due(line: Line, bars: Sequence[Bar], day: date) -> bool:
    """The line's venue trades on day and its last bar is the session before: decisions
    dated any other day are not acted on."""
    return bool(bars) and venues.sessions(line.venue, bars[-1].day, day) == (bars[-1].day, day)
