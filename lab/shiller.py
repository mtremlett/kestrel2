"""shiller - THE S&P 500 TOTAL-RETURN MONTHLY LINE from January 1901, built from Shiller's free
monthly table (the open CSV of his data: date, index price, dividend per year). IBKR has no bars
that old, so the archive is the only source and every bar says so (source `shiller`). The
index starts at January 1901's price; each month it grows by the price change plus a twelfth of
the year's dividend, reinvested. A month is a flat bar (open = high = low = close, no volume),
named by its first day in UTC. Pure: text in, bars out; the file's fetch and its place in the
store belong to the writer."""

from __future__ import annotations

import csv
from datetime import UTC, date, datetime
from decimal import Decimal
from io import StringIO

from desk.rollup import Candle

FROM_SHILLER = "shiller"
JANUARY_1901 = date(1901, 1, 1)
_TENTHOUSANDTH = Decimal("0.0001")  #: the store keeps every price to a ten-thousandth


def total_return(text: str) -> list[Candle]:
    """The monthly total-return bars of the table's text from January 1901 on, one a month;
    a missing or repeated month, or a price or dividend that cannot be, is refused with its date."""
    rows = [
        (date.fromisoformat(r["Date"]), r["SP500"], r["Dividend"])
        for r in csv.DictReader(StringIO(text))
    ]
    bars: list[Candle] = []
    last: tuple[Decimal, Decimal] | None = None  # the index and the price of the month before
    for month, price_text, dividend_text in rows:
        if month < JANUARY_1901:
            continue
        if month.day != 1 or (bars and (month.year * 12 + month.month) != _number(bars[-1]) + 1):
            raise ValueError(f"{month} is not the month after the one before it")
        price, dividend = Decimal(price_text), Decimal(dividend_text)
        if price <= 0 or dividend < 0:
            raise ValueError(f"{month} has a price or dividend that cannot be")
        index = price if last is None else last[0] * (price + dividend / 12) / last[1]
        last = (index, price)
        close = index.quantize(_TENTHOUSANDTH)
        bars.append(
            Candle(
                datetime(month.year, month.month, 1, tzinfo=UTC),
                close,
                close,
                close,
                close,
                0,
                FROM_SHILLER,
            )
        )
    if not bars or bars[0].start.date() != JANUARY_1901:
        raise ValueError(f"the table does not begin at {JANUARY_1901}")
    return bars


def _number(bar: Candle) -> int:
    """The month's count since year 0, so the next month is one more."""
    return bar.start.year * 12 + bar.start.month
