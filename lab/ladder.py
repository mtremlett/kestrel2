"""ladder - THE LADDER'S FIRST SET: every published rule the desk holds, on every one of the
desk's lines, through every rung that is built, each answer kept with its reason and the
number of trials it was judged against. It can be stopped and run again, and ends with one
line of counts.

NOTHING IS CHOSEN BY EYE. The set is every rule with a publication on file (`lab/published.py`) on
every line of its declared universe, over one window fixed before any result, from the line's first
bar. EVERY TRIAL IS COUNTED BEFORE ANYTHING IS RUN: each cell is entered in the set's register
(`lab/trials.py`) before the first is judged, so a cell that fails or is never reached is
counted, and every answer is corrected for the whole count.

THE RUNGS RUN, each answer in its own words (`rung.Answer`) with its reason: the author's result
(`lab/reproduce.py`), the first, luck and yearly rungs (`lab/deflated.py`), the folds (the last
five whole years pooled over the rule's lines; a fold is no trial) and the market's. The
one verdict is the one rule over those six: a cell whose folds could not be run has none, a worst
fold too thin to say holds it at THIN, a rule whose author's figure is not reproduced has none.
A rung not yet runnable is named on every line (UNRUN). Nothing goes to paper before all eleven.

THE RUNG MAP (L2): the plan's eleven rungs, each `n name: module, test`. They are not a row's
names: `first` holds 1-3, `market` 4 (against the market) and 6 (against the line held). The
test is where the rung's own proof goes (L3-L13), no two the same, and every rung owes it; one
sharing a module changes it only for a defect. A file not yet there is marked (unbuilt); after
the dash, what else is known to be owed.
 1 sample size, effective trades: lab/rung.py, tests/unit/test_lab_rung.py - bets pooled over lines
 2 costs charged: lab/rung.py, tests/unit/test_lab_rung_costs.py (unbuilt)
 3 a confidence interval: lab/rung.py, tests/unit/test_lab_rung_interval.py (unbuilt)
 4 excess after market risk, by size: lab/market.py, tests/unit/test_lab_market.py
 5 two regime windows: lab/regime.py, tests/unit/test_lab_regime.py - unrun: no weather (REG-01)
 6 benchmark excess by interval: lab/market.py, tests/unit/test_lab_market_line.py (unbuilt)
 7 deflated Sharpe: lab/deflated.py, tests/unit/test_lab_deflated.py - one clustered set (L14)
 8 purged cross-validation: lab/purged.py (unbuilt), tests/unit/test_lab_purged.py (unbuilt)
 9 placebo on blocks of days: lab/shuffle.py, tests/unit/test_lab_shuffle.py - days, not blocks
10 walk-forward folds: lab/folds.py, tests/unit/test_lab_folds.py - the ladder runs `pool`
11 block bootstrap: lab/montecarlo.py, tests/unit/test_lab_montecarlo.py - single trades, no gate

RARE LARGE LOSSES (G2, R-RUNNER-103). Nine small wins in ten and a loss at the stop in the tenth,
worth nothing together, show thirty wins and no loss one time in twenty-four. So wherever the
first rung judges trades it counts ONE MORE, which the rule did not make: a loss at its own
stop, the least any judged trade would have made had its stop sold it, with a stop's costs. It
is a trade in the standard errors and all read from them (the luck's chance; the Sharpe, its
count, skew and kurtosis), and none of the verdict's trades: in no count of the 30 asked.

A PROXY (R-RUNNER-95): a line with less history than its named proxy is judged on the proxy's
longer bars, labelled `proxy: SPY for VUAG`; the cell stays the real line.
REFUSED (R-RUNNER-108): a line the desk's sizing refuses at its capital is a judged outcome
(`refused by the desk's sizing: <reason>`), kept, counted apart from errors, not forward.
KEPT BY WHAT MADE IT. The results file holds one JSON line per cell as it finishes, forced to
disk, found again by its key: the code this module reaches, the cell's bars and its market's,
the rates, the count of trials and the reproductions behind it. A cell kept under that key is
skipped; change any and it is judged again. A cell that could not be judged (a line parked or
stale, too short a history, a day with no rate) keeps its reason and key: tried again when the
key differs, else after 30 minutes. A cut line is cut off.

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
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import desk
from desk import archive, carry, keeper
from desk.command import DOLLARS, POUND
from desk.lines import LINES, Line
from desk.orders import Refused
from desk.store import Bar
from desk.strategy import STRATEGIES, Rule
from lab import batch, cell, published, reproduce, rulebook, rung, tape, trials, verdict
from lab.batch import Bars
from lab.cell import Cell
from lab.reproduce import Reproduction
from lab.rung import Answer, Rates

ME = "lab.ladder"  #: this module as the cell knows it, however the process was started
QUESTION = "set 1: does a published rule earn on one of the desk's lines?"
#: The one window: from where the daily history is carried back to, to the last session
#: before the set first ran. A later end is a new set of trials, on purpose.
START, END = date(2000, 1, 1), date(2026, 11, 13)
FOLDS = verdict.FOLDS
#: The market each venue's lines are set beside: the S&P 500 in New York, the FTSE 100 in London.
MARKETS = {"US": "SPY", "LSE": "ISF"}
PROXIES = {"VUAG": "SPY"}  #: a short-history line and the longer series that may stand in for it
FOLDER, RESULTS, POUNDS = "ladder", "set1.jsonl", "pound.jsonl"
DESK = Path(desk.__file__).parent  #: the one list of eponymous files: this folder


@dataclass(frozen=True)
class Plan:
    """A set: its name in its rows, its trials' question, its files' name."""

    tag: int | str
    question: str
    stem: str


FIRST = Plan(1, QUESTION, "set1")
#: A cell that waits on data is tried again no sooner than this after its last try.
RETRY = timedelta(minutes=30)
FAILED = (ValueError, OSError, keeper.Stale)  #: what may leave a cell unjudged; all else is a bug


def cells() -> tuple[Cell, ...]:
    """The set: every published rule on every line it declares."""
    return tuple(
        Cell(name, line, START, END)
        for name in published.PUBLISHED
        for line in STRATEGIES[name].declared.universe
    )


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
    """Each line's daily bars to the window's end, through the keeper's door: a line parked or
    not refreshed that far is refused."""

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


@dataclass
class Shared:
    """What the cells of one run hold in common, asked once for each rule."""

    todo: Sequence[Cell]
    behind: dict[str, tuple[Reproduction, ...]] = field(default_factory=dict)
    pools: dict[str, verdict.Pool] = field(default_factory=dict)


def _resolve(c: Cell, bars: Bars) -> tuple[Cell, Sequence[Bar], Line | None]:
    """The cell as judged, from its line's first bar so that its years are years it could trade
    in, with its bars: its proxy's, longer, where one stands in (the third, the proxy)."""
    own = bars(c.line)
    if proxy := _proxy(c.line, own, bars):
        c, own = Cell(c.strategy, proxy, c.start, c.end), bars(proxy)
    start = max([c.start, *(bar.day for bar in own[:1])])
    return Cell(c.strategy, c.line, start, c.end), own, proxy


