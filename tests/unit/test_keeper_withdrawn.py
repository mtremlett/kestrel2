"""A day the keeper's judge later drops is withdrawn, never deleted (R-RUNNER-311)."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest
import test_keeper as tk

from desk import bars, keeper


def test_a_day_the_judge_later_drops_is_withdrawn_not_deleted_and_no_line_shrinks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pretend, hot = tk.Archive(), tmp_path / keeper.HOT
    pretend.keep(tmp_path, tk._at(6))
    before = {line: bars.daily(hot, line) for line in tk.LINES}
    nine = Decimal(9)
    still = [
        replace(b, open=nine, high=nine, low=nine, close=nine, volume=0) for b in before[tk.UK][-6:]
    ]
    with bars.writing(hot) as round_:
        round_.daily(tk.UK, still)  # the older rules kept the frozen run: it is the bar held
    monkeypatch.setattr(keeper, "RULES", "an older set of rules")
    monkeypatch.setattr(
        pretend,
        "daily",
        lambda line, _day: (*before[line][:-6], *still) if line == tk.UK else before[line],
    )
    pretend.keep(tmp_path, tk._at(6, 10))
    assert [b.day for b in bars.daily(hot, tk.UK)] == [
        b.day for b in before[tk.UK][:-5]
    ]  # the frozen run is unserved
    assert all(bars.daily(hot, x) == before[x] for x in (tk.US, tk.TWIN))
    with bars.writing(hot) as round_:
        round_.daily(tk.UK, before[tk.UK][-6:])  # a true bar brings a day back
    assert bars.daily(hot, tk.UK) == before[tk.UK]


def test_a_refused_day_over_an_older_different_bar_hides_nothing(tmp_path: Path) -> None:
    store, old = tmp_path / "bars.db", tk.Archive().daily(tk.UK, tk._at(6).date())[0]
    new = replace(old, open=Decimal(9), high=Decimal(9), low=Decimal(9), close=Decimal(9))
    with bars.writing(store) as round_:
        round_.daily(tk.UK, (old,))
        round_.daily(tk.UK, (), refused=(new,))
    assert bars.daily(store, tk.UK) == (old,)
    with bars.writing(store) as round_:
        round_.daily(tk.UK, (), refused=(old,))
    assert bars.daily(store, tk.UK) == ()
