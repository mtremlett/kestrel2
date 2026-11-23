"""A day the keeper's judge later refuses hides only the refused bar, never a true held one
(R-RUNNER-311, R-DATA-77)."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest
import test_keeper as tk

from desk import bars, keeper


def test_a_refused_day_leaves_the_true_bar_held_for_it_standing_and_no_line_shrinks(
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
    assert [b.day for b in bars.daily(hot, tk.UK)][-5:] == [b.day for b in before[tk.UK][-5:]]
    assert bars.daily(hot, tk.UK)[-5:] == before[tk.UK][-5:]  # the refused run hid no true bar
    assert all(bars.daily(hot, x) == before[x] for x in (tk.US, tk.TWIN))
    with bars.writing(hot) as round_:
        round_.daily(tk.UK, before[tk.UK][-6:])  # a true bar brings a day back
    assert bars.daily(hot, tk.UK) == before[tk.UK]
