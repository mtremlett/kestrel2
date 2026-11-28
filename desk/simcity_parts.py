"""simcity_parts - SimCity's night and its worlds: the night's one record, with the words that
tell it, and a world's market dealt again from the saved lines; and its mishaps done to a desk's
morning (shares behind its back, every line opening at its low, the kill switch pulled), folded
in from simcity_parts2. desk.simcity gives them out."""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, time
from decimal import Decimal
from itertools import chain, pairwise
from typing import TYPE_CHECKING

from desk import book, kill, orders, venues
from desk.broker import Fault
from desk.lines import Line
from desk.orders import pennies
from desk.store import Bar

if TYPE_CHECKING:
    from desk.simcity import _Life

Archive = Mapping[Line, Sequence[Bar]]
MONTH = 20  #: sessions of a line's that stay together, in their saved order, in every world


@dataclass(frozen=True)
class Night:
    """ONE NIGHT'S RECORD: what the desk's lives came to over the worlds, the census, and every
    promise of the desk's the night saw broken. Green is no part bare and no promise broken."""

    at: datetime
    worlds: int  #: seeded worlds lived, each from holding nothing to its end or the desk's stop
    days: int  #: sessions lived in them all, each with its own day's record
    met: Mapping[Fault | None, int]  #: the orders at the broker's door, by the fault each met
    deaths: int  #: times the desk died mid-send and was started again
    withheld: int  #: days whose profit was withheld, the book not the broker's
    trips: int  #: round trips closed, in the worlds lived to their end
    profit: Decimal  #: pounds after every cost: the days' records added up
    market: Decimal  #: pounds the capital would have made simply holding the market
    idle: tuple[str, ...]  #: the rules that held no line in any world lived to its end
    census: Mapping[str, tuple[str, ...]]  #: each part of the money path, and what ran it
    broken: tuple[str, ...]
    left: tuple[str, ...]  #: lines left out of a world on days before their first bar

    @property
    def bare(self) -> tuple[str, ...]:
        """The parts no scenario ran."""
        return tuple(part for part, ran in self.census.items() if not ran)

    @property
    def green(self) -> bool:
        return not (self.bare or self.broken)

    def words(self) -> str:
        """One message, in plain English, for whoever must be told."""
        met = "; ".join(f"{fault.value}: {n}" for fault, n in self.met.items() if fault)
        idle = f" Rules that never held a line: {', '.join(self.idle)}." if self.idle else ""
        bare = f" NO SCENARIO for {', '.join(self.bare)}." if self.bare else ""
        broken = f" BROKEN: {'; '.join(self.broken)}." if self.broken else ""
        left = f" Left out until their first bar: {', '.join(self.left)}." if self.left else ""
        return (
            f"SIMCITY {'GREEN' if self.green else 'RED'}, {self.at:%Y-%m-%d %H:%M} UTC. The desk "
            f"lived {self.worlds} seeded worlds, {self.days} days, at the pretend broker. Of its "
            f"orders {self.met[None]} met no fault; {met}. It died mid-send and was started again "
            f"{self.deaths} times. On {self.withheld} days the book was not the broker's and the "
            f"profit withheld. {self.trips} round trips made {self.profit} pounds after every "
            f"cost; holding the market made {self.market}.{idle} Census: {len(self.census)} "
            f"parts of the money path, {len(self.bare)} with no scenario.{bare}{broken}{left}"
        )


def _market(archive: Archive, rng: random.Random) -> dict[Line, tuple[Bar, ...]]:
    """A WORLD'S MARKET: every saved line on its own days from its own first bar, each bar's shape
    kept against the close before it, to the penny; the days dealt again a MONTH at a time."""
    market = {}
    for line, bars in sorted(archive.items(), key=lambda item: item[0].symbol):
        steps = list(pairwise(bars))
        months = [steps[at : at + MONTH] for at in range(0, len(steps), MONTH)]
        rng.shuffle(months)
        made = list(bars[:1])
        level = made[0].close if made else Decimal(0)  #: the world's close, before rounding
        for kept, (before, bar) in zip(bars[1:], chain.from_iterable(months), strict=True):
            shape = (bar.open, bar.high, bar.low, bar.close)
            start, high, low, close = (pennies(p * level / before.close) for p in shape)
            made.append(Bar(kept.day, start, high, low, close, bar.volume))
            level *= bar.close / before.close
        market[line] = _restored(line, made)
    return market


def _restored(line: Line, bars: Sequence[Bar]) -> tuple[Bar, ...]:
    """The line with each session the store withdrew (#2088, VUAG 2019-05-23) lived as a still
    day at the close before it: the world goes on; HOLE and PARKED prove the day's refusal."""
    have = {bar.day: bar for bar in bars}
    for d in venues.sessions(line.venue, bars[0].day, bars[-1].day) if bars else ():
        if d not in have and d not in line.suspended:
            have[d] = Bar(d, *(have[max(k for k in have if k < d)].close,) * 4, 0)
    return tuple(have[d] for d in sorted(have))


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
