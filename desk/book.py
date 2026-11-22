"""book - THE LEDGER AND THE BOOK. Fills are written under the broker's own ids; the book is
their sum, and reconciling compares it with the broker's positions. The send path keeps the kill
switch's record, sends nothing while it is on, notes each order, and cancels what a dead desk
left working. Conformance trades are a cost of their own (conformance_cost)."""

from __future__ import annotations

import csv
from collections import Counter, deque
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import astuple, dataclass, replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from desk import halt
from desk.book_parts import (
    CANCELS,
    RATES,
    SWITCH,
    TURNS,
    Switch,
    cancel_all,
    entry,
    keep,
    killed,
    rate,
    record_rates,
    retry_id,
    switch,
)
from desk.book_parts import (
    rates_kept as rates_kept,
)
from desk.book_parts import (
    unless_killed as _unless_killed,
)
from desk.book_parts2 import (
    COLUMNS,
    LEDGER,
    LEVELS,
    STOPS,
    _record,
    adopt,
    fills,
    found,
    levels,
)
from desk.broker import Broker, Crash, Disconnected, Fill, Report
from desk.halt import Blocker, Stopped
from desk.lines import Line
from desk.orders import (
    Charges,
    Order,
    Refused,
    Sale,
    Settings,
    charges,
    gate,
    is_zoo,
    leg_of,
    strategy_of,
)
from desk.risk import Standing
from desk.store import Bar

#: what moved to desk.book_parts and desk.book_parts2 and is still given from here, for the callers
__all__ = (
    "COLUMNS",
    "LEDGER",
    "LEVELS",
    "RATES",
    "STOPS",
    "SWITCH",
    "TURNS",
    "Switch",
    "CANCELS",
    "cancel_all",
    "_record",
    "adopt",
    "fills",
    "found",
    "keep",
    "killed",
    "levels",
    "rate",
    "record_rates",
    "switch",
)
GOING = "going.csv"  #: the order at the broker's door, until the desk has its answer


def turn(root: Path, to: Switch, at: datetime, why: str) -> None:
    """Write on the kill switch's record what happened to it, when (UTC), and why."""
    record = (*switch(root), entry(at, to, why))
    keep(root / SWITCH, [TURNS, *((t.isoformat(), s.value, w) for t, s, w in record)])


class Alarm(Exception):
    """The broker's place failed in a way the desk does not know: the kill switch is on."""


@dataclass(frozen=True)
class Sent:
    order_id: str
    filled: int
    reason: str | None  #: why it did not fill completely; None only when it did
    blocker: Blocker | None = None  #: what stood in its way: named with the reason, or neither

    def __post_init__(self) -> None:
        if (self.reason is None) != (self.blocker is None):
            raise ValueError(f"{self.order_id}: {self.reason!r} with the blocker {self.blocker}")


@dataclass(frozen=True)
class RoundTrip:
    buy: Fill
    sell: Fill
    gross: Decimal  #: pounds, before costs
    costs: Charges  #: pounds, every cost of both legs, line by line
    profit: Decimal  #: pounds, gross less every cost


@dataclass(frozen=True)
class Difference:
    """One entry of a broker's that is not the desk's book."""

    name: str  #: what is held, in the words the book and the broker's entries share
    broker: Decimal | int  #: the shares the broker's entry gives; 0 when it gives no entry
    book: int  #: the shares the desk's book holds of it; 0 when it holds none


Tell = Callable[[str, str], None]  #: the door to his phone: a message's name, then its words
Reckoning = tuple[dict[str, int], tuple[str, ...], set[str], tuple[Difference, ...]]


def side(root: Path, held: Mapping[str, int], order_id: str) -> dict[str, int]:
    """THE ZOO STANDS APART (his 22 Nov ruling): of the lines held, those of the order's own side,
    the zoo's (orders.is_zoo) or the desk's, by the side of each line's last buy (a line with no
    buy of the desk's records is the desk's). The gate counts a buy's holdings and room by it; a
    sale (its rule's, a stop's or go flat's) meets the whole book, so every share can be sold."""
    owner = {f.symbol: is_zoo(f.order_id) for f in fills(root) if f.quantity > 0}
    zoo = is_zoo(order_id)
    return {symbol: shares for symbol, shares in held.items() if owner.get(symbol, False) == zoo}


