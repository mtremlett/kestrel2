"""archive - THE ONE CLIENT FOR THE FREE PRICE ARCHIVE. It asks for a line's daily bars, or
its five-minute bars, and reads the answer exactly, once, on entry: pence become pounds here
and nowhere else, and an answer about another line, of another span of bar, or in a currency
the master does not hold, is refused.

The archive is Yahoo's public chart service: free, with no key, and with no promise that it
lasts. It dates each daily bar by its session's opening moment in UTC, which for London and
New York falls on the session's own day; that day is the bar's day. The pound in dollars it
dates by London's midnight, which in summer is 23:00 UTC of the evening before: an hour is
added to every daily stamp, so that moment falls on the day it opens and a bar is never read
a day early, ahead of its time (G7). A five-minute bar it
dates by the moment the five minutes start, and it keeps them for sixty days only (DAT-11)."""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from http.client import HTTPException
from pathlib import Path
from typing import Any, TypeVar
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from desk import store
from desk.bars import EPOCH, Five, writing
from desk.lines import TAG, Line
from desk.store import Bar, Refused

SOURCE = "https://query1.finance.yahoo.com/v8/finance/chart/"
SUFFIX = {"LSE": ".L", "US": ""}  #: the archive's name for a line is its symbol and this
PENCE = {"GBP": "GBp"}  #: the archive's name for a hundredth of a currency
SINCE = date(2010, 1, 1)  #: the first year the calendar knows
#: The first session of SPY, the reference series (R-RUNGS-5): the archive holds it from here,
#: and is asked this far back for a reference series only, never for a line the desk trades.
REFERENCE_SINCE = date(1993, 1, 29)
FIELDS = ("open", "high", "low", "close", "volume")
DAILY, FIVE = "1d", "5m"  #: the archive's names for the two spans of bar the desk asks for
#: How far back five-minute bars are asked for. The archive refuses the whole answer when any
#: of it is over sixty days old (seen 13 November 2026), so the desk asks for a day less.
KEPT = timedelta(days=59)
STORE = "archive"  #: the folder of a home that holds the raw answers, a folder to a day
MIDNIGHT = timedelta(hours=1)  #: London's midnight in summer, behind UTC's by this
#: Slow: the least gap between two asks. Backing off: the waits, in seconds, before each retry
#: of an ask the archive turned away (too many asks, or its own fault) or did not answer.
#: The archive publishes no limit and the desk never probes for one with bursts (a ban would cost
#: the desk its own data): the pace is a fixed courtesy and the backoff learns from real refusals.
PACE = 1.0
BACKOFF = (5, 30, 120)
ASKED_TO_WAIT = 300  #: the longest wait the archive's own Retry-After is obeyed for, in seconds
#: Where the runner reads whether the archive refuses: `{"refusing_since": <time or null>}`.
STATE = "archive.json"
ALERT_AFTER = timedelta(hours=6)  #: how long the archive may refuse before the operator is told
When = TypeVar("When")
Read = TypeVar("Read")
Row = tuple[int, Decimal, Decimal, Decimal, Decimal, int]


def _moment(day: date) -> int:
    return int(datetime(day.year, day.month, day.day, tzinfo=UTC).timestamp())


def _name(line: Line) -> str:
    """What the archive calls a line: an adjusted twin is asked for by its series' own name."""
    return line.symbol.removesuffix(TAG) + SUFFIX[line.venue]


def _address(line: Line, first: int, end: int, span: str) -> str:
    name = _name(line)
    return f"{SOURCE}{name}?period1={first}&period2={end}&interval={span}"


def address(line: Line, day: date, since: date = SINCE) -> str:
    """Where every bar of a line from since (2010) up to, and not including, day is asked for."""
    return _address(line, _moment(since), _moment(day), DAILY)


