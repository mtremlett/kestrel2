"""simcity_parts2 - SimCity's mishaps done to a desk's morning: shares behind its back, every line
opening at its low, the kill switch pulled; desk.simcity deals them out."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import replace
from datetime import UTC, date, datetime, time
from typing import TYPE_CHECKING

from desk import book, kill, orders

if TYPE_CHECKING:
    from desk.simcity import _Life


def _behind(life: _Life, on: date) -> None:
    """Shares the desk did not buy are at the broker before the day: the seed's number of them,
    on a line the desk does not hold (a sale beside its own shares takes the pretend broker's
    stop down with it, desk/broker.py). The desk sells them, or names them."""
    free = {line.symbol for line in life.market} - set(book.positions(life.desk))
    symbol = life.rng.choice(sorted(free))
    life.pretend.inject(symbol, life.rng.randint(1, 50))
    record = life.live(on)
    mine = [
        f.quantity for f in book.fills(life.desk) if f.order_id == f"{on:%Y%m%d}-stranger-{symbol}"
    ]
    sold = (bool(mine) and sum(mine) == 0) or symbol in record.mismatches
    life.promise("a position the desk did not make is sold or named", sold)


def _gapped(life: _Life, on: date) -> bool:
    """Every line opens at the day's low; the stop under each buy it fills is then moved under
    that fill, never left where the close put it. False when no buy filled: still owed."""
    life.market = {
        x: tuple(replace(b, open=b.low) if b.day == on else b for b in bars)
        for x, bars in life.market.items()
    }
    life.pretend.reopen(on, life.market)
    life.live(on)
    lines = {x.symbol: x for x in life.market}
    paid = {f.symbol: f.price for f in book.fills(life.desk) if f.quantity > 0 and f.day == on}
    due = {s: orders.stop_under(lines[s], p) for s, p in paid.items()}
    rests = {s: level for s, (_, level) in life.pretend.resting_stops().items()}
    fits = all(rests[s] == due[s] for s in rests & due.keys())
    life.promise("a stop rests where its fill puts it", fits)
    shares = book.positions(life.desk)  #: what is held, bought on the gap day or before it
    held = {f.symbol: f for f in book.fills(life.desk) if f.quantity > 0 and f.symbol in shares}
    before = {x.symbol: [b.close for b in bars if b.day < on] for x, bars in life.market.items()}
    for s in sorted(s for s, closes in before.items() if not closes):
        life.promise(f"FAULT line {s}: no bar before the gap day, its gap is unrunnable", False)
    shut = {s: closes[-1] for s, closes in before.items() if closes}
    sold = [
        orders.Order(
            f"gap-{s}",
            lines[s],
            shares[s],
            shut[s],
            life.rates[lines[s].currency],
            orders.stop_under(lines[s], shut[s]),
            session=on,
        )
        for s, f in held.items()
        if s in shut
    ]
    gone = [o.order_id for o in sold if orders.gapped(o, held[o.line.symbol].price, life.room)]
    life.promise("a gap down to the low leaves a stop's loss inside the gap limit", not gone)
    return bool(held)


def _killed(life: _Life, on: date) -> None:
    """The switch is pulled before the day and released after its record; then the drill."""
    at, reached = datetime.combine(on, time(7), UTC), life.pretend.submitted()
    said = kill.pull(life.desk, life.pretend, at, "SimCity pulls it for a day")
    life.live(on)
    quiet = life.pretend.submitted() == reached and "KILL SWITCH ON" in said.words()
    life.promise("with the kill switch on nothing reaches the broker, and the desk says so", quiet)
    kill.release(life.desk, at, "SimCity releases it")
    with suppress(kill.Failed):  #: a drill that failed is not on the record: said below
        kill.drill(life.desk, at)
    life.promise("the kill switch's drill is on the record", kill.drilled(life.desk, on))
