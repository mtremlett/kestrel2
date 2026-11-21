"""The local Stooq daily reader: only OK rows; a line with no file is refused by name."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from desk import daily_local
from desk.lines import LINES

FIXTURE = Path(__file__).parents[1] / "fixtures" / "stooq"


def test_only_ok_rows_are_read_and_a_missing_file_is_refused_by_name() -> None:
    spy = next(line for line in LINES if line.symbol == "SPY")
    got = daily_local.stooq_rows(spy, FIXTURE)
    assert [bar.day for bar in got] == [date(2026, 11, 9), date(2026, 11, 11)]
    isf = next(line for line in LINES if line.venue == "LSE")
    with pytest.raises(ValueError, match=f"ticker={isf.symbol}.UK holds no daily row"):
        daily_local.stooq_rows(isf, FIXTURE)
