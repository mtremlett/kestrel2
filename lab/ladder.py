"""ladder - THE LADDER'S FIRST SET: every published rule the desk holds, on every one of the
desk's lines, through every rung that is built, each answer kept with its reason and the
number of trials it was judged against. It can be stopped and run again, and ends with one
line of counts.

NOTHING IS CHOSEN BY EYE. The set is every rule with a publication on file (`lab/published.py`) on
every line of its declared universe, over one window fixed before any result, from the line's first
bar. EVERY TRIAL IS COUNTED BEFORE ANYTHING IS RUN: each cell is entered in the set's register
(`lab/trials.py`) before the first is judged, so a cell that fails or is never reached is
counted, and every answer is corrected for the whole count.

THE RUNGS RUN, each answer in its own words (`rung.Answer`): the author's result
(`lab/reproduce.py`), the first, luck and yearly rungs (`lab/deflated.py`), the folds (the last
five whole years pooled over the rule's lines; a fold is no trial) and the market's. The one
verdict is the one rule over those six: no folds, or an author's figure not reproduced, gives
none; a worst fold too thin to say holds it at THIN. A rung not yet runnable is named on every
line (UNRUN). Nothing goes to paper before all eleven.

THE RUNG MAP (L2): the plan's eleven rungs, each `n name: module, test`. A row's names differ:
`first` holds 1-3, `market` 4 and 6. Each rung's proof is in its own test; (unbuilt) marks a file
not yet there; after the dash, what is owed. BUILT: the ladder judges by it (it declares a RUNG).
 1 sample size, effective trades: lab/rung_sample.py, tests/unit/test_lab_rung_sample.py
 2 costs charged: lab/rung_costs.py, tests/unit/test_lab_rung_costs.py
 3 a confidence interval: lab/rung_ci.py, tests/unit/test_lab_rung_ci.py
 4 excess after market risk, by size: lab/rung_beta.py, tests/unit/test_lab_rung_beta.py
 5 two regime windows: lab/rung_regimes.py, tests/unit/test_lab_rung_regimes.py - unrun: no weather
 6 benchmark excess by interval: lab/rung_benchmark.py, tests/unit/test_lab_rung_benchmark.py
 7 deflated Sharpe: lab/rung_dsr.py, tests/unit/test_lab_rung_dsr.py - one clustered set (L14)
 8 purged cross-validation: lab/rung_cpcv.py, tests/unit/test_lab_rung_cpcv.py
 9 placebo on blocks of days: lab/rung_placebo.py, tests/unit/test_lab_rung_placebo.py
10 walk-forward folds: lab/rung_folds.py, tests/unit/test_lab_rung_folds.py - the ladder runs `pool`
11 block bootstrap: lab/rung_bootstrap.py, tests/unit/test_lab_rung_bootstrap.py - no gate

RARE LARGE LOSSES (G2, R-RUNNER-103). The first rung counts ONE MORE trade the rule did not make: a
loss at its own stop, the least any judged trade would have made, in the standard errors and all
read from them and in no count of the 30 asked. A loss that GAPS THROUGH the stop is not covered:
the blind review (R-RUNNER-40) passed such noise at the first rung on up to 19 lines in 100.

A PROXY (R-RUNNER-95): a line with less history than its named proxy is judged on the proxy's
bars, labelled `proxy: SPY for VUAG`. REFUSED (R-RUNNER-108): a line the desk's sizing refuses
is a judged outcome (`refused by the desk's sizing: <reason>`), kept, counted apart from errors.
KEPT BY WHAT MADE IT. The results file holds one JSON line per cell as it finishes, forced to
disk, found again by its key: the code this module reaches, the cell's bars and its market's,
the rates, the count of trials and the reproductions. A cell kept under that key is skipped;
change any and it is judged again. A cell that could not be judged (a line parked or stale, a
short history, a day with no rate) keeps its reason and key, and is judged again only when the
key differs; one with no key (its bars could not be read) is tried again after 30 minutes. A
row is appended only when it differs from the cell's last. A cut line is cut off.

The sets as a command - SET EPON and the `python -m lab.ladder` door - are `lab/ladder_sets.py`.
"""

from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import os
import sys
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import desk
from desk import archive, carry, keeper
from desk.command import DOLLARS, POUND
from desk.lines import LINES, Line
from desk.store import Bar
from desk.strategy import STRATEGIES, Rule
from lab import batch, cell, published, reproduce, rulebook, rung, tape, trials, verdict
from lab.batch import Bars
from lab.cell import Cell
from lab.ladder_parts import FAILED, RUNGS, Shared, _count, _declared, _due, _made, _pool, _resolve
from lab.rung import Answer, Rates

