"""verdict - THE LADDER'S VERDICT ON ONE CELL: every rung's answer with its reason, the rungs
not run with theirs, and the one rule over them (`lab/ladder.py` holds the spec this builds)."""

from __future__ import annotations

import json
import random
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from desk.command import CAPITAL
from desk.lines import Line
from desk.orders import Settings
from desk.store import Bar
from lab import cell, deflated, folds, luck, market, reproduce, rung, shuffle, trials
from lab.cell import Cell
from lab.deflated import Deflated
from lab.folds import Pooled
from lab.reproduce import Reproduction
from lab.rung import Answer, Rates, Verdict

#: The rules trade a line five to ten times a year and a fold is asked for thirty trades: so
#: the last five whole calendar years are the folds, the rule's trades pooled over its lines.
#: A fold is not a trial: nothing is picked from it, and the luck rung counts none.
FOLDS = folds.YEARS
#: Draws of the judged trades' pounds for the resampled drawdowns: they measure, never gate.
RESAMPLES = 1000
#: Rungs that are built and that this set cannot yet be run through, each with why.
UNRUN = {
    "regime": "the weather that names each day's regime is not built (REG-01)",
    "plateau": "the published rules carry no settings to choose among yet",
    "stress": "it gives pounds lost and never a pass; the loss limit to judge them by is not set",
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
STATUS = "PRE-REVIEW"  #: what every table is until the blind review (R-RUNNER-40) is clean
COLUMNS = ("rule", "line", "venue", "answer", "rungs", "trials", "reproduction", "goes forward")
Row = Mapping[str, Any]  #: a cell's line in the results file
Pair = tuple[Answer, str]
Judged = dict[str, Pair]  #: each rung's answer on a cell, and its reason


class TooYoung(ValueError):
    """TOO YOUNG: the line has too few bars to have made a trade; no answer, and no FAULT."""


class UnitStep(ValueError):
    """A line in pounds that steps by the pound's rate in a day: part of it is in dollars."""


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
) -> dict[str, Any]:
    """Every rung's answer with its reason, the rungs not run with theirs, the verdict's.
    The folds are the rule's, pooled over its lines: `pooled` is asked only when they are read.
    `first` is the cell's first rung where the caller has run it already."""
    try:
        reproduce.settled(c.strategy, made)
    except ValueError as missed:  #: the rule as coded is not the author's: no verdict on ours
        return {"rungs": {"reproduce": [Answer.FAIL.name, str(missed)]}, "every": False}
    verdict = first or ready(c, own, pounds, made)
    unrun = UNRUN | ({} if made else {"reproduce": NO_FIGURE})
    settings = Settings(CAPITAL)
    (one,) = deflated.judge([verdict], count - 1)  #: every other trial the register holds
    rungs = _named(verdict, one)
    if made:
        said = "; ".join(f"{m.figure.hand.value} result, {m.figure.source}" for m in made)
        rungs["reproduce"] = (Answer.PASS, f"reproduced: {said}")
    rungs["folds"] = _folded(pooled)
    against = market.judge(verdict, own, beside, held, pounds)
    said = (
        against.fault or rungs["first"][1]
    )  #: its own missing day, or the first rung's THIN or FAULT
    if against.line is not None and against.wide is not None:
        said = (
            f"over {against.days} days, {against.wide.t:.2f} standard errors beyond "
            f"{against.wide.beta:.2f} of {beside.symbol}'s moves and {against.line.t:.2f} beyond "
            f"{against.line.beta:.2f} of its own line's; {rung.T_PASS} asked of both"
        )
    rungs["market"] = (against.answer, said)
    if (last := shuffled(c, own, settings, pounds, rungs, made)) is not None:
        rungs["shuffle"] = last
    named = {name: rungs[name][0] for name in deflated.NAMED if name in rungs}
    return {
        "trades": len(verdict.trades),
        "rungs": {name: [answer.name, reason] for name, (answer, reason) in rungs.items()},
        "drawdown": drawdowns([t.gross - t.costs.total for t in verdict.trades], trials.name(c)),
        "unrun": unrun,
        "every": all(answer is Answer.PASS for answer, _ in rungs.values()),
    } | ({"answer": deflated.rule(named).name} if len(named) == len(deflated.NAMED) else {})


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


