"""verdict - THE LADDER'S VERDICT ON ONE CELL: every rung's answer with its reason, the rungs
not run with theirs, and the one rule over them (`lab/ladder.py` holds the spec this builds)."""

from __future__ import annotations

import random
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from desk.command import CAPITAL
from desk.lines import Line
from desk.orders import Settings
from desk.store import Bar
from lab import (
    cell,
    deflated,
    folds,
    holding,
    luck,
    market,
    plateau,
    reproduce,
    rung,
    rung_regimes,
    shuffle,
    stress,
    trials,
    weather,
)
from lab.cell import Cell
from lab.deflated import Deflated
from lab.folds import Pooled
from lab.reproduce import Reproduction
from lab.rung import Answer, Rates, Verdict
from lab.verdict_parts import (
    COLUMNS as COLUMNS,
)
from lab.verdict_parts import (
    INCUBATE as INCUBATE,
)
from lab.verdict_parts import (
    STATUS as STATUS,
)
from lab.verdict_parts import (
    Row as Row,
)
from lab.verdict_parts import (
    by_rule as by_rule,
)
from lab.verdict_parts import (
    cell_line as cell_line,
)
from lab.verdict_parts import (
    goes as goes,
)
from lab.verdict_parts import (
    write_table as write_table,
)

#: The rules trade a line five to ten times a year and a fold is asked for thirty trades: so
#: the last five whole calendar years are the folds, the rule's trades pooled over its lines.
#: A fold is not a trial: nothing is picked from it, and the luck rung counts none.
FOLDS = folds.YEARS
#: Draws of the judged trades' pounds for the resampled drawdowns: they measure, never gate.
RESAMPLES = 1000
#: Rungs that are built and that this set cannot yet be run through, each with why.
UNRUN = {
    "plateau": "neither its rule's variants nor its rule declared fixed were handed in",
}
NO_FIGURE = "no author's figure is on file for the rule: no published result stands behind it"
#: A rule trades a line five to ten times a year and wants 200 sessions to warm up: a line of
#: fewer bars than those and a year's trading has made no trade yet, which says nothing of the rule.
MIN_BARS = 200 + 252
#: A close that moves in a day by that day's pound, or one over it, to within this, on a line in
#: pounds, is a part of the line quoted in dollars (M3): a step under the price store's jump.
#: Units change between two sessions, so the day's OPEN stands at the same step: a session that
#: opens near the close before it and then falls has made its move itself (a crash), and is judged.
STEP = Decimal("0.03")
#: THE LADDER'S ONE SWITCH (R-RUNNER-225, 230; the scorecard, easing 6 of DECISIONS). Off: the first
#: rung to fail keeps the shuffle unrun and every answer is the rung's own. On: only a hard fail
#: (a negative after-cost mean, a failed reproduction, stress over its limit) stops a line; every
#: other rung is run and graded PASS, WEAK or FAIL, and none stops it. On since card
#: ease-switch-on (R-RUNNER-231), once.
EASED = True
T_INCUBATE = Decimal(1)  #: a basket's mean this many standard errors above nothing, or over
WEAK = (Answer.THIN, Answer.DOUBT)  #: a scorecard's WEAK: neither a win nor a loss
#: THE RULE OVER THE RUNGS, once (R-RUNNER-435): a cell passes with no FAIL and at most MAX_WEAK
#: WEAK; a yearly Sharpe above SHARPE_STOP is a hard stop, whatever the rungs say.
MAX_WEAK = 2
SHARPE_STOP = 2.0
Pair = tuple[Answer, str]
Judged = dict[str, Pair]  #: each rung's answer on a cell, and its reason


class TooYoung(ValueError):
    """TOO YOUNG: the line has too few bars to have made a trade; no answer, and no FAULT."""


class UnitStep(ValueError):
    """A line in pounds that steps by the pound's rate in a day: part of it is in dollars."""


def scorecard(answers: Sequence[Answer], yearly_sharpe: float) -> str:
    """STOP, PASS or FAIL over the rungs' answers: the one rule (MAX_WEAK, SHARPE_STOP)."""
    if yearly_sharpe > SHARPE_STOP:
        return "STOP"
    weak = sum(a in WEAK for a in answers)
    fails = any(a in (Answer.FAIL, Answer.FAULT) for a in answers)
    return "PASS" if not fails and weak <= MAX_WEAK else "FAIL"


