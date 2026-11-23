"""tiers - WHICH LINES GET WHICH DATA, for 4,000+ tickers (DAT-01, DAT-05). Pure: data in, data out.

Tier A: held, signalled and watched names (in that order of claim), 1-minute from the broker,
as many as the line allowance. Tier B: breadth beyond it, US at 1 minute from one bought
vendor feed (only once a strategy needs it), London at 5 minutes from the broker; unbought US
breadth stays daily. Tier C: every ticker daily. Each tier's source sits behind one `Feed`, so
a vendor changes without touching a strategy. A name moves tier when its claim changes."""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from desk.lines import Line

#: IBKR's market-data lines the desk may use (his allowance, 14 November 2026).
LINE_ALLOWANCE = 100


class Tier(Enum):
    """The three kinds of data a line can have."""

    A = "A"  #: held, signalled or watched: live 1-minute from the broker
    B = "B"  #: breadth: US 1-minute from the vendor feed, London 5-minute from the broker
    C = "C"  #: daily bars only


@dataclass(frozen=True)
class Placement:
    """A line's tier and the finest bars kept live for it."""

    tier: Tier
    timeframe: str  #: the finest bars kept live for the line: "1m", "5m" or "1d"


class Feed(Protocol):
    """The one adapter a tier's source sits behind: a vendor changes here and nowhere else."""

    def bars(self, symbol: str, timeframe: str) -> list[object]:
        """The line's newest bars at that timeframe."""
        ...


@dataclass(frozen=True)
class Feeds:
    """The feed behind each tier, one adapter apiece."""

    a: Feed
    b_us: Feed | None  #: None until breadth is bought
    b_london: Feed
    c: Feed

    def for_placement(self, line: Line, placement: Placement) -> Feed:
        """The feed that serves a line at its placement."""
        if placement.tier is Tier.A:
            return self.a
        if placement.tier is Tier.C:
            return self.c
        if line.venue == "US":
            if self.b_us is None:
                raise LookupError(f"{line.symbol}: tier B US breadth placed but no feed bought")
            return self.b_us
        return self.b_london


def place(
    universe: Iterable[Line],
    *,
    held: Collection[str] = (),
    signalled: Collection[str] = (),
    watched: Collection[str] = (),
    allowance: int = LINE_ALLOWANCE,
    us_breadth_bought: bool = False,
) -> dict[str, Placement]:
    """Every line's placement. Claims fill tier A in the order held, signalled, watched (then
    symbol), up to the allowance; the rest go to B if a feed serves them, else to C."""
    lines = {line.symbol: line for line in universe}
    claims = [s for group in (held, signalled, watched) for s in sorted(set(group) & lines.keys())]
    top = list(dict.fromkeys(claims))[: max(allowance, 0)]
    out: dict[str, Placement] = {}
    for symbol, line in sorted(lines.items()):
        if symbol in top:
            out[symbol] = Placement(Tier.A, "1m")
        elif line.venue == "US":
            out[symbol] = Placement(Tier.B, "1m") if us_breadth_bought else Placement(Tier.C, "1d")
        else:
            out[symbol] = Placement(Tier.B, "5m")
    return out


def moves(
    before: Mapping[str, Placement], after: Mapping[str, Placement]
) -> dict[str, tuple[Placement | None, Placement]]:
    """The names whose placement changed (or that are new): symbol -> (was, now)."""
    return {s: (before.get(s), p) for s, p in after.items() if before.get(s) != p}
