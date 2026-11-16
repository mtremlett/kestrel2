"""ladder_sets - THE LADDER'S SETS AS A COMMAND: set EPON (R-RUNNER-81), its table, and the
`python -m lab.ladder` door. Every rule of every `desk/eponymous_*.py` on every line the
research store holds, judged by the cell engine of `lab/ladder.py`, in its register and
results file; it writes `ladder/sets/EPON.md` and `.json` - each rule, line and rung's answer
with its reason, the trials, the author's result beside the desk's, what goes forward - and
ends `SET EPON: <n> rules, <passed> passed, table <path>`. A rule has passed when a line's one
verdict is PASS and every rung run passed. Every table is PRE-REVIEW until the blind review
(R-RUNNER-40) is clean. `python -m lab.ladder first` runs the first set instead; `leveraged`
runs set LEV (STR-18): six trend rules, named in `TREND`, on the leveraged lines only, judged
on their own trial count.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from functools import partial
from pathlib import Path

from desk.lines import Line
from lab import batch, history_bars, ladder, ladder_pool, tape, trials, verdict
from lab.batch import Bars
from lab.cell import Cell
from lab.ladder import END, FOLDER, START, Plan, _last, _whole, eponymous, run
from lab.rung import Rates

EPON = Plan("EPON", "set EPON: does an eponymous rule earn on a line the store holds?", "EPON")
LEV = Plan("LEV", "set LEV: does a trend rule earn on a leveraged line the store holds?", "LEV")
#: Set LEV's family, named before any result (STR-18): the eponymous rules that follow a trend,
#: none that fades one. Adding a rule is a new set. Its trials are its rules times its lines,
#: not the 63,920 of EPON, whose family is every rule on every line.
TREND = (
    "donchian_channel_breakout",
    "faber_tactical",
    "weinstein_stage",
    "keltner_channel_trend",
    "clenow_momentum",
    "minervini_breakout",
)


def epon(
    home: Path,
    bars: Bars,
    pounds: Rates,
    lines: Sequence[Line],
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    rules: Sequence[str] | None = None,
    go: Callable[..., str] = run,
    plan: Plan = EPON,
) -> str:
    """A set: each rule on each line, judged and kept under the plan's own register, then its
    table written: the counts line and `SET <tag>: <n> rules, <passed> passed, table <path>`."""
    rules = eponymous() if rules is None else rules
    todo = tuple(Cell(rule, line, START, END) for rule in rules for line in lines)
    counts = go(home, bars, pounds, todo, now, plan)  #: a rule's lines together: its pool once
    count = trials.count(home / FOLDER / f"{plan.stem}.trials.jsonl", plan.question)
    last = _last(_whole(home / FOLDER / f"{plan.stem}.jsonl"))
    rows = [last[tuple(batch.row(c))] for c in todo]
    sets = home / FOLDER / "sets"
    table = verdict.write_table(
        sets, plan.tag, plan.question, rows, rules, count, ladder.rungs_built()
    )
    passed = sum(any(map(verdict.goes, mine)) for mine in verdict.by_rule(rows, rules).values())
    last_line = f"SET {plan.tag}: {len(rules)} rules, {passed} passed, table {table}"
    return f"{counts}\n{tapes_held(home)}\n{last_line}"


def tapes_held(home: Path) -> str:
    """The tapes the ladder keeps, measured on disk: how many, and their bytes in megabytes."""
    sizes = [p.stat().st_size for p in (home / FOLDER / tape.FOLDER).glob("*.tape")]
    return f"tapes on disk: {len(sizes)} files, {sum(sizes) / 2**20:.1f} MB"


def _pooled(make: Callable[[], Bars]) -> Callable[..., str]:
    """`run` on the pool, the bars made in each worker by `make`."""
    return lambda home, _, pounds, todo, now, plan: ladder_pool.run(
        home, make, pounds, todo, now, plan
    )


def leveraged(lines: Sequence[Line]) -> tuple[Line, ...]:
    """The lines that make more than their market's daily move."""
    return tuple(line for line in lines if line.leverage > 1)


def main(env: Mapping[str, str], argv: Sequence[str] = ()) -> int:
    """Set EPON on every line the research store holds; `first` runs the first set instead and
    `leveraged` set LEV, the trend rules on the leveraged lines. All run on the pool
    (R-RUNNER-110): every core but two."""
    if not env.get("KESTREL2_DATA"):
        sys.exit("ladder: KESTREL2_DATA names no data folder, so the set has no home")
    home = Path(env["KESTREL2_DATA"])
    if list(argv) not in ([], ["first"], ["leveraged"]):
        sys.exit(
            f"ladder: {list(argv)} is no set; the command takes nothing, `first` or `leveraged`"
        )
    make = partial(history_bars.reader, home)
    pounds, held = history_bars.pounds(home), history_bars.lines(home)
    if argv == ["leveraged"]:
        held = leveraged(held)
        said = epon(home, make(), pounds, held, rules=TREND, go=_pooled(make), plan=LEV)
    elif argv:
        said = ladder_pool.run(home, make, pounds, ladder.cells())
    else:
        said = epon(home, make(), pounds, held, go=_pooled(make))
    sys.stdout.write(said + "\n")
    return 0
