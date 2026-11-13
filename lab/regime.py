"""regime - PERIODS AND REGIMES: a strategy replayed in each stretch of its history and in each
kind of market weather, kept for the weather it earns in, and tagged when it trades outside it.

A rule can be real and still earn in one kind of market only: a breakout pays while prices
trend and bleeds while they churn. Judged on all its history together, the churn can drown
the trend and a real edge is thrown away; or the whole can pass and hide that one stretch
made all of it. So the window is replayed twice over, every replay judged by the first rung
(`lab/rung.py`), after the broker's costs, and all of them shown side by side.

THE PERIODS. The window in equal parts, oldest first, cut by the folds rung's own cutting
(`lab/folds.py`), each part a cell of its own: a trade held across a boundary belongs to
neither side. A period is shown and never picked from. It cannot come again, so no strategy
is kept for having earned in one, and none is failed here for having earned in one only:
the worst stretch of unseen history is the folds rung's to judge.

THE REGIMES. The weather is the caller's: each day's regime by name, as it was known at that
day's close. This module cannot see a label written with hindsight; that is the caller's to
keep, and the weather's own module's when it is built. A trade belongs to the regime of the
day it was decided on, the day `Trade.bought` names, which is all the desk could know when
it sent the order. Each regime's replay is the whole window's own priced trades bought under
it, so nothing is priced twice and every trade is in one regime exactly. No label after the
window's end is read.

NEVER FAILED FOR WORKING IN ONLY ONE. A strategy's home is every regime whose replay passed
the first rung. It is not failed here when it has a home, or when it passed on the whole
window: one regime is enough, and a regime it lost in does not fail it. A strategy that
passed only on all weather together (too few trades in any one regime) has no home: nothing
here says which weather made its result. Each replay carries the first rung's own answer:
too few trades in a regime is not enough evidence there, never a fail, and a regime no
trade was bought in reads as a test that tested nothing (`rung.Answer`): that replay shows
nothing of the rule, and it is no fault of the whole. `passed` and `home` say only where
it earned on enough trades; why it did not is the replay's own answer to give.

THE PRICE, counted elsewhere. Everything here is before any correction for luck. The whole
and every regime are separate looks at one rule, each a trial the luck rung counts
(`lab/luck.py`): a rule that passed in one regime of five was picked from six, and a regime
with no trade in it is a look all the same. `names` gives each look the name it is entered
under in the register (`lab/trials.py`) before the replay is run. And a weather is itself a
choice: every way of naming the days that was tried is as many looks again, which only the
caller can count, so the weather is fixed before any result.

THE TAG. A paper trade bought outside the strategy's home is tagged out of regime: in a
regime it failed in, one too thin to say, or weather the replay never saw; and every trade
of a strategy with no home. The tag refuses nothing. It is a fact kept on the trade, so
paper results in and out of the home regime can be told apart.

REFUSED, as faults in the test: a day of the window with no regime, or one whose name is
not one plain word; a window all one regime, which replays nothing (two or more are asked);
fewer than two periods, or more periods than the window has bars.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal

from desk.orders import Settings
from desk.store import Bar
from lab import cell, folds, rung, trials
from lab.cell import Cell
from lab.rung import Verdict

#: Each day's regime by name, as known at that day's close.
Weather = Mapping[date, str]
#: The fewest regimes, and the fewest periods, that make a replay.
LEAST = 2


@dataclass(frozen=True)
class Replay:
    name: str  #: the regime, or the period's first and last day
    bars: int  #: the window's bars in it
    verdict: Verdict  #: the first rung's, on the trades bought in it


@dataclass(frozen=True)
class Tag:
    bought: date  #: the day the trade was decided on
    regime: str
    outside: bool  #: out of regime: bought outside the strategy's home


@dataclass(frozen=True)
class Replayed:
    whole: Verdict  #: the first rung's on the whole window
    periods: tuple[Replay, ...]  #: oldest first
    regimes: tuple[Replay, ...]  #: by name

    @property
    def home(self) -> tuple[str, ...]:
        """Every regime whose replay passed the first rung."""
        return tuple(r.name for r in self.regimes if r.verdict.passed)

    @property
    def passed(self) -> bool:
        """Not failed here: it earned on the whole window, or in one regime or more."""
        return self.whole.passed or bool(self.home)

    @property
    def trials(self) -> tuple[Verdict, ...]:
        """The whole and every regime: the looks this strategy cost."""
        return (self.whole, *(r.verdict for r in self.regimes))

    @property
    def names(self) -> tuple[str, ...]:
        """Each look's name as a trial in the register, in the order of `trials`."""
        whole = trials.name(self.whole.key.cell)
        return (whole, *(f"{whole}, in {r.name}" for r in self.regimes))

    def tag(self, weather: Weather, bought: date) -> Tag:
        """The tag on a paper trade decided on that day, by the weather of that day."""
        name = _named(weather, bought)
        return Tag(bought, name, name not in self.home)


def judge(
    window: Cell,
    bars: Sequence[Bar],
    settings: Settings,
    fx: Decimal,
    weather: Weather,
    periods: int,
) -> Replayed:
    """The window replayed in so many periods and in each regime of its weather, every
    replay judged by the first rung; fx is pounds per unit of the line's currency."""
    days = [bar.day for bar in cell.shown(window, bars) if bar.day >= window.start]
    if not LEAST <= periods <= len(days):
        raise ValueError(
            f"{window}: {len(days)} bars in {periods} periods replay nothing: two periods or "
            "more, each a bar or more"
        )
    whole = rung.judge(cell.run(window, bars), bars, settings, fx)
    under: dict[str, list[date]] = {}
    for day in days:
        under.setdefault(_named(weather, day), []).append(day)
    if len(under) < LEAST:
        raise ValueError(
            f"{window}: all {sorted(under)}, which replays nothing: two regimes or more"
        )
    first, *rest = folds.cut(window, bars, periods - 1)
    parts = (*first, *(outside for _, outside in rest))
    return Replayed(
        whole,
        tuple(_period(part, bars, settings, fx) for part in parts),
        tuple(_regime(whole, name, under[name]) for name in sorted(under)),
    )


def _period(part: Cell, bars: Sequence[Bar], settings: Settings, fx: Decimal) -> Replay:
    """One part of the window, run and judged as a cell of its own."""
    record = cell.run(part, bars)
    name = f"{part.start} to {part.end}"
    return Replay(name, record.bars, rung.judge(record, bars, settings, fx))


def _regime(whole: Verdict, name: str, days: Sequence[date]) -> Replay:
    """The whole window's trades bought on the regime's days, judged alone. Its key is the
    whole's with the regime and its days told in, so each replay is a result of its own."""
    told = "\n".join([whole.key.data, name, *(day.isoformat() for day in days)])
    key = replace(whole.key, data=hashlib.sha256(told.encode()).hexdigest())
    bought = set(days)
    priced = tuple(p for p in whole.trades if p.trade.bought in bought)
    return Replay(name, len(days), rung.verdict(key, priced))


def _named(weather: Weather, day: date) -> str:
    name = weather.get(day, "")
    if name.split() != [name]:
        raise ValueError(f"{day} has no regime of one plain word: the weather gave {name!r}")
    return name
