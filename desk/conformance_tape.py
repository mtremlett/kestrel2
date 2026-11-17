"""conformance_tape - what the conformance run needs to know of the desk beside it: a desk
round's hours (no run begins within LEAD minutes of one), the desk's own share of the account read
before a run, whether a holding of the desk's moved while the run was made, and the soak: one
conformance round, its line kept in the soak ledger (`soak.csv`, R-RUNNER-223)."""

from __future__ import annotations

import csv
from collections.abc import Callable, Mapping
from datetime import date, datetime, timedelta
from datetime import time as hour
from decimal import Decimal
from pathlib import Path

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


Round = Callable[[Path, str, Callable[[], datetime]], tuple[bool, str]]  #: conformance.trade
LEDGER, HEAD = "soak.csv", ("at", "market", "answer")


def soak(root: Path, market: str, clock: Callable[[], datetime], trade: Round) -> tuple[bool, str]:
    """One round, and its line in the ledger: whether all is well, and the round's one line."""
    now = clock()
    good, line = trade(root, market, clock)
    path = root / LEDGER
    fresh = not path.exists()
    root.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as kept:
        out = csv.writer(kept)
        if fresh:
            out.writerow(HEAD)
        out.writerow((now.isoformat(), market, line))
    return good, line
