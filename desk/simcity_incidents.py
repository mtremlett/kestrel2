"""simcity_incidents - SCENARIOS SimCity lives because a night met them: each is a morning the
desk was put in, a promise it must keep there, and the day it then runs. Each carries its
request (R-RUNNER-246 to 248, 314 to 319, 323 to 325, 347: a held line with no bar for a
session, shares beside the book under a stop, a halt, a silent broker or Gateway, a locked
store, a stale keeper) in `git log` and `docs/DECISIONS.md`."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from itertools import count
from typing import TYPE_CHECKING

from desk import (
    bars,
    book,
    conformance,
    conformance_parts,
    day_money,
    halt,
    keeper,
    keeper_live,
    kill,
    messenger,
    paper,
    venues,
    watch,
)
from desk.bars import Five
from desk.broker import Fault, Pretend, Report
from desk.conformance_parts import Side
from desk.keeper_rotate import Kept, record
from desk.lines import LINES, YARDSTICK, Line
from desk.orders import Order, Sale
from desk.running import DAY
from desk.spans import Timed
from desk.store import Bar

if TYPE_CHECKING:
    from desk.simcity import _Life

HOLE = "a held line has no bar for the session"
LEFT = "shares the book lacks rest at the broker under a stop"
SOLD = "shares the book lacks, under a stop at the broker, are left under it and never sold"
CANCELLED = "the broker cancels every order of the day with nothing filled"
NAMED = "an order cancelled unfilled is named that day, and the book stays the broker's"
HALTED = "a halt is in force while the day's buys are asked for"
DROPPED = "a halt takes down a buy still working at the broker, and leaves every stop resting"
STILL = "with a halt in force nothing is bought"
OUTSIDE = "a line no ISA can hold is never bought"
PARKED = "a yardstick with a session missing refuses the day by name"
STALE = "a venue's daily bars are a session short at the keeper's last refresh"
REFUSED = "the price store's door refuses a venue short of a session, naming its line"
DEAF = "the market goes unheard for an hour: he is told once in each hour, and nothing is halted"
LIVE = "lines in session whose one-minute bar has just ended are none of them stale"
UNHELD = (
    "the live keeper asks for one-minute bars of lines the store never held: each is named stale"
)
UNBARRED = "a conformance plan with no bar of the session before the day refuses, naming the line"
LOCKED = "a store another writer holds refuses the round by name, loses nothing, serves the next"
SILENT = "a broker silent after an order is sent: the kill switch is on, the alarm names the order"
SLOW = "a broker that fills nothing cannot keep the desk's day past the step's time"
STOP_SILENT = (
    "a gateway silent when the stop is to fire fails that step by name and puts the account back"
)
SHUT = (
    "a closed Gateway port outside its restart: the run is not begun, nothing sent, his to look at"
)
PROMISE = "a held line with no bar for a session is named owed and the day's profit withheld"


def hole(life: _Life, on: date) -> None:
    """A held line's bar for the day is missing when the day ends. The desk must make no record
    from an older price: its record names the line owed and withholds the profit. The yardstick
    is not chosen: its own close is owed to every record, and without it the day has none."""
    bars = {x: b for x, b in life.market.items() if any(d.day == on for d in b)}
    held = [x for x in bars if x.symbol in dict(life.pretend.stops()) and x != YARDSTICK]
    if not held:
        life.live(on)
        return
    line, whole = held[0], life.market[held[0]]
    life.market[line] = tuple(bar for bar in whole if bar.day != on)
    record = life.live(on)
    life.market[line] = whole  #: the record names the line owed, or a stop or sale ended it
    owed = line.symbol + day_money.NO_CLOSE_OWED in record.mismatches and record.profit is None
    life.promise(PROMISE, owed or line.symbol not in book.positions(life.desk))


def beside(life: _Life, on: date) -> None:
    """Shares the book never saw rest at the broker under their own stop. The desk must not
    sell them on top of the stop (that sells twice): after the day the broker holds them
    all, still under the stop. A hand then clears them."""
    free = sorted({x.symbol for x in life.market} - set(book.positions(life.desk)))
    symbol = life.rng.choice(free)
    level = min(b.low for x, bars in life.market.items() if x.symbol == symbol for b in bars)
    shares = life.rng.randint(1, 50)
    life.pretend.inject(symbol, shares)
    life.pretend.put_stop_back(symbol, level / 2)
    life.live(on)
    held = dict(life.pretend.holdings()).get(symbol, 0)
    life.promise(SOLD, held == shares and dict(life.pretend.stops()).get(symbol, 0) == shares)
    life.pretend.cancel_stop(symbol)  # a hand clears the stranger, so the world goes on
    life.pretend.inject(symbol, -held)


def cancelled(life: _Life, on: date) -> None:
    """The broker cancels, unfilled, the first order it is sent on every line. The desk must name
    each such order on the morning's list (unless another rule's order then fills its line) and
    leave the book the broker's: shares never bought are never in it, so no sale is sent."""
    seen = len(life.pretend.submitted())
    life.pretend._faults.update(  # noqa: SLF001 - the world's own broker, told what to do
        {x.symbol: Fault.REJECT for x in life.market}
    )
    life.live(on)
    life.pretend._faults.clear()  # noqa: SLF001 - what no order met is not left waiting
    told = {b.order_id for b in halt.morning(life.desk, on)[halt.Blocker.BROKER]}
    answers = {i: life.pretend.report(i) for i in life.pretend.submitted()[seen:]}
    bought = {i.rsplit("-", 1)[1] for i, r in answers.items() if r and r.fills}
    resent = {
        i.removesuffix("-r1") for i, r in answers.items() if i.endswith("-r1") and r and r.fills
    }
    refused = {i for i, r in answers.items() if r and not r.fills and not i.endswith("-r1")}
    refused -= told | resent
    named = all(i.rsplit("-", 1)[1] in bought for i in refused)
    level = dict(book.positions(life.desk)) == dict(life.pretend.holdings())
    life.promise(NAMED, named and level)


