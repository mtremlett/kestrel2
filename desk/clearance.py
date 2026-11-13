"""clearance - THE DAY'S CHECK, AND NO ORDER WITHOUT IT. Every day, and before any order, the
paper account is read through the one door (desk/paper.py) and set against the desk's book:
what it holds, and every order resting on it. The desk's own stops are told from anyone
else's orders (desk/reports.py): each line held must be under a stop of the desk's own for
exactly the shares held, and nothing else may rest there. Every difference is named in
words. Only questions are sent.

Each check goes on the desk's record, dated: first that it was begun, then what it found.
`require` is asked by whoever would send an order, at the last moment, and refuses unless
the newest check on the record was begun today, came back, and named nothing. So a check
whose reading stopped, a desk that died in one, a later check that named something and a
record that cannot be read whole each refuse: none of them is a clean day. The day is the
UTC date, inside which London's session and New York's each fall whole."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from pathlib import Path

from desk import book, listing, paper, reports
from desk.lines import LINES, Line
from desk.listing import Listing, Unlisted
from desk.orders import Refused
from desk.paper import Account, Resting

CHECKS = "checks.csv"
COLUMNS = ("at", "result", "found")
BEGUN, CLEAN, DIFFERS = "begun", "clean", "differs"  #: a check's result, as the record words it


def _utc(moment: datetime) -> datetime:
    if moment.utcoffset() != timedelta(0):
        raise ValueError(f"{moment} is no moment in UTC: the day's check is dated in UTC alone")
    return moment


@dataclass(frozen=True)
class Check:
    """One run of the day's check, as the record keeps it."""

    at: datetime  #: when it was begun, in UTC
    #: Every difference it named; none, and the account is the desk's book. None while it
    #: has not come back: its reading stopped, or the desk died in it.
    found: tuple[str, ...] | None

    def __post_init__(self) -> None:
        _utc(self.at)

    def row(self) -> tuple[str, ...]:
        """As the record keeps it: the moment, the result in a word, each difference."""
        result = BEGUN if self.found is None else DIFFERS if self.found else CLEAN
        return (self.at.isoformat(), result, *(self.found or ()))


def differences(
    account: Account,
    listings: Mapping[str, Listing | Unlisted],
    held: Mapping[str, int],
    lines: Iterable[Line],
) -> tuple[str, ...]:
    """Every way the paper account is not the desk's book, each named in words; none, and
    nothing but the desk trades the account and each line held is under the desk's own stop.
    held is the book (book.positions); listings, each line as the broker lists it now.
    First the holdings (paper.differences). Then the desk's own resting stops, by the same
    one rule (book.differences): a line's stop is for exactly the shares the book holds, so
    a line held under none, a stop for other shares and a line under two are each named.
    Then every other order: the desk's own that is no stop the broker is holding, and
    anyone else's, which protects nothing of the desk's."""
    holdings = paper.differences(account, held, lines)
    told = reports.orders(account.orders, listings)
    stops = paper.named(held, told.stops, "the desk's own stop resting at the broker is for")
    idle = (_order(o, "the desk's own, and no stop the broker is holding") for o in told.unsettled)
    return (*holdings, *stops, *idle, *(_order(o, "not the desk's own") for o in told.others))


def _order(order: Resting, whose: str) -> str:
    return (
        f"{order.symbol}: an order resting at the broker to {order.action} {order.shares} "
        f"({order.kind}, {order.state}, the broker's id {order.broker_id}, "
        f"client {order.client}), {whose}"
    )


def checks(root: Path) -> tuple[Check, ...]:
    """The record of the day's checks, oldest first. No record is a desk never checked; one
    that is there and is not, row for row, as the desk writes it is an error, never a clean
    day."""
    path = root / CHECKS
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8") as record:
        rows = list(csv.reader(record))
    if rows[:1] != [list(COLUMNS)]:
        raise ValueError(f"{path}: not the record of the day's checks, so nothing is sent")
    return tuple(_check(path, row) for row in rows[1:])


def _check(path: Path, row: list[str]) -> Check:
    """A row of the record: a check exactly as the desk writes one, or an error."""
    found = None if row[1:] == [BEGUN] else tuple(row[2:])
    try:
        check = Check(datetime.fromisoformat("".join(row[:1])), found)
    except ValueError as fault:
        raise ValueError(f"{path}: {row} is no check of the desk's: {fault}") from fault
    if list(check.row()) != row:
        raise ValueError(f"{path}: {row} is no check of the desk's, so nothing is sent")
    return check


def check(root: Path, now: datetime) -> Check:
    """THE DAY'S CHECK, run every day and before any order: each of the desk's lines as the
    broker lists it now, then the account, read through the one door and set against the
    desk's book, whose ledger whoever runs the day has brought up to date first. The check
    is on the record as begun before anything is asked, and as what it found once it comes
    back; a reading that stops is raised, and leaves it begun."""
    before = checks(root)
    begun = Check(now, None)
    if before and before[-1].at > now:
        raise ValueError(f"a check at {now} would come before the record's last, {before[-1].at}")
    _keep(root, (*before, begun))
    listings = listing.read(LINES)
    found = differences(paper.read(), listings, book.positions(root), LINES)
    done = replace(begun, found=found)
    _keep(root, (*before, done))
    return done


def _keep(root: Path, record: Iterable[Check]) -> None:
    book._write(root / CHECKS, [COLUMNS, *(check.row() for check in record)])


def require(root: Path, now: datetime, order_id: str) -> None:
    """Asked at the last moment before an order goes to the paper broker: Refused, in the
    check's own words, unless the newest check on the record was begun today (now's date,
    in UTC), came back, and named nothing."""
    today, record = _utc(now).date(), checks(root)
    last = record[-1] if record else None
    if last is None or last.at.date() != today:
        why = f"the paper account has not been checked today, {today}"
    elif last.found is None:
        why = f"the check begun at {last.at:%H:%M} UTC today has not come back"
    elif last.found:
        why = f"the check at {last.at:%H:%M} UTC today named: {'; '.join(last.found)}"
    else:
        return
    raise Refused(f"{order_id}: not sent, {why}")
