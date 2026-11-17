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

BEHIND THE LADDER'S ONE SWITCH. `graded` gives its answer only while `lab/verdict.py`'s EASED is
on, and None while off, so nothing else changes. Not yet called by the verdict (R-RUNNER-229,
Remains): it declares no `RUNG` because it reads the market's days, which the registry's rung
(handed the first rung's verdict alone) is not given.

PROVEN ALONE, by `tests/unit/test_lab_rung_retail.py`: known answers worked by hand.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from statistics import fmean, stdev

from lab import verdict
from lab.rung import MIN_TRADES, Answer

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


def graded(basket: Sequence[float], market: Sequence[float]) -> tuple[Answer, str] | None:
    """The rung's answer while the ladder is EASED; None while it is not."""
    return judge(basket, market) if verdict.EASED else None
