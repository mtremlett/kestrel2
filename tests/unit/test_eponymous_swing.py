"""The eponymous swing rules: each buys and sells on the days its published rule fixes, worked
out by hand on a synthetic series, and is blind to every later bar."""

from __future__ import annotations

import importlib
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from desk import eponymous_swing as swing
from desk.store import Bar
from desk.strategy import Action, Timeframe

START = date(2020, 1, 1)
DESK = Path(__file__).resolve().parents[2] / "desk"
MODULES = sorted(p.stem for p in DESK.glob("eponymous_*.py"))


def _bars(closes: list[int]) -> tuple[Bar, ...]:
    return tuple(
        Bar(START + timedelta(n), Decimal(c), Decimal(c), Decimal(c), Decimal(c), 1000)
        for n, c in enumerate(closes)
    )


def _trades(bars: tuple[Bar, ...]) -> list[tuple[int, Action]]:
    days = {bar.day: n for n, bar in enumerate(bars)}
    decided = swing.decide({"X": bars})
    assert len(decided) == len(bars)
    assert {d.strategy for d in decided} == {"weekly_reversal_jegadeesh"}
    return [(days[d.day], d.action) for d in decided if d.action is not Action.HOLD]


#: day 0-4 flat at 100; day 5 closes 99, under day 0's 100: the week lost, so BUY on day 5.
#: Held five sessions (days 6-10): SELL on day 10. Day 10 closes 98, under day 5's 99, but
#: a rule that has just sold waits a day: it buys on day 11, the week still a loser (97 < 99).
#: Days 12-16 are held; day 16 SELL. Closes then rise: no losing week, no more trades.
CLOSES = [
    100,
    100,
    100,
    100,
    100,
    99,
    99,
    99,
    99,
    99,
    98,
    97,
    100,
    101,
    102,
    103,
    104,
    105,
    106,
    107,
]


def test_it_buys_a_losing_week_holds_five_sessions_then_sells() -> None:
    assert _trades(_bars(CLOSES)) == [
        (5, Action.BUY),
        (10, Action.SELL),
        (11, Action.BUY),
        (16, Action.SELL),
    ]


def test_a_flat_week_is_not_a_loser_and_five_closes_are_not_yet_a_week() -> None:
    assert _trades(_bars([100, 90, 80, 70, 60])) == []
    assert _trades(_bars([100] * 12)) == []


def test_a_later_bar_changes_no_earlier_decision() -> None:
    bars = _bars(CLOSES)
    assert _trades(bars)[:3] == _trades(bars[:14])[:3]


def test_it_declares_five_sessions_on_daily_closes() -> None:
    declared = swing.EPONYMOUS["weekly_reversal_jegadeesh"].declared
    assert declared.bar is Timeframe.DAILY and declared.hold == 5


def test_every_eponymous_module_declares_unique_runnable_rules() -> None:
    names: list[str] = []
    for module in MODULES:
        mapping = getattr(importlib.import_module(f"desk.{module}"), "EPONYMOUS", None)
        assert mapping, f"desk.{module} declares no EPONYMOUS"
        for name, rule in mapping.items():
            assert hasattr(rule, "declared") and hasattr(rule, "step"), f"{module}: {name}"
            names.append(name)
    assert len(names) == len(set(names)), "a rule name is used twice"
