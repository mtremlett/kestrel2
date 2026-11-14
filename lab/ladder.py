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
luck rung, the deflated Sharpe and the yearly Sharpe (`lab/deflated.py`); the folds
(`lab/folds.py`); and the market's rung (`lab/market.py`). The one verdict is the one rule
over those six, every one: a cell whose folds could not be run has no verdict, and a worst
fold too thin to say holds the verdict at THIN at best, however the whole history scored. A
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
day with no rate) keeps its reason, its key and the time of its last try: it is tried again at
once when the key differs, and when it is the same no sooner than 30 minutes after. A line a
stop cut short is cut off.

THE RATES are the desk's own until the data lane keeps a rate for every day (R-RUNGS-3): each
day's pounds per dollar comes from `desk/carry.py`, the one rule the desk prices a day by, from
the same archive and inside the same bounds as the desk's day takes it (`desk/command.py`).

SET EPON (R-RUNNER-81) is what `python -m lab.ladder` runs: every rule of every
`desk/eponymous_*.py` (named in `MODULES`, so that its code is in every key; a file not named
there is refused) on every line the research store holds, in the same register, results file and
rungs. It ends by writing
`ladder/sets/EPON.md` and `.json` - each rule, each line, each rung's answer with its reason, the
trials it was judged against, the author's result beside the desk's, and what goes forward - and one
line, `SET EPON: <n> rules, <passed> passed, table <path>`. A rule has passed when it has a line
whose one verdict is PASS and whose every rung run passed. Every table is PRE-REVIEW until the blind
review (R-RUNNER-40) is clean. `python -m lab.ladder first` runs the first set of published rules.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from functools import cache, lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any

import desk
from desk import archive, carry, eponymous_bands, eponymous_connors, keeper
from desk.command import DOLLARS, POUND
from desk.lines import LINES, Line
from desk.store import Bar
from desk.strategy import STRATEGIES
from lab import batch, cell, published, reproduce, sweep, trials, universe, verdict
from lab.batch import Bars
from lab.cell import Cell
from lab.reproduce import Reproduction
from lab.rung import Answer, Rates

ME = "lab.ladder"  #: this module as the cell knows it, however the process was started
QUESTION = "set 1: does a published rule earn on one of the desk's lines?"
#: The one window: from where the daily history is to be carried back to, to the last
#: session before the set was first run. A later end is a new set of trials, on purpose.
START, END = date(2000, 1, 1), date(2026, 11, 13)
FOLDS = verdict.FOLDS
#: The market each venue's lines are set beside: the S&P 500 in New York, the FTSE 100 in London.
MARKETS = {"US": "SPY", "LSE": "ISF"}
FOLDER, RESULTS = "ladder", "set1.jsonl"
STATUS = "PRE-REVIEW"  #: what every table is until the blind review (R-RUNNER-40) is clean
#: The files of eponymous rules the ladder reads. A new `desk/eponymous_*.py` is named here, so
#: that its code is reached by the code version of every key that it could change.
MODULES: Sequence[ModuleType] = (eponymous_bands, eponymous_connors)
COLUMNS = ("rule", "line", "venue", "answer", "rungs", "trials", "reproduction", "goes forward")


@dataclass(frozen=True)
class Plan:
    """A set: its name in its rows, the question its trials are counted under, its files' name."""

    tag: int | str
    question: str
    stem: str


FIRST = Plan(1, QUESTION, "set1")
EPON = Plan("EPON", "set EPON: does an eponymous rule earn on a line the store holds?", "EPON")
#: A cell that waits on data is tried again no sooner than this after its last try.
RETRY = timedelta(minutes=30)
FAILED = (ValueError, OSError, keeper.Stale)  #: what may leave a cell unjudged; all else is a bug
Row = Mapping[str, Any]  #: a cell's line in the results file


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


def _whole(results: Path) -> bytes:
    """The results file as far as its last whole line: a line a stop cut short is cut off."""
    text = results.read_bytes() if results.exists() else b""
    return text[: text.rfind(b"\n") + 1]


