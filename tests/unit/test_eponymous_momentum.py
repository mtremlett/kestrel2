"""Antonacci's dual momentum (absolute leg) on a series whose calls the rule fixes by hand."""

from datetime import date
from decimal import Decimal

from desk import eponymous_momentum
from desk.eponymous_momentum import DualMomentum
from desk.store import Bar
from desk.strategy import Action, _run

#: the close at each month-end; each month also has a first-of-month bar at an absurd price
#: that only a rule peeking at the wrong close would heed
ENDS = [*range(100, 116), *[90, 80] + [80] * 10, 95, 95, 95]


def _bar(day: date, close: int) -> Bar:
    price = Decimal(close)
    return Bar(day, price, price, price, price, 1)


def test_calls_fall_on_the_first_bar_after_the_month_end_the_rule_fixes() -> None:
    bars = []
    for n, close in enumerate(ENDS):
        year, month = 2020 + n // 12, n % 12 + 1
        bars += [_bar(date(year, month, 1), 1000), _bar(date(year, month, 20), close)]
    called = {
        d.day: d.action
        for d in _run("dual_momentum", DualMomentum(), "X", bars)
        if d.action is not Action.HOLD
    }
    # month k decides on ENDS[k-1] against ENDS[k-13]: k=13 buys (112>100), k=17 sells
    # (90<104), k=29 buys again (95>90); every month between holds its position.
    assert called == {
        date(2021, 2, 1): Action.BUY,
        date(2021, 6, 1): Action.SELL,
        date(2022, 6, 1): Action.BUY,
    }


def test_declares_no_holding_period_and_says_why() -> None:
    # his ruling 21 Nov: each rule's hold limit is its own sell logic's; the month-end call alone
    assert "Holding period: none" in eponymous_momentum.__doc__
    assert DualMomentum.declared.hold is None