def send(
    root: Path,
    broker: Broker,
    order: Order | Sale,
    settings: Settings,
    tell: Tell | None = None,
    standing: Standing | None = None,
    exposure: Mapping[str, Decimal] | None = None,
    moves: Mapping[str, tuple[float, ...]] | None = None,
) -> Sent:
    """Ask the broker what it did with the order's id, so a desk that restarts never sends it
    twice; if it never received it, gate it and send it. Fills are recorded, a buy's stop rests
    at the broker. Where the book is not the broker's nothing is bought, and a line sells only if
    its shares agree. Kill switch on: nothing is sent; a halt: no buy. Every refusal names its
    blocker (Stopped), as does a short answer. A place that fails unknown pulls the kill switch
    (Alarm); one that disagrees halts buying and is told (tell). Given the book's standing the gate
    also refuses a buy past a loss limit or the day's new lines, and, given the pounds controlled
    per underlying (exposure), one past its market's cap, and given the daily returns of the line
    and the lines held (moves), one correlated with a held line past the cap (orders.gate)."""
    _settle(root, broker)
    report = broker.report(order.order_id)
    if again := retry_id(root, order.order_id, report, datetime.now(UTC).date()):
        order, report = replace(order, order_id=again), broker.report(again)  #: once, same gate
    if report is None:
        _unless_stopped(root, order)
        held, differ, unsure, _ = _compare(root, broker)
        if differ and (isinstance(order, Order) or order.line.symbol in unsure):
            words = f"{order.order_id}: not sent, the book is not the broker's on {list(differ)}"
            raise Stopped(Blocker.BOOK, words)
        try:
            mine = held if isinstance(order, Sale) else side(root, held, order.order_id)
            gate(order, settings, mine, standing, exposure, moves)
        except Refused as refused:
            raise Stopped(Blocker.GATE, str(refused)) from refused
        _unless_stopped(root, order)  #: read again, at the last moment before it goes
        try:
            report = _place(root, broker, order, tell)
        except Disconnected as lost:  #: never received: stated, and sent again next time
            return Sent(order.order_id, 0, str(lost), Blocker.BROKER)
    collect(root, broker)  #: a stop sold on the day of its buy is in no answer
    filled, short = sum(abs(f.quantity) for f in report.fills), report.reason is not None
    return Sent(order.order_id, filled, report.reason, Blocker.BROKER if short else None)


def _place(root: Path, broker: Broker, order: Order | Sale, tell: Tell | None) -> Report:
    """The order goes to the broker, the desk's note of it kept until it has the last answer."""
    going = root / GOING
    name, kept = f"{order.order_id}-stop", levels(root)  #: the broker may lose a buy's stop
    if isinstance(order, Order) and name not in kept:
        keep(root / STOPS, [LEVELS, *kept.items(), (name, order.stop)])
    keep(going, [(order.order_id,)])
    try:
        report = broker.place(order)
    except Refused:
        going.unlink()
        raise
    except Disconnected:  #: whether the broker received it is unknown: the note stays for _settle
        raise
    except Crash:
        raise
    except Exception as error:  # noqa: BLE001 - unknown: the desk does not guess; _disagreed alarms
        report = _disagreed(root, broker, order, error, tell)
    going.unlink()
    return report


def _disagreed(
    root: Path, broker: Broker, order: Order | Sale, error: Exception, tell: Tell | None
) -> Report:
    """THE BROKER'S WORD, FILLS AND ACCOUNT DO NOT AGREE after the order has gone (R-PAPER-11,
    Unprotected): buying is halted until he lifts it, he is told (tell), and the broker's report
    is given, so the order is never sent again. Else the kill switch is pulled, Alarm raised."""
    from desk import placing  # noqa: PLC0415 - placing reaches book through paper: a load cycle

    if tell is None or not isinstance(error, placing.Unprotected):
        words = f"{order.order_id}: place failed with {error!r}; the kill switch is on"
        turn(root, Switch.ON, datetime.now(UTC), words)
        cancel_all(root, broker, datetime.now(UTC).date())
        raise Alarm(words) from error
    words = f"{order.order_id}: the broker's word, fills and account do not agree: {error}"
    why = f"{words}; no buy goes until he lifts this"
    halt.stop(root, broker, datetime.now(UTC), why, by="send path")
    tell(f"disagree {order.order_id}", f"{words}. Buying is halted; sales go on.")
    return broker.report(order.order_id) or Report(order.order_id, (), words)


