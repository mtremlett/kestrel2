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

THE RUNG MAP (L2): the plan's eleven rungs and easing 4's twelfth, each `n name: module, test`.
A row's names differ:
`first` holds 1-3, `market` 4 and 6. Each rung's proof is in its own test; (unbuilt) marks a file
not yet there; after the dash, what is owed. BUILT: its module declares a RUNG, so the ladder
judges by it; every other row owes `no RUNG` first (the test holds the two to agree).
 1 sample size, effective trades: lab/rung_sample.py, tests/unit/test_lab_rung_sample.py - no RUNG
 2 costs charged: lab/rung_costs.py, tests/unit/test_lab_rung_costs.py
 3 a confidence interval: lab/rung_ci.py, tests/unit/test_lab_rung_ci.py
 4 excess after market risk, by size: lab/market.py, tests/unit/test_lab_rung_beta.py - no RUNG
 5 two regime windows: lab/rung_regimes.py, tests/unit/test_lab_rung_regimes.py
 6 benchmark excess: lab/rung_benchmark.py, tests/unit/test_lab_rung_benchmark.py - no RUNG
 7 deflated Sharpe: lab/rung_dsr.py, tests/unit/test_lab_rung_dsr.py - no RUNG; L14's clustered set
 8 purged cross-validation: lab/rung_cpcv.py, tests/unit/test_lab_rung_cpcv.py
 9 placebo on blocks of days: lab/rung_placebo.py, tests/unit/test_lab_rung_placebo.py - no RUNG
10 walk-forward folds: lab/folds.py, tests/unit/test_lab_folds.py - no RUNG; the ladder runs `pool`
11 block bootstrap: lab/rung_bootstrap.py, tests/unit/test_lab_rung_bootstrap.py - no RUNG, no gate
12 retail, basket beside market: lab/rung_retail.py, tests/unit/test_lab_rung_retail.py - no RUNG

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
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import desk
from desk import carry, keeper
from desk.command import CAPITAL, DOLLARS, POUND
from desk.lines import LINES, Line
from desk.store import Bar
from desk.strategy import STRATEGIES, Rule
from lab import batch, cell, published, reproduce, rulebook, rung, tape, trials, verdict
from lab.batch import Bars
from lab.cell import Cell
from lab.ladder_parts import (
    FAILED,
    RUNGS,
    Shared,
    _count,
    _declared,
    _due,
    _made,
    _pool,
    _resolve,
    faults,
)
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
FOLDER, RESULTS = "ladder", "set1.jsonl"
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
    mods = {r.split("lab/")[1].split(".py")[0] for r in rows if ".py (unbuilt)" not in r}
    return sum(hasattr(importlib.import_module(f"lab.{m}"), "RUNG") for m in mods), len(rows)


def names(c: Cell) -> list[str]:
    """The trials a cell costs, as the register names them: itself alone, for a fold is no trial."""
    return [trials.name(c)]


class Kept:
    """The results file read line by line into an index of offsets only: each cell's last whole
    line (its answer now) is found by seek, and `end` is where the last whole line ends, so a
    line a stop cut short is cut off. No row is held."""

    def __init__(self, results: Path) -> None:
        self.path = results
        self._read()

    def _read(self) -> None:
        self.at, self.end, self.lines = {}, 0, 0
        if not self.path.exists():
            return
        with self.path.open("rb") as file:
            for line in file:
                if not line.endswith(b"\n"):
                    break
                self.at[tuple(json.loads(line)["cell"])] = (self.end, len(line))
                self.end += len(line)
                self.lines += 1

    def compact(self) -> None:
        """When superseded lines outnumber live cells, the file is rewritten once with each cell's
        last line only: a temp file beside it, then replaced: a stop leaves it whole."""
        if self.lines - len(self.at) <= len(self.at):
            return
        fresh = self.path.with_suffix(".compact")
        with fresh.open("wb") as out:
            for offset, size in sorted(self.at.values()):
                with self.path.open("rb") as file:
                    file.seek(offset)
                    out.write(file.read(size))
            out.flush()
            os.fsync(out.fileno())
        fresh.replace(self.path)
        self._read()

    def get(self, key: tuple[str, ...]) -> verdict.Row | None:
        """The cell's last line, read back from the file, or None."""
        if key not in self.at:
            return None
        offset, size = self.at[key]
        with self.path.open("rb") as file:
            file.seek(offset)
            return cast(verdict.Row, json.loads(file.read(size)))

    def rows(self) -> Iterator[verdict.Row]:
        """Every cell's last line, one at a time."""
        return (cast(verdict.Row, self.get(key)) for key in self.at)


