"""Known answer: the published %R rule fixes the entry and exit days of a series."""

from datetime import date, timedelta
from decimal import Decimal

from desk.eponymous_williams_r import decide
from desk.store import Bar
from desk.strategy import Action


def _trades(closes: list[int]) -> dict[int, Action]:
    bars = [
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
    return {n: d.action for n, d in enumerate(decide({"X": bars})) if d.action is not Action.HOLD}


def test_buys_in_the_bottom_tenth_of_the_ten_day_range_and_sells_in_the_top_tenth() -> None:
    # Nine days at 100 then 90: range 89 to 101, %R = -91.7 (at or below -90): BUY on day 9. Then
    # 100: %R = -8.3 (at or above -10): SELL on day 10. Every other day: nothing.
    assert _trades([*[100] * 9, 90, 100, 100]) == {9: Action.BUY, 10: Action.SELL}


def test_waits_for_the_oversold_band_and_ten_days() -> None:
    assert _trades([*[100] * 9, 94]) == {}  # %R = -87.5, not oversold
    assert _trades([*[100] * 5, 90]) == {}  # under ten days of history
    assert _trades([*[100] * 9, 90, 95, 95]) == {9: Action.BUY}  # %R -50: held, not sold
