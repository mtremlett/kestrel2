"""The Stooq client: its table is read once on entry; anything else is refused by name."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from desk import stooq
from desk.lines import Line

LINE = Line("VUAG", "LSE", "GBP", 1)
TABLE = b"Date,Open,High,Low,Close,Volume\n2020-03-02,1,2,0.5,1.5,10\n2020-03-03,1,2,0.5,1.5,\n"


def test_a_table_is_read_into_bars_before_the_day_and_a_refusal_names_what_came() -> None:
    bars = stooq.parse(LINE, TABLE, date(2020, 3, 3))
    assert [(b.day, b.close, b.volume) for b in bars] == [(date(2020, 3, 2), Decimal("1.5"), 10)]
    assert "s=vuag.uk&i=d&d2=20200303&apikey=k" in stooq.address(LINE, date(2020, 3, 3), "k")
    with pytest.raises(ValueError, match="VUAG: Stooq gave no table of bars: Access denied"):
        stooq.parse(LINE, b"Access denied", date(2020, 3, 3))
    with pytest.raises(ValueError, match="a bar that cannot be read"):
        stooq.parse(LINE, b"Date,Open,High,Low,Close,Volume\nx,1,2,3,4,5\n", date(2020, 3, 3))
