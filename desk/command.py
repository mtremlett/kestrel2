"""command - THE DESK'S DAY AS THE RUNNER ASKS FOR IT, until the supervisor does (his ruling,
#159). Three commands, each one line of answer and a code, 0 when all is well:

    python -m desk.running              ONE STEP of the desk now (running.step)
    python -m desk.running --preflight  the morning's pre-flight: READY, or what is not
    python -m desk.running --rehearse   a whole trading day lived again, the markets shut

All is kept in `desk` under the folder the environment names (KESTREL2_DATA); the doors:

THE PRICE STORE'S DOOR is the keeper's (`keeper.saved`): a round or a record reads the daily
bars as the keeper last kept them, and a venue's bars left a session short are refused.

THE DAY'S POUNDS PER DOLLAR (`rates`): the pound's last close in dollars before the day, from
the same archive, until the data lane's own rate lands; once a day's rate is on the desk's
record that one is given, so it is the same at every asking.

THE PRE-FLIGHT (`preflight`) asks what a morning step would and sends no order: his phone's
key, the Gateway, the kill switch and today's drill, the paper account against the book,
the bars of the session before, the pound, any halt. Its one line names each.

THE REHEARSAL (`rehearse`) lives the last session again, every five minutes of its day, on a
record of its own and at the real paper Gateway. It begins only on a day no market trades,
the real desk's kill switch off: an order it sends cannot fill, and the adapter cancels what
the broker did not fill. Its own book is empty, but the paper account may hold lines and their
resting stops, as it does since the desk trades: what is found at the start is the account's,
unseen by the rehearsal's steps and never sold, cancelled or moved by it. Its orders carry the ids
of the session rehearsed, a day that is over, never the next real day's. A step that fails is
counted and the next carries on, as in the day itself; at the end whatever of the desk's is
still working is cancelled. It is GO only if each venue's round and the day's record were
made, both daily messages written, no check named the account, nothing was left working or
filled, and the account is as it was found: the same holdings, and the same working orders by
id and level. Its messages go on its own record alone."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from functools import partial
from http.client import HTTPException
from pathlib import Path

from desk import (
    archive,
    book,
    clearance,
    gateway,
    halt,
    keeper,
    kill,
    listing,
    messenger,
    paper,
    placing,
    pnl,
    running,
    venues,
)
from desk import day as days
from desk.lines import LINES, Line
from desk.orders import Settings
from desk.paper import Account
from desk.running import DAY, VENUES, Desk

ROOT, STORE, REHEARSALS = "desk", "store", "rehearsals"  #: folders, each inside the one before
CAPITAL = Decimal(10_000)  #: the paper desk's one capital, in pounds, until he rules another
#: The pound in dollars at the archive; no pound closes outside these; the oldest close trusted.
POUND, DOLLARS, FRESH = Line("GBPUSD=X", "US", "USD", 1), (Decimal(1), Decimal(2)), 4 * DAY
FIRST, LAST, EVERY = time(5, 30), time(22), timedelta(minutes=5)  #: the runner's day, UK clock
NAMED = (OSError, HTTPException, ValueError, kill.Failed, messenger.Undelivered, paper.NotPaper)
USAGE = "python -m desk.running [--preflight | --rehearse]"
RUN = timedelta(minutes=30)  #: the rehearsal's longest run, as the runner allows it
WINDOW = RUN + timedelta(minutes=60)  #: how near a market's open, or inside it, bars a rehearsal
AFTER = timedelta(minutes=30)  #: how long past a session's uncrossing a rehearsal still waits
OPEN = "REHEARSAL NO-GO: not begun: {}."
GO = (
    "REHEARSAL GO: {:%a %d %b} lived again in {} steps at the paper Gateway ({} failed and the "
    "next carried on), no market trading: {} orders decided, {} of them sent to the broker and "
    "cancelled, none filled; the account left as found, the day's record made, {} messages "
    "written and none sent to his phone.{}"
)
UNSENT = " NO ORDER REACHED THE BROKER: this rehearsal does not prove the sending."


def rates(root: Path, day: date) -> dict[str, Decimal]:
    """A DAY'S POUNDS PER UNIT OF EACH CURRENCY: the dollar's as the desk's record at root
    keeps it for the day, else one over the pound's last close in dollars before the day. A
    close that is no pound's, or too old for the day, is an error and no rate."""
    try:
        kept: Decimal | None = book.rate(root, "USD", day)
    except ValueError:
        kept = None
    if kept is None:
        #: the archive adds the day's own bar, still moving (seen 14 November 2026): not before it
        last = [bar for bar in archive.fetch(POUND, day) if bar.day < day][-1:]
        if not (last and day - last[0].day <= FRESH and DOLLARS[0] < last[0].close < DOLLARS[1]):
            raise ValueError(f"{day}: the archive has no pound in dollars to trust: {last}")
        kept = (1 / last[0].close).quantize(Decimal("0.000001"))
    return {"GBP": Decimal(1), "USD": kept}


