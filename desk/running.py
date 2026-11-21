"""running - THE DESK UNATTENDED, AND RECOVERED AFTER A RESTART. One step (`step`) does
whatever the desk owes at the moment it is given, each thing once; whoever keeps the desk
alive asks for a step every few minutes, one at a time. A step remembers nothing: what is
done is on the desk's records, what is not is done by the next step, so a desk that died
anywhere is started again simply by asking for a step.

THE CRASH WATCH'S LOOK (watch.look) is made first at every step, whatever the gateway says:
it halts buying on a crash, and till it has read a venue's first bar it holds that venue's
round. A look that fails holds every round; the rest is done, and the failure raised after.

What a step owes, in this order, and only of a gateway that says it is ready:
- THE LEDGER brought up to date with the broker's fills, at every step in which a market is
  open: the broker tells of the day alone.
- THE KILL SWITCH'S DRILL (`_drill`), once each day (UTC), at its first step with anything
  below to do: no order goes on a day the switch was not seen to work. A drill that broke a
  promise is a step that failed: nothing below is done, and the next step drills again.
- THE DAY'S CHECK (clearance.check), from the hour he wakes, and again before each round and
  each record. When it names anything, what a dead desk left at the broker is first put
  right (`recover`) and the account checked again. Still not clean, no order goes, he is told.
- THE DAY'S ORDERS, one round for each venue, while it trades: the money path's own day
  (day.trade), on the bars saved before today, for that venue's lines. The send path asks
  the broker of every order first, so a round begun twice sends nothing twice. A round is
  made once, whatever was answered: an order refused in it is not sent later.
- THE INTRADAY ROUNDS (`_intraday`), after the day's own: each intraday rule of the desk's at
  each whole bar of its span, through the same check, gate, stops and records (none trade yet).
- THE DAY'S RECORD (day.publish), once every market that traded has its closes kept
  (keeper.HELD); a session the desk missed gets its own first, oldest first.

Then, whatever happened, he is told through the desk's one voice (desk/messenger.py): the
morning and evening messages, a gateway that is his to look at, his weekly login and, in his
waking hours, each thing on the record (`notes`). A step that fails is still an error raised
to whoever asked for it: the next step tries again, and he is told of the day's first only."""

from __future__ import annotations

import csv
import sys
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import NamedTuple

from desk import (
    book,
    clearance,
    day,
    gateway,
    goflat,
    intraday,
    keeper,
    kill,
    listing,
    messenger,
    paper,
    placing,
    restop,
    venues,
    watch,
)
from desk.book import Switch
from desk.gateway import Known, State
from desk.lines import LINES, YARDSTICK, Line
from desk.listing import Listing, Unlisted
from desk.messenger_parts import Mail
from desk.orders import Order, Refused, Sale, Settings, size, strategy_of
from desk.rollup import Candle
from desk.running_parts import PUT_RIGHT
from desk.running_parts import recover as recover
from desk.store import Bar
from desk.strategy import Action, Decision

NOTES, HEAD = "running.csv", ("at", "what", "words")
VENUES = {"LSE": "London", "US": "New York"}  #: each venue of the desk's lines, as he is told it
DAY = timedelta(days=1)
ORDERS, RECOVERED, UNCLEAN, TROUBLE = "orders {}", "recovered", "unclean", "trouble"
ONCE = (UNCLEAN, TROUBLE)  #: told once a day, the first: of a failure, the first of its kind
NOT_THE_BOOK = "The paper account is not the desk's book, so no order goes. Its check named: {}."
FAILED = (
    "A step of the desk failed; the next tries again: {}: {} (in {}). Its like today is not told."
)
UNDRILLED = (
    "today's rehearsal of the kill switch did not pass, so the desk sends no order, checks no "
    "account and makes no record until one does. It was a rehearsal on a pretend desk: no real "
    "order was involved. Each promise named next was NOT kept: {}"
)
UNASKED = Known(State.UNWELL, gateway.UNWELL.format("the desk's knock on it failed"))
Rules = Mapping[str, Callable[[], intraday.IntradayRule]]
Saved = tuple[Mapping[Line, Sequence[Bar]], Collection[str]]  #: bars by line; who is parked


