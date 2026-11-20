"""incubation - A RULE THE LADDER CALLS INCUBATE TRADES ON PAPER ONLY (R-RUNNER-232), at one
fixed small size, on its own book line apart from the desk's rules, through the same gate and
stops. Its orders carry the strategy name `inc_<rule>`, so its fills are told from the desk's
by the order id alone; the ladder never promotes it, only its paper record and his yes."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from decimal import Decimal

from desk.broker import Fill
from desk.lines import Line
from desk.orders import HOLDINGS, Order, Refused, Settings, size
from desk.strategy import Decision

PREFIX = "inc_"  #: the mark on the strategy name of every incubating rule's decision and order
POUNDS = Decimal(250)  #: the most one incubating position may cost, commission and tax included
MOST_OPEN = 2  #: the most positions the incubation line holds at once


def incubate(decision: Decision) -> Decision:
    """The decision of a rule on trial: the same, under its incubation name."""
    return replace(decision, strategy=PREFIX + decision.strategy)


def held(ledger: Iterable[Fill]) -> dict[str, int]:
    """The incubation line's own book: the shares its orders (and their stops) left, by line."""
    book: dict[str, int] = {}
    for fill in ledger:
        parts = fill.order_id.split("-")
        if len(parts) >= 3 and parts[1].startswith(PREFIX):
            book[fill.symbol] = book.get(fill.symbol, 0) + fill.quantity
    return {symbol: shares for symbol, shares in sorted(book.items()) if shares}


def size_incubating(
    decision: Decision,
    line: Line,
    price: Decimal,
    fx: Decimal,
    ledger: Iterable[Fill],
) -> Order:
    """An incubating rule's buy, sized at POUNDS a position and booked on the incubation line
    (its order id carries PREFIX). A third open position is refused; the sizer's own gate
    then judges it as it does the desk's."""
    if not decision.strategy.startswith(PREFIX):
        raise ValueError(f"{decision.strategy}: not an incubating rule; `incubate` marks one")
    book = held(ledger)
    if line.symbol not in book and len(book) >= MOST_OPEN:
        raise Refused(
            f"{decision.day:%Y%m%d}-{decision.strategy}-{line.symbol}: {len(book)} incubating "
            f"positions already, at most {MOST_OPEN}"
        )
    return size(decision, line, price, fx, Settings(POUNDS * HOLDINGS), book)
