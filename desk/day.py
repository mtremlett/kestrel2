"""day - THE DESK'S DAY: decide on the bars before it, size, send, and at its end reconcile
and publish one record. The same days run again from the same saved data give the same records."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, localcontext
from functools import partial
from pathlib import Path

from desk import book, day_money, halt, handpark, intraday, paper, restop, strategy, venues
from desk.broker import Broker, Crash, Restopping
from desk.day_parts import HEADER as HEADER
from desk.day_parts import RECORDS as RECORDS
from desk.day_parts import Record as Record
from desk.day_parts import _alert as _alert
from desk.day_parts import _bare as _bare
from desk.day_parts import _barred as _barred
from desk.day_parts import _due as _due
from desk.day_parts import _row as _row
from desk.day_parts import _unreached as _unreached
from desk.day_parts import _unread as _unread
from desk.day_parts import _watch as _watch
from desk.day_parts import records as records
from desk.day_parts import standing as standing
from desk.halt import Blocker, Stopped
from desk.lines import YARDSTICK, Line
from desk.orders import (
    ZOO,
    ZOO_ROOM,
    Order,
    Refused,
    Sale,
    Settings,
    gapped,
    is_zoo,
    order_id_of,
    pennies,
    size,
    stop_under,
    strategy_of,
    traded_value,
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
    strangers: bool = False,
) -> Record:
    """A whole day from the data saved by its end, the day's own bars in it: its orders are
    decided on the bars before the day alone, each stop is moved under its fill (restop), and
    then its record is published."""
    seen = {line: tuple(bar for bar in bars if bar.day < day) for line, bars in archive.items()}
    trade(root, seen, broker, settings, day, rates, strangers=strangers)
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
    worth = day_money.worth(root, archive, day)
    market = (
        day_money.close(archive, YARDSTICK, day) / day_money.close(archive, YARDSTICK, since) - 1
    )
    profit = None if differ else pennies(worth - opened + cash - costs.total)
    held = pennies(settings.capital * market)
    halts = tuple(h.at for h in halt.on(root, day)), halt.stopped(root, day)
    heat = day_money.heat(root, archive, day)
    split = day_money.fx_split(root, archive, day)
    earned = day_money.idle_interest(root, archive, day, settings.capital, RISK_FREE)
    fx = None if split is None else pennies(split[0] + split[2])
    interest = None if earned is None else pennies(earned)
    record = Record(
        day, profit, costs.published(), held, differ, worth, len(ledger), *halts, heat, fx, interest
    )
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
    strangers: bool = False,
    zoo: bool = False,
) -> tuple[book.Sent, ...]:
    """The day's orders, after the market opens: each rule's decision on the session before, its
    position read from the book; the sales first, then each buy sized from the book after the send
    before it. A line sold this morning, by its rule or its stop, is not bought again today. While
    the book is not the broker's the send path refuses every buy, and the sale of a line whose
    shares differ. rates are the day's pounds per unit of each currency. Nothing is sent for a day
    that is over: its record made, or a later fill in the ledger. Every signal has its answer, each
    not filled whole on the morning's list (halt.morning) under its blocker, with the lines no rule
    could decide; the desk dying leaves none unlisted (_unreached). A place the broker disagrees
    with is told through tell (book.send). A position the desk did not make is sold first
    (_strangers), when strangers is set: the step's scripted wire (desk/running.py) has no room yet
    for the broker's holdings read it needs. A strategy in killed (its own kill condition met,
    lab/promotion.py) buys nothing, said so; what it holds is still sold by its rule or its stop.
    The zoo trades after the desk (_zoo, its paper switch), selling first a line the desk buys."""
    _stand_down(root, archive, broker, settings, tell)
    if later := max((fill.day for fill in book.fills(root) if fill.day > day), default=None):
        raise ValueError(f"{day}: the day is over, the ledger holding a fill of {later}")
    if made := [record.day for record in records(root) if record.day >= day]:
        raise ValueError(f"{day}: the day is over, the records running to {made[-1]}")
    book.record_rates(root, day, rates)
    taken = _strangers(root, archive, broker, settings, day, tell) if strangers else []
    held, holders = book.positions(root), _holders(root)
    due = {line.symbol: line for line, bars in archive.items() if _due(line, bars, day)}
    if unpriced := sorted({line.currency for line in due.values()} - set(rates)):
        raise ValueError(f"{day}: no rate in pounds for {unpriced}; nothing sent")
    _unread(root, tuple(archive), due, day)
    decided = strategy.today(
        {symbol: archive[line] for symbol, line in due.items()},
        {symbol: holders[symbol] for symbol in held if symbol in due and symbol in holders},
        opened={f.symbol: f.day for f in book.fills(root) if f.quantity > 0},
    )
    sent = list[book.Sent]()
    try:
        _orders(root, broker, settings, day, tell, killed, decided, due, archive, rates, sent)
        sent += _zoo(root, broker, day, tell, due, archive, rates, sent) if zoo else []
    except (Crash, book.Alarm) as dead:
        _unreached(root, day, decided, sent, dead)
        raise
    return (*taken, *sent)


def _stand_down(
    root: Path,
    archive: Mapping[Line, Sequence[Bar]],
    broker: Broker,
    settings: Settings,
    tell: book.Tell | None,
) -> None:
    """STP-10: a stop that sold, since the last record, at a loss past GAP_LOSS of the capital
    (orders.gapped) halts buying, once for each such sale, until he lifts it. The loss is read
    from the stop's fill against its buy's price, in the pounds of the buy's day."""
    book.collect(root, broker)  #: the stops the open sold
    lines, fills = {line.symbol: line for line in archive}, book.fills(root)
    buys, since = (
        {f.order_id: f for f in fills if f.quantity > 0},
        max((r.day for r in records(root)), default=date.min),
    )
    for sale in fills:
        buy = buys.get(sale.order_id.removesuffix("-stop"))
        if sale.quantity >= 0 or sale.day <= since or buy is None or sale.symbol not in lines:
            continue
        line = lines[sale.symbol]
        priced = Order(
            buy.order_id,
            line,
            -sale.quantity,
            buy.price,
            book.rate(root, line.currency, buy.day),
            stop_under(line, buy.price),
        )
        why = f"{sale.order_id}: the stop sold at {sale.price}, a gap past the loss limit"
        if gapped(priced, sale.price, settings) and why not in {h.why for h in halt.kept(root)}:
            halt.stop(root, broker, datetime.now(UTC), why, by="gap")
            if tell:
                tell(f"gap {sale.order_id}", f"{why}. Buying is halted until he lifts it.")


