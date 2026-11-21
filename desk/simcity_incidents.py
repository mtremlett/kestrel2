"""simcity_incidents - SCENARIOS SimCity lives because a night met them: each is a morning the
desk was put in, a promise it must keep there, and the day it then runs. R-RUNNER-246: a held
line has no bar for a session (a hole in the saved data), so the day has no record.
R-RUNNER-247: shares at the broker with a stop resting, bought beside the book (the 16 November
conformance run's), which the desk's sale refused as "the desk is long only". R-RUNNER-314: the
keeper's job failed on 17 November with a venue's daily bars a session short. R-RUNNER-323: the
18 November London run, whose buy the broker cancelled with nothing filled, so none were held.
R-RUNNER-315: the 16 November session the yardstick has no bar for, so the line is parked.
R-RUNNER-248: the 16 November afternoon the crash watch heard nothing of the market.
R-RUNNER-317: the keeper's live job failed on 17 November, its one-minute lines all stale.
R-RUNNER-316: the keeper's live job asked for one-minute bars of lines the store never held.
R-RUNNER-318: the 17 November conformance job, a London line with no bar of the session before.
R-RUNNER-319: the keeper's live job, 17 November, met "database is locked" on its store.
R-RUNNER-325: 18 November, the paper Gateway's port closed outside its restart: conformance-us."""

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
    halt,
    keeper,
    keeper_live,
    messenger,
    paper,
    venues,
    watch,
)
from desk.bars import Five
from desk.broker import Fault
from desk.keeper_rotate import Kept, record
from desk.lines import YARDSTICK, Line
from desk.spans import Timed

if TYPE_CHECKING:
    from desk.simcity import _Life

HOLE = "a held line has no bar for the session"
LEFT = "shares the book lacks rest at the broker under a stop"
SOLD = "shares the book lacks, under a stop at the broker, are taken into the book and sold"
CANCELLED = "the broker cancels every order of the day with nothing filled"
NAMED = "an order cancelled unfilled is named that day, and the book stays the broker's"
HALTED = "a halt is in force while the day's buys are asked for"
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
SHUT = (
    "a closed Gateway port outside its restart: the run is not begun, nothing sent, his to look at"
)
PROMISE = "a held line with no bar for a session is named when the day is refused"


def hole(life: _Life, on: date) -> None:
    """A held line's bar for the day is missing when the day ends. The desk must refuse to make
    a record from an older price, naming the line; when the bar arrives it runs the same day."""
    bars = {x: b for x, b in life.market.items() if any(d.day == on for d in b)}
    held = [x for x in bars if x.symbol in dict(life.pretend.stops())]
    if not held:
        life.live(on)
        return
    line, whole = held[0], life.market[held[0]]
    life.market[line] = tuple(bar for bar in whole if bar.day != on)
    try:
        life.live(on)
    except ValueError as refusal:  #: the desk's own word that the day has no record
        life.promise(PROMISE, line.symbol in str(refusal))
        life.market[line] = whole
        life.live(on)
    else:  #: a stop or a sale ended the holding that day: no close was owed
        life.market[line] = whole
        life.promise(PROMISE, line.symbol not in book.positions(life.desk))


def beside(life: _Life, on: date) -> None:
    """Shares the book never saw rest at the broker under their own stop. The desk must take
    them into the book (else its sale is refused, the desk being long only) and send the sale;
    after the day the book and the broker hold the same shares, a stop only under what is held."""
    free = sorted({x.symbol for x in life.market} - set(book.positions(life.desk)))
    symbol = life.rng.choice(free)
    level = min(b.low for x, bars in life.market.items() if x.symbol == symbol for b in bars)
    life.pretend.inject(symbol, life.rng.randint(1, 50))
    life.pretend.put_stop_back(symbol, level / 2)
    life.live(on)
    held = dict(life.pretend.holdings()).get(symbol, 0)
    taken = book.positions(life.desk).get(symbol, 0) == held
    life.promise(SOLD, taken and dict(life.pretend.stops()).get(symbol, 0) in (0, held))


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
    refused = {i for i, r in answers.items() if r and not r.fills} - told
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
    if YARDSTICK not in life.market:
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
    line = sorted((x for x in life.market if x.venue == YARDSTICK.venue), key=lambda x: x.symbol)[0]
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


def shut(life: _Life, on: date) -> None:
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
