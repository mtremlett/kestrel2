"""The ladder's shuffle rung: an edge in the order of days beats every shuffle of them."""

from __future__ import annotations

from decimal import Decimal

from test_lab_rung import POUND, TEN_K, _walk

from lab import shuffle
from lab.cell import Cell


def _share(*pushes: float) -> Decimal:
    bars = _walk(1, *pushes, days=3000)
    return shuffle.share(
        Cell("breakout_20_10", "VUSA", bars[0].day, bars[-1].day), bars, TEN_K, POUND
    )


def test_a_planted_edge_is_in_the_order_of_days_and_the_same_trial_is_shuffled_the_same() -> None:
    assert shuffle.SHUFFLES == 100
    assert _share(0.012) == _share(0.012) == Decimal(1) / 101
    assert _share(0.0) > shuffle.SHARE, "a walk with no edge is among the best of its own shuffles"