def _holders(root: Path) -> dict[str, str]:
    """Each line's last buyer among the desk's strategies; a stranger's buy holds for none."""
    buys = {f.symbol: strategy_of(f.order_id) for f in book.fills(root) if f.quantity > 0}
    return {symbol: h for symbol, h in buys.items() if h != "stranger"}


#: BIC-05, AG-05: the pounds the book may stand below its highest point (his "£1,500").
PEAK_FALL = Decimal(1500)


def _peak_fall(root: Path, day: date, tell: book.Tell | None) -> None:
    """ON PAPER A FALL FROM THE BOOK'S HIGHEST POINT PAST PEAK_FALL IS TOLD TO HIM (BIC-05): the
    profits of the records so far, summed, against their highest running total. Alert only."""
    total = peak = Decimal(0)
    for record in records(root):
        total += record.profit or Decimal(0)
        peak = max(peak, total)
    if tell is not None and peak - total > PEAK_FALL:
        tell(
            f"peak fall {day}",
            f"DRAWDOWN ALERT: £{peak - total} below its highest; paper, trading on.",
        )


def _currency(
    root: Path, archive: Mapping[Line, Sequence[Bar]], day: date, tell: book.Tell | None
) -> None:
    """BIC-04: what the closed trades so far owe to the currency's move, told apart from what
    they made by trading, and what the open holdings owe it; told only when there is some."""
    if tell is None:
        return
    split = day_money.fx_split(root, archive, day)
    if split is None:
        return  #: nothing has traded, or a fill's day's rate was never kept
    gain, trading, held = split
    if gain or held:
        tell(
            f"currency {day}",
            f"CURRENCY: £{gain} of the gross is the currency, £{trading} trading; "
            f"£{held:.2f} on open holdings.",
        )