def _last(whole: bytes) -> dict[tuple[str, ...], Row]:
    """Each cell's last line in the results: its answer now."""
    return {tuple(row["cell"]): row for row in map(json.loads, whole.splitlines())}


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
    """Pounds per dollar for each day to the window's end, by the desk's one rule
    (`desk/carry.py`): one over the pound's last close before the day while it is fresh, and
    across a UK-only holiday the last London session's rate, carried. A day the rule gives
    none, or whose last close is no pound's, has no rate, and the first rung refuses it."""
    closes = {
        bar.day: bar.close
        for bar in ask(POUND, END + keeper.DAY)
        if DOLLARS[0] < bar.close < DOLLARS[1]
    }
    if not closes:
        return {}
    first = min(closes)
    days = [first + n * keeper.DAY for n in range(1, (END - first).days + 1)]
    known = {day: rate for day in days if (rate := carry.pounds_per_dollar(closes, day))}
    return {day: rate for day in days if (rate := carry.carried(known, day))}


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
    results, register = (home / FOLDER / f"{plan.stem}{end}" for end in (".jsonl", ".trials.jsonl"))
    if not results.exists() and not register.exists():  #: the set's first run, and only that
        results.parent.mkdir(parents=True, exist_ok=True)
        (fresh := register.with_suffix(".new")).unlink(missing_ok=True)
        trials.start(fresh)
        trials.ask(fresh, plan.question)
        fresh.replace(register)  #: whole or not there: a stop before this begins it again
    count = trials.enter(register, plan.question, [name for c in todo for name in names(c)])
    whole = _whole(results)
    last = _last(whole)
    behind: dict[str, tuple[Reproduction, ...]] = {}
    tally: Counter[str] = Counter()
    with results.open("ab") as out:
        out.truncate(len(whole))
        for c in todo:
            was = last.get(tuple(batch.row(c)))
            row = _one(c, bars, pounds, (plan.tag, count), was, behind, now())
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
        f"ladder set {plan.tag}: {len(todo)} cells, each a rule on a line, judged against "
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
    tagged: tuple[int | str, int],
    was: Row | None,
    behind: dict[str, tuple[Reproduction, ...]],
    now: datetime,
) -> Row:
    """The cell's line: the one kept, where it is kept under the key these bars, rates and
    trials give; else its answers now, or why it could not be judged. It is judged from the
    line's first bar, so that its years are years it could trade in."""
    tag, count = tagged
    head: dict[str, Any] = {"set": tag, "cell": batch.row(c), "trials": count}
    key = None  #: what this try covers, once the cell's bars are read
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
        head |= {"reproduction": [reproduce.said(one) for one in made]} if made else {}
        key = hashlib.sha256("\n".join(parts).encode()).hexdigest()
        if was is not None and was.get("key") == key and not _due(was, now):
            return was  #: kept, or failed on all of this before and tried not long ago
        judged = verdict.judge(c, own, beside, held, pounds, count, made)
        return head | {"key": key, "from": c.start.isoformat()} | judged
    except FAILED as error:
        if was is not None and "error" in was and "key" not in was and not _due(was, now):
            return was  #: its bars could not be read, and it was tried not long ago
        return (
            head
            | ({} if key is None else {"key": key})
            | {"error": f"{type(error).__name__}: {error}", "tried": now.isoformat()}
        )


def _due(was: Row, now: datetime) -> bool:
    """A failed cell is tried again once its last try is 30 minutes old; a kept one never."""
    return "error" in was and now - datetime.fromisoformat(was["tried"]) >= RETRY


def eponymous(
    modules: Sequence[ModuleType] = MODULES, folder: Path = Path(desk.__file__).parent
) -> tuple[str, ...]:
    """The name of every rule of every `desk/eponymous_*.py`. A file not named in `MODULES`, or
    one that names its rules in no `EPONYMOUS`, is refused: its rules would be judged on code
    the keys do not reach, or not at all."""
    files = {path.stem for path in folder.glob("eponymous_*.py")}
    if files != {m.__name__.rpartition(".")[2] for m in modules}:
        raise ValueError(f"{sorted(files)} are not the modules the ladder names: {MODULES}")
    names: list[str] = []
    for module in modules:
        if not hasattr(module, "EPONYMOUS"):
            raise ValueError(f"{module.__name__} names its rules in no EPONYMOUS mapping")
        names += module.EPONYMOUS
    if len(set(names)) != len(names):
        raise ValueError(f"an eponymous rule is named twice: {sorted(names)}")
    return tuple(names)