def _post(env: Mapping[str, str]) -> messenger.Post:
    """His phone. With no key of his in the environment, a door that says so at every
    message: the desk still does its work, and each step that owes him words then fails,
    by name, until the key is set. The words wait on the delivery record."""
    try:
        return messenger.telegram(env)
    except ValueError as missing:
        why = str(missing)

    def unsaid(_text: str) -> int:
        raise messenger.Undelivered(why)

    return unsaid


def _desk(root: Path, post: messenger.Post, home: Path) -> Desk:
    """The real doors, with the desk's records at root; the keeper's stores are in home."""
    return Desk(
        root,
        Settings(CAPITAL),
        post,
        partial(rates, root),
        home / keeper.HOT,
        partial(keeper.saved, home),
        paper.Door(paper.DESK),
    )


def _phone(env: Mapping[str, str]) -> str:
    messenger.telegram(env)
    return "its key is set"


def _knock(now: datetime, door: paper.Door) -> str:
    if not (known := gateway.known(now, door=door)):
        raise ConnectionError(known.words)
    return "it answered"


def _switch(root: Path, now: datetime) -> str:
    if on := book.killed(root):
        raise ValueError(f"{on}; no order goes until it is released")
    running._drill(root, now)
    return "off, and drilled today"


def _account(root: Path, now: datetime, door: paper.Door) -> str:
    if found := clearance.check(root, now, door).found:
        raise ValueError(f"it is not the desk's book: {'; '.join(found)}")
    return "it is the desk's book"


def _prices(desk: Desk, today: date) -> str:
    """The lines with a bar of the session before today, on each venue that trades today."""
    saved = desk.held(today)
    fits = [running._fit(saved, v, today) for v in VENUES if venues.sessions(v, today, today)]
    fit, out = sum(len(lines) for lines, _, _ in fits), [s for _, left, _ in fits for s in left]
    if not fits:
        return "no market trades today"
    if not fit:
        raise ValueError(f"no line has a bar of the session before, so no order would go: {out}")
    left = f" (left out, parked or stale: {', '.join(out)})"
    return f"{fit} lines to trade on" + left * bool(out)


def _pound(desk: Desk, today: date) -> str:
    """The day's dollar, kept on the desk's record so the US round reads it, not the archive;
    a pound that cannot be trusted is an error here and nothing is kept."""
    rate = desk.rates(today)
    book.record_rates(desk.root, today, rate)
    return f"a dollar is £{rate['USD']}, kept for the day"


def preflight(desk: Desk, env: Mapping[str, str], now: datetime) -> tuple[bool, str]:
    """THE MORNING'S PRE-FLIGHT: whether the desk is ready for today, and its one line. Each
    thing a morning step leans on is asked in turn and named, ready or not; none stops the
    next. The drill and the day's check go on the desk's record, as a step's would. No order
    is sent, and nothing is put right: that is a step's."""
    today, root = now.date(), desk.root
    probes: tuple[tuple[str, Callable[[], object]], ...] = (
        ("his phone", lambda: _phone(env)),
        ("the Gateway", lambda: _knock(now, desk.door)),
        ("the kill switch", lambda: _switch(root, now)),
        ("the paper account", lambda: _account(root, now, desk.door)),
        ("prices", lambda: _prices(desk, today)),
        ("the pound", lambda: _pound(desk, today)),
        ("halts", lambda: halt.said(root, today) or "none in force"),
    )
    ready, wrong = list[str](), list[str]()
    for name, probe in probes:
        try:
            ready.append(f"{name}: {probe()}")
        except NAMED as why:
            wrong.append(f"{name}: {type(why).__name__}: {why}")
    head = f"PREFLIGHT {today:%a %d %b}: "
    if wrong:
        fine = "; ".join(ready) or "nothing"
        return False, f"{head}NOT READY. {'; '.join(wrong)}. Ready: {fine}."
    halted = ", BUT NO BUY GOES: a halt is in force" * bool(halt.in_force(root))
    return True, f"{head}READY{halted}. {'; '.join(ready)}."


