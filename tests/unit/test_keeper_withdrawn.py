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
from desk.store import Bar


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


D = 20  #: the session each row of the table is about (of about seventy since August)


def _history() -> list[Bar]:
    """The line's held history: true bars, no two alike."""
    return list(tk._bars(tk.UK, tk.MON))


def _frozen(bars: list[Bar], days: range) -> list[Bar]:
    """The bars with those sessions repeating the one before the first, with no volume: a
    frozen feed (five or more in a row are dropped; one alone is a quiet day)."""
    was = bars[D - 5]
    return [replace(was, day=b.day, volume=0) if n in days else b for n, b in enumerate(bars)]


def _zero(bars: list[Bar]) -> list[Bar]:
    """The bars with session D's close at zero: a price that cannot be."""
    return [replace(b, close=Decimal(0)) if n == D else b for n, b in enumerate(bars)]


#: THE WITHDRAW RULE, one synthetic row per rule (failure pattern 13): what the store holds for
#: session D (its bar, and whether it is marked withdrawn), what the archive answers, and whether
#: D is served after one refresh. The judge is one judgement: a day stays withdrawn only while it
#: drops the held bar in the line's whole held history; nothing is ever deleted.
ROWS = {
    "an untrue answered day whose held bar is that bar is withdrawn": (
        _zero(_history()),
        False,
        _zero(_history()),
        False,
    ),
    "an untrue answered day over another held bar leaves the held one served (R-DATA-77)": (
        _history(),
        False,
        _zero(_history()),
        True,
    ),
    "a frozen answer over a held bar the whole history keeps leaves it served": (
        _frozen(_history(), range(D, D + 1)),
        False,
        _frozen(_history(), range(D - 4, D + 1)),
        True,
    ),
    "a day withdrawn by an older judge whose held bar the judge keeps is served again": (
        _history(),
        True,
        _history()[:D] + _history()[D + 1 :],
        True,
    ),
    "a withdrawn day whose held bar the judge still drops stays withdrawn": (
        _zero(_history()),
        True,
        _history()[:D] + _history()[D + 1 :],
        False,
    ),
}


@pytest.mark.parametrize("row", ROWS)
def test_the_withdraw_rule_table(tmp_path: Path, row: str) -> None:
    held, marked, answer, served = ROWS[row]
    hot, day = tmp_path / keeper.HOT, held[D].day
    with bars.writing(hot, bars.Source.IBKR) as round_:
        round_.daily(tk.UK, held)
    with bars.writing(hot, bars.Source.IBKR) as round_:  # an older judge's mark: none given
        round_.daily(tk.UK, [], withdrawn=[day] if marked else [])
    assert (day in {b.day for b in bars.daily(hot, tk.UK)}) is not marked
    keeper._kept_in(hot, {tk.UK: tuple(answer)}, tk.MON, {}, standing=False)
    shown = {b.day: b for b in bars.daily(hot, tk.UK)}
    assert (day in shown) is served
    assert not served or shown[day] == held[D]  # served as held: its bar unchanged
    assert set(bars.sources(hot, tk.UK, bars.DAILY)) == {bars.Source.IBKR}  # nothing relabelled
