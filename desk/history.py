"""history - THE ONE CLIENT FOR THE BROKER'S HISTORICAL BARS: a line's daily bars, asked of IB
Gateway's paper port through the desk's one door (desk/paper.py), read-only, as its own client
(CLIENT), the store's FIRST source (his ruling of 16 November 2026: IBKR, then the archive,
then the old Stooq downloads). It asks one line at a time and waits PACING seconds between
asks, inside IBKR's limit of 60 asks in ten minutes; it asks never inside a desk round. A line
the broker will not give is Refused, with the broker's own words, for the store to judge."""

from __future__ import annotations

import time
from collections.abc import Callable, Collection, Sequence
from datetime import date, datetime
from typing import BinaryIO

from desk import conformance, paper, venues
from desk.lines import Line
from desk.store import Answer, Bar, Refused

CLIENT = 225  #: the history reader's own client id at the gateway (never 222 or 223)
PACING = 11.0  #: seconds between asks: 60 asks in ten minutes is the broker's limit
ASK, BARS, NEWS, ID = 20, "17", "4", 9001
#: A bar's fields in the answer: its day, open, high, low, close, volume, the average and a count.
WIDTH = 8
#: The primary exchange the broker lists a London line under; a US line is routed by SMART.
PRIMARY = {"LSE": "LSEETF", "US": ""}
#: The timeframes the database keeps, each with the bar size IBKR names it by; the gateway serves
#: all of them, so none is rolled up from a lower one here.
SIZES = {
    "1m": "1 min", "2m": "2 mins", "5m": "5 mins", "10m": "10 mins", "15m": "15 mins",
    "30m": "30 mins", "1h": "1 hour", "4h": "4 hours", "1d": "1 day", "1wk": "1 week",
}  # fmt: skip


class Busy(Exception):
    """A desk round runs: the broker's history is not asked, and nothing was sent."""


Wait = Callable[[float], object]  #: what lets time pass between asks


def request(line: Line, day: date, since: date, timeframe: str = "1d") -> bytes:
    """The ask for a line's daily bars from since to the end of the day before day (every bar
    of a session still open, or not yet begun, is left out), of the trades, in the line's
    own currency, in the bars of the timeframe (daily unless said). A year or more is asked in
    whole years. A timeframe the database does not keep is a KeyError."""
    span = (day - since).days
    length = f"{span} D" if span <= 365 else f"{span // 365 + 1} Y"
    end = f"{day:%Y%m%d} 00:00:00 UTC"
    contract = (0, line.symbol, "STK", "", 0, "", "", "SMART", PRIMARY[line.venue], line.currency)
    return paper.message(
        ASK, ID, *contract, "", "", 0, end, SIZES[timeframe], length, 1, "TRADES", 1, 0, ""
    )


def _bars(fields: list[str], day: date, since: date) -> tuple[Bar, ...]:
    """The bars of an answer of the broker's, those from since and before day."""
    body = fields[5:]
    if len(fields) < 5 or not fields[4].isdigit() or len(body) != int(fields[4]) * WIDTH:
        raise ValueError(f"the broker's bars of a shape the desk does not read: {fields}")
    found = []
    for at in range(0, len(body), WIDTH):
        stamp, *given, volume = body[at : at + 6]
        taken = date(int(stamp[:4]), int(stamp[4:6]), int(stamp[6:8]))
        if since <= taken < day:
            o, h, low, c = (paper.number(p, fields) for p in given)
            found.append(Bar(taken, o, h, low, c, int(volume)))
    return tuple(found)


def ask(wire: BinaryIO, send: paper.Send, line: Line, day: date, since: date) -> Answer:
    """One line's daily bars over an open conversation, or the broker's words for refusing."""
    send(request(line, day, since))
    while True:
        fields = paper.receive(wire)
        if fields[0] == BARS and fields[1] == str(ID):
            return _bars(fields, day, since)
        if fields[0] == NEWS and fields[2] == str(ID):
            return Refused(f"the broker's {fields[3]}: {fields[4]}")
        paper.other(fields)  # news of the feeds is let by; any other stops the read


def quiet(now: datetime) -> bool:
    """Whether no desk round runs at the moment: the account is the desk's then."""
    at = venues.uk_time(now).time()
    return not any(start <= at < end for start, end in conformance.ROUNDS)


def gather(
    lines: Sequence[Line], day: date, since: date, now: datetime, wait: Wait = time.sleep
) -> dict[Line, Answer]:
    """Each line's daily bars before day, from since, the broker asked on one connection at
    PACING seconds apart. Not asked in a desk round: it raises Busy, and nothing is sent."""
    if not quiet(now):
        raise Busy("a desk round runs (08:00-08:30, 14:30-15:00 UK): history is not asked now")
    paper.CLIENT = CLIENT  #: this process is the history reader, at the door

    def talk(wire: BinaryIO, send: paper.Send) -> dict[Line, Answer]:
        paper.start(wire, send)
        answers: dict[Line, Answer] = {}
        for line in lines:
            if answers:
                wait(PACING)
            answers[line] = ask(wire, send, line, day, since)
        return answers

    return paper.dial(talk)


Ask = tuple[Line, str]  #: one line in one timeframe: the unit the pull plans, paces and resumes by


def plan(lines: Sequence[Line], done: Collection[Ask]) -> list[Ask]:
    """Every ask of every line in every timeframe the database keeps that is not yet done, in a
    fixed order, so a pull stopped anywhere takes up where it left off and fills only the gaps."""
    return [(line, frame) for line in lines for frame in SIZES if (line, frame) not in done]


def pull(
    asks: Sequence[Ask],
    fetch: Callable[[Line, str], Answer],
    keep: Callable[[Line, str, Answer], object],
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
