"""archive - THE ONE CLIENT FOR THE FREE PRICE ARCHIVE. It asks for a line's daily bars, or
its five-minute bars, and reads the answer exactly, once, on entry: pence become pounds here
and nowhere else, and an answer about another line, of another span of bar, or in a currency
the master does not hold, is refused.

The archive is Yahoo's public chart service: free, with no key, and with no promise that it
lasts. It dates each daily bar by its session's opening moment in UTC, which for London and
New York falls on the session's own day; that day is the bar's day. A five-minute bar it
dates by the moment the five minutes start, and it keeps them for sixty days only (DAT-11)."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from http.client import HTTPException
from typing import Any, TypeVar
from urllib.request import Request, urlopen

from desk.bars import EPOCH, Five
from desk.lines import Line
from desk.store import Bar, Refused

SOURCE = "https://query1.finance.yahoo.com/v8/finance/chart/"
SUFFIX = {"LSE": ".L", "US": ""}  #: the archive's name for a line is its symbol and this
PENCE = {"GBP": "GBp"}  #: the archive's name for a hundredth of a currency
SINCE = date(2010, 1, 1)  #: the first year the calendar knows
FIELDS = ("open", "high", "low", "close", "volume")
DAILY, FIVE = "1d", "5m"  #: the archive's names for the two spans of bar the desk asks for
#: How far back five-minute bars are asked for. The archive refuses the whole answer when any
#: of it is over sixty days old (seen 13 November 2026), so the desk asks for a day less.
KEPT = timedelta(days=59)
When = TypeVar("When")
Read = TypeVar("Read")
Row = tuple[int, Decimal, Decimal, Decimal, Decimal, int]


def _moment(day: date) -> int:
    return int(datetime(day.year, day.month, day.day, tzinfo=UTC).timestamp())


def _address(line: Line, first: int, end: int, span: str) -> str:
    name = line.symbol + SUFFIX[line.venue]
    return f"{SOURCE}{name}?period1={first}&period2={end}&interval={span}"


def address(line: Line, day: date) -> str:
    """Where every bar of a line from 2010 up to, and not including, day is asked for."""
    return _address(line, _moment(SINCE), _moment(day), DAILY)


def address_five(line: Line, now: datetime) -> str:
    """Where every five-minute bar the archive still keeps of a line, up to now, is asked for.
    A now in no time zone is refused."""
    first, end = ((moment - EPOCH) // timedelta(seconds=1) for moment in (now - KEPT, now))
    return _address(line, first, end, FIVE)


def _unit(line: Line, currency: object) -> Decimal:
    if currency == line.currency:
        return Decimal(1)
    if currency == PENCE.get(line.currency):
        return Decimal("0.01")
    raise ValueError(f"{line.symbol}: the archive prices it in {currency}, not {line.currency}")


def _read(line: Line, span: str, payload: bytes) -> tuple[dict[str, Any], list[Row]]:
    """The archive's answer for a line: what it says of the line, and its bars, each with the
    moment it starts, its prices in the line's currency and its volume. A moment it gives
    without a full bar has none."""
    chart = json.loads(payload, parse_float=Decimal, parse_constant=Decimal)["chart"]
    if chart["error"] is not None or not chart["result"]:
        raise ValueError(f"{line.symbol}: the archive gave no answer: {chart['error']}")
    result: dict[str, Any] = chart["result"][0]
    meta: dict[str, Any] = result["meta"]
    if meta["symbol"] != line.symbol + SUFFIX[line.venue]:
        raise ValueError(f"{line.symbol}: the archive answered about {meta['symbol']}")
    if meta["dataGranularity"] != span:
        given = meta["dataGranularity"]
        raise ValueError(f"{line.symbol}: the archive answered in bars of {given}, not {span}")
    unit = _unit(line, meta["currency"])
    stamps: list[int] = result.get("timestamp", [])  # absent when it holds no bar at all
    quote = result["indicators"]["quote"][0] if stamps else {}
    rows = []
    for n, stamp in enumerate(stamps):
        open_, high, low, close, volume = (quote[field][n] for field in FIELDS)
        if None in (open_, high, low, close, volume):
            continue
        if not isinstance(volume, int):
            raise ValueError(f"{line.symbol}: the archive gave a volume of {volume} shares")
        rows.append((stamp, open_ * unit, high * unit, low * unit, close * unit, volume))
    return meta, rows


def parse(line: Line, payload: bytes) -> tuple[Bar, ...]:
    """A line's daily bars from the archive's answer."""
    rows = _read(line, DAILY, payload)[1]
    return tuple(Bar(datetime.fromtimestamp(row[0], UTC).date(), *row[1:]) for row in rows)


def parse_five(line: Line, payload: bytes, now: datetime) -> tuple[Five, ...]:
    """A line's five-minute bars from the archive's answer, as far as they had ended by now.
    The archive closes its answer with the price of the moment, dated at the line's last
    trade or, once the session is over, at its close (seen 13 November 2026, in a session and
    after one): that is no bar. A bar that starts off a five-minute mark refuses the answer."""
    meta, rows = _read(line, FIVE, payload)
    moment = min(meta["regularMarketTime"], meta["currentTradingPeriod"]["regular"]["end"])
    ended = min(moment, (now - EPOCH) // timedelta(seconds=1) - 299)
    return tuple(
        Five(datetime.fromtimestamp(row[0], UTC), *row[1:]) for row in rows if row[0] < ended
    )


def _ask(address: str) -> bytes:
    request = Request(address, headers={"User-Agent": "Mozilla/5.0"})  # noqa: S310
    with urlopen(request, timeout=30) as answer:  # noqa: S310
        return bytes(answer.read())


def fetch(line: Line, day: date) -> tuple[Bar, ...]:
    """Every bar the archive holds for a line before day, read on entry."""
    return parse(line, _ask(address(line, day)))


def fetch_five(line: Line, now: datetime) -> tuple[Five, ...]:
    """Every five-minute bar the archive still keeps for a line, up to now, read on entry."""
    return parse_five(line, _ask(address_five(line, now)), now)


def gather(
    lines: Iterable[Line], when: When, ask: Callable[[Line, When], Read]
) -> dict[Line, Read | Refused]:
    """Every line's bars as ask reads them: `fetch` before a day, `fetch_five` up to a moment.
    A line the archive cannot be reached for, or whose answer is refused, is refused alone,
    with the reason, and the others carry on."""
    answers: dict[Line, Read | Refused] = {}
    for line in lines:
        try:
            answers[line] = ask(line, when)
        except (OSError, HTTPException, ValueError) as refusal:  # the network's or the answer's
            answers[line] = Refused(f"{type(refusal).__name__}: {refusal}")
    return answers