__all__ = ["FAILED", "RUNGS", "Shared", "_count", "_resolve"]  #: what other modules take from here
ME = "lab.ladder"  #: this module as the cell knows it, however the process was started
QUESTION = "set 1: does a published rule earn on one of the desk's lines?"
#: The one window: from where the daily history is carried back to, to the last session
#: before the set first ran. A later end is a new set of trials, on purpose.
START, END = date(2000, 1, 1), date(2026, 11, 13)
FOLDS = verdict.FOLDS
#: The market each venue's lines are set beside: the S&P 500 in New York, the FTSE 100 in London.
MARKETS = {"US": "SPY", "LSE": "ISF"}
FOLDER, RESULTS, POUNDS = "ladder", "set1.jsonl", "pound.jsonl"
DESK = Path(desk.__file__).parent  #: the one list of eponymous files: this folder


@dataclass(frozen=True)
class Plan:
    """A set: its name in its rows, its trials' question, its files' name."""

    tag: int | str
    question: str
    stem: str


FIRST = Plan(1, QUESTION, "set1")


def cells() -> tuple[Cell, ...]:
    """The set: every published rule on every line it declares."""
    return tuple(
        Cell(name, line, START, END)
        for name in published.PUBLISHED
        for line in STRATEGIES[name].declared.universe
    )


def rungs_built() -> tuple[int, int]:
    """The map's rungs the ladder judges by (their module declares a RUNG), and the map's rungs."""
    paragraph = (__doc__ or "").split("THE RUNG MAP")[1].split("\n\n")[0]
    rows = [line for line in paragraph.splitlines() if line.lstrip()[:1].isdigit()]
    mods = {r.split("lab/")[1].split(".py")[0] for r in rows if "(unbuilt)" not in r}
    return len(mods - {n.rpartition(".")[2] for n in rung.found(RUNGS)[1]}), len(rows)


def names(c: Cell) -> list[str]:
    """The trials a cell costs, as the register names them: itself alone, for a fold is no trial."""
    return [trials.name(c)]


def _whole(results: Path) -> bytes:
    """The results file as far as its last whole line: a line a stop cut short is cut off."""
    text = results.read_bytes() if results.exists() else b""
    return text[: text.rfind(b"\n") + 1]


def _last(whole: bytes) -> dict[tuple[str, ...], verdict.Row]:
    """Each cell's last line in the results: its answer now."""
    return {tuple(row["cell"]): row for row in map(json.loads, whole.splitlines())}


def stored(home: Path) -> Bars:
    """Each line's daily bars to the window's end, by the keeper; a stale line is refused."""

    def bars(line: Line) -> Sequence[Bar]:
        held, parked = keeper.saved(home, END + keeper.DAY, [line])
        if parked:
            raise ValueError(f"{line.symbol}: parked by the price store; waits on its bars")
        return held[line]

    return bars


def rates(
    ask: Callable[[Line, date], Sequence[Bar]] = archive.fetch, home: Path | None = None
) -> dict[date, Decimal]:
    """Pounds per dollar for each day to the window's end, by `desk/carry.py`'s one rule: one over
    the pound's last close before the day while fresh, carried across a UK-only holiday, else none.
    With a home, asked of the archive only while the kept table lacks END."""
    held = rung.kept_closes(
        home and home / FOLDER / POUNDS, END, lambda: ask(POUND, END + keeper.DAY)
    )
    closes = {day: close for day, close in held.items() if DOLLARS[0] < close < DOLLARS[1]}
    first = min(closes, default=END)  #: no closes, no days, no rates
    days = [first + n * keeper.DAY for n in range(1, (END - first).days + 1)]
    known = {day: rate for day in days if (rate := carry.pounds_per_dollar(closes, day))}
    return {day: rate for day in days if (rate := carry.carried(known, day))}


def begun(home: Path, todo: Sequence[Cell], plan: Plan) -> tuple[Path, int]:
    """The set's results file and its count of trials entered; the register made on a first run."""
    results, register = (home / FOLDER / (plan.stem + e) for e in (".jsonl", ".trials.jsonl"))
    if not results.exists() and not register.exists():  #: the set's first run, and only that
        results.parent.mkdir(parents=True, exist_ok=True)
        (fresh := register.with_suffix(".new")).unlink(missing_ok=True)
        trials.start(fresh)
        trials.ask(fresh, plan.question)
        fresh.replace(register)  #: whole or not there: a stop before this begins it again
    return results, trials.enter(register, plan.question, [n for c in todo for n in names(c)])


def run(
    home: Path,
    bars: Bars,
    pounds: Rates,
    todo: Sequence[Cell] | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    plan: Plan = FIRST,
) -> str:
    """The set judged and kept under home, a cell kept already skipped: the one line of counts."""
    if cell.code_version(module=ME) != cell.RUNGS[ME]:
        raise RuntimeError("the code on disk has changed since this process loaded it")
    todo = cells() if todo is None else todo
    results, count = begun(home, todo, plan)
    whole = _whole(results)
    last = _last(whole)
    shared = Shared(todo)
    tally: Counter[str] = Counter()
    with tape.on(home / FOLDER / tape.FOLDER), results.open("ab") as out:
        out.truncate(len(whole))
        for c in todo:
            was = last.get(tuple(batch.row(c)))
            row = _one(c, bars, pounds, (plan.tag, count), was, shared, now())
            if row != was:
                out.write(json.dumps(row).encode() + b"\n")
                out.flush()
                os.fsync(out.fileno())
            _count(tally, row, was)
    answers = ", ".join(f"{a.name} {tally[a.name]}" for a in reversed(Answer))
    return (
        f"ladder set {plan.tag}: {len(todo)} cells, each a rule on a line, judged against "
        f"{count} trials: {tally['judged']} judged now, {tally['kept']} kept from before, "
        f"{tally['error']} could not be judged and are tried again next run, "
        f"{tally['refused']} refused by the desk's sizing; the one rule's "
        f"answers: {answers}; {tally['short']} with no verdict, a named rung not run; "
        f"{tally['missed']} not the author's rule; {tally['every']} passed "
        f"every rung run, {tally['behind']} of them behind an author's result; none goes to "
        "paper before all eleven rungs are built."
    )


