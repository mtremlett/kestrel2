"""The lines parked live: late, missing or out of line, and back by themselves."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from desk import bars, keeper
from desk.bars import Five, Source
from desk.lines import Line

NOW, LINES = datetime(2026, 11, 16, 10, tzinfo=UTC), [Line(s, "LSE", "GBP", 1) for s in "ABCD"]


def _bar(minutes: int, price: int) -> Five:
    p = Decimal(price)
    return Five(NOW - timedelta(minutes=minutes), p, p, p, p, 1)


def test_a_late_missing_or_out_of_line_line_is_parked_and_comes_back(tmp_path: Path) -> None:
    hot, (clean, late, jump, none) = tmp_path / keeper.HOT, LINES
    with bars.writing(hot, Source.IBKR) as kept:
        kept.five(clean, [_bar(10, 100), _bar(5, 100)])
        kept.five(late, [_bar(30, 100), _bar(20, 100)])
        kept.five(jump, [_bar(10, 100), _bar(5, 200)])
    parked = keeper.parked_live(hot, LINES, NOW)
    assert set(parked) == {"B", "C", "D"} and "moved" in parked["C"]
    assert keeper.parked_live(hot, LINES, NOW - timedelta(minutes=115)) == {}  # just opened
    with bars.writing(hot, Source.IBKR) as kept:
        kept.five(late, [_bar(5, 100)])
    assert "B" not in keeper.parked_live(hot, LINES, NOW) and none.symbol in parked
