"""running - THE DESK UNATTENDED, AND RECOVERED AFTER A RESTART. One step (`step`) does
whatever the desk owes at the moment it is given, each thing once; whoever keeps the desk
alive asks for a step every few minutes, one at a time and never two together (the
supervisor: not built, docs/STATUS.md). A step remembers nothing. What is done is on the
desk's records, and what is not is done by the next step: so a desk that died anywhere is
started again simply by asking for a step.

What a step owes, in this order, and only of a gateway that says it is ready:
- THE LEDGER brought up to date with the broker's fills, at every step in which a market is
  open: the broker tells of the day alone.
- THE DAY'S CHECK (clearance.check), from the hour he wakes, and again before each round of
  orders. When it names anything, what a dead desk left at the broker is first put right
  (`recover`) and the account checked again. Still not clean, no order goes and he is told.
- THE DAY'S ORDERS, one round for each venue, while it trades: the money path's own day
  (day.trade), on the bars saved before today, for that venue's lines. The send path asks
  the broker of every order before it sends, so a round begun twice sends nothing twice.
- THE DAY'S RECORD (day.publish), once every market that traded has been shut five minutes;
  a session the desk missed gets its own first, oldest first, at that day's own rates.

Then, whatever happened, he is told through the desk's one voice (desk/messenger.py): the
morning and the evening message, a gateway that is his to look at, his weekly login, and,
in his waking hours, each thing on the record of what the desk did (`notes`): a round, a
recovery, an account that is not the book, a step that failed. A step that fails is still an
error raised to whoever asked for it: the next step tries again, and he is told of the
day's first only."""

from __future__ import annotations

import csv
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import NamedTuple

from desk import (
    book,
    clearance,
    day,
    gateway,
    kill,
    listing,
    messenger,
    paper,
    placing,
    venues,
)
from desk.gateway import Known, State
from desk.lines import LINES, Line
from desk.listing import Listing, Unlisted
from desk.orders import Settings
from desk.reports import HELD
from desk.store import Bar

NOTES, HEAD = "running.csv", ("at", "what", "words")
VENUES = {"LSE": "London", "US": "New York"}  #: each venue of the desk's lines, as he is told it
SHUT = timedelta(minutes=5)  #: how long after a day's last closing auction its record is made
DAY = timedelta(days=1)
ORDERS, RECOVERED, UNCLEAN, TROUBLE = "orders {}", "recovered", "unclean", "trouble"
ONCE = (UNCLEAN, TROUBLE)  #: told once a day, the first, however often they happen in it
PUT_RIGHT = "The desk put right what a desk that stopped part-way left at the paper broker: {}."
NOT_THE_BOOK = "The paper account is not the desk's book, so no order goes. Its check named: {}."
FAILED = "A step of the desk failed; the next tries again: {}: {}. Later ones today are not told."
UNASKED = Known(State.UNWELL, gateway.UNWELL.format("the desk's knock on it failed"))
#: The bars the store kept before a day, for every line, and the symbols it has parked.
Saved = tuple[Mapping[Line, Sequence[Bar]], Collection[str]]


@dataclass(frozen=True)
class Desk:
    """All a step is given beside the moment: the desk's records, and its doors out."""

    root: Path  #: where the ledger, the checks, the switch, the records and the messages are
    room: Settings
    post: messenger.Post  #: the door to his phone
    bars: Callable[[date], Saved]  #: the price store's door, asked for the bars before a day
    #: A day's pounds per unit of each currency: the same answer at every asking.
    rates: Callable[[date], Mapping[str, Decimal]]


class Note(NamedTuple):
    """One thing the desk did unattended, as its record keeps it and as he is told it."""

    at: datetime
    what: str
    words: str


def notes(root: Path) -> tuple[Note, ...]:
    """What the desk did unattended, oldest first. A file there that is not this record is
    an error, never a day on which nothing was done."""
    path = root / NOTES
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8") as kept:
        rows = list(csv.reader(kept))
    if rows[:1] != [list(HEAD)]:
        raise ValueError(f"{path}: not the record of what the desk did, so nothing is done")
    return tuple(Note(datetime.fromisoformat(at), what, words) for at, what, words in rows[1:])


