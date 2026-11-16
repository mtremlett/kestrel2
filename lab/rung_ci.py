"""rung_ci - THE LADDER'S THIRD RUNG: is the mean gain of a rule's trades, after costs, clear
of nothing by its whole confidence interval?

The interval is the mean plus and minus T_PASS standard errors (Wasserman, All of Statistics,
6.3.2), the sample's own deviation estimating the spread. The rung answers on the whole interval,
not on a sign: wholly above nothing PASS, wholly below FAIL, holding nothing DOUBT. Under MIN_TRADES
gains it is THIN, never a fail; no gain at all is a FAULT in the test (LAD-06, LAD-09); gains
with no spread are refused loudly. Its two errors and thirty trades are the first rung's own
(`lab/rung.py`), read from there.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal, localcontext

from desk.strategy import ARITHMETIC
from lab import rung
from lab.rung import MIN_TRADES, T_PASS, Answer, Rung


def interval(gains: Sequence[Decimal]) -> tuple[Decimal, Decimal]:
    """The mean gain less and plus T_PASS standard errors; at least two gains, with a spread."""
    n = len(gains)
    if n < 2:
        raise ValueError(f"{n} gains: an interval needs two")
    with localcontext(ARITHMETIC):
        mean = sum(gains, Decimal(0)) / n
        spread = sum(((g - mean) ** 2 for g in gains), Decimal(0)) / (n - 1)
        if not spread:
            raise ValueError(f"{n} gains all of {mean}: no spread to judge them by")
        reach = T_PASS * (spread / n).sqrt()
        return mean - reach, mean + reach


def judge(gains: Sequence[Decimal]) -> Answer:
    """The rung's answer on the gains of the judged trades."""
    if not gains:
        return Answer.FAULT
    if len(gains) < MIN_TRADES:
        return Answer.THIN
    low, high = interval(gains)
    if low > 0:
        return Answer.PASS
    return Answer.FAIL if high < 0 else Answer.DOUBT


def _judged(first: rung.Verdict) -> tuple[Answer, str]:
    """The interval rung as the ladder reads it: its answer, and the interval in words."""
    answer = judge(first.gains)
    if answer in (Answer.FAULT, Answer.THIN):
        return answer, f"{len(first.gains)} gains: under {MIN_TRADES} the interval is not read"
    low, high = interval(first.gains)
    return answer, f"the mean gain lies in {low:.4f} to {high:.4f} after costs; needs above nothing"


RUNG = Rung("ci", f"the mean gain is clear of nothing by {T_PASS} standard errors", _judged)
