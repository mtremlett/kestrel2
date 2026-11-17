"""day - THE DESK'S DAY: decide on the bars before it, size, send, and at its end reconcile
and publish one record. The same days run again from the same saved data give the same records."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from desk import book, halt, restop, strategy, venues
from desk.broker import Broker, Crash, Restopping
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
    book_held, differ, unsure, stops = book.reckon(root, broker, day)
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
    heat = _heat(root, archive, day)
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


def _heat(root: Path, archive: Mapping[Line, Sequence[Bar]], upto: date) -> Decimal | None:
    """The book's heat at a day's end, in pounds: each held line's shares times the larger of
    what falls from its newest buy's price to the stop kept for it, and the worst overnight
    gap down (a close to the next open) in its bars since that buy, at the day's rate. None
    if a held line's stop level was never kept: the heat is then not known."""
    kept, lines = book.levels(root), {line.symbol: line for line in archive}
    buys = {f.symbol: f for f in book.fills(root) if f.quantity > 0 and f.day <= upto}
    heat = Decimal(0)
    for symbol, shares in book.positions(root, upto).items():
        buy, line = buys[symbol], lines[symbol]
        if (stop := kept.get(f"{buy.order_id}-stop")) is None:
            return None
        bars = [bar for bar in archive[line] if buy.day <= bar.day <= upto]
        gaps = (before.close - after.open for before, after in zip(bars, bars[1:], strict=False))
        fall = max(buy.price - stop, *gaps, Decimal(0))
        heat += shares * fall * book.rate(root, line.currency, upto)
    return pennies(heat)


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
    tell: book.Tell | None = None,
    killed: frozenset[str] = frozenset(),
) -> tuple[book.Sent, ...]:
    """The day's orders, after the market opens: each rule's decision on the session before,
    its position read from the book; the sales first, then each buy sized from the book after
    the send before it. A line sold this morning, by its rule or its stop, is not bought
    again today. While the book is not the broker's the send path refuses every buy, and the
    sale of a line whose shares differ. rates are the day's pounds per unit of each currency.
    Nothing is sent for a day that is over: its record made, or a later fill in the ledger.
    Every signal has its answer, each not filled whole on the morning's list (halt.morning) under
    its blocker, with the lines no rule could decide; the desk dying leaves none unlisted
    (_unreached). A place the broker disagrees with is told through tell (book.send). A position
    the desk did not make is sold first (_strangers).
    A strategy in killed (its own kill condition met, lab/promotion.py) buys nothing, said so;
    what it holds is still sold by its rule or its stop."""
    book.collect(root, broker)  #: the stops the open sold
    if later := max((fill.day for fill in book.fills(root) if fill.day > day), default=None):
        raise ValueError(f"{day}: the day is over, the ledger holding a fill of {later}")
    if made := [record.day for record in records(root) if record.day >= day]:
        raise ValueError(f"{day}: the day is over, the records running to {made[-1]}")
    book.record_rates(root, day, rates)
    taken = _strangers(root, archive, broker, settings, day, tell)
    held = book.positions(root)
    buys = {f.symbol: strategy_of(f.order_id) for f in book.fills(root) if f.quantity > 0}
    holders = {symbol: h for symbol, h in buys.items() if h != "stranger"}
    due = {line.symbol: line for line, bars in archive.items() if _due(line, bars, day)}
    unpriced = sorted({line.currency for line in due.values()} - set(rates))
    if unpriced:
        raise ValueError(f"{day}: no rate in pounds for {unpriced}; nothing sent")
    _unread(root, tuple(archive), due, day)
    decided = strategy.today(
        {symbol: archive[line] for symbol, line in due.items()},
        {symbol: holders[symbol] for symbol in held if symbol in due and symbol in holders},
    )
    sent = list[book.Sent]()
    try:
        _orders(root, broker, settings, day, tell, killed, decided, due, archive, rates, sent)
    except (Crash, book.Alarm) as dead:
        _unreached(root, day, decided, sent, dead)
        raise
    return (*taken, *sent)


