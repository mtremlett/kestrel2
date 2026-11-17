"""history - THE ONE CLIENT FOR THE BROKER'S HISTORICAL BARS: a line's daily bars, asked of IB
Gateway's paper port through the desk's one door (desk/paper.py), read-only, as its own client
(CLIENT), the store's FIRST source (his ruling of 16 November 2026: IBKR, then the archive,
then the old Stooq downloads). It asks one line at a time and waits PACING seconds between
asks, inside IBKR's limit of 60 asks in ten minutes; it asks never inside a desk round. A line
the broker will not give is Refused, with the broker's own words, for the store to judge."""

from __future__ import annotations

import os
import time
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import BinaryIO, TypeVar, cast

from desk import conformance_tape, listing, paper, venues
from desk.lines import LINES, POUND, Line
from desk.rollup import Candle
from desk.store import Answer, Bar, Refused

CLIENT = 225  #: the history reader's own client id at the gateway (never 222 or 223)
PACING = 11.0  #: seconds between asks: 60 asks in ten minutes is the broker's limit
ASK, BARS, NEWS, ID = 20, "17", "4", 9001
#: A bar's fields in the answer: its day, open, high, low, close, volume, the average and a count.
WIDTH = 8
#: The primary exchange the broker lists a London line under; a US line is routed by SMART.
PRIMARY = {"LSE": "LSEETF", "US": ""}
#: The pound in dollars is asked as a forex pair (GBP.USD at IDEALPRO), of the midpoint: it has no
#: trades, and the broker gives its bars no volume (-1), kept as none.
CASH = (0, "GBP", "CASH", "", 0, "", "", "IDEALPRO", "", "USD")
#: The timeframes the database keeps, each with the bar size IBKR names it by; the gateway serves
#: all of them, so none is rolled up from a lower one here.
SIZES = {
    "1m": "1 min", "2m": "2 mins", "5m": "5 mins", "10m": "10 mins", "15m": "15 mins",
    "30m": "30 mins", "1h": "1 hour", "4h": "4 hours", "1d": "1 day", "1wk": "1 week",
}  # fmt: skip
#: The timeframes a pull asks the broker for. Its 1 hour, 4 hour and weekly bars start on the
#: venue's session (a US hour at :30 UTC), off the store's marks, which the writer refuses; they are
#: rolled up locally from the lower timeframes pulled (his ruling of 16 November), not asked.
PULLED = tuple(frame for frame in SIZES if frame not in ("1h", "4h", "1wk"))
#: Days back one ask goes, per timeframe: the longest span IBKR gives in one ask for its bar size
#: (1 min: a day; 2 mins: 2; 5 to 15 mins: a week; 30 mins to 4 hours: a month; daily: a year).
REACH = {
    "1m": 1, "2m": 2, "5m": 7, "10m": 7, "15m": 7,
    "30m": 30, "1h": 30, "4h": 30, "1d": 365, "1wk": 365,
}  # fmt: skip
#: Pages one pull walks back, each REACH days before the one after it, stopping at the first the
#: broker gives nothing for or refuses: IBKR's deepest history per bar size (1 min: a month;
#: 2 to 15 mins: half a year; 30 mins to 4 hours: two years; daily and weekly: twenty years).
PAGES = {
    "1m": 30, "2m": 90, "5m": 26, "10m": 26, "15m": 26,
    "30m": 25, "1h": 25, "4h": 25, "1d": 20, "1wk": 20,
}  # fmt: skip

#: What an ask gives: a day's bars for the daily and weekly, candles (with their time) for the rest.
Got = Answer | tuple[Candle, ...]
DAILY = ("1d", "1wk")
B = TypeVar("B", Bar, Candle)  #: a bar of either kind


class Busy(Exception):
    """A desk round runs: the broker's history is not asked, and nothing was sent."""


Wait = Callable[[float], object]  #: what lets time pass between asks


def request(line: Line, day: date, since: date, timeframe: str = "1d") -> bytes:
    """The ask for a line's daily bars from since to the end of the day before day (every bar
    of a session still open, or not yet begun, is left out), of the trades (the pound's: a
    forex pair's midpoint), in the line's own currency, in the bars of the
    timeframe (daily unless said), their times as epoch seconds for an intraday one. A year or
    more is asked in whole years. A timeframe the database does not keep is a KeyError."""
    span = (day - since).days
    length = f"{span} D" if span <= 365 else f"{span // 365 + 1} Y"
    end = f"{day:%Y%m%d} 00:00:00 UTC"
    contract = (0, line.symbol, "STK", "", 0, "", "", "SMART", PRIMARY[line.venue], line.currency)
    if line == POUND:
        contract = CASH
    return paper.message(
        ASK,
        ID,
        *contract,
        "",
        "",
        0,
        end,
        SIZES[timeframe],
        length,
        1,
        "MIDPOINT" if line == POUND else "TRADES",
        1 if timeframe in DAILY else 2,
        0,
        "",
    )