def address_five(line: Line, now: datetime, back: timedelta = KEPT) -> str:
    """Where a line's five-minute bars up to now are asked for: every one the archive still
    keeps, or those of a shorter time back. A now in no time zone is refused."""
    first, end = ((moment - EPOCH) // timedelta(seconds=1) for moment in (now - back, now))
    return _address(line, first, end, FIVE)


def _unit(line: Line, currency: object) -> Decimal:
    if currency == line.currency:
        return Decimal(1)
    if currency == PENCE.get(line.currency):
        return Decimal("0.01")
    raise ValueError(f"{line.symbol}: the archive prices it in {currency}, not {line.currency}")


def _adjust(
    line: Line, result: dict[str, Any], n: int, row: tuple[Decimal, ...]
) -> tuple[Decimal, ...]:
    """A bar's prices as the archive adjusts them for dividends and splits: all four scaled by
    the bar's adjusted close over its close. An answer with no adjusted close is refused."""
    try:
        adjusted = result["indicators"]["adjclose"][0]["adjclose"][n]
    except (KeyError, IndexError) as gone:
        raise ValueError(f"{line.symbol}: the archive gave no adjusted close") from gone
    return tuple(price * adjusted / row[3] for price in row)


def _read(line: Line, span: str, payload: bytes) -> tuple[dict[str, Any], list[Row]]:
    """The archive's answer for a line: what it says of the line, and its bars, each with the
    moment it starts, its prices in the line's currency and its volume. A moment it gives
    without a full bar has none."""
    chart = json.loads(payload, parse_float=Decimal, parse_constant=Decimal)["chart"]
    if chart["error"] is not None or not chart["result"]:
        raise ValueError(f"{line.symbol}: the archive gave no answer: {chart['error']}")
    result: dict[str, Any] = chart["result"][0]
    meta: dict[str, Any] = result["meta"]
    if meta["symbol"] != _name(line):
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
        prices: tuple[Decimal, ...] = (open_, high, low, close)
        if line.symbol.endswith(TAG):
            prices = _adjust(line, result, n, prices)
        o, h, lo, c = (price * unit for price in prices)
        rows.append((stamp, o, h, lo, c, volume))
    return meta, rows


def parse(line: Line, payload: bytes) -> tuple[Bar, ...]:
    """A line's daily bars from the archive's answer."""
    rows = _read(line, DAILY, payload)[1]
    return tuple(
        Bar((EPOCH + timedelta(seconds=row[0]) + MIDNIGHT).date(), *row[1:]) for row in rows
    )


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


def _record(refusing: bool) -> None:
    """Write when the archive began refusing (kept while it goes on), or null once it answers,
    to archive.json in the folder KESTREL2_DATA names, if it names one."""
    data = os.environ.get("KESTREL2_DATA")
    if not data:
        return
    path = Path(data) / STATE
    since = None
    if refusing:
        since = json.loads(path.read_text("utf-8")).get("refusing_since") if path.exists() else None
        since = since or datetime.now(UTC).isoformat()
    part = path.with_suffix(".part")
    part.write_text(json.dumps({"refusing_since": since}), "utf-8")
    part.replace(path)


def alert(data: Path, now: datetime) -> str | None:
    """The line to send the operator once the archive has refused for six hours (DAT-08), read
    from archive.json in data; None while it answers, or has refused for less."""
    path = data / STATE
    since = json.loads(path.read_text("utf-8"))["refusing_since"] if path.exists() else None
    if since is None or now - datetime.fromisoformat(since) < ALERT_AFTER:
        return None
    return f"the price archive has refused every ask since {since}"


def _once(address: str) -> bytes:
    request = Request(address, headers={"User-Agent": "Mozilla/5.0"})  # noqa: S310
    with urlopen(request, timeout=30) as answer:  # noqa: S310
        return bytes(answer.read())


def _turned_away(refusal: Exception) -> bool:
    """Whether an ask failed in a way a wait may mend: no answer, or a 429 or a server's fault."""
    if isinstance(refusal, HTTPError):
        return refusal.code == 429 or refusal.code >= 500
    return True


def _wait(refusal: Exception, wait: int) -> float:
    """How long to wait: the back-off, or longer if the archive said how long (Retry-After)."""
    said = refusal.headers.get("Retry-After", "") if isinstance(refusal, HTTPError) else ""
    return max(wait, min(int(said), ASKED_TO_WAIT)) if said.isdigit() else wait


def _ask(address: str) -> bytes:
    """One ask of the archive, slowly, backing off when it is turned away or does not answer.
    When the last wait is spent the refusal stands, and archive.json says since when."""
    waits = iter(BACKOFF)
    while True:
        time.sleep(PACE)
        try:
            payload = _once(address)
        except (OSError, HTTPException) as refusal:
            wait = next(waits, None)
            if wait is not None and _turned_away(refusal):
                time.sleep(_wait(refusal, wait))
                continue
            if _turned_away(refusal):
                _record(refusing=True)
            raise
        _record(refusing=False)
        return payload


def _kept(kept: Path | None, address: str, read: Callable[[bytes], Read]) -> Read:
    """The archive's answer at an address, read on entry. With a kept file, the raw answer is
    read from it instead of asked again, and written there only once read whole, never a
    refused one."""
    if kept is not None and kept.exists():
        return read(kept.read_bytes())
    payload = _ask(address)
    bars = read(payload)
    if kept is not None:
        kept.parent.mkdir(parents=True, exist_ok=True)
        part = kept.with_suffix(".part")
        part.write_bytes(payload)
        part.replace(kept)
    return bars


def fetch(
    line: Line, day: date, home: Path | None = None, *, since: date = SINCE
) -> tuple[Bar, ...]:
    """Every bar the archive holds for a line from since before day, read on entry. With a home, the
    archive's answer is kept raw there, one file to a line and day, and read instead of asked
    again; an answer is kept only once it has been read whole, never a refused one."""
    name = f"{line.symbol}{SUFFIX[line.venue]}" + ("" if since == SINCE else f"-{since}")
    data = os.environ.get("KESTREL2_DATA")
    home = home or (Path(data) if data else None)
    kept = None if home is None else home / STORE / str(day) / name
    return _kept(kept, address(line, day, since), lambda raw: parse(line, raw))


def fetch_five(
    line: Line, now: datetime, back: timedelta = KEPT, home: Path | None = None
) -> tuple[Five, ...]:
    """A line's five-minute bars up to now, read on entry: every one the archive still keeps,
    or those of a shorter time back. With a home, the raw answer is kept there (the archive
    forgets after sixty days), one file to a line and moment, and read instead of asked again."""
    name = f"{line.symbol}{SUFFIX[line.venue]}-{back.days}d"
    kept = None if home is None else home / STORE / "five" / now.strftime("%Y%m%dT%H%M") / name
    return _kept(kept, address_five(line, now, back), lambda raw: parse_five(line, raw, now))


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


def keep_reference(live: Path, line: Line, bars: Sequence[Bar]) -> tuple[store.Fault, ...]:
    """Clean a line's bars and keep them in the long database beside the live file at live, as
    traded: one bar a day, each sound alone. Those that cannot be true are left out and listed."""
    faults: list[store.Fault] = []
    weekdays = {bar.day for bar in bars if bar.day.weekday() < 5}
    sound = []
    for bar in store._once(bars, faults):  # noqa: SLF001  # the store's own cleaning, not copied
        entered = store._entered(line, bar, weekdays, faults)  # noqa: SLF001  # the store's own cleaning, not copied
        if isinstance(entered, str):
            faults.append(store.Fault(bar.day, entered))
        else:
            sound.append(entered)
    with writing(live) as round_:
        round_.daily(line, sound)
    return tuple(faults)
