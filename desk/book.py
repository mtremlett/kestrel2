"""book - THE LEDGER AND THE BOOK. Fills are written under the broker's own ids. The book is
the sum of those fills, never the orders the desk meant to send, and reconciling compares
it with the positions the broker reports. The send path keeps the kill switch's record,
and sends nothing while it is on, and no buy while a halt is in force."""

from __future__ import annotations

import csv
from collections import Counter, deque
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import astuple, dataclass, replace
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path

from desk import halt
from desk.broker import Broker, Disconnected, Fill
from desk.halt import Blocker, Stopped
from desk.lines import Line
from desk.orders import Charges, Order, Refused, Sale, Settings, charges, gate, leg_of

LEDGER, RATES, SWITCH = "ledger.csv", "rates.csv", "switch.csv"
COLUMNS = ("execution_id", "order_id", "symbol", "quantity", "price", "day")
TURNS = ("at", "turn", "why")


class Switch(Enum):
    """A word on the kill switch's record: pulled, released, or drilled on a rehearsal desk."""

    ON = "on"
    OFF = "off"
    DRILLED = "drilled"


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


def send(root: Path, broker: Broker, order: Order | Sale, settings: Settings) -> Sent:
    """Ask the broker what it did with the order's id, so a desk that restarts never sends
    it twice; if it never received it, pass the pre-trade gate and send it. Its fills are
    recorded and its stop rests at the broker. The gate reads the book, brought up to date
    with the broker's fills first. While the book is not the broker's on any line nothing
    is bought, and a line is sold only if its shares agree: one that has lost its stop may
    go, shares the broker may not hold may not. While the kill switch is on nothing is sent
    at all, and while a halt is in force no buy, were either done as the broker answered;
    what the broker already has is recorded. Every refusal made here names its blocker
    (Stopped), the gate's too, and so does an answer that is not a whole fill; a refusal
    that names none is the broker's own door's."""
    report = broker.report(order.order_id)
    if report is None:
        _unless_stopped(root, order)
        held, differ, unsure = _compare(root, broker)
        if differ and (isinstance(order, Order) or order.line.symbol in unsure):
            words = f"{order.order_id}: not sent, the book is not the broker's on {list(differ)}"
            raise Stopped(Blocker.BOOK, words)
        try:
            gate(order, settings, held)
        except Refused as refused:
            raise Stopped(Blocker.GATE, str(refused)) from refused
        _unless_stopped(root, order)  #: read again, at the last moment before it goes
        try:
            report = broker.place(order)
        except Disconnected as lost:  #: never received: stated, and sent again next time
            return Sent(order.order_id, 0, str(lost), Blocker.BROKER)
    collect(root, broker)  #: a stop sold on the day of its buy is in no answer
    filled, short = sum(abs(f.quantity) for f in report.fills), report.reason is not None
    return Sent(order.order_id, filled, report.reason, Blocker.BROKER if short else None)


def turn(root: Path, to: Switch, at: datetime, why: str) -> None:
    """Write on the kill switch's record what happened to it at a moment, in UTC, and why."""
    record = (*switch(root), _turn(at, to, why))
    _write(root / SWITCH, [TURNS, *((t.isoformat(), s.value, w) for t, s, w in record)])


def switch(root: Path) -> tuple[tuple[datetime, Switch, str], ...]:
    """The kill switch's record, oldest first: each moment, what happened to it, and why. No
    record is a switch never touched; one that is there and cannot be read whole is an error,
    never a switch that is off."""
    path = root / SWITCH
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8") as record:
        rows = list(csv.reader(record))
    if rows[:1] != [list(TURNS)]:
        raise ValueError(f"{path}: not the kill switch's record, so nothing is sent")
    return tuple(_turn(datetime.fromisoformat(at), Switch(to), why) for at, to, why in rows[1:])


