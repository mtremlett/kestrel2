"""simcitynight - ONE NIGHT'S RECORD of SimCity, and the words it is told in."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from desk.broker import Fault


@dataclass(frozen=True)
class Night:
    """ONE NIGHT'S RECORD: what the desk's lives came to, added up over the worlds, the census,
    and every promise of the desk's that the night saw broken, with how many worlds broke it
    and the first of them. Green is no part bare and no promise broken."""

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
    left: tuple[str, ...]  #: the lines left out of a world on days before their first bar

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
        left = (
            f" Left out of a world until their first bar: {', '.join(self.left)}."
            if self.left
            else ""
        )
        return (
            f"SIMCITY {'GREEN' if self.green else 'RED'}, {self.at:%Y-%m-%d %H:%M} UTC. The desk "
            f"lived {self.worlds} seeded worlds, {self.days} days, at the pretend broker. Of its "
            f"orders {self.met[None]} met no fault; {met}. It died mid-send and was started "
            f"again {self.deaths} times. On {self.withheld} days the book was not the broker's "
            f"and the profit withheld. "
            f"{self.trips} round trips made {self.profit} pounds after every cost; holding the "
            f"market made {self.market}.{idle} Census: {len(self.census)} parts of the money "
            f"path, {len(self.bare)} with no scenario.{bare}{broken}{left}"
        )