def judge(
    c: Cell,
    own: Sequence[Bar],
    beside: Line,
    held: Sequence[Bar],
    pounds: Rates,
    count: int,
    made: Sequence[Reproduction],
    pooled: Callable[[], Pooled],
    first: Verdict | None = None,
    family: int | None = None,
    surface: plateau.Surface | plateau.Fixed | None = None,
) -> dict[str, Any]:
    """Every rung's answer with its reason, the rungs not run with theirs, the verdict's.
    The folds are the rule's, pooled over its lines: `pooled` is asked only when they are read.
    `first` is the cell's first rung where the caller has run it already; `family` the trials
    of its rule, used only when EASED; `surface` its rule at its settings, or FIXED where it
    has none (`_plateaued`)."""
    try:
        reproduce.settled(c.strategy, made)
    except ValueError as missed:  #: the rule as coded is not the author's: no verdict on ours
        return {"rungs": {"reproduce": [Answer.FAIL.name, str(missed)]}, "every": False}
    verdict = first or ready(c, own, pounds, made)
    unrun = UNRUN | ({} if made else {"reproduce": NO_FIGURE})
    settings = Settings(CAPITAL)
    (one,) = deflated.judge([verdict], _charged(c, count, family) - 1)  #: every other trial
    rungs = named(verdict, one, c.strategy if EASED else None)
    if EASED and verdict.answer is Answer.FAIL and verdict.t is not None and verdict.t < 0:
        return _stopped(len(verdict.trades), {"first": rungs["first"]}, unrun)  #: a hard fail
    if made:
        said = "; ".join(f"{m.figure.hand.value} result, {m.figure.source}" for m in made)
        rungs["reproduce"] = (Answer.PASS, f"reproduced: {said}")
    rungs["folds"] = _folded(pooled)
    rungs["market"] = _marketed(market.judge(verdict, own, beside, held, pounds), beside, rungs)
    rungs["regime"] = _weathered(own, verdict, made)
    rungs["stress"] = _stressed(c, own, settings, pounds)
    if EASED and rungs["stress"][0] is Answer.FAIL:  #: a hard fail: the shuffle is not run
        return _stopped(len(verdict.trades), rungs, unrun)
    if (last := shuffled(c, own, settings, pounds, rungs, made, EASED)) is not None:
        rungs["shuffle"] = last
    unrun = _plateaued(surface, rungs, unrun)
    read = {name: rungs[name][0] for name in deflated.NAMED if name in rungs}
    return {
        "trades": len(verdict.trades),
        "rungs": reported(rungs),
        "drawdown": drawdowns([t.gross - t.costs.total for t in verdict.trades], trials.name(c)),
        "holding": _held(verdict, own, beside, held, pounds, settings),
        "unrun": unrun,
        "every": every(rungs),
    } | ({"answer": deflated.rule(read).name} if len(read) == len(deflated.NAMED) else {})


def every(rungs: Judged) -> bool:
    """Every rung that gates passed: a rung only reported (`deflated.REPORTED`, the luck rung
    since L18) holds nothing back."""
    return all(a is Answer.PASS for n, (a, _) in rungs.items() if n not in deflated.REPORTED)


def _plateaued(
    surface: plateau.Surface | plateau.Fixed | None, rungs: Judged, unrun: Mapping[str, str]
) -> dict[str, str]:
    """The rungs left unrun once plateau is judged into `rungs` where the cell's surface, or
    its rule FIXED, is handed in; with neither, plateau stays UNRUN, with why."""
    if surface is None:
        return dict(unrun)
    rungs["plateau"] = plateau.judged(surface)
    return {name: why for name, why in unrun.items() if name != "plateau"}


def basket_answer(basket: Verdict, stressed: Answer) -> str:
    """A basket's answer's name. Off: the ladder's own. EASED: a basket the ladder fails on enough
    trades, whose after-cost mean is T_INCUBATE standard errors above nothing and whose stress
    passed, is INCUBATE; a PASS stays PASS, and any other stress answer is never INCUBATE."""
    pending = basket.answer is Answer.FAIL and basket.t is not None and basket.t >= T_INCUBATE
    return INCUBATE if EASED and pending and stressed is Answer.PASS else basket.answer.name


def stress_answer(c: Cell, own: Sequence[Bar], pounds: Rates) -> Answer:
    """The stress rung's answer on a line, for a basket: it stands on its lines' stress."""
    return _stressed(c, own, Settings(CAPITAL), pounds)[0]


def _charged(c: Cell, count: int, family: int | None) -> int:
    """The trials a cell is charged: the register's, or with EASED its rule's family's."""
    if EASED and family is None:
        raise ValueError(f"{c.strategy}: EASED judges by the rule's family count, none given")
    return family if EASED and family is not None else count


def _held(
    one: Verdict, own: Sequence[Bar], beside: Line, held: Sequence[Bar], pounds: Rates, s: Settings
) -> str:
    """The strategy's figure beside the market's, held through the same window after the same
    costs; the market's own missing bar or rate is said in words, as the market rung says it."""
    try:
        return holding.beside(one, own, beside, held, pounds, s).row()
    except ValueError as why:
        return f"not shown: {why}"


