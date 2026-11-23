"""The contest over a market: hand-worked worst folds, joins yes or no, trials, and a fold that
cannot be scored said so."""

from __future__ import annotations

import json
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk.store import Bar
from lab import weather

START = date(2024, 1, 1)


def test_the_contest_table_holds_the_hand_worked_worst_folds(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    for name, value in [("WINDOW", 2), ("VOL_WINDOW", 2), ("VOL_RANK", 1), ("DD_WINDOW", 2)]:
        monkeypatch.setattr(weather, name, value)
    monkeypatch.setattr(weather, "DD_LIMIT", Decimal("0.05"))
    bars = [
        Bar(START + timedelta(days=n), Decimal(c), Decimal(c), Decimal(c), Decimal(c), 1)
        for n, c in enumerate([100, 110, 99, 99, 198])
    ]
    #: trend: up day -0.1 vs down days (0, +1) mean 0.5: edge -0.6. Shallow days -0.1, +1 (0.45)
    #: vs deep 0: edge 0.45 joins. Breadth is trend again: -0.6, ties, does not join. Volatility
    #: has only a calm day scored, so it cannot be scored.
    got = {e.layer: e for e in weather.contest(bars, {"a": bars, "b": bars}, folds=1)}
    drawdown, breadth = got["drawdown"].contest, got["breadth"].contest
    assert drawdown is not None and breadth is not None
    assert (drawdown.layer, drawdown.trend, drawdown.wins) == (
        Decimal("0.45"),
        Decimal("-0.6"),
        True,
    )
    assert (breadth.layer, breadth.wins, breadth.trials) == (Decimal("-0.6"), False, 3)
    assert got["volatility"].contest is None and "fold 0 of 1" in got["volatility"].why
    weather.write(tmp_path, list(got.values()))
    table = (tmp_path / "weather.md").read_text(encoding="utf-8")
    assert "| drawdown | 0.45 | -0.6 | yes | 3 |" in table
    assert "| breadth | -0.6 | -0.6 | no | 3 |" in table
    assert "cannot score" in table and "PRE-REVIEW" in table
    saved = json.loads((tmp_path / "weather.json").read_text(encoding="utf-8"))
    assert saved["status"] == "PRE-REVIEW" and len(saved["layers"]) == 3
