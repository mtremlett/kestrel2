"""streak - FIRST-LIGHT COUNTED BY THE DESK ITSELF (NS-10): ten consecutive days that each
count, from the day records alone. A day counts only by day.Record's verdict (its book was the
broker's, no halt in force, its orders sent and none stopped), so a day that sent nothing is
never green; the records hold every session in order (day._kept), so adjacent records are
adjacent sessions and one day that does not count ends the run."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from desk.day import Record

NEEDED = 10  #: the days in a row that make FIRST-LIGHT


@dataclass(frozen=True)
class Streak:
    """The run of counting days that ends the records, and the last day that broke one."""

    days: int
    broke: date | None  #: the latest day that did not count; None, none has not

    @property
    def reached(self) -> bool:
        """FIRST-LIGHT: the run is ten days or more."""
        return self.days >= NEEDED

    def says(self) -> str:
        """The run in plain English, for the operator."""
        if self.reached:
            return f"FIRST-LIGHT: {self.days} clean days in a row."
        since = f", since {self.broke} did not count" * (self.broke is not None)
        return f"{self.days} of {NEEDED} clean days in a row{since}."


def count(records: Sequence[Record]) -> Streak:
    """The streak the records, oldest first, end with."""
    days = 0
    for record in reversed(records):
        if not record.counts:
            return Streak(days, record.day)
        days += 1
    return Streak(days, None)
