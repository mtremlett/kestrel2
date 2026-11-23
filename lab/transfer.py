"""transfer - THE GRID'S TRANSFER STUDY: does a rule's best setting on one line earn on the
others? (R-RUNNER-82; the study is a PRE-REVIEW, never a verdict.)

For each rule and each line the store holds, the rule's settings are tried on that line and the
one fitted is the centre of a plateau (`lab/plateau.py`), never the best score, never a lone
peak: a line whose settings show no plateau fits nothing and sends nothing on. The fitted
setting is then scored, by the first rung and the desk's costs, on every OTHER line, so a
setting is judged where it was not chosen. A rule with no other setting than its published one
(the five today, until R-GRID-1 gives more) has no grid to fit: it is scored as published, on
every line, and is named so.

The cells are run by the batch service into the sweep's own journals, so a stopped study
resumes at the first cell not kept. Nothing is chosen by eye and nothing is promoted: the
study writes `ladder/sets/grid-transfer.md` and `.json` in the data folder and ends with one
line of counts. `python -m lab.transfer STORE KEPT DATA`.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from itertools import product
from pathlib import Path
from typing import Any

from desk.bars import LIVE
from desk.command import CAPITAL
from desk.lines import Line
from desk.orders import Settings
from desk.strategy import STRATEGIES
from lab import batch, history_bars, ladder, plateau, rung, sweep
from lab.batch import Failed
from lab.cell import Cell
from lab.plateau import Grid, Setting
from lab.rung import Rates, Verdict

LABEL = "PRE-REVIEW"
FOLDER, NAME = Path("ladder") / "sets", "grid-transfer"
#: A strategy on a line, judged by the first rung; None where it could not be judged.
Score = Callable[[str, Line], Verdict | None]


@dataclass(frozen=True)
class Family:
    """A rule and the settings tried: its grid (empty: the published setting alone), and the
    name of the strategy the desk's engine makes at a setting."""

    rule: str
    grid: Grid
    named: Callable[[Setting], str]


@dataclass(frozen=True)
class Row:
    """One setting of one rule scored on one line."""

    rule: str
    fitted: str | None  #: the line the setting was fitted on; None where it is as published
    setting: Setting
    line: str
    t: Decimal | None
    answer: str | None  #: None where the cell could not be judged; REFUSED where sizing declined
    refusal: str | None = None  #: the words of the desk's refusal, for a REFUSED answer


@dataclass(frozen=True)
class Study:
    """Every score the study made, and how many lines fitted and how many did not."""

    rows: tuple[Row, ...]
    fits: int  #: lines with a plateau, whose centre went on to the others
    bare: int  #: lines whose settings showed no plateau: nothing fitted, nothing sent on


def families() -> tuple[Family, ...]:
    """Every rule the desk's engine can make, at the settings it has: the published one."""

    def published(name: str) -> Callable[[Setting], str]:
        return lambda _setting: name

    return tuple(Family(name, (), published(name)) for name in STRATEGIES)


def _row(family: Family, fitted: Line | None, setting: Setting, line: Line, score: Score) -> Row:
    found = score(family.named(setting), line)
    on = f"{line.symbol} on {line.venue}"
    at = None if fitted is None else f"{fitted.symbol} on {fitted.venue}"
    if found is None:
        return Row(family.rule, at, setting, on, None, None)
    answer = "REFUSED" if found.refused else found.answer.name
    return Row(family.rule, at, setting, on, found.t, answer, found.refusal)


def study(kinds: Sequence[Family], lines: Sequence[Line], score: Score) -> Study:
    """Each rule's settings fitted on each line and scored on all the others; a rule with no
    grid scored as published on every line."""
    rows: list[Row] = []
    fits = bare = 0
    for family in kinds:
        if not family.grid:
            rows += [_row(family, None, (), line, score) for line in lines]
            continue
        for line in lines:
            tried = {s: score(family.named(s), line) for s in product(*family.grid)}
            surface = {s: v for s, v in tried.items() if v is not None}
            chosen = plateau.choose(family.grid, surface) if surface else None
            if chosen is None or not chosen.passed:
                bare += 1
                continue
            fits += 1
            rows += [_row(family, line, chosen.setting, o, score) for o in lines if o != line]
    return Study(tuple(rows), fits, bare)


def scorer(path: Path, kept: Path, rates: Rates) -> Score:
    """The first rung's verdict on a strategy and a line, its bars from the history database
    at path, its cell kept in the sweep's journal of that line under kept, over the ladder's
    one window."""
    settings = Settings(CAPITAL)

    bars = sweep.reader(path)

    def score(name: str, line: Line) -> Verdict | None:
        try:
            todo = Cell(name, line, ladder.START, ladder.END)
            sweep.journal(kept, line).parent.mkdir(parents=True, exist_ok=True)
            (outcome,) = batch.run([todo], bars, sweep.journal(kept, line))
            if isinstance(outcome, Failed):
                return None
            return rung.judge(outcome, bars(line), settings, rates)
        except ladder.FAILED:
            return None  # a line whose bars or rates cannot judge it is counted, not guessed

    return score


def counts(done: Study, lines: int) -> str:
    """The study's one line of counts."""
    said = Counter(row.answer or "NONE" for row in done.rows)
    answers = ", ".join(f"{name} {n}" for name, n in sorted(said.items()))
    return (
        f"grid transfer study {LABEL}: {lines} lines, {len(done.rows)} scores ({answers}); "
        f"{done.fits} fits sent to other lines, {done.bare} lines with no plateau"
    )


def report(done: Study, lines: int) -> tuple[str, dict[str, Any]]:
    """The study as a page and as data, both labelled."""
    table = ["| rule | fitted on | setting | scored on | t | answer |", "|---|---|---|---|---|---|"]
    for r in done.rows:
        answer = f"REFUSED: {r.refusal}" if r.refusal else r.answer
        cells = (r.rule, r.fitted or "as published", r.setting, r.line, r.t, answer)
        table.append("| " + " | ".join(str(c) for c in cells) + " |")
    head = [f"# Grid transfer study ({LABEL})", "", counts(done, lines), ""]
    rows = [
        {**vars(r), "setting": [str(v) for v in r.setting], "t": None if r.t is None else str(r.t)}
        for r in done.rows
    ]
    data = {"label": LABEL, "lines": lines, "fits": done.fits, "bare": done.bare, "rows": rows}
    return "\n".join([*head, *table, ""]), data


def main(argv: Sequence[str]) -> None:
    """The study over every line the store holds, written under DATA, its counts printed."""
    root, kept, data = (Path(folder).resolve() for folder in argv[:3])
    lines = sweep.held(root)
    with sweep.alone(kept):
        done = study(families(), lines, scorer(data / LIVE, kept, history_bars.pounds(data)))
    page, rows = report(done, len(lines))
    (data / FOLDER).mkdir(parents=True, exist_ok=True)
    for suffix, text in ((".md", page), (".json", json.dumps(rows, indent=1))):
        made = data / FOLDER / (NAME + suffix + ".new")
        made.write_text(text, encoding="utf-8")
        made.replace(made.with_suffix(""))
    sys.stdout.write(counts(done, len(lines)) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
