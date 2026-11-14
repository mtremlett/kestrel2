"""The ladder's folds rung: each fold judged beside the history before it, verdict on the worst."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from decimal import Decimal

import pytest
from test_lab_luck import DAY
from test_lab_rung import FREE, POUND, SHAPE, TEN_K, _bars, _walk

from desk.lines import LINES, Line
from desk.store import Bar
from lab import folds, rung
from lab.cell import Cell, Key, Trade
from lab.rung import Answer, Priced, Verdict

EDGE = 0.012
VUSA = next(line for line in LINES if line.symbol == "VUSA")


def _window(bars: Sequence[Bar]) -> Cell:
    return Cell("breakout_20_10", "VUSA", bars[0].day, bars[-1].day)


def _verdict(*gains: str) -> Verdict:
    days = (DAY, DAY)
    made = tuple(
        Priced(
            Trade(*days),
            1,
            Decimal(1),
            1 + Decimal(g),
            FREE,
            days,
            sum(map(Decimal, gains), Decimal(0)) / len(gains),
        )
        for g in gains
    )
    return rung.verdict(Key(Cell("breakout_20_10", "VUSA", DAY, DAY), "code", "data"), made)


def test_a_window_is_cut_into_equal_parts_and_a_trade_across_a_boundary_is_in_neither() -> None:
    bars = _bars(SHAPE)  #: 25 bars: bought on bar 20's close, sold on bar 23's, filled on bar 24
    days = [bar.day for bar in bars]  #: cut in five parts of five, each beside all before it
    want = [(days[0], days[5 * n - 1], days[5 * n], days[5 * n + 4]) for n in range(1, 5)]
    assert [(i.start, i.end, o.start, o.end) for i, o in folds.cut(_window(bars), bars, 4)] == want
    inner = Cell("breakout_20_10", "VUSA", days[2], days[12])  #: its own bars, parts a bar apart
    ends = [(i.end, o.start, o.end) for i, o in folds.cut(inner, bars, 2)]
    assert ends == [(days[4], days[5], days[8]), (days[8], days[9], days[12])]
    for count, bad in [(0, bars), (25, bars), (1, bars[:1])]:
        with pytest.raises(ValueError, match="cannot be cut"):
            folds.cut(_window(bad), bad, count)
    assert len(folds.cut(_window(bars), bars, 24)) == 24, "a bar a part is the limit"


def _book(seed: int, *pushes: float) -> dict[Line, Sequence[Bar]]:
    """Twelve lines in pounds, each its own walk: the folds' pool, a year of it 30 trades."""
    lines = [line for line in LINES if line.currency == "GBP"]
    return {line: _walk(seed * 10 + n, *pushes) for n, line in enumerate(lines)}


def test_the_folds_pool_a_rules_lines_by_the_year_and_the_worst_year_speaks() -> None:
    assert folds.FOLDS >= 5 and list(folds.years(date(2025, 12, 31))) == list(range(2021, 2026))
    assert list(folds.years(date(2026, 11, 13))) == list(range(2021, 2026)), "whole years only"
    end = date(2025, 12, 31)
    alive, why = folds.judge("breakout_20_10", _book(0, EDGE, EDGE, EDGE), TEN_K, POUND, end)
    assert alive is Answer.PASS and "trades pooled from 12 lines" in why, why
    dead, why = folds.judge("breakout_20_10", _book(0, 0, 0, 0), TEN_K, POUND, end)
    assert dead is not Answer.PASS, why
    #: the edge turned about from the autumn of 2023: the years after it earned nothing
    sour, why = folds.judge("breakout_20_10", _book(0, EDGE, -EDGE, -EDGE), TEN_K, POUND, end)
    assert sour in (Answer.FAIL, Answer.DOUBT) and ("2024" in why or "2025" in why), why
    short, why = folds.judge("breakout_20_10", {VUSA: _walk(0, EDGE, EDGE)}, TEN_K, POUND, end)
    assert short is Answer.THIN and "30 asked" in why, why
