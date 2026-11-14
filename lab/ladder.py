"""ladder - THE LADDER'S FIRST SET: every published rule the desk holds, on every one of the
desk's lines, through every rung that is built, each answer kept with its reason and the
number of trials it was judged against. `python -m lab.ladder` is the whole of it: it can be
stopped at any moment and run again, one process at a time, and it ends with one line of counts.

NOTHING IS CHOSEN BY EYE. The set is every rule with a publication on file
(`lab/published.py`) on every line of its declared universe, over one window fixed here
before any result and judged from the line's first bar in it, so its years are years it
traded. The folds, the market each venue is set beside and the question the trials are
counted under are fixed here too, and none is an argument of the command.

EVERY TRIAL IS COUNTED BEFORE ANYTHING IS RUN. Each cell, and each of its folds, is entered
in the set's own register of trials (`lab/trials.py`) before the first is judged, so a cell
that fails, cannot be judged or is never reached has been counted already, and every answer
is corrected for the register's whole count. A set that grows is judged again against it.

THE RUNGS RUN, each one's answer in the rung's own words (`rung.Answer`) with its reason:
the author's own result where a figure is on file (`lab/reproduce.py`); the first rung, the
luck rung, the deflated Sharpe and the yearly Sharpe, with the one verdict rule over them
(`lab/deflated.py`); the folds (`lab/folds.py`); and the market's rung (`lab/market.py`). A
rule whose author's figure is not reproduced is given no verdict on the desk's lines. A rung
that is built and cannot yet be run is named with its reason on every line (UNRUN): none is
left out in silence, and nothing is called passed that was not judged. No answer here sends
anything to paper: that takes all eleven rungs, each proven, and they are not all built.

KEPT BY WHAT MADE IT. The results file holds one JSON line for each cell as it finishes,
forced to disk before the next begins. A line is found again by its key: the code this
module reaches, the cell's bars and its market's, the rates of exchange it was priced at,
the count of trials and the reproductions behind it. A cell kept under that key is skipped;
change any of them and it is judged again, and the last line of a cell is its answer now. A
cell that could not be judged (a line parked or stale, too short a history for a trade, a
day with no rate) keeps its reason and the time of its last try, and is tried again no sooner
than 30 minutes after it, whatever the runs between. A line a stop cut short is cut off.

THE RATES are the desk's own until the data lane keeps a rate for every day (R-RUNGS-3): a
day's pounds per dollar is one over the pound's last close in dollars before that day, from
the same archive and inside the same bounds as the desk's day takes it (`desk/command.py`).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from functools import cache
from pathlib import Path
from typing import Any

from desk import archive, keeper
from desk.command import CAPITAL, DOLLARS, FRESH, POUND
from desk.lines import LINES, Line
from desk.orders import Settings
from desk.store import Bar
from desk.strategy import STRATEGIES
from lab import batch, cell, deflated, folds, luck, market, published, reproduce, rung, trials
from lab.batch import Bars
from lab.cell import Cell
from lab.deflated import Deflated
from lab.reproduce import Reproduction
from lab.rung import Answer, Rates, Verdict

ME = "lab.ladder"  #: this module as the cell knows it, however the process was started
QUESTION = "set 1: does a published rule earn on one of the desk's lines?"
#: The one window: from where the daily history is to be carried back to, to the last
#: session before the set was first run. A later end is a new set of trials, on purpose.
START, END = date(2000, 1, 1), date(2026, 11, 13)
#: The rules trade a line five to ten times a year and a fold is asked for thirty trades: so
#: the window in three parts, two of them folds, each a trial the luck rung counts.
FOLDS = 2
#: The market each venue's lines are set beside: the S&P 500 in New York, the FTSE 100 in London.
MARKETS = {"US": "SPY", "LSE": "ISF"}
FOLDER, RESULTS, REGISTER = "ladder", "set1.jsonl", "set1.trials.jsonl"
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
#: A cell that waits on data is tried again no sooner than this after its last try.
RETRY = timedelta(minutes=30)
FAILED = (ValueError, OSError, keeper.Stale)  #: what may leave a cell unjudged; all else is a bug
Row = Mapping[str, Any]  #: a cell's line in the results file
Judged = dict[str, tuple[Answer, str]]  #: each rung's answer on a cell, and its reason


def cells() -> tuple[Cell, ...]:
    """The set: every published rule on every line it declares, over the one window."""
    return tuple(
        Cell(name, line, START, END)
        for name in published.PUBLISHED
        for line in STRATEGIES[name].declared.universe
    )


def names(c: Cell) -> list[str]:
    """The trials a cell costs, as the register names them: itself, and each of its folds."""
    whole = trials.name(c)
    return [whole, *(f"{whole}, fold {n} of {FOLDS}" for n in range(1, FOLDS + 1))]


def stored(home: Path) -> Bars:
    """Each line's daily bars to the window's end, through the keeper's door: a line parked,
    or not refreshed that far, is refused and never judged on what is held."""

    def bars(line: Line) -> Sequence[Bar]:
        held, parked = keeper.saved(home, END + keeper.DAY, [line])
        if parked:
            raise ValueError(f"{line.symbol}: parked by the price store; waits on its bars")
        return held[line]

    return bars


def rates(ask: Callable[[Line, date], Sequence[Bar]] = archive.fetch) -> dict[date, Decimal]:
    """Pounds per dollar for each day to the window's end, as the desk's day takes it: one
    over the pound's last close before the day. A day whose last close is too old, or is no
    pound's, has no rate, and the first rung refuses to price it."""
    closes = ask(POUND, END + keeper.DAY)
    made: dict[date, Decimal] = {}
    for bar, later in zip(closes, [*closes[1:], None], strict=True):
        until = min(bar.day + FRESH, END if later is None else later.day)
        if DOLLARS[0] < bar.close < DOLLARS[1]:
            rate = (1 / bar.close).quantize(Decimal("0.000001"))
            made |= {bar.day + n * keeper.DAY: rate for n in range(1, (until - bar.day).days + 1)}
    return made