def rates(ask: Callable[[Line, date], Sequence[Bar]] | None = None) -> dict[date, Decimal]:
    """Pounds per dollar for each day to the window's end, by `desk/carry.py`'s one rule: one over
    the pound's last close before the day while fresh, carried across a UK-only holiday, else none.
    The pound's bars come from `ask` alone, the one door (`history_bars.pounds`); none: raises."""
    if ask is None:
        raise ValueError("ladder.rates: no source of the pound's bars; pass history_bars' door")
    held = {bar.day: bar.close for bar in ask(POUND, END + keeper.DAY)}
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
    last = Kept(results)
    shared = Shared(todo)
    register = results.with_suffix(".trials.jsonl")
    kin = lambda rule: trials.family(register, plan.question, rule)  # noqa: E731 - read when EASED
    tally: Counter[str] = Counter()
    with tape.on(home / FOLDER / tape.FOLDER), results.open("ab") as out:
        out.truncate(last.end)
        for c in todo:
            was = last.get(tuple(batch.row(c)))
            row = _one(c, bars, pounds, (plan.tag, count), was, shared, now(), kin)
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
    kin: Callable[[str], int] | None = None,
) -> verdict.Row:
    """The cell's line: the one kept under the key these bars, rates and trials give, else its
    answers now, or why it could not be judged."""
    tag, count = tagged
    family = kin(c.strategy) if verdict.EASED and kin else None  #: the rule's trials, if EASED
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
            d for d in pounds if d <= c.end and (c.line.currency != "GBP" or pool.dollars)
        )
        market = cell.key(Cell(c.strategy, beside, c.start, c.end), held).data
        parts = [mine.code, mine.data, market, pool.data, str(count), f"capital {CAPITAL}"]
        parts += [f"{d} {pounds[d]}" for d in days] + ([] if family is None else [f"in {family}"])
        parts += [tape.rule_code(c.strategy)] + [one.key.code + one.key.data for one in made]
        found = rung.found(RUNGS)
        parts += [one.name + one.code for one in found[0]] + list(found[1])  #: both are in its key
        head |= {"reproduction": [reproduce.said(one) for one in made]} if made else {}
        key = hashlib.sha256(";".join(parts).encode()).hexdigest()
        if was is not None and was.get("key") == key:
            return was  #: kept, or failed on all of this before: it waits for its key to change
        if (first := pool.firsts.get(c)) is not None and first.refusal is not None:
            return head | {"key": key, "refused": f"refused by the desk's sizing: {first.refusal}"}
        folded = lambda: pool.fold(pounds, made)  # noqa: E731 - asked for only if the folds are read
        judged = verdict.judge(c, own, beside, held, pounds, count, made, folded, first, family)
        done = _declared(judged, pool, c, own, pounds, made, found)
        return head | {"key": key, "from": c.start.isoformat()} | done
    except FAILED as error:
        if was is not None and "error" in was and "key" not in was and not _due(was, now):
            return was  #: its bars could not be read, and it was tried not long ago
        return (
            head
            | ({} if key is None else {"key": key})
            | {"error": f"{type(error).__name__}: {error}", "tried": now.isoformat()}
        )


def eponymous(folder: Path = DESK, book: Path | None = None) -> tuple[str, ...]:
    """Every rule of every `desk/eponymous_*.py`, then any the catalogue's specs add; a file with no
    `EPONYMOUS` is refused. A rule that takes data (Zweig's breadth) is left out. A name in both is
    one rule, listed once: the specs are read beside the Python rules, so none goes unregistered
    when the Python ones go."""
    for path in sorted(folder.glob("eponymous_*.py")):
        module = importlib.import_module(f"{desk.__name__}.{path.stem}")
        if not hasattr(module, "EPONYMOUS"):
            raise ValueError(f"{module.__name__} names its rules in no EPONYMOUS mapping")
    every = rulebook.eponymous(folder)
    python = tuple(n for n, make in every.items() if not _needs_data(make))
    return python + tuple(
        n for n in rulebook.specs(book, folder) if n not in python and not _needs_data(every[n])
    )


def _needs_data(make: type[Rule]) -> bool:
    """Whether the rule cannot be made without an argument."""
    return any(p.default is p.empty for p in inspect.signature(make).parameters.values())


def door(env: Mapping[str, str], argv: Sequence[str]) -> int:
    """The command: the set run, then each rung any cell FAULTed on said on its own line with its
    share and reason; 1 when most cells FAULTed, so a set that judged nothing is never green.
    The intraday and scalping sets keep no results file (their table is all), so none is read."""
    from lab import ladder_sets

    code = ladder_sets.main(env, argv)
    sets = {"": ladder_sets.EPON, "first": FIRST}
    sets |= {"leveraged": ladder_sets.LEV, "variants": ladder_sets.VAR}
    plan = sets.get(argv[0] if argv else "")
    if plan is None:
        return code
    kept = Kept(Path(env["KESTREL2_DATA"]) / FOLDER / f"{plan.stem}.jsonl")
    kept.compact()  #: once the set is judged, never while a run holds the file
    said, mostly = faults(kept.rows())
    sys.stdout.write("".join(f"{line}" + chr(10) for line in said))
    return code or int(mostly)


if __name__ == "__main__":
    sys.exit(door(os.environ, sys.argv[1:]))
