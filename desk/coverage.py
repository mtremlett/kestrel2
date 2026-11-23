"""coverage - HOW MUCH HISTORY THE STORE HOLDS FOR EACH LINE, and whether the desk may trust it.

A line needs sessions enough for twice the longest lookback any rule uses (DAT-03), five years
for the A-GATE. A parked line scores nothing. The desk's score is the mean of its lines'; the
desk is fit to trade only while the parked share stays under its cap (DQ-01)."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from decimal import Decimal

from desk.strategy import SWEEPS

#: sessions: the longest setting the grid may try on any rule (desk/strategy.py's SWEEPS)
LOOKBACK = max(int(v) for sweep in SWEEPS.values() for vs in sweep.values() for v in vs)
NEED = 2 * LOOKBACK  #: sessions a line must hold before a rule may trade it
A_GATE = 5 * 252  #: sessions: five years, the history the A-GATE judges on
PARKED_CAP = Decimal("0.10")  #: the most of the lines that may stand parked


@dataclass(frozen=True)
class Coverage:
    """One line's sessions held, whether they are enough, and its score from 0 to 1."""

    symbol: str
    sessions: int
    enough: bool
    score: Decimal


def measure(held: Mapping[str, int], parked: Collection[str]) -> tuple[Coverage, ...]:
    """Each line's coverage, by symbol: sessions held against NEED; a parked line scores 0."""
    return tuple(
        Coverage(
            symbol,
            sessions,
            sessions >= NEED and symbol not in parked,
            Decimal(0) if symbol in parked else Decimal(min(sessions, A_GATE)) / A_GATE,
        )
        for symbol, sessions in sorted(held.items())
    )


def desk_score(lines: tuple[Coverage, ...]) -> Decimal:
    """The desk's quality: the mean of its lines' scores (0 for no lines)."""
    return sum((c.score for c in lines), Decimal(0)) / len(lines) if lines else Decimal(0)


def parked_within_cap(held: Mapping[str, int], parked: Collection[str]) -> bool:
    """True while the parked share of the lines held is no more than PARKED_CAP."""
    return Decimal(len(set(parked) & held.keys())) <= PARKED_CAP * len(held)
