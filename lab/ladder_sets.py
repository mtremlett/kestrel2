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

import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from functools import cache, lru_cache, partial
from pathlib import Path

from desk.lines import Line
from desk.store import Bar
from lab import batch, ladder, ladder_pool, sweep, tape, trials, universe, verdict
from lab.batch import Bars
from lab.cell import Cell
from lab.ladder import END, FOLDER, START, Plan, _last, _whole, eponymous, rates, run, stored
from lab.rung import Rates

EPON = Plan("EPON", "set EPON: does an eponymous rule earn on a line the store holds?", "EPON")


def epon(
    home: Path,
    bars: Bars,
    pounds: Rates,
    lines: Sequence[Line],
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    rules: Sequence[str] | None = None,
    go: Callable[..., str] = run,
) -> str:
    """Set EPON: each rule on each line, judged and kept, then its table written: the counts
    line and `SET EPON: <n> rules, <passed> passed, table <path>`."""
    rules = eponymous() if rules is None else rules
    todo = tuple(Cell(rule, line, START, END) for rule in rules for line in lines)
    counts = go(home, bars, pounds, todo, now, EPON)  #: a rule's lines together: its pool once
    count = trials.count(home / FOLDER / f"{EPON.stem}.trials.jsonl", EPON.question)
    last = _last(_whole(home / FOLDER / f"{EPON.stem}.jsonl"))
    rows = [last[tuple(batch.row(c))] for c in todo]
    sets = home / FOLDER / "sets"
    table = verdict.write_table(
        sets, EPON.tag, EPON.question, rows, rules, count, ladder.rungs_built()
    )
    passed = sum(any(map(verdict.goes, mine)) for mine in verdict.by_rule(rows, rules).values())
    last_line = f"SET {EPON.tag}: {len(rules)} rules, {passed} passed, table {table}"
    return f"{counts}\n{tapes_held(home)}\n{last_line}"


def tapes_held(home: Path) -> str:
    """The tapes the ladder keeps, measured on disk: how many, and their bytes in megabytes."""
    sizes = [p.stat().st_size for p in (home / FOLDER / tape.FOLDER).glob("*.tape")]
    return f"tapes on disk: {len(sizes)} files, {sum(sizes) / 2**20:.1f} MB"


def first_bars(home: Path) -> Bars:
    """The first set's bars, as a worker makes them for itself."""
    return cache(stored(home))


def store_bars(home: Path) -> Bars:
    """The research store's bars to the window's end, as a worker makes them for itself."""
    store = home / "grid" / "store"  #: the research store, one folder to a venue

    def read(line: Line) -> Sequence[Bar]:
        return [bar for bar in universe.read(store, line).bars if bar.day <= END]

    return lru_cache(maxsize=4)(read)


def _pooled(make: Callable[[], Bars]) -> Callable[..., str]:
    """`run` on the pool, the bars made in each worker by `make`."""
    return lambda home, _, pounds, todo, now, plan: ladder_pool.run(
        home, make, pounds, todo, now, plan
    )


def main(env: Mapping[str, str], argv: Sequence[str] = ()) -> int:
    """Set EPON on every line the research store holds; `first` runs the first set instead.
    Both run on the pool (R-RUNNER-110): every core but two."""
    if not env.get("KESTREL2_DATA"):
        sys.exit("ladder: KESTREL2_DATA names no data folder, so the set has no home")
    home = Path(env["KESTREL2_DATA"])
    if list(argv) not in ([], ["first"]):
        sys.exit(f"ladder: {list(argv)} is no set; the command takes nothing, or `first`")
    if argv:
        todo, make = ladder.cells(), partial(first_bars, home)
        sys.stdout.write(ladder_pool.run(home, make, rates(home=home), todo) + "\n")
        return 0
    make = partial(store_bars, home)
    store = home / "grid" / "store"
    said = epon(home, make(), rates(home=home), sweep.held(store), go=_pooled(make))
    sys.stdout.write(said + "\n")
    return 0
