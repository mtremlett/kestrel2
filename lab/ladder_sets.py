"""ladder_sets - THE LADDER'S SETS AS A COMMAND: set EPON (R-RUNNER-81), its table, and the
`python -m lab.ladder` door. Every rule of every `desk/eponymous_*.py` on every line the
research store holds, judged by the cell engine of `lab/ladder.py`, in its register and
results file; it writes `ladder/sets/EPON.md` and `.json` - each rule, line and rung's answer
with its reason, the trials, the author's result beside the desk's, what goes forward - and
ends `SET EPON: <n> rules, <passed> passed, table <path>`. A rule has passed when a line's one
verdict is PASS and every rung run passed. Every table is PRE-REVIEW until the blind review
(R-RUNNER-40) is clean. `first` runs set 1 instead, its table published too; `leveraged`
runs set LEV (STR-18): six trend rules, named in `TREND`, on the leveraged lines only, judged
on their own trial count. `variants` names set VAR before any result (canon B6): every variant
of every ranged catalogue row entered as a trial in its own register; none is judged yet (GC).
`transfer` publishes set 2, the grid's transfer study, from the file `lab/transfer.py` wrote.
A set that ends with its `SET` line is told to his phone once (LAD-09), through the one door.
A set refused by its pre-flight for gaps in its inputs exits `WAITS` (3) for the store's next fill.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from functools import partial
from pathlib import Path
from typing import cast

from desk import keeper, messenger
from desk.lines import LINES, Line
from lab import (
    basket,
    batch,
    folds,
    history_bars,
    intraday,
    ladder,
    ladder_pool,
    members,
    rulebook,
    scalping,
    tape,
    transfer,
    trials,
    variants,
    verdict,
    weather,
)
from lab.batch import Bars
from lab.cell import Cell
from lab.ladder import END, FOLDER, START, Kept, Plan, eponymous, run
from lab.ladder_parts import FAILED, Shared, _made, _resolve, faults
from lab.published_epon import TESTED
from lab.rung import Answer, Rates, Verdict

#: The command's exit when a set's pre-flight finds gaps in its inputs (`folds.Gaps`): it waits for
#: the greenkeeper's next fill of the store, an event; never 1, a fault, which halts the job.
WAITS = 3
EPON = Plan("EPON", "set EPON: does an eponymous rule earn on a line the store holds?", "EPON")
LEV = Plan("LEV", "set LEV: does a trend rule earn on a leveraged line the store holds?", "LEV")
VAR = Plan("VAR", "set VAR: does a variant of a ranged catalogue row earn on a line?", "VAR")
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


def _names(record: members.Record, line: Line) -> bool:
    """Whether the list's record names the line, today or in its changes."""
    return any(t.venue == line.venue for t in record.today) and line.symbol in (
        {t.symbol for t in record.today} | {c.symbol for c in record.changes}
    )


def window(line: Line, records: Mapping[str, members.Record]) -> tuple[date, date] | None:
    """The days a line was a member of any list that names it, as one window: its longest
    run of membership. None when no list's record names the line: it is traded as it is."""
    named = [r for r in records.values() if _names(r, line)]
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


def _bias(line: Line, first: date, records: Mapping[str, members.Record]) -> str:
    """A line's survivorship note: `members.bias` of the first list naming it, from its first
    day; a line no list names says it is not corrected."""
    for name, record in records.items():
        if _names(record, line):
            return members.bias(name, max(first, members.FIRST))  #: a record starts at FIRST
    return NOT_CORRECTED


def survivors(
    rules: Sequence[str], lines: Sequence[Line], records: Mapping[str, members.Record]
) -> tuple[tuple[Cell, ...], tuple[str, ...]]:
    """Each rule's cells, a line only over the days it was a member, and one note for each
    line saying whether its survivorship was corrected. A line the lists never named is traded
    over the whole window and its note says so; a line that was never a member is left out."""
    windows = {line: window(line, records) for line in lines}
    spans = {line: windows[line] or (START, END) for line in lines}
    notes = tuple(
        f"{line.symbol} ({line.venue}): " + _bias(line, spans[line][0], records)
        for line in lines
        if spans[line][0] <= spans[line][1]
    )
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
    return publish(home, bars, pounds, (todo, rules, notes), counts, plan, len(lines))