def _turn(at: datetime, to: Switch, why: str) -> tuple[datetime, Switch, str]:
    """An entry of the kill switch's record: a moment in UTC and a reason, or an error."""
    if at.utcoffset() != timedelta(0) or not why.strip():
        raise ValueError(f"the kill switch, {to.value} at {at} for {why!r}: no UTC time or reason")
    return at, to, why


def _unless_killed(root: Path, order_id: str) -> None:
    """Refuse the order while the kill switch is on, in the switch's own words."""
    if on := killed(root):
        raise Stopped(Blocker.KILL, f"{order_id}: not sent, {on}")


def _unless_stopped(root: Path, order: Order | Sale) -> None:
    """Refuse the order while the kill switch is on, and a buy while a halt is in force, in
    the halts' own words."""
    _unless_killed(root, order.order_id)
    if isinstance(order, Order) and (halts := halt.in_force(root)):
        said = "; ".join(h.since for h in halts)
        raise Stopped(Blocker.HALT, f"{order.order_id}: not sent, a halt is in force, {said}")


def killed(root: Path) -> str | None:
    """The kill switch's word while it is on, when it was pulled and why; None while it is
    off. A drill pulls a rehearsal desk's switch, never this one, so it is neither."""
    turns = [(at, to, why) for at, to, why in switch(root) if to is not Switch.DRILLED]
    if not turns or turns[-1][1] is Switch.OFF:
        return None
    at, _, why = turns[-1]
    return f"the kill switch is on, pulled at {at:%Y-%m-%d %H:%M} UTC: {why}"


def fills(root: Path) -> tuple[Fill, ...]:
    """Every fill the desk has recorded, in the order it learned of them."""
    path = root / LEDGER
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8") as ledger:
        rows = list(csv.DictReader(ledger))
    return tuple(
        Fill(
            r["execution_id"],
            r["order_id"],
            r["symbol"],
            int(r["quantity"]),
            Decimal(r["price"]),
            date.fromisoformat(r["day"]),
        )
        for r in rows
    )


def _write(path: Path, rows: Iterable[Sequence[object]]) -> None:
    """Written whole, then swapped in, so a desk that dies mid-write leaves the old file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    written = path.with_suffix(".tmp")
    with written.open("w", newline="", encoding="utf-8") as out:
        csv.writer(out).writerows(rows)
    written.replace(path)


def _record(root: Path, new: Iterable[Fill]) -> None:
    """Add the fills not already in the ledger, under the broker's execution ids."""
    ledger = fills(root)
    known = {fill.execution_id for fill in ledger}
    added = tuple(fill for fill in new if fill.execution_id not in known)
    if added:
        _write(root / LEDGER, [COLUMNS, *(astuple(fill) for fill in ledger + added)])


def collect(root: Path, broker: Broker) -> None:
    """Write in the ledger every fill the broker gives that it lacks: a stop the broker sells
    is in no order's answer."""
    _record(root, broker.fills())


def reconcile(root: Path, broker: Broker) -> tuple[str, ...]:
    """The lines on which the desk's book is not the broker's, once every fill the broker
    made is in the ledger: the shares differ, or the stop resting at the broker is not for
    exactly the shares held. None named: the book is the broker's."""
    return _compare(root, broker)[1]


def _compare(root: Path, broker: Broker) -> tuple[dict[str, int], tuple[str, ...], set[str]]:
    """The broker asked once each for its fills, its stops and its holdings, in that order:
    the book the fills add up to, the names on which it is not the broker's, and those of
    them whose shares differ. The stops are read before the holdings, so a stop that sells
    between the two shows as shares gone, never as shares still there to be sold."""
    collect(root, broker)
    ours = positions(root)
    stops = differences(ours, broker.stops())
    shares = {d.name for d in differences(ours, broker.holdings())}
    return ours, tuple(sorted(shares | {d.name for d in stops})), shares