def halted(life: _Life, on: date) -> None:
    """A halt is called before the day: no buy may reach the broker, and the day's list names it."""
    at, reached = datetime.combine(on, time(7), UTC), life.pretend.buys
    called = halt.call(life.desk, at, "SimCity halts a day")
    life.live(on)
    life.promise(STILL, life.pretend.buys == reached)
    halt.lift(life.desk, called, at, "SimCity lifts it")


def dropped(life: _Life, on: date) -> None:
    """A buy is working at the broker when a halt is called (the 19 November VHYG buy). The halt
    must cancel it by its id and leave the stops resting; the day then runs, no order left."""
    held = book.positions(life.desk)
    line = next(x for x in sorted(life.market, key=lambda x: x.symbol) if x.symbol not in held)
    price = life.market[line][-1].close
    order = Order(f"drop-{line.symbol}", line, 1, price, life.rates[line.currency], price / 2)
    life.pretend._working[order.order_id] = order  # noqa: SLF001 - a buy the world's broker holds
    stops, at = life.pretend.stops(), datetime.combine(on, time(7), UTC)
    stopped = halt.stop(life.desk, life.pretend, at, "SimCity halts a working buy")
    life.promise(DROPPED, stopped.cancelled == (order.order_id,) and life.pretend.stops() == stops)
    halt.lift(life.desk, stopped.halt, at, "SimCity lifts it")
    life.live(on)


def outside(life: _Life, on: date) -> None:
    """Every line but the yardstick and those held is recorded as outside an ISA for the day: no
    buy of such a line reaches the broker (the yardstick's own key is the day's, and is kept)."""
    whole, reached, held = life.market, len(life.pretend.submitted()), book.positions(life.desk)
    barred = {x.symbol for x in whole if x.symbol not in held and x != YARDSTICK}
    life.market = {
        x if x.symbol not in barred else replace(x, isa=False): b for x, b in whole.items()
    }
    life.live(on)
    sent = life.pretend.submitted()[reached:]
    life.promise(OUTSIDE, not any(i.rpartition("-")[2] in barred for i in sent))
    life.market = whole