#: BIC-03: the yearly rate idle cash is told to earn, and the Sharpe's risk-free rate (4%).
RISK_FREE = Decimal("0.04")


def _interest(
    root: Path,
    archive: Mapping[Line, Sequence[Bar]],
    day: date,
    settings: Settings,
    tell: book.Tell | None,
) -> None:
    """BIC-03: what the capital's idle cash earned at RISK_FREE from the first fill to this day,
    told once a day beside the profit, not in it: the day's profit must equal the ledger's and
    the broker's (day_parts reconcile), which interest is in neither. Only when positive."""
    if tell is None:
        return  #: nobody to tell: the sum (a read of every fill's day) is not made
    earned = day_money.idle_interest(root, archive, day, settings.capital, RISK_FREE)
    if earned is not None and earned > 0:
        first = min(f.day for f in book.fills(root))
        tell(f"interest {day}", f"INTEREST: £{earned:.2f} earned on idle cash since {first}.")


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
    """The sales, the zoo's yields (_yields), then the buys, each answer added to sent."""
    held = book.positions(root)
    for d in (d for d in decided if d.action is Action.SELL):  #: by the rule that holds it
        sale = Sale(order_id_of(d), due[d.symbol], held[d.symbol], session=d.day)
        made = book.intend(
            root, sale.order_id, (d.strategy, d.symbol, d.day), archive[sale.line][-1]
        )
        answer = _answer(root, day, _send(root, broker, sale, settings, tell, None))
        book.chain(root, made, answer)
        sent.append(answer)
    sent += _yields(root, broker, settings, tell, decided, due)  #: none without the zoo
    _alert(root, day, settings, tell)
    _peak_fall(root, day, tell)
    _currency(root, archive, day, tell)
    _interest(root, archive, day, settings, tell)
    watch = partial(_watch, root, archive, rates)  #: read again at each buy
    for d in (d for d in decided if d.action is Action.BUY):
        line = due[d.symbol]
        price = archive[line][-1].close, rates[line.currency]
        args = (root, broker, d, line, price, settings, day, tell, watch, archive[line])
        made = book.intend(root, order_id_of(d), (d.strategy, d.symbol, d.day), archive[line][-1])
        answer = _answer(root, day, _barred(d) if d.strategy in killed else _buy(*args))
        book.chain(root, made, answer)
        sent.append(answer)


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
            sale = Sale(f"{day:%Y%m%d}-stranger-{name}", lines[name], shares, session=day)
            made = book.intend(root, sale.order_id, ("stranger", name, day), archive[sale.line][-1])
            sold.append(_answer(root, day, _send(root, broker, sale, settings, tell, None)))
            book.chain(root, made, sold[-1])
    return sold


def _answer(root: Path, day: date, sent: book.Sent) -> book.Sent:
    """An order's answer, put on the morning's list if it was blocked and taken off if not."""
    if sent.blocker is None or sent.reason is None:
        halt.note(root, day, (), (sent.order_id,))
    else:
        blocked = halt.Blocked(sent.order_id, sent.blocker, sent.filled, sent.reason)
        halt.note(root, day, (blocked,))
    return sent


