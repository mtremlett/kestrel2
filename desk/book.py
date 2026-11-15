"""book - THE LEDGER AND THE BOOK. Fills are written under the broker's own ids; the book is
their sum, never the orders the desk meant to send, and reconciling compares it with the
broker's positions. The send path keeps the kill switch's record, sends nothing while it is on
and no buy in a halt, notes each order as it goes, and cancels what a dead desk left working."""

from __future__ import annotations

import csv
from collections import Counter, deque
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import astuple, dataclass, replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path

from desk import halt
from desk.broker import Broker, Crash, Disconnected, Fill, Report
from desk.carry import carried
from desk.halt import Blocker, Stopped
from desk.lines import Line
from desk.orders import Charges, Order, Refused, Sale, Settings, charges, gate, leg_of

LEDGER, RATES, SWITCH = "ledger.csv", "rates.csv", "switch.csv"
GOING = "going.csv"  #: the order at the broker's door, kept only until the desk has its answer
STOPS, LEVELS = "stops.csv", ("stop", "level")  #: each buy's stop level, kept as the buy goes
COLUMNS = ("execution_id", "order_id", "symbol", "quantity", "price", "day")
TURNS = ("at", "turn", "why")


class Alarm(Exception):
    """The broker's place failed in a way the desk does not know: the kill switch is on."""


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


Tell = Callable[[str, str], None]  #: the door to his phone: a message's name, then its words
Reckoning = tuple[dict[str, int], tuple[str, ...], set[str], tuple[Difference, ...]]


def send(
    root: Path, broker: Broker, order: Order | Sale, settings: Settings, tell: Tell | None = None
) -> Sent:
    """Ask the broker what it did with the order's id, so a desk that restarts never sends it
    twice; if it never received it, pass the pre-trade gate and send it. Fills are recorded and
    a buy's stop rests at the broker. Where the book (brought up to date) is not the broker's
    nothing is bought, and a line is sold only if its shares agree. Kill switch on: nothing is
    sent; a halt in force: no buy. Every refusal names its blocker (Stopped), as does an answer
    that is not a whole fill. A place that fails unknown pulls the kill switch (Alarm); one
    that disagrees halts buying and is told (tell). A dead desk's working orders go first."""
    _settle(root, broker)
    report = broker.report(order.order_id)
    if report is None:
        _unless_stopped(root, order)
        held, differ, unsure, _ = _compare(root, broker)
        if differ and (isinstance(order, Order) or order.line.symbol in unsure):
            words = f"{order.order_id}: not sent, the book is not the broker's on {list(differ)}"
            raise Stopped(Blocker.BOOK, words)
        try:
            gate(order, settings, held)
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
        _write(root / STOPS, [LEVELS, *kept.items(), (name, order.stop)])
    _write(going, [(order.order_id,)])
    try:
        report = broker.place(order)
    except (Disconnected, Refused):
        going.unlink()
        raise
    except Crash:
        raise
    except Exception as error:  #: unknown: the desk does not guess, and the note stays
        if (report := _disagreed(root, broker, order, error, tell)) is None:
            words = f"{order.order_id}: place failed with {error!r}; the kill switch is on"
            turn(root, Switch.ON, datetime.now(UTC), words)
            tuple(broker.cancel())
            raise Alarm(words) from error
    going.unlink()
    return report


def _disagreed(
    root: Path, broker: Broker, order: Order | Sale, error: Exception, tell: Tell | None
) -> Report | None:
    """THE BROKER'S WORD, FILLS AND ACCOUNT DO NOT AGREE after the order has gone (R-PAPER-11,
    Unprotected): buying is halted until he lifts it, he is told (tell), and the broker's
    report is given, so the order is never sent again. Else None; with no one to tell, too."""
    from desk import placing  # noqa: PLC0415 - placing reaches book through paper: a load cycle

    if tell is None or not isinstance(error, placing.Unprotected):
        return None
    words = f"{order.order_id}: the broker's word, fills and account do not agree: {error}"
    halt.call(root, datetime.now(UTC), f"{words}; no buy goes until he lifts this", by="send path")
    tell(f"disagree {order.order_id}", f"{words}. Buying is halted; sales go on.")
    return broker.report(order.order_id) or Report(order.order_id, (), words)


def _settle(root: Path, broker: Broker) -> None:
    """A DESK THAT DIED MID-SEND left its note (_place) and perhaps its order working, to fill
    behind a gate that counts the book alone: before any send the broker cancels the desk's
    own working orders, then the note is gone. While the kill switch is on it waits."""
    going = root / GOING
    if going.exists() and killed(root) is None:
        tuple(broker.cancel())
        going.unlink()


def levels(root: Path) -> dict[str, Decimal]:
    """THE STOPS THE DESK RESTED: each buy's stop level under "<buy>-stop", oldest first."""
    path = root / STOPS
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as kept:
        rows = list(csv.reader(kept))
    if rows[:1] != [list(LEVELS)]:
        raise ValueError(f"{path}: not the desk's stop levels")
    return {name: Decimal(level) for name, level in rows[1:]}


