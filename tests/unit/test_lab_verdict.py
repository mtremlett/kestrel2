"""The verdict of one cell (`lab/verdict.py`): the one rule reads the folds and the market, a
step of units is refused before any rung, and a line too young is its own label."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from decimal import Decimal
from typing import Any

import pytest
from test_lab_ladder import EDGE, ISF, NOISE, VUSA

from desk.store import Bar
from lab import ladder, market, verdict
from lab.cell import Cell
from lab.rung import Answer, Rates

CELL = Cell("breakout_20_10", VUSA, EDGE[0].day, ladder.END)


def _judge(bars: Sequence[Bar] = EDGE, pounds: Rates | None = None) -> dict[str, Any]:
    return verdict.judge(CELL, bars, ISF, NOISE, pounds or {}, 6, ())


@pytest.mark.parametrize("rung_failing", ["folds", "market"])
def test_a_cell_failing_only_one_rung_is_not_a_pass(
    monkeypatch: pytest.MonkeyPatch, rung_failing: str
) -> None:
    real = market.judge
    if rung_failing == "folds":
        monkeypatch.setattr(verdict, "_folded", lambda *_: (Answer.FAIL, "a sour year"))
    else:
        monkeypatch.setattr(
            market, "judge", lambda *a: replace(real(*a), answer=Answer.FAIL, line=None)
        )
    rungs = _judge()["rungs"]
    others = {name: answer for name, (answer, _) in rungs.items() if name != rung_failing}
    assert rungs[rung_failing][0] == "FAIL" and others["first"] == "PASS"
    assert _judge()["every"] is False and _judge()["answer"] == "FAIL"


def test_a_step_of_units_is_refused_unless_the_master_names_it() -> None:
    day = EDGE[300].day
    up = Decimal("1.27")
    stepped = [
        bar if bar.day < day else replace(bar, close=bar.close * up, high=bar.high * 2)
        for bar in EDGE
    ]
    pounds = {bar.day: Decimal("0.79") for bar in EDGE}
    with pytest.raises(verdict.UnitStep, match=str(day)):
        _judge(stepped, pounds)
    named = replace(VUSA, real_moves=frozenset({(day, stepped[300].close)}))
    verdict._unstepped(named, stepped, pounds)
    verdict._unstepped(VUSA, EDGE, pounds)


def test_a_line_too_young_to_have_traded_is_too_young_and_no_fault() -> None:
    with pytest.raises(verdict.TooYoung, match="waits on 452"):
        _judge(EDGE[:100])
    assert not issubclass(verdict.TooYoung, ArithmeticError)


def test_resampled_drawdowns_are_parts_of_the_capital_and_drawn_the_same_again() -> None:
    #: +500 and -500 drawn twice: a fall of 0, 500, 500 or 1,000 pounds, of 10,000 capital
    both = [Decimal(500), Decimal(-500)]
    assert verdict.drawdowns(both, "a trial") == {"median": 0.05, "p95": 0.1}
    assert verdict.drawdowns(both, "a trial") == verdict.drawdowns(both, "a trial")
    assert verdict.drawdowns([Decimal(-1000)], "x") == {"median": 0.1, "p95": 0.1}
