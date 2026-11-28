"""chain - A PUBLISHED SET MAKES ITS VARIANTS: each rule of a set's table that has a catalogue
row is tried at settings fixed here, before any result, and written once (canon B6).

`ranges` puts each parameter of a row at its published value and one step either side (x2/3
and x3/2, whole numbers rounded half up), held inside its block's range; a parameter left with
under three values is not ranged. `cells` makes every variant (`lab.variants`) of each such
rule on each line the rule's rows name, over the row's own window. `sweep` runs them by the
ladder's engine under the set's own plan, so they sit in its register beside its rows and the
count every row is judged against includes them all. `report` asks, for each rule and line, the
centre of the plateau of its variants' first rungs (`lab.plateau`, never the best score) and
writes `<tag>-chain.md` and `.json` beside the set's table, PRE-REVIEW, with the trial count;
a line with no plateau is named so, never dropped.
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from functools import partial
from pathlib import Path
from typing import Any

from desk.lines import LINES
from lab import (
    basket,
    history_bars,
    ladder,
    ladder_pool,
    ladder_sets,
    plateau,
    rulebook,
    variants,
    verdict,
)
from lab.batch import Bars
from lab.blocks import BLOCKS
from lab.cell import Cell
from lab.rung import Rates, Verdict
from lab.spec import PLACES, Ranges, Spec

_CENT = Decimal("0.0001")


def _step(value: int | Decimal, num: int, den: int) -> int | Decimal:
    """The value times num/den: whole numbers rounded half up, decimals to four places."""
    scaled = Decimal(value) * num / den
    if isinstance(value, int):
        return int(scaled.quantize(1, rounding=ROUND_HALF_UP))
    return scaled.quantize(_CENT, rounding=ROUND_HALF_UP)


def ranges(spec: Spec) -> Ranges:
    """The row's settings at their published value and a step either side, lowest first."""
    made: dict[tuple[str, str], tuple[int | Decimal, ...]] = {}
    for place in PLACES:
        for param, value in spec.params[place].items():
            held = BLOCKS[getattr(spec, place)].params[param]
            around = (_step(value, 2, 3), value, _step(value, 3, 2))
            kept = sorted({min(max(v, held.low), held.high) for v in around})
            if len(kept) >= 3:
                made[(place, param)] = tuple(kept)
    return made


def cells(table: Mapping[str, Any]) -> tuple[Cell, ...]:
    """Every variant of each catalogued rule of the set's table on each of its lines."""
    book = rulebook.specs()
    lines = {(line.symbol, line.venue): line for line in LINES}
    made = []
    for rule in table["rules"]:
        spec = book.get(rule["rule"])
        if spec is None or not (tried := ranges(spec)):
            continue
        found = variants.variants(replace(spec, ranges=tried))
        for row in rule["cells"]:
            _, symbol, venue, start, end = row["cell"]
            if (symbol, venue) == basket.NAME:
                continue  # the pooled line is no line to run a variant on
            line = lines[symbol, venue]
            window = date.fromisoformat(start), date.fromisoformat(end)
            made += [Cell(v.spec.name, line, *window) for v in found]
    return tuple(made)


def sweep(
    home: Path,
    bars: Bars,
    pounds: Rates,
    tag: str,
    go: Callable[..., str] = ladder_pool.run,
) -> str:
    """The set `tag`'s variants run under its own plan, kept beside its rows: the engine's line."""
    plan = next(p for p in (ladder_sets.EPON, ladder_sets.LEV) if p.tag == tag)
    path = home / ladder.FOLDER / "sets" / f"{tag}.json"
    table = json.loads(path.read_text("utf-8"))  # bounded: one set table, written whole
    return go(home, bars, pounds, cells(table), plan=plan)


def centre(spec: Spec, firsts: Mapping[str, Verdict]) -> plateau.Chosen:
    """The centre of the plateau of the row's variants' first rungs, by variant name: the
    deepest setting, never the best score; its `passed` says whether a plateau stands."""
    ranged = replace(spec, ranges=ranges(spec))
    tried = {v.setting: firsts[v.spec.name] for v in variants.variants(ranged)}
    return plateau.choose(tuple(ranged.ranges.values()), tried)


