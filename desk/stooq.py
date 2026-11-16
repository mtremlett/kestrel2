"""stooq - THE ONE CLIENT FOR STOOQ, the second source of daily bars (R-RUNNER-189). It asks
for a line's daily history afresh and reads the answer once, on entry, into the store's Bar.

Stooq gives a plain table, one row to a session: Date,Open,High,Low,Close,Volume. Its London
prices may be in pence or pounds; that is matched in the one store, by the closes both sources
hold, never here. An answer with another header, or a row that is not a bar, is refused."""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from urllib.request import Request, urlopen

from desk.lines import Line
from desk.store import Bar

SOURCE = "https://stooq.com/q/d/l/"
SUFFIX = {"LSE": ".uk", "US": ".us"}  #: Stooq's name for a line is its symbol and this
SINCE = date(2010, 1, 1)  #: the first year the calendar knows
HEADER = ["Date", "Open", "High", "Low", "Close", "Volume"]


def address(line: Line, day: date) -> str:
    """Where every bar of a line from 2010 up to, and not including, day is asked for."""
    name = (line.symbol + SUFFIX[line.venue]).lower()
    return f"{SOURCE}?s={name}&d1={SINCE:%Y%m%d}&d2={day:%Y%m%d}&i=d"


def parse(line: Line, payload: bytes, day: date) -> tuple[Bar, ...]:
    """A line's daily bars before day from Stooq's answer; refused if no table."""
    rows = list(csv.reader(payload.decode("utf-8").splitlines()))
    if not rows or rows[0] != HEADER:
        raise ValueError(f"{line.symbol}: Stooq gave no table of bars: {payload[:40]!r}")
    bars = []
    for row in rows[1:]:
        try:
            when = date.fromisoformat(row[0])
            o, h, low, c = (Decimal(x) for x in row[1:5])
            bar = Bar(when, o, h, low, c, int(row[5]))
        except (ValueError, InvalidOperation, IndexError) as bad:
            raise ValueError(f"{line.symbol}: Stooq gave a row that is no bar: {row}") from bad
        if when < day:
            bars.append(bar)
    return tuple(bars)


def fetch(line: Line, day: date) -> tuple[Bar, ...]:
    """Every bar Stooq holds for a line before day, read on entry."""
    with urlopen(Request(address(line, day)), timeout=30) as answer:  # noqa: S310
        return parse(line, bytes(answer.read()), day)
