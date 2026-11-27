"""Known answer: the published 10-month rule fixes the entry and exit days of a made-up series."""

from datetime import date
from decimal import Decimal

from desk import eponymous_faber_tactical
from desk.eponymous_faber_tactical import decide
from desk.store import Bar
from desk.strategy import Action


def _trades(month_ends: list[int]) -> dict[int, Action]:
    """Two bars a month (the 1st and the 20th) at that month's close; the trades by bar."""
    bars = [
        Bar(date(2020 + (m // 12), m % 12 + 1, d), *(Decimal(c),) * 4, 1)
        for m, c in enumerate(month_ends)
        for d in (1, 20)
    ]
    got = decide({"X": bars})
    return {n: d.action for n, d in enumerate(got) if d.action is not Action.HOLD}


def test_buys_over_the_ten_month_average_and_sells_under_it() -> None:
    # ten flat months: the close equals its average, so out. Month 11 closes at 110 over its
    # average 101: BUY on month 12's first bar (bar 22). Month 12 closes at 90 under its
    # average 100: SELL on month 13's first bar (bar 24). Every other day: nothing.
    assert _trades([*[100] * 10, 110, 90, 90]) == {22: Action.BUY, 24: Action.SELL}


def test_waits_for_ten_months_of_month_ends() -> None:
    assert _trades([*range(100, 109), 120]) == {}  # nine month-ends only
    assert _trades([*range(100, 110), 120]) == {20: Action.BUY}  # the tenth arrives: in


def test_declares_no_holding_period_and_says_why() -> None:
    # his ruling 21 Nov: each rule's hold limit is its own sell logic's; stated, no time stop
    assert "Holding period: none" in eponymous_faber_tactical.__doc__
    assert all(r.declared.hold is None for r in eponymous_faber_tactical.EPONYMOUS.values())