def _bars(fields: list[str], day: date, since: date) -> tuple[Bar, ...]:
    """The bars of an answer of the broker's, those from since and before day."""
    body = fields[5:]
    if len(fields) < 5 or not fields[4].isdigit() or len(body) != int(fields[4]) * WIDTH:
        raise ValueError(f"the broker's bars of a shape the desk does not read: {fields}")
    found = []
    for at in range(0, len(body), WIDTH):
        stamp, *given, volume = body[at : at + 6]
        if len(stamp) != len("20261112"):
            raise NotImplementedError(
                f"a bar that carries its time ({stamp}): Bar holds a day only"
            )
        taken = date(int(stamp[:4]), int(stamp[4:6]), int(stamp[6:8]))
        if since <= taken < day:
            o, h, low, c = (paper.number(p, fields) for p in given)
            found.append(Bar(taken, o, h, low, c, max(int(volume), 0)))
    return tuple(found)


def _candles(fields: list[str], day: date, since: date) -> tuple[Candle, ...]:
    """The candles of an intraday answer, each time in epoch seconds, from since and before day;
    each is named for its source, ibkr."""
    body = fields[5:]
    if len(fields) < 5 or not fields[4].isdigit() or len(body) != int(fields[4]) * WIDTH:
        raise ValueError(f"the broker's bars of a shape the desk does not read: {fields}")
    found = []
    for at in range(0, len(body), WIDTH):
        stamp, *given, volume = body[at : at + 6]
        if not stamp.isdigit():
            raise ValueError(f"a bar time that is no epoch seconds ({stamp}): {fields}")
        start = datetime.fromtimestamp(int(stamp), UTC)
        if since <= start.date() < day:
            o, h, low, c = (paper.number(p, fields) for p in given)
            found.append(Candle(start, o, h, low, c, max(int(volume), 0), "ibkr"))
    return tuple(found)


def ask(
    wire: BinaryIO, send: paper.Send, line: Line, day: date, since: date, timeframe: str = "1d"
) -> Got:
    """One line's bars of a timeframe (daily unless said) over an open conversation, or the
    broker's words for refusing."""
    send(request(line, day, since, timeframe))
    while True:
        fields = paper.receive(wire)
        if fields[0] == BARS and fields[1] == str(ID):
            return (_bars if timeframe in DAILY else _candles)(fields, day, since)
        if fields[0] == NEWS and fields[2] == str(ID):
            return Refused(f"the broker's {fields[3]}: {fields[4]}")
        paper.other(fields)  # news of the feeds is let by; any other stops the read


def quiet(now: datetime) -> bool:
    """Whether no desk round runs at the moment: the account is the desk's then."""
    at = venues.uk_time(now).time()
    return not any(start <= at < end for start, end in conformance_tape.ROUNDS)


def gather(
    lines: Sequence[Line], day: date, since: date, now: datetime, wait: Wait = time.sleep
) -> dict[Line, Answer]:
    """Each line's daily bars before day, from since, the broker asked on one connection at
    PACING seconds apart. Not asked in a desk round: it raises Busy, and nothing is sent."""
    if not quiet(now):
        raise Busy("a desk round runs (08:00-08:30, 14:30-15:00 UK): history is not asked now")
    door = paper.Door(CLIENT)  #: the history reader's own door, passed down

    def talk(wire: BinaryIO, send: paper.Send) -> dict[Line, Answer]:
        paper.start(wire, send, door)
        answers: dict[Line, Answer] = {}
        for line in lines:
            if answers:
                wait(PACING)
            answers[line] = cast(Answer, ask(wire, send, line, day, since))  # daily asks give bars
        return answers

    return paper.dial(talk)


#: The most lines one call asks the broker for: at PACING, inside the keeper's four minutes.
MOST = 12


def lacks(line: Line, answer: Answer, day: date) -> bool:
    """The archive gave nothing for a line, or lacks its venue's last session before day."""
    last = venues.sessions(line.venue, day - timedelta(14), day - timedelta(1))[-1]
    return isinstance(answer, Refused) or not answer or answer[-1].day < last


RECENT = timedelta(days=30)  #: how far back the broker's daily bars are asked to join the archive's


def scaled(one: B, magnifier: int) -> B:
    """One bar of the broker's, its prices turned from its unit (100 is pence) into the line's
    currency."""
    unit = Decimal(magnifier)
    return replace(
        one, open=one.open / unit, high=one.high / unit, low=one.low / unit, close=one.close / unit
    )


