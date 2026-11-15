"""rung_benchmark - THE BENCHMARK RUNG: does a strategy beat what simply holding its benchmark
would have made, over the same days in the market, by more than chance would give (R-RUNNER-123)?

EACH JUDGED TRADE IS A PAIR: its return after every cost (`rung.Priced.gain`, the first rung's own,
read from the tape of `lab/tape.py`) and the benchmark's return over the same stretch, its
open on the day the trade's buy filled to its open on the day the sale did, in pounds at each
day's rate and with no cost at all (the benchmark is held for nothing, so the rule must beat it
at its dearest). A sale by a stop falls in the day, not at its open: the benchmark is read to
that open all the same. The EXCESS is the one less the other.

JUDGED BY ITS INTERVAL, NOT ITS SIGN: the mean excess in `rung.T_PASS` standard errors either
side, the first rung's own bar. The rung passes a strategy whose WHOLE interval lies above nothing.

FAILING FAIRLY (LAD-06). Where the first rung found too few trades, or none, there is nothing
here to judge: its answer (THIN or FAULT) is given, measuring nothing. Refused loudly: a trade
day the benchmark has no bar on; excesses all alike, which leave no spread to judge by.

PROVEN ALONE (`tests/unit/test_lab_rung_benchmark.py`): a planted edge passes; noise passes at
about the stated rate and no more; a power curve over edge sizes; a rung with its decision
inverted is caught. The result is keyed by the tape's key and this module's code (`Key.rung`).
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from statistics import fmean

from desk.lines import Line
from desk.store import Bar
from lab import rung
from lab.cell import Key
from lab.rung import Answer, Priced, Rates, Verdict

ME = "lab.rung_benchmark"  #: this module as the cell knows it, for the key its result carries


@dataclass(frozen=True)
class Excess:
    """The rung's answer on one tape: its trades' excess over the benchmark, with its interval."""

    key: Key  #: the tape's key, made this rung's by its code
    broker: str  #: whose schedule priced the trades
    n: int  #: the trades judged; none where the first rung left nothing to judge
    mean: float | None  #: the mean excess of a trade over its benchmark
    low: float | None  #: the interval's lower end: `rung.T_PASS` standard errors under the mean
    high: float | None
    answer: Answer  #: PASS or FAIL, or the first rung's THIN or FAULT


def judge(verdict: Verdict, benchmark: Line, held: Sequence[Bar], rates: Rates) -> Excess:
    """The first rung's verdict, its trades set beside the benchmark's bars, oldest first."""
    key = verdict.key.rung(ME)
    if verdict.answer in (Answer.FAULT, Answer.THIN):
        return Excess(key, verdict.broker, 0, None, None, None, verdict.answer)
    marks = {bar.day: bar.open * rung.rate(benchmark, rates, bar.day) for bar in held}
    excess = [float(p.gain - _made(p, marks, benchmark)) for p in verdict.trades]
    mean, low, high = interval(excess)
    answer = Answer.PASS if beats(low) else Answer.FAIL
    return Excess(key, verdict.broker, len(excess), mean, low, high, answer)


def _made(priced: Priced, marks: Mapping[date, Decimal], benchmark: Line) -> Decimal:
    """What the benchmark made over the days the trade was held, as a part of its first open."""
    try:
        bought, sold = (marks[day] for day in priced.held)
    except KeyError as lost:
        raise ValueError(
            f"{benchmark.symbol} has no bar on {lost.args[0]}, a day of a trade"
        ) from lost
    return sold / bought - 1


def beats(low: float) -> bool:
    """The one decision: the whole interval above nothing."""
    return low > 0


def interval(excess: Sequence[float]) -> tuple[float, float, float]:
    """The mean and its interval, `rung.T_PASS` sample standard errors either side."""
    n, mean = len(excess), fmean(excess)
    spread = sum((x - mean) ** 2 for x in excess) / (n - 1)
    if not spread:
        raise ValueError(f"{n} excesses all of {mean}: no spread to judge them by")
    reach = float(rung.T_PASS) * math.sqrt(spread / n)
    return mean, mean - reach, mean + reach
