"""The one-bar-late rung (E13): every judged trade made a bar late, priced by the first rung's own
pricing, and judged by its own rule. An edge that lasts (the kit's crowd) passes; one paid only on
the next open (the kit's churner on its paid line) is lost a bar late and FAILS; a cell the first
rung did not pass keeps its answer and is not re-priced."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta
from decimal import Decimal

import pytest
import test_lab_ladder_known_answer as crowds
import test_lab_rung_known_answer as kit

from desk.command import CAPITAL
from desk.lines import Line
from desk.orders import Settings
from desk.store import Bar
from lab import cell, ladder, rung, rung_late
from lab.cell import Cell
from lab.rung import Answer

(AMD,) = (line for line in kit.US if line.symbol == "AMD")


@pytest.fixture(autouse=True)
def planted(monkeypatch: pytest.MonkeyPatch) -> None:
    """Both kits' planted rules in the book, each with its own known answer."""
    kit.plant(monkeypatch)
    crowds._plant(monkeypatch)


def _first(rule: str, line: Line, bars: Sequence[Bar]) -> rung.Verdict:
    record = cell.run(Cell(rule, line, ladder.START, ladder.END), bars)
    return rung.judge(record, bars, Settings(CAPITAL), _rates(bars))


def _rates(bars: Sequence[Bar]) -> rung.Rates:
    """Pounds per dollar on every day of the bars, as the kits price them."""
    return {bar.day: Decimal("0.8") for bar in bars}


def test_the_late_trades_are_the_judged_trades_each_made_a_bar_later() -> None:
    bars = crowds._crowds(1, crowds.RISE)
    first = _first("crowd", AMD, bars)
    made = rung_late.late(first, bars, _rates(bars))
    n = {bar.day: k for k, bar in enumerate(bars)}

    def bars_of(verdict: rung.Verdict) -> list[tuple[int, int]]:
        return [(n[p.trade.bought], n[p.trade.sold or p.trade.bought]) for p in verdict.trades]

    on_time, late = bars_of(first), bars_of(made)
    assert len(late) >= len(on_time) - 1 >= 30  #: only the last may fall past the shown bars
    assert late == [(b + 1, s + 1) for b, s in on_time[: len(late)]]
    assert all(
        p.held[0] - q.held[0] == timedelta(1)
        for p, q in zip(made.trades, first.trades[: len(late)], strict=True)
    )


def test_an_edge_that_lasts_passes_a_bar_late() -> None:
    bars = crowds._crowds(1, crowds.RISE)
    first = _first("crowd", AMD, bars)
    assert first.answer is Answer.PASS
    answer, why = rung_late.RUNG.judge(first, bars, _rates(bars))
    assert answer is Answer.PASS, why
    assert "a bar late" in why and "on time" in why and why.count("mean gain") == 2


def test_an_edge_paid_only_on_the_next_open_fails_a_bar_late() -> None:
    bars = kit._paid(4)
    first = _first("churner", AMD, bars)
    assert first.answer is Answer.PASS
    answer, why = rung_late.RUNG.judge(first, bars, _rates(bars))
    assert answer is Answer.FAIL, why


def test_a_cell_the_first_rung_did_not_pass_keeps_its_answer_and_is_not_priced_again(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bars = crowds._crowds(1, 0)
    unpriced = _first("crowd", AMD, crowds._crowds(1, crowds.RISE))

    def priced(*_: object) -> rung.Verdict:
        raise AssertionError("priced a bar late a cell the first rung did not pass")

    monkeypatch.setattr(rung_late, "late", priced)
    first = _first("crowd", AMD, bars)
    assert first.answer is Answer.FAIL
    assert rung_late.RUNG.judge(first, bars, _rates(bars)) == (Answer.FAIL, rung_late.NOT_PRICED)
    assert rung_late.RUNG.read(first) == (Answer.FAIL, rung_late.NOT_PRICED)
    with pytest.raises(ValueError, match="bars"):
        rung_late.RUNG.read(unpriced)
