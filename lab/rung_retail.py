"""rung_retail - THE RETAIL RUNG (EASING 4, R-RUNNER-225, 229): does the basket beat simply
holding its market, on risk, as one retail trader would feel it?

The basket's days (a rule's lines pooled, `lab/basket.py`) and the market's days over the same
stretch, each a part of the capital, oldest first. Each is compounded into its STANDING: the
return over the stretch, the WORST FALL (the deepest drop of the compounded value from its
highest, as a part of that high) and the Sharpe (the mean of a day over its sample deviation; a
ratio, so a year's scale cancels between the two).

PRE-REGISTERED AND FROZEN (docs/DECISIONS.md, R-RUNNER-225, easing 4). PASS when the basket's
Sharpe is at least the market's, OR its return is at least KEEPS (80%) of the market's and its
worst fall at most FALL (60%) of the market's. Otherwise FAIL: the rung has a bar, not a doubt.
A basket that loses a little but falls half as far passes; one that matches the market's return
with its whole fall fails unless it matches its Sharpe as well.

FAILING FAIRLY (LAD-06). No day is a FAULT in the test; under MIN_TRADES days, THIN, never a
fail. Refused loudly: series of different lengths; a series with no spread (no Sharpe to read).

THE DAYS (`days`). The market's day is its close over the close before, in pounds at each day's
rate. The basket's day is the pounds its trades sold that day made after every cost, a part of the
capital (0 on a day none sold). Both run over the market's bars from the basket's first buy to its
last sale. The basket sits in cash between trades, which its fall and its return show fairly.

BEHIND THE LADDER'S ONE SWITCH. `grade` gives its answer only while `lab/verdict.py`'s EASED is
on, and None while off, so nothing else changes. `lab/basket.py` calls it. It declares no `RUNG`
because it reads the market's days, which the registry's rung (handed the first rung's verdict
alone) is not given.

PROVEN ALONE, by `tests/unit/test_lab_rung_retail.py`: known answers worked by hand.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from statistics import fmean, stdev

from desk.command import CAPITAL
from desk.lines import Line
from desk.store import Bar
from lab import rung, verdict
from lab.rung import MIN_TRADES, Answer, Rates, Verdict

KEEPS = 0.8  #: the part of the market's return the basket must keep, if it is to pass on risk
FALL = 0.6  #: the part of the market's worst fall the basket may take, if it is to pass on risk


@dataclass(frozen=True)
class Standing:
    """A series of days compounded: what it made, how far it fell, how steadily."""

    made: float  #: the return over the stretch
    fall: float  #: the worst fall, a part of the high it fell from
    sharpe: float  #: the mean day over its sample deviation


def standing(days: Sequence[float]) -> Standing:
    """The days' compounded return, worst fall and Sharpe; at least two days, with a spread."""
    if len(days) < 2:
        raise ValueError(f"{len(days)} days: a standing needs two")
    spread = stdev(days)
    if not spread:
        raise ValueError(f"{len(days)} days all of {days[0]}: no spread to read a Sharpe by")
    value = high = 1.0
    fall = 0.0
    for day in days:
        value *= 1 + day
        high = max(high, value)
        fall = max(fall, 1 - value / high)
    return Standing(value - 1, fall, fmean(days) / spread)


def beats(basket: Standing, market: Standing) -> bool:
    """The one decision: the market's Sharpe matched, or 80% of its return for 60% of its fall."""
    on_risk = basket.made >= KEEPS * market.made and basket.fall <= FALL * market.fall
    return basket.sharpe >= market.sharpe or on_risk


def judge(basket: Sequence[float], market: Sequence[float]) -> tuple[Answer, str]:
    """The rung's answer on the basket's days and the market's, paired, with its reason."""
    if len(basket) != len(market):
        raise ValueError(f"{len(basket)} basket days beside {len(market)} of the market's")
    if not basket:
        return Answer.FAULT, "no day of the basket to set beside its market"
    if len(basket) < MIN_TRADES:
        return Answer.THIN, f"{len(basket)} days: under {MIN_TRADES} the market is not beaten"
    ours, theirs = standing(basket), standing(market)
    why = (
        f"basket {ours.made:.1%} return, {ours.fall:.1%} worst fall, Sharpe {ours.sharpe:.3f}; "
        f"market {theirs.made:.1%}, {theirs.fall:.1%}, {theirs.sharpe:.3f}; its Sharpe, or "
        f"{KEEPS:.0%} of its return with {FALL:.0%} of its fall, asked"
    )
    return (Answer.PASS if beats(ours, theirs) else Answer.FAIL), why


@dataclass(frozen=True)
class Against:
    """The market a basket is set beside: its line, its bars oldest first, the rates."""

    line: Line
    bars: Sequence[Bar]
    rates: Rates


def days(basket: Verdict, against: Against) -> tuple[list[float], list[float]]:
    """The basket's days and its market's, paired, over the market's bars from the basket's first
    buy to its last sale; the market has no bar on a trade's day: refused."""
    first = min(p.held[0] for p in basket.trades)
    last = max(p.held[1] for p in basket.trades)
    bars = [b for b in against.bars if first <= b.day <= last]
    sold = {b.day: Decimal(0) for b in bars}
    for p in basket.trades:
        if p.held[1] not in sold:
            raise ValueError(f"{against.line.symbol} has no bar on {p.held[1]}, a day of a sale")
        sold[p.held[1]] += (p.gross - p.costs.total) / CAPITAL
    marks = [b.close * rung.rate(against.line, against.rates, b.day) for b in bars]
    market = [float(now / was - 1) for was, now in zip(marks, marks[1:], strict=False)]
    return [float(sold[b.day]) for b in bars[1:]], market


def grade(basket: Verdict, against: Against) -> tuple[Answer, str] | None:
    """The rung's answer on a pooled basket while EASED (None while not); a basket the first rung
    could not judge gives that answer, which it inherits."""
    if not verdict.EASED:
        return None
    if basket.answer in (Answer.FAULT, Answer.THIN):
        return basket.answer, "the first rung found too few trades, or none, to set beside it"
    return judge(*days(basket, against))
