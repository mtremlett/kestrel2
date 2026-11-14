"""Known answer: the published RSI-2 rule fixes the entry and exit days of a made-up series."""

from datetime import date, timedelta
from decimal import Decimal

from desk.eponymous_connors import decide
from desk.store import Bar
from desk.strategy import Action


def _bars(closes: list[int]) -> list[Bar]:
    return [
        Bar(date(2020, 1, 1) + timedelta(days=n), Decimal(c), Decimal(c), Decimal(c), Decimal(c), 1)
        for n, c in enumerate(closes)
    ]


def _trades(closes: list[int]) -> dict[int, Action]:
    got = decide({"X": _bars(closes)})
    return {n: d.action for n, d in enumerate(got) if d.action is not Action.HOLD}


def test_buys_the_dip_in_an_uptrend_and_sells_above_the_five_day_average() -> None:
    # 200 days up by 1; a fall of 10 makes the 2-day RSI 9.09 (under 10) with the close above
    # its 200-day average: BUY on day 200. 290 is under the 5-day average 294.6: held. 300 is
    # over 295.2: SELL on day 202. Every other day: nothing.
    assert _trades([*range(100, 300), 289, 290, 300, 301, 302]) == {
        200: Action.BUY,
        202: Action.SELL,
    }


def test_waits_for_two_hundred_days_and_for_the_uptrend() -> None:
    dip = [*range(100, 150), 139]
    assert _trades(dip) == {}  # the same dip with under 200 days of history
    assert _trades([*range(400, 200, -1), 150, 140]) == {}  # a fall below the 200-day average
