"""store - THE ONE PRICE STORE AND ITS ONE WRITER. Bars are cleaned once, on entry; a line
that cannot be made clean is parked with a reason and a date, and the others carry on."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from desk.lines import Line


@dataclass(frozen=True)
class Bar:
    day: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


@dataclass(frozen=True)
class Parked:
    symbol: str
    reason: str
    day: date


def prepare(root: Path, archive: Mapping[Line, Sequence[Bar]], day: date) -> tuple[Parked, ...]:
    """Clean the archive's bars into the store at root, ready to trade on day."""
    raise NotImplementedError("store.prepare: cleaning on entry is phase 1")


def read(root: Path, symbol: str) -> tuple[Bar, ...]:
    """Every clean bar the store holds for one line, oldest first."""
    raise NotImplementedError("store.read: the store is phase 1")