def turn(root: Path, to: Switch, at: datetime, why: str) -> None:
    """Write on the kill switch's record what happened to it, when (UTC), and why."""
    record = (*switch(root), _turn(at, to, why))
    _write(root / SWITCH, [TURNS, *((t.isoformat(), s.value, w) for t, s, w in record)])


def switch(root: Path) -> tuple[tuple[datetime, Switch, str], ...]:
    """The kill switch's record, oldest first; one not readable whole is an error, never off."""
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
    """Refuse the order while the kill switch is on, and a buy while a halt is in force."""
    _unless_killed(root, order.order_id)
    if isinstance(order, Order) and (halts := halt.in_force(root)):
        said = "; ".join(h.since for h in halts)
        raise Stopped(Blocker.HALT, f"{order.order_id}: not sent, a halt is in force, {said}")


def killed(root: Path) -> str | None:
    """The kill switch's word while it is on, when and why; None while off. A drill is neither."""
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
        rows = csv.reader(ledger)
        if next(rows, None) != list(COLUMNS):
            raise ValueError(f"{path}: not the desk's ledger")
        return tuple(
            Fill(e, o, y, int(q), Decimal(p), date.fromisoformat(d)) for e, o, y, q, p, d in rows
        )


def _write(path: Path, rows: Iterable[Sequence[object]]) -> None:
    """Written whole, then swapped in, so a desk that dies mid-write leaves the old file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    written = path.with_suffix(".tmp")
    with written.open("w", newline="", encoding="utf-8") as out:
        csv.writer(out).writerows(rows)
    written.replace(path)


def _revision(execution_id: str) -> tuple[str, int]:
    """An execution id as its fill and version: a correction changes the last part (.01 to .02)."""
    fill, _, last = execution_id.rpartition(".")
    return (fill, int(last)) if last.isdecimal() and fill else (execution_id, 0)


def _record(root: Path, new: Iterable[Fill]) -> None:
    """Add the fills not in the ledger; a fill the broker corrects replaces its earlier version."""
    kept = fills(root)
    latest = {_revision(f.execution_id)[0]: f for f in kept}
    for fill in new:
        name = _revision(fill.execution_id)[0]
        latest[name] = max(latest.get(name, fill), fill, key=lambda f: _revision(f.execution_id)[1])
    if tuple(latest.values()) != tuple(kept):
        _write(root / LEDGER, [COLUMNS, *(astuple(fill) for fill in latest.values())])


def collect(root: Path, broker: Broker) -> None:
    """Write in the ledger every fill the broker gives that it lacks (a stop sale, a correction)."""
    _record(root, broker.fills())


def reconcile(root: Path, broker: Broker) -> tuple[str, ...]:
    """The lines on which the book is not the broker's: shares differ, or the stop is not theirs."""
    return _compare(root, broker)[1]


def reckon(root: Path, broker: Broker) -> Reckoning:
    """The book, the lines that differ, those whose shares do, the stops that do: one reading."""
    return _compare(root, broker)


def _compare(root: Path, broker: Broker) -> Reckoning:
    """One reading: the book, the names it is not the broker's on, those whose shares differ,
    the stops that are not the book's. The broker is asked fills, stops, holdings in that order,
    so a stop that sells between the last two shows as shares gone, never still there."""
    collect(root, broker)
    ours = positions(root)
    stops = differences(ours, broker.stops())
    shares = {d.name for d in differences(ours, broker.holdings())}
    return ours, tuple(sorted(shares | {d.name for d in stops})), shares, stops


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
    short = sorted(symbol for symbol, shares in held.items() if shares < 0)
    if short:
        raise ValueError(f"the ledger sells more than it bought of {short}: the desk is long only")
    return {symbol: shares for symbol, shares in sorted(held.items()) if shares}


def record_rates(root: Path, day: date, rates: Mapping[str, Decimal]) -> None:
    """Keep the day's pounds per unit of each currency: fills are priced from this record."""
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
        return {
            (date.fromisoformat(r["day"]), r["currency"]): Decimal(r["rate"])
            for r in csv.DictReader(saved)
        }


def rate(root: Path, currency: str, day: date) -> Decimal:
    """Pounds per unit of a currency kept for a day, carried over a UK-only holiday (desk.carry)."""
    kept = carried({d: r for (d, c), r in _rates(root).items() if c == currency}, day)
    if kept is None:
        raise ValueError(f"no {currency} rate kept for {day}")
    return kept


def dealt(
    root: Path, lines: Iterable[Line], day: date, last: date, counted: int
) -> tuple[Decimal, Charges]:
    """A DAY'S DEALING, in pounds: sales less buys and every cost of the fills its record is the
    first to count: those dated after the last record's day, and any that reached the ledger
    late."""
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
    known, rates = {line.symbol: line for line in lines}, _rates(root)
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
