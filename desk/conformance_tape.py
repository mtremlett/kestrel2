"""conformance_tape - what the conformance run needs to know of the desk beside it: a desk
round's hours (no run begins within LEAD minutes of one), the desk's own share of the account read
before a run, and whether a holding of the desk's moved while the run was made."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime, timedelta
from datetime import time as hour
from decimal import Decimal

from desk import paper, venues

LEAD = 5  #: minutes before a desk round's start from which no run begins
#: A desk round's hours (UK), when the read of the day's cancelled orders is not made.
ROUNDS = ((hour(8, 0), hour(8, 30)), (hour(14, 30), hour(15, 0)))


def round_at(now: datetime, lead: int) -> bool:
    """Whether a desk round runs at the moment, or begins within lead minutes."""
    at = venues.uk_time(now).time()
    ahead = (datetime.combine(date.min, at) + timedelta(minutes=lead)).time()
    return any(start <= ahead < end or start <= at < end for start, end in ROUNDS)


def share(raw: paper.Account) -> tuple[dict[str, Decimal], set[str]]:
    """The desk's share of the account, read whole before the run: what it holds, by the
    broker's name for each, and the lines (contracts) its own client has an order working on."""
    held = {h.name: h.shares for h in raw.holdings if h.shares}
    return held, {o.contract for o in raw.orders if o.client == str(paper.DESK)}


def moved(held: Mapping[str, Decimal]) -> str:
    """Said when a desk holding, as the run began, is not as it was: a FIRST-LIGHT FAULT."""
    now = {h.name: h.shares for h in paper.whole().holdings}
    moved = [
        f"{name} {was} -> {now.get(name, 0)}"
        for name, was in held.items()
        if now.get(name, 0) != was
    ]
    return f" FIRST-LIGHT FAULT: the desk's holdings changed: {'; '.join(moved)}." * bool(moved)
