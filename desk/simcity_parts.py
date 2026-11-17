"""simcity_parts - SimCity's night and its worlds: the night's one record, with the words that
tell it, and a world's market dealt again from the saved lines. desk.simcity gives them out."""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from itertools import chain, pairwise

from desk.broker import Fault
from desk.lines import Line
from desk.orders import pennies
from desk.store import Bar

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
        market[line] = tuple(made)
    return market