def _line(
    spec: Spec, line: Any, window: tuple[date, date], bars: Bars, pounds: Rates
) -> dict[str, Any]:
    """One rule on one line: the centre of its plateau, or why there is none."""
    own = bars(line)
    ranged = replace(spec, ranges=ranges(spec))
    firsts = {}
    try:
        for v in variants.variants(ranged):
            firsts[v.spec.name] = verdict.ready(Cell(v.spec.name, line, *window), own, pounds, ())
    except (ValueError, OSError) as why:  # a line that waits on data or units is named, not hidden
        return {"line": [line.symbol, line.venue], "plateau": False, "why": f"unjudged: {why}"}
    chosen = centre(spec, firsts)
    names = {v.setting: v.spec.name for v in variants.variants(ranged)}
    found = {"line": [line.symbol, line.venue], "plateau": chosen.passed, "depth": chosen.depth}
    found["centre"] = names[chosen.setting]
    found["why"] = "" if chosen.passed else f"no plateau: deepest setting {chosen.depth} deep"
    return found


def report(home: Path, bars: Bars, pounds: Rates, tag: str) -> Path:
    """`<tag>-chain.md` and `.json` beside the set's table: for each rule and line the centre
    of its variants' plateau, PRE-REVIEW, with the set's trial count."""
    folder = home / ladder.FOLDER / "sets"
    table = json.loads((folder / f"{tag}.json").read_text("utf-8"))  # bounded: one set table
    book = rulebook.specs()
    lines = {(line.symbol, line.venue): line for line in LINES}
    rows = []
    for rule in table["rules"]:
        spec = book.get(rule["rule"])
        if spec is None or not ranges(spec):
            continue
        for row in rule["cells"]:
            _, symbol, venue, start, end = row["cell"]
            if (symbol, venue) == basket.NAME:
                continue
            window = date.fromisoformat(start), date.fromisoformat(end)
            rows.append(
                {"rule": spec.name} | _line(spec, lines[symbol, venue], window, bars, pounds)
            )
    data = {"set": tag, "status": "PRE-REVIEW", "trials": table["trials"], "rows": rows}
    out = [f"# SET {tag} chain - PRE-REVIEW", "", f"Judged against {table['trials']} trials.", ""]
    out += ["| rule | line | centre | depth | note |", "|---|---|---|---|---|"]
    for r in rows:
        cols = [r["rule"], "{} ({})".format(*r["line"]), r.get("centre", "-")]
        out.append("| " + " | ".join([*cols, str(r.get("depth", "-")), r["why"]]) + " |")
    (folder / f"{tag}-chain.json").write_text(json.dumps(data, indent=1), "utf-8")
    path = folder / f"{tag}-chain.md"
    path.write_text(chr(10).join(out) + chr(10), "utf-8")
    return path


def _pooled(
    make: Callable[[], Bars], home: Path, _: object, pounds: Rates, todo: Any, **kw: Any
) -> str:
    """The variants on the pool, the bars made in each worker by `make`."""
    return ladder_pool.run(home, make, pounds, todo, **kw)


def stale(folder: Path, tag: str) -> bool:
    """Whether the set's table is there and its chain is missing or older than the table."""
    table, made = folder / f"{tag}.json", folder / f"{tag}-chain.json"
    return table.exists() and (not made.exists() or made.stat().st_mtime < table.stat().st_mtime)


def _said(folder: Path, tag: str) -> str:
    """The set's line: its variants, the trials it was judged against, the plateaus found."""
    data = json.loads((folder / f"{tag}-chain.json").read_text("utf-8"))  # bounded: one set
    table = json.loads((folder / f"{tag}.json").read_text("utf-8"))  # bounded: one set
    found = sum(bool(r["plateau"]) for r in data["rows"])
    return f"{tag}: {len(cells(table))} variants, {data['trials']} trials, {found} centres"


def main(env: Mapping[str, str]) -> int:
    """The command: each set's table with no chain, or a chain older than it, is chained, one
    line each (variants, trials, centres found); 1 only when a set could not be chained."""
    if not env.get("KESTREL2_DATA"):
        sys.exit("chain: KESTREL2_DATA names no data folder, so the sets have no home")
    home = Path(env["KESTREL2_DATA"])
    folder, failed = home / ladder.FOLDER / "sets", False
    make = partial(history_bars.reader, home)
    for tag in (str(ladder_sets.EPON.tag), str(ladder_sets.LEV.tag)):
        if not stale(folder, tag):
            continue
        try:
            pounds, own = history_bars.pounds(home), make()
            sweep(home, own, pounds, tag, go=partial(_pooled, make))
            report(home, own, pounds, tag)
        except (ValueError, OSError, KeyError) as why:  # said on its line, and the exit is 1
            sys.stdout.write(f"{tag}: not chained: {why}" + chr(10))
            failed = True
            continue
        sys.stdout.write(_said(folder, tag) + chr(10))
    return int(failed)


if __name__ == "__main__":
    sys.exit(main(os.environ))
