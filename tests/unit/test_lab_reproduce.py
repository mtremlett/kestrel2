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
from desk.orders import Settings
from desk.store import Bar
from lab import cell, published, reproduce, rung
from lab.cell import Cell
from lab.published import Case, Published
from lab.reproduce import Figure, Fill, Hand, Measure, Reproduction, Stated

VUSA = next(line for line in LINES if line.symbol == "VUSA")
#: The Turtles' rule, by hand (highs and lows half a point either side of each close): bar
#: 20's 11 clears the highs of 10.5 and buys; ten days at 20 put the lows at 19.5, so bar 31's
#: 19 sells; bar 32's 25 clears 20.5 and buys; bar 33's 18 is under bar 31's low of 18.5 and
#: sells. Filled at the close: 11 to 19 and 25 to 18, +72.72...% and -28%, one winner of two.
#: Filled at the next open (each bar opens on its close): 20 to 25 and 18 to 18, +25% and 0%.
#: In points of the price, as Connors prints a test: 8 - 7 = 1 at the close, 5 + 0 at the open.
CLOSES = (*[10] * 20, 11, *[20] * 10, 19, 25, 18, 18)
DAYS = venues.sessions("LSE", date(2020, 1, 2), date(2020, 2, 19))


def _bars() -> tuple[Bar, ...]:
    made = Case("", tuple(Decimal(c) for c in CLOSES), ()).bars()
    return tuple(replace(bar, day=day) for bar, day in zip(made, DAYS, strict=True))


def _figure(fill: Fill, *stated: tuple[Measure, str, str]) -> Figure:
    numbers = tuple(Stated(m, Decimal(value), Decimal(within)) for m, value, within in stated)
    source = ("breakout_20_10", "a planted author", VUSA, DAYS[0], DAYS[-1])
    return Figure(*source, fill, numbers, Hand.AUTHOR)


AT_CLOSE = (
    (Measure.TRADES, "2", "0"),
    (Measure.WINNERS, "50", "0"),
    (Measure.MEAN_GAIN, "22.36", "0.01"),  #: half of 72.72...% less 28% is 22.3636...%
    (Measure.NET_POINTS, "1", "0"),
)


def test_the_authors_own_figure_is_reproduced_counted_as_the_author_counted() -> None:
    bars = _bars()
    made = reproduce.reproduce(_figure(Fill.CLOSE, *AT_CLOSE), bars)
    measured = [str(round(found.measured, 6)) for found in made.found]
    assert made.reproduced and measured == ["2.000000", "50.000000", "22.363636", "1.000000"]
    kept = cell.key(made.key.cell, bars).rung("lab.reproduce")
    assert made.key == kept, "the code, this module's too, and the bars that made it"
    #: history before the period warms the rule, and a trade belongs to the period it was
    #: bought in: from bar 21 the second trade alone is the author's
    later = replace(_figure(Fill.CLOSE, (Measure.MEAN_GAIN, "-28", "0")), start=DAYS[21])
    assert reproduce.reproduce(later, bars).reproduced
    #: the same rule filled a day later is another result: the author's way of counting is
    #: part of the figure, and the same figure is not reproduced by it
    late = reproduce.reproduce(_figure(Fill.NEXT_OPEN, *AT_CLOSE), bars)
    out = [(Decimal(2), True), (Decimal(50), True), (Decimal("12.5"), False), (Decimal(5), False)]
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
    #: sources that disagree: the same is anywhere in the range they give, its ends included,
    #: and nowhere outside it; a range given upside down is no range
    ranges = (("12.5", "14", True), ("11", "12.5", True), ("12.51", "14", False))
    for low, high, same in (*ranges, ("11", "12.49", False)):
        between = Stated.between(Measure.MEAN_GAIN, Decimal(low), Decimal(high))
        ranged = replace(figure, stated=(between,), hand=Hand.SECOND)
        assert reproduce.reproduce(ranged, bars).reproduced is same, (low, high)
    for low, high in (("3", "2"), ("-Infinity", "Infinity")):
        with pytest.raises(ValueError, match=f"no range runs from {low} to {high}"):
            Stated.between(Measure.TRADES, Decimal(low), Decimal(high))
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


