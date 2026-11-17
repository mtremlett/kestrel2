"""verdict_parts - THE LADDER'S TABLE: a cell's line, whether it goes forward, and the set's
results file and table (`lab/verdict.py` gives these to its callers)."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from lab.rung import Answer

STATUS = "PRE-REVIEW"  #: what every table is until the blind review (R-RUNNER-40) is clean
COLUMNS = ("rule", "line", "venue", "answer", "rungs", "trials", "reproduction", "goes forward")
Row = Mapping[str, Any]  #: a cell's line in the results file


def goes(row: Row) -> bool:
    """A cell goes forward when its one verdict is PASS, every rung run passed and its row says
    that no rung is unrun: passing the rungs that happen to be built is not passing the ladder."""
    passed = row.get("answer") == Answer.PASS.name and bool(row.get("every"))
    return passed and row.get("unrun") == {}


def by_rule(rows: Sequence[Row], rules: Sequence[str]) -> dict[str, list[Row]]:
    """The rows of each rule, in the order the rules are given."""
    return {rule: [row for row in rows if row["cell"][0] == rule] for rule in rules}


def _rule(rule: str, rows: Sequence[Row]) -> Row:
    return {"rule": rule, "passed": any(map(goes, rows)), "cells": rows}


def cell_line(row: Row) -> list[str]:
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
        "yes" if goes(row) else "no",
    ]


def write_table(
    folder: Path,
    tag: int | str,
    question: str,
    rows: Sequence[Row],
    rules: Sequence[str],
    count: int,
    built: tuple[int, int],
) -> Path:
    """The set's results table, `<tag>.md` and `<tag>.json`, labelled PRE-REVIEW, its header
    saying how many of the ladder's rungs are built: `built` is (built, of)."""
    folder.mkdir(parents=True, exist_ok=True)
    mine = by_rule(rows, rules)
    data: dict[str, object] = {"set": tag, "question": question, "status": STATUS}
    data |= {"cells": len(rows), "trials": count, "refused": sum("refused" in r for r in rows)}
    data |= {"rungs_built": built[0], "rungs": built[1]}
    data |= {"rules": [_rule(r, rs) for r, rs in mine.items()]}
    (folder / f"{tag}.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
    #: the register is never shortened: a trial an earlier run of the set entered stays counted
    said = f"Cells: {len(rows)}. Each is judged against {count} trials, all its register ever held."
    out = [f"# SET {tag} - {STATUS}", "", f"rungs built: {built[0]} of {built[1]}", ""]
    out += [f"{question} {said}", ""]
    out += [f"{STATUS}: not final until the blind review (R-RUNNER-40) is clean.", ""]
    for rule, rs in mine.items():
        out += [f"## {rule}: {sum(map(goes, rs))} of {len(rs)} lines go forward", ""]
        out += ["| " + " | ".join(COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]
        for row in rs:
            cells = [rule, row["cell"][1], row["cell"][2], *cell_line(row)]
            out.append(
                "| " + " | ".join(c.replace("|", "/").replace("\n", " ") for c in cells) + " |"
            )
        out.append("")
    (path := folder / f"{tag}.md").write_text("\n".join(out), encoding="utf-8")
    return path
