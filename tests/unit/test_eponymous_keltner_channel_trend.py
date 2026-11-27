"""Known answer: Keltner's published channel rule fixes the entry and exit days of a series."""

from datetime import date, timedelta
from decimal import Decimal

from desk import eponymous_keltner_channel_trend
from desk.eponymous_keltner_channel_trend import decide
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
    got = decide({"X": bars})
    return {n: d.action for n, d in enumerate(got) if d.action is not Action.HOLD}


def test_buys_over_the_upper_band_holds_inside_it_and_sells_under_the_lower_band() -> None:
    # Ten days at 100 (range 2): day 10 closes 110 over centre 101 + 2 = 103: BUY. Days 11-14
    # stay at 110 inside or over the band: nothing. Day 15 closes 90 under centre 104 - 2: SELL.
    # Day 16 at 90 is under the lower band and not over the upper: stays out.
    assert _trades([*[100] * 10, *[110] * 5, 90, 90]) == {10: Action.BUY, 15: Action.SELL}


def test_waits_for_ten_days_and_for_a_close_clear_of_the_band() -> None:
    assert _trades([*[100] * 5, *[120] * 3]) == {}  # under ten days of history
    assert _trades([*[100] * 10, 102]) == {}  # 102 is inside 101 + 2 = 103


def test_declares_no_holding_period_and_says_why() -> None:
    # his ruling 21 Nov: each rule's hold limit is its own sell logic's; stated, no time stop
    assert "Holding period: none" in eponymous_keltner_channel_trend.__doc__
    assert all(r.declared.hold is None for r in eponymous_keltner_channel_trend.EPONYMOUS.values())