def _settle(root: Path, broker: Broker) -> None:
    """A DESK THAT DIED MID-SEND left its note (_place) and perhaps an order working, to fill
    behind a gate that counts the book alone: before any send they go. Kill switch on: waits."""
    if (going := root / GOING).exists() and killed(root) is None:
        cancel_all(root, broker, datetime.now(UTC).date())
        going.unlink()


def _unless_stopped(root: Path, order: Order | Sale) -> None:
    """Refuse the order while the kill switch is on, and a buy while a halt is in force."""
    _unless_killed(root, order.order_id)
    if isinstance(order, Order) and (halts := halt.in_force(root)):
        said = "; ".join(h.since for h in halts)
        raise Stopped(Blocker.HALT, f"{order.order_id}: not sent, a halt is in force, {said}")


_write = keep  # old name, for other lanes' callers until they move


def strangers(root: Path, broker: Broker) -> tuple[tuple[str, int], ...]:
    """THE POSITIONS THE DESK DID NOT MAKE: each name the broker holds more shares of than
    the book, and those shares (whole ones; a part share is for a hand to look at)."""
    more = differences(positions(root), broker.holdings())
    return tuple((d.name, int(d.broker) - d.book) for d in more if d.broker > d.book)


def collect(root: Path, broker: Broker) -> None:
    """Write in the ledger every fill the broker gives that it lacks."""
    _record(root, broker.fills())


def reconcile(root: Path, broker: Broker) -> tuple[str, ...]:
    """The lines on which the book is not the broker's: shares differ, or the stop is not theirs."""
    return _compare(root, broker)[1]


def _compare(root: Path, broker: Broker) -> Reckoning:
    """One reading: the book, the names it is not the broker's on, those whose shares differ,
    the stops that are not the book's. The broker is asked fills, stops, holdings in that order,
    so a stop that sells between the last two shows as shares gone, never still there."""
    collect(root, broker)
    ours = positions(root)
    stops = differences(ours, broker.stops())
    shares = {d.name for d in differences(ours, broker.holdings())}
    return ours, tuple(sorted(shares | {d.name for d in stops})), shares, stops


def reckon(root: Path, broker: Broker, on: date | None = None) -> Reckoning:
    """The book, the lines that differ, those whose shares do, the stops that do: one reading.
    Given a day, its differing lines also name the strangers the desk met on it (adopted): that
    day's book was not the broker's this morning, whatever the sale did."""
    held, differ, unsure, stops = _compare(root, broker)
    return held, tuple(sorted({*differ, *adopted(root, on)})), unsure, stops


def adopted(root: Path, on: date | None) -> set[str]:
    """The lines on which the desk took in a position it did not make, on that day."""
    return {f.symbol for f in fills(root) if f.day == on and f.execution_id.startswith("stranger-")}


def differences(
    held: Mapping[str, int], entries: Iterable[tuple[str, Decimal | int]]
) -> tuple[Difference, ...]:
    """THE BOOK AGAINST A BROKER: the one comparison of its holdings or resting stops. held is
    the book; entries are the broker's (name, shares), which must be the book's own: shares in
    two entries are never one line. A name the book holds and the broker omits has no shares;
    one listed at none is not held. None named: they agree."""
    rows = list(entries)
    places = Counter(name for name, shares in rows if shares)
    rows += [(name, 0) for name in held.keys() - {name for name, _ in rows}]
    return tuple(
        Difference(name, shares, held.get(name, 0))
        for name, shares in sorted(rows)
        if shares != held.get(name, 0) or (shares and places[name] > 1)
    )


def positions(root: Path, upto: date = date.max) -> dict[str, int]:
    """What the desk holds, or held at a day's end: its ledger's fills added up, line by line."""
    held: dict[str, int] = {}
    for fill in fills(root):
        if fill.day <= upto:
            held[fill.symbol] = held.get(fill.symbol, 0) + fill.quantity
    if short := sorted(symbol for symbol, shares in held.items() if shares < 0):
        raise ValueError(f"the ledger sells more than it bought of {short}: the desk is long only")
    return {symbol: shares for symbol, shares in sorted(held.items()) if shares}


