"""broker - THE PRETEND BROKER the desk trades against in simulation. It behaves like the
real one: its own execution ids, stops resting at the broker, and faults on request."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from desk.lines import Line
from desk.store import Bar


@dataclass(frozen=True)
class Fill:
    execution_id: str  #: the broker's own id, never the desk's
    order_id: str
    symbol: str
    quantity: int  #: positive bought, negative sold
    price: Decimal


class Fault(Enum):
    REJECT = "reject"
    PARTIAL = "partial fill"
    DISCONNECT = "disconnection"
    CRASH = "the desk dies after the broker has the order"


class Crash(Exception):
    """The desk died mid-send: the broker has the order and the desk has no answer."""


class Pretend:
    def __init__(self, archive: Mapping[Line, Sequence[Bar]], faults: Mapping[str, Fault]) -> None:
        """Fills at the archive's prices; a fault applies to a symbol's first order."""
        raise NotImplementedError("broker.Pretend: the pretend broker is phase 2")

    def open(self, day: date) -> None:
        """The market opens on day: orders fill at its prices and resting stops are tested."""
        raise NotImplementedError("broker.Pretend.open: phase 2")

    def submitted(self) -> tuple[str, ...]:
        """Every order id received, once for each time it was received."""
        raise NotImplementedError("broker.Pretend.submitted: phase 2")

    def fills(self) -> tuple[Fill, ...]:
        raise NotImplementedError("broker.Pretend.fills: phase 2")

    def positions(self) -> dict[str, int]:
        raise NotImplementedError("broker.Pretend.positions: phase 2")

    def resting_stops(self) -> dict[str, tuple[int, Decimal]]:
        """Every stop resting at the broker: the shares it would sell, and its level."""
        raise NotImplementedError("broker.Pretend.resting_stops: phase 2")

    def inject(self, symbol: str, quantity: int) -> None:
        """A position the desk did not make, as if bought by hand."""
        raise NotImplementedError("broker.Pretend.inject: phase 2")
