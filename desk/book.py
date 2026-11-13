"""book - THE LEDGER AND THE BOOK. Fills are written under the broker's own ids. The book is
the sum of those fills, never the orders the desk meant to send, and reconciling compares
it with the positions the broker reports."""

from __future__ import annotations

import csv
from collections import Counter, deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import astuple, dataclass, replace
from datetime import date
from decimal import Decimal
from pathlib import Path

from desk.broker import Disconnected, Fill, Pretend
from desk.lines import Line
from desk.orders import Order, Refused, Sale, Settings, charges, gate

LEDGER, RATES = "ledger.csv", "rates.csv"
COLUMNS = ("execution_id", "order_id", "symbol", "quantity", "price", "day")


@dataclass(frozen=True)
class Sent:
    order_id: str
    filled: int
    reason: str | None  #: why it did not fill completely; None only when it did


@dataclass(frozen=True)
class RoundTrip:
    buy: Fill
    sell: Fill
    gross: Decimal  #: pounds, before costs
    costs: Decimal  #: pounds, every cost of both legs
    profit: Decimal  #: pounds, gross less costs


@dataclass(frozen=True)
class Difference:
    """One entry of a broker's that is not the desk's book."""

    name: str  #: what is held, in the words the book and the broker's entries share
    broker: Decimal | int  #: the shares the broker's entry gives; 0 when it gives no entry
    book: int  #: the shares the desk's book holds of it; 0 when it holds none


def send(root: Path, broker: Pretend, order: Order | Sale, settings: Settings) -> Sent:
    """Ask the broker what it did with the order's id, so a desk that restarts never sends
    it twice; if it never received it, pass the pre-trade gate and send it. Its fills are
    recorded and its stop rests at the broker. The gate reads the book, brought up to date
    with the broker's fills first. While the book is not the broker's on any line nothing
    is bought, and a line is sold only if its shares agree: one that has lost its stop may
    go, shares the broker may not hold may not."""
    report = broker.report(order.order_id)
    if report is None:
        differ, held, symbol = reconcile(root, broker), positions(root), order.line.symbol
        unsure = any(d.name == symbol for d in differences(held, broker.positions().items()))
        if differ and (isinstance(order, Order) or unsure):
            raise Refused(
                f"{order.order_id}: not sent, the book is not the broker's on {list(differ)}"
            )
        gate(order, settings, held)
        try:
            report = broker.place(order)
        except Disconnected as lost:  #: never received: stated, and sent again next time
            return Sent(order.order_id, 0, str(lost))
    collect(root, broker)  #: a stop sold on the day of its buy is in no answer
    return Sent(order.order_id, sum(abs(f.quantity) for f in report.fills), report.reason)


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


def collect(root: Path, broker: Pretend) -> None:
    """Write in the ledger every fill the broker made that it lacks: a stop the broker sells
    is in no order's answer."""
    _record(root, broker.fills())


def reconcile(root: Path, broker: Pretend) -> tuple[str, ...]:
    """The lines on which the desk's book is not the broker's, once every fill the broker
    made is in the ledger: the shares differ, or the stop resting at the broker is not for
    exactly the shares held. None named: the book is the broker's."""
    collect(root, broker)
    ours = positions(root)
    stops = [(symbol, shares) for symbol, (shares, _) in broker.resting_stops().items()]
    differ = (*differences(ours, broker.positions().items()), *differences(ours, stops))
    return tuple(sorted({d.name for d in differ}))


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


def positions(root: Path) -> dict[str, int]:
    """What the desk holds: the shares of each line its ledger's fills add up to, never the
    orders it meant to send. A line sold out is not held."""
    held: dict[str, int] = {}
    for fill in fills(root):
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


def round_trips(root: Path, lines: Iterable[Line]) -> tuple[RoundTrip, ...]:
    """Each sale in the ledger matched with the buys it closes, oldest first, in pounds at
    each fill's own day's rate. A fill split between trips shares its charges by its shares."""
    known, rates = {line.symbol: line for line in lines}, _rates(root)
    unknown = sorted({fill.symbol for fill in fills(root)} - set(known))
    if unknown:
        raise ValueError(f"the ledger trades lines the desk was not given: {unknown}")

    def pounds(fill: Fill, shares: int) -> tuple[Decimal, Decimal]:
        """The fill's value and its share of the fill's charges, both for shares, in pounds."""
        line = known[fill.symbol]
        rate = rates.get((fill.day, line.currency))
        if rate is None:
            raise ValueError(f"{fill.execution_id}: no {line.currency} rate kept for {fill.day}")
        fee = charges(line, fill.quantity, fill.price, rate) * shares / abs(fill.quantity)
        return fill.price * shares * rate, fee

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
                    got - paid - bought - sold,
                )
            )
    return tuple(trips)
