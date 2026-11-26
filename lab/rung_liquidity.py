"""rung_liquidity - LIQUIDITY AND CAPACITY: could the desk make the rule's trades on the line
without being more than its own share of the market on the day?

The first rung (`lab/rung.py`) sizes every trade by the desk's one sizing home (`orders.size`, from
the one capital). This rung reads those shares and sets each leg against the line's volume on the
day it filled. A rule that needs more than `orders.LIQUIDITY` of a day's volume (1%, the desk's own
SIZ-10 number: one home) on any leg FAILS: its fills are not the market's prices but its own
impact. A leg on a day of no volume is more than any share. Its reason names the worst leg's day.

CAPACITY, in the reason: the largest pot at which the worst leg is still at the share, the capital
times the share over the worst leg's part of its day, since the shares grow with the pot.

IT ONLY LOWERS A PASS (as the costs rung does): a cell the first rung did not pass keeps the first
rung's answer, FAIL, THIN or FAULT, and nothing is read for it (LAD-06). The bars and reasons are
in `docs/DECISIONS.md` (26 Nov, before any EPON result).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from desk.command import CAPITAL
from desk.orders import LIQUIDITY
from desk.store import Bar
from lab import rung
from lab.rung import Answer, Rates, Rung

NONE_TRADED = Decimal("Infinity")  #: a leg's part of a day on which nothing traded


@dataclass(frozen=True)
class Depth:
    """The liquidity rung's answer on one cell, with the worst leg behind it."""

    worst: Decimal | None  #: the largest part of its day's volume any leg took; None: not read
    on: date | None  #: the day of that leg
    capacity: Decimal | None  #: pounds of pot at which the worst leg is at LIQUIDITY
    answer: Answer


def judge(first: rung.Verdict, bars: Sequence[Bar]) -> Depth:
    """The first rung's priced trades set against the volume of each leg's day; only its PASS
    is read, and lowered to FAIL where a leg takes more than LIQUIDITY of its day."""
    if first.answer is not Answer.PASS:
        return Depth(None, None, None, first.answer)
    volume = {bar.day: bar.volume for bar in bars}
    legs = [(p.shares, day) for p in first.trades for day in p.held]
    if missing := sorted({day for _, day in legs} - volume.keys()):
        raise ValueError(f"{first.key.cell}: no bar to read the volume of {missing[:3]}")
    parts = [
        (Decimal(shares) / volume[day] if volume[day] else NONE_TRADED, day) for shares, day in legs
    ]
    worst, on = max(parts)
    capacity = CAPITAL * LIQUIDITY / worst
    return Depth(worst, on, capacity, Answer.FAIL if worst > LIQUIDITY else Answer.PASS)


def _judged(first: rung.Verdict, bars: Sequence[Bar], _rates: Rates) -> tuple[Answer, str]:
    """The liquidity rung as the ladder reads it: its answer, the worst leg and the capacity."""
    depth = judge(first, bars)
    if depth.worst is None or depth.capacity is None:
        return depth.answer, "the first rung did not pass it, so its volume is not read"
    if depth.worst == NONE_TRADED:
        return depth.answer, f"a leg on {depth.on}, a day of no volume; capacity no pounds"
    return (
        depth.answer,
        f"its worst leg took {depth.worst:.4%} of the day's volume on {depth.on}, needs at most"
        f" {LIQUIDITY:.0%}; capacity {depth.capacity:,.0f} pounds",
    )


def _unread(first: rung.Verdict) -> tuple[Answer, str]:
    """The rung without the bars: it cannot read a volume, so only an answer it keeps is given."""
    if first.answer is Answer.PASS:
        raise ValueError(f"{first.key.cell}: the liquidity rung reads the bars' volumes")
    return first.answer, "the first rung did not pass it, so its volume is not read"


RUNG = Rung("liquidity", f"no leg over {LIQUIDITY:.0%} of its day's volume", _unread, _judged)
