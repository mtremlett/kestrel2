"""The intraday weather: trend labels worked by hand, per session, blind to the future."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from desk.rollup import Candle
from lab import weather_intraday as wi


def _bars(*sessions: tuple[int, ...]) -> list[Candle]:
    out = []
    for d, closes in enumerate(sessions):
        t0 = datetime(2024, 1, 2 + d, 14, 30, tzinfo=UTC)
        for n, c in enumerate(closes):
            px = Decimal(c)
            out.append(Candle(t0 + timedelta(minutes=5 * n), px, px, px, px, 1, "ibkr"))
    return out


def test_labels_are_hand_worked_per_session_and_future_blind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(wi, "WINDOW", 3)
    bars = _bars((10, 12, 14, 13, 9), (20, 10, 30, 30))
    got = list(wi.trend(bars).values())
    # session 1: means 12, 13, 12 -> up, down, down; session 2 restarts: warming twice,
    # then 30 vs mean 20 up, 30 vs mean 23.3 up
    assert got == ["warming", "warming", "up", "down", "down", "warming", "warming", "up", "up"]
    for k in range(len(bars)):
        assert list(wi.trend(bars[: k + 1]).values()) == got[: k + 1]
    with pytest.raises(ValueError):
        wi.trend(bars[::-1])
