"""spec - a strategy as data: a row naming its blocks (`lab.blocks`), their parameters, its
source and at least one known answer, built only by `Spec.parse`, which refuses a row that is
wrong in any way and says which part and why. `SpecRule` runs a spec as the desk's own Rule, so
the one engine decides on it as it decides on a Python rule.

A row: name, entry, exit, stop, filter (block names), params (per place), source and cases
(known answers: bars as [high, low, close], the wish after each), and may carry ranges (per
place, a setting's values to try, lowest first, each held to its block; `lab.variants` makes
them). A spec with no case is refused. Out of the market it buys when its entry fires and its
filter allows; in it, it sells when its exit or its stop fires.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, localcontext
from types import MappingProxyType
from typing import Any, ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import ARITHMETIC, RANGES, Declared, Timeframe
from lab.block_base import Block, Kind, Param
from lab.blocks import BLOCKS

PLACES = tuple(kind.value for kind in Kind)
#: One setting of a row, as (place, parameter), and the values to try, lowest first.
Ranges = Mapping[tuple[str, str], tuple[int | Decimal, ...]]
_DAY = date(2020, 1, 1)


@dataclass(frozen=True)
class Case:
    """A known answer: bars as (high, low, close), and whether the rule wants to be in the
    market after each, holding what it last wanted."""

    bars: tuple[tuple[Decimal, Decimal, Decimal], ...]
    wants: tuple[bool, ...]


def _number(where: str, param: Param, value: Any) -> int | Decimal:
    """One parameter, of its kind and inside its range, or refused."""
    kind = param.kind
    if isinstance(value, bool) or type(value) not in (int, str, Decimal):
        raise ValueError(f"{where} is {value!r}, not a {kind.__name__}")
    if kind is int and type(value) is not int:
        raise ValueError(f"{where} is {value!r}, not a whole number")
    try:
        made = kind(value)
    except InvalidOperation:
        raise ValueError(f"{where} is {value!r}, not a number") from None
    if not param.low <= made <= param.high:
        raise ValueError(f"{where} is {made}, outside {param.low} to {param.high}")
    return made


def _place(row: Mapping[str, Any], place: str) -> tuple[str, Mapping[str, int | Decimal]]:
    """The block a place names, and its parameters checked against what the block takes."""
    name = row[place]
    spot = BLOCKS.get(name) if isinstance(name, str) else None
    if spot is None:
        raise ValueError(f"{place}: unknown block {name!r}; known: {sorted(BLOCKS)}")
    if spot.kind.value != place:
        raise ValueError(f"{place}: block {name!r} is a {spot.kind.value}, not a {place}")
    given = row["params"].get(place, {})
    if not isinstance(given, Mapping) or set(given) != set(spot.params):
        raise ValueError(f"{place} {name}: takes parameters {sorted(spot.params)}, got {given!r}")
    return name, MappingProxyType(
        {k: _number(f"{place} {name} {k}", p, given[k]) for k, p in spot.params.items()}
    )


def _case(n: int, raw: Any) -> Case:
    if not isinstance(raw, Mapping) or set(raw) != {"bars", "wants"}:
        raise ValueError(f"case {n}: needs exactly bars and wants, got {raw!r}")
    if len(raw["bars"]) != len(raw["wants"]) or any(len(bar) != 3 for bar in raw["bars"]):
        raise ValueError(f"case {n}: bars are [high, low, close], one wish for each")
    bars = tuple(tuple(Decimal(str(x)) for x in bar) for bar in raw["bars"])
    return Case(bars, tuple(bool(w) for w in raw["wants"]))  # type: ignore[arg-type]


def _ranges(row: Mapping[str, Any], params: Mapping[str, Mapping[str, Any]]) -> Ranges:
    """A row's ranges as ((place, setting), values), each value held to its block; a range
    off the row, of no values, or not rising (lowest first) is refused. Places joined by "+"
    ("entry+exit") range one setting they share, moved together; their own values must agree."""
    made: dict[tuple[str, str], tuple[int | Decimal, ...]] = {}
    seen: set[tuple[str, str]] = set()  # each place's setting ranged once
    given = row.get("ranges", {})
    places = given.items() if isinstance(given, Mapping) else [("ranges", given)]
    for place, settings in places:
        spots = str(place).split("+")
        alone = set(spots) <= set(PLACES) and len(set(spots)) == len(spots)
        if not alone or not isinstance(settings, Mapping) or not settings:
            raise ValueError(f"spec {row['name']} ranges: {place!r} is no place with settings")
        for param, values in settings.items():
            where = f"spec {row['name']} {place} {param}"
            if any(param not in params[s] for s in spots) or not isinstance(values, list):
                raise ValueError(f"{where}: {values!r} is no list of values for a setting")
            twice = any((s, param) in seen for s in spots)
            seen.update((s, param) for s in spots)
            if not values or twice or len({params[s][param] for s in spots}) > 1:
                raise ValueError(f"{where}: {values!r} is no list of values for one setting")
            for spot in spots:
                tried = tuple(_number(where, BLOCKS[row[spot]].params[param], v) for v in values)
            if any(low >= high for low, high in zip(tried, tried[1:], strict=False)):
                raise ValueError(f"{where}: {values} is not lowest first, each value once")
            made[(place, param)] = tried
    return MappingProxyType(made)


@dataclass(frozen=True)
class Spec:
    """A strategy as data. Made only by `Spec.parse`."""

    name: str
    entry: str
    exit: str
    stop: str
    filter: str
    params: Mapping[str, Mapping[str, int | Decimal]]
    source: str
    cases: tuple[Case, ...]
    ranges: Ranges  #: the settings `lab.variants` tries; none for a row tried as written

    @classmethod
    def parse(cls, row: Mapping[str, Any]) -> Spec:
        """The spec a row describes, or a ValueError naming what is wrong with it."""
        fields = {"name", "source", "params", "cases", *PLACES}
        extra = set(row) - fields - {"ranges"}
        if fields - set(row) or extra:
            raise ValueError(
                f"spec row: missing {sorted(fields - set(row))}, extra {sorted(extra)}"
            )
        name = row["name"]
        if not isinstance(name, str) or not name.strip() or not str(row["source"]).strip():
            raise ValueError(f"spec {name!r}: a name and a source are written")
        if "[" in name:  # `lab.variants` names a variant `row[settings]`: one trial, one name
            raise ValueError(f"spec {name!r}: a bracket is a variant's name, never a row's")
        if not isinstance(row["params"], Mapping) or set(row["params"]) - set(PLACES):
            raise ValueError(f"spec {name}: params are given for the places {PLACES} only")
        if not row["cases"]:
            raise ValueError(f"spec {name}: no known-answer case")
        chosen = {place: _place(row, place) for place in PLACES}
        spec = cls(
            name=name,
            source=str(row["source"]),
            params=MappingProxyType({place: chosen[place][1] for place in PLACES}),
            cases=tuple(_case(n, raw) for n, raw in enumerate(row["cases"])),
            ranges=_ranges(row, {place: chosen[place][1] for place in PLACES}),
            **{place: chosen[place][0] for place in PLACES},
        )
        spec.hold_cases()
        return spec

    def hold_cases(self) -> None:
        """Refuse the spec unless its rule gives each of its own known answers."""
        for n, case in enumerate(self.cases):
            rule, holding, said = SpecRule(self), False, []
            for k, (high, low, close) in enumerate(case.bars):
                bar = Bar(_DAY + timedelta(k), close, high, low, close, 1000)
                holding = rule.step(bar, holding)
                said.append(holding)
            if tuple(said) != case.wants:
                raise ValueError(f"spec {self.name}: case {n} gives {said}, not {case.wants}")


class SpecRule:
    """A spec as the desk's Rule: shown a bar, it says whether to be in the market."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, RANGES)

    def __init__(self, spec: Spec) -> None:
        self._blocks: dict[str, Block] = {
            place: BLOCKS[getattr(spec, place)].make(**spec.params[place]) for place in PLACES
        }

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        with localcontext(ARITHMETIC):
            fired = {place: block.see(bar, holding) for place, block in self._blocks.items()}
        if holding:
            return not (fired["exit"] or fired["stop"])
        return fired["entry"] and fired["filter"]