def parked(life: _Life, on: date) -> None:
    """The yardstick's bar for the session before the day is missing (a gap in the archive, the
    line parked). The desk must refuse the day, naming the line, for the market's gain over the
    gap cannot be told; when the bar is back the same day runs."""
    whole = life.market.get(YARDSTICK, ())
    gone = [b.day for b in whole if b.day < on][-1:]
    if not gone:
        life.live(on)
        return
    life.market[YARDSTICK] = tuple(b for b in whole if b.day != gone[0])
    try:
        life.live(on)
    except ValueError as refusal:  #: the desk's own word that the day has no record
        life.promise(PARKED, YARDSTICK.symbol in str(refusal))
        life.market[YARDSTICK] = whole
        life.live(on)
    else:
        life.market[YARDSTICK] = whole
        life.promise(PARKED, False)


def stale(life: _Life, on: date) -> None:
    """The keeper's last refresh of every venue readied a week before the day, so a session is
    lacking. The price store's door must refuse, naming a line, never serve the older bars."""
    lines = sorted(life.market, key=lambda x: x.symbol)
    stored = life.desk / "keeper"
    for venue in {x.venue for x in lines}:
        past = Kept(on - timedelta(days=7), datetime.combine(on, time(), UTC), 1, {}, frozenset())
        record(stored / keeper.DAILY / venue, past)
    try:
        keeper.saved(stored, on, lines)
    except keeper.Stale as refusal:  #: the keeper's own word that the store is not fresh
        life.promise(REFUSED, lines[0].symbol in str(refusal))
    else:
        life.promise(REFUSED, False)
    life.live(on)


def deaf(life: _Life, on: date) -> None:
    """The market's last bar of the session ended an hour ago and no bar since has come. The
    crash watch looks at three moments (two in one hour, one in the next): it must tell him it
    is blind once in each of the two hours, and call no halt for that alone."""
    if YARDSTICK not in life.market or on not in venues.sessions(YARDSTICK.venue, on, on):
        life.live(on)
        return
    daily = {x: [b for b in bars_ if b.day < on] for x, bars_ in life.market.items()}
    daily[YARDSTICK] = daily[YARDSTICK][-1:]  #: a calm month, so only the deafness can halt
    session, price = venues.hours(YARDSTICK.venue, on), Decimal(daily[YARDSTICK][-1].close)
    hot, post = life.desk / "deaf-bars.db", count(1).__next__
    with bars.writing(hot) as round_:
        round_.five(YARDSTICK, [Five(session.open + timedelta(hours=1), *(price,) * 4, 1)])
    first = session.open + timedelta(hours=2)
    kept = halt.kept(life.desk)
    for at in (first, first + timedelta(minutes=20), first + timedelta(minutes=65)):
        watch.look(life.desk, hot, daily, at, lambda _words: post())
    told = [d.name for d in messenger.deliveries(life.desk) if d.name.endswith("h blind")]
    hours = {f"watch {on:%Y-%m-%d} {at:%H}h blind" for at in (first, first + timedelta(hours=1))}
    life.promise(
        DEAF, hours <= set(told) and len(told) == len(set(told)) and kept == halt.kept(life.desk)
    )
    life.live(on)


def minutes(life: _Life, on: date) -> None:
    """Two hours into the session every line of the yardstick's venue is due, and the broker
    answers each with the one-minute bar that has just ended. The keeper's live run must call
    none of them stale (else its job fails for a market that is whole), and keep the bars."""
    if venues.sessions(YARDSTICK.venue, on, on) != (on,):
        life.live(on)  #: the venue keeps a holiday: it has no hours to be stale in
        return
    now = venues.hours(YARDSTICK.venue, on).open + timedelta(hours=2)
    lines = sorted((x for x in life.market if x.venue == YARDSTICK.venue), key=lambda x: x.symbol)
    price = Decimal(1)

    def ask(_line: Line, at: datetime) -> tuple[Timed, ...]:
        return (Timed(keeper_live.MINUTES, at - timedelta(minutes=1), *(price,) * 4, 1),)

    hot = life.desk / "minutes-bars.db"
    words, missed = keeper_live.minute_round(hot, lines, now, ask)
    life.promise(LIVE, bool(lines) and not missed and ", 0 stale," in words)
    life.live(on)


