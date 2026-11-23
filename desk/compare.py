"""compare - HOW AN OLD STORE'S BARS MEET THE BARS THE STORE HOLDS (the operator's ruling of 15
November 2026: the store keeps as-traded prices, raw and immutable; adjusting is done on read).

An old store's bar for a moment the store holds is judged against the held bar, day by day:
- it agrees, within a vendor's rounding (AGREE);
- or it is the adjusted form of it: all four prices in one factor, the same factor on every bar
  of the day, and the factor explained by the line's recorded splits (any product of them, or
  their inverses) and the dividends a few months pay (DIVIDENDS). It is never written over the
  raw, and its day is not taken whole: the factor says how to read the raw as adjusted;
- or it is a real disagreement, counted by its day."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from statistics import median_low
from types import MappingProxyType
from typing import Protocol

from desk.lines import Line

#: Two sources' bars for one moment agree when no price of the four is further from the price
#: held than this part of the price given: each vendor rounds its own way. Volumes are not
#: compared, for each vendor counts the trades of its own venues.
AGREE = Decimal("0.0001")
#: Adjusted prices keep more decimals than as-traded ones; a factor holds within this fraction.
FACTOR = Decimal("0.001")
#: The lowest factor dividends alone explain: the old store's bars span months, and a dividend
#: lowers the bars before it by its yield (an FX rate, 0.66 to 0.81, is never one).
DIVIDENDS = Decimal("0.85")
Prices = Sequence[Decimal]  #: open, high, low, close


class Priced(Protocol):
    """A five-minute bar: the moment it starts and its prices."""

    @property
    def start(self) -> datetime:
        """The moment the bar starts."""

    @property
    def open(self) -> Decimal:
        """The first price."""

    @property
    def high(self) -> Decimal:
        """The highest price."""

    @property
    def low(self) -> Decimal:
        """The lowest price."""

    @property
    def close(self) -> Decimal:
        """The last price."""


@dataclass(frozen=True)
class Verdict:
    """How the bars an old store gave met the bars held."""

    met: int  #: bars that meet a bar held
    differ: tuple[date, ...]  #: the day of each that is no form of the bar held
    factors: Mapping[date, Decimal]  #: by day the old prices over the raw, where that is not 1


def _explained(line: Line, factor: Decimal) -> bool:
    """A factor the line's recorded splits, with the dividends of a few months, account for."""
    steps = {Decimal(1)}
    for _, ratio in line.splits:
        steps = {step * ratio**power for step in steps for power in (-1, 0, 1)}
    return any(DIVIDENDS <= factor / step <= 1 + FACTOR for step in steps)


def _factor(held: Prices, given: Prices) -> Decimal | None:
    """The one factor the given prices are the held ones in: 1 if they agree, None if none."""
    if all(abs(was - now) <= AGREE * now for was, now in zip(held, given, strict=True)):
        return Decimal(1)
    factor = given[3] / held[3]
    if abs(factor - 1) <= FACTOR:  # too near 1 to be an adjustment: a disagreement
        return None
    fits = all(
        abs(was * factor - now) <= FACTOR * now for was, now in zip(held, given, strict=True)
    )
    return factor if fits else None


def judge(line: Line, met: Iterable[tuple[Priced, Prices]]) -> Verdict:
    """Each bar the old store gave for a moment held (its start, the held prices, the given),
    judged by its UTC day: both venues trade within one."""
    days: dict[date, list[Decimal | None]] = {}
    for bar, held in met:
        prices = [bar.open, bar.high, bar.low, bar.close]
        days.setdefault(bar.start.date(), []).append(_factor(held, prices))
    differ, factors = list[date](), dict[date, Decimal]()
    for day, found in sorted(days.items()):
        fits = [factor for factor in found if factor is not None]
        usual = median_low(fits) if fits else Decimal(1)
        if usual != 1 and _explained(line, usual):
            factors[day] = usual
        else:
            usual = Decimal(1)
        agreeing = (f is not None and abs(f / usual - 1) <= FACTOR for f in found)
        differ.extend(day for same in agreeing if not same)
    return Verdict(sum(map(len, days.values())), tuple(differ), MappingProxyType(factors))


def doubt(met: int, differ: Sequence[date]) -> str | None:
    """Why bars that passed every check are still not kept, if they are not: no bar held to
    prove their clock, or half or more of those held differ, on the days named."""
    if not met:
        return "no bar is held for any of their moments to prove their clock; none kept"
    held = f"{len(differ)} of the {met} bars already held for the same moments differ"
    days = ", ".join(sorted({str(day) for day in differ}))
    other = f"{held}: another clock or another instrument (on {days}); none kept"
    return other if len(differ) * 2 > met else None
