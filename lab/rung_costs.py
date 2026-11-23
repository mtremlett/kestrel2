"""rung_costs - THE LADDER'S SECOND RUNG: is the edge still there when the broker's costs are
charged, and when they turn out twice as dear?

The first rung (`lab/rung.py`) prices every trade by the desk's one cost model (`orders.charges`)
and asks whether the mean after costs is clear of chance. This rung reads those same priced trades
and asks the other question, how much of the edge the costs took. An edge that clears chance
by a hair after costs, but is gone if the spread is a little wider or the slippage a little worse,
rests on the cost estimate and not on the rule. Nothing is priced again here.

THE BREAK-EVEN (Novy-Marx and Velikov 2016, "A Taxonomy of Anomalies and Their Trading Costs",
Review of Financial Studies 29(1)): the multiple of the charged costs at which the mean return
falls to nothing, the mean gross return a trade over the mean cost a trade, both on the pounds the
trade took. A break-even of 4 means costs four times dearer would still leave the rule at nil.

PASSES when the first rung passes it AND its break-even is at least DOUBLED (2): the rule earns,
and would earn with every cost twice what the schedule says. FAILS when the first rung fails it,
or the break-even is under DOUBLED. Under MIN_TRADES it is THIN, and with no trades a FAULT:
this rung says what the first rung said, never a fail it could not have passed (LAD-06).

REFUSED LOUDLY: a trade charged nothing. A schedule that costs a trade nothing is a missing cost
model, not a cheap one, and a rung that read it would be judging gross returns as if net.

THE OLD DESK'S AUDIT OF 20 OCTOBER, each kept as a case that must fail (tests): LAD-09, a rung
skipped or read as passed when it had nothing to read (no trades is a fault, not a pass; a trade
without costs is refused); LAD-03, luck on a few trades (under 30 it is THIN, never PASS); LAD-08,
the stated line: of noise with no net edge, about the t-table's 2.5% pass, and no more.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, localcontext

from desk.strategy import ARITHMETIC
from lab import rung
from lab.cell import Key
from lab.rung import Answer, Priced, Rung

#: The costs the schedule states may be this many times as dear and the rule still earns.
DOUBLED = Decimal(2)


@dataclass(frozen=True)
class Costed:
    """The costs rung's answer on one cell, with the break-even behind it."""

    key: Key
    broker: str  #: whose schedule priced it
    breakeven: (
        Decimal | None
    )  #: the multiple of the costs at which the mean is nil; None: no trades
    t: Decimal | None  #: the first rung's, mean after costs in standard errors
    answer: Answer


def breakeven(trades: Sequence[Priced]) -> Decimal:
    """The mean gross return a trade over the mean cost a trade, on the pounds each took."""
    for one in trades:
        if one.costs.total <= 0:
            raise ValueError(f"{one.trade}: costs not charged, so no edge is judged after them")
    with localcontext(ARITHMETIC):
        gross = sum((one.gross / one.paid for one in trades), Decimal(0))
        return gross / sum((one.costs.total / one.paid for one in trades), Decimal(0))


def judge(first: rung.Verdict) -> Costed:
    """The first rung's priced trades read for how much of the edge the costs took."""
    if not first.trades:
        return Costed(first.key, first.broker, None, first.t, first.answer)
    multiple = breakeven(first.trades)
    answer = first.answer
    if answer is Answer.PASS and multiple < DOUBLED:
        answer = Answer.FAIL
    return Costed(first.key, first.broker, multiple, first.t, answer)


def _judged(first: rung.Verdict) -> tuple[Answer, str]:
    """The costs rung as the ladder reads it: its answer, and the break-even behind it in words."""
    costed = judge(first)
    if costed.breakeven is None:
        return costed.answer, "no trades priced, so no costs to double"
    return (
        costed.answer,
        f"the edge holds to {costed.breakeven:.1f} times the costs; needs {DOUBLED}",
    )


RUNG = Rung("costs", f"the edge survives costs {DOUBLED} times as dear", _judged)
