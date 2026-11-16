"""conformance_soak - THE CONFORMANCE SOAK (R-RUNNER-223, his list of 16 November 2026):

    python -m desk.paper --conformance london|us --soak

One conformance round of one share, then exit; it may run many times a day, hourly in the
venue's hours. It is the conformance run (conformance.trade, given to it) and nothing more:
each round's order ids carry its own minute (the plan's stamp), so none reuses an earlier
round's. A round inside a desk round (08:00-08:30 and 14:30-15:00 UK, five minutes either
side) or outside its venue's hours sends nothing and says which. Every round, done or
refused, is its own line in the soak ledger (`soak.csv`), so a day is read in one place."""

from __future__ import annotations

import csv
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

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
