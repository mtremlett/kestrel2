"""Known answer: Zweig's breadth thrust fixes the entry and exit days of a made-up series."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from desk.eponymous_zweig_breadth_thrust import HOLD, Breadth, decide
from desk.store import Bar
from desk.strategy import Action


def _trades(percent_up: list[int]) -> dict[int, Action]:
    days = [date(2020, 1, 1) + timedelta(days=n) for n in range(len(percent_up))]
    bars = [Bar(d, Decimal(1), Decimal(1), Decimal(1), Decimal(1), 1) for d in days]
    breadth = {d: Breadth(p, 100 - p) for d, p in zip(days, percent_up, strict=True)}
    return {
        n: d.action
        for n, d in enumerate(decide({"X": bars}, breadth))
        if d.action is not Action.HOLD
    }


def test_buys_the_thrust_and_sells_after_eleven_months() -> None:
    # 20 days at 30% up seed the 10-day average at 0.30; days at 90% lift it to 0.631 on the
    # fourth (index 23), over 0.615 with 0.30 inside the window: BUY. SELL HOLD sessions later.
    assert _trades([30] * 20 + [90] * (HOLD + 20)) == {23: Action.BUY, 23 + HOLD: Action.SELL}


def test_no_thrust_when_the_climb_is_slow_or_never_started_low() -> None:
    assert _trades([50] * 20 + [90] * 20) == {}  # the average never fell under 0.40
    assert _trades([30] * 20 + [65] * 40) == {}  # over 0.615 only after 12 days: too slow


def test_a_day_without_breadth_fails_loudly_and_an_empty_day_is_refused() -> None:
    bars = [Bar(date(2020, 1, 1), *[Decimal(1)] * 4, 1)]
    with pytest.raises(KeyError, match="no breadth"):
        decide({"X": bars}, {})
    with pytest.raises(ValueError, match="advances or declines"):
        Breadth(0, 0)