def in_currency(answer: Answer, magnifier: int) -> Answer:
    """THE ONE HOME OF THE UNIT RULE: the broker's bars with their prices turned from its unit
    into the line's currency, once, on entry (`scaled`); a refusal is passed on."""
    if isinstance(answer, Refused):
        return answer
    return [scaled(b, magnifier) for b in answer]


def priced(
    home: Path, now: datetime, answers: Mapping[Line, Answer], door: paper.Door
) -> dict[Line, Answer]:
    """Each line's answer in the line's currency, by the unit the broker lists the line in today;
    a line the broker does not list is Refused, in its words."""
    listed = listing.kept(home, now, LINES, door)
    out: dict[Line, Answer] = {}
    for line, answer in answers.items():
        one = listed.get(line.symbol)
        if one is None:
            out[line] = Refused(f"{line.symbol}: not a line of the desk, its unit is unknown")
            continue
        out[line] = (
            Refused(one.reason)
            if isinstance(one, listing.Unlisted)
            else in_currency(answer, one.magnifier)
        )
    return out


def daily(
    now: datetime, wait: Wait = time.sleep, home: Path | None = None
) -> Callable[[Sequence[Line], date], dict[Line, Answer]]:
    """THE KEEPER'S BROKER: the daily bars before a day of the lines (at most MOST) the archive
    lacks, over one conversation, in each line's currency (the desk's root: home, else
    KESTREL2_DATA). A broker that cannot be asked (a desk round, no gateway) gives
    each line a Refused in words, so the line is judged on the archive alone and, if that too
    lacks it, is parked and named."""

    def ask_all(lines: Sequence[Line], day: date) -> dict[Line, Answer]:
        try:
            got = gather(lines[:MOST], day, day - RECENT, now, wait)
            root = home or Path(os.environ["KESTREL2_DATA"])
            return priced(root, now, got, paper.Door(CLIENT))
        except (Busy, OSError) as err:
            return {line: Refused(f"the broker was not asked: {err}") for line in lines}

    return ask_all


Ask = tuple[Line, str]  #: one line in one timeframe: the unit the pull plans, paces and resumes by


def plan(lines: Sequence[Line], done: Collection[Ask]) -> list[Ask]:
    """Every ask of every line in every timeframe the database keeps that is not yet done, in a
    fixed order, so a pull stopped anywhere takes up where it left off and fills only the gaps."""
    return [(line, frame) for line in lines for frame in PULLED if (line, frame) not in done]


def pull(
    asks: Sequence[Ask],
    fetch: Callable[[Line, str], Got],
    keep: Callable[[Line, str, Got], object],
    wait: Wait = time.sleep,
    limit: int | None = None,
) -> int:
    """Make the asks one at a time, PACING seconds apart (so never over the broker's limit), each
    answer given to keep as it comes (the caller notes it done), stopping after limit asks.
    Returns how many were made; the asks not made are what plan gives again."""
    made = 0
    for line, frame in asks:
        if made == limit:
            break
        if made:
            wait(PACING)
        keep(line, frame, fetch(line, frame))
        made += 1
    return made


def back(wire: BinaryIO, send: paper.Send, line: Line, frame: str, day: date, wait: Wait) -> Got:
    """One line's bars of a timeframe as far back as the broker gives: PAGES pages of REACH days,
    each before the last, PACING apart. The first page refused is the answer; a later page
    refused or empty ends the walk, the pages already had kept."""
    found: list[Bar | Candle] = []
    for page in range(PAGES[frame]):
        end = day - timedelta(REACH[frame] * page)
        if page:
            wait(PACING)
        got = ask(wire, send, line, end, end - timedelta(REACH[frame]), frame)
        if not isinstance(got, tuple) and not found:
            return got
        if not isinstance(got, tuple) or not got:
            break
        found.extend(got)
    return cast(Got, tuple(found))


def run(
    asks: Sequence[Ask],
    keep: Callable[[Line, str, Got], object],
    day: date,
    now: datetime,
    wait: Wait = time.sleep,
    limit: int | None = None,
) -> int:
    """The pull over the broker's own conversation, as the history reader, paced, each ask going
    back as far as the broker gives (PAGES); not in a desk round (Busy, nothing sent). Returns
    how many asks were made."""
    if not quiet(now):
        raise Busy("a desk round runs (08:00-08:30, 14:30-15:00 UK): history is not asked now")
    door = paper.Door(CLIENT)

    def talk(wire: BinaryIO, send: paper.Send) -> int:
        paper.start(wire, send, door)

        def fetch(line: Line, frame: str) -> Got:
            return back(wire, send, line, frame, day, wait)

        return pull(asks, fetch, keep, wait, limit)

    return paper.dial(talk)
