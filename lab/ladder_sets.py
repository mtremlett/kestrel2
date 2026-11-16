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
from datetime import UTC, date, datetime, timedelta
from functools import cache, lru_cache, partial
from pathlib import Path

from desk.lines import Line
from desk.store import Bar
from lab import batch, ladder, ladder_pool, members, sweep, tape, trials, universe, verdict
from lab.batch import Bars
from lab.cell import Cell
from lab.ladder import END, FOLDER, START, Plan, _last, _whole, eponymous, rates, run, stored
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


NOT_CORRECTED = "survivorship: not corrected"


def _spells(record: members.Record, line: Line) -> list[tuple[date, date]]:
    """The runs of days in [START, END] the line was on the list, as first and last days."""
    mine = [c for c in reversed(record.changes) if c.symbol == line.symbol and c.day > START]
    open_from = START if line.symbol in record.symbols(START) else None
    spells = []
    for change in mine:
        if change.joined and open_from is None:
            open_from = change.day
        elif not change.joined and open_from is not None:
            spells.append((open_from, change.day - timedelta(days=1)))  #: out on its day
            open_from = None
    return spells + ([(open_from, END)] if open_from is not None else [])


def window(line: Line, records: Mapping[str, members.Record]) -> tuple[date, date] | None:
    """The days a line was a member of any list that names it, as one window: its longest
    run of membership. None when no list's record names the line: it is traded as it is."""
    named = [
        r
        for r in records.values()
        if any(t.venue == line.venue for t in r.today)
        and line.symbol in {t.symbol for t in r.today} | {c.symbol for c in r.changes}
    ]
    if not named:
        return None
    runs = sorted(run for r in named for run in _spells(r, line))
    merged: list[tuple[date, date]] = []
    for first, last in runs:
        if merged and first <= merged[-1][1] + timedelta(days=1):
            merged[-1] = (merged[-1][0], max(last, merged[-1][1]))
        else:
            merged.append((first, last))
    never = (END, START)  #: no member day: an empty window, which `survivors` leaves out
    return max(merged, key=lambda w: w[1] - w[0]) if merged else never


def survivors(
    rules: Sequence[str], lines: Sequence[Line], records: Mapping[str, members.Record]
) -> tuple[tuple[Cell, ...], tuple[str, ...]]:
    """Each rule's cells, a line only over the days it was a member, and one note for each
    line saying whether its survivorship was corrected. A line the lists never named is traded
    over the whole window and its note says so; a line that was never a member is left out."""
    windows = {line: window(line, records) for line in lines}
    notes = tuple(
        f"{line.symbol} ({line.venue}): {NOT_CORRECTED}" for line in lines if windows[line] is None
    )
    spans = {line: windows[line] or (START, END) for line in lines}
    cells = tuple(
        Cell(rule, line, *spans[line])
        for rule in rules
        for line in lines
        if spans[line][0] <= spans[line][1]
    )
    return cells, notes


def epon(
    home: Path,
    bars: Bars,
    pounds: Rates,
    lines: Sequence[Line],
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    rules: Sequence[str] | None = None,
    go: Callable[..., str] = run,
    plan: Plan = EPON,
    records: Mapping[str, members.Record] = members.RECORDS,
) -> str:
    """A set: each rule on each line, judged and kept under the plan's own register, then its
    table written: the counts line and `SET <tag>: <n> rules, <passed> passed, table <path>`."""
    rules = eponymous() if rules is None else rules
    todo, notes = survivors(rules, lines, records)
    counts = go(home, bars, pounds, todo, now, plan)  #: a rule's lines together: its pool once
    count = trials.count(home / FOLDER / f"{plan.stem}.trials.jsonl", plan.question)
    last = _last(_whole(home / FOLDER / f"{plan.stem}.jsonl"))
    rows = [last[tuple(batch.row(c))] for c in todo]
    sets = home / FOLDER / "sets"
    table = verdict.write_table(
        sets, plan.tag, plan.question, rows, rules, count, ladder.rungs_built()
    )
    with table.open("a", encoding="utf-8") as out:
        out.write("\n## Survivorship\n\n" + "".join(f"- {note}\n" for note in notes))
    said = f"survivorship: {len(notes)} of {len(lines)} lines not corrected, none guessed"
    passed = sum(any(map(verdict.goes, mine)) for mine in verdict.by_rule(rows, rules).values())
    last_line = f"SET {plan.tag}: {len(rules)} rules, {passed} passed, table {table}"
    return f"{counts}\n{said}\n{tapes_held(home)}\n{last_line}"


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
    if argv == ["leveraged"]:
        make = partial(store_bars, home)
        held = leveraged(sweep.held(home / "grid" / "store"))
        said = epon(home, make(), rates(home=home), held, rules=TREND, go=_pooled(make), plan=LEV)
        sys.stdout.write(said + "\n")
        return 0
    if argv:
        todo, make = ladder.cells(), partial(first_bars, home)
        sys.stdout.write(ladder_pool.run(home, make, rates(home=home), todo) + "\n")
        return 0
    make = partial(store_bars, home)
    store = home / "grid" / "store"
    said = epon(home, make(), rates(home=home), sweep.held(store), go=_pooled(make))
    sys.stdout.write(said + "\n")
    return 0
