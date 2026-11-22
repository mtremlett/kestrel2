"""ladder_parts - WHAT THE LADDER'S CELLS HOLD IN COMMON (R-RUNNER-237): the part of
`lab/ladder.py` that resolves a cell to its bars and proxy, pools a rule's lines for the folds,
adds the declared rungs to a cell's answers and counts its line. Split out of `lab/ladder.py`,
which imports it and still answers to every name; it never imports the ladder."""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from desk import keeper
from desk.lines import LINES, Line
from desk.store import Bar
from lab import cell, reproduce, verdict
from lab.batch import Bars
from lab.cell import Cell
from lab.reproduce import Reproduction
from lab.rung import Answer, Rates

RUNGS = "lab"  #: the package whose `rung_*` modules declare the rungs the ladder runs
PROXIES = {"VUAG": "SPY"}  #: a short-history line and the longer series that may stand in for it
#: A cell that waits on data is tried again no sooner than this after its last try.
RETRY = timedelta(minutes=30)
FAILED = (ValueError, OSError, keeper.Stale)  #: what may leave a cell unjudged; all else is a bug
UNWIRED = "the ladder does not yet judge by these modules, which declare no RUNG"


@dataclass
class Shared:
    """What the cells of one run hold in common, asked once for each rule."""

    todo: Sequence[Cell]
    behind: dict[str, tuple[Reproduction, ...]] = field(default_factory=dict)
    pools: dict[str, verdict.Pool] = field(default_factory=dict)


def _resolve(c: Cell, bars: Bars) -> tuple[Cell, Sequence[Bar], Line | None]:
    """The cell as judged from its first bar, with its bars (a proxy's where one stands in)."""
    own = bars(c.line)
    if proxy := _proxy(c.line, own, bars):
        c, own = Cell(c.strategy, proxy, c.start, c.end), bars(proxy)
    start = max([c.start, *(bar.day for bar in own[:1])])
    return Cell(c.strategy, c.line, start, c.end), own, proxy


def _pool(rule: str, shared: Shared, bars: Bars, pounds: Rates) -> verdict.Pool:
    """The rule's lines that can be judged; one that waits is left out of the folds. A proxy is
    pooled once. Only the rule at hand is kept: its bars are most of the memory."""
    if rule not in shared.pools:
        shared.pools.clear()
        firsts, lines = {}, {}
        for c in (one for one in shared.todo if one.strategy == rule):
            try:
                made, own, _ = _resolve(c, bars)
                firsts[made] = verdict.ready(made, own, pounds, shared.behind[rule])
            except FAILED:
                continue
            if not firsts[made].refused:  #: a line the sizing refuses is judged alone, as refused
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


def _declared(
    judged: dict[str, Any],
    pool: verdict.Pool,
    c: Cell,
    own: Sequence[Bar],
    pounds: Rates,
    made: Sequence[Reproduction],
    found: tuple[Sequence[Any], Sequence[str]],
) -> dict[str, Any]:
    """The cell's answers with each rung that its module declares (`rung.found`) added, judged
    on the first rung's verdict; the one rule's answer stays the named rungs'. A rung module
    that declares none is named unrun. A cell with no first rung (the author's result not
    reproduced) has none to read."""
    declared, waiting = found
    if "trades" not in judged:
        return judged
    modules = ", ".join(name.rpartition(".")[2] for name in waiting)
    unrun = judged["unrun"] | ({"unwired": f"{UNWIRED}: {modules}"} if waiting else {})
    rungs, added = dict(judged["rungs"]), {}
    for one in declared:
        added[one.name] = one.judge(pool.firsts.get(c) or verdict.ready(c, own, pounds, made))
        rungs[one.name] = [added[one.name][0].name, added[one.name][1]]
    every = judged["every"] and verdict.every(added)
    return judged | {"rungs": rungs, "unrun": unrun, "every": every}


def _proxy(line: Line, own: Sequence[Bar], bars: Bars) -> Line | None:
    """The line named to stand in for this one, when its bars begin earlier than the line's own."""
    stand = next((one for one in LINES if one.symbol == PROXIES.get(line.symbol)), None)
    longer = bars(stand) if stand else ()
    return stand if longer and (not own or longer[0].day < own[0].day) else None


def _due(was: verdict.Row, now: datetime) -> bool:
    """A failed cell is tried again once its last try is 30 minutes old."""
    return "error" in was and now - datetime.fromisoformat(was["tried"]) >= RETRY


def faults(rows: Iterable[verdict.Row]) -> tuple[list[str], bool]:
    """One line for each rung that any judged cell FAULTed on: its share of the cells, the rung
    and the commonest reason; and whether most of the cells did (a set that judged nothing)."""
    judged = [row["rungs"] for row in rows if "rungs" in row]
    said, mostly = [], False
    for name in dict.fromkeys(n for rungs in judged for n in rungs):
        reasons = Counter(
            r[name][1] for r in judged if name in r and r[name][0] == Answer.FAULT.name
        )
        if reasons:
            share = sum(reasons.values())
            why = reasons.most_common(1)[0][0]
            said.append(f"FAULT: {share} of {len(judged)} cells at rung {name}: {why}")
            mostly |= 2 * share > len(judged)
    return said, mostly
