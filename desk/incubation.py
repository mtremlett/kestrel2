"""EASING 3, THE DESK'S HALF (R-RUNNER-232): a rule the ladder calls INCUBATE trades on paper only,
at one fixed small size and on its own book line (its strategy name begins INC), apart from the
desk's rules. It is promoted only on its live paper record and his yes, never by the ladder. This
module only reads the book; the send path's gate and stops are the desk's own."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from desk import book
from desk.lines import Line
from desk.orders import Order, Refused, Settings, size
from desk.strategy import Decision

INC = "inc_"  #: the front of every incubating rule's strategy name: its own line of the book
POSITION = Decimal(250)  #: pounds a position may cost, fixed whatever the rule
MOST_OPEN = 2  #: the most positions open at once
SMALL = Settings(POSITION, holdings=1)  #: one position is the whole of the pounds


def is_incubating(order_id: str) -> bool:
    """Whether the order, or the stop it left, is an incubating rule's."""
    parts = order_id.split("-")
    return len(parts) > 1 and parts[1].startswith(INC)


def held(root: Path) -> dict[str, int]:
    """The lines held on the incubation line, by the side of each line's last buy."""
    owner = {f.symbol: is_incubating(f.order_id) for f in book.fills(root) if f.quantity > 0}
    return {s: n for s, n in book.positions(root).items() if owner.get(s, False)}


def buy(
    root: Path, decision: Decision, line: Line, price: Decimal, fx: Decimal, market: Decimal | None
) -> Order:
    """An INCUBATE rule's buy, booked on the incubation line and sized to POSITION pounds; a third
    open position is refused, as the gate refuses a sixth holding of the desk's."""
    mine = held(root)
    if line.symbol not in mine and len(mine) >= MOST_OPEN:
        raise Refused(f"{decision.strategy}-{line.symbol}: {len(mine)} open, at most {MOST_OPEN}")
    named = replace(decision, strategy=INC + decision.strategy)
    return size(named, line, price, fx, SMALL, mine, market)
