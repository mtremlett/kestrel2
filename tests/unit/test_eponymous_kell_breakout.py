"""Known answer: Kell's base-and-break rule fixes the entry and exit days of a made-up series."""

from datetime import date, timedelta
from decimal import Decimal

from desk.eponymous_kell_breakout import decide
from desk.store import Bar
from desk.strategy import Action


def _trades(closes: list[int]) -> dict[int, Action]:
    bars = [
        Bar(date(2020, 1, 1) + timedelta(days=n), Decimal(c), Decimal(c), Decimal(c), Decimal(c), 1)
        for n, c in enumerate(closes)
    ]
    return {n: d.action for n, d in enumerate(decide({"X": bars})) if d.action is not Action.HOLD}


def test_buys_the_close_over_the_base_and_sells_under_the_ten_day_average() -> None:
    # 25 days at 100 are the base. 110 is over its high, and over the 10-day (101.8) and 20-day
    # (100.95) averages: BUY on day 25. 112 and 114 stay over the 10-day average. 100 falls
    # under it (104.4): SELL on day 28. A later 100 breaks nothing.
    assert _trades([100] * 25 + [110, 112, 114, 100, 100]) == {25: Action.BUY, 28: Action.SELL}


def test_waits_for_a_full_base_and_for_a_close_strictly_over_it() -> None:
    assert _trades([100] * 19 + [110]) == {}  # only 19 sessions of base
    assert _trades([100] * 25 + [100, 100]) == {}  # a tie with the base's high is no break
