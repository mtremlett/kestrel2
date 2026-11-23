"""published_case - THE SHAPE OF A KNOWN ANSWER: a rule's source, and the series on which the
published rule trades on stated bars and on no other (`lab/published.py` holds the rules to
them). A series is its closes; each bar opens on its close, and its high and low lie `reach`
either side of it, one bar a day from 1 January 2020, bars counted from 0; a rule that reads
more (volume, a day's range, the month) is given its bars whole."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from desk.store import Bar

FIRST = date(2020, 1, 1)
Trades = tuple[tuple[int, int | None], ...]  #: each trade's bars: bought, sold (None: held)


@dataclass(frozen=True)
class Case:
    """One series and the trades the published rule makes on it, with the working."""

    why: str  #: the working, by hand, from the rule's own words
    closes: tuple[Decimal, ...]
    trades: Trades  #: the bars the published rule buys and sells on, and no other
    reach: Decimal = Decimal("0.5")
    rows: tuple[Bar, ...] = ()  #: the bars whole, where the closes do not say enough

    def bars(self) -> tuple[Bar, ...]:
        """The series as bars: the whole bars given, or one a day from the closes."""
        r = self.reach
        days = enumerate(self.closes)
        return self.rows or tuple(
            Bar(FIRST + timedelta(n), c, c + r, c - r, c, 1000) for n, c in days
        )


@dataclass(frozen=True)
class Published:
    """A rule's source and the cases it must give, at least one of which trades."""

    source: str  #: the author and the work the rule is taken from
    cases: tuple[Case, ...]

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("a published rule with no source is nobody's rule")
        if not any(case.trades for case in self.cases):
            raise ValueError(
                f"{self.source}: on its known answers it buys nothing, which any code can do"
            )


def known(why: str, closes: Sequence[int | str], trades: Trades, reach: str = "0.5") -> Case:
    """A case of closes, at most `reach` either side for the day's high and low."""
    return Case(why, tuple(Decimal(c) for c in closes), trades, Decimal(reach))
