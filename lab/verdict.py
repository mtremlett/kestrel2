"""verdict - THE LADDER'S VERDICT ON ONE CELL: every rung's answer with its reason, the rungs
not run with theirs, and the one rule over them (`lab/ladder.py` holds the spec this builds)."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from desk.command import CAPITAL
from desk.lines import Line
from desk.orders import Settings
from desk.store import Bar
from lab import cell, deflated, folds, luck, market, reproduce, rung, shuffle
from lab.cell import Cell
from lab.deflated import Deflated
from lab.reproduce import Reproduction
from lab.rung import Answer, Rates, Verdict

#: The rules trade a line five to ten times a year and a fold is asked for thirty trades: so
#: the window in three parts, two of them folds, each a trial the luck rung counts.
FOLDS = 2
#: Rungs that are built and that this set cannot yet be run through, each with why.
UNRUN = {
    "regime": "the weather that names each day's regime is not built (REG-01)",
    "plateau": "the published rules carry no settings to choose among yet",
    "stress": "it gives pounds lost and never a pass; the loss limit to judge them by is not set",
}
NO_FIGURE = "no author's figure is on file for the rule: no published result stands behind it"
NO_FOLDS = "the folds rung cannot yet hand an author's result to its folds"
#: A rule trades a line five to ten times a year and wants 200 sessions to warm up: a line of
#: fewer bars than those and a year's trading has made no trade yet, which says nothing of the rule.
MIN_BARS = 200 + 252
Pair = tuple[Answer, str]
Judged = dict[str, Pair]  #: each rung's answer on a cell, and its reason


def judge(
    c: Cell,
    own: Sequence[Bar],
    beside: Line,
    held: Sequence[Bar],
    pounds: Rates,
    count: int,
    made: Sequence[Reproduction],
) -> dict[str, Any]:
    """Every rung's answer with its reason, the rungs not run with theirs, the verdict's."""
    try:
        reproduce.settled(c.strategy, made)
    except ValueError as missed:  #: the rule as coded is not the author's: no verdict on ours
        return {"rungs": {"reproduce": [Answer.FAIL.name, str(missed)]}, "every": False}
    unrun = UNRUN | ({"folds": NO_FOLDS} if made else {"reproduce": NO_FIGURE})
    settings = Settings(CAPITAL)
    verdict = rung.judge(cell.run(c, own), own, settings, pounds, made)
    if verdict.answer is Answer.FAULT and len(own) < MIN_BARS:
        raise ValueError(f"{c.line.symbol}: {len(own)} bars, no trade yet; waits on {MIN_BARS}")
    (one,) = deflated.judge([verdict], count - 1)  #: every other trial the register holds
    rungs = _named(verdict, one)
    if made:
        said = "; ".join(f"{m.figure.hand.value} result, {m.figure.source}" for m in made)
        rungs["reproduce"] = (Answer.PASS, f"reproduced: {said}")
    elif verdict.answer is Answer.FAULT:  #: no trade in it, so none in any fold of it
        rungs["folds"] = rungs["first"]
    else:
        rungs["folds"] = _folded(c, own, settings, pounds)
    against = market.judge(verdict, own, beside, held, pounds)
    said = rungs["first"][1]
    if against.line is not None and against.wide is not None:
        said = (
            f"over {against.days} days, {against.wide.t:.2f} standard errors beyond "
            f"{against.wide.beta:.2f} of {beside.symbol}'s moves and {against.line.t:.2f} beyond "
            f"{against.line.beta:.2f} of its own line's; {rung.T_PASS} asked of both"
        )
    rungs["market"] = (against.answer, said)
    if (last := shuffled(c, own, settings, pounds, rungs)) is not None:
        rungs["shuffle"] = last
    named = {name: rungs[name][0] for name in deflated.NAMED if name in rungs}
    return {
        "trades": len(verdict.trades),
        "rungs": {name: [answer.name, reason] for name, (answer, reason) in rungs.items()},
        "unrun": unrun,
        "every": all(answer is Answer.PASS for answer, _ in rungs.values()),
    } | ({"answer": deflated.rule(named).name} if len(named) == len(deflated.NAMED) else {})


def _named(verdict: Verdict, one: Deflated) -> Judged:
    """The four rungs read from the trial's trades (`deflated.OWN`), each with its reason."""
    first = (
        f"{len(verdict.trades)} trades judged, their mean gain after every cost "
        f"({verdict.broker}) {_n(verdict.t)} standard errors above nothing; "
        f"{rung.MIN_TRADES} trades and {rung.T_PASS} asked"
    )
    why = {
        "first": first,
        "luck": f"its chance of {one.luck.chance:.2g}, times {one.luck.trials} trials, is "
        f"{one.luck.corrected:.2g}; {luck.FAMILY} or under asked",
        "deflated": f"a deflated Sharpe of {one.deflated:.2f}; {deflated.PASS} passes and under "
        f"{deflated.FAIL} fails",
        "yearly": f"a yearly Sharpe of {_n(one.yearly)}; over {deflated.FLAG} is doubted",
    }
    if verdict.answer in (Answer.FAULT, Answer.THIN):  #: no rung has more to judge than the first
        why = dict.fromkeys(why, first)
    return {name: (answer, why[name]) for name, answer in one.rungs.items()}


def _folded(c: Cell, own: Sequence[Bar], settings: Settings, pounds: Rates) -> Pair:
    """The folds rung: the worst of the folds, its year named in the reason."""
    worst = (folded := folds.judge(c, own, settings, pounds, FOLDS)).worst
    return (
        folded.answer,
        f"the worst of {FOLDS} folds, from {worst.outside.key.cell.start}: "
        f"{len(worst.outside.trades)} trades at {_n(worst.outside.t)} standard errors; on "
        f"the history before it, {len(worst.inside.trades)} at {_n(worst.inside.t)}",
    )


def shuffled(
    c: Cell, own: Sequence[Bar], settings: Settings, pounds: Rates, rungs: Judged
) -> Pair | None:
    """The shuffle rung, run last and only on a trial that passed every rung before it: any
    other is given the least of their answers, since a shuffle costs a hundred runs. A trial
    short of a rung before it (the folds, behind an author's result) has no verdict to shuffle."""
    before = [rungs[name] for name in deflated.NAMED[:-1] if name in rungs]
    if len(before) < len(deflated.NAMED) - 1:
        return None
    least = min(before, key=lambda one: one[0])
    if least[0] is not Answer.PASS:
        return least
    share = shuffle.share(c, own, settings, pounds)
    return (
        Answer.PASS if share <= shuffle.SHARE else Answer.FAIL,
        f"{shuffle.SHUFFLES} shuffles of its days, its share among them {share:.3f}; "
        f"{shuffle.SHARE} or under passes",
    )


def _n(number: Decimal | float | None) -> str:
    return "no" if number is None else f"{number:.2f}"
