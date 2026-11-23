"""Known answer: Bollinger's squeeze fixes the entry and exit days of a made-up series."""

from datetime import date, timedelta
from decimal import Decimal

from desk.eponymous_bollinger_squeeze import decide
from desk.store import Bar
from desk.strategy import Action


def _trades(closes: list[int]) -> dict[int, Action]:
    bars = [
        Bar(date(2020, 1, 1) + timedelta(days=n), Decimal(c), Decimal(c), Decimal(c), Decimal(c), 1)
        for n, c in enumerate(closes)
    ]
    got = decide({"X": bars})
    return {n: d.action for n, d in enumerate(got) if d.action is not Action.HOLD}


def test_buys_the_breakout_from_a_squeeze_and_sells_under_the_middle_band() -> None:
    # 146 flat days: the bands have no width, the narrowest in six months. A close of 110 is far
    # over the upper band (104.9): BUY on day 146. 110 again stays over the 101 average: held.
    # 90 is under the average 100.5: SELL on day 148.
    assert _trades([100] * 146 + [110, 110, 90]) == {146: Action.BUY, 148: Action.SELL}


def test_no_buy_without_a_squeeze_or_six_months_of_history() -> None:
    widening = [100 + (n % 2) * (1 + n // 50) for n in range(146)]
    assert _trades([*widening, 200]) == {}  # bands wider than ever: no squeeze
    assert _trades([100] * 100 + [110]) == {}  # under six months of band widths
