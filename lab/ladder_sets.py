"""ladder_sets - THE LADDER'S SETS AS A COMMAND: set EPON (R-RUNNER-81), its table, and the
`python -m lab.ladder` door. Every rule of every `desk/eponymous_*.py` on every line the
research store holds, judged by the cell engine of `lab/ladder.py`, in its register and
results file; it writes `ladder/sets/EPON.md` and `.json` - each rule, line and rung's answer
with its reason, the trials, the author's result beside the desk's, what goes forward - and
ends `SET EPON: <n> rules, <passed> passed, table <path>`. A rule has passed when a line's one
verdict is PASS and every rung run passed. Every table is PRE-REVIEW until the blind review
(R-RUNNER-40) is clean. `python -m lab.ladder first` runs the first set instead.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from functools import cache, lru_cache
from pathlib import Path

from desk.lines import Line
from desk.store import Bar
from lab import batch, sweep, trials, universe
from lab.batch import Bars
from lab.cell import Cell
from lab.ladder import END, FOLDER, START, Plan, Row, _last, _whole, eponymous, rates, run, stored
from lab.rung import Answer, Rates

STATUS = "PRE-REVIEW"  #: what every table is until the blind review (R-RUNNER-40) is clean
COLUMNS = ("rule", "line", "venue", "answer", "rungs", "trials", "reproduction", "goes forward")
EPON = Plan("EPON", "set EPON: does an eponymous rule earn on a line the store holds?", "EPON")


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


def _by_rule(rows: Sequence[Row], rules: Sequence[str]) -> dict[str, list[Row]]:
    return {rule: [row for row in rows if row["cell"][0] == rule] for rule in rules}


def _said(row: Row) -> list[str]:
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
        "yes" if _goes(row) else "no",
    ]


def _table(folder: Path, rows: Sequence[Row], rules: Sequence[str], count: int) -> Path:
    """The set's results table, `EPON.md` and `EPON.json`, labelled PRE-REVIEW."""
    folder.mkdir(parents=True, exist_ok=True)
    mine = _by_rule(rows, rules)
    data: dict[str, object] = {"set": EPON.tag, "question": EPON.question, "status": STATUS}
    data |= {"trials": count, "refused": sum("refused" in row for row in rows)}
    data |= {
        "rules": [{"rule": r, "passed": any(map(_goes, rs)), "cells": rs} for r, rs in mine.items()]
    }
    (folder / f"{EPON.tag}.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
    head = f"{EPON.question} Judged against {count} trials."
    out = [f"# SET {EPON.tag} - {STATUS}", "", head, ""]
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
        sys.stdout.write(run(home, cache(stored(home)), rates(home=home)) + "\n")
        return 0
    store = home / "grid" / "store"  #: the research store, one folder to a venue

    def read(line: Line) -> Sequence[Bar]:  #: the line's bars to the window's end
        return [bar for bar in universe.read(store, line).bars if bar.day <= END]

    sys.stdout.write(
        epon(home, lru_cache(maxsize=4)(read), rates(home=home), sweep.held(store)) + "\n"
    )
    return 0
