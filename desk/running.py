"""running - THE DESK UNATTENDED, AND RECOVERED AFTER A RESTART. One step (`step`) does
whatever the desk owes at the moment it is given, each thing once; whoever keeps the desk
alive asks for a step every few minutes. A step remembers nothing: what is done is on the
desk's records, what is not is done by the next, so a desk that died restarts by a step.

THE CRASH WATCH'S LOOK (watch.look) is made first at every step, whatever the gateway says:
it halts buying on a crash, and till it has read a venue's first bar it holds that round.
A look that fails holds every round; the rest is done, and the failure raised after.

What a step owes, in this order, and only of a gateway that says it is ready:
- THE LEDGER brought up to date with the broker's fills, at each step while a market is open.
- THE KILL SWITCH'S DRILL (`_drill`), once each day (UTC), at its first step with anything
  below to do: no order goes on a day the switch was not seen to work. A drill that broke a
  promise fails the step, and the next drills again.
- THE DAY'S CHECK (clearance.check), from the hour he wakes, and before each round and record.
  When it names anything, what a dead desk left at the broker is put right (`recover`) and
  the account checked again. Still not clean, no order goes, he is told.
- THE DAY'S ORDERS (desk/rounds.py), one round for each venue while it trades: the money
  path's own day (day.trade), on the bars saved before today. The send path asks the broker
  of every order first, so a round begun twice sends nothing twice; an order refused in it
  is not sent later.
- THE INTRADAY ROUNDS (desk/bar_rounds.py), after the day's own: each intraday rule at each whole
  bar of its span, through the same check, gate, stops and records (none trade yet); with the
  paper switch (ZOO_ON) the zoo's rules too, one share each, said to be a MACHINERY TEST,
  NOT EVIDENCE OF AN EDGE (CANON B6, his 22 Nov ruling).
- THE DAY'S RECORD (day.publish), once every market that traded has its closes kept
  (keeper.HELD); a session the desk missed gets its own first.

Then, whatever happened, he is told through the desk's one voice (desk/messenger.py): the
morning and evening messages, a gateway to look at, his weekly login and each thing on the
record (`notes`). A step that fails raises to its asker; the next tries again."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from datetime import date, datetime, timedelta
from pathlib import Path

from desk import (
    bar_rounds,
    book,
    clearance,
    day,
    gateway,
    goflat,
    halt,
    keeper,
    kill,
    listing,
    messenger,
    placing,
    rounds,
    venues,
    watch,
)
from desk.book import Switch
from desk.gateway import Known, State
from desk.lines import LINES
from desk.listing import Listing, Unlisted
from desk.running_notes import (
    DAY,
    RECOVERED,
    TROUBLE,
    UNCLEAN,
    VENUES,
    ZOO_NOTE,
    Desk,
    _note,
    notes,
)
from desk.running_parts import PUT_RIGHT
from desk.running_parts import recover as recover

NOT_THE_BOOK = "The paper account is not the desk's book, so no order goes. Its check named: {}."
FAILED = (
    "A step of the desk failed; the next tries again: {}: {} (in {}). Its like today is not told."
)
UNDRILLED = (
    "today's rehearsal of the kill switch did not pass, so the desk sends no order, checks no "
    "account and makes no record until one does. It was a rehearsal on a pretend desk: no real "
    "order was involved. Each promise named next was NOT kept: {}"
)
ZOO_ON = "zoo-on-paper"  #: the one paper switch: this file in the desk's root turns the zoo on
DOWN_MARK = "gateway_down"  #: the file at root holding when the Gateway was first found down
UNASKED = Known(State.UNWELL, gateway.UNWELL.format("the desk's knock on it failed"))


def _clean(
    desk: Desk, broker: placing.Paper, listings: Mapping[str, Listing | Unlisted], now: datetime
) -> bool:
    """The day's check, run now: is the paper account the desk's book? What it names is put
    right (recover) and checked again; what it still names he is told, and no order goes."""
    found = clearance.check(desk.root, now, desk.door).found
    if found and (did := recover(desk.root, broker, listings, now.date(), desk.door)):
        _note(desk.root, now, RECOVERED, PUT_RIGHT.format("; ".join(did)))
        found = clearance.check(desk.root, now, desk.door).found
    if found:
        _note(desk.root, now, UNCLEAN, NOT_THE_BOOK.format("; ".join(found)))
    return not found


def down_since(root: Path, known: Known, now: datetime) -> datetime | None:
    """When the paper Gateway went down, if it is down (not ready, not its daily restart): the
    first moment it was found so, kept in a mark at root until it answers again."""
    mark = root / DOWN_MARK
    if known.state not in (State.HIS, State.UNWELL):
        mark.unlink(missing_ok=True)
        return None
    if not mark.exists():
        mark.write_text(now.isoformat())
    return datetime.fromisoformat(mark.read_text())  # bounded: one timestamp, never grows


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


def _stand(root: Path, broker: placing.Paper, now: datetime) -> None:
    """The step's first duties at a ready gateway: a halt in force (the look's or his) takes
    the working buys down, then the day's drill."""
    if halt.in_force(root):
        broker.cancel()
    _drill(root, now)


