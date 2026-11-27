"""Contract: the old Stooq store's daily rows are read, OK rows only, a missing file by name."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from desk.daily_local import stooq_rows
from desk.lines import LINES

FIXTURE = Path(__file__).parent.parent / "fixtures" / "stooq"
ISF = next(line for line in LINES if line.symbol == "ISF")


def test_only_the_ok_rows_are_read_and_a_missing_file_is_refused_by_name() -> None:
    got = stooq_rows(ISF, FIXTURE)
    assert [(b.day, b.close) for b in got] == [(date(2025, 10, 23), Decimal("10.5"))]
    other = next(line for line in LINES if line.venue == "US")
    with pytest.raises(ValueError, match=f"{other.symbol}.US holds no daily row"):
        stooq_rows(other, FIXTURE)
