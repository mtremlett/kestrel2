"""transfer - THE GRID'S TRANSFER STUDY: does a rule's best setting on one line earn on the
others? `python -m lab.transfer [STORE]` is the whole of it: every line the research store
holds (`sweep.held`), every rule the desk's engine can make, every setting of it, each judged
by the first rung (`lab/rung.py`) after the desk's costs, and the answer written to
`ladder/sets/grid-transfer.md` and `.json` in the data folder, labelled PRE-REVIEW, ending
with one line of counts. It can be stopped at any moment and run again: a cell is kept in its
line's journal (`lab/batch.py`) under its code and its bars, and is not run twice.

NOTHING IS PICKED BY EYE. A rule's settings are its grid (`Space`), declared in this module.
The five published rules have no parameters in the desk's engine yet (R-GRID-1), so each has
one setting, the published one, judged on every line. A rule with a grid is fitted on each
line in turn by `lab/plateau.py`: the setting promoted is the centre of a plateau of passing
neighbours, never the best score, and a line whose surface holds no plateau promotes nothing
and its best is shown, not transferred. Only a promoted setting is scored on the other lines,
which fitted nothing: that is the transfer. A cell that cannot be judged is named with its
reason and left off the surface, as the plateau's rule asks.
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from itertools import product
from pathlib import Path
from typing import Any

from desk.command import CAPITAL
from desk.lines import Line
from desk.orders import Settings
from desk.strategy import STRATEGIES
from lab import batch, ladder, plateau, reproduce, rung, sweep, universe
from lab.cell import Cell
from lab.plateau import Grid, Setting
from lab.rung import Answer, Rates, Verdict

LABEL = "PRE-REVIEW"
FOLDER, STEM = Path("ladder") / "sets", "grid-transfer"
#: What may leave a cell unjudged; anything else is a bug and stops the study.
FAILED = (ValueError, OSError)
#: Judges the named strategies on a line: each one's first-rung verdict, or why it has none.
Judge = Callable[[Line, Sequence[str]], Mapping[str, Verdict | str]]


@dataclass(frozen=True)
class Space:
    """One rule's settings: a grid of parameters, and the name the engine knows each by."""

    grid: Grid
    name: Callable[[Setting], str]

    def settings(self) -> tuple[Setting, ...]:
        """Every setting of the grid; the one empty setting where it has no parameters."""
        return tuple(product(*self.grid))


#: The desk's engine has no parameters yet: each rule is its one published setting.
SPACES: Mapping[str, Space] = {rule: Space((), lambda _s, rule=rule: rule) for rule in STRATEGIES}  # type: ignore[misc]


@dataclass(frozen=True)
class Fit:
    """A rule's setting chosen on one line by its plateau."""

    rule: str
    line: Line  #: the line it was fitted on
    setting: Setting
    depth: int
    promoted: bool  #: the centre of a plateau; else shown and never transferred


@dataclass(frozen=True)
class Study:
    """Every score, every fit and every cell without a verdict."""

    lines: tuple[Line, ...]
    scores: Mapping[tuple[str, Setting, Line], tuple[Answer, Decimal | None]]
    fits: tuple[Fit, ...]
    failed: Mapping[str, str]  #: "rule setting on SYMBOL VENUE" to why it has no verdict


def study(lines: Sequence[Line], spaces: Mapping[str, Space], judge: Judge) -> Study:
    """Every setting of every rule judged on every line; each rule with a grid fitted on each
    line by its plateau."""
    scores: dict[tuple[str, Setting, Line], tuple[Answer, Decimal | None]] = {}
    fits: list[Fit] = []
    failed: dict[str, str] = {}
    for line in lines:
        names = {
            (rule, s): space.name(s) for rule, space in spaces.items() for s in space.settings()
        }
        got = judge(line, list(dict.fromkeys(names.values())))
        for (rule, setting), name in names.items():
            one = got[name]
            if isinstance(one, str):
                failed[f"{name} on {line.symbol} {line.venue}"] = one
            else:
                scores[rule, setting, line] = (one.answer, one.t)
        for rule, space in spaces.items():
            surface = {
                s: v for s in space.settings() if isinstance(v := got[space.name(s)], Verdict)
            }
            if space.grid and surface:
                best = plateau.choose(space.grid, surface)
                fits.append(Fit(rule, line, best.setting, best.depth, best.passed))
    return Study(tuple(lines), scores, tuple(fits), failed)


def transfers(done: Study, fit: Fit) -> dict[Line, tuple[Answer, Decimal | None]]:
    """A promoted fit's setting as scored on each other line; nothing for one not promoted."""
    if not fit.promoted:
        return {}
    return {
        line: done.scores[fit.rule, fit.setting, line]
        for line in done.lines
        if line != fit.line and (fit.rule, fit.setting, line) in done.scores
    }