def epon(
    home: Path,
    bars: Bars,
    pounds: Rates,
    lines: Sequence[Line],
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    rules: Sequence[str] | None = None,
) -> str:
    """Set EPON: each rule on each line, judged and kept, then its table written: the counts
    line and `SET EPON: <n> rules, <passed> passed, table <path>`."""
    rules = eponymous() if rules is None else rules
    todo = tuple(Cell(rule, line, START, END) for line in lines for rule in rules)
    counts = run(home, bars, pounds, todo, now, EPON)  #: a line's rules together: its bars once
    count = trials.count(home / FOLDER / f"{EPON.stem}.trials.jsonl", EPON.question)
    last = _last(_whole(home / FOLDER / f"{EPON.stem}.jsonl"))
    rows = [last[tuple(batch.row(c))] for c in todo]
    table = _table(home / FOLDER / "sets", rows, rules, count)
    passed = sum(any(map(_goes, mine)) for mine in _by_rule(rows, rules).values())
    return f"{counts}\nSET {EPON.tag}: {len(rules)} rules, {passed} passed, table {table}"


def _goes(row: Row) -> bool:
    """A cell goes forward when its one verdict is PASS and every rung run passed."""
    return row.get("answer") == Answer.PASS.name and bool(row.get("every"))


def _by_rule(rows: Iterable[Row], rules: Sequence[str]) -> dict[str, list[Row]]:
    rows = list(rows)
    return {rule: [row for row in rows if row["cell"][0] == rule] for rule in rules}


def _said(row: Row) -> list[str]:
    """A cell's table line: its answer, each rung's answer and reason, and the author's result."""
    rungs = [f"{name} {a}: {why}" for name, (a, why) in row.get("rungs", {}).items()]
    unrun = [f"{name} UNRUN: {why}" for name, why in row.get("unrun", {}).items()]
    own = row.get("reproduction") or [row.get("unrun", {}).get("reproduce", "")]
    result = (
        f"not judged, tried again next run: {row['error']}" if "error" in row else " | ".join(own)
    )
    text = " <br> ".join(rungs + unrun) or row.get("error", "")
    return [
        row.get("answer", "none"),
        text,
        str(row["trials"]),
        result,
        "yes" if _goes(row) else "no",
    ]


def _table(folder: Path, rows: Sequence[Row], rules: Sequence[str], count: int) -> Path:
    """The set's results table, `EPON.md` and `EPON.json`, labelled PRE-REVIEW."""
    folder.mkdir(parents=True, exist_ok=True)
    mine = _by_rule(rows, rules)
    data: dict[str, object] = {
        "set": EPON.tag,
        "question": EPON.question,
        "status": STATUS,
        "trials": count,
    }
    data["rules"] = [
        {"rule": r, "passed": any(map(_goes, rs)), "cells": rs} for r, rs in mine.items()
    ]
    (folder / f"{EPON.tag}.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
    out = [
        f"# SET {EPON.tag} - {STATUS}",
        "",
        f"{EPON.question} Judged against {count} trials.",
        "",
    ]
    out += [f"{STATUS}: not final until the blind review (R-RUNNER-40) is clean.", ""]
    for rule, rs in mine.items():
        out += [f"## {rule}: {sum(map(_goes, rs))} of {len(rs)} lines go forward", ""]
        out += ["| " + " | ".join(COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]
        for row in rs:
            cells = [rule, row["cell"][1], row["cell"][2], *_said(row)]
            out.append(
                "| " + " | ".join(c.replace("|", "/").replace("\n", " ") for c in cells) + " |"
            )
        out.append("")
    (path := folder / f"{EPON.tag}.md").write_text("\n".join(out), encoding="utf-8")
    return path


def main(env: Mapping[str, str], argv: Sequence[str] = ()) -> int:
    """Set EPON on every line the research store holds; `first` runs the first set instead."""
    if not env.get("KESTREL2_DATA"):
        sys.exit("ladder: KESTREL2_DATA names no data folder, so the set has no home")
    home = Path(env["KESTREL2_DATA"])
    if list(argv) not in ([], ["first"]):
        sys.exit(f"ladder: {list(argv)} is no set; the command takes nothing, or `first`")
    if argv:
        sys.stdout.write(run(home, cache(stored(home)), rates()) + "\n")
        return 0
    store = home / "grid" / "store"  #: the research store, one folder to a venue

    def read(line: Line) -> Sequence[Bar]:
        """The line's bars to the window's end, as research reads them."""
        return [bar for bar in universe.read(store, line).bars if bar.day <= END]

    read = lru_cache(maxsize=4)(read)
    sys.stdout.write(epon(home, read, rates(), sweep.held(store)) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(os.environ, sys.argv[1:]))