def unheld(life: _Life, on: date) -> None:
    """The live keeper's store holds five-minute bars but never a one-minute bar of any line, and
    a venue is in session. The run must finish, never die on the store's LookupError, and name
    each line it could get no bar for as stale."""
    if on not in venues.sessions(YARDSTICK.venue, on, on):
        life.live(on)
        return
    session = venues.hours(YARDSTICK.venue, on)
    lines = sorted((x for x in life.market if x.venue == YARDSTICK.venue), key=lambda x: x.symbol)
    hot, now = life.desk / "unheld-bars.db", session.open + timedelta(hours=1)
    with bars.writing(hot) as round_:
        round_.five(YARDSTICK, [Five(session.open, *(Decimal(1),) * 4, 1)])

    def ask(line: Line, at: datetime) -> tuple[Timed, ...]:
        return bars.timed(hot, line, keeper_live.MINUTES, at - timedelta(hours=1), at)

    try:
        _, stale_ = keeper_live.minute_round(hot, lines, now, ask)
    except LookupError:  #: the store's own word that it never held the span
        life.promise(UNHELD, False)
    else:
        life.promise(UNHELD, bool(stale_))
    life.live(on)


def unbarred(life: _Life, on: date) -> None:
    """The store holds a London line's daily bars but not the session before the day (17 November,
    the conformance job). The plan of the run must refuse, naming the line and the session, and
    never size an order from an older close."""
    line = next(x for x in life.begun(on) if x.venue == YARDSTICK.venue)
    before = venues.sessions(line.venue, on - timedelta(days=9), on)[-2]
    home = life.desk / "unbarred"
    with bars.writing(home / keeper.HOT) as round_:
        round_.daily(line, [b for b in life.market[line] if b.day < before])
    past = Kept(on, datetime.combine(on, time(), UTC), 1, {}, frozenset())
    record(home / keeper.DAILY / line.venue, past)
    try:
        conformance_parts.plan([line], line, on, {line.currency: Decimal(1)}, "0000", home)
    except ValueError as refusal:  #: the plan's own word that the session has no bar
        life.promise(UNBARRED, line.symbol in str(refusal) and f"{before}" in str(refusal))
    else:
        life.promise(UNBARRED, False)
    life.live(on)


def locked(life: _Life, on: date) -> None:
    """Another writer holds the live store when the keeper's one-minute round begins (17 November,
    "database is locked"). The round must be refused by name (NoRound) with nothing of it landed,
    and the next run, the store free, must go through."""
    lines = sorted((x for x in life.market if x.venue == YARDSTICK.venue), key=lambda x: x.symbol)
    opened = datetime.combine(on, time(9), UTC)  #: any day will do; the store ignores the calendar
    hot, now = life.desk / "locked-bars.db", opened + timedelta(hours=1)
    with bars.writing(hot) as round_:
        round_.five(YARDSTICK, [Five(opened, *(Decimal(1),) * 4, 1)])

    def ask(line: Line, at: datetime) -> tuple[Timed, ...]:
        return bars.timed(hot, line, keeper_live.MINUTES, at - timedelta(hours=1), at)

    refused, wait = False, bars.WAIT
    bars.WAIT = 0.05  #: the world will not wait the five seconds a real night does
    try:
        with closing(sqlite3.connect(hot, isolation_level=None)) as other:
            other.execute("BEGIN IMMEDIATE")
            try:
                keeper_live.minute_round(hot, lines, now, ask)
            except bars.NoRound as busy:  #: the store's own word that the round was not begun
                refused = str(hot) in str(busy)
    finally:
        bars.WAIT = wait
    keeper_live.minute_round(hot, lines, now, ask)
    life.promise(LOCKED, refused and bool(bars.five(hot, YARDSTICK, opened, now)))
    life.live(on)


