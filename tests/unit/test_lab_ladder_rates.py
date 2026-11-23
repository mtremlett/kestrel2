"""The ladder's rates have one door (his 22 Nov, "paramount"): the pound's bars are asked of the
source the caller passes, the history database, once, to the window's end; no source, no rates."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from desk.command import POUND
from desk.lines import Line
from desk.store import Bar
from lab import ladder


def test_the_rates_come_only_through_the_door_they_are_given() -> None:
    day, asked = date(2020, 1, 6), []

    def ask(line: Line, before: date) -> list[Bar]:
        asked.append((line, before))
        closes = [(day, "1.25"), (day + timedelta(1), "1.6"), (ladder.END, "1.28")]
        return [Bar(d, Decimal(c), Decimal(c), Decimal(c), Decimal(c), 0) for d, c in closes]

    first = ladder.rates(ask)
    assert asked == [(POUND, ladder.END + timedelta(1))] and day not in first
    assert (first[day + timedelta(1)], first[day + timedelta(2)]) == (
        Decimal("0.8"),
        Decimal("0.625"),
    )
    with pytest.raises(ValueError, match="no source of the pound's bars"):
        ladder.rates()
