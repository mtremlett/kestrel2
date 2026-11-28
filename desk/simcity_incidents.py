"""simcity_incidents: SimCity's scenario for the night of 23 November, when desk-day died on
ValueError 'not the desk's records' (the live records.csv was written before the FX columns)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from desk import day

if TYPE_CHECKING:
    from desk.simcity import _Life

OLD = "records kept before currency and interest are read, never refused, and the day goes on"
_NAMES = "day,profit,commission,spread,slippage,currency,uk_taxes,market,worth,counted,heat"
_FIRST = "2026-11-16,-35.95,3.76,1.85,1.85,0.55,0.00,-36.26,3675.63,2,163.15,,0"


def old_records(life: _Life, on: date) -> None:
    """A records.csv in the header the desk wrote before the FX columns lies in the records'
    folder: it must be read as its one record, with its currency charge in place."""
    folder = life.desk / "old-records"
    folder.mkdir(exist_ok=True)
    (folder / day.RECORDS).write_text(f"{_NAMES},halted,stopped,differ\n{_FIRST}\n", "utf-8")
    try:
        kept = day.records(folder)
        read = [(r.day, r.profit, r.costs.currency) for r in kept] == [
            (date(2026, 11, 16), Decimal("-35.95"), Decimal("0.55"))
        ]
    except ValueError:  #: the refusal of 23 November: the promise fails, the day goes on
        read = False
    life.promise(OLD, read)
    life.live(on)
