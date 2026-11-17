"""Coverage: history against the longest lookback, and the parked share."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from desk import coverage
from desk.store_parts import Bar

TODAY = date(2026, 11, 17)


def _bars(count: int, days_apart: int = 1) -> list[Bar]:
    one = Decimal(1)
    return [
        Bar(TODAY - timedelta(days=n * days_apart), one, one, one, one, 1) for n in range(count)
    ]


def test_a_line_is_enough_only_with_twice_the_lookback_across_five_years() -> None:
    held = {
        "OLD": _bars(500, 4),  # 500 sessions over 2,000 days: enough
        "DENSE": _bars(500),  # 500 sessions, under two years
        "THIN": _bars(399, 5),  # five years, one session short of twice 200
        "NONE": [],
    }
    assert coverage.short(held, 200, TODAY) == ("DENSE", "THIN", "NONE")
    assert coverage.measure("OLD", held["OLD"], 200, TODAY).first == TODAY - timedelta(days=1996)
    assert coverage.measure("NONE", [], 200, TODAY).first is None


@pytest.mark.parametrize(("parked", "fit"), [(0, True), (4, True), (5, False)])
def test_the_desk_is_fit_while_a_fifth_of_its_lines_or_fewer_are_parked(
    parked: int, fit: bool
) -> None:
    assert coverage.fit(parked, 20) is fit
    with pytest.raises(ValueError, match="0 lines"):
        coverage.fit(0, 0)
