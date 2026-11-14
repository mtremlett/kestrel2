"""The step of units: a pound line that falls by the dollar's rate in a day is not judged."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal

import pytest

from desk.lines import LINES
from desk.store import Bar
from lab import units

VUSA = next(line for line in LINES if line.symbol == "VUSA")
DAY, RATE = date(2020, 1, 1), Decimal("0.8")


def _bars(*closes: str) -> list[Bar]:
    made = (Decimal(c) for c in closes)
    return [Bar(DAY + timedelta(n), c, c, c, c, 1) for n, c in enumerate(made)]


def test_a_close_that_moves_by_the_rate_overnight_on_a_pound_line_is_refused_by_its_day() -> None:
    rates = {DAY + timedelta(n): RATE for n in range(4)}
    units.refuse(VUSA, _bars("10", "10.3", "10.2", "10.1"), rates)  #: a market's move
    units.refuse(VUSA, _bars("10", "8.1", "9"), {})  #: no rate that day, nothing to match
    for steps in (("10", "10", "8.1"), ("10", "10", "12.4")):
        with pytest.raises(ValueError, match="step of units on 2020-01-03"):
            units.refuse(VUSA, _bars(*steps), rates)
    named = replace(VUSA, real_moves=frozenset({(DAY + timedelta(2), Decimal("0.8"))}))
    units.refuse(named, _bars("10", "10", "8.1"), rates)  #: the master names it real
    dollars = replace(VUSA, currency="USD")
    units.refuse(dollars, _bars("10", "10", "8.1"), rates)  #: only a pound line steps