def _marketed(against: market.Against, beside: Line, rungs: Judged) -> Pair:
    """The market rung's answer with its reason: the market's own missing day, or the first
    rung's THIN or FAULT, which it inherits, or the two betas."""
    if against.line is None or against.wide is None:
        return against.answer, against.fault or rungs["first"][1]
    return against.answer, (
        f"over {against.days} days, {against.wide.t:.2f} standard errors beyond "
        f"{against.wide.beta:.2f} of {beside.symbol}'s moves and {against.line.t:.2f} beyond "
        f"{against.line.beta:.2f} of its own line's; {rung.T_PASS} asked of both"
    )


def _stopped(trades: int, rungs: Judged, unrun: Mapping[str, str]) -> dict[str, Any]:
    """A line stopped at a hard fail: the rungs judged so far, the verdict FAIL, no shuffle."""
    return {"trades": trades, "rungs": reported(rungs), "unrun": unrun, "every": False} | {
        "answer": Answer.FAIL.name
    }


def reported(rungs: Judged) -> dict[str, list[str]]:
    """Each rung's answer and reason for the results file: its grade where EASED (WEAK is a
    THIN or a DOUBT), else its answer's name."""
    return {
        name: ["WEAK" if EASED and answer in WEAK else answer.name, reason]
        for name, (answer, reason) in rungs.items()
    }


