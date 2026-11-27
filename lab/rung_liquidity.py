"""rung_liquidity - LIQUIDITY AND CAPACITY: could the desk make the rule's trades on the line
without being more than its own share of the market on the day?

The first rung (`lab/rung.py`) sizes every trade by the desk's one sizing home (`orders.size`, from
the one capital). This rung reads those shares and sets each leg against the line's volume on the
day it filled. A rule that needs more than `orders.LIQUIDITY` of a day's volume (1%, the desk's own
SIZ-10 number: one home) on any leg FAILS: its fills are not the market's prices but its own
impact. A day whose volume is recorded as nothing is the record's gap, not a market that did not
trade (634 of 2,063 history lines hold one): its leg is not read, and is counted in the reason;
with no leg read the rule is THIN, never failed on a gap. Its reason names the worst leg's day,
and whose volume it read: the judged bars' line, a proxy's where one stands in (`ladder_parts`).

CAPACITY, in the reason: about the largest pot at which the worst leg is still at the share, the
capital times the share over the worst leg's part of its day, as the shares grow with the pot
(whole shares and a fifth of the pot a holding, so near enough, never exact).

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


@dataclass(frozen=True)
class Depth:
    """The liquidity rung's answer on one cell, with the worst leg behind it."""

    worst: Decimal | None  #: the largest part of its day's volume any leg took; None: not read
    on: date | None  #: the day of that leg
    capacity: Decimal | None  #: pounds of pot at which the worst leg is at LIQUIDITY
    answer: Answer
    unread: int = 0  #: legs on a day with no volume recorded, left unread


def judge(first: rung.Verdict, bars: Sequence[Bar]) -> Depth:
    """The first rung's priced trades set against the volume of each leg's day; only its PASS
    is read, and lowered to FAIL where a leg takes more than LIQUIDITY of its day."""
    if first.answer is not Answer.PASS:
        return Depth(None, None, None, first.answer)
    volume = {bar.day: bar.volume for bar in bars}
    legs = [(p.shares, day) for p in first.trades for day in p.held]
    if missing := sorted({day for _, day in legs} - volume.keys()):
        raise ValueError(f"{first.key.cell}: no bar to read the volume of {missing[:3]}")
    parts = [(Decimal(shares) / volume[day], day) for shares, day in legs if volume[day]]
    unread = len(legs) - len(parts)
    if not parts:
        return Depth(None, None, None, Answer.THIN, unread)
    worst, on = max(parts)
    answer = Answer.FAIL if worst > LIQUIDITY else Answer.PASS
    return Depth(worst, on, CAPITAL * LIQUIDITY / worst, answer, unread)


def _judged(first: rung.Verdict, bars: Sequence[Bar], _rates: Rates) -> tuple[Answer, str]:
    """The liquidity rung as the ladder reads it: its answer, the worst leg and the capacity."""
    depth = judge(first, bars)
    if depth.unread and depth.worst is None:
        return depth.answer, f"no leg's day has a volume recorded ({depth.unread} legs)"
    if depth.worst is None or depth.capacity is None:
        return depth.answer, "the first rung did not pass it, so its volume is not read"
    n = depth.unread
    gaps = f"; {n} leg{'s' * (n > 1)} on a day with no volume recorded, not read" if n else ""
    return (
        depth.answer,
        f"its worst leg took {depth.worst:.4%} of {first.key.cell.line.symbol}'s volume on"
        f" {depth.on}, needs at most {LIQUIDITY:.0%}; capacity about {depth.capacity:,.0f} pounds"
        + gaps,
    )


def _unread(first: rung.Verdict) -> tuple[Answer, str]:
    """The rung without the bars: it cannot read a volume, so only an answer it keeps is given."""
    if first.answer is Answer.PASS:
        raise ValueError(f"{first.key.cell}: the liquidity rung reads the bars' volumes")
    return first.answer, "the first rung did not pass it, so its volume is not read"


RUNG = Rung("liquidity", f"no leg over {LIQUIDITY:.0%} of its day's volume", _unread, _judged)