def first(
    home: Path,
    make: Callable[[], Bars],
    pounds: Rates,
    todo: Sequence[Cell] | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> str:
    """Set 1 on the pool, each published rule on the lines it declares, whole (none corrected
    for survivorship), its table published as every set's is (L16)."""
    todo = ladder.cells() if todo is None else todo
    counts = _pooled(make)(home, None, pounds, todo, now, ladder.FIRST)
    rules = tuple(dict.fromkeys(c.strategy for c in todo))
    notes = tuple(
        f"{one.symbol} ({one.venue}): {NOT_CORRECTED}"
        for one in dict.fromkeys(c.line for c in todo)
    )
    return publish(home, make(), pounds, (todo, rules, notes), counts, ladder.FIRST, len(notes))


def publish(
    home: Path,
    bars: Bars,
    pounds: Rates,
    judged: tuple[Sequence[Cell], Sequence[str], Sequence[str]],
    counts: str,
    plan: Plan,
    lines: int,
) -> str:
    """A judged set's table, `rungs built: n of 12` in its header, and the set's closing lines;
    `judged` is its cells, rules and survivorship notes, of `lines` lines."""
    todo, rules, notes = judged
    last = Kept(home / FOLDER / f"{plan.stem}.jsonl")
    kept = [last.get(tuple(batch.row(c))) for c in todo]
    if counts.startswith(ladder_pool.STOPPED) or None in kept:  #: no table of a pass cut short
        return counts  #: by STOP, nor of cells never judged: older rows would stand as this pass
    count = trials.count(home / FOLDER / f"{plan.stem}.trials.jsonl", plan.question)
    rows = [cast(verdict.Row, row) for row in kept]
    stop, shown = faults(rows)  #: over 1% of the cells FAULT, baskets aside: withheld (L20)
    if verdict.EASED:  #: easing 2: each rule's lines also judged pooled, one basket a rule
        rows += baskets(bars, pounds, todo, rules, plan)
    sets = home / FOLDER / "sets"
    table = verdict.write_table(
        sets, plan.tag, plan.question, rows, rules, count, ladder.rungs_built()
    )
    withheld = [] if shown else ["", "## NOT PUBLISHED", "", *(f"- {line}" for line in stop)]
    with table.open("a", encoding="utf-8") as out:
        out.write("\n## Survivorship\n\n" + "".join(f"- {note}\n" for note in notes))
        out.write(NL.join(_authors(rules) + withheld) + NL)
    said = survivorship_said(notes, lines)
    said += "" if shown else NL + stop[-1]
    passed = sum(any(map(verdict.goes, mine)) for mine in verdict.by_rule(rows, rules).values())
    last_line = f"SET {plan.tag}: {len(rules)} rules, {passed} passed, table {table}"
    return f"{counts}\n{said}\n{tapes_held(home)}\n{last_line}"


def survivorship_said(notes: Sequence[str], lines: int) -> str:
    """The set's survivorship line: how many of its lines no list corrected."""
    left = sum(note.endswith(NOT_CORRECTED) for note in notes)
    return f"survivorship: {left} of {lines} lines not corrected, none guessed"


def _authors(rules: Sequence[str]) -> list[str]:
    """The table's lines for each rule's published test (`published_epon.TESTED`)."""
    tested = [f"- {rule}: {TESTED[rule].said()}" for rule in rules if rule in TESTED]
    return ["", "## The authors' tests, none yet reproduced", "", *tested]


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
    out += ["", "## Survivorship", ""] + [f"- {note}" for note in notes] + _authors(rules)
    table.write_text(NL.join(out) + NL, encoding="utf-8")


def baskets(
    bars: Bars, pounds: Rates, todo: Sequence[Cell], rules: Sequence[str], plan: Plan
) -> list[verdict.Row]:
    """One basket row for each rule that has a line to pool: the lines' first rungs (a line that
    cannot be read or that the sizing refuses is left out), each basket one look among the set's
    baskets, one a rule (L18: never every line the register ever held)."""
    shared, pooled = Shared(todo), list[tuple[str, list[Verdict], Answer]]()
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
        stressed = min(stresses, default=Answer.PASS)  #: the least of its lines' stress
        pooled += [(rule, firsts, stressed)] if firsts else []
    return [  #: charged the baskets the set judges, never a rule that gave none
        basket.row(plan.tag, rule, firsts, len(pooled), stressed, _against(firsts[0], bars, pounds))
        for rule, firsts, stressed in pooled
    ]


def _against(first: Verdict, bars: Bars, pounds: Rates) -> basket.Against:
    """The market a basket is set beside: its first line's venue's (`ladder.MARKETS`), its bars
    and the pound rates; a market the keeper refuses is one with no bars, the retail rung's gap."""
    venue = first.key.cell.line.venue
    market = next(one for one in LINES if one.symbol == ladder.MARKETS[venue])
    try:
        held = bars(market)
    except keeper.Stale:  #: named by `basket.grade` as a market holding no bars, never dropped
        held = ()
    return basket.Against(market, held, pounds)


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
    """`run` on the pool, the bars made in each worker by `make`, after the same pre-flight as
    `ladder.run` (L20): a set whose bars have a gap refuses to start; a missing pound day is its
    cell's named reason, never a refused set."""

    def go(
        home: Path,
        _: object,
        pounds: Rates,
        todo: Sequence[Cell],
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        plan: Plan = ladder.FIRST,
    ) -> str:
        ladder.preflight(todo, make(), pounds)
        return ladder_pool.run(home, make, pounds, todo, now, plan)

    return go


def entered(home: Path) -> str:
    """Set VAR's family entered before any of it runs: each variant a trial, run or not."""
    made = variants.family(rulebook.specs())
    register = ladder.begun(home, (), VAR)[0].with_suffix(".trials.jsonl")
    count = trials.enter(register, VAR.question, [variant.spec.name for variant in made])
    return f"SET VAR: {len(made)} variants entered, {count} trials counted; none judged yet (GC)"


def transferred(home: Path) -> str:
    """Set 2, the grid's transfer study (`lab/transfer.py`, PRE-REVIEW, never a verdict), read from
    the results file the study wrote and closed with its `SET` line: its rules, how many scored
    PASS on some line, and that none goes forward. No study written: refused, naming the file."""
    path = home / transfer.FOLDER / f"{transfer.NAME}.json"
    if not path.exists():
        sys.exit(f"ladder: no transfer study at {path}; `python -m lab.transfer` writes it first")
    data = json.loads(path.read_text("utf-8"))  # bounded: one study, rewritten whole each run
    rows, label = data["rows"], data["label"]
    rules = dict.fromkeys(row["rule"] for row in rows)
    passed = {row["rule"] for row in rows if row["answer"] == Answer.PASS.name}
    fits = f"{data['fits']} fitted, {data['bare']} bare"
    counts = f"{data['lines']} lines, {len(rows)} scores, {fits}"
    return (
        f"set TRANSFER ({label}): {counts}{NL}SET TRANSFER: {len(rules)} rules, {len(passed)} "
        f"scored PASS on a line, none goes forward ({label}, never a verdict), "
        f"table {path.with_suffix('.md')}"
    )


def leveraged(lines: Sequence[Line]) -> tuple[Line, ...]:
    """The lines that make more than their market's daily move."""
    return tuple(line for line in lines if line.leverage > 1)


def told(home: Path, said: str, now: datetime, door: Callable[[], messenger.Post]) -> str:
    """A finished set's summary sent once a day for each `SET` line it ends with (a set judged
    again to another answer is told again), through `messenger.send`, its record in the ladder's
    folder; a set with no `SET` line (stopped, or cells left unjudged) is not told. Its line says
    the message's number, or why his phone was not told."""
    ended = [one for one in said.split(NL) if one.startswith("SET ")]
    if not ended:
        return "telegram: not told, the set ended with no SET line"
    try:
        sent = messenger.send(home / FOLDER, now, f"ladder {now.date()} {ended[-1]}", said, door())
    except (ValueError, messenger.Undelivered) as why:
        return f"telegram: NOT TOLD, {why}"
    return f"telegram: told, message {sent.number}"


def main(
    env: Mapping[str, str],
    argv: Sequence[str] = (),
    door: Callable[[Mapping[str, str]], messenger.Post] = messenger.telegram,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> int:
    """Set EPON on every line the research store holds; `first` runs the first set instead and
    `leveraged` set LEV, the trend rules on the leveraged lines; `intraday` set INTRADAY
    (five-minute rules), `scalping` set SCALP (one-minute rules); `variants` only enters set
    VAR's trials; `transfer` publishes set 2, the grid's study. The sets run on the pool
    (R-RUNNER-110): every core but two. A finished set is told to his phone by `told`; 1 when
    it could not be. A set whose inputs have gaps exits `WAITS`, told on stderr, nothing written."""
    if not env.get("KESTREL2_DATA"):
        sys.exit("ladder: KESTREL2_DATA names no data folder, so the set has no home")
    home = Path(env["KESTREL2_DATA"])
    sets: tuple[list[str], ...] = (
        [],
        ["first"],
        ["leveraged"],
        ["intraday"],
        ["scalping"],
        ["variants"],
        ["transfer"],
    )
    if list(argv) not in sets:
        sys.exit(
            f"ladder: {list(argv)} is no set; the command takes nothing, `first`, `leveraged`, "
            "`intraday`, `scalping`, `variants` or `transfer`"
        )
    if argv == ["variants"]:  #: names a family; reads no bars
        sys.stdout.write(entered(home) + NL)
        return 0
    try:
        said = transferred(home) if argv == ["transfer"] else _judged(home, argv)
    except folds.Gaps as gaps:  #: no table, no phone: the set waits for the store's next fill
        sys.stderr.write(f"ladder: the set waits for the store's next fill: {gaps}{NL}")
        raise SystemExit(WAITS) from None
    sys.stdout.write(said + NL)
    phone = told(home, said, now(), partial(door, env))
    sys.stdout.write(phone + NL)
    return int("NOT TOLD" in phone)


def _judged(home: Path, argv: Sequence[str]) -> str:
    """A set judged on the store's bars, named by `argv`, and what it said."""
    make = partial(history_bars.reader, home)
    pounds, held = history_bars.pounds(home), history_bars.lines(home)
    if argv == ["intraday"]:
        said = intraday.judge_set(home, pounds)
    elif argv == ["scalping"]:
        said = scalping.judge_set(home, pounds)
    elif argv == ["leveraged"]:
        held = leveraged(held)
        said = epon(home, make(), pounds, held, rules=TREND, go=_pooled(make), plan=LEV)
    elif argv:
        said = first(home, make, pounds)
    else:
        said = epon(home, make(), pounds, held, go=_pooled(make))
        said += NL + weather_line(home, make(), held)
    return said
