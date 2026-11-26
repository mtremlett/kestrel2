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

THE INDICATORS each rule is built of are held first to tables printed by somebody else
(`lab/published_tables.py`): no rule is proven while one of them gives another number.

A series is its closes (`lab/published_case.py`); bars are counted from 0. The
eponymous rules of `desk/eponymous_*.py` are written down the same way in
`lab/published_epon.py`, their own book: the ladder's first set is the desk's five.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import localcontext
from functools import cache

from desk import strategy
from desk.lines import LINES
from desk.store import Bar
from desk.strategy import ARITHMETIC, Action, _run
from lab import cell, rulebook
from lab.cell import Cell
from lab.published_case import Case as Case
from lab.published_case import Published as Published
from lab.published_case import Trades, known
from lab.published_epon import EPONYMOUS_PUBLISHED
from lab.published_tables import indicators

PUBLISHED: Mapping[str, Published] = {
    "rsi2_pullback": Published(
        "Connors and Alvarez, Short Term Trading Strategies That Work (2008): RSI-2",
        (
            known(
                "bar 201: RSI(2) 9.1, not under 5; 202: 3.2 buys; 203: 285 is under its 5-day "
                "average of 290.8 and holds; 204: 300 is over 291 and sells",
                [*range(100, 300), 300, 290, 280, 285, 300],
                ((202, 204),),
            ),
            known(
                "the same pullback under a falling 200-day average is never bought",
                [*range(400, 200, -1), 190, 180, 170, 185, 200],
                (),
            ),
            known(
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
            known(
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
            known(
                "highs of 10.5 for twenty days: bar 20's 10.4 does not clear them; bar 21's 11 "
                "clears bar 20's high of 10.9; bar 23's 9.4 is under the lows of 9.5, and sells",
                [10] * 20 + ["10.4", 11, 11, "9.4", "9.4"],
                ((21, 23),),
            ),
        ),
    ),
    "trend_50_200": Published(
        "the 50-day and 200-day moving-average cross (the golden cross), long only",
        (
            known(
                "bar 200: the 50-day at 102 crosses over the 200-day at 100.5; from bar 250 at "
                "50 the 50-day is 197 - 3j and the 200-day 124.75 - j/4, first under at j = 27",
                [100] * 200 + [200] * 50 + [50] * 40,
                ((200, 277),),
            ),
            known(
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
            known(
                "ten days with a true range of 2: bands 94 and 106. Bar 10 closes 110, over "
                "106, and buys; its lower band is 110 - 3 x 2.9 = 101.3. Bar 11 closes on it "
                "exactly and holds; the band is carried, and bar 12's 100 sells",
                [100] * 10 + [110, "101.3", 100],
                ((10, 12),),
                reach="1",
            ),
            known(
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
    """The rule's publication, once the indicators give their published tables and the desk's
    engine and the ladder's cell have both given its known answers on every series; refused,
    and not remembered, when any does not. A variant is held to its row's publication."""
    indicators()
    rule = PUBLISHED.get(name) or EPONYMOUS_PUBLISHED.get(name)
    row, _, setting = name.partition("[")
    if rule is None and setting:  #: a variant is its row's code at other settings (L17)
        return proven(row)
    if rule is None:
        raise ValueError(f"{name}: no published rule on file, so no code can be held to it")
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
    if name in strategy.STRATEGIES:
        decided = [d.action for d in strategy.decide({LINES[0].symbol: bars}) if d.strategy == name]
    else:  #: an eponymous rule is the rule book's class, under the template's one runner
        with localcontext(ARITHMETIC):
            decided = [d.action for d in _run(name, rulebook.rule(name)(), LINES[0].symbol, bars)]
    turns = [n for n, action in enumerate(decided) if action is not Action.HOLD]
    return tuple(zip(turns[::2], [*turns[1::2], None], strict=False))


def _cell(name: str, bars: Sequence[Bar]) -> Trades:
    at = {bar.day: n for n, bar in enumerate(bars)}
    record = cell.run(Cell(name, LINES[0], bars[0].day, bars[-1].day), bars)
    return tuple((at[t.bought], None if t.sold is None else at[t.sold]) for t in record.trades)