def _pool(rule: str, shared: Shared, bars: Bars, pounds: Rates) -> verdict.Pool:
    """The rule's lines that can be judged: one that waits (on bars, years, units or a rate) is
    left out of the folds. A proxy is pooled once. Only the rule at hand is kept: its bars are
    most of the memory, and a set runs a rule's cells together."""
    if rule not in shared.pools:
        shared.pools.clear()
        firsts, lines = {}, {}
        for c in (one for one in shared.todo if one.strategy == rule):
            try:
                made, own, _ = _resolve(c, bars)
                firsts[made] = verdict.ready(made, own, pounds, shared.behind[rule])
            except (*FAILED, Refused):  #: a line the sizing refuses is judged alone, as refused
                continue
            lines[made] = own
        dollars = any(c.line.currency != "GBP" for c in lines)
        data = ";".join(f"{c.line.symbol} {cell.key(c, own).data}" for c, own in lines.items())
        data = hashlib.sha256(data.encode()).hexdigest()
        shared.pools[rule] = verdict.Pool(list(lines.items()), firsts, data, dollars)
    return shared.pools[rule]


def _count(tally: Counter[str], row: verdict.Row, was: verdict.Row | None) -> None:
    """Add one cell's line to the counts."""
    fate = next((k for k in ("error", "refused") if k in row), "kept" if row is was else "judged")
    tally[fate] += 1
    tally[row.get("answer", "none")] += 1
    tally["missed"] += fate in ("kept", "judged") and "unrun" not in row
    tally["short"] += "unrun" in row and "answer" not in row
    tally["every"] += row.get("every", False)
    tally["behind"] += row.get("every", False) and "reproduce" in row["rungs"]


