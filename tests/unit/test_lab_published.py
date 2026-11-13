"""The published rules: every rule the ladder judges names its author's source and gives the
publication's known answers, and code that does not give them is refused before any verdict."""

from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import replace
from decimal import Decimal
from typing import Any, cast

import pytest
from test_lab_rung import POUND, SHAPE, TEN_K, _bars

from desk import strategy
from desk.store import Bar
from lab import cell, published, rung
from lab.cell import Cell
from lab.published import Published

BREAKOUT = "breakout_20_10"


class _Eager:
    """Not the Turtles' rule: in on any close over 10.2, a day before theirs on their series."""

    declared = strategy.STRATEGIES[BREAKOUT].declared

    def step(self, bar: Bar, _holding: bool) -> bool:
        return bar.close > Decimal("10.2")


def test_each_rule_the_ladder_judges_gives_its_published_answers_and_names_its_source() -> None:
    assert set(published.PUBLISHED) == set(strategy.STRATEGIES)
    for name, rule in published.PUBLISHED.items():
        assert published.proven(name) is rule and rule.source.strip()
        assert sum(len(case.trades) for case in rule.cases) >= 1, name
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
    for refused in (
        lambda: published.proven(BREAKOUT),
        lambda: rung.judge(record, bars, TEN_K, POUND),
    ):
        with pytest.raises(ValueError, match=r"not the published rule.*\(20, 23\).*\(21, 23\)"):
            refused()
    monkeypatch.undo()
    assert published.proven(BREAKOUT), "a refusal is not remembered"
    #: a rule with no publication on file cannot be judged at all
    monkeypatch.delitem(cast(MutableMapping[str, Published], published.PUBLISHED), BREAKOUT)
    published.proven.cache_clear()
    with pytest.raises(ValueError, match="no published rule on file"):
        rung.judge(record, bars, TEN_K, POUND)