def _orders(
    root: Path,
    broker: Broker,
    settings: Settings,
    day: date,
    tell: book.Tell | None,
    killed: frozenset[str],
    decided: Sequence[Decision],
    due: Mapping[str, Line],
    archive: Mapping[Line, Sequence[Bar]],
    rates: Mapping[str, Decimal],
    sent: list[book.Sent],
) -> None:
    """The sales, then the buys, each answer added to sent as it is given."""
    held = book.positions(root)
    for d in (d for d in decided if d.action is Action.SELL):  #: by the rule that holds it
        sale = Sale(order_id_of(d), due[d.symbol], held[d.symbol])
        sent.append(_answer(root, day, _send(root, broker, sale, settings, tell, None)))
    for d in (d for d in decided if d.action is Action.BUY):
        line = due[d.symbol]
        price = archive[line][-1].close, rates[line.currency]
        barred = _barred(d) if d.strategy in killed else None
        bought = barred or _buy(root, broker, d, line, price, settings, day, tell)
        sent.append(_answer(root, day, bought))


def _unreached(
    root: Path, day: date, decided: Sequence[Decision], sent: Sequence[book.Sent], dead: Exception
) -> None:
    """NO SIGNAL HALF-PROCESSED (TST-08): each signal still without an answer when the desk died
    goes on the morning's list, saying so; it is decided again when the desk starts."""
    answered = {s.order_id for s in sent}
    why = f"not reached, the desk stopped on {type(dead).__name__}: {dead}"
    names = (order_id_of(d) for d in decided if d.action is not Action.HOLD)
    halt.note(
        root,
        day,
        [halt.Blocked(n, Blocker.BROKER, 0, f"{n}: {why}") for n in names if n not in answered],
    )


def _strangers(
    root: Path,
    archive: Mapping[Line, Sequence[Bar]],
    broker: Broker,
    settings: Settings,
    day: date,
    tell: book.Tell | None,
) -> list[book.Sent]:
    """THE POSITIONS THE DESK DID NOT MAKE (TRD-06): each is named (told, and on the morning's
    list when it cannot be sold), taken into the book at its line's last close, and sold at the
    market, answered like any sale. A name in no line of the desk's is left for a hand."""
    lines, sold, found = (
        {line.symbol: line for line in archive},
        [],
        dict(book.strangers(root, broker)),
    )
    listed = halt.morning(root, day).values() if halt.stopped(root, day) is not None else ()
    old = [b.order_id for blocked in listed for b in blocked if "-stranger-" in b.order_id]
    idle = [b.order_id for blocked in listed for b in blocked if "not reached" in b.reason]
    halt.note(root, day, (), idle + [i for i in old if i.split("-stranger-")[1] not in found])
    for name, shares in found.items():
        tell and tell("stranger", f"{name}: {shares} shares the desk did not buy; selling them")
        if (line := lines.get(name)) and archive[line]:
            book.adopt(root, line, shares, archive[line][-1].close, day)
        else:
            why = f"{name}: {shares} shares the desk did not buy, in no line it has bars for"
            halt.note(
                root, day, [halt.Blocked(f"{day:%Y%m%d}-stranger-{name}", Blocker.BOOK, 0, why)]
            )
    mine = [f for f in book.fills(root) if strategy_of(f.order_id) == "stranger"]
    for name in sorted({f.symbol for f in mine} & lines.keys()):  #: those a sale left whole too
        if (shares := sum(f.quantity for f in mine if f.symbol == name)) > 0:
            sale = Sale(f"{day:%Y%m%d}-stranger-{name}", lines[name], shares)
            sold.append(_answer(root, day, _send(root, broker, sale, settings, tell, None)))
    return sold


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
    return _send(root, broker, order, settings, tell, standing(root, day))


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
) -> book.Sent:
    """Send through the one door; its refusal is the order's answer, kept with the day's
    under the blocker the send path names; one it does not name is the broker's own door's."""
    try:
        return book.send(root, broker, order, settings, tell, held)
    except Stopped as stopped:
        return book.Sent(order.order_id, 0, str(stopped), stopped.blocker)
    except Refused as refused:
        return book.Sent(order.order_id, 0, str(refused), Blocker.BROKER)


def _due(line: Line, bars: Sequence[Bar], day: date) -> bool:
    """The line's venue trades on day and its last bar is the session before: decisions
    dated any other day are not acted on."""
    return bool(bars) and venues.sessions(line.venue, bars[-1].day, day) == (bars[-1].day, day)
