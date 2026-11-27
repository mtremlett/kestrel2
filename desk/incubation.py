"""INCUBATION (R-RUNNER-232, easing 3, the desk's half): a rule the ladder calls INCUBATE trades
on paper only, at one fixed small size, on its own book line apart from the desk's rules,
through the same gate and stops. Promotion is on its paper record and his yes, never here."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date
from decimal import Decimal

from desk import orders
from desk.broker import Fill
from desk.lines import Line
from desk.orders import Order, Refused, Settings
from desk.strategy import Action, Decision

TAG = "inc_"  #: the front of every incubating rule's strategy name, so its orders are its own
POSITION = Decimal(250)  #: pounds one position may cost, counted at what the line controls
MOST_OPEN = 2  #: the lines an incubating book may hold at once
BOOK_ROOM = Settings(
    POSITION * MOST_OPEN, holdings=MOST_OPEN
)  #: its allowance, apart from the desk's


def is_incubating(order_id: str) -> bool:
    """Whether the order, or the stop it left, is an incubating rule's: its strategy begins TAG."""
    return orders.strategy_of(order_id).startswith(TAG)


def side(fills: Iterable[Fill], held: Mapping[str, int]) -> dict[str, int]:
    """The lines held whose last buy was an incubating rule's: the book line the gate counts."""
    owner = {f.symbol: is_incubating(f.order_id) for f in fills if f.quantity > 0}
    return {symbol: shares for symbol, shares in held.items() if owner.get(symbol, False)}


def buy(
    rule: str,
    line: Line,
    day: date,
    price: Decimal,
    fx: Decimal,
    mine: Mapping[str, int],
    market: Decimal | None = None,
) -> Order:
    """The incubating rule's buy: sized to POSITION pounds, its id on the incubation line, and
    refused by the one gate (orders.gate) once MOST_OPEN lines are open, a held line aside;
    mine is the incubation line's holdings (side)."""
    if line.symbol not in mine and len(mine) >= MOST_OPEN:
        raise Refused(f"{rule}-{line.symbol}: {len(mine)} incubating, at most {MOST_OPEN} open")
    decision = Decision(f"{TAG}{rule}", line.symbol, day, Action.BUY)
    return orders.size(decision, line, price, fx, BOOK_ROOM, mine, market)