@dataclass(frozen=True)
class Desk:
    """All a step is given beside the moment: the desk's records, and its doors out."""

    root: Path  #: where the ledger, the checks, the switch, the records and the messages are
    room: Settings
    post: messenger.Post  #: the door to his phone
    #: A day's pounds per unit of each currency: the same answer at every asking.
    rates: Callable[[date], Mapping[str, Decimal]]
    #: The fast store of five-minute bars for the crash watch, and the one door to the daily
    #: bars, as last kept by the store's keeper (no archive is asked at a step).
    hot: Path
    held: Callable[[date], Saved]
    door: paper.Door  #: who the desk is at the paper Gateway
    mail: Mail | None = None  #: the email door, if his SMTP_ settings are set
    #: The intraday rules the desk may trade, as `intraday.RULES`: none until one passes the ladder.
    rules: Rules = field(default_factory=lambda: intraday.RULES)


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
    """Keep one thing done; of those told once a day (ONCE), the first alone."""
    kept = notes(root)
    if what.split()[0] in ONCE and any((n.what, n.at.date()) == (what, now.date()) for n in kept):
        return
    rows = ((n.at.isoformat(), n.what, n.words) for n in (*kept, Note(now, what, words)))
    book._write(root / NOTES, [HEAD, *rows])


def _clean(
    desk: Desk, broker: placing.Paper, listings: Mapping[str, Listing | Unlisted], now: datetime
) -> bool:
    """The day's check, run now: whether the paper account is the desk's book. When it names
    anything, what a dead desk left is put right (recover) and the account checked again.
    What it still names he is told, and no order goes."""
    found = clearance.check(desk.root, now, desk.door).found
    if found and (did := recover(desk.root, broker, listings, now.date(), desk.door)):
        _note(desk.root, now, RECOVERED, PUT_RIGHT.format("; ".join(did)))
        found = clearance.check(desk.root, now, desk.door).found
    if found:
        _note(desk.root, now, UNCLEAN, NOT_THE_BOOK.format("; ".join(found)))
    return not found


def _pending(root: Path, now: datetime, seen: watch.Look | None, once: bool = True) -> list[str]:
    """The venues whose round of orders is owed now: in continuous trading, with no round of
    today's on the record (not once: the intraday rounds, whatever is), and, of the market's
    own venue, once the look has read a bar of the session (watch.EARLY). A look that failed
    (None) holds every round."""
    if seen is None:
        return []
    done = {note.what for note in notes(root) if note.at.date() == now.date()}
    trading = {venue: venues.open_at(venue, now) for venue in VENUES}
    return [
        venue
        for venue, hours in trading.items()
        if hours and now < hours.close and not (once and ORDERS.format(venue) in done)
        if not (venue == YARDSTICK.venue and seen.unread.get(YARDSTICK) == watch.EARLY)
    ]


def _again(root: Path, now: datetime, seen: watch.Look | None) -> dict[str, set[str]]:
    """THE ROUND OWED ONCE MORE (R-RUNNER-395): of a venue still trading whose round is on the
    record and not yet made again, the symbols of today's orders the desk ITSELF cancelled (the
    cancel record) with nothing filled under the id or its -r1. A refusal, a fill and a
    broker-side cancel stand: only the desk's own cancels go again, as <id>-r1."""
    path = root / book.CANCELS
    if seen is None or not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as rows:
        mine = {row[0] for row in csv.reader(rows) if row[1:] == [now.date().isoformat()]}
    done = {note.what for note in notes(root) if note.at.date() == now.date()}
    filled = {fill.order_id for fill in book.fills(root) if fill.day == now.date()}
    out = dict[str, set[str]]()
    for venue in VENUES:
        hours = venues.open_at(venue, now)
        if not hours or now >= hours.close or ORDERS.format(venue) not in done:
            continue
        if f"{ORDERS.format(venue)} again" in done:
            continue
        stamp = f"{now:%Y%m%d}-"
        cut = {
            line.symbol
            for line in LINES
            if line.venue == venue
            for oid in mine
            if oid.startswith(stamp) and oid.endswith(f"-{line.symbol}")
            if not {oid, f"{oid}-r1"} & filled
        }
        if cut:
            out[venue] = cut
    return out


