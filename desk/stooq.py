"""stooq - THE ONE CLIENT FOR STOOQ'S DAILY BARS, the second source beside the archive. It asks
for a line's whole daily history afresh, and reads the answer once, on entry, into bars as
Stooq prices them: its London prices may be in pence, and the store, not this client, matches
the unit by the closes both sources hold. Stooq now refuses a download without a key (seen 16
November 2026: "Access denied"), which the operator gets free from stooq.com and puts in
STOOQ_API_KEY; without it every ask is refused, in those words, and the archive stands alone."""

from __future__ import annotations

import csv
import os
from datetime import date
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from desk.lines import Line
from desk.store import Bar

SOURCE = "https://stooq.com/q/d/l/"
SUFFIX = {"LSE": "uk", "US": "us"}  #: Stooq's market for a venue, after the symbol's dot
HEADER = ["Date", "Open", "High", "Low", "Close", "Volume"]
KEY = "STOOQ_API_KEY"


def address(line: Line, day: date, key: str | None = None) -> str:
    """Where every daily bar of a line before day is asked for (the key, if one is held)."""
    query = {"s": f"{line.symbol.lower()}.{SUFFIX[line.venue]}", "i": "d", "d2": f"{day:%Y%m%d}"}
    return f"{SOURCE}?{urlencode(query | ({'apikey': key} if key else {}))}"


def _prices(row: list[str]) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    o, h, lo, c = (Decimal(p) for p in row[1:5])
    return o, h, lo, c


def parse(line: Line, payload: bytes, day: date) -> tuple[Bar, ...]:
    """A line's daily bars before day from Stooq's CSV; anything but its table is refused."""
    rows = list(csv.reader(payload.decode("utf-8").splitlines()))
    if not rows or rows[0] != HEADER:
        said = rows[0][0] if rows and rows[0] else "nothing"
        raise ValueError(f"{line.symbol}: Stooq gave no table of bars: {said[:60]}")
    try:
        bars = tuple(Bar(date.fromisoformat(r[0]), *_prices(r), int(r[5] or 0)) for r in rows[1:])
    except (ValueError, InvalidOperation, IndexError) as bad:
        raise ValueError(f"{line.symbol}: Stooq gave a bar that cannot be read: {bad}") from bad
    return tuple(bar for bar in bars if bar.day < day)


def _ask(address: str) -> bytes:
    with urlopen(Request(address), timeout=30) as answer:  # noqa: S310
        return bytes(answer.read())


def fetch(line: Line, day: date) -> tuple[Bar, ...]:
    """Every bar Stooq holds for a line before day, read on entry."""
    return parse(line, _ask(address(line, day, os.environ.get(KEY))), day)
