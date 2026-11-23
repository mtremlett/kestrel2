"""Known answer: the published momentum rule fixes the entry and exit days of a made-up series."""

from datetime import date, timedelta
from decimal import Decimal

from desk.eponymous_clenow_momentum import decide
from desk.store import Bar
from desk.strategy import Action


def _trades(closes: list[int]) -> dict[int, Action]:
    bars = [
        Bar(date(2020, 1, 1) + timedelta(days=n), Decimal(c), Decimal(c), Decimal(c), Decimal(c), 1)
        for n, c in enumerate(closes)
    ]
    return {n: d.action for n, d in enumerate(decide({"X": bars})) if d.action is not Action.HOLD}


def test_buys_a_steady_climb_once_the_average_is_full_and_sells_below_it() -> None:
    # 100 closes up by 1 (under 1.1% a day): the average is full on day 99, the close is
    # above it and the score positive: BUY. 120 is under the average (and a 40% move): SELL.
    assert _trades([*range(100, 200), 120, 121]) == {99: Action.BUY, 100: Action.SELL}


def test_sells_on_a_fifteen_percent_move_even_above_the_average() -> None:
    # 230 is 15.6% over 199 and far above the average, yet the move alone ends the holding;
    # the same move in the window also stops a buy.
    assert _trades([*range(100, 200), 230]) == {99: Action.BUY, 100: Action.SELL}
    assert _trades([*range(100, 199), 240]) == {}


def test_waits_for_a_full_average_and_for_a_rising_trend() -> None:
    assert _trades([*range(100, 190)]) == {}  # 90 days only: no 100-day average yet
    assert _trades([*range(300, 200, -1)]) == {}  # a fall: under its average