def _fit(
    saved: Saved, venue: str, today: date
) -> tuple[dict[Line, Sequence[Bar]], list[str], date]:
    """Of the bars saved before today, a venue's lines fit to decide on; the lines left out,
    by name (parked, or no bar of the session before today); and that session."""
    bars, parked = saved
    last = venues.sessions(venue, today - 9 * DAY, today)[-2]
    mine = {line: series for line, series in bars.items() if line.venue == venue}
    stale = {line for line, series in mine.items() if [bar.day for bar in series][-1:] != [last]}
    out = sorted(line.symbol for line in mine if line in stale or line.symbol in parked)
    return {line: series for line, series in mine.items() if line.symbol not in out}, out, last


def _round(
    desk: Desk, broker: placing.Paper, venue: str, now: datetime, only: Collection[str] = ()
) -> None:
    """A venue's orders for today, by the money path's own day, on the bars saved before
    today for the venue's lines; the round goes on the record with the answer to each order.
    A line parked by the store, or with no bar of the session before, is left out and named,
    never passed over in silence. Then each held line's stop is moved to 10% under its fill
    once (restop). A desk that dies in the round runs it again: the send path asks first."""
    today = now.date()
    kept = desk.held(today)
    saved, out, last = _fit(kept, venue, today)
    if only:  #: the round again: just the lines whose orders the desk cancelled
        saved, out = {ln: s for ln, s in saved.items() if ln.symbol in only}, []

    def tell(
        name: str, words: str
    ) -> None:  #: kept as a note: told at his next step until delivered
        _note(desk.root, now, name, words)

    sent = day.trade(desk.root, saved, broker, desk.room, today, desk.rates(today), tell)
    restop.move(desk.root, broker, LINES)  #: each held line's stop, under its fill (R-RUNNER-220)
    said = [
        f"{s.order_id}, {s.filled} shares done" + f" ({s.reason})" * bool(s.reason) for s in sent
    ]
    words = f"{VENUES[venue]}, today's orders: {'; '.join(said) or 'none sent in this round'}."
    held = _held_out(desk.root, out, kept[1], last)
    out = [symbol for symbol in out if symbol not in held]
    left = f" Left out, parked or with no bar of {last:%a %d %b}: {', '.join(out)}."
    name = ORDERS.format(venue) + " again" * bool(only)
    _note(desk.root, now, name, words + left * bool(out) + "".join(held.values()))


def _latest(
    desk: Desk, lines: Mapping[str, Line], span: intraday.Span, now: datetime
) -> dict[str, list[Candle]]:
    """The venue's lines whose latest whole bar of the span just closed, with the session's
    bars to it; a line whose store never held the span is skipped."""
    length, bars = timedelta(minutes=span.value), dict[str, list[Candle]]()
    for symbol, line in lines.items():
        try:
            whole = intraday.session(desk.hot, line, span, now.date())
            made = [c for c in whole if c.start + length <= now]
        except LookupError:  # the store never held this span for the line: not decided on
            continue
        if made and made[-1].start + 2 * length > now:
            bars[symbol] = made
    return bars


