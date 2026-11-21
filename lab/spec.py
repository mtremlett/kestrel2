"""spec - a strategy as data: a row naming its blocks (`lab.blocks`), their parameters, its
source and at least one known answer, built only by `Spec.parse`, which refuses a row that is
wrong in any way and says which part and why. `SpecRule` runs a spec as the desk's own Rule, so
the one engine decides on it as it decides on a Python rule.

A row: name, entry, exit, stop, filter (block names), params (per place), source and cases
(known answers: bars as [high, low, close], the wish after each). A spec with no case is
refused. Out of the market it buys when its entry fires and its filter allows; in it, it
sells when its exit or its stop fires.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
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

    @classmethod
    def parse(cls, row: Mapping[str, Any]) -> Spec:
        """The spec a row describes, or a ValueError naming what is wrong with it."""
        fields = {"name", "source", "params", "cases", *PLACES}
        if set(row) != fields:
            raise ValueError(
                f"spec row: missing {sorted(fields - set(row))}, extra {sorted(set(row) - fields)}"
            )
        name = row["name"]
        if not isinstance(name, str) or not name.strip() or not str(row["source"]).strip():
            raise ValueError(f"spec {name!r}: a name and a source are written")
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


def variants(spec: Spec, place: str, setting: str, values: tuple[int, ...]) -> tuple[Spec, ...]:
    """The spec once for each value of one setting, each checked against the block's range
    and named for its change, so the name is the trial the luck count enters. The known answers
    belong to the base spec's own settings and are not asked of a variant."""
    block = BLOCKS[getattr(spec, place)]
    if setting not in block.params or len(set(values)) != len(values) or not values:
        raise ValueError(f"spec {spec.name}: {place} takes {sorted(block.params)} once each")
    made = []
    for value in values:
        number = _number(f"{place} {setting}", block.params[setting], value)
        new = MappingProxyType({**spec.params[place], setting: number})
        made.append(
            replace(
                spec,
                name=f"{spec.name} {place}.{setting}={number}",
                params=MappingProxyType({**spec.params, place: new}),
            )
        )
    return tuple(made)


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