def test_the_first_rung_waits_for_the_authors_own_result(monkeypatch: pytest.MonkeyPatch) -> None:
    bars, figure = _bars(), _figure(Fill.CLOSE, *AT_CLOSE)
    record = cell.run(Cell(figure.strategy, VUSA, DAYS[0], DAYS[-1]), bars)

    def judge(*made: Reproduction) -> rung.Verdict:
        return rung.judge(record, bars, Settings(Decimal(10_000)), {}, made)

    made = reproduce.reproduce(figure, bars)
    #: no figure on file: judged, the verdict saying no author's result stands behind it; and
    #: a reproduction of a figure that is not on file stands behind nothing
    assert judge().reproduced == ()
    with pytest.raises(ValueError, match="a planted author is no figure on file for it"):
        judge(made)
    #: the figure on file: no verdict before it is reproduced, at either door of the rung
    monkeypatch.setattr(reproduce, "FIGURES", (figure,))
    with pytest.raises(ValueError, match="no verdict before its published.*a planted author"):
        judge()
    with pytest.raises(ValueError, match="no verdict before its published.*a planted author"):
        rung.verdict(record.key, ())
    with pytest.raises(ValueError, match="no verdict before"):  #: said before any price is missed
        dollars = Cell(figure.strategy, "SPY", DAYS[0], DAYS[-1])
        rung.judge(cell.run(dollars, bars), bars, Settings(Decimal(10_000)), {})
    assert judge(made, made).reproduced == (made,)
    assert rung.verdict(record.key, (), (made,)).reproduced == (made,)
    #: one made by other code than this, or over another period, is no reproduction of it;
    #: nor is one that leaves a stated number out, or moves how near is the same
    elsewhere = replace(made.key, cell=Cell("breakout_20_10", VUSA, *DAYS[1:3]))
    for key in (replace(made.key, code="older"), elsewhere):
        with pytest.raises(ValueError, match="another market or period.*or by other code"):
            judge(replace(made, key=key))
    wide = replace(made.found[2], stated=replace(made.found[2].stated, within=Decimal(99)))
    for found in ((), made.found[:2], (*made.found[:2], wide)):
        with pytest.raises(ValueError, match="not the figure's numbers"):
            replace(made, found=found)
    #: a rule of another author waits for nothing of this one's, and is not helped by it
    other = cell.run(Cell("rsi2_pullback", VUSA, DAYS[0], DAYS[-1]), bars)
    assert rung.judge(other, bars, Settings(Decimal(10_000)), {}).reproduced == ()
    with pytest.raises(ValueError, match="rsi2_pullback: a planted author is no figure on file"):
        rung.judge(other, bars, Settings(Decimal(10_000)), {}, (made,))
    #: a figure the code misses holds the rule up, each number out named; and every figure
    #: on file is waited for, not the first alone
    missed = reproduce.reproduce(_figure(Fill.NEXT_OPEN, *AT_CLOSE), bars)
    monkeypatch.setattr(reproduce, "FIGURES", (figure, missed.figure))
    with pytest.raises(ValueError, match=r"not reproduced.*: 12.5\d* against the author's 22.36"):
        judge(made, missed)
    with pytest.raises(ValueError, match="no verdict before"):
        judge(made)
    #: a replication standing in for the author is waited for alike, the verdict carries
    #: whose result stands behind it, and a number missed is called the replication's
    second, astray = (replace(one.figure, hand=Hand.SECOND) for one in (made, missed))
    monkeypatch.setattr(reproduce, "FIGURES", (second,))
    with pytest.raises(ValueError, match="no verdict before"):
        judge()
    (behind,) = judge(reproduce.reproduce(second, bars)).reproduced
    assert behind.figure.hand is Hand.SECOND
    with pytest.raises(ValueError, match="a planted author is no figure on file"):
        judge(made)  #: the author's own is not the replication on file
    monkeypatch.setattr(reproduce, "FIGURES", (astray,))
    with pytest.raises(ValueError, match="against the replication's 22.36"):
        judge(reproduce.reproduce(astray, bars))