def _intraday(desk: Desk, broker: placing.Paper, venue: str, now: datetime) -> None:
    """THE INTRADAY ROUND (R-RUNNER-202): each rule decides on each line of the venue at its
    latest whole bar; its orders go by the one send path, each id dated with its bar's start,
    so a bar seen twice sends once. Stops are then moved; a round that sent nothing is not kept."""
    root, today, said, held = desk.root, now.date(), list[str](), book.positions(desk.root)
    lines, rates = {ln.symbol: ln for ln in LINES if ln.venue == venue}, desk.rates(today)
    owner = {f.symbol: strategy_of(f.order_id) for f in book.fills(root) if f.quantity > 0}
    for name, make in desk.rules.items():
        bars = _latest(desk, lines, make().span, now)
        mine = {s: owner[s] for s in held if s in owner}
        for d in intraday.today(venue, bars, mine, {name: make}):
            if d.action is Action.HOLD:
                continue
            line, stamp = lines[d.symbol], f"{today:%Y%m%d}-{name}-{d.symbol}"
            oid = f"{stamp}-{d.at:%H%M}{d.action.name[0]}"  #: a bar's buy and its sale differ
            if d.action is Action.SELL:
                order: Sale | Order = Sale(oid, line, held[d.symbol], session=today)
            else:
                buy, fx = Decision(name, d.symbol, today, d.action), rates[line.currency]
                try:
                    order = size(buy, line, bars[d.symbol][-1].close, fx, desk.room, held)
                    order = replace(order, order_id=oid)
                except Refused as refused:
                    said.append(str(refused))
                    continue
            sent = day._send(root, broker, order, desk.room, None, day.standing(root, today))
            said.append(f"{sent.order_id}, {sent.filled} shares done ({sent.reason or 'sent'})")
    if said:
        restop.move(root, broker, LINES)
        words = f"{VENUES[venue]}, this bar's orders: {'; '.join(said)}."
        _note(root, now, f"intraday {venue} {now:%H%M}", words)


def _held_out(
    root: Path, out: Sequence[str], parked: Collection[str], last: date
) -> dict[str, str]:
    """Of the lines left out, those the desk HOLDS, each with why its sell rule was not
    checked today and the level its stop rests at (R-RUNNER-312)."""
    held, levels, buys = book.positions(root), book.levels(root), dict[str, str]()
    for fill in book.fills(root):
        if fill.quantity > 0:
            buys[fill.symbol] = fill.order_id
    why = {s: "parked by the store" if s in parked else f"no bar of {last:%a %d %b}" for s in out}
    return {
        s: f" {s} held, not judged today: {why[s]}; its stop rests at "
        f"{levels.get(f'{buys[s]}-stop', 'a level the desk has not kept')}."
        for s in out
        if held.get(s)
    }


def _owed(root: Path, now: datetime) -> list[date]:
    """The sessions whose record is owed now, oldest first: each since the last record (with
    none yet, since the ledger's first fill, or today), today's only once every venue that
    traded today has had its closes kept (keeper.HELD), or the price store's door refuses."""
    kept, today = day.records(root), now.date()
    first = min((fill.day for fill in book.fills(root)), default=today)
    since = kept[-1].day if kept else min(first, today) - DAY
    traded = {on for venue in VENUES for on in venues.sessions(venue, since + DAY, today)}
    shut = all(
        now >= venues.hours(venue, today).auction + keeper.HELD
        for venue in VENUES
        if venues.sessions(venue, today, today)
    )
    return [on for on in sorted(traded) if on < today or shut]


def _drill(root: Path, now: datetime) -> None:
    """THE DAY'S DRILL of the kill switch (kill.drill), unless one made today is on its
    record (the desk unattended asks for today's own). One that broke a promise is that
    error, in his words."""
    if (Switch.DRILLED, now.date()) not in {(to, at.date()) for at, to, _ in book.switch(root)}:
        try:
            kill.drill(root, now)
        except kill.Failed as broke:
            raise kill.Failed(UNDRILLED.format(broke)) from broke


