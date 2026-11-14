"""ladder - THE LADDER, AND ITS SPEC. `python -m lab.ladder` takes every published rule the desk
holds (`lab/published.py`), on every line it declares, through every rung, and keeps each
answer with its reason and its count of trials; it can be stopped at any moment and run again,
one process at a time, and ends with one line of counts. THIS DOCSTRING IS THE ONE HOME of what
the ladder must do; a rung's module says how it does its part, and may not set another bar.
Its known answers are tested in `tests/ladder_spec/`. What is written here and not yet built is
listed under OWED at the foot, and until that is empty no answer of the ladder is to be believed.

WHAT PASS MEANS. On this line the rule earned, after every cost of the broker named, by more
than luck among every trial tried, by more than its line or its market simply held, in the
worst of the last five years as in the whole, and by the order of its days and not their mix.
PASS is held to two rates, measured on planted histories and recorded by the tests: of sets
with no edge in any trial, at most one in twenty is given a PASS; of trials with the planted
edge, four in five or more. PASS sends nothing to paper: that is the promotion's
(`lab/promotion.py`). The other answers (`rung.Answer`): FAIL, it did not earn, by a test that
could have passed it; DOUBT, neither won nor lost, never promoted; THIN, too little evidence,
never a fail; FAULT, the test is at fault and says nothing of the rule.

NOTHING IS CHOSEN BY EYE. The set, the window (judged from each line's first bar in it), the
folds, each venue's market, the seeds, the question the trials are counted under and every bar
below are fixed here before any result, and none is an argument of the command.

THE ONE VERDICT (G1) is the least answer over EVERY gating rung, each named in
`deflated.NAMED`: a trial short of any one of them has no verdict, however the rest scored, and
a rung joins or leaves only by a change to this page. THE RUNGS AND THEIR BARS:
  reproduce  where the rule's author has a figure on file, the code as it is makes it again
             (`lab/reproduce.py`); if not, no verdict on any line. Handed to every rung (M2).
  first      30 judged trades or more, and their mean gain after every cost 2 standard errors
             or more above nothing, the rule's own stop planted among them (`lab/rung.py`).
  luck       its chance of that, times every trial of the set, at most 0.05 (`lab/luck.py`).
  deflated   a deflated Sharpe of 0.90 passes; under 0.50 fails; between them, DOUBT.
  yearly     a yearly Sharpe over 2 is DOUBT, never a win (`lab/deflated.py`, canon B6).
  folds      walk-forward by the year, pooled by rule: the worst of FOLDS years earned.
  market     its excess over its own line simply held, and over its market, each 2 standard
             errors or more above nothing (`lab/market.py`; MARKETS names each venue's).
  shuffle    of SHUFFLES histories of its own days in a random order, 0.05 or fewer do as well.
Three more measure and never gate, each named on every line with its figures or the reason it
was not run: regime, plateau, and stress with its resampled drawdowns.

RARE LARGE LOSSES (G2). Nine small wins in ten and a loss at the stop in the tenth, worth
nothing together, show thirty wins and no loss one time in twenty-four, and no bar above stops
that: at 30 trades 3.7% of such trials passed the first rung, the luck rung and the deflated
Sharpe, whatever the count of trials. So wherever the first rung judges trades it counts ONE
MORE, which the rule did not make: a loss at its own stop, the least any judged trade would
have made had its stop sold it, with a stop's costs. It is in the standard errors and in all
that is read from them (the luck's chance, the Sharpe's skew and kurtosis), and in no count of
trades and no sum of pounds. A real edge on few tight trades pays for it with more trades, and
that is the price. The least length of record that a Sharpe's skew and kurtosis ask for
(MinTRL) is no second bar: it is the deflated band, read from the other side, and it too is
blind to a loss not yet seen.

THE FOLDS (M1, M2, M6). The last FOLDS (5) whole calendar years of the window are the folds,
each judged out-of-sample on its own year beside the in-sample history before it, every year
back to the window's start (anchored). A rule trades a line five to ten times a year, so no
line is asked for a fold's trades alone: the rule's trades on ALL its lines are pooled in each
fold and the one answer is every line's. A fold's gains are taken by the day, every day of its
year, summed over its lines as the market's rung marks them, so trades held together are not
counted as bets apart; its trades are those bought and sold inside it, as a cell's are.
With 30 pooled judged trades or more a fold PASSES if its mean day earned after costs, FAILS at
2 standard errors or more under nothing, and is in DOUBT between; with fewer it is THIN; with
none, FAULT. The verdict is the worst fold's. A fold is not a trial: nothing is picked from it.

THE SHUFFLE (Monte Carlo, gating). Each of a line's days is kept whole, as its moves from the
close before, and SHUFFLES (100) times they are put in a random order and the rule run on the
history that makes, priced by the first rung. Each has the line's whole rise and no order in
it, so a rule that earns as much there has timed nothing. The trial's share is the shuffles
with standard errors at or above its own, and itself, over SHUFFLES + 1: 0.05 or under PASSES,
more FAILS. It is run last and only on a trial that has passed every rung before it; any other
is given the least of their answers. The order is drawn from the trial's name: a trial run
again is shuffled the same.

RESAMPLED DRAWDOWNS (Monte Carlo, for stress and sizing; never a pass). The judged trades'
pounds are drawn again with replacement, as many as were judged, RESAMPLES (1,000) times from
the trial's name, and each draw's deepest fall from a high is taken. The line keeps, under
`drawdown`, their `median` and their 95th percentile (`p95`) as parts of the capital, beside
the stress scenarios (`lab/stress.py`). The loss that judges them is the money lane's to set,
once (R-RUNGS-11).

EVERY TRIAL IS COUNTED BEFORE ANYTHING IS RUN, in the set's own register (`lab/trials.py`): one
trial a cell, so one that fails or is never reached is counted already, and every answer is
corrected for the whole count. A trial's name carries the hash of its rule's code, the rule's
class in `desk/strategy.py` and all it names there (M4): a changed rule is new trials, never a
free second look. The ladder so rebuilt is a new set, under a new question and register.

KEPT BY WHAT MADE IT (M4). The results file holds one JSON line for each cell as it finishes,
forced to disk before the next begins, the last line of a cell its answer now. Each line says
what made it, under `made`: the commit, the code this module reaches, the rule's hash, the
cell's bars, its market's, and the table of rates. A cell kept under those and the count of
trials and reproductions is skipped; change any and it is judged again. A cell that could not
be judged (a line parked or stale, too short a history for a trade, a day with no rate) keeps
its reason and the time of its last try, and is tried again no sooner than 30 minutes later.

THE RATES (M5) are one kept table under the data home, never asked for twice: a run adds the
days the table lacks and reads the rest from it, so a verdict can be made again from what it
names. A day's pounds per dollar is one over the pound's last close BEFORE that day, the rate
the desk's own day has that morning (`desk/command.py`), inside the same bounds; never a later.

A STEP OF UNITS (M3). A London line of a dollar fund can arrive part in dollars and part in
pounds, a step under the price store's jump. A close that moves in one day by that day's rate
or by one over it, to within 3%, on a day the instrument master does not name a real move, is
such a step: the cell is not judged, and waits with the day as its reason.

OWED: the stop planted; the folds as written (they are two thirds of one line, 30 trades asked
of each, and wait where a figure is on file); the shuffle; the drawdowns; one trial a cell and
the rule's hash in its name; `made`; the kept table of rates; the step of units.
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
            tally["missed"] += "error" not in row and "unrun" not in row
            tally["short"] += "unrun" in row and "answer" not in row
            tally["every"] += row.get("every", False)
            tally["behind"] += row.get("every", False) and "reproduce" in row["rungs"]
    answers = ", ".join(f"{a.name} {tally[a.name]}" for a in reversed(Answer))
    return (
        f"ladder set 1: {len(todo)} cells, each a published rule on a line, judged against "
        f"{count} trials: {tally['judged']} judged now, {tally['kept']} kept from before, "
        f"{tally['failed']} could not be judged and are tried again next run; the one rule's "
        f"answers: {answers}; {tally['short']} with no verdict, a named rung not run; "
        f"{tally['missed']} not the author's rule; {tally['every']} passed "
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
