"""The verdict of one cell (`lab/verdict.py`): the one rule reads the folds and the market, a
step of units is refused before any rung, a line too young is its own label, and nothing goes
forward while a rung is unrun."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from test_lab_ladder import EDGE, ISF, NOISE, VUSA

from desk.store import Bar
from lab import ladder, market, verdict
from lab.cell import Cell
from lab.folds import Pooled
from lab.rung import Answer, Rates

CELL = Cell("breakout_20_10", VUSA, EDGE[0].day, ladder.END)


def _judge(
    bars: Sequence[Bar] = EDGE, pounds: Rates | None = None, sour: bool = False
) -> dict[str, Any]:
    """The cell's verdict with the folds of its rule, the one line pooled; `sour` has the
    worst year fail."""
    pooled = verdict.pool([(CELL, EDGE)], {})
    if sour:
        pooled = replace(pooled, years=(replace(pooled.years[0], answer=Answer.FAIL),))
    return verdict.judge(CELL, bars, ISF, NOISE, pounds or {}, 6, (), lambda: pooled)


@pytest.mark.parametrize("rung_failing", ["folds", "market"])
def test_a_cell_failing_only_one_rung_is_not_a_pass(
    monkeypatch: pytest.MonkeyPatch, rung_failing: str
) -> None:
    real = market.judge
    if rung_failing == "market":
        monkeypatch.setattr(
            market, "judge", lambda *a: replace(real(*a), answer=Answer.FAIL, line=None)
        )
    sour = rung_failing == "folds"
    rungs = _judge(sour=sour)["rungs"]
    others = {name: answer for name, (answer, _) in rungs.items() if name != rung_failing}
    assert rungs[rung_failing][0] == "FAIL" and others["first"] == "PASS"
    assert _judge(sour=sour)["every"] is False and _judge(sour=sour)["answer"] == "FAIL"


def test_a_step_of_units_is_refused_unless_the_master_names_it() -> None:
    day = EDGE[300].day
    up = Decimal("1.27")
    stepped = [
        bar
        if bar.day < day
        else Bar(bar.day, bar.open * up, bar.high * up, bar.low * up, bar.close * up, bar.volume)
        for bar in EDGE
    ]
    pounds = {bar.day: Decimal("0.79") for bar in EDGE}
    with pytest.raises(verdict.UnitStep, match=str(day)):
        _judge(stepped, pounds)
    named = replace(VUSA, real_moves=frozenset({(day, stepped[300].close)}))
    verdict._unstepped(named, stepped, pounds)
    verdict._unstepped(VUSA, EDGE, pounds)
    #: the same rise made inside the session, from an open at the close before: a real move, not
    #: units (the blind review, R-RUNNER-40: 251 London lines refused, most for a crash day)
    rose = replace(EDGE[300], open=EDGE[299].close, low=EDGE[299].close, close=stepped[300].close)
    verdict._unstepped(VUSA, [*EDGE[:300], replace(rose, high=rose.close)], pounds)


def test_nothing_goes_forward_while_a_rung_is_unrun_and_the_table_says_cells_beside_trials(
    tmp_path: Path,
) -> None:
    passed = {"first": ["PASS", "passed"]}
    row = {"cell": ["breakout_20_10", "VUSA", "LSE"], "trials": 3, "answer": "PASS", "every": True}
    row |= {"rungs": passed, "unrun": {"regime": "the weather is not built"}}
    assert not verdict.goes(row) and verdict.goes(row | {"unrun": {}})
    assert not verdict.goes({k: v for k, v in row.items() if k != "unrun"}), "unsaid is not none"
    table = verdict.write_table(
        tmp_path, "T", "Does it earn?", [row], ["breakout_20_10"], 3, (7, 11)
    )
    md = table.read_text(encoding="utf-8")
    assert (
        "\nrungs built: 7 of 11\n" in md
        and ": 0 of 1 lines go forward" in md
        and md.rstrip().endswith("| no |")
    )
    assert "Does it earn? Cells: 1. Each is judged against 3 trials" in md
    data = json.loads(table.with_suffix(".json").read_text(encoding="utf-8"))
    assert (data["cells"], data["trials"], data["rules"][0]["passed"]) == (1, 3, False)
    assert (data["rungs_built"], data["rungs"]) == (7, 11)


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


def test_folds_that_cannot_be_run_are_a_fault_with_their_reason_and_the_rest_stand() -> None:
    def short() -> Pooled:
        raise ValueError("no 5 whole years of history to fold")

    done = verdict.judge(CELL, EDGE, ISF, NOISE, {}, 6, (), short)
    assert done["rungs"]["folds"] == [
        "FAULT",
        "the folds could not be run: no 5 whole years of history to fold",
    ]
    assert done["rungs"]["first"][0] == "PASS" and done["answer"] == "FAULT"
