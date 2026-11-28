"""Contract: Shiller's table becomes the 1901 total-return monthly line."""

from decimal import Decimal

import pytest

from lab import shiller

TABLE = """Date,SP500,Dividend,Earnings
1900-12-01,6.00,0.30,0.5
1901-01-01,6.10,0.24,0.5
1901-02-01,6.10,0.24,0.5
1901-03-01,6.20,0.24,0.5
"""


def test_the_line_begins_in_january_1901_and_reinvests_the_dividend() -> None:
    bars = shiller.total_return(TABLE)
    assert [b.start.strftime("%Y-%m") for b in bars] == ["1901-01", "1901-02", "1901-03"]
    assert bars[0].close == Decimal("6.1000") and bars[0].volume == 0
    assert bars[1].close == Decimal("6.1000") * (Decimal("6.10") + Decimal("0.02")) / Decimal(
        "6.10"
    )
    assert {b.source for b in bars} == {"shiller"}


@pytest.mark.parametrize(
    "bad",
    [
        TABLE.replace("1901-02-01", "1901-04-01"),
        TABLE.replace("6.20", "0"),
        TABLE.split("\n", 2)[0] + "\n1902-01-01,6,0.2,0\n",
    ],
)
def test_a_gap_a_bad_price_or_a_late_start_is_refused(bad: str) -> None:
    with pytest.raises(ValueError):
        shiller.total_return(bad)
