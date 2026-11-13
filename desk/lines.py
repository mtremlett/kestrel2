"""lines - THE INSTRUMENT MASTER. Facts about a line come from here, never from its name."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from desk import venues


@dataclass(frozen=True)
class Line:
    symbol: str
    venue: str  #: "LSE" or "US"; each venue keeps its own calendar
    currency: str  #: the currency its prices are quoted in: "GBP" or "USD"
    #: Days a close moved further than the store believes a market moves, recorded as real:
    #: a crash or a jump, confirmed, never a split (the archive's prices must be adjusted).
    real_moves: frozenset[date] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if self.venue not in venues.RULES:
            raise ValueError(f"{self.symbol}: no calendar for venue {self.venue!r}")
