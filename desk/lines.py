"""lines - THE INSTRUMENT MASTER. Facts about a line come from here, never from its name."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Line:
    symbol: str
    venue: str  #: "LSE" or "US"; each venue keeps its own calendar
    currency: str  #: the currency its prices are quoted in: "GBP" or "USD"
