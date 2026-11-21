"""variants - A ROW'S SETTINGS TRIED, EACH ONE COUNTED: the variants of a spec row made from
the ranges of its settings, every one entered as a trial before it is run, and the centre of
a plateau reported, never a lone peak (canon B6).

A range names one setting of the row (its place and parameter) and the values to try, lowest
first. A block declares what a setting may be (`lab.blocks`); every value is held to that
declaration. The variants are every combination of the ranges, 3 values and 4 make 12, in
the order of the ranges given, and the range's order is the plateau grid's (`lab.plateau`).

A variant is its row with other settings, so the row's known answers, which hold only at
the row's own, are not asked of it. Its name carries its settings and so tells it apart as a
trial; `enter` counts them all under the question, and a variant never run counts as much as
one that won. The pick is `lab.plateau`'s: the deepest setting of the passing surface.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from itertools import product
from pathlib import Path
from types import MappingProxyType

from lab import plateau, trials
from lab.blocks import BLOCKS
from lab.plateau import Chosen, Setting, Value
from lab.rung import Verdict
from lab.spec import PLACES, Spec, _number

#: One setting of a row, as (place, parameter), and the values to try, lowest first.
Ranges = Mapping[tuple[str, str], Sequence[Value]]


@dataclass(frozen=True)
class Variant:
    """A row with other settings, and the settings that made it."""

    setting: Setting  #: one value for each range, in the ranges' order
    spec: Spec  #: the row with these settings, named by them


def variants(spec: Spec, ranges: Ranges) -> tuple[Variant, ...]:
    """Every combination of the ranges as a spec of its own; a range off the row, or a value
    outside what its block allows, is refused."""
    if not ranges:
        raise ValueError(f"spec {spec.name}: no ranges, so no variants")
    for place, param in ranges:
        if place not in PLACES or param not in spec.params[place]:
            raise ValueError(f"spec {spec.name}: no setting {param!r} at {place!r} to range over")
    for (place, param), values in ranges.items():
        if len(set(values)) != len(values):
            raise ValueError(f"spec {spec.name}: {place} {param} repeats a value in {list(values)}")
    made = []
    for setting in product(*ranges.values()):
        params = {place: dict(spec.params[place]) for place in PLACES}
        for (place, param), value in zip(ranges, setting, strict=True):
            where = f"spec {spec.name} {place} {param}"
            params[place][param] = _number(where, BLOCKS[getattr(spec, place)].params[param], value)
        label = ",".join(
            f"{place}.{param}={v}" for (place, param), v in zip(ranges, setting, strict=True)
        )
        frozen = MappingProxyType({place: MappingProxyType(p) for place, p in params.items()})
        made.append(Variant(setting, replace(spec, name=f"{spec.name}[{label}]", params=frozen)))
    return tuple(made)


def enter(register: Path, question: str, made: Sequence[Variant]) -> int:
    """All the variants counted as trials under the question, before any is run; the
    question's count after them."""
    return trials.enter(register, question, [variant.spec.name for variant in made])


def centre(ranges: Ranges, surface: Mapping[Setting, Verdict]) -> Chosen:
    """The centre of the best plateau on the surface, as the plateau module finds it."""
    return plateau.choose([tuple(values) for values in ranges.values()], surface)
