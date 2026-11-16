"""Known answer: the published Double 7's rule fixes the entry and exit days of a series."""

from datetime import date, timedelta
from decimal import Decimal

from desk.eponymous_connors_double_7 import decide
from desk.store import Bar
from desk.strategy import Action


def _trades(closes: list[int]) -> dict[int, Action]:
    bars = [
        Bar(date(2020, 1, 1) + timedelta(n), *(Decimal(c),) * 4, 1) for n, c in enumerate(closes)
    ]
    got = decide({"X": bars})
    return {n: d.action for n, d in enumerate(got) if d.action is not Action.HOLD}


def test_buys_a_seven_day_closing_low_in_an_uptrend_and_sells_a_seven_day_closing_high() -> None:
    # 200 days up by 1 to 299, then 290: the lowest close of 7 and over the 200-day average,
    # BUY on day 200. 295 is no high of 7 (299 is in the window); 300 is: SELL on day 202.
    assert _trades([*range(100, 300), 290, 295, 300, 301]) == {200: Action.BUY, 202: Action.SELL}


def test_waits_for_a_low_the_uptrend_and_two_hundred_days() -> None:
    assert _trades([*range(100, 300), 299, 301]) == {}  # no low of 7 closes
    assert _trades([*range(400, 200, -1), 190]) == {}  # below the 200-day average
    assert _trades([*range(100, 150), 140]) == {}  # under 200 days of history