def refusal(
    root: Path, name: str, line: Line, held: Mapping[str, int]
) -> tuple[str, Blocker] | None:
    """THE ONE HOME of a buy's refusals before sizing, daily or intraday (R-RUNNER-436): a line
    no ISA can hold (line.isa no) or no retail customer may buy (line.retail no), one parked by
    hand, or one held already; each said with its blocker. None: the buy may be sized."""
    if line.isa is False or line.retail is False:
        why = (
            "is recorded as a line no stocks and shares ISA can hold"
            if line.isa is False
            else "is recorded as a line no UK retail customer may buy"
        )
        return f"{name}: not sent, {line.symbol} {why}", Blocker.GATE
    if hand := handpark.parked(root).get(line.symbol):
        return f"{name}: not sent, parked by hand: {line.symbol} ({hand})", Blocker.GATE
    if held.get(line.symbol):
        return f"{name}: not sent, {line.symbol} is held already", Blocker.HELD
    return None


def _buy(
    root: Path,
    broker: Broker,
    d: Decision,
    line: Line,
    price: tuple[Decimal, Decimal],
    settings: Settings,
    day: date,
    tell: book.Tell | None,
    watch: Callable[[str], tuple[dict[str, Decimal], dict[str, tuple[float, ...]]]] | None = None,
    bars: Sequence[Bar] = (),
) -> book.Sent:
    """One rule's buy, sized from the book as the send before it left it, at the line's last
    close and the day's rate. A line held, or sold this morning, is not bought: said so. Nor is
    one an ISA is not recorded as able to hold (line.isa no): the ISA buys only those; nor one no
    retail customer may buy (line.retail no), which the broker would only refuse, slowly."""
    now, name = book.positions(root), order_id_of(d)
    if no := refusal(root, name, line, now):
        return book.Sent(name, 0, *no)
    if d.symbol in _sold(root, day, False):
        return book.Sent(
            name, 0, f"{name}: not sent, {d.symbol} was sold this morning", Blocker.HELD
        )
    try:
        order = size(d, line, *price, settings, now, None, traded_value(bars, price[1]))
    except Refused as refused:  #: the gate's answer, kept with the day's others
        return book.Sent(name, 0, str(refused), Blocker.GATE)
    looked = watch and watch(d.symbol)
    return _send(
        root, broker, order, settings, tell, standing(root, day), *(looked or (None, None))
    )


def _send(
    root: Path,
    broker: Broker,
    order: Order | Sale,
    settings: Settings,
    tell: book.Tell | None,
    held: Standing | None,
    pounds: Mapping[str, Decimal] | None = None,
    moves: Mapping[str, tuple[float, ...]] | None = None,
) -> book.Sent:
    """Send through the one door; its refusal is the order's answer, kept with the day's
    under the blocker the send path names; one it does not name is the broker's own door's."""
    try:
        sent = book.send(root, broker, order, settings, tell, held, pounds, moves)
    except Stopped as stopped:
        sent = book.Sent(order.order_id, 0, str(stopped), stopped.blocker)
    except Refused as refused:
        sent = book.Sent(order.order_id, 0, str(refused), Blocker.BROKER)
    return replace(sent, asked=order.quantity)


def _sold(root: Path, day: date, zoo: bool) -> set[str]:
    """The lines one side (orders.is_zoo) sold on day, by its rule or its stop."""
    return {
        f.symbol
        for f in book.fills(root)
        if f.day == day and f.quantity < 0 and is_zoo(f.order_id) == zoo
    }


