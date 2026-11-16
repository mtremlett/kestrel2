"""stooq - THE ONE CLIENT FOR STOOQ, the second source of daily bars. It asks for a line's
whole daily history and reads the answer exactly, once, on entry: anything but the price table
(Stooq answers a client it doubts with a page of script, or with the words "No data") is
refused, with what it said. Prices come as Stooq quotes them; `matched` brings them into the
archive's unit by the closes both hold, the one place that does so."""

from __future__ import annotations

import csv
from collections.abc import Sequence
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from urllib.request import Request, urlopen

from desk.archive import SINCE
from desk.lines import Line
from desk.store import SPLIT_NEAR, Bar

SOURCE = "https://stooq.com/q/d/l/"
SUFFIX = {"LSE": ".uk", "US": ".us"}  #: Stooq's name for a line is its symbol and this
PRICES = ("open", "high", "low", "close")
HEADER = "Date,Open,High,Low,Close,Volume"


def address(line: Line, day: date) -> str:
    """Where every bar of a line from 2010 up to, and not including, day is asked for."""
    name = line.symbol.lower() + SUFFIX[line.venue]
    return f"{SOURCE}?s={name}&i=d&d1={SINCE:%Y%m%d}&d2={day - timedelta(1):%Y%m%d}"


def parse(line: Line, payload: bytes) -> tuple[Bar, ...]:
    """The bars in Stooq's answer for a line; ValueError for any answer that is not the table."""
    text = payload.decode("utf-8")
    if not text.startswith(HEADER):
        raise ValueError(f"Stooq gave no price table for {line.symbol}: {text[:60]!r}")
    try:
        return tuple(
            Bar(
                date.fromisoformat(row["Date"]),
                Decimal(row["Open"]),
                Decimal(row["High"]),
                Decimal(row["Low"]),
                Decimal(row["Close"]),
                int(Decimal(row["Volume"] or 0)),
            )
            for row in csv.DictReader(text.splitlines())
        )
    except (InvalidOperation, KeyError, TypeError, OverflowError) as bad:
        raise ValueError(
            f"Stooq's table for {line.symbol} has a row that cannot be read: {bad!r}"
        ) from bad


def matched(first: Sequence[Bar], second: Sequence[Bar]) -> dict[date, Bar]:
    """The second source's bars by day, in the first's unit: the middle ratio of the closes both
    hold is read as 1, 100 or 1/100 (pence among pounds), else left as it is."""
    held = {b.day: b.close for b in first if b.close.is_finite() and b.close > 0}
    sane = [b for b in second if b.close.is_finite() and b.close > 0]
    ratios = sorted(held[b.day] / b.close for b in sane if b.day in held)
    middle = ratios[len(ratios) // 2] if ratios else Decimal(1)
    best = min((Decimal(1), Decimal(100), Decimal(1) / 100), key=lambda k: abs(middle / k - 1))
    k = best if abs(middle / best - 1) <= SPLIT_NEAR else Decimal(1)
    return {b.day: replace(b, **{p: getattr(b, p) * k for p in PRICES}) for b in sane}


def fetch(line: Line, day: date) -> tuple[Bar, ...]:
    """Every bar Stooq holds for a line before day, read on entry."""
    request = Request(address(line, day), headers={"User-Agent": "Mozilla/5.0"})  # noqa: S310
    with urlopen(request, timeout=30) as answer:  # noqa: S310
        return parse(line, answer.read())
