"""simcity_incidents: SimCity's scenario for the night of 23 November, when desk-day died on
ValueError 'not the desk's records' (the live records.csv was written before the FX columns)."""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from desk import day_parts

if TYPE_CHECKING:
    from desk.simcity import _Life

OLD = "records kept before currency and interest are read, never refused, and the day goes on"
_NAMES = "day,profit,commission,spread,slippage,currency,uk_taxes,market,worth,counted,heat"
_FIRST = "2026-11-16,-35.95,3.76,1.85,1.85,0.55,0.00,-36.26,3675.63,2,163.15,,0"


def old_records(life: _Life, on: date) -> None:
    """A records.csv in the header written before the FX columns: read as its one record, its
    currency charge in place."""
    try:
        rows = list(csv.reader([f"{_NAMES},halted,stopped,differ", _FIRST]))
        kept = day_parts._made(rows)  # noqa: SLF001  #: read by lines: the day's file counts are the real files'
        read = [(r.day, r.profit, r.costs.currency) for r in kept] == [
            (date(2026, 11, 16), Decimal("-35.95"), Decimal("0.55"))
        ]
    except ValueError:  #: the refusal of 23 November: the promise fails, the day goes on
        read = False
    life.promise(OLD, read)
    life.live(on)
