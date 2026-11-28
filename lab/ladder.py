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

The rung map, and its count of rungs built, are `lab/ladder_map.py`'s (R-RUNNER-571): a new rung
adds its row there, never here.

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
Split out of it (O79): the results file read by offset (`lab/ladder_kept.py`), the set's
pre-flight (`lab/ladder_preflight.py`) and the eponymous rules' list (`lab/ladder_epon.py`).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from desk import carry, keeper
from desk.command import CAPITAL, POUND
from desk.lines import DOLLARS, LINES, Line
from desk.store import Bar
from desk.strategy import STRATEGIES
from lab import batch, cell, published, reproduce, rung, tape, trials, verdict
from lab.batch import Bars
from lab.cell import Cell
from lab.ladder_kept import Kept
from lab.ladder_map import rungs_built as rungs_built  #: its callers' name (R-RUNNER-571)
from lab.ladder_parts import (
    FAILED,
    MARKETS,
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
from lab.ladder_preflight import _priced, _unrated, preflight
from lab.rung import Answer, Rates

#: What other modules take from here.
__all__ = ["FAILED", "MARKETS", "RUNGS", "Shared", "_count", "_resolve"]
ME = "lab.ladder"  #: this module as the cell knows it, however the process was started
QUESTION = "set 1: does a published rule earn on one of the desk's lines?"
#: The one window: from where the daily history is carried back to, to the last session
#: before the set first ran. A later end is a new set of trials, on purpose.
START, END = date(2000, 1, 1), date(2026, 11, 13)
FOLDS = verdict.FOLDS
FOLDER, RESULTS = "ladder", "set1.jsonl"


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


def names(c: Cell) -> list[str]:
    """The trials a cell costs, as the register names them: itself alone, for a fold is no trial."""
    return [trials.name(c)]


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
    preflight(todo, bars, pounds)
    results, count = begun(home, todo, plan)
    last = Kept(results)
    shared = Shared(todo)
    tally: Counter[str] = Counter()
    with tape.on(home / FOLDER / tape.FOLDER), results.open("ab") as out:
        out.truncate(last.end)
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
    """The cell's row: kept under the key of its bars, rates, trials; else judged, or why not."""
    tag, count = tagged
    head: dict[str, Any] = {"set": tag, "cell": batch.row(c), "trials": count}
    key = None  #: what this try covers, once the cell's bars are read
    try:
        c, own, proxy = _resolve(c, bars)
        head |= {"proxy": f"proxy: {proxy.symbol} for {head['cell'][1]}"} if proxy else {}
        held = bars(beside := next(one for one in LINES if one.symbol == MARKETS[c.line.venue]))
        made = _made(c.strategy, shared, bars)
        pool = _pool(c.strategy, shared, _priced(bars, pounds, c.strategy, shared.todo), pounds)
        mine = cell.key(c, own).rung(ME)
        days = sorted(
            d for d in pounds if d <= c.end and (c.line.currency != "GBP" or pool.dollars)
        )
        market = cell.key(Cell(c.strategy, beside, c.start, c.end), held).data
        parts = [mine.code, mine.data, market, pool.data, str(count), f"capital {CAPITAL}"]
        parts += [f"{d} {pounds[d]}" for d in days]
        parts += [tape.rule_code(c.strategy)] + [one.key.code + one.key.data for one in made]
        found = rung.found(RUNGS)
        parts += [one.name + one.code for one in found[0]] + list(found[1])  #: both are in its key
        head |= {"reproduction": [reproduce.said(one) for one in made]} if made else {}
        key = hashlib.sha256(";".join(parts).encode()).hexdigest()
        if was is not None and was.get("key") == key:
            return was  #: kept, or failed on all of this before: it waits for its key to change
        if (first := pool.firsts.get(c)) is not None and first.refusal is not None:
            return head | {"key": key, "refused": f"refused by the desk's sizing: {first.refusal}"}
        if gap := _unrated(c, ((c.line, own), (beside, held)), pounds):
            raise ValueError(gap)  #: the cell's reason, kept under its key; never a FAULT
        folded = lambda: pool.fold(pounds, made)  # noqa: E731 - asked for only if the folds are read
        look = None if first is None else pool.among(c)  #: L18: among its rule's own lines
        judged = verdict.judge(c, own, beside, held, pounds, count, made, folded, first, None, look)
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


def door(env: Mapping[str, str], argv: Sequence[str]) -> int:
    """The command: the set run, then each rung any cell FAULTed on said on its own line with its
    share and reason; 1, and NOT PUBLISHED said, when over 1% of its cells FAULTed (L20).
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
    said, shown = faults(kept.rows())
    sys.stdout.write("".join(f"{line}" + chr(10) for line in said))
    return code or int(not shown)


if __name__ == "__main__":
    sys.exit(door(os.environ, sys.argv[1:]))
