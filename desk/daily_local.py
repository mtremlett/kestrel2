"""daily_local - THE OLD STOOQ STORE'S DAILY ROWS, READ-ONLY (R-RUNNER-419). stooq_store keeps a
line's daily parquet at freq=d/market=<uk|us>/ticker=<SYMBOL>.<UK|US>/part.parquet; only the rows
it marks OK are read, a day by its stamp's UTC date, and a line with no file is refused by name."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pyarrow.parquet as pq  # type: ignore[import-untyped]  # ships no stubs

from desk.lines import Line
from desk.store import Bar

MARKET = {"LSE": "UK", "US": "US"}  #: stooq_store's name for each venue
PRICED = ("ts", "open", "high", "low", "close", "volume", "row_state")  #: stooq_store's columns


def _d(x: float | str) -> Decimal:
    return Decimal(str(x))


def stooq_rows(line: Line, folder: Path) -> list[Bar]:
    """A line's OK daily rows in stooq_store; none held is refused."""
    market = MARKET[line.venue]
    file = folder / f"freq=d/market={market.lower()}/ticker={line.symbol}.{market}/part.parquet"
    if not file.is_file():
        raise ValueError(f"{file.parent.name} holds no daily row of {line.symbol}")
    table = pq.ParquetFile(file).read(columns=list(PRICED))
    return [
        Bar(at.date(), _d(o), _d(h), _d(lo), _d(c), int(v))
        for at, o, h, lo, c, v, state in zip(*(table[k].to_pylist() for k in PRICED), strict=True)
        if state == "OK" and None not in (o, h, lo, c, v)
    ]
