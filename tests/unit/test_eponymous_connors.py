"""Known answer: the published RSI-2 rule fixes the entry and exit days of a made-up series."""

from datetime import date, timedelta
from decimal import Decimal

from desk import eponymous_connors
from desk.eponymous_connors import decide, decide_percent_b
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


def test_percent_b_buys_after_three_low_days_and_sells_over_point_eight() -> None:
    # 200 days up by 1, then 280, 275, 270: %b is 0.088, -0.061, -0.124 (under 0.2 three days
    # running, above the 200-day average): BUY on day 202. 285 -> 0.375, 295 -> 0.694: held.
    # 300 -> 0.824, over 0.8: SELL on day 205.
    closes = [*range(100, 300), 280, 275, 270, 285, 295, 300, 310]
    got = decide_percent_b({"X": _bars(closes)})
    assert {n: d.action for n, d in enumerate(got) if d.action is not Action.HOLD} == {
        202: Action.BUY,
        205: Action.SELL,
    }
    two_low = decide_percent_b({"X": _bars([*range(100, 300), 280, 275, 285])})
    assert all(d.action is Action.HOLD for d in two_low)  # only two low days: no buy


def test_declares_no_holding_period_and_says_why() -> None:
    # his ruling 21 Nov: the sale is the rule's own sell logic alone, no time stop; stated
    assert "Holding period: none" in eponymous_connors.__doc__
    rules = eponymous_connors.EPONYMOUS.values()
    assert all(r.declared.hold is None for r in rules)
