"""The published rules: every rule the ladder judges names its author's source and gives the
publication's known answers, and code that does not give them is refused before any verdict."""

from __future__ import annotations

import re
from collections.abc import MutableMapping
from dataclasses import replace
from decimal import Decimal
from statistics import stdev
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


def _plain(self: Any, value: Decimal) -> Decimal | None:
    self.seen, size = [*getattr(self, "seen", []), value][-self._size :], self._size
    self.value = sum(self.seen, Decimal(0)) / size if len(self.seen) == size else None
    return cast(Decimal | None, self.value)


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


def test_no_rule_is_proven_on_an_indicator_that_does_not_give_its_published_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tables = published.indicators()
    assert tables is published.INDICATORS and len(tables) == 5
    for table in tables.values():  #: every printed column is held, on prices given exactly
        assert table.source.strip() and table.given and all(table.printed.values())
    with pytest.raises(ValueError, match="prints nothing"):
        replace(tables["moving average"], printed={})
    #: the commonest mistake: the deviation of a sample (over 19), where Bollinger's is over 20
    sample = Decimal(stdev(published.INDICATORS["Bollinger's bands"].given["Price"][:20]))
    monkeypatch.setattr(strategy._Window, "deviation", lambda _: sample)
    wrong = r"Bollinger's bands, its Standard Deviation, is not.*StockCharts.*1\.3255 at row 0"
    for refused in (published.indicators, lambda: published.proven(BREAKOUT)):
        published.indicators.cache_clear()
        published.proven.cache_clear()
        with pytest.raises(ValueError, match=wrong):
            refused()
    monkeypatch.undo()
    #: and a plain 14-day average passed off as Wilder's: right on the first row, wrong after
    monkeypatch.setattr(strategy._Wilder, "add", _plain)
    with pytest.raises(ValueError, match=r"under the RSI, its Avg Gain,.*0\.2384 at row 1"):
        published.indicators()
    monkeypatch.undo()
    #: and a true range blind to the gap from yesterday's close: the day's own range alone
    step = strategy._Supertrend.step

    def blind(rule: Any, bar: Bar, held: bool) -> bool:
        rule._last = None
        return step(rule, bar, held)

    monkeypatch.setattr(strategy._Supertrend, "step", blind)
    with pytest.raises(ValueError, match=r"true range, its TR, is not.*0\.4200 at row 8"):
        published.indicators()
    monkeypatch.undo()
    #: every row of every column is held, to the last place printed: any one of them out by
    #: one in that place, or a column a row short, is refused, and named
    held = cast(MutableMapping[str, Any], published.INDICATORS)
    for name, table in dict(tables).items():
        for column, printed in table.printed.items():
            one = Decimal(1).scaleb(-len(str(printed[0]).split(".")[1]))
            near = [
                (*printed[:n], printed[n] + one, *printed[n + 1 :]) for n in range(len(printed))
            ]
            for other in (printed[:-1], *near):
                monkeypatch.setitem(held, name, replace(table, printed={column: other}))
                with pytest.raises(
                    ValueError, match=re.escape(f"the desk's {name}, its {column}, is not")
                ):
                    published.indicators()
        monkeypatch.setitem(held, name, table)