def shuffled(
    c: Cell,
    own: Sequence[Bar],
    settings: Settings,
    pounds: Rates,
    rungs: Judged,
    made: Sequence[Reproduction],
) -> Pair | None:
    """The shuffle rung, run last and only on a trial that passed every rung before it: any
    other is given the least of their answers and told it was not run, since a shuffle costs a
    hundred runs. A trial short of a rung before it (the folds, behind an author's result) has
    no verdict to shuffle."""
    before = {name: rungs[name][0] for name in deflated.NAMED[:-1] if name in rungs}
    if len(before) < len(deflated.NAMED) - 1:
        return None
    name, least = min(before.items(), key=lambda one: one[1])
    if least is not Answer.PASS:
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


def _n(number: Decimal | float | None) -> str:
    return "no" if number is None else f"{number:.2f}"


def goes(row: Row) -> bool:
    """A cell goes forward when its one verdict is PASS, every rung run passed and its row says
    that no rung is unrun: passing the rungs that happen to be built is not passing the ladder."""
    passed = row.get("answer") == Answer.PASS.name and bool(row.get("every"))
    return passed and row.get("unrun") == {}


def by_rule(rows: Sequence[Row], rules: Sequence[str]) -> dict[str, list[Row]]:
    """The rows of each rule, in the order the rules are given."""
    return {rule: [row for row in rows if row["cell"][0] == rule] for rule in rules}


def _rule(rule: str, rows: Sequence[Row]) -> Row:
    return {"rule": rule, "passed": any(map(goes, rows)), "cells": rows}


def cell_line(row: Row) -> list[str]:
    """A cell's table line: its answer, each rung's answer and reason, and the author's result."""
    rungs = [f"{name} {a}: {why}" for name, (a, why) in row.get("rungs", {}).items()]
    unrun = [f"{name} UNRUN: {why}" for name, why in row.get("unrun", {}).items()]
    own = " | ".join(row.get("reproduction") or [row.get("unrun", {}).get("reproduce", "")])
    result = f"not judged, tried again next run: {row['error']}" if "error" in row else own
    text = " <br> ".join(filter(None, [row.get("proxy"), *rungs, *unrun]))
    text = text or row.get("error", row.get("refused", ""))
    return [
        row.get("answer", "none"),
        text,
        str(row["trials"]),
        result,
        "yes" if goes(row) else "no",
    ]


def write_table(
    folder: Path,
    tag: int | str,
    question: str,
    rows: Sequence[Row],
    rules: Sequence[str],
    count: int,
    built: tuple[int, int],
) -> Path:
    """The set's results table, `<tag>.md` and `<tag>.json`, labelled PRE-REVIEW, its header
    saying how many of the ladder's rungs are built: `built` is (built, of)."""
    folder.mkdir(parents=True, exist_ok=True)
    mine = by_rule(rows, rules)
    data: dict[str, object] = {"set": tag, "question": question, "status": STATUS}
    data |= {"cells": len(rows), "trials": count, "refused": sum("refused" in r for r in rows)}
    data |= {"rungs_built": built[0], "rungs": built[1]}
    data |= {"rules": [_rule(r, rs) for r, rs in mine.items()]}
    (folder / f"{tag}.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
    #: the register is never shortened: a trial an earlier run of the set entered stays counted
    said = f"Cells: {len(rows)}. Each is judged against {count} trials, all its register ever held."
    out = [f"# SET {tag} - {STATUS}", "", f"rungs built: {built[0]} of {built[1]}", ""]
    out += [f"{question} {said}", ""]
    out += [f"{STATUS}: not final until the blind review (R-RUNNER-40) is clean.", ""]
    for rule, rs in mine.items():
        out += [f"## {rule}: {sum(map(goes, rs))} of {len(rs)} lines go forward", ""]
        out += ["| " + " | ".join(COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]
        for row in rs:
            cells = [rule, row["cell"][1], row["cell"][2], *cell_line(row)]
            out.append(
                "| " + " | ".join(c.replace("|", "/").replace("\n", " ") for c in cells) + " |"
            )
        out.append("")
    (path := folder / f"{tag}.md").write_text("\n".join(out), encoding="utf-8")
    return path
