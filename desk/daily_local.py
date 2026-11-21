"""daily_local - THE LOCAL STOOQ DAILY BARS (R-RUNNER-419, 21 November 2026). A line's daily rows
in stooq_store (freq=d/market=../ticker=SYM.MKT/part.parquet), read-only: only rows it marks OK,
a day by its stamp's UTC date. A line with no file is refused by name, never answered empty."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pyarrow.parquet as pq  # type: ignore[import-untyped]  # ships no stubs

from desk.lines import Line
from desk.store import Bar

PRICED = ("ts", "open", "high", "low", "close", "volume", "row_state")  #: stooq_store's columns
MARKET = {"LSE": "uk", "US": "us"}  #: stooq_store's folder for a venue


def _d(x: float | str) -> Decimal:
    return Decimal(str(x))


def stooq_rows(line: Line, folder: Path) -> list[Bar]:
    """A line's daily rows marked OK; none held is a ValueError naming the line's folder."""
    market = MARKET[line.venue]
    file = folder / f"freq=d/market={market}/ticker={line.symbol}.{market.upper()}/part.parquet"
    if not file.is_file():
        raise ValueError(f"{file.parent.name} holds no daily row of {line.symbol}")
    table = pq.ParquetFile(file).read(columns=list(PRICED))
    return [
        Bar(at.date(), _d(o), _d(h), _d(lo), _d(c), int(v))
        for at, o, h, lo, c, v, state in zip(*(table[k].to_pylist() for k in PRICED), strict=True)
        if state == "OK" and None not in (o, h, lo, c, v)
    ]
