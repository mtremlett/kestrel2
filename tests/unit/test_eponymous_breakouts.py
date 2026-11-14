"""Darvas's box on a series whose entry and exit days the published rule fixes."""

from datetime import date, timedelta
from decimal import Decimal

from desk.eponymous_breakouts import RULES, decide
from desk.store import Bar
from desk.strategy import Action

#: high, low, close per session. Box 1 (top 10, bottom 9) stands on session 3; session 4
#: closes over it (BUY) and its box (10.2, 9.5) stands on 7, raising the stop to 9.5;
#: session 9 breaks out again, box (10.9, 10.0) stands on 12 and lifts the stop to 10.0;
#: session 13 closes under it (SELL). The next box, (10.3, 9.6), stands only on 17, since
#: the low of 14 undercuts for 3 more sessions; 18 closes over it (BUY).
SERIES = [
    ("10", "9", "9.5"), ("9.8", "9.2", "9.5"), ("9.7", "9.3", "9.5"), ("9.6", "9.4", "9.5"),
    ("10.2", "9.5", "10.1"), ("10.1", "9.8", "10"), ("10", "9.7", "9.9"), ("10", "9.9", "9.95"),
    ("10.1", "9.8", "10"), ("10.9", "10", "10.8"), ("10.6", "10.3", "10.4"),
    ("10.5", "10.2", "10.3"), ("10.4", "10.1", "10.2"), ("10.3", "9.8", "9.9"),
    ("10", "9.6", "9.7"), ("9.9", "9.7", "9.8"), ("9.8", "9.7", "9.75"), ("9.7", "9.65", "9.7"),
    ("10.6", "9.9", "10.5"),
]  # fmt: skip


def _bars() -> list[Bar]:
    start = date(2026, 1, 5)
    return [
        Bar(start + timedelta(n), Decimal(c), Decimal(h), Decimal(lo), Decimal(c), 1)
        for n, (h, lo, c) in enumerate(SERIES)
    ]


def test_darvas_buys_and_sells_on_the_days_the_published_rule_fixes() -> None:
    days = decide({"X": _bars()})
    assert {d.strategy for d in days} == set(RULES)
    acts = {n: d.action for n, d in enumerate(days) if d.action is not Action.HOLD}
    assert acts == {4: Action.BUY, 13: Action.SELL, 18: Action.BUY}


def test_darvas_never_reads_a_later_bar() -> None:
    whole = decide({"X": _bars()})
    assert decide({"X": _bars()[:14]}) == whole[:14]


def test_darvas_waits_for_the_third_session_before_the_box_stands() -> None:
    early = _bars()[:3] + [
        Bar(date(2026, 2, 1), Decimal(10), Decimal("10.5"), Decimal("9.4"), Decimal("10.4"), 1)
    ]
    assert {d.action for d in decide({"X": early})} == {Action.HOLD}
