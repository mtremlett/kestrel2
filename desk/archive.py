"""archive - THE ONE CLIENT FOR THE FREE PRICE ARCHIVE. It asks for a line's daily bars and
reads the answer exactly, once, on entry: pence become pounds here and nowhere else, and an
answer about another line, or in a currency the master does not hold, is refused.

The archive is Yahoo's public chart service: free, with no key, and with no promise that it
lasts. It dates each daily bar by its session's opening moment in UTC, which for London and
New York falls on the session's own day; that day is the bar's day."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from datetime import UTC, date, datetime
from decimal import Decimal
from http.client import HTTPException
from typing import Any
from urllib.request import Request, urlopen

from desk.lines import Line
from desk.store import Bar, Refused

SOURCE = "https://query1.finance.yahoo.com/v8/finance/chart/"
SUFFIX = {"LSE": ".L", "US": ""}  #: the archive's name for a line is its symbol and this
PENCE = {"GBP": "GBp"}  #: the archive's name for a hundredth of a currency
SINCE = date(2010, 1, 1)  #: the first year the calendar knows
FIELDS = ("open", "high", "low", "close", "volume")


def _moment(day: date) -> int:
    return int(datetime(day.year, day.month, day.day, tzinfo=UTC).timestamp())


def address(line: Line, day: date) -> str:
    """Where every bar of a line from 2010 up to, and not including, day is asked for."""
    return (
        f"{SOURCE}{line.symbol}{SUFFIX[line.venue]}?period1={_moment(SINCE)}"
        f"&period2={_moment(day)}&interval=1d"
    )


def _unit(line: Line, currency: object) -> Decimal:
    if currency == line.currency:
        return Decimal(1)
    if currency == PENCE.get(line.currency):
        return Decimal("0.01")
    raise ValueError(f"{line.symbol}: the archive prices it in {currency}, not {line.currency}")


def parse(line: Line, payload: bytes) -> tuple[Bar, ...]:
    """A line's bars from the archive's answer. A day it gives without a full bar has none."""
    chart = json.loads(payload, parse_float=Decimal, parse_constant=Decimal)["chart"]
    if chart["error"] is not None or not chart["result"]:
        raise ValueError(f"{line.symbol}: the archive gave no answer: {chart['error']}")
    result: dict[str, Any] = chart["result"][0]
    named = result["meta"]["symbol"]
    if named != line.symbol + SUFFIX[line.venue]:
        raise ValueError(f"{line.symbol}: the archive answered about {named}")
    unit = _unit(line, result["meta"]["currency"])
    stamps: list[int] = result.get("timestamp", [])  # absent when it holds no bar at all
    quote = result["indicators"]["quote"][0] if stamps else {}
    bars = []
    for n, stamp in enumerate(stamps):
        open_, high, low, close, volume = (quote[field][n] for field in FIELDS)
        if None in (open_, high, low, close, volume):
            continue
        if not isinstance(volume, int):
            raise ValueError(f"{line.symbol}: the archive gave a volume of {volume} shares")
        day = datetime.fromtimestamp(stamp, UTC).date()
        bars.append(Bar(day, open_ * unit, high * unit, low * unit, close * unit, volume))
    return tuple(bars)


def fetch(line: Line, day: date) -> tuple[Bar, ...]:
    """Every bar the archive holds for a line before day, read on entry."""
    request = Request(address(line, day), headers={"User-Agent": "Mozilla/5.0"})  # noqa: S310
    with urlopen(request, timeout=30) as answer:  # noqa: S310
        return parse(line, answer.read())


def gather(
    lines: Iterable[Line], day: date, ask: Callable[[Line, date], tuple[Bar, ...]] = fetch
) -> dict[Line, tuple[Bar, ...] | Refused]:
    """Every line's bars before day. A line the archive cannot be reached for, or whose
    answer is refused, is refused alone, with the reason, and the others carry on."""
    answers: dict[Line, tuple[Bar, ...] | Refused] = {}
    for line in lines:
        try:
            answers[line] = ask(line, day)
        except (OSError, HTTPException, ValueError) as refusal:  # the network's or the answer's
            answers[line] = Refused(f"{type(refusal).__name__}: {refusal}")
    return answers