def drawdowns(pounds: Sequence[Decimal], name: str) -> dict[str, float]:
    """The judged trades' pounds drawn again with replacement, as many as were judged,
    RESAMPLES times from the trial's name; each draw's deepest fall from a high of the
    capital's pounds is taken as a part of the capital. Their median and 95th percentile,
    as plain numbers for the results file."""
    if not pounds:
        return {}
    rng = random.Random(name)  # noqa: S311 - a repeatable draw, not a secret
    falls: list[Decimal] = []
    for _ in range(RESAMPLES):
        equity = peak = CAPITAL
        deepest = Decimal(0)
        for won in rng.choices(pounds, k=len(pounds)):
            equity += won
            peak = max(peak, equity)
            deepest = max(deepest, peak - equity)
        falls.append(deepest / CAPITAL)
    falls.sort()
    return {
        "median": float(falls[(RESAMPLES - 1) // 2]),
        "p95": float(falls[(RESAMPLES - 1) * 95 // 100]),
    }


@dataclass
class Pool:
    """A rule's lines that could be judged, each with its bars and its first rung."""

    lines: list[tuple[Cell, Sequence[Bar]]]
    firsts: dict[Cell, Verdict]  #: each line's first rung, run once to know it can be
    data: str  #: the version of every line's bars, in every cell's key
    dollars: bool  #: a line in dollars is pooled: the rates of exchange are in every cell's key
    folded: Pooled | None = None  #: pooled once, when first read
    failed: ValueError | None = None  #: why it could not be, told to every cell of the rule

    def fold(self, pounds: Rates, made: Sequence[Reproduction] = ()) -> Pooled:
        """The lines folded by the last five whole years: once, a failure remembered."""
        if self.failed is not None:
            raise self.failed
        try:
            self.folded = self.folded or pool(self.lines, pounds, made)
        except ValueError as cannot:
            self.failed = cannot
            raise
        return self.folded


def _folded(pooled: Callable[[], Pooled]) -> Pair:
    """The folds rung: the rule's worst year, or a FAULT where its years cannot be had."""
    try:
        folded = pooled()
    except ValueError as cannot:  #: a fault in the test, said as one with its reason
        return Answer.FAULT, f"the folds could not be run: {cannot}"
    return folded.answer, folded.reason


def ready(c: Cell, own: Sequence[Bar], pounds: Rates, made: Sequence[Reproduction]) -> Verdict:
    """The cell's first rung, or why the line waits: a step of units in it, too few bars for a
    trade (whatever it scored, a few trades say nothing of the rule), a day with no rate."""
    _unstepped(c.line, own, pounds)
    if len(own) < MIN_BARS:
        raise TooYoung(f"{c.line.symbol}: {len(own)} bars, no trade yet; waits on {MIN_BARS}")
    return rung.judge(cell.run(c, own), own, Settings(CAPITAL), pounds, made)


def pool(
    lines: Sequence[tuple[Cell, Sequence[Bar]]], pounds: Rates, made: Sequence[Reproduction] = ()
) -> Pooled:
    """One rule's lines, each with its bars, folded by the last five whole years, the author's
    figure on file for the rule handed to every fold."""
    return folds.pool(lines, Settings(CAPITAL), pounds, FOLDS, made)


def _unstepped(line: Line, own: Sequence[Bar], pounds: Rates) -> None:
    """Refuse a line in pounds whose open and close both step by the pound's rate in a day, not
    named a real move."""
    named = {day for day, _ in line.real_moves}
    for before, after in zip(own, own[1:], strict=False):
        rate = pounds.get(after.day)
        if line.currency != "GBP" or rate is None or after.day in named:
            continue
        moved = [price / before.close for price in (after.open, after.close)]
        if any(all(abs(m / r - 1) <= STEP for m in moved) for r in (rate, 1 / rate)):
            raise UnitStep(
                f"{line.symbol}: on {after.day} the open and the close step by the pound's {rate} "
                "or its inverse, as a change of units; waits for the data lane to mend the bars "
                "or the master to name the move"
            )


def named(verdict: Verdict, one: Deflated, family: str | None = None) -> Judged:
    """The four rungs read from the trial's trades (`deflated.OWN`), each with its reason."""
    first = (
        f"{len(verdict.trades)} trades judged, their mean gain after every cost "
        f"({verdict.broker}) {_n(verdict.t)} standard errors above nothing; "
        f"{rung.MIN_TRADES} trades and {rung.T_PASS} asked"
    )
    of = "" if family is None else f" of the {family} family"
    why = {
        "first": first,
        "luck": f"its chance of {one.luck.chance:.2g}, times {one.luck.trials} trials{of}, is "
        f"{one.luck.corrected:.2g}; {luck.FAMILY} or under asked",
        "deflated": f"a deflated Sharpe of {one.deflated:.2f}; {deflated.PASS} passes and under "
        f"{deflated.FAIL} fails",
        "yearly": f"a yearly Sharpe of {_n(one.yearly)}; over {deflated.FLAG} is doubted",
    }
    if verdict.answer in (Answer.FAULT, Answer.THIN):  #: no rung has more to judge than the first
        why = dict.fromkeys(why, first)
    return {name: (answer, why[name]) for name, answer in one.rungs.items()}


def shuffled(
    c: Cell,
    own: Sequence[Bar],
    settings: Settings,
    pounds: Rates,
    rungs: Judged,
    made: Sequence[Reproduction],
    graded: bool = False,
) -> Pair | None:
    """The shuffle rung, run last and only on a trial that passed every rung before it: any
    other is given the least of their answers and told it was not run, since a shuffle costs a
    hundred runs; `graded` (EASED) runs it on every trial that reaches it. A trial short of a
    rung before it (the folds,
    behind an author's result) has no verdict to shuffle."""
    before = {name: rungs[name][0] for name in deflated.NAMED[:-1] if name in rungs}
    if len(before) < len(deflated.NAMED) - 1:
        return None
    name, least = min(before.items(), key=lambda one: one[1])
    if least is not Answer.PASS and not graded:
        return least, (
            f"not run: its {shuffle.SHUFFLES} shuffles are kept for a trial that passed every "
            f"rung before it, and {name} answered {least.name}"
        )
    share = shuffle.share(c, own, settings, pounds, made)
    return (
        Answer.PASS if share <= shuffle.SHARE else Answer.FAIL,
        f"{shuffle.SHUFFLES} shuffles of its days, its share among them {share:.3f}; "
        f"{shuffle.SHARE} or under passes",
    )


def _stressed(c: Cell, own: Sequence[Bar], settings: Settings, pounds: Rates) -> Pair:
    """The stress rung on the line's whole history, or a FAULT where it cannot be asked."""
    try:
        return stress.judge(
            Cell(c.strategy, c.line, own[0].day, c.end), own, settings, pounds
        ).judged()
    except ValueError as cannot:  #: a fault in the test, said as one with its reason
        return Answer.FAULT, f"the stress scenarios could not be run: {cannot}"


def _weathered(own: Sequence[Bar], verdict: Verdict, made: Sequence[Reproduction]) -> Pair:
    """The regime rung: the priced trades judged apart in the up and the down days they were
    bought on, or a FAULT where the weather cannot be named."""
    try:
        said = rung_regimes.by_weather(
            verdict.key.rung(rung_regimes.__name__), verdict.trades, weather.named(own), made
        )
    except ValueError as cannot:  #: a fault in the test, said as one with its reason
        return Answer.FAULT, f"the weather could not be named: {cannot}"
    return said.answer, (
        f"up days {said.up.answer.name} on {len(said.up.trades)} trades, down days "
        f"{said.down.answer.name} on {len(said.down.trades)}; both must pass"
    )


def _n(number: Decimal | float | None) -> str:
    return "no" if number is None else f"{number:.2f}"
