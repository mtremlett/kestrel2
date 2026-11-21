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

import json
import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from functools import partial
from pathlib import Path
from typing import cast

from desk.lines import LINES, Line
from lab import (
    basket,
    batch,
    history_bars,
    ladder,
    ladder_pool,
    members,
    rung_retail,
    tape,
    trials,
    verdict,
    weather,
)
from lab.batch import Bars
from lab.cell import Cell
from lab.ladder import END, FOLDER, START, Kept, Plan, eponymous, run
from lab.ladder_parts import FAILED, Shared, _made, _resolve
from lab.rung import Answer, Rates

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


NL = chr(10)
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
    last = Kept(home / FOLDER / f"{plan.stem}.jsonl")
    rows = [cast(verdict.Row, last.get(tuple(batch.row(c)))) for c in todo]
    if verdict.EASED:  #: easing 2: each rule's lines also judged pooled, one basket a rule
        rows += baskets(home, bars, pounds, todo, rules, plan)
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


def _furthest(rows: Sequence[verdict.Row]) -> tuple[verdict.Row, str, str]:
    """The rule's best line (one that goes forward, else the one that ran the most rungs), the
    last rung it ran and that rung's answer with its reason."""
    best = max(rows, key=lambda r: (verdict.goes(r), len(r.get("rungs", {}))))
    rungs = best.get("rungs", {})
    if not rungs:
        return best, "none", str(best.get("error", best.get("refused", "no rung run")))
    name, (answer, why) = list(rungs.items())[-1]
    return best, name, f"{answer}: {why}"


def condense(
    table: Path, rows: Sequence[verdict.Row], rules: Sequence[str], notes: Sequence[str]
) -> None:
    """Rewrite the set's table as one row per rule (furthest rung, why, lines judged, best line)
    and keep every cell, whole, in `<tag>.cells.json` beside it."""
    cells = table.with_suffix(".cells.json")
    cells.write_text(json.dumps(list(rows), indent=1), encoding="utf-8")
    head = table.read_text(encoding="utf-8").split(NL + "## ")[0].rstrip()
    out = [head, "", f"Every cell, whole, is in `{cells.name}`.", ""]
    out += ["| rule | furthest rung | why | lines judged | best line | goes forward |"]
    out += ["|---|---|---|---|---|---|"]
    for rule, mine in verdict.by_rule(rows, rules).items():
        if not mine:
            continue
        best, rung, why = _furthest(mine)
        judged = sum("rungs" in r for r in mine)
        fields = [rule, rung, why, f"{judged} of {len(mine)}", best["cell"][1]]
        fields.append("yes" if any(map(verdict.goes, mine)) else "no")
        out.append("| " + " | ".join(f.replace("|", "/").replace(NL, " ") for f in fields) + " |")
    out += ["", "## Survivorship", ""] + [f"- {note}" for note in notes]
    table.write_text(NL.join(out) + NL, encoding="utf-8")


def baskets(
    home: Path, bars: Bars, pounds: Rates, todo: Sequence[Cell], rules: Sequence[str], plan: Plan
) -> list[verdict.Row]:
    """One basket row for each rule that has a line to pool: the lines' first rungs (a line that
    cannot be read or that the sizing refuses is left out), charged the rule's family of trials."""
    shared, rows = Shared(todo), list[verdict.Row]()
    for rule in rules:
        firsts, stresses = [], []
        for c in (one for one in todo if one.strategy == rule):
            try:
                made, own, _ = _resolve(c, bars)
                first = verdict.ready(made, own, pounds, _made(rule, shared, bars))
                firsts.append(first)
                if not first.refused:
                    stresses.append(verdict.stress_answer(made, own, pounds))
            except FAILED:
                continue
        firsts = [first for first in firsts if not first.refused]
        stressed = next((a for a in stresses if a is not Answer.PASS), Answer.PASS)
        if firsts:
            family = trials.family(home / FOLDER / f"{plan.stem}.trials.jsonl", plan.question, rule)
            against = _against(firsts[0].key.cell.line, bars, pounds)
            rows.append(basket.row(plan.tag, rule, firsts, family, stressed, against))
    return rows


def _against(line: Line, bars: Bars, pounds: Rates) -> rung_retail.Against:
    """The market a basket is set beside: its first line's venue's (`ladder.MARKETS`), its bars
    and the pound rates."""
    market = next(one for one in LINES if one.symbol == ladder.MARKETS[line.venue])
    return rung_retail.Against(market, bars(market), pounds)


def tapes_held(home: Path) -> str:
    """The tapes the ladder keeps, measured on disk: how many, and their bytes in megabytes."""
    sizes = [p.stat().st_size for p in (home / FOLDER / tape.FOLDER).glob("*.tape")]
    return f"tapes on disk: {len(sizes)} files, {sum(sizes) / 2**20:.1f} MB"


def weather_line(home: Path, bars: Bars, held: Sequence[Line]) -> str:
    """Run the weather contest (part 1) on the US market line (`ladder.MARKETS`) with breadth
    over the held lines, write weather.md and .json under ladder/sets, and say it in one line.
    A layer that joins changes no verdict yet."""
    market = next(one for one in LINES if one.symbol == ladder.MARKETS["US"])
    entries = weather.contest(bars(market), {one.symbol: bars(one) for one in held})
    (sets := home / FOLDER / "sets").mkdir(parents=True, exist_ok=True)
    weather.write(sets, entries)
    said = [
        f"{e.layer} cannot score"
        if e.contest is None
        else f"{e.layer} {'joins' if e.contest.wins else 'stays out'}, worst fold "
        f"{e.contest.layer:.6f} against trend's {e.contest.trend:.6f}"
        for e in entries
    ]
    trials_ = max((e.contest.trials for e in entries if e.contest), default=0)
    return f"weather: {'; '.join(said)}; {trials_} trials"


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
        said += "\n" + weather_line(home, make(), held)
    sys.stdout.write(said + "\n")
    return 0
