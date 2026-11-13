"""day - THE DESK'S DAY: prepare the data, decide, size, send, reconcile, publish one record.
The same days run again from the same saved data give the same records."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from desk.broker import Pretend
from desk.lines import Line
from desk.orders import Settings
from desk.store import Bar


@dataclass(frozen=True)
class Costs:
    """Every cost line, in pounds. A record cannot be made with one missing."""

    commission: Decimal
    spread: Decimal
    slippage: Decimal
    currency: Decimal
    uk_taxes: Decimal


@dataclass(frozen=True)
class Record:
    day: date
    profit: Decimal | None  #: after every cost; None when the book is not the broker's
    costs: Costs
    market: Decimal  #: what simply holding the market would have earned
    mismatches: tuple[str, ...]  #: lines where the desk's book and the broker's differ


def run(
    root: Path,
    archive: Mapping[Line, Sequence[Bar]],
    broker: Pretend,
    settings: Settings,
    day: date,
) -> Record:
    raise NotImplementedError("day.run: the desk's day is phase 2")