def _note(root: Path, now: datetime, what: str, words: str) -> None:
    """Keep one thing done; of those told once a day (ONCE), the day's first alone."""
    kept = notes(root)
    if what in ONCE and any(n.what == what and n.at.date() == now.date() for n in kept):
        return
    rows = ((n.at.isoformat(), n.what, n.words) for n in (*kept, Note(now, what, words)))
    book._write(root / NOTES, [HEAD, *rows])


def recover(
    root: Path, broker: placing.Paper, listings: Mapping[str, Listing | Unlisted], today: date
) -> tuple[str, ...]:
    """AFTER A RESTART: what a desk that died part-way through an order left at the broker,
    put right by the order's own rules (desk/placing.py), each thing done named. Every order
    of the desk's own still working is cancelled: what `place` did not see filled is never
    left working. The ledger takes the fills the broker made meanwhile. Then each line with
    a stop of the desk's own open on it, if its shares at the broker are the book's, is left
    under the one stop due (_due, Paper.settle). A line whose shares are not the book's is
    left as it is, for the day's check to name. Nothing is done while the kill switch is on,
    or undrilled: the desk sends nothing then."""
    if book.killed(root) or not kill.drilled(root, today):
        return ()
    did = [f"cancelled {name}, left working" for name in broker.cancel()]
    book.collect(root, broker)
    held, account = book.positions(root), paper.read()
    bought = {fill.order_id for fill in book.fills(root) if fill.quantity > 0}
    for listed in listings.values():
        if isinstance(listed, Listing):
            shares, stops = placing.on(account, listed)
            mine = stops and shares == held.get(listed.line.symbol, 0)
            for due in _due(shares, stops, bought) if mine else ():
                broker.settle(listed, shares, stops, due)
                under = f"one stop for {shares} shares" if due else "no stop, none of it held"
                did.append(f"{listed.line.symbol} left under {under}")
    return tuple(did)


def _due(
    shares: Decimal, stops: Sequence[paper.Resting], bought: Collection[str]
) -> tuple[placing.Stop | None, ...]:
    """The one stop a line found after a restart is to be left under, or None for none; and
    nothing at all for a line to be left as it is. The stop is for the shares held, at the
    level and under the name of the newest of the line's stops whose buy the ledger holds a
    fill of: a stop that came with a buy that bought nothing gives no level, as after any
    order (placing._due). No share held, and no stop is due: one left resting could sell
    short. Left as it is: a line already under one stop the broker holds for exactly its
    shares, and a line held with no stop to take a level from."""
    if [(o.left, o.state in HELD) for o in stops] == [(shares, True)]:
        return ()
    levels = [
        (int(o.number), placing.Stop(shares, o.level, o.ref))
        for o in stops
        if o.level is not None and o.ref.removesuffix("-stop") in bought
    ]
    return (max(levels)[1],) if shares and levels else () if shares else (None,)


def _clean(
    desk: Desk, broker: placing.Paper, listings: Mapping[str, Listing | Unlisted], now: datetime
) -> bool:
    """The day's check, run now: whether the paper account is the desk's book. When it names
    anything, what a dead desk left is put right (recover) and, if anything was, the account
    is checked again. What a check still names he is told, and no order goes."""
    found = clearance.check(desk.root, now).found
    if found and (did := recover(desk.root, broker, listings, now.date())):
        _note(desk.root, now, RECOVERED, PUT_RIGHT.format("; ".join(did)))
        found = clearance.check(desk.root, now).found
    if found:
        _note(desk.root, now, UNCLEAN, NOT_THE_BOOK.format("; ".join(found)))
    return not found


def _pending(root: Path, now: datetime) -> list[str]:
    """The venues whose round of orders is owed now: in continuous trading, with no round of
    today's on the record."""
    done = {note.what for note in notes(root) if note.at.date() == now.date()}
    trading = {venue: venues.open_at(venue, now) for venue in VENUES}
    return [
        venue
        for venue, hours in trading.items()
        if hours and now < hours.close and ORDERS.format(venue) not in done
    ]