def report(done: Study) -> dict[str, Any]:
    """The study as the JSON file holds it: counts, then each rule's judgments and fits."""
    rules: dict[str, Any] = {}
    for rule in sorted({key[0] for key in done.scores} | {fit.rule for fit in done.fits}):
        mine = Counter(a.name for (r, _s, _l), (a, _t) in done.scores.items() if r == rule)
        fitted = []
        for fit in (f for f in done.fits if f.rule == rule):
            back = transfers(done, fit)
            held = sum(a is Answer.PASS for a, _t in back.values())
            where = f"{fit.line.symbol} {fit.line.venue}"
            fitted.append(
                {"line": where, "setting": [str(v) for v in fit.setting], "depth": fit.depth}
                | {"promoted": fit.promoted, "scored": len(back), "passed": held}
            )
        rules[rule] = {"judged": dict(mine), "fits": fitted}
    counts = {
        "lines": len(done.lines),
        "rules": len(rules),
        "judged": len(done.scores),
        "failed": len(done.failed),
        "fitted": len(done.fits),
        "promoted": sum(fit.promoted for fit in done.fits),
        "scored": sum(len(transfers(done, fit)) for fit in done.fits),
        "passed": sum(
            a is Answer.PASS for fit in done.fits for a, _t in transfers(done, fit).values()
        ),
    }
    return {"label": LABEL, "counts": counts, "rules": rules, "failed": dict(done.failed)}


def sentence(counts: Mapping[str, int]) -> str:
    """The one line of counts the command ends with."""
    return (
        f"grid transfer ({LABEL}): {counts['lines']} lines, {counts['rules']} rules, "
        f"{counts['judged']} cells judged, {counts['failed']} without a verdict; "
        f"{counts['promoted']} of {counts['fitted']} fits promoted from a plateau, scored on "
        f"{counts['scored']} other lines, {counts['passed']} passed there"
    )


def markdown(done: Mapping[str, Any]) -> str:
    """The same report for the operator: the label first, then a rule at a time."""
    out = [f"# Grid transfer study - {done['label']}", "", sentence(done["counts"]), ""]
    for rule, body in done["rules"].items():
        judged = ", ".join(f"{name} {n}" for name, n in sorted(body["judged"].items()))
        out += [f"## {rule}", "", f"Judged on the lines: {judged or 'none'}.", ""]
        for fit in body["fits"]:
            kind = "promoted" if fit["promoted"] else "no plateau, not transferred"
            out.append(
                f"- fitted on {fit['line']}: setting {', '.join(fit['setting'])} "
                f"(depth {fit['depth']}, {kind}); passed on {fit['passed']} of "
                f"{fit['scored']} other lines"
            )
        out.append("")
    out += [f"Without a verdict: {len(done['failed'])}.", ""]
    return "\n".join(out)


def judging(root: Path, home: Path, rates: Rates) -> Judge:
    """The real judge: the line's bars from the store at root, each strategy's cell kept in
    the line's journal under home, and the trades priced by the first rung at these rates."""
    owed: dict[str, tuple[reproduce.Reproduction, ...]] = {}

    def judge(line: Line, names: Sequence[str]) -> Mapping[str, Verdict | str]:
        try:
            bars = universe.read(root, line).bars
        except FAILED as error:
            return {name: f"{type(error).__name__}: {error}" for name in names}
        start = max([ladder.START, *(bar.day for bar in bars[:1])])
        journal = home / line.venue / f"{line.symbol}.jsonl"
        journal.parent.mkdir(parents=True, exist_ok=True)
        done = batch.run(
            [Cell(n, line, start, ladder.END) for n in names], lambda _l: bars, journal
        )
        out: dict[str, Verdict | str] = {}
        for name, outcome in zip(names, done, strict=True):
            try:
                if isinstance(outcome, batch.Failed):
                    out[name] = outcome.error
                    continue
                if name not in owed:
                    figures = [f for f in reproduce.FIGURES if f.strategy == name]
                    owed[name] = tuple(
                        reproduce.reproduce(f, universe.read(root, f.line).bars) for f in figures
                    )
                out[name] = rung.judge(outcome, bars, Settings(CAPITAL), rates, owed[name])
            except FAILED as error:
                out[name] = f"{type(error).__name__}: {error}"
        return out

    return judge


def main(argv: Sequence[str], env: Mapping[str, str], rates: Callable[[], Rates]) -> int:
    """The study over the store, written to the data folder; its one line of counts to stdout."""
    if not env.get("KESTREL2_DATA"):
        sys.exit("transfer: KESTREL2_DATA names no data folder, so the study has no home")
    data = Path(env["KESTREL2_DATA"])
    root = Path(argv[0]) if argv else data / "grid" / "store"
    out = data / FOLDER
    out.mkdir(parents=True, exist_ok=True)
    judge = judging(root, out / STEM, rates())
    done = report(study(sweep.held(root), SPACES, judge))
    (out / f"{STEM}.json").write_text(json.dumps(done, indent=1), encoding="utf-8")
    (out / f"{STEM}.md").write_text(markdown(done), encoding="utf-8")
    sys.stdout.write(sentence(done["counts"]) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], os.environ, ladder.rates))
