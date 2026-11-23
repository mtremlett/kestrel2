"""Known answer: Zanger's breakout rule fixes the entry and exit days of a made-up series."""

from datetime import date, timedelta
from decimal import Decimal

from desk.eponymous_dan_zanger import decide
from desk.store import Bar
from desk.strategy import Action

BASE = [(100, 101, 1000)] * 50  # fifty quiet sessions: close, high, volume


def _trades(days: list[tuple[int, int, int]]) -> dict[int, Action]:
    bars = [
        Bar(date(2020, 1, 1) + timedelta(n), Decimal(c), Decimal(h), Decimal(c), Decimal(c), v)
        for n, (c, h, v) in enumerate(days)
    ]
    got = decide({"X": bars})
    return {n: d.action for n, d in enumerate(got) if d.action is not Action.HOLD}


def test_buys_the_heavy_volume_breakout_and_sells_under_the_ten_day_average() -> None:
    # Day 50 clears the 50-day high on light volume: no buy. Day 51 clears it again on 2x the
    # 50-day volume: BUY. Days 52-53 stay over the 10-day average (101.4): held. Day 54 closes
    # at 90, under the average 100.4: SELL.
    days = [*BASE, (102, 102, 1000), (103, 103, 2000), (104, 104, 1000), (105, 105, 1000)]
    assert _trades([*days, (90, 90, 1000)]) == {51: Action.BUY, 54: Action.SELL}


def test_waits_for_fifty_days_and_for_a_breakout_on_heavy_volume() -> None:
    assert _trades([(100, 101, 1000)] * 49 + [(110, 110, 9000)]) == {}  # under 50 days seen
    assert _trades([*BASE, (100, 100, 9000)]) == {}  # heavy volume, no breakout
