"""tiers - WHICH DATA EACH NAME GETS: Tier A (held, then signalled, then watched names: one-minute
bars from the broker, at most the line allowance), Tier B (US breadth, one-minute from one vendor,
bought only after the A-GATE: no feed yet, so a name placed there is a loud refusal), Tier C (every
other ticker, daily). A name over the allowance: London's falls to
fifteen minutes from the broker, the rest to C. Each tier's source sits in one Feed, so a vendor
changes there and no strategy notices. Tiers are recomputed from the sets of the day, so a name
moves as it gains or loses a position or signal."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from enum import Enum

from desk.bars_schema import Source
from desk.spans import DAILY, SPANS

ALLOWANCE = 100  #: the broker's market-data lines, as of 14 November 2026
LONDON_BREADTH = "15m"  #: the span of a London name beyond the broker's lines


class Tier(Enum):
    """A name's tier of data."""

    A = "A"
    B = "B"
    C = "C"


@dataclass(frozen=True)
class Feed:
    """Where a tier's bars come from and at what span: the one adapter a vendor change touches."""

    source: Source
    span: str

    def __post_init__(self) -> None:
        if self.span not in SPANS:
            raise ValueError(f"unknown span {self.span!r}")


FEEDS: Mapping[Tier, Feed] = {
    Tier.A: Feed(Source.IBKR, "1m"),
    Tier.C: Feed(Source.ARCHIVE, DAILY),
}  # Tier B has no feed until a strategy needs the vendor's: bought after the A-GATE
LONDON = Feed(Source.IBKR, LONDON_BREADTH)


@dataclass(frozen=True)
class Placement:
    """One name's tier and the feed that serves it."""

    tier: Tier
    feed: Feed


def feed_of(tier: Tier) -> Feed:
    """The feed of a tier; Tier B's is not bought yet and says so."""
    if tier not in FEEDS:
        raise NotImplementedError(f"tier {tier.value} has no feed: the vendor is bought after the A-GATE")
    return FEEDS[tier]


def place(
    tickers: Collection[str],
    held: Collection[str] = (),
    signalled: Collection[str] = (),
    watched: Collection[str] = (),
    london: Collection[str] = (),
    allowance: int = ALLOWANCE,
) -> dict[str, Placement]:
    """Each ticker's placement. Held names come first for the allowance, then signalled, then
    watched, each in name order; one over the allowance goes to London's breadth feed if listed
    there, else to Tier C. A held, signalled or watched name not in `tickers` is refused."""
    wanted = [n for group in (held, signalled, watched) for n in sorted(set(group))]
    stray = sorted(set(wanted) - set(tickers))
    if stray:
        raise ValueError(f"names with a position, signal or watch but no ticker: {stray}")
    top = list(dict.fromkeys(wanted))
    chosen = set(top[: max(allowance, 0)])
    out: dict[str, Placement] = {}
    for name in sorted(set(tickers)):
        if name in chosen:
            out[name] = Placement(Tier.A, FEEDS[Tier.A])
        elif name in top and name in set(london):
            out[name] = Placement(Tier.C, LONDON)
        else:
            out[name] = Placement(Tier.C, FEEDS[Tier.C])
    return out