def _work(desk: Desk, now: datetime, seen: watch.Look | None) -> None:
    """What a step owes of a ready gateway, in the module's order; the paper account is asked
    only when something is owed. Each round and record has the check before it, and the day's
    drill is before them all, an error raised if it broke a promise."""
    root = desk.root
    rounds, owed, last = _pending(root, now, seen), _owed(root, now), clearance.checks(root)[-1:]
    checked = bool(last) and last[0].at.date() == now.date() and last[0].found is not None
    awake = gateway._uk(now).time() >= messenger.MORNING.start
    live = _pending(root, now, seen, False) if desk.rules else []
    again = _again(root, now, seen)
    check = bool(rounds or owed or live or again) or (awake and not checked)
    if not (check or owed or any(venues.open_at(venue, now) for venue in VENUES)):
        return
    listings = listing.kept(root, now, LINES, desk.door)
    broker = placing.Paper(listings, root, lambda: now, desk.door)
    book.collect(root, broker)
    _drill(root, now)
    if sold := goflat.step(root, broker, desk.room, now):
        _note(root, now, "go flat", f"{goflat.state(root)}: {'; '.join(sold)}")
    if check and not _clean(desk, broker, listings, now):
        rounds, live, again = [], [], {}
    for venue in rounds:
        _round(desk, broker, venue, now)
    for venue, symbols in again.items():  #: once more, the same check, gate and send
        _round(desk, broker, venue, now, symbols)
    for venue in live:  #: the intraday rounds, after the day's own
        _intraday(desk, broker, venue, now)
    for on in owed:  #: a missed session's rates are kept first, as its own day would have
        book.record_rates(root, on, desk.rates(on))
        day.publish(root, desk.held(on + DAY)[0], broker, desk.room, on)


def _say(desk: Desk, now: datetime, known: Known) -> None:
    """Everything he is owed at a moment, each under its own name and so once: a gateway that
    is his to look at, at any hour; the morning and evening message; and, in his waking
    hours, his weekly login's reminder and each thing the desk did in the last day (notes)."""
    root, post, local = desk.root, desk.post, gateway._uk(now)
    if known.state is State.HIS:
        since = local - timedelta(hours=gateway.WAKES.hour)
        messenger.send(root, now, f"gateway {since:%Y-%m-%d}", known.words, post)
    messenger.morning(root, now, known, post)
    messenger.evening(root, now, known, post)
    if desk.mail:
        messenger.summary(root, now, desk.mail)
    if messenger.MORNING.start <= local.time() < messenger.SLEEPS:
        messenger.remind(root, now, post)
        for note in (n for n in notes(root) if now - n.at < DAY):
            messenger.send(root, now, f"{note.what} {note.at:%Y-%m-%d %H:%M:%S}", note.words, post)


def _where(fault: BaseException) -> str:
    """The innermost desk function on a failure's traceback, as module.function: no failure
    is anonymous."""
    where, trace = "outside the desk", fault.__traceback__
    while trace is not None:
        module = trace.tb_frame.f_globals.get("__name__", "")
        if module.startswith("desk."):
            where = f"{module}.{trace.tb_frame.f_code.co_name}"
        trace = trace.tb_next
    return where


def step(desk: Desk, now: datetime) -> None:
    """ONE STEP OF THE DESK UNATTENDED, at a moment in UTC: of a gateway that says it is ready,
    whatever is owed is done (_work). A step that fails goes on the record, the day's first,
    and the error is raised all the same. Done or failed, he is then told all he is owed
    (_say), a gateway whose asking failed as one that did not say it is ready."""
    if now.utcoffset() != timedelta(0):
        raise ValueError(f"{now} is no moment in UTC: the desk's day is kept in UTC alone")
    known, seen, unseen = UNASKED, None, None  #: the look, or the error that it failed with
    try:
        known = gateway.known(now, door=desk.door)
        try:
            seen = watch.look(desk.root, desk.hot, desk.held(now.date())[0], now, desk.post)
        except Exception as failed:  # noqa: BLE001 - no round goes unseen; the rest is done
            unseen = failed
        if known:
            _work(desk, now, seen)
        if unseen:
            raise unseen
    except Exception as fault:
        kind = type(fault).__name__
        _note(desk.root, now, f"{TROUBLE} {kind}", FAILED.format(kind, fault, _where(fault)))
        raise
    finally:
        _say(desk, now, known)


if __name__ == "__main__":
    from desk import command  #: the command line's home; it imports this module, so only here

    sys.exit(command.main(sys.argv[1:]))
