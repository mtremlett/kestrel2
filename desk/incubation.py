"""incubation - A RULE THE LADDER CALLS INCUBATE trades on paper only, at one fixed small size
(STAKE pounds a position, at most OPEN open), on its own book line apart from the desk's rules,
through the same gate and stops (R-RUNNER-232, easing 3). It is promoted only on its paper record
and the operator's yes, never by the ladder. It reads the ledger; it writes nothing."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

from desk.book_parts2 import fills
from desk.lines import Line
from desk.orders import HOLDINGS, Order, Refused, Settings, gate, size, strategy_of
from desk.strategy import Decision

LINE = "incubation"  #: the book line (the strategy part of an order id) every such buy is booked on
STAKE = Decimal(250)  #: pounds a position costs, counted at what its line controls
OPEN = 2  #: the most positions open on the incubation line at once
ANSWER = "INCUBATE"  #: the ladder's answer for such a rule (lab.verdict_parts.INCUBATE)
SETTINGS = Settings(capital=STAKE * HOLDINGS)  #: a fifth of it is the stake: the gate's one room


def held(root: Path, upto: date = date.max) -> dict[str, int]:
    """The shares open on the incubation line, from the ledger's fills booked on it."""
    shares: dict[str, int] = {}
    for fill in fills(root):
        if fill.day <= upto and strategy_of(fill.order_id) == LINE:
            shares[fill.symbol] = shares.get(fill.symbol, 0) + fill.quantity
    return {symbol: n for symbol, n in sorted(shares.items()) if n}


def buy(
    root: Path, answer: str, decision: Decision, line: Line, price: Decimal, fx: Decimal
) -> Order:
    """The buy of an INCUBATE rule's decision: sized to STAKE and booked on the incubation line.
    Refused (Refused) for any other answer, and for a new line while OPEN are open."""
    if answer != ANSWER:
        raise Refused(f"{decision.strategy}: {answer} is not INCUBATE; it trades by its own rules")
    open_now = held(root)
    if line.symbol not in open_now and len(open_now) >= OPEN:
        raise Refused(f"{decision.strategy}-{line.symbol}: {len(open_now)} open, at most {OPEN}")
    order = size(replace(decision, strategy=LINE), line, price, fx, SETTINGS, open_now)
    gate(order, SETTINGS, open_now)
    return order