def _moments(on: date) -> list[datetime]:
    """Every five minutes of the runner's day on a UK clock, in UTC, the first and last in."""
    first, last = (datetime.combine(on, at, venues.zone("LSE", on)) for at in (FIRST, LAST))
    return [(first + n * EVERY).astimezone(UTC) for n in range((last - first) // EVERY + 1)]


def _amiss(desk: Desk, on: date, left: Sequence[str], changes: Sequence[str]) -> list[str]:
    """What a rehearsed day left that a good day does not, each thing in words."""
    root, kept = desk.root, running.notes(desk.root)
    done, told = {note.what for note in kept}, {d.name for d in messenger.deliveries(desk.root)}
    wrong = [
        f"{VENUES[venue]}'s round of orders was not made"
        for venue in VENUES
        if venues.sessions(venue, on, on) and running.ORDERS.format(venue) not in done
    ]
    wrong += [note.words for note in kept if note.what == running.UNCLEAN]
    daily = (messenger.MORNING.name, messenger.EVENING.name)
    wrong += [f"the {name} message was not written" for name in daily if f"{name} {on}" not in told]
    if [record.day for record in days.records(root)] != [on]:
        wrong.append("the day's record was not made")
    if fills := book.fills(root):
        wrong.append(f"an order FILLED, the markets shut: {[fill.order_id for fill in fills]}")
    if left or changes:
        wrong.append(f"the paper account is not as found; left working, now cancelled: {left}")
        wrong += changes
    return wrong


@dataclass(frozen=True)
class Found(paper.Apart):
    """THE ACCOUNT AS THE REHEARSAL FOUND IT: its held lines and working orders are the
    account's, so the rehearsal's steps do not see them and cannot touch them (a Door's apart)."""

    orders: frozenset[str] = frozenset()  #: the broker's ids of the orders found working

    def without(self, account: Account) -> Account:
        """The account less what was found: what is left is the rehearsal's own."""
        gone = [o for o in account.orders if o.broker_id not in self.orders]
        return Account(
            tuple(h for h in account.holdings if h.name not in self.holdings), tuple(gone)
        )

    def changes(self, found: Account, now: Account) -> list[str]:
        """How the account now differs from found: the same holdings, the same working orders
        by id and level, and nothing else of the rehearsal's working. Each, named."""
        kept = {h.name: h.shares for h in now.holdings if h.shares}
        words = [
            f"{h.name}: {h.shares} shares held, now {kept.get(h.name, 0)}"
            for h in found.holdings
            if h.shares and kept.pop(h.name, 0) != h.shares
        ]
        words += [f"{name}: {shares} shares held, found none" for name, shares in kept.items()]
        listed = {o.broker_id: o for o in now.orders}
        for old in found.orders:
            if (new := listed.pop(old.broker_id, None)) is None:
                words.append(f"a held line's order {old.ref} ({old.symbol}) was cancelled")
            elif new.level != old.level:
                words.append(f"a held line's order {old.ref} ({old.symbol}) was moved")
        words += [f"its own order {o.ref} ({o.symbol}) is still working" for o in listed.values()]
        return words


def _trading(now: datetime) -> list[str]:
    """The markets open at now, opening within WINDOW, or ended less than AFTER ago."""
    return [
        VENUES[venue]
        for venue in VENUES
        for on in venues.sessions(venue, now.date(), now.date())
        if (hours := venues.hours(venue, on)).open < now + WINDOW and hours.auction + AFTER >= now
    ]


def _live(desk: Desk, moments: Sequence[datetime], clock: Callable[[], datetime]) -> list[str]:
    """A step at each moment, as the day's: one that fails is named and the next carries on; the
    run stops, named, if a market comes near by the clock."""
    failed = list[str]()
    for at in moments:
        if near := _trading(clock()):
            failed.append(f"{at:%H:%M} UTC stopped, {' and '.join(near)} near")
            break
        try:
            running.step(desk, at)
        except Exception as fault:  # noqa: BLE001 - a failed step is the rehearsal's finding
            failed.append(f"{at:%H:%M} UTC {type(fault).__name__}")
    return failed


def rehearse(
    root: Path, now: datetime, clock: Callable[[], datetime] = lambda: datetime.now(UTC)
) -> tuple[bool, str]:
    """THE REHEARSAL: the last session before today lived again, a step at each of its
    moments, on a new record under root and at the real paper Gateway; whether it is GO, and
    its one line. Not begun while the kill switch at root is on. Its book is empty: what the
    paper account holds or has working when it begins is the account's (Found), and is left
    as found. Not begun, either, while while a market's session is open or opens
    within the rehearsal's longest run and an hour (WINDOW), or ended just now (AFTER); a run
    that finds one so stops at once. A step that fails is counted and the next carries on; then
    the desk's own orders still working are
    cancelled and the account is read again, whatever happened."""
    today, before = now.date(), paper.whole(paper.Door(paper.DESK))
    trading = _trading(now)
    barred = (
        f"{' and '.join(trading)} trade now, soon or just ended, and an order it sent could fill"
        * bool(trading),
        book.killed(root) or "",
    )
    if any(barred):
        return False, OPEN.format("; ".join(filter(None, barred)))
    on = max(venues.sessions(venue, today - 9 * DAY, today - DAY)[-1] for venue in VENUES)
    said: list[str] = []

    def post(text: str) -> int:
        said.append(text)
        return len(said)

    moments = _moments(on)
    found = Found(
        frozenset(h.name for h in before.holdings if h.shares),
        frozenset(o.broker_id for o in before.orders),
    )
    door = paper.Door(paper.DESK, found)  #: the account found is not the rehearsal's to see
    desk = replace(_desk(root / REHEARSALS / f"{now:%Y%m%dT%H%M%S}", post, root.parent), door=door)
    failed = _live(desk, moments, clock)
    left = placing.Paper(listing.read(LINES, door), desk.root, lambda: now, door).cancel()
    if wrong := _amiss(desk, on, left, found.changes(before, paper.whole(door))):
        steps = f"; steps that failed: {', '.join(failed)}" * bool(failed)
        return False, f"REHEARSAL NO-GO: {'; '.join(wrong)}{steps}"
    words = " ".join(note.words for note in running.notes(desk.root))
    orders, sent = words.count(" shares done"), words.count(": the broker says ")
    counts = (on, len(moments), len(failed), orders, sent, len(said), UNSENT * (not sent))
    return True, GO.format(*counts)


def hourly(desk: Desk, now: datetime) -> None:
    """His hourly profit and loss (desk/pnl.py), told after a real step: not in a rehearsal,
    which has no day of its own to tell."""
    today = now.date()

    def words() -> str:
        daily = desk.held(today)[0]
        return pnl.told(desk.root, desk.hot, daily, desk.rates(today), desk.room.capital, now)

    messenger.hourly(desk.root, now, words, desk.post)


def main(
    argv: Sequence[str],
    env: Mapping[str, str] = os.environ,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> int:
    """THE COMMAND LINE (USAGE): its one line of answer printed last, and 0 when all is well.
    A step that fails is its own error raised, so the code is not 0 and the error is said."""
    root, now = Path(env["KESTREL2_DATA"]) / ROOT, clock()
    if not root.is_absolute():
        raise SystemExit(f"KESTREL2_DATA names no whole path to a folder: {root.parent}")
    desk = _desk(root, _post(env), root.parent)
    match argv:
        case []:
            running.step(desk, now)
            hourly(desk, now)
            good, line = True, f"STEP {now:%a %d %b %H:%M} UTC: done."
        case ["--preflight"]:
            good, line = preflight(desk, env, now)
        case ["--rehearse"]:
            good, line = rehearse(root, now, clock)
        case _:
            raise SystemExit(USAGE)
    print(line)  # noqa: T201 - the command's answer to whoever asked
    return int(not good)