def _round(desk: Desk, broker: placing.Paper, venue: str, now: datetime) -> None:
    """A venue's orders for today, by the money path's own day, on the bars saved before
    today for the venue's lines the store has not parked; then the round goes on the record
    with the answer to each order. A desk that dies in it runs it again: the send path asks
    the broker of each order first."""
    today = now.date()
    bars, parked = desk.bars(today)
    saved = {
        line: series
        for line, series in bars.items()
        if line.venue == venue and line.symbol not in parked
    }
    sent = day.trade(desk.root, saved, broker, desk.room, today, desk.rates(today))
    said = [
        f"{s.order_id}, {s.filled} shares done" + f" ({s.reason})" * bool(s.reason) for s in sent
    ]
    words = f"{VENUES[venue]}, today's orders: {'; '.join(said) or 'none was due'}."
    _note(desk.root, now, ORDERS.format(venue), words)


def _owed(root: Path, now: datetime) -> list[date]:
    """The sessions whose record is owed now, oldest first: each since the last record (with
    none yet, since the ledger's first fill, or today), and today's only once every venue
    that traded today has been shut for SHUT."""
    kept, today = day.records(root), now.date()
    first = min((fill.day for fill in book.fills(root)), default=today)
    since = kept[-1].day if kept else min(first, today) - DAY
    traded = {on for venue in VENUES for on in venues.sessions(venue, since + DAY, today)}
    shut = all(
        now >= venues.hours(venue, today).auction + SHUT
        for venue in VENUES
        if venues.sessions(venue, today, today)
    )
    return [on for on in sorted(traded) if on < today or shut]


def _work(desk: Desk, now: datetime) -> None:
    """What a step owes of a ready gateway, in the module's order. The paper account is
    asked only when something is owed: a market open, a check, a record."""
    root = desk.root
    rounds, owed, last = _pending(root, now), _owed(root, now), clearance.checks(root)[-1:]
    checked = bool(last) and last[0].at.date() == now.date() and last[0].found is not None
    check = bool(rounds) or (gateway._uk(now).time() >= messenger.MORNING.start and not checked)
    if not (check or owed or any(venues.open_at(venue, now) for venue in VENUES)):
        return
    listings = listing.read(LINES)
    broker = placing.Paper(listings, root, lambda: now)
    book.collect(root, broker)
    if check and not _clean(desk, broker, listings, now):
        rounds = []
    for venue in rounds:
        _round(desk, broker, venue, now)
    for on in owed:  #: a missed session's rates are kept first, as its own day would have
        book.record_rates(root, on, desk.rates(on))
        day.publish(root, desk.bars(on + DAY)[0], broker, desk.room, on)


def _say(desk: Desk, now: datetime, known: Known) -> None:
    """Everything he is owed at a moment, each under its own name and so once: his line of
    a gateway that is his to look at, a day's; the morning message; each thing the desk did
    in the last day (notes), kept for his waking hours as the daily messages are; the
    evening message; his weekly login's reminder."""
    root, post = desk.root, desk.post
    if known.state is State.HIS:
        messenger.send(root, now, f"gateway {now:%Y-%m-%d}", known.words, post)
    messenger.morning(root, now, known, post)
    awake = messenger.MORNING.start <= gateway._uk(now).time() < messenger.SLEEPS
    for note in notes(root):
        if awake and now - note.at < DAY:
            messenger.send(root, now, f"{note.what} {note.at:%Y-%m-%d %H:%M}", note.words, post)
    messenger.evening(root, now, known, post)
    messenger.remind(root, now, post)


def step(desk: Desk, now: datetime) -> None:
    """ONE STEP OF THE DESK UNATTENDED, at a moment in UTC: the gateway is asked whether it
    is ready, and of one that is, whatever is owed is done (_work). A step that fails goes
    on the record, the day's first, and the error is raised all the same. Done or failed,
    he is then told everything he is owed (_say), a gateway whose asking failed told as one
    that did not say it is ready."""
    if now.utcoffset() != timedelta(0):
        raise ValueError(f"{now} is no moment in UTC: the desk's day is kept in UTC alone")
    known = UNASKED
    try:
        known = gateway.known(now)
        if known:
            _work(desk, now)
    except Exception as fault:
        _note(desk.root, now, TROUBLE, FAILED.format(type(fault).__name__, fault))
        raise
    finally:
        _say(desk, now, known)
