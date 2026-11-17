"""basket - THE LADDER'S BASKET (EASING 2, R-RUNNER-225, 227): a rule judged on all its lines
pooled as one portfolio at the desk's sizing, beside each line reported as it is.

The lines' priced trades (each line's first rung, sized by the desk's sizer from the one capital
number) are taken together as one trial of the rule: the first rung's own rule on the pooled
after-cost gains, the luck and the deflated Sharpe charged the rule's FAMILY of trials. A line
too thin to be judged alone adds its trades to the basket. Only the ladder's EASED switch
(`lab/verdict.py`) asks for it; the row it gives stands among the rule's lines in the table.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from typing import Any

from lab import deflated, rung, verdict
from lab.cell import Cell
from lab.rung import Answer, Verdict

NAME = ("BASKET", "all lines pooled")  #: the line and the venue of a basket's cell in the table


def pool(lines: Sequence[Verdict]) -> Verdict:
    """The lines' first-rung verdicts as one: every priced trade together, the first rung's rule
    read on their gains, the window from the earliest start to the latest end."""
    if not lines:
        raise ValueError("a basket needs a line to pool; none was given")
    first = lines[0].key.cell
    if {v.key.cell.strategy for v in lines} != {first.strategy}:
        raise ValueError(
            f"a basket is one rule's lines; given {[v.key.cell.strategy for v in lines]}"
        )
    window = Cell(
        first.strategy,
        first.line,
        min(v.key.cell.start for v in lines),
        max(v.key.cell.end for v in lines),
    )
    priced = tuple(p for v in lines for p in v.trades)
    key = replace(lines[0].key, cell=window)
    return replace(rung.verdict(key, priced), key=key, reproduced=lines[0].reproduced)


def row(tag: int | str, rule: str, lines: Sequence[Verdict], family: int) -> dict[str, Any]:
    """The basket's line of the results file: its answer, the rungs read from its pooled trades
    and its reasons, charged `family` trials, the rule's variants ever run."""
    basket = pool(lines)
    (one,) = deflated.judge([basket], family - 1)  #: every other trial of the family
    rungs = verdict.named(basket, one, rule)
    return {
        "set": tag,
        "cell": [rule, *NAME],
        "trials": family,
        "trades": len(basket.trades),
        "rungs": verdict.reported(rungs),
        "unrun": verdict.UNRUN,
        "every": all(answer is Answer.PASS for answer, _ in rungs.values()),
        "answer": basket.answer.name,
    }
