"""The published rules: every rule the ladder judges names its author's source and gives the
publication's known answers, and code that does not give them is refused before any verdict."""

from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import replace
from decimal import Decimal
from typing import Any, cast

import numpy as np
import pytest
from test_lab_rung import POUND, SHAPE, TEN_K, _bars

from desk import strategy
from desk.store import Bar
from lab import cell, grid, published, rung
from lab.cell import Cell
from lab.published import Published

BREAKOUT = "breakout_20_10"


def _answers(name: str, prices: grid.Prices) -> bool:
    try:
        return bool(grid.held(name, prices).any())
    except grid.TooClose:
        return False


class _Eager:
    """Not the Turtles' rule: in on any close over 10.2, a day before theirs on their series."""

    declared = strategy.STRATEGIES[BREAKOUT].declared

    def step(self, bar: Bar, _holding: bool) -> bool:
        return bar.close > Decimal("10.2")


def test_each_rule_the_ladder_judges_gives_its_published_answers_and_names_its_source() -> None:
    assert set(published.PUBLISHED) == set(strategy.STRATEGIES)
    for name, rule in published.PUBLISHED.items():
        assert published.proven(name) is rule and rule.source.strip()
        #: the fast grid answers a series with a trade itself, so it too is held to the rule
        traded = [grid.prices(case.bars()) for case in rule.cases if case.trades]
        assert any(_answers(name, prices) for prices in traded), name
    (case,) = published.PUBLISHED[BREAKOUT].cases
    assert case.trades == ((21, 23),) and len(case.bars()) == 25
    assert (case.bars()[21].high, case.bars()[21].low) == (Decimal("11.5"), Decimal("10.5"))
    with pytest.raises(ValueError, match="buys nothing"):
        Published("a rule whose known answers hold no trade", (replace(case, trades=()),))
    with pytest.raises(ValueError, match="no source"):
        Published(" ", (case,))


def test_code_that_is_not_the_published_rule_is_refused_and_gives_no_verdict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bars = _bars(SHAPE)
    record = cell.run(Cell(BREAKOUT, "VUSA", bars[0].day, bars[24].day), bars)
    assert rung.judge(record, bars, TEN_K, POUND).trades, "the published rule is judged"
    rules = cast(MutableMapping[str, Any], strategy.STRATEGIES)
    monkeypatch.setitem(rules, BREAKOUT, _Eager)
    published.proven.cache_clear()
    wrong = r"the desk's engine is not the published rule.*\(20, 23\).*\(21, 23\)"
    for refused in (
        lambda: published.proven(BREAKOUT),
        lambda: rung.judge(record, bars, TEN_K, POUND),
    ):
        with pytest.raises(ValueError, match=wrong):
            refused()
    monkeypatch.undo()
    #: and the ladder's own cell, where the fast grid answers: out a day late is refused too
    held = grid.held
    monkeypatch.setattr(grid, "held", lambda name, p: held(name, p) | np.roll(held(name, p), 1))
    with pytest.raises(ValueError, match=r"the cell is not the published rule.*\(21, 24\)"):
        published.proven(BREAKOUT)
    monkeypatch.undo()
    #: a rule with no publication on file cannot be judged at all
    monkeypatch.delitem(cast(MutableMapping[str, Published], published.PUBLISHED), BREAKOUT)
    published.proven.cache_clear()
    with pytest.raises(ValueError, match="no published rule on file"):
        rung.judge(record, bars, TEN_K, POUND)
