"""day - THE DESK'S DAY: prepare the data, decide, size, send, reconcile, publish one record.
The same days run again from the same saved data give the same records."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from desk import book, strategy, venues
from desk.broker import Pretend
from desk.lines import Line
from desk.orders import Order, Refused, Sale, Settings, order_id_of, size, strategy_of
from desk.store import Bar
from desk.strategy import Action


@dataclass(frozen=True)
class Costs:
    """Every cost line, in pounds. A record cannot be made with one missing."""

    commission: Decimal
    spread: Decimal
    slippage: Decimal
    currency: Decimal
    uk_taxes: Decimal


@dataclass(frozen=True)
class Record:
    day: date
    profit: Decimal | None  #: after every cost; None when the book is not the broker's
    costs: Costs
    market: Decimal  #: what simply holding the market would have earned
    mismatches: tuple[str, ...]  #: lines where the desk's book and the broker's differ


def run(
    root: Path,
    archive: Mapping[Line, Sequence[Bar]],
    broker: Pretend,
    settings: Settings,
    day: date,
    rates: Mapping[str, Decimal],
) -> Record:
    trade(root, archive, broker, settings, day, rates)
    raise NotImplementedError("day.run: the day's reconciled record is scenes 6 and 7")


def trade(
    root: Path,
    archive: Mapping[Line, Sequence[Bar]],
    broker: Pretend,
    settings: Settings,
    day: date,
    rates: Mapping[str, Decimal],
) -> tuple[book.Sent, ...]:
    """The day's orders, after the market opens: each rule's decision on the session before,
    its position read from the book; the sales first, then each buy sized from the book after
    the send before it. A line sold this morning, by its rule or its stop, is not bought
    again today. While the book is not the broker's the send path refuses every buy, and the
    sale of a line they differ on. rates are the day's pounds per unit of each currency."""
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


def _send(root: Path, broker: Pretend, order: Order | Sale, settings: Settings) -> book.Sent:
    """Send through the one door; its refusal is the order's answer, kept with the day's."""
    try:
        return book.send(root, broker, order, settings)
    except Refused as refused:
        return book.Sent(order.order_id, 0, str(refused))


def _due(line: Line, bars: Sequence[Bar], day: date) -> bool:
    """The line's venue trades on day and its last bar is the session before: decisions
    dated any other day are not acted on."""
    return bool(bars) and venues.sessions(line.venue, bars[-1].day, day) == (bars[-1].day, day)
