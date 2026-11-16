"""records - THE TYPED RECORDS OF THE PRICE STORE: a bar, a fault found in bars, the archive's
refusal and a parked line. Plain frozen data; the store (desk/store.py) owns every rule."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Bar:
    day: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    def scaled(self, unit: Decimal) -> Bar:
        """The same bar with every price times unit (pence to pounds is 0.01)."""
        prices = (self.open * unit, self.high * unit, self.low * unit, self.close * unit)
        return Bar(self.day, *prices, self.volume)


@dataclass(frozen=True)
class Fault:
    day: date  #: the session it concerns
    what: str
    lasting: bool = False  #: a step in the price: wrong for every bar before it, however old


@dataclass(frozen=True)
class Refused:
    """The archive's answer for a line it would not, or could not, give."""

    reason: str


@dataclass(frozen=True)
class Parked:
    symbol: str
    reason: str
    day: date
