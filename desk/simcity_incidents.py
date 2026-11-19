"""simcity_incidents - SCENARIOS SimCity lives because a night met them: each is a morning the
desk was put in, a promise it must keep there, and the day it then runs. R-RUNNER-246: a held
line has no bar for a session (a hole in the saved data), so the day has no record.
R-RUNNER-247: shares at the broker with a stop resting, bought beside the book (the 16 November
conformance run's), which the desk's sale refused as "the desk is long only"."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, time
from typing import TYPE_CHECKING

from desk import book, halt
from desk.broker import Fault
from desk.lines import YARDSTICK

if TYPE_CHECKING:
    from desk.simcity import _Life

HOLE = "a held line has no bar for the session"
LEFT = "shares the book lacks rest at the broker under a stop"
SOLD = "shares the book lacks, under a stop at the broker, are taken into the book and sold"
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


CANCELLED = "a buy is left working at the broker and cancelled there"
HALTED = "a halt is in force while the day's buys are asked for"
KEPT = "a buy the broker cancelled leaves the book with no shares the broker lacks"
STILL = "with a halt in force nothing is bought"
OUTSIDE = "a line no ISA can hold is never bought"


def cancelled(life: _Life, on: date) -> None:
    """Every buy is stranded working at the broker (the desk dies, is started, runs the day
    again) and what is left is cancelled there: the book may hold no share the broker lacks."""
    for line in life.market:
        life.pretend._faults[line.symbol] = Fault.STRAND  # noqa: SLF001 - the world's own broker
    life.live(on)
    life.pretend.cancel()
    broker = dict(life.pretend.holdings())
    life.promise(KEPT, all(broker.get(s) == n for s, n in book.positions(life.desk).items()))


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