def silent(life: _Life, on: date) -> None:
    """The broker says nothing to the first order it is sent (18 November, "timed out"). The
    desk must not guess what became of it: the kill switch goes on, the day ends in the alarm
    naming the order and the silence, nothing is booked; released, the same day then runs."""
    at = datetime.combine(on, time(7), UTC)
    failed = list[str]()

    def mute(order: Order | Sale) -> Report:
        failed.append(order.order_id)
        raise TimeoutError("timed out")

    life.pretend.place = mute  # type: ignore[method-assign]  # the world's broker, told to go quiet
    try:
        life.live(on)
    except book.Alarm as alarm:  #: the send path's own word that it does not know the order
        named = bool(failed) and failed[0] in str(alarm) and "timed out" in str(alarm)
        life.promise(SILENT, named and book.killed(life.desk) is not None)
        kill.release(life.desk, at, "SimCity releases it")
        del life.pretend.place  # the world's broker speaks again
        life.live(on)
    else:
        del life.pretend.place
        life.promise(SILENT, not failed)  #: no order was sent: nothing to be silent to


def slow(life: _Life, on: date) -> None:
    """The broker fills nothing, so each order sent is given the whole wait (19 November: 120 s
    each, the step killed at 240 s). The day's worst case, every order waiting out its time
    (paper.FILL_SECONDS) and the knock (paper.SECONDS), must end inside the step's time."""
    seen = len(life.pretend.submitted())
    life.live(on)
    sent = len(life.pretend.submitted()) - seen
    life.promise(SLOW, sent * paper.FILL_SECONDS + paper.SECONDS <= paper.STEP_SECONDS)


def gateway_silent(life: _Life, on: date) -> None:
    """The gateway says nothing when the conformance run's stop is to fire (17 November,
    "conformance-us", TimeoutError). The step must be recorded as failed, naming TimeoutError;
    the last step must still put the account back, so neither the book nor the broker holds a
    share and no order rests."""
    held = [x for x in life.begun(on) if x.venue == YARDSTICK.venue]
    line = next(x for x in LINES if x.retail and x.leverage == 1 and x.venue == YARDSTICK.venue)
    whole = life.market[held[0]]  #: the world's bars on a line the desk's own list knows
    home = life.desk / f"silent-{on}"
    with bars.writing(home / keeper.HOT) as round_:
        round_.daily(line, [b for b in whole if b.day < on])
    record(
        home / keeper.DAILY / line.venue,
        Kept(on, datetime.combine(on, time(), UTC), 1, {}, frozenset()),
    )
    refused = next(x for x in LINES if x.retail is False)
    run = conformance_parts.plan([line], refused, on, {line.currency: Decimal(1)}, "0000", home)
    price = run.second.price
    world = Pretend({line: (Bar(on, *(price,) * 4, 0), Bar(on + DAY, *(price,) * 4, 0))}, {})
    world.open(on)

    def quiet(_order: Order) -> str:
        raise TimeoutError("timed out")

    said: dict[str, str] = {}
    side = Side(home, world, lambda: (), quiet)
    failed = conformance_parts.live(side, run, said.__setitem__)
    answer = said.get(conformance_parts.TRIGGER, "")
    left = book.positions(home) or dict(world.holdings()) or world.stops()
    life.promise(
        STOP_SILENT, failed == [conformance_parts.TRIGGER] and "TimeoutError" in answer and not left
    )
    life.live(on)


def unreachable(life: _Life, on: date) -> None:
    """The paper Gateway's port is closed in the market's hours, outside its 03:00 restart (18
    November, conformance-us). The run must be refused, nothing sent, in the words that tell
    him the Gateway is his to look at; it asks the Gateway once and the desk goes on."""
    market, asked = "us", []
    if venues.sessions(conformance.MARKETS[market], on, on) != (on,):
        life.live(on)  #: the venue keeps a holiday: no run is due
        return
    now = venues.hours(conformance.MARKETS[market], on).open + timedelta(hours=2)

    def refused(talk: object, *_seconds: float) -> None:
        asked.append(talk)
        raise ConnectionRefusedError(f"port {paper.PORT} is closed")

    dial, paper.dial = paper.dial, refused  # type: ignore[assignment]
    try:
        well, words = conformance.trade(life.desk, market, lambda: now)
    finally:
        paper.dial = dial
    head = f"CONFORMANCE {market} NOT BEGUN, nothing sent: The paper Gateway does not answer: "
    life.promise(
        SHUT, not well and words.startswith(head + "its port is closed") and len(asked) == 1
    )
    life.live(on)
