"""A day the keeper's judge drops hides only the row that is the refused bar (R-DATA-77)."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest
import test_keeper as tk

from desk import bars, keeper


def test_a_refused_bar_never_hides_a_different_bar_held_for_its_day(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pretend, hot = tk.Archive(), tmp_path / keeper.HOT
    pretend.keep(tmp_path, tk._at(6))
    before = {line: bars.daily(hot, line) for line in tk.LINES}
    nine = Decimal(9)
    still = [
        replace(b, open=nine, high=nine, low=nine, close=nine, volume=0) for b in before[tk.UK][-6:]
    ]
    monkeypatch.setattr(keeper, "RULES", "an older set of rules")
    monkeypatch.setattr(
        pretend,
        "daily",
        lambda line, _day: (*before[line][:-6], *still) if line == tk.UK else before[line],
    )
    pretend.keep(tmp_path, tk._at(6, 10))
    now = bars.daily(hot, tk.UK)
    assert now[-5:] == before[tk.UK][-5:] and len(now) == len(before[tk.UK])  # true days stand
    assert all(bars.daily(hot, x) == before[x] for x in (tk.US, tk.TWIN))
