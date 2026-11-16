"""The Stooq client: its address, and a table of bars read once, on entry."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from desk import stooq
from desk.lines import Line

UK, DAY = Line("VUAG", "LSE", "GBP", 1), date(2020, 3, 4)
ROWS = ["Date,Open,High,Low,Close,Volume", "2020-03-02,1,2,0.5,1.5,100", "2020-03-04,1,1,1,1,1"]
TABLE = "\n".join(ROWS).encode()


def test_the_address_names_the_line_by_its_venue_and_asks_up_to_the_day() -> None:
    assert stooq.address(UK, DAY).endswith("?s=vuag.uk&d1=20100101&d2=20200304&i=d")


def test_a_table_gives_the_bars_before_the_day_and_nothing_else_is_taken() -> None:
    (bar,) = stooq.parse(UK, TABLE, DAY)
    assert (bar.day, bar.close, bar.volume) == (date(2020, 3, 2), Decimal("1.5"), 100)
    for bad in (b"No data", TABLE.replace(b",100", b",x")):
        with pytest.raises(ValueError, match="VUAG"):
            stooq.parse(UK, bad, DAY)
