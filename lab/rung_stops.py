"""rung_stops - THE STOP-RULE RUNG (R-RUNNER-408): four rival stops on the same trades, each
sized by risk (size = risk budget / stop distance), so a trade's gain is its R: the move over
the distance to its first stop, less costs. Research only; the desk's stop is `orders.stop_under`
and nothing here changes it. Rivals and judging rule are pre-registered in docs/DECISIONS.md.

A trade is a fill at a bar's open and the rule's own exit at a later close. A bar whose low
reaches the resting stop sells there, or at its open if that gapped under it. The ATR is the
mean true range of the 20 bars before the fill (no bar of the fill's day or later is read).
"""

from __future__ import annotations

import enum
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from statistics import fmean

from desk.store import Bar
from lab import rung, rung_ci, rung_dsr
from lab.rung import Answer
from lab.rung_folds import Fold, Walked

ATR_BARS = 20


class Stop(enum.Enum):
    """The rival stops: the fixed fall of today's desk, two ATR distances, a chandelier trail."""

    FIXED = "fixed"  #: 10% under the fill; 30% on a 3x line
    ATR2 = "atr2"
    ATR3 = "atr3"
    CHANDELIER = "chandelier"  #: ATR3 from the fill, raised to 3 ATR under the highest high


TRIALS = len(Stop)  #: the count named for the luck correction


def atr(bars: Sequence[Bar]) -> Decimal:
    """The mean true range of the last ATR_BARS of these bars (at least ATR_BARS + 1)."""
    if len(bars) <= ATR_BARS:
        raise ValueError(f"{len(bars)} bars: the ATR({ATR_BARS}) needs {ATR_BARS + 1}")
    tail = bars[-ATR_BARS - 1 :]
    ranges = (
        max(b.high - b.low, abs(b.high - p.close), abs(b.low - p.close))
        for p, b in zip(tail, tail[1:], strict=False)
    )
    return Decimal(str(fmean(float(r) for r in ranges)))


def distance(stop: Stop, fill: Decimal, ranged: Decimal, leverage: int = 1) -> Decimal:
    """How far under the fill the first stop rests."""
    if stop is Stop.FIXED:
        return fill * Decimal("0.10") * leverage
    return ranged * (2 if stop is Stop.ATR2 else 3)


def gain(
    stop: Stop, history: Sequence[Bar], held: Sequence[Bar], cost: Decimal, leverage: int = 1
) -> Decimal:
    """One trade's R after costs: `history` the bars before the fill, `held` the bars from the
    fill's day to the rule's exit (the fill at the first open, the exit at the last close);
    `cost` the round trip as a fraction of the fill."""
    fill = held[0].open
    width = distance(stop, fill, atr(history) if stop is not Stop.FIXED else Decimal(0), leverage)
    if width <= 0 or width >= fill:
        raise ValueError(f"stop distance {width} on a fill at {fill}: no stop can rest there")
    level, high = fill - width, fill
    for bar in held[1:]:
        if bar.low <= level:
            return (min(bar.open, level) - fill - cost * fill) / width
        high = max(high, bar.high)
        if stop is Stop.CHANDELIER:
            level = max(level, high - width)
    return (held[-1].close - fill - cost * fill) / width


def judged(gains: Sequence[Decimal]) -> Side:
    """One side of a fold: the first rung's t and the interval rung's answer."""
    return Side(rung.standard_errors(gains) if len(gains) > 1 else None, rung_ci.judge(gains))


@dataclass(frozen=True)
class Side:
    """What a fold's side shows `Walked`: the t and the answer."""

    t: Decimal | None
    answer: Answer


def walk(folds: Sequence[Sequence[Decimal]]) -> Walked[Side]:
    """Each fold's gains judged beside the gains before it; the answer is the worst fold's."""
    return Walked(
        tuple(
            Fold(judged([g for f in folds[:i] for g in f]), judged(f)) for i, f in enumerate(folds)
        )
    )


def winner(rivals: dict[Stop, Sequence[Sequence[Decimal]]], spread: float) -> Stop | None:
    """The rival whose worst out-of-sample fold passes and whose pooled gains pass the deflated
    Sharpe over TRIALS (the highest t among those that do), or None: today's stop stays."""
    passed = {
        s: walk(f)
        for s, f in rivals.items()
        if walk(f).passed
        and rung_dsr.judge([g for x in f for g in x], TRIALS, spread) is Answer.PASS
    }
    return max(passed, key=lambda s: passed[s].worst.outside.t or 0) if passed else None
