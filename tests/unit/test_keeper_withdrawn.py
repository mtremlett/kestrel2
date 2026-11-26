"""A day the keeper's judge later drops is withdrawn, never deleted (R-RUNNER-311)."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import test_keeper as tk

from desk import bars, keeper, store_scope
from desk.lines import Line


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
    monkeypatch.setattr(keeper, "RULES", "an older set of rules")
    monkeypatch.setattr(
        pretend,
        "daily",
        lambda line, _day: (*before[line][:-6], *still) if line == tk.UK else before[line],
    )
    pretend.keep(tmp_path, tk._at(6, 10))
    now = bars.daily(hot, tk.UK)
    assert [b.day for b in now] == [b.day for b in before[tk.UK]]
    assert [b for b in now if b not in before[tk.UK]] == [still[0]]  # only the kept day moved
    assert all(bars.daily(hot, x) == before[x] for x in (tk.US, tk.TWIN))


def test_a_day_the_judge_refuses_is_unserved_and_a_true_bar_brings_it_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pretend, hot = tk.Archive(), tmp_path / keeper.HOT
    pretend.keep(tmp_path, tk._at(6))
    before = bars.daily(hot, tk.UK)
    judged = store_scope.judge
    monkeypatch.setattr(keeper, "RULES", "an older set of rules")

    def refusing(line: Line, *a: Any, **k: Any) -> Any:
        kept, faults, park = judged(line, *a, **k)
        return (kept[:-1] if line == tk.UK else kept), faults, park

    monkeypatch.setattr(keeper, "scoped_judge", refusing)
    pretend.keep(tmp_path, tk._at(6, 10))
    assert [b.day for b in bars.daily(hot, tk.UK)] == [b.day for b in before[:-1]]  # unserved
    monkeypatch.setattr(keeper, "scoped_judge", judged)
    monkeypatch.setattr(keeper, "RULES", "a newer set of rules")
    pretend.keep(tmp_path, tk._at(6, 20))
    assert bars.daily(hot, tk.UK) == before  # a true bar brings the day back
