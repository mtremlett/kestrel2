"""incubation - A RULE THE LADDER CALLS INCUBATE TRADES ON PAPER ONLY (R-RUNNER-232, EASING 3):
one fixed small size (ROOM pounds a position, at most OPEN open), its orders on a book line of
their own (INCUBATING in the strategy part of the id, as the zoo's), through the same gate and
stops. Only the ladder's INCUBATE is booked here; a PASS rule is untouched. Promotion is never
the ladder's: it waits for the live paper record and his yes."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import replace
from decimal import Decimal

from desk import orders
from desk.broker import Fill
from desk.lines import Line
from desk.strategy import Action, Decision

INCUBATING = "inc_"  #: the front of an incubating rule's name in its order ids
ROOM = Decimal(250)  #: pounds a position may cost
OPEN = 2  #: positions open at once
#: The gate's settings for the incubation line: its capital is its positions' rooms together.
SETTINGS = orders.Settings(ROOM * OPEN, new_lines=OPEN, holdings=OPEN)


def is_incubating(order_id: str) -> bool:
    """Whether the order, or the stop it left, is an incubating rule's."""
    return order_id.split("-")[1:2] != [] and order_id.split("-")[1].startswith(INCUBATING)


def booked(decision: Decision, verdicts: Mapping[str, str]) -> Decision:
    """The decision on the incubation line if the ladder's verdict on its rule is INCUBATE,
    else the decision itself."""
    if verdicts.get(decision.strategy) != "INCUBATE":
        return decision
    return replace(decision, strategy=INCUBATING + decision.strategy)


def apart(fills: Iterable[Fill], held: Mapping[str, int]) -> dict[str, int]:
    """Of the lines held, those whose last buy was an incubating rule's."""
    owner = {f.symbol: is_incubating(f.order_id) for f in fills if f.quantity > 0}
    return {symbol: shares for symbol, shares in held.items() if owner.get(symbol, False)}


def size(
    decision: Decision,
    line: Line,
    price: Decimal,
    fx: Decimal,
    held: Mapping[str, int],
    market: Decimal | None = None,
    traded: Decimal | None = None,
) -> orders.Order:
    """The buy of an incubating rule, sized to ROOM pounds, through the one sizer and its gate.
    held is the incubation line's own (apart); a third open position is refused."""
    if decision.action is not Action.BUY or not is_incubating(f"-{decision.strategy}-"):
        raise ValueError(f"{decision.strategy}: not an incubating buy; only INCUBATE rules are")
    if line.symbol not in held and len(held) >= OPEN:
        raise orders.Refused(f"{orders.order_id_of(decision)}: {len(held)} open, at most {OPEN}")
    return orders.size(decision, line, price, fx, SETTINGS, held, market, traded)
