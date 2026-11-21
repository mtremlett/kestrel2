"""incubation - THE INCUBATION LINE (R-RUNNER-232): a rule the ladder calls INCUBATE trades on
paper only, at one fixed small size and at most two open, on a book line of its own apart from
the desk's rules, through the same gate and stops. It only reads the ledger; promotion is the
operator's, on the live paper record, never the ladder's."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from desk.broker import Fill
from desk.lines import Line
from desk.orders import HOLDINGS, Order, Refused, Settings, size, strategy_of
from desk.strategy import Decision

POSITION = Decimal(250)  #: pounds a position may cost, counted at what the line controls
OPEN = 2  #: the most positions the incubation line holds at once


def held(ledger: Iterable[Fill], rules: frozenset[str]) -> dict[str, int]:
    """The incubation line's book: the shares of fills whose order is an INCUBATE rule's."""
    book: dict[str, int] = {}
    for fill in ledger:
        if strategy_of(fill.order_id) in rules:
            book[fill.symbol] = book.get(fill.symbol, 0) + fill.quantity
    return {symbol: shares for symbol, shares in sorted(book.items()) if shares}


def buy(
    decision: Decision,
    line: Line,
    price: Decimal,
    fx: Decimal,
    rules: frozenset[str],
    ledger: Iterable[Fill],
) -> Order:
    """The order an INCUBATE rule's buy makes: sized to POSITION against the incubation line's
    own book, and refused as a new position once OPEN are held. Any other rule is not its."""
    if decision.strategy not in rules:
        raise ValueError(
            f"{decision.strategy}: not an INCUBATE rule; the desk's own sizing applies"
        )
    mine = held(ledger, rules)
    if line.symbol not in mine and len(mine) >= OPEN:
        raise Refused(f"{decision.strategy}-{line.symbol}: {len(mine)} incubating, at most {OPEN}")
    return size(decision, line, price, fx, Settings(capital=POSITION * HOLDINGS), mine)
