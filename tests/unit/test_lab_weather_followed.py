"""What followed each weather label, per fold: hand-worked, and blind to the label's own day."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from desk.store import Bar
from lab import weather

START = date(2024, 1, 1)


def _bars(*closes: int) -> list[Bar]:
    return [
        Bar(START + timedelta(days=n), Decimal(c), Decimal(c), Decimal(c), Decimal(c), 1)
        for n, c in enumerate(closes)
    ]


def test_the_return_after_each_label_is_the_hand_worked_one_per_fold() -> None:
    bars = _bars(100, 110, 99, 99, 198)
    days = [bar.day for bar in bars]
    labels = dict(zip(days, ["warming", "up", "down", "up", "down"], strict=True))
    #: after day 1 (up): 99/110-1 = -0.1; day 2 (down): 0; day 3 (up): +1; day 4 has no next
    whole = weather.followed(labels, bars)[0]
    assert whole == {"up": Decimal("0.45"), "down": Decimal(0)}
    first, second = weather.followed(labels, bars, folds=2)
    assert first == {"up": Decimal("-0.1")}
    assert second == {"down": Decimal(0), "up": Decimal(1)}


def test_a_layers_edge_is_good_days_less_the_rest_per_fold_and_refuses_a_one_sided_fold() -> None:
    bars = _bars(100, 110, 99, 99, 198)
    days = [bar.day for bar in bars]
    labels = dict(zip(days, ["warming", "up", "down", "up", "down"], strict=True))
    assert weather.edges(labels, bars, "up") == [Decimal("0.45")]
    with pytest.raises(ValueError, match="fold 0 of 2"):
        weather.edges(labels, bars, "up", folds=2)


def test_a_layer_wins_only_if_its_worst_fold_beats_trends_and_the_trials_are_kept() -> None:
    bars = _bars(*([100] * 199), 100, 110, 99, 99, 198)
    days = [bar.day for bar in bars]
    tail = ["calm", "stormy", "calm", "calm", "stormy"]
    labels = {d: "warming" for d in days[:-5]} | dict(zip(days[-5:], tail, strict=True))
    #: calm days are followed by +0.1, 0, +1 (mean 11/30), the stormy day by -0.1: edge 7/15;
    #: trend's up day (-0.1) trails its down days (mean 11/30): edge -7/15
    contest = weather.against_trend(labels, "calm", bars, folds=1, trials=3)
    assert (contest.layer, contest.trend, contest.trials) == (
        Decimal(7) / 15,
        -(Decimal(7) / 15),
        3,
    )
    assert contest.wins
    assert not weather.Contest(contest.trend, contest.layer, 3).wins
