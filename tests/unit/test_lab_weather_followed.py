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
