"""chain - A PUBLISHED SET MAKES ITS VARIANTS: each rule of a set's table that has a catalogue
row is tried at settings fixed here, before any result, and written once (canon B6).

`ranges` puts each parameter of a row at its published value and one step either side (x2/3
and x3/2, whole numbers rounded half up), held inside its block's range; a parameter left with
under three values is not ranged. `cells` makes every variant (`lab.variants`) of each such
rule on each line the rule's rows name, over the row's own window. `sweep` runs them by the
ladder's engine under the set's own plan, so they sit in its register beside its rows and the
count every row is judged against includes them all.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from desk.lines import LINES
from lab import basket, ladder, ladder_pool, ladder_sets, rulebook, variants
from lab.batch import Bars
from lab.blocks import BLOCKS
from lab.cell import Cell
from lab.rung import Rates
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