def _made(rule: str, shared: Shared, bars: Bars) -> tuple[Reproduction, ...]:
    """The rule's reproductions of its authors' figures, made once for all its cells."""
    if rule not in shared.behind:
        owed = [figure for figure in reproduce.FIGURES if figure.strategy == rule]
        shared.behind[rule] = tuple(reproduce.reproduce(f, bars(f.line)) for f in owed)
    return shared.behind[rule]


def _one(
    c: Cell,
    bars: Bars,
    pounds: Rates,
    tagged: tuple[int | str, int],
    was: verdict.Row | None,
    shared: Shared,
    now: datetime,
) -> verdict.Row:
    """The cell's line: the one kept, where it is kept under the key these bars, rates and
    trials give; else its answers now, or why it could not be judged."""
    tag, count = tagged
    head: dict[str, Any] = {"set": tag, "cell": batch.row(c), "trials": count}
    key = None  #: what this try covers, once the cell's bars are read
    try:
        line = c.line
        c, own, proxy = _resolve(c, bars)
        head |= {"proxy": f"proxy: {proxy.symbol} for {line.symbol}"} if proxy else {}
        beside = next(one for one in LINES if one.symbol == MARKETS[c.line.venue])
        held = bars(beside)
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
        head |= {"reproduction": [reproduce.said(one) for one in made]} if made else {}
        key = hashlib.sha256(";".join(parts).encode()).hexdigest()
        if was is not None and was.get("key") == key and not _due(was, now):
            return was  #: kept, or failed on all of this before and tried not long ago
        folded = lambda: pool.fold(pounds, made)  # noqa: E731 - asked for only if the folds are read
        judged = verdict.judge(
            c, own, beside, held, pounds, count, made, folded, pool.firsts.get(c)
        )
        return head | {"key": key, "from": c.start.isoformat()} | judged
    except Refused as error:  #: the desk's sizing declines the line at this capital: judged
        reason = f"refused by the desk's sizing: {error}"
        return head | ({} if key is None else {"key": key}) | {"refused": reason}
    except FAILED as error:
        if was is not None and "error" in was and "key" not in was and not _due(was, now):
            return was  #: its bars could not be read, and it was tried not long ago
        return (
            head
            | ({} if key is None else {"key": key})
            | {"error": f"{type(error).__name__}: {error}", "tried": now.isoformat()}
        )


def _proxy(line: Line, own: Sequence[Bar], bars: Bars) -> Line | None:
    """The line named to stand in for this one, when its bars begin earlier than the line's own."""
    stand = next((one for one in LINES if one.symbol == PROXIES.get(line.symbol)), None)
    longer = bars(stand) if stand else ()
    return stand if longer and (not own or longer[0].day < own[0].day) else None


def _due(was: verdict.Row, now: datetime) -> bool:
    """A failed cell is tried again once its last try is 30 minutes old."""
    return "error" in was and now - datetime.fromisoformat(was["tried"]) >= RETRY


def code(folder: Path = DESK) -> str:
    """sha256 of the text of every eponymous file, a Windows line ending not a change: part of
    every key, so no rule is judged on code the keys do not reach."""
    texts = [p.read_bytes().replace(b"\r\n", b"\n") for p in sorted(folder.glob("eponymous_*.py"))]
    return hashlib.sha256(b"\0".join(texts)).hexdigest()


CODE = code()  #: the eponymous files as this process loaded them: in every key


def eponymous(folder: Path = DESK) -> tuple[str, ...]:
    """The name of every rule of every `desk/eponymous_*.py`, by the rule book; a file with no
    `EPONYMOUS` is refused, by name. A rule that takes data (Zweig's breadth) is left out."""
    for path in sorted(folder.glob("eponymous_*.py")):
        module = importlib.import_module(f"{desk.__name__}.{path.stem}")
        if not hasattr(module, "EPONYMOUS"):
            raise ValueError(f"{module.__name__} names its rules in no EPONYMOUS mapping")
    return tuple(n for n, make in rulebook.eponymous(folder).items() if not _needs_data(make))


def _needs_data(make: type[Rule]) -> bool:
    """Whether the rule cannot be made without an argument."""
    return any(p.default is p.empty for p in inspect.signature(make).parameters.values())


if __name__ == "__main__":
    from lab import ladder_sets

    sys.exit(ladder_sets.main(os.environ, sys.argv[1:]))