def differences(
    held: Mapping[str, int], entries: Iterable[tuple[str, Decimal | int]]
) -> tuple[Difference, ...]:
    """THE BOOK AGAINST A BROKER: the one comparison, for any broker, of its holdings or of
    the stops resting there. held is the book (positions); entries are what the broker
    gives, each a name and its shares, the name in the words held uses. Every entry must be
    the book's own shares of its name: entries that only add up to them are two places, or
    a change while they were read, and a name with shares in two entries is never the
    book's one line. A name the book holds and the broker does not give is named at no
    shares; a name the broker lists at no shares is not held. None named: they agree."""
    rows = list(entries)
    places = Counter(name for name, shares in rows if shares)
    rows += [(name, 0) for name in held.keys() - {name for name, _ in rows}]
    return tuple(
        Difference(name, shares, held.get(name, 0))
        for name, shares in sorted(rows)
        if shares != held.get(name, 0) or (shares and places[name] > 1)
    )


def positions(root: Path, upto: date = date.max) -> dict[str, int]:
    """What the desk holds, or held at the end of a day: the shares of each line its ledger's
    fills add up to, never the orders it meant to send. A line sold out is not held."""
    held: dict[str, int] = {}
    for fill in fills(root):
        if fill.day <= upto:
            held[fill.symbol] = held.get(fill.symbol, 0) + fill.quantity
    short = sorted(symbol for symbol, shares in held.items() if shares < 0)
    if short:
        raise ValueError(f"the ledger sells more than it bought of {short}: the desk is long only")
    return {symbol: shares for symbol, shares in sorted(held.items()) if shares}


def record_rates(root: Path, day: date, rates: Mapping[str, Decimal]) -> None:
    """Keep the day's pounds per unit of each currency, so its fills are priced in pounds
    from the saved record, never from a rate looked up again later."""
    kept = _rates(root)
    for currency, rate in rates.items():
        if not (rate.is_finite() and rate > 0) or (currency == "GBP" and rate != 1):
            raise ValueError(f"{day}: a rate of {rate} pounds per {currency}")
        if kept.setdefault((day, currency), rate) != rate:
            raise ValueError(f"{day}: {currency} was kept at {kept[day, currency]}, not {rate}")
    _write(root / RATES, [("day", "currency", "rate"), *((*key, r) for key, r in kept.items())])


def _rates(root: Path) -> dict[tuple[date, str], Decimal]:
    path = root / RATES
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as saved:
        rows = list(csv.DictReader(saved))
    return {(date.fromisoformat(r["day"]), r["currency"]): Decimal(r["rate"]) for r in rows}


def rate(root: Path, currency: str, day: date) -> Decimal:
    """The pounds per unit of a currency kept for a day: what a holding in it is valued at
    that day's end. None kept for that very day is an error, never an older day's rate."""
    kept = _rates(root).get((day, currency))
    if kept is None:
        raise ValueError(f"no {currency} rate kept for {day}")
    return kept


def dealt(
    root: Path, lines: Iterable[Line], day: date, last: date, counted: int
) -> tuple[Decimal, Charges]:
    """A DAY'S DEALING, in pounds: what the sales brought in less what the buys paid, and
    every cost, line by line, of the fills its record is the first to count. Those are the
    fills dated after the last record's day, and any dated by then that reached the ledger
    after that record had counted its own: the ledger keeps fills in the order they came."""
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
    """How the ledger's fills are priced in pounds: each at its own day's kept rate, its costs
    from the one cost model, a stop's sale priced as one. A line not given is an error."""
    known, rates = {line.symbol: line for line in lines}, _rates(root)
    unknown = sorted({fill.symbol for fill in fills(root)} - set(known))
    if unknown:
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


def round_trips(root: Path, lines: Iterable[Line]) -> tuple[RoundTrip, ...]:
    """Each sale in the ledger matched with the buys it closes, oldest first, in pounds at
    each fill's own day's rate, after every cost of both legs from the one cost model, a
    stop's sale priced as one. A fill split between trips shares its costs by its shares."""
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
            trips.append(
                RoundTrip(
                    replace(buy, quantity=shares),
                    replace(fill, quantity=-shares),
                    got - paid,
                    bought + sold,
                    got - paid - (bought + sold).total,
                )
            )
    return tuple(trips)