def dealt(
    root: Path, lines: Iterable[Line], day: date, last: date, counted: int
) -> tuple[Decimal, Charges]:
    """A DAY'S DEALING, in pounds: sales less buys and every cost of the fills its record is the
    first to count: those dated after the last record's day, and any that came late."""
    pounds, ledger = _priced(root, lines), fills(root)
    old = [fill for fill in ledger if fill.day <= last]
    if len(old) < counted:
        raise ValueError(f"the ledger holds {len(old)} fills by {last}, fewer than the {counted}")
    cash, costs = Decimal(0), Charges(*(Decimal(0),) * 5)
    for fill in old[counted:] + [fill for fill in ledger if last < fill.day <= day]:
        value, fee = pounds(fill, abs(fill.quantity))
        cash, costs = cash + (value if fill.quantity < 0 else -value), costs + fee
    return cash, costs


def _priced(root: Path, lines: Iterable[Line]) -> Callable[[Fill, int], tuple[Decimal, Charges]]:
    """How the ledger's fills are priced in pounds: at the day's kept rate, by the cost model."""
    known, rates = {line.symbol: line for line in lines}, rates_kept(root)
    if unknown := sorted({fill.symbol for fill in fills(root)} - set(known)):
        raise ValueError(f"the ledger trades lines the desk was not given: {unknown}")

    def pounds(fill: Fill, shares: int) -> tuple[Decimal, Charges]:
        """The fill's value and its share of the fill's costs, both for shares, in pounds."""
        line = known[fill.symbol]
        fx = rates.get((fill.day, line.currency))
        if fx is None:
            raise ValueError(f"{fill.execution_id}: no {line.currency} rate kept for {fill.day}")
        leg, whole = leg_of(fill.order_id, fill.quantity), abs(fill.quantity)
        fee = charges(line, leg, whole, fill.price, fx).part(shares, whole)
        return fill.price * shares * fx, fee

    return pounds


def conformance_cost(root: Path, lines: Iterable[Line]) -> Decimal:
    """THE CONFORMANCE COST, apart from the desk's profit: the ledger's money moved, less costs."""
    moved, costs = dealt(root, lines, date.max, date.min, 0)
    return moved - costs.total


def round_trips(root: Path, lines: Iterable[Line]) -> tuple[RoundTrip, ...]:
    """Each sale matched with the buys it closes, oldest first, in pounds after every cost."""
    pounds = _priced(root, lines)
    opened: dict[str, deque[tuple[Fill, int]]] = {}
    trips: list[RoundTrip] = []
    for fill in fills(root):
        lots = opened.setdefault(fill.symbol, deque())
        if fill.quantity > 0:
            lots.append((fill, fill.quantity))
        left = -fill.quantity
        while left > 0:
            buy, open_shares = lots.popleft()
            shares = min(open_shares, left)
            if open_shares > shares:
                lots.appendleft((buy, open_shares - shares))
            left -= shares
            (paid, bought), (got, sold) = pounds(buy, shares), pounds(fill, shares)
            gross, costs = got - paid, bought + sold
            bought_leg, sold_leg = replace(buy, quantity=shares), replace(fill, quantity=-shares)
            trips.append(RoundTrip(bought_leg, sold_leg, gross, costs, gross - costs.total))
    return tuple(trips)


def currency_gain(root: Path, lines: Iterable[Line], trips: Iterable[RoundTrip]) -> Decimal:
    """CURRENCY APART FROM TRADING (BIC-04): the pounds the trips gained or lost because the
    currency moved between the buy's day and the sale's, the shares sold at the sale's price
    times the change in the day's rate. A trip's gross less this is its trading profit."""
    currency = {line.symbol: line.currency for line in lines}
    return sum(
        (
            -t.sell.quantity
            * t.sell.price
            * (
                rate(root, currency[t.sell.symbol], t.sell.day)
                - rate(root, currency[t.buy.symbol], t.buy.day)
            )
            for t in trips
        ),
        Decimal(0),
    )


def open_currency_gain(
    root: Path, lines: Iterable[Line], prices: Mapping[str, Decimal], day: date
) -> Decimal:
    """CURRENCY ON OPEN HOLDINGS (BIC-04): what the shares still held, the newest buys (sales
    close the oldest), have gained or lost at today's price from the currency's move since the
    buy's day, apart from the price's own."""
    money, total = {line.symbol: line.currency for line in lines}, Decimal(0)
    for symbol, held in positions(root, day).items():
        for buy in (f for f in reversed(fills(root)) if f.symbol == symbol and f.quantity > 0):
            shares, held = min(held, buy.quantity), held - min(held, buy.quantity)
            move = rate(root, money[symbol], day) - rate(root, money[symbol], buy.day)
            total += shares * prices[symbol] * move
    return total