def _paper(desk: Desk, listings: Mapping[str, Listing | Unlisted], now: datetime) -> placing.Paper:
    """The desk's one broker at the paper Gateway, for a moment."""
    return placing.Paper(listings, desk.root, lambda: now, desk.door)


def _work(desk: Desk, now: datetime, seen: watch.Look | None) -> None:
    """What a step owes of a ready gateway, in the module's order; the paper account is asked
    only when something is owed. Each round and record has the check before it, the drill first."""
    root = desk.root
    due, owed, last = (
        rounds._pending(root, now, seen),
        _owed(root, now),
        clearance.checks(root)[-1:],
    )
    checked = bool(last) and last[0].at.date() == now.date() and last[0].found is not None
    awake = gateway._uk(now).time() >= gateway.WAKES
    live = rounds._pending(root, now, seen, False) if bar_rounds._rules(desk) else []
    again = rounds._again(root, now, seen)
    check = bool(due or owed or live or again) or (awake and not checked)
    if not (check or owed or any(venues.open_at(venue, now) for venue in VENUES)):
        return
    broker = _paper(desk, listings := listing.kept(root, now, LINES, desk.door), now)
    bar = placing.Paper(listings, root, lambda: now, desk.door, within=True)  #: R-RUNNER-468
    book.collect(root, broker)
    _stand(root, broker, now)
    if sold := goflat.step(root, broker, desk.room, now):
        _note(root, now, "go flat", f"{goflat.state(root)}: {'; '.join(sold)}")
    if check and not _clean(desk, broker, listings, now):
        due, live, again = [], [], {}
    for venue in due:
        rounds._round(desk, broker, venue, now)
    for venue, symbols in again.items():  #: once more, the same check, gate and send
        rounds._round(desk, broker, venue, now, symbols)
    placed: list[book.Sent] = []
    for venue in live:  #: the intraday rounds, after the day's own, their orders due today
        bar_rounds._intraday(desk, bar, venue, now, placed)
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
    messenger.morning(root, now, known, post, desk.room.capital)
    messenger.idle(root, now, post)
    messenger.evening(root, now, known, post)
    if desk.mail:
        messenger.summary(root, now, desk.mail)
    if gateway.WAKES <= local.time() < messenger.SLEEPS:
        messenger.remind(root, now, post)
        for note in (n for n in notes(root) if now - n.at < DAY and n.what.split()[0] != ZOO_NOTE):
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
    and the error is raised all the same. Done or failed, he is then told all he is owed (_say)."""
    if now.utcoffset() != timedelta(0):
        raise ValueError(f"{now} is no moment in UTC: the desk's day is kept in UTC alone")
    known, seen, unseen = UNASKED, None, None  #: the look, or the error that it failed with
    try:
        known = gateway.known(now, door=desk.door)
        try:
            seen = watch.look(
                desk.root,
                desk.hot,
                desk.held(now.date())[0],
                now,
                desk.post,
                door=lambda: _paper(desk, listing.kept(desk.root, now, LINES, desk.door), now),
            )
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