def _yields(
    root: Path,
    broker: Broker,
    settings: Settings,
    tell: book.Tell | None,
    decided: Sequence[Decision],
    due: Mapping[str, Line],
) -> list[book.Sent]:
    """THE ZOO YIELDS (his 22 Nov ruling): a line a rule of the desk's buys today that a zoo rule
    holds is sold out of the zoo first, under the zoo rule's own id, so the desk's five trade as
    if the zoo were not there. No zoo holding: nothing is sent."""
    held, holders, sold = book.positions(root), _holders(root), list[book.Sent]()
    wanted = {d.symbol: d.day for d in decided if d.action is Action.BUY and d.symbol in held}
    for symbol, on in wanted.items():  #: once a line, dated as the buy: the paper door's session
        if (holder := holders.get(symbol, "")).startswith(ZOO):
            zoo = order_id_of(Decision(holder, symbol, on, Action.SELL))
            sale = Sale(zoo, due[symbol], held[symbol], session=on)
            sold.append(_send(root, broker, sale, settings, tell, None))
    return sold


def _zoo(
    root: Path,
    broker: Broker,
    day: date,
    tell: book.Tell | None,
    due: Mapping[str, Line],
    archive: Mapping[Line, Sequence[Bar]],
    rates: Mapping[str, Decimal],
    desks: Sequence[book.Sent],
) -> list[book.Sent]:
    """THE ZOO'S DAILY ROUND, A MACHINERY TEST, NOT EVIDENCE OF AN EDGE (his 22 Nov ruling): after
    the desk's own orders, each zoo daily rule (intraday.ZOO_DAILY) decides on each zoo line due
    today, holding what it bought; a sale sells it, a buy is one share, refused as the desk's are,
    through the one gate on the zoo's own allowance (ZOO_ROOM, standing of the zoo alone). Only
    paper.MAX_ORDERS in all go to the broker, the desk's own (desks) first; the rest are kept in the
    day's answers as carried to the next step, never sent."""
    room = paper.MAX_ORDERS - sum(1 for s in desks if s.asked)
    lines = sorted({ln.symbol for ln in intraday.zoo_lines()} & due.keys())
    held, holders, sent = book.positions(root), _holders(root), list[book.Sent]()
    opened = {f.symbol: f.day for f in book.fills(root) if f.quantity > 0}
    for name, rule in intraday.ZOO_DAILY.items():
        for symbol in lines:
            line, last = due[symbol], symbol in held and holders.get(symbol) == name
            with localcontext(strategy.ARITHMETIC):
                *_, d = strategy._run(name, rule(), symbol, archive[line], last, opened.get(symbol))
            if d.action is Action.HOLD:
                continue
            if room <= 0:
                words = f"{order_id_of(d)}: not sent, carried to the next step (the step's time)"
                sent.append(book.Sent(order_id_of(d), 0, words, Blocker.CARRIED))
                continue
            made = book.intend(
                root, order_id_of(d), (d.strategy, d.symbol, d.day), archive[line][-1]
            )
            if d.action is Action.SELL:
                sale = Sale(order_id_of(d), line, held[symbol], session=d.day)
                answer = _send(root, broker, sale, ZOO_ROOM, tell, None)
            else:
                close = archive[line][-1].close, rates[line.currency]
                answer = _zoo_buy(root, broker, d, line, close, day, tell)
            book.chain(root, made, answer)
            sent.append(answer)
            room -= 1 if answer.asked else 0
    return sent


def _zoo_buy(
    root: Path,
    broker: Broker,
    d: Decision,
    line: Line,
    price: tuple[Decimal, Decimal],
    day: date,
    tell: book.Tell | None,
) -> book.Sent:
    """A zoo rule's buy: one share, never the room, refused as the desk's own buy is."""
    held, name = book.positions(root), order_id_of(d)
    if no := refusal(root, name, line, held):
        return book.Sent(name, 0, *no)
    if d.symbol in _sold(root, day, True) | _sold(root, day, False):
        return book.Sent(
            name, 0, f"{name}: not sent, {d.symbol} was sold this morning", Blocker.HELD
        )
    try:
        order = replace(size(d, line, *price, ZOO_ROOM, held), quantity=1)
    except Refused as refused:
        return book.Sent(name, 0, str(refused), Blocker.GATE)
    return _send(root, broker, order, ZOO_ROOM, tell, standing(root, day, True))
