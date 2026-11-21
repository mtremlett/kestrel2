"""The ladder's yearly folds: a rule's trades pooled over its lines, the worst year judged on."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from test_lab_rung import TEN_K, _walk

from desk.lines import LINES
from lab import cell, folds, reproduce
from lab.cell import Cell
from lab.folds import Pooled
from lab.reproduce import Figure, Fill, Found, Hand, Measure, Reproduction, Stated
from lab.rung import Answer

ISF = next(line for line in LINES if line.symbol == "ISF")
VUSA = next(line for line in LINES if line.symbol == "VUSA")

DOLLARS = {date(2010, 1, 1) + timedelta(n): Decimal("0.8") for n in range(4000)}
_STATED = Stated(Measure.TRADES, Decimal(1), Decimal(0))
EDGE, YEAR, RULE = 0.012, 365, "breakout_20_10"
LSE = tuple(
    line for line in LINES if line.retail
)  #: the lines a retail customer may buy (R-PAPER-14)


def _pool(seed: int, *pushes: float, count: int = 5) -> Pooled:
    """Every line of one rule, each a walk with the planted push in each of its years."""
    cells = [
        (Cell(RULE, line, bars[0].day, bars[-1].day), bars)
        for line, bars in ((s, _walk(seed + n, *pushes, days=YEAR)) for n, s in enumerate(LSE))
    ]
    return folds.pool(cells, TEN_K, DOLLARS, count)


def test_an_edge_in_every_year_passes_a_dead_walk_does_not_and_a_sour_year_is_named() -> None:
    for seed in (1,):
        alive, none = _pool(seed, *[EDGE] * 8), _pool(seed, *[0] * 8)
        assert [y.year for y in alive.years] == [2012, 2013, 2014, 2015, 2016]
        assert alive.answer is Answer.PASS and all(y.lines == len(LSE) for y in alive.years), seed
        assert all(y.trades >= 30 and y.before is not None for y in alive.years), seed
        assert none.answer is not Answer.PASS, seed
        sour = _pool(seed, *[EDGE] * 5, -EDGE, *[EDGE] * 2)  #: one year where breakouts fell back
        assert sour.answer in (Answer.FAIL, Answer.DOUBT) and sour.worst.year == 2015, seed
        assert "2015" in sour.reason and f"over {len(LSE)} lines" in sour.reason, seed


def test_a_rule_with_an_authors_figure_is_still_folded(monkeypatch: pytest.MonkeyPatch) -> None:
    bars = _walk(1, EDGE, days=YEAR * 7)
    c = Cell(RULE, VUSA, bars[0].day, bars[-1].day)
    figure = Figure(
        RULE, "a planted author", c.line, c.start, c.end, Fill.CLOSE, (_STATED,), Hand.AUTHOR
    )
    made = Reproduction(
        figure, cell.key(c, bars).rung("lab.reproduce"), (Found(_STATED, Decimal(1)),)
    )
    monkeypatch.setattr(reproduce, "FIGURES", (figure,))
    with pytest.raises(ValueError, match="no verdict before its published result"):
        folds.pool([(c, bars)], TEN_K, DOLLARS, 5)
    pooled = folds.pool([(c, bars)], TEN_K, DOLLARS, 5, (made,))
    assert [y.year for y in pooled.years] == [2011, 2012, 2013, 2014, 2015]
    assert folds.judge(c, bars, TEN_K, DOLLARS, 2, (made,)).folds[0].outside.reproduced == (made,)


def test_the_years_are_whole_and_the_answers_are_fair() -> None:
    bars = _walk(1, EDGE, days=YEAR * 3)
    cells = [(Cell(RULE, VUSA, bars[0].day, bars[-1].day), bars)]
    with pytest.raises(ValueError, match="no 5 whole years"):
        folds.pool(cells, TEN_K, DOLLARS)
    with pytest.raises(ValueError, match="one rule's"):
        folds.pool(
            [*cells, (Cell("trend_50_200", ISF, bars[0].day, bars[-1].day), bars)], TEN_K, DOLLARS
        )
    few = folds.pool(cells, TEN_K, DOLLARS, 1).years[0]  #: a year with under 30 trades is THIN
    assert few.trades < 30 and few.answer is Answer.THIN
    assert folds._answer(0, None, Decimal(0)) is Answer.FAULT
    assert folds._answer(40, Decimal(-3), Decimal(-1)) is Answer.FAIL
    assert folds._answer(40, Decimal(-1), Decimal(-1)) is Answer.DOUBT
    assert folds._answer(40, Decimal("0.5"), Decimal(1)) is Answer.PASS


def test_two_lines_with_different_ends_fold_and_give_a_verdict() -> None:
    bars = _walk(1, *[EDGE] * 8, days=YEAR)
    short = [b for b in bars if b.day <= date(2014, 12, 31)]
    cells = [
        (Cell(RULE, VUSA, bars[0].day, bars[-1].day), bars),
        (Cell(RULE, ISF, short[0].day, short[-1].day), short),
    ]
    pooled = folds.pool(cells, TEN_K, DOLLARS, 4)
    assert [y.lines for y in pooled.years] == [2, 2, 1, 1]
    assert pooled.answer is not Answer.FAULT
