"""coverage - how much history each line holds, and how much of the desk is parked (DQ-01)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from desk.store_parts import Bar

TIMES = 2  #: a line needs history this many times the longest lookback a rule uses
A_GATE_YEARS = 5  #: and, whatever the lookback, this many years by the A-GATE
PARKED_CAP = Decimal("0.2")  #: the most of the lines that may be parked before the desk is unfit


@dataclass(frozen=True)
class Coverage:
    """One line's history held, measured by `measure`."""

    symbol: str
    sessions: int
    first: date | None  #: the oldest session held; None when the line holds none
    enough: bool  #: sessions at least TIMES the longest lookback, spanning A_GATE_YEARS


def measure(symbol: str, bars: Sequence[Bar], longest: int, today: date) -> Coverage:
    """A line's coverage on `today` against the longest lookback (in sessions) any rule reads."""
    first = min((b.day for b in bars), default=None)
    long_enough = first is not None and (today - first).days >= A_GATE_YEARS * 365
    return Coverage(symbol, len(bars), first, long_enough and len(bars) >= TIMES * longest)


def short(held: Mapping[str, Sequence[Bar]], longest: int, today: date) -> tuple[str, ...]:
    """The symbols whose history is not enough, in the order given."""
    return tuple(s for s, bars in held.items() if not measure(s, bars, longest, today).enough)


def parked_share(parked: int, lines: int) -> Decimal:
    """The share of the lines parked; refuses a desk of no lines."""
    if lines <= 0:
        raise ValueError(f"a share of {lines} lines")
    return Decimal(parked) / Decimal(lines)


def fit(parked: int, lines: int) -> bool:
    """Whether the parked share is within PARKED_CAP."""
    return parked_share(parked, lines) <= PARKED_CAP