def _one(
    c: Cell,
    bars: Bars,
    pounds: Rates,
    tagged: tuple[int | str, int],
    was: verdict.Row | None,
    shared: Shared,
    now: datetime,
) -> verdict.Row:
    """The cell's line: the one kept under the key these bars, rates and trials give, else its
    answers now, or why it could not be judged."""
    tag, count = tagged
    head: dict[str, Any] = {"set": tag, "cell": batch.row(c), "trials": count}
    key = None  #: what this try covers, once the cell's bars are read
    try:
        c, own, proxy = _resolve(c, bars)
        head |= {"proxy": f"proxy: {proxy.symbol} for {head['cell'][1]}"} if proxy else {}
        held = bars(beside := next(one for one in LINES if one.symbol == MARKETS[c.line.venue]))
        made = _made(c.strategy, shared, bars)
        pool = _pool(c.strategy, shared, bars, pounds)
        mine = cell.key(c, own).rung(ME)
        days = sorted(
            day for day in pounds if day <= c.end and (c.line.currency != "GBP" or pool.dollars)
        )
        market = cell.key(Cell(c.strategy, beside, c.start, c.end), held).data
        rates = (f"{d} {pounds[d]}" for d in days)
        parts = [mine.code, CODE, mine.data, market, pool.data, str(count), *rates]
        parts += [one.key.code + one.key.data for one in made]
        declared, waiting = rung.found(RUNGS)  #: both are in the row, so both are in its key
        parts += [one.name + one.code for one in declared] + list(waiting)
        head |= {"reproduction": [reproduce.said(one) for one in made]} if made else {}
        key = hashlib.sha256(";".join(parts).encode()).hexdigest()
        if was is not None and was.get("key") == key:
            return was  #: kept, or failed on all of this before: it waits for its key to change
        if (first := pool.firsts.get(c)) is not None and first.refusal is not None:
            reason = f"refused by the desk's sizing: {first.refusal}"
            return head | {"key": key, "refused": reason}
        folded = lambda: pool.fold(pounds, made)  # noqa: E731 - asked for only if the folds are read
        judged = verdict.judge(c, own, beside, held, pounds, count, made, folded, first)
        done = _declared(judged, pool, c, own, pounds, made)
        return head | {"key": key, "from": c.start.isoformat()} | done
    except FAILED as error:
        if was is not None and "error" in was and "key" not in was and not _due(was, now):
            return was  #: its bars could not be read, and it was tried not long ago
        return (
            head
            | ({} if key is None else {"key": key})
            | {"error": f"{type(error).__name__}: {error}", "tried": now.isoformat()}
        )


def code(folder: Path = DESK) -> str:
    """sha256 of every eponymous file's text, line endings aside: part of every key."""
    texts = [p.read_bytes().replace(b"\r\n", b"\n") for p in sorted(folder.glob("eponymous_*.py"))]
    return hashlib.sha256(b"\0".join(texts)).hexdigest()


CODE = code()  #: the eponymous files as this process loaded them: in every key


def eponymous(folder: Path = DESK, book: Path | None = None) -> tuple[str, ...]:
    """Every rule of every `desk/eponymous_*.py`, then any the catalogue's specs add; a file with no
    `EPONYMOUS` is refused. A rule that takes data (Zweig's breadth) is left out. A name in both is
    one rule, listed once: the specs are read beside the Python rules, so none goes unregistered
    when the Python ones go."""
    for path in sorted(folder.glob("eponymous_*.py")):
        module = importlib.import_module(f"{desk.__name__}.{path.stem}")
        if not hasattr(module, "EPONYMOUS"):
            raise ValueError(f"{module.__name__} names its rules in no EPONYMOUS mapping")
    python = tuple(n for n, make in rulebook.eponymous(folder).items() if not _needs_data(make))
    return python + tuple(n for n in rulebook.specs(book, folder) if n not in python)


def _needs_data(make: type[Rule]) -> bool:
    """Whether the rule cannot be made without an argument."""
    return any(p.default is p.empty for p in inspect.signature(make).parameters.values())


if __name__ == "__main__":
    from lab import ladder_sets

    sys.exit(ladder_sets.main(os.environ, sys.argv[1:]))
