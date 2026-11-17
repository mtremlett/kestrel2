"""day - THE DESK'S DAY: decide on the bars before it, size, send, and at its end reconcile
and publish one record. The same days run again from the same saved data give the same records."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from functools import partial
from pathlib import Path

from desk import book, day_money, halt, restop, strategy, venues
from desk.broker import Broker, Restopping
from desk.day_parts import BEFORE_HEAT as BEFORE_HEAT
from desk.day_parts import HEADER as HEADER
from desk.day_parts import MONEY as MONEY
from desk.day_parts import RECORDS as RECORDS
from desk.day_parts import Record as Record
from desk.day_parts import _row as _row
from desk.day_parts import records as records
from desk.halt import Blocker, Stopped
from desk.lines import YARDSTICK, Line
from desk.orders import (
    Order,
    Refused,
    Sale,
    Settings,
    order_id_of,
    pennies,
    size,
    strategy_of,
)
from desk.risk import Standing
from desk.store import Bar
from desk.strategy import Action, Decision


def run(
    root: Path,
    archive: Mapping[Line, Sequence[Bar]],
    broker: Restopping,
    settings: Settings,
    day: date,
    rates: Mapping[str, Decimal],
) -> Record:
    """A whole day from the data saved by its end, the day's own bars in it: its orders are
    decided on the bars before the day alone, each stop is moved under its fill (restop), and
    then its record is published."""
    seen = {line: tuple(bar for bar in bars if bar.day < day) for line, bars in archive.items()}
    trade(root, seen, broker, settings, day, rates)
    restop.move(root, broker, archive)  #: each fill's stop, under the fill (R-RUNNER-220)
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
    worth = day_money.worth(root, archive, day)
    market = (
        day_money.close(archive, YARDSTICK, day) / day_money.close(archive, YARDSTICK, since) - 1
    )
    profit = None if differ else pennies(worth - opened + cash - costs.total)
    held = pennies(settings.capital * market)
    halts = tuple(h.at for h in halt.on(root, day)), halt.stopped(root, day)
    heat = day_money.heat(root, archive, day)
    record = Record(day, profit, costs.published(), held, differ, worth, len(ledger), *halts, heat)
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


def trade(
    root: Path,
    archive: Mapping[Line, Sequence[Bar]],
    broker: Broker,
    settings: Settings,
    day: date,
    rates: Mapping[str, Decimal],
    tell: book.Tell | None = None,
    killed: frozenset[str] = frozenset(),
) -> tuple[book.Sent, ...]:
    """The day's orders, after the market opens: each rule's decision on the session before,
    its position read from the book; the sales first, then each buy sized from the book after
    the send before it. A line sold this morning, by its rule or its stop, is not bought
    again today. While the book is not the broker's the send path refuses every buy, and the
    sale of a line whose shares differ. rates are the day's pounds per unit of each currency.
    Nothing is sent for a day that is over: its record made, or a later fill in the ledger.
    Every buy and sale the rules ask for has its answer, and each not filled whole goes on
    the morning's list as it is answered, under its blocker (halt.morning), with the lines
    no rule could decide. A place the broker disagrees with is told through tell (book.send).
    A strategy in killed (its own kill condition met, lab/promotion.py) buys nothing, said so;
    what it holds is still sold by its rule or its stop."""
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
    sent = list[book.Sent]()
    for d in (d for d in decided if d.action is Action.SELL):  #: by the rule that holds it
        sale = Sale(order_id_of(d), due[d.symbol], held[d.symbol])
        sent.append(_answer(root, day, _send(root, broker, sale, settings, tell, None)))
    _alert(root, day, settings, tell)
    exposed = partial(day_money.exposure, root, archive, rates)  #: read again at each buy
    for d in (d for d in decided if d.action is Action.BUY):
        line = due[d.symbol]
        price = archive[line][-1].close, rates[line.currency]
        args = (root, broker, d, line, price, settings, day, tell, exposed)
        sent.append(_answer(root, day, _barred(d) if d.strategy in killed else _buy(*args)))
    return tuple(sent)


def _alert(root: Path, day: date, settings: Settings, tell: book.Tell | None) -> None:
    """ON PAPER A LOSS LIMIT REACHED IS TOLD TO HIM (halt.drawdown): the buys still go, the gate
    having refused them if the limit is past; recorded once for the day."""
    at = datetime.combine(day, time(), UTC)
    words = halt.drawdown(root, at, standing(root, day), settings)
    if words and tell is not None:
        tell(f"drawdown {day}", words)


def _barred(d: Decision) -> book.Sent:
    """The answer for a buy by a strategy that met its kill condition: not sent, and why."""
    name = order_id_of(d)
    why = f"{name}: not sent, {d.strategy} met its kill condition and buys nothing"
    return book.Sent(name, 0, why, Blocker.GATE)


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
    tell: book.Tell | None,
    exposed: Callable[[], dict[str, Decimal]] | None = None,
) -> book.Sent:
    """One rule's buy, sized from the book as the send before it left it, at the line's last
    close and the day's rate. A line held, or sold this morning, is not bought: said so. Nor is
    one an ISA is not recorded as able to hold (line.isa no): the ISA buys only those; nor one no
    retail customer may buy (line.retail no), which the broker would only refuse, slowly."""
    now, name = book.positions(root), order_id_of(d)
    if line.isa is False or line.retail is False:
        why = (
            "is recorded as a line no stocks and shares ISA can hold"
            if line.isa is False
            else "is recorded as a line no UK retail customer may buy"
        )
        return book.Sent(name, 0, f"{name}: not sent, {d.symbol} {why}", Blocker.GATE)
    sold = {f.symbol for f in book.fills(root) if f.day == day and f.quantity < 0}
    if d.symbol in now or d.symbol in sold:
        why = "is held already" if d.symbol in now else "was sold this morning"
        return book.Sent(name, 0, f"{name}: not sent, {d.symbol} {why}", Blocker.HELD)
    try:
        order = size(d, line, *price, settings, now)
    except Refused as refused:  #: the gate's answer, kept with the day's others
        return book.Sent(name, 0, str(refused), Blocker.GATE)
    return _send(root, broker, order, settings, tell, standing(root, day), exposed and exposed())


def standing(root: Path, day: date) -> Standing:
    """WHERE THE BOOK STANDS AGAINST ITS LOSS AND ORDER-RATE LIMITS when the day opens
    (canon B1, risk.loss_limit): the day's loss is the pounds the last published record lost
    (0 when it gained or was withheld), the week's the net pounds lost over the records of
    day's own ISO week, and the new lines the lines first bought today."""
    profits = [(r.day, r.profit or Decimal(0)) for r in records(root)]
    week = sum((p for d, p in profits if d.isocalendar()[:2] == day.isocalendar()[:2]), Decimal(0))
    lost = -profits[-1][1] if profits else Decimal(0)
    bought = {f.symbol for f in book.fills(root) if f.day == day and f.quantity > 0}
    return Standing(max(lost, Decimal(0)), max(-week, Decimal(0)), len(bought))


def _send(
    root: Path,
    broker: Broker,
    order: Order | Sale,
    settings: Settings,
    tell: book.Tell | None,
    held: Standing | None,
    pounds: Mapping[str, Decimal] | None = None,
) -> book.Sent:
    """Send through the one door; its refusal is the order's answer, kept with the day's
    under the blocker the send path names; one it does not name is the broker's own door's."""
    try:
        return book.send(root, broker, order, settings, tell, held, pounds)
    except Stopped as stopped:
        return book.Sent(order.order_id, 0, str(stopped), stopped.blocker)
    except Refused as refused:
        return book.Sent(order.order_id, 0, str(refused), Blocker.BROKER)


def _due(line: Line, bars: Sequence[Bar], day: date) -> bool:
    """The line's venue trades on day and its last bar is the session before: decisions
    dated any other day are not acted on."""
    return bool(bars) and venues.sessions(line.venue, bars[-1].day, day) == (bars[-1].day, day)
