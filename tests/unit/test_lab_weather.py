"""The market weather: trend labels worked by hand, blind to the future, and readable by the
regime replay."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from desk.store import Bar
from lab import regime, weather

START = date(2024, 1, 1)


def _bars(*closes: int) -> list[Bar]:
    return [
        Bar(START + timedelta(days=n), Decimal(c), Decimal(c), Decimal(c), Decimal(c), 1)
        for n, c in enumerate(closes)
    ]


def test_labels_are_the_hand_worked_ones_and_future_blind(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(weather, "WINDOW", 3)
    closes = (10, 11, 12, 9, 9, 10, 20, 5)
    #: means of the last three closes: 11, 10.67, 10, 9.33, 13, 11.67; the close against it
    by_hand = ["warming", "warming", "up", "down", "down", "up", "up", "down"]
    labels = weather.trend(_bars(*closes))
    assert list(labels.values()) == by_hand
    for t in range(len(closes)):
        assert weather.trend(_bars(*closes[: t + 1])) == dict(list(labels.items())[: t + 1])
    assert list(labels)[0] == START and set(by_hand) == {"up", "down", "warming"}
    with pytest.raises(ValueError, match="oldest first"):
        weather.trend(_bars(1, 2, 3)[::-1])


def test_the_regime_replay_reads_the_label_as_one_plain_word() -> None:
    day = START
    label = weather.trend(_bars(*range(1, 250)))
    assert regime._named(label, day) == "warming"
    assert regime._named(label, START + timedelta(days=248)) == "up"