def interest(
    root: Path, lines: Iterable[Line], capital: Decimal, annual: Decimal, first: date, last: date
) -> Decimal:
    """INTEREST ON IDLE CASH (BIC-03): each day from first to last, the capital less what the
    ledger has spent by its end (costs too), if positive, earns annual / 365 of itself."""
    held, total, day = tuple(lines), Decimal(0), first
    while day <= last:
        cash, costs = dealt(root, held, day, date.min, 0)
        total += max(capital + cash - costs.total, Decimal(0)) * annual / 365
        day += timedelta(days=1)
    return total


def attributed(
    trips: Iterable[RoundTrip], by: Callable[[RoundTrip], object]
) -> dict[object, Decimal]:
    """THE PROFIT TOLD APART (TRD-12): pounds after every cost summed under what the key says of a
    trip: its strategy (the buy's order id), its line, the days it was held, its costs."""
    total: dict[object, Decimal] = {}
    for trip in trips:
        total[by(trip)] = total.get(by(trip), Decimal(0)) + trip.profit
    return total


@dataclass(frozen=True)
class Story:
    """A TRADE'S WHOLE STORY (TRD-11, DQ-08): the trip, its signal's strategy and session, read
    from the buy's order id, and the bar that signal read: the line's last bar before the buy."""

    strategy: str
    bar: Bar
    trip: RoundTrip
    held: int  #: calendar days from the buy to the sale


def told(trips: Iterable[RoundTrip], archive: Mapping[Line, Sequence[Bar]]) -> tuple[Story, ...]:
    """Each trip's story, in the ledger's order; a buy whose line has no earlier bar is refused."""
    bars, stories = {line.symbol: days for line, days in archive.items()}, []
    for trip in trips:
        buy = trip.buy
        if not (read := [bar for bar in bars.get(buy.symbol, ()) if bar.day < buy.day]):
            raise ValueError(f"{buy.order_id}: {buy.symbol} has no bar before {buy.day}")
        held = (trip.sell.day - buy.day).days
        stories.append(Story(strategy_of(buy.order_id), read[-1], trip, held))
    return tuple(stories)


STORY = "story.csv"


@dataclass(frozen=True)
class Link:
    """THE ID CHAIN AT DECISION TIME (TRD-11, DQ-08): one decision's signal (strategy, line,
    session), the bar it read, and the send path's answer, under the id its order and fills have."""

    order_id: str
    strategy: str
    symbol: str
    session: date
    bar_day: date
    bar_close: Decimal
    filled: int  #: shares the order filled at once
    blocker: str  #: what stood in its way; empty when nothing did


SENDING = "SENDING"  #: a chain's blocker from before the send until its answer completes it


def _keep(root: Path, made: Link) -> Link:
    with (root / STORY).open("a", newline="", encoding="utf-8") as out:
        csv.writer(out).writerow(astuple(made))
    return made


def intend(root: Path, order_id: str, signal: tuple[str, str, date], bar: Bar) -> Link:
    """Keep a decision's chain BEFORE its order is sent (B5), still unanswered (SENDING), so a
    send that raises leaves the order traceable. The signal: strategy, symbol, session; a
    stranger's sale has the strategy "stranger"."""
    return _keep(root, Link(order_id, *signal, bar.day, bar.close, 0, SENDING))


def chain(root: Path, made: Link, answer: Sent) -> Link:
    """Complete a kept chain with the send path's answer, on a line after the first."""
    blocker = answer.blocker.name if answer.blocker else ""
    return _keep(root, replace(made, filled=answer.filled, blocker=blocker))


def chains(root: Path) -> Iterator[Link]:
    """The chains kept, one per order id, in the order first kept, each as last written."""
    if not (root / STORY).exists():
        return
    last: dict[str, Link] = {}
    with (root / STORY).open(newline="", encoding="utf-8") as kept:
        for r in csv.reader(kept):
            sees, read = date.fromisoformat(r[3]), date.fromisoformat(r[4])
            last[r[0]] = Link(r[0], r[1], r[2], sees, read, Decimal(r[5]), int(r[6]), r[7])
    yield from last.values()
