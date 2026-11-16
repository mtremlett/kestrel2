"""eponymous_mansfield_rs_momentum - Mansfield's relative strength, ported as a rule under the
one template (SET 1 of the eponymous strategies, R-RUNNER-75). Its family is momentum. The paper
desk does not trade it.

AUTHOR: Stan Weinstein, after the relative-strength charts of Mansfield Stock Charts. SOURCE
(secondary; the book is of 1988, read here only through later accounts, and not checked): Weinstein,
Secrets for Profiting in Bull and Bear Markets (1988). The rule: divide a stock's price by the
market index's, divide that ratio by its own 52-week average, take one from it and multiply by
ten. That is the Mansfield RS. Above the zero line the stock beats the market; Weinstein buys a
stock when it crosses above zero and leaves it when it falls back under.

AUTHOR'S TEST: none that the book gives as a figure: Weinstein teaches the chart reading and
publishes no return for this line alone, so there is no published figure to quote. The ladder
measures the rule on the desk's data.

THE INDEX. A rule under the template sees one line, but the RS needs the market: this port takes
the desk's S&P 500 line (SPY) out of the bars given and measures every other line against it,
on the days both traded; with no SPY the rule raises. Weinstein's weeks are daily bars here: 52
weeks are 260 sessions. His other test, the stock above its rising 30-week average, is not ported
(one rule only).

The old desk is a quarry for the reading only; none of its code is copied.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal, localcontext
from typing import ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import (
    ARITHMETIC,
    CLOSES,
    ZERO,
    Decision,
    Declared,
    Rule,
    Timeframe,
    _run,
    _Window,
)

NAME = "mansfield_rs_momentum"
#: the index the stock is measured against, the days of 52 weeks, and Mansfield's scale
INDEX, YEAR, SCALE = "SPY", 260, Decimal(10)
_ONE = Decimal(1)


class MansfieldRs:
    """In while the Mansfield RS of the ratio bars shown is above zero."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, CLOSES)

    def __init__(self) -> None:
        self._ratios = _Window(YEAR)

    def step(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the template's call; this rule needs no holding
        """Shown the next bar of the stock's price over the index's: whether to be in."""
        self._ratios.add(bar.close)
        return self._ratios.full and (bar.close / self._ratios.mean() - _ONE) * SCALE > ZERO


def _ratio_bars(series: Sequence[Bar], index: Mapping[date, Decimal]) -> list[Bar]:
    """The stock's closes over the index's, on the days both have a bar."""
    return [
        Bar(b.day, r, r, r, r, b.volume)
        for b in series
        if b.day in index
        for r in (b.close / index[b.day],)
    ]


def decide(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """The rule's decision for every line but the index, on every day it shares with it."""
    if INDEX not in bars:
        raise ValueError(f"Mansfield RS needs the index line {INDEX} among the bars")
    index = {b.day: b.close for b in bars[INDEX]}
    with localcontext(ARITHMETIC):
        return tuple(
            d
            for symbol, series in bars.items()
            if symbol != INDEX
            for d in _run(NAME, MansfieldRs(), symbol, _ratio_bars(series, index))
        )


EPONYMOUS: Mapping[str, type[Rule]] = {NAME: MansfieldRs}
