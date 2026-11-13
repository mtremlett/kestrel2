"""published - THE PUBLISHED RULES: a strategy is judged only by code proven to be the rule
its author published (STR-12).

A rule that is coded wrongly and then fails has told nothing about the rule: the old desk
threw strategies away on its own mistakes. So before the first rung (`lab/rung.py`) gives any
verdict on a strategy, the code is held to the publication. Each rule the ladder judges is
written down here with its author's source and its known answers: short series of prices on
which the published rule, worked by hand from its own words, buys and sells on stated bars
and on no other. The same series and days are pinned, with their working, in the
strategies' own contract test. Two pieces of code must give exactly those trades: the desk's
own engine (`strategy.decide`), which is what would trade, and the ladder's cell
(`lab/cell.py`), which is what is judged: the fast grid's answer wherever the grid gives
one, so each rule has a series with a trade that the grid answers itself (a tie it refuses
goes to the desk's engine).

Code that gives any other trade on any series is not the published rule, and it is refused
loudly: a fault in the test, never a verdict on the strategy. A rule with nothing written
here cannot be judged at all, so a new rule reaches the ladder only with its source and its
known answers. A handful of short series proves the rule's plain cases and the ties named
below, and no more: it is the gate at the ladder's door, not the whole proof, which is the
strategies' contract test on long walks.

A series is its closes; each bar opens on its close, and its high and low lie `reach` either
side of it, one bar a day. Bars are counted from 0.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from functools import cache

from desk import strategy
from desk.lines import LINES
from desk.store import Bar
from desk.strategy import Action
from lab import cell
from lab.cell import Cell

Trades = tuple[tuple[int, int | None], ...]  #: each trade's bars: bought, sold (None: held)
_FIRST = date(2020, 1, 1)


@dataclass(frozen=True)
class Case:
    why: str  #: the working, by hand, from the rule's own words
    closes: tuple[Decimal, ...]
    trades: Trades  #: the bars the published rule buys and sells on, and no other
    reach: Decimal = Decimal("0.5")

    def bars(self) -> tuple[Bar, ...]:
        days, r = enumerate(self.closes), self.reach
        return tuple(Bar(_FIRST + timedelta(n), c, c + r, c - r, c, 1000) for n, c in days)


@dataclass(frozen=True)
class Published:
    source: str  #: the author and the work the rule is taken from
    cases: tuple[Case, ...]

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("a published rule with no source is nobody's rule")
        if not any(case.trades for case in self.cases):
            raise ValueError(
                f"{self.source}: on its known answers it buys nothing, which any code can do"
            )


def _case(why: str, closes: Sequence[int | str], trades: Trades, reach: str = "0.5") -> Case:
    return Case(why, tuple(Decimal(c) for c in closes), trades, Decimal(reach))


PUBLISHED: Mapping[str, Published] = {
    "rsi2_pullback": Published(
        "Connors and Alvarez, Short Term Trading Strategies That Work (2008): RSI-2",
        (
            _case(
                "bar 201: RSI(2) 9.1, not under 5; 202: 3.2 buys; 203: 285 is under its 5-day "
                "average of 290.8 and holds; 204: 300 is over 291 and sells",
                [*range(100, 300), 300, 290, 280, 285, 300],
                ((202, 204),),
            ),
            _case(
                "the same pullback under a falling 200-day average is never bought",
                [*range(400, 200, -1), 190, 180, 170, 185, 200],
                (),
            ),
            _case(
                "bar 209 falls to 110 with RSI(2) at 2.2, but the 200 days sum to 22,000: a "
                "close exactly on its average is not above it",
                [100] * 200 + [150, 200, 250, 300, 350, 410, 410, 410, 410, 110],
                (),
            ),
        ),
    ),
    "bollinger_pullback": Published(
        "Bollinger's bands at his settings, 20 days and 2 deviations (Bollinger on Bollinger "
        "Bands, 2001): a close under the lower band bought, one over the middle sold",
        (
            _case(
                "bar 20: mean 9.95, two deviations 0.436, so 9 is under 9.514 and buys; 21: "
                "9.5 is under the mean of 9.925 and holds; 22: 10.5 is over 9.95 and sells",
                [10] * 20 + [9, "9.5", "10.5"],
                ((20, 22),),
            ),
        ),
    ),
    "breakout_20_10": Published(
        "Faith, Way of the Turtle (2007): the Turtles' system 1, on the close",
        (
            _case(
                "highs of 10.5 for twenty days: 10.4 does not clear them and 11 does, on bar "
                "21; bar 23's 9.4 is under the lows of 9.5 ten days before, and sells",
                [10] * 20 + ["10.4", 11, 11, "9.4", "9.4"],
                ((21, 23),),
            ),
        ),
    ),
    "trend_50_200": Published(
        "the 50-day and 200-day moving-average cross (the golden cross), long only",
        (
            _case(
                "bar 200: the 50-day at 102 crosses over the 200-day at 100.5; from bar 250 at "
                "50 the 50-day is 197 - 3j and the 200-day 124.75 - j/4, first under at j = 27",
                [100] * 200 + [200] * 50 + [50] * 40,
                ((200, 277),),
            ),
            _case(
                "a 50-day already above when both averages first exist is no cross it saw",
                [*range(100, 360)],
                (),
            ),
        ),
    ),
    "supertrend_10_3": Published(
        "Seban's Supertrend, 10 days and 3 average true ranges, its bands carried as "
        "KivancOzbilgic's reference script carries them",
        (
            _case(
                "ten days with a true range of 2: bands 94 and 106. Bar 10 closes 110, over "
                "106, and buys; its lower band is 110 - 3 x 2.9 = 101.3. Bar 11 closes on it "
                "exactly and holds; the band is carried, and bar 12's 100 sells",
                [100] * 10 + [110, "101.3", 100],
                ((10, 12),),
                reach="1",
            ),
            _case(
                "the same with bar 11 at 102, clear of the band of 101.3, and held: no tie, "
                "so the fast grid answers this one itself and is held to the rule too",
                [100] * 10 + [110, 102, 100],
                ((10, 12),),
                reach="1",
            ),
        ),
    ),
}


@cache
def proven(name: str) -> Published:
    """The rule's publication, once the desk's engine and the ladder's cell have both given
    its known answers on every series; refused, and not remembered, when either does not."""
    if name not in PUBLISHED:
        raise ValueError(f"{name}: no published rule on file, so no code can be held to it")
    rule = PUBLISHED[name]
    for case in rule.cases:
        bars = case.bars()
        for whose, made in (
            ("the desk's engine", _desk(name, bars)),
            ("the cell", _cell(name, bars)),
        ):
            if made != case.trades:
                raise ValueError(
                    f"{name}: {whose} is not the published rule ({rule.source}). It trades "
                    f"bars {made} where the rule trades {case.trades}: {case.why}"
                )
    return rule


def _desk(name: str, bars: Sequence[Bar]) -> Trades:
    decided = [d.action for d in strategy.decide({LINES[0].symbol: bars}) if d.strategy == name]
    turns = [n for n, action in enumerate(decided) if action is not Action.HOLD]
    return tuple(zip(turns[::2], [*turns[1::2], None], strict=False))


def _cell(name: str, bars: Sequence[Bar]) -> Trades:
    at = {bar.day: n for n, bar in enumerate(bars)}
    record = cell.run(Cell(name, LINES[0], bars[0].day, bars[-1].day), bars)
    return tuple((at[t.bought], None if t.sold is None else at[t.sold]) for t in record.trades)
