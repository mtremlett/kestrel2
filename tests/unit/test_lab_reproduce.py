"""The author's own result: a rule run on the author's market over the author's period, counted
as the author counted, and set beside the figure the author printed."""

from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import replace
from datetime import date
from decimal import Decimal
from typing import cast

import pytest

from desk import venues
from desk.lines import LINES
from desk.store import Bar
from lab import cell, published, reproduce
from lab.published import Case, Published
from lab.reproduce import Figure, Fill, Measure, Stated

VUSA = next(line for line in LINES if line.symbol == "VUSA")
#: The Turtles' rule, by hand (highs and lows half a point either side of each close): bar
#: 20's 11 clears the highs of 10.5 and buys; ten days at 20 put the lows at 19.5, so bar 31's
#: 19 sells; bar 32's 25 clears 20.5 and buys; bar 33's 18 is under bar 31's low of 18.5 and
#: sells. Filled at the close: 11 to 19 and 25 to 18, +72.72...% and -28%, one winner of two.
#: Filled at the next open (each bar opens on its close): 20 to 25 and 18 to 18, +25% and 0%.
CLOSES = (*[10] * 20, 11, *[20] * 10, 19, 25, 18, 18)
DAYS = venues.sessions("LSE", date(2020, 1, 2), date(2020, 2, 19))


def _bars() -> tuple[Bar, ...]:
    made = Case("", tuple(Decimal(c) for c in CLOSES), ()).bars()
    return tuple(replace(bar, day=day) for bar, day in zip(made, DAYS, strict=True))


def _figure(fill: Fill, *stated: tuple[Measure, str, str]) -> Figure:
    numbers = tuple(Stated(m, Decimal(value), Decimal(within)) for m, value, within in stated)
    return Figure("breakout_20_10", "a planted author", VUSA, DAYS[0], DAYS[-1], fill, numbers)


AT_CLOSE = (
    (Measure.TRADES, "2", "0"),
    (Measure.WINNERS, "50", "0"),
    (Measure.MEAN_GAIN, "22.36", "0.01"),  #: half of 72.72...% less 28% is 22.3636...%
)


def test_the_authors_own_figure_is_reproduced_counted_as_the_author_counted() -> None:
    bars = _bars()
    made = reproduce.reproduce(_figure(Fill.CLOSE, *AT_CLOSE), bars)
    measured = [str(round(found.measured, 6)) for found in made.found]
    assert made.reproduced and measured == ["2.000000", "50.000000", "22.363636"]
    kept = cell.key(made.key.cell, bars).rung("lab.reproduce")
    assert made.key == kept, "the code, this module's too, and the bars that made it"
    #: history before the period warms the rule, and a trade belongs to the period it was
    #: bought in: from bar 21 the second trade alone is the author's
    later = replace(_figure(Fill.CLOSE, (Measure.MEAN_GAIN, "-28", "0")), start=DAYS[21])
    assert reproduce.reproduce(later, bars).reproduced
    #: the same rule filled a day later is another result: the author's way of counting is
    #: part of the figure, and the same figure is not reproduced by it
    late = reproduce.reproduce(_figure(Fill.NEXT_OPEN, *AT_CLOSE), bars)
    out = [(Decimal(2), True), (Decimal(50), True), (Decimal("12.5"), False)]
    assert [(f.measured, f.same) for f in late.found] == out
    assert not late.reproduced
    at_open = (Measure.MEAN_GAIN, "12.5", "0")
    assert reproduce.reproduce(_figure(Fill.NEXT_OPEN, at_open), bars).reproduced
    #: a trade whose sale has no bar to fill on is not counted: the last bar taken away, the
    #: second trade's sale at the next open is gone, and one trade of +25% is left
    early = replace(_figure(Fill.NEXT_OPEN, at_open), end=DAYS[-2])
    (short,) = reproduce.reproduce(early, bars[:-1]).found
    assert (short.measured, short.same) == (Decimal(25), False)


def test_a_figure_is_missed_by_a_hair_and_met_on_its_edge() -> None:
    bars = _bars()
    for stated, same in (("12.39", False), ("12.4", True), ("12.6", True), ("12.61", False)):
        figure = _figure(Fill.NEXT_OPEN, (Measure.MEAN_GAIN, stated, "0.1"))
        assert reproduce.reproduce(figure, bars).reproduced is same, stated
    #: one number out is the whole figure out
    out = _figure(Fill.CLOSE, (Measure.TRADES, "3", "0"), (Measure.WINNERS, "50", "0"))
    assert not reproduce.reproduce(out, bars).reproduced


def test_nothing_is_called_a_reproduction_that_could_not_be_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bars, figure = _bars(), _figure(Fill.CLOSE, *AT_CLOSE)
    #: the author's market, whole: a session with no bar is refused, in the period or in the
    #: history that warms the rule before it, and so is a bar on a day that is no session
    saturday = replace(bars[21], day=date(2020, 2, 1))
    for holed, day in (
        (bars[:25] + bars[26:], DAYS[25]),
        (bars[:5] + bars[6:], DAYS[5]),
        (bars[:22] + (saturday,) + bars[22:], saturday.day),
    ):
        with pytest.raises(ValueError, match=f"1 days of VUSA.*the first {day}"):
            reproduce.reproduce(replace(figure, start=DAYS[20]), holed)
    #: no trade in the author's period is nothing to set beside the figure
    with pytest.raises(ValueError, match="no trade"):
        reproduce.reproduce(replace(figure, end=DAYS[19]), bars)
    #: a figure is an author's, with its numbers and how near is the same, fixed beforehand
    for wrong, why in (
        ({"source": " "}, "nobody's"),
        ({"stated": ()}, "states no number"),
        ({"stated": figure.stated[:1] * 2}, "twice"),
        ({"stated": (Stated(Measure.TRADES, Decimal(2), Decimal(-1)),)}, "nearer than"),
        ({"stated": (Stated(Measure.TRADES, Decimal(2), Decimal("Infinity")),)}, "no number"),
        ({"strategy": "a rule of no author"}, "no published rule"),
    ):
        with pytest.raises(ValueError, match=why):
            replace(figure, **wrong)
    #: every figure on file is of a rule on file; and code that is not the published rule
    #: reproduces nothing
    assert all(kept.strategy in published.PUBLISHED for kept in reproduce.FIGURES)
    monkeypatch.delitem(cast(MutableMapping[str, Published], published.PUBLISHED), figure.strategy)
    published.proven.cache_clear()
    with pytest.raises(ValueError, match="no published rule on file"):
        reproduce.reproduce(figure, bars)