def run(
    home: Path,
    bars: Bars,
    pounds: Rates,
    todo: Sequence[Cell] | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> str:
    """The set judged and kept under home, a cell kept already skipped: the one line of counts."""
    if cell.code_version(module=ME) != cell.RUNGS[ME]:
        raise RuntimeError("the code on disk has changed since this process loaded it")
    todo = cells() if todo is None else todo
    results, register = home / FOLDER / RESULTS, home / FOLDER / REGISTER
    if not results.exists() and not register.exists():  #: the set's first run, and only that
        results.parent.mkdir(parents=True, exist_ok=True)
        (fresh := register.with_suffix(".new")).unlink(missing_ok=True)
        trials.start(fresh)
        trials.ask(fresh, QUESTION)
        fresh.replace(register)  #: whole or not there: a stop before this begins it again
    count = trials.enter(register, QUESTION, [name for c in todo for name in names(c)])
    text = results.read_bytes() if results.exists() else b""
    whole = text[: text.rfind(b"\n") + 1]
    last = {tuple(row["cell"]): row for row in map(json.loads, whole.splitlines())}
    behind: dict[str, tuple[Reproduction, ...]] = {}
    tally: Counter[str] = Counter()
    with results.open("ab") as out:
        out.truncate(len(whole))
        for c in todo:
            was = last.get(tuple(batch.row(c)))
            row = _one(c, bars, pounds, count, was, behind, now())
            if row != was:
                out.write(json.dumps(row).encode() + b"\n")
                out.flush()
                os.fsync(out.fileno())
            tally["failed" if "error" in row else "kept" if row is was else "judged"] += 1
            tally[row.get("answer", "none")] += 1
            tally["missed"] += "error" not in row and "answer" not in row
            tally["every"] += row.get("every", False)
            tally["behind"] += row.get("every", False) and "reproduce" in row["rungs"]
    answers = ", ".join(f"{a.name} {tally[a.name]}" for a in reversed(Answer))
    return (
        f"ladder set 1: {len(todo)} cells, each a published rule on a line, judged against "
        f"{count} trials: {tally['judged']} judged now, {tally['kept']} kept from before, "
        f"{tally['failed']} could not be judged and are tried again next run; the one rule's "
        f"answers: {answers}; {tally['missed']} not the author's rule; {tally['every']} passed "
        f"every rung run, {tally['behind']} of them behind an author's result; none goes to "
        "paper before all eleven rungs are built."
    )


def _one(
    c: Cell,
    bars: Bars,
    pounds: Rates,
    count: int,
    was: Row | None,
    behind: dict[str, tuple[Reproduction, ...]],
    now: datetime,
) -> Row:
    """The cell's line: the one kept, where it is kept under the key these bars, rates and
    trials give; else its answers now, or why it could not be judged. It is judged from the
    line's first bar, so that its years are years it could trade in."""
    head: dict[str, Any] = {"set": 1, "cell": batch.row(c), "trials": count}
    tried = was.get("tried") if was is not None else None  #: a waiting cell's last try
    if was is not None and tried and now - datetime.fromisoformat(tried) < RETRY:
        return was  #: it waits on data, and was tried not long ago
    try:
        beside = next(line for line in LINES if line.symbol == MARKETS[c.line.venue])
        own, held = bars(c.line), bars(beside)
        if c.strategy not in behind:
            owed = [figure for figure in reproduce.FIGURES if figure.strategy == c.strategy]
            behind[c.strategy] = tuple(reproduce.reproduce(f, bars(f.line)) for f in owed)
        made = behind[c.strategy]
        c = Cell(c.strategy, c.line, max([c.start, *(bar.day for bar in own[:1])]), c.end)
        mine = cell.key(c, own).rung(ME)
        days = sorted(day for day in pounds if day <= c.end and c.line.currency != "GBP")
        market = cell.key(Cell(c.strategy, beside, c.start, c.end), held).data
        parts = [mine.code, mine.data, market, str(count), *(f"{d} {pounds[d]}" for d in days)]
        parts += [one.key.code + one.key.data for one in made]
        key = hashlib.sha256("\n".join(parts).encode()).hexdigest()
        if was is not None and was.get("key") == key:
            return was
        judged = _judge(c, own, beside, held, pounds, count, made)
        return head | {"key": key, "from": c.start.isoformat()} | judged
    except FAILED as error:
        return head | {"error": f"{type(error).__name__}: {error}", "tried": now.isoformat()}


def _judge(
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
        worst = (folded := folds.judge(c, own, settings, pounds, FOLDS)).worst
        rungs["folds"] = (
            folded.answer,
            f"the worst of {FOLDS} folds, from {worst.outside.key.cell.start}: "
            f"{len(worst.outside.trades)} trades at {_n(worst.outside.t)} standard errors; on "
            f"the history before it, {len(worst.inside.trades)} at {_n(worst.inside.t)}",
        )
    against = market.judge(verdict, own, beside, held, pounds)
    said = rungs["first"][1]
    if against.line is not None and against.wide is not None:
        said = (
            f"over {against.days} days, {against.wide.t:.2f} standard errors beyond "
            f"{against.wide.beta:.2f} of {beside.symbol}'s moves and {against.line.t:.2f} beyond "
            f"{against.line.beta:.2f} of its own line's; {rung.T_PASS} asked of both"
        )
    rungs["market"] = (against.answer, said)
    return {
        "trades": len(verdict.trades),
        "rungs": {name: [answer.name, reason] for name, (answer, reason) in rungs.items()},
        "unrun": unrun,
        "answer": one.answer.name,
        "every": all(answer is Answer.PASS for answer, _ in rungs.values()),
    }


def _named(verdict: Verdict, one: Deflated) -> Judged:
    """The four rungs the one verdict rule reads, each with its reason."""
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


def _n(number: Decimal | float | None) -> str:
    return "no" if number is None else f"{number:.2f}"


def main(env: Mapping[str, str]) -> int:
    if not env.get("KESTREL2_DATA"):
        sys.exit("ladder: KESTREL2_DATA names no data folder, so the set has no home")
    home = Path(env["KESTREL2_DATA"])
    sys.stdout.write(run(home, cache(stored(home)), rates()) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(os.environ))
