"""The ladder's shuffle rung: an edge in the order of days beats every shuffle of them."""

from __future__ import annotations

from decimal import Decimal

import pytest
from test_lab_rung import POUND, TEN_K, _walk

from desk.lines import LINES
from lab import cell, reproduce, shuffle
from lab.cell import Cell
from lab.reproduce import Figure, Fill, Found, Hand, Measure, Reproduction, Stated

VUSA = next(line for line in LINES if line.symbol == "VUSA")


def _share(*pushes: float, made: tuple[Reproduction, ...] = ()) -> Decimal:
    bars = _walk(1, *pushes, days=3000)
    c = Cell("breakout_20_10", VUSA, bars[0].day, bars[-1].day)
    return shuffle.share(c, bars, TEN_K, POUND, made)


def test_a_planted_edge_is_in_the_order_of_days_and_the_same_trial_is_shuffled_the_same() -> None:
    assert shuffle.SHUFFLES == 100
    assert _share(0.012) == _share(0.012) == Decimal(1) / 101
    assert _share(0.0) > shuffle.SHARE, "a walk with no edge is among the best of its own shuffles"


def test_a_rule_with_an_authors_figure_is_shuffled_with_its_reproduction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    #: the blind re-review (R-RUNNER-188): each shuffle was judged with no reproduction, so a
    #: rule with an author's figure on file was refused at the last rung and never judged
    bars = _walk(1, 0.012, days=3000)
    c = Cell("breakout_20_10", VUSA, bars[0].day, bars[-1].day)
    stated = Stated(Measure.TRADES, Decimal(1), Decimal(0))
    figure = Figure(
        c.strategy, "an author", VUSA, c.start, c.end, Fill.CLOSE, (stated,), Hand.AUTHOR
    )
    made = Reproduction(
        figure, cell.key(c, bars).rung("lab.reproduce"), (Found(stated, Decimal(1)),)
    )
    monkeypatch.setattr(reproduce, "FIGURES", (figure,))
    assert _share(0.012, made=(made,)) == Decimal(1) / 101
