"""Known answer: the published Turtle Soup rule fixes the entry and exit days of a series."""

from datetime import date, timedelta
from decimal import Decimal

from desk import eponymous_raschke_swing
from desk.eponymous_raschke_swing import RaschkeTurtleSoup, decide
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
    # day 0 sets the 20-day low 99; day 20 undercuts it (98) and closes back over it: BUY.
    # day 21 holds; day 22 closes 97, under the buying day's low 98: SELL. Nothing else.
    days = [(99, 100), *[FLAT] * 19, (98, 105), (100, 106), (96, 97)]
    assert _trades(days) == {20: Action.BUY, 22: Action.SELL}


def test_the_older_low_must_be_four_sessions_old_and_the_close_back_over_it() -> None:
    assert _trades([*[FLAT] * 16, (99, 100), *[FLAT] * 3, (98, 105)]) == {20: Action.BUY}
    assert _trades([*[FLAT] * 17, (99, 100), *[FLAT] * 2, (98, 105)]) == {}  # three sessions old
    assert _trades([(99, 100), *[FLAT] * 19, (97, 98)]) == {}  # no close back over 99
    assert _trades([(99, 100), *[FLAT] * 18, (98, 105)]) == {}  # under twenty days of history


def test_a_falling_market_with_failed_breakdowns_buys_each_time() -> None:
    # the rule is not too strict: five stepped-down copies of the book's setup, five buys
    block = [(99, 100), *[FLAT] * 19, (98, 105), (100, 106), (96, 97)]
    days = [(lo - 10 * k, c - 10 * k) for k in range(5) for lo, c in block]
    assert list(_trades(days).values()).count(Action.BUY) == 5


def test_declares_no_holding_period_and_says_why() -> None:
    # his ruling 21 Nov: each rule's hold limit is its own sell logic's; the book's stop alone
    assert "Holding period: none" in eponymous_raschke_swing.__doc__
    assert RaschkeTurtleSoup.declared.hold is None
