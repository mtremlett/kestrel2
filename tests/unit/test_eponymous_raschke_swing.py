"""Known answer: the published Turtle Soup rule fixes the entry and exit days of a series."""

from datetime import date, timedelta
from decimal import Decimal

from desk.eponymous_raschke_swing import decide
from desk.store import Bar
from desk.strategy import Action

FLAT = (109, 110)  # (low, close)


def _trades(days: list[tuple[int, int]]) -> dict[int, Action]:
    bars = [
        Bar(date(2020, 1, 1) + timedelta(n), Decimal(c), Decimal(c + 1), Decimal(lo), Decimal(c), 1)
        for n, (lo, c) in enumerate(days)
    ]
    return {n: d.action for n, d in enumerate(decide({"X": bars})) if d.action is not Action.HOLD}


def test_buys_a_failed_new_low_and_sells_under_the_buying_days_low() -> None:
    # day 0 sets the 20-day low 99; day 20 undercuts it (98): the setup. Day 21 holds 98 and
    # closes back over 99: BUY. Day 22 closes 97, under the setup low 98: SELL. Nothing else.
    days = [(99, 100), *[FLAT] * 19, (98, 100), (99, 106), (96, 97)]
    assert _trades(days) == {21: Action.BUY, 22: Action.SELL}


def test_the_older_low_must_be_four_sessions_old_and_the_close_back_over_it() -> None:
    assert _trades([*[FLAT] * 16, (99, 100), *[FLAT] * 3, (98, 105), (99, 106)]) == {21: Action.BUY}
    assert _trades([*[FLAT] * 17, (99, 100), *[FLAT] * 2, (98, 105), (99, 106)]) == {}  # 3 old
    assert _trades([(99, 100), *[FLAT] * 19, (97, 98), (96, 97)]) == {}  # new low, stop hit
    assert _trades([(99, 100), *[FLAT] * 19, (97, 98), (97, 98)]) == {}  # no close over 99
    assert _trades([(99, 100), *[FLAT] * 18, (98, 105), (99, 106)]) == {}  # under 20 days
