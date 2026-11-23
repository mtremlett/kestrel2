"""The timeframes: each span's bars start on its marks, and any span is written and read back
through the one store (R-RUNNER-218)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk import bars
from desk.lines import Line
from desk.spans import SPANS, Timed

LINE = Line("BA", "LSE", "GBP", 1)
PRICES = (Decimal("10.5"), Decimal("11"), Decimal("10"), Decimal("10.75"))


def _bar(span: str, start: datetime) -> Timed:
    return Timed(span, start, *PRICES, 7)


def test_the_ten_timeframes_are_held_and_each_round_trips_on_its_mark(tmp_path: Path) -> None:
    assert list(SPANS) == [
        "1m",
        "2m",
        "five-minute",
        "10m",
        "15m",
        "30m",
        "1h",
        "4h",
        "daily",
        "1wk",
    ]
    day = datetime(2026, 11, 16, 8, 0, tzinfo=UTC)  # a Monday
    one = [_bar("1m", day + timedelta(minutes=1)), _bar("1m", day + timedelta(minutes=2))]
    four, week = _bar("4h", day), _bar("1wk", day.replace(hour=0))
    with bars.writing(tmp_path / bars.LIVE) as round_:
        assert round_.timed(LINE, "1m", one) == 2
        assert round_.timed(LINE, "4h", [four]) == 1
        assert round_.timed(LINE, "1wk", [week]) == 1
    path, far = tmp_path / bars.LIVE, day + timedelta(days=8)
    assert bars.timed(path, LINE, "1m", day, far) == tuple(one)
    assert bars.timed(path, LINE, "4h", day, far) == (four,)
    assert bars.timed(path, LINE, "1wk", day - timedelta(days=1), far) == (week,)
    assert sorted(p.name for p in tmp_path.glob("*.db")) == sorted([bars.HISTORY, bars.LIVE])


@pytest.mark.parametrize(
    ("span", "start"),
    [
        ("1m", datetime(2026, 11, 16, 8, 1, 30, tzinfo=UTC)),
        ("4h", datetime(2026, 11, 16, 9, 0, tzinfo=UTC)),
        ("1wk", datetime(2026, 11, 17, 0, 0, tzinfo=UTC)),
        ("1m", datetime(2026, 11, 16, 8, 1)),
        ("daily", datetime(2026, 11, 16, tzinfo=UTC)),
    ],
)
def test_a_bar_off_its_span_s_mark_is_refused(span: str, start: datetime) -> None:
    with pytest.raises(ValueError):
        _bar(span, start)
