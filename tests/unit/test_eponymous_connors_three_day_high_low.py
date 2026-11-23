"""Known answer: the published three-day high/low rule fixes the entry and exit days of a series."""

from datetime import date, timedelta
from decimal import Decimal

from desk.eponymous_connors_three_day_high_low import decide
from desk.store import Bar
from desk.strategy import Action


def _bars(closes: list[int]) -> list[Bar]:
    return [
        Bar(
            date(2020, 1, 1) + timedelta(days=n),
            Decimal(c),
            Decimal(c + 1),
            Decimal(c - 1),
            Decimal(c),
            1,
        )
        for n, c in enumerate(closes)
    ]


def _trades(closes: list[int]) -> dict[int, Action]:
    got = decide({"X": _bars(closes)})
    return {n: d.action for n, d in enumerate(got) if d.action is not Action.HOLD}


def test_buys_the_third_lower_day_in_an_uptrend_and_sells_above_the_five_day_average() -> None:
    # 200 days up by 1, then 297, 295, 293: days 200, 201, 202 each have a lower high and low
    # than the day before, with the close over its 200-day average: BUY on day 202 only. 300
    # is over the 5-day average 296.8: SELL on day 203. Every other day: nothing.
    assert _trades([*range(100, 300), 297, 295, 293, 300, 301]) == {
        202: Action.BUY,
        203: Action.SELL,
    }


def test_waits_for_the_third_day_the_uptrend_and_two_hundred_days() -> None:
    assert _trades([*range(100, 300), 297, 295, 300, 301]) == {}  # two lower days, not three
    assert _trades([*range(100, 300), 297, 295, 299, 297, 295]) == {}  # the run was broken
    assert _trades([*range(400, 200, -1), 150, 140, 130]) == {}  # below the 200-day average
    assert _trades([*range(100, 150), 147, 145, 143]) == {}  # under 200 days of history
