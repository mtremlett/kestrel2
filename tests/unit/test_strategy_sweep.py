"""The settings the grid may try: each sweep holds its published value, and a named variant
decides as the rule does at that setting; the five stay five."""

from __future__ import annotations

import inspect
from datetime import date, timedelta
from decimal import Decimal, localcontext

import pytest

from desk import strategy
from desk.store import Bar
from desk.strategy import Action

HALF = Decimal("0.5")
CLOSES = [100 + (n * 7) % 13 + n // 20 - (n % 5) * 3 for n in range(320)]


def _bars(closes: list[int]) -> list[Bar]:
    day = date(2020, 1, 1)
    return [
        Bar(day + timedelta(n), Decimal(c), Decimal(c) + HALF, Decimal(c) - HALF, Decimal(c), 1000)
        for n, c in enumerate(closes)
    ]


def _actions(name: str, rule: strategy.Rule, closes: list[int]) -> list[Action]:
    with localcontext(strategy.ARITHMETIC):
        return [d.action for d in strategy._run(name, rule, "X", _bars(closes))]


def test_each_sweep_holds_the_published_value_and_the_five_stay_five() -> None:
    assert set(strategy.SWEEPS) == set(strategy.STRATEGIES) and len(strategy.STRATEGIES) == 5
    for name, grid in strategy.SWEEPS.items():
        params = inspect.signature(strategy.STRATEGIES[name]).parameters
        assert all(params[key].default in values for key, values in grid.items()), name
    assert not set(strategy.VARIANTS) & set(strategy.STRATEGIES)


@pytest.mark.parametrize("name", sorted(strategy.VARIANTS))
def test_a_variant_decides_as_its_rule_does_at_that_setting(name: str) -> None:
    base, setting = name.rstrip("]").split("[")
    key, value = setting.split("=")
    given = next(v for v in strategy.SWEEPS[base][key] if str(v) == value)
    maker = strategy.VARIANTS[name]
    assert maker.declared is strategy.STRATEGIES[base].declared
    direct = strategy.STRATEGIES[base](**{key: given})
    assert _actions(name, maker(), CLOSES) == _actions(base, direct, CLOSES)


def test_a_15_day_breakout_buys_where_the_published_20_has_no_history() -> None:
    closes = [10] * 15 + [11, 8]  #: day 16 clears 15 days' highs; day 17 is under the low
    seen = _actions("v", strategy.VARIANTS["breakout_20_10[entry=15]"](), closes)
    assert seen.index(Action.BUY) == 15 and seen[16] is Action.SELL
    assert Action.BUY not in _actions("p", strategy.STRATEGIES["breakout_20_10"](), closes)
