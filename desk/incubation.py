"""incubation - A RULE THE LADDER CALLS INCUBATE trades on paper only (R-RUNNER-232): one fixed
small size, at most two open, on its own book line (every order id starts INC), through the
same gate and stops as the desk's rules. It reads desk.book and changes none of it; the ladder never
promotes a rule from here, only his yes on its paper record."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from desk import book
from desk.broker import Broker
from desk.lines import Line
from desk.orders import HOLDINGS, Order, Refused, Sale, Settings, size
from desk.strategy import Decision

INC = "inc-"  #: the incubation line: the start of every order id it makes
POUNDS = Decimal(250)  #: the pounds of one position
OPEN = 2  #: the most positions open at once
SETTINGS = Settings(POUNDS * HOLDINGS)  #: the gate's room for one position is then POUNDS


def held(root: Path) -> dict[str, int]:
    """The shares the incubation line holds, by symbol: its own fills added up."""
    shares: dict[str, int] = {}
    for fill in book.fills(root):
        if fill.order_id.startswith(INC):
            shares[fill.symbol] = shares.get(fill.symbol, 0) + fill.quantity
    return {symbol: n for symbol, n in sorted(shares.items()) if n}


def buy(root: Path, decision: Decision, line: Line, price: Decimal, fx: Decimal) -> Order:
    """The incubating rule's buy, sized to POUNDS and booked on the incubation line; Refused
    where a third position would open."""
    open_now = held(root)
    order = size(decision, line, price, fx, SETTINGS, {})
    if line.symbol not in open_now and len(open_now) >= OPEN:
        raise Refused(
            f"{order.order_id}: {len(open_now)} incubating positions already, at most {OPEN}"
        )
    return Order(
        INC + order.order_id,
        order.line,
        order.quantity,
        order.price,
        order.fx,
        order.stop,
        session=order.session,
    )


def sell(root: Path, order_id: str, line: Line) -> Sale:
    """The sale of every share the incubation line holds of the line, on the incubation line."""
    return Sale(INC + order_id, line, held(root)[line.symbol])


def send(
    root: Path, broker: Broker, order: Order | Sale, tell: book.Tell | None = None
) -> book.Sent:
    """Send an incubation order through the desk's one send path, gate and stops."""
    if not order.order_id.startswith(INC):
        raise ValueError(f"{order.order_id}: not an incubation order")
    return book.send(root, broker, order, SETTINGS, tell)
