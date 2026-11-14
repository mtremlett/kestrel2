"""Known answer: the published stage-analysis rule fixes the entry and exit days of a series."""

from datetime import date, timedelta
from decimal import Decimal

from desk.eponymous_weinstein_stage import decide
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


def test_buys_a_break_above_a_rising_thirty_week_average_and_sells_the_close_below_it() -> None:
    # 150 flat days (idx 0-149) fill the 150-day average; 110..114 lift it. On idx 154 the
    # average has a week of history, is above its value on idx 149, and the close is above it:
    # BUY on 154 only. 115 holds; 50 closes below the average: SELL on 156.
    assert _trades([*[100] * 150, 110, 111, 112, 113, 114, 115, 50]) == {
        154: Action.BUY,
        156: Action.SELL,
    }


def test_waits_for_a_rising_average_over_a_year_of_history_and_a_close_above_it() -> None:
    assert _trades([*range(300, 150, -1), *[240] * 6]) == {}  # above a FALLING average
    assert _trades([*range(100, 200)]) == {}  # under 150 days of history
    assert _trades([*range(100, 250), 90, 90, 90, 90, 90, 90]) == {}  # rising, but closed below
