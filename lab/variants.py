"""variants - A ROW'S SETTINGS TRIED, EACH ONE COUNTED: the variants of a spec row made from
the ranges of its settings, every one entered as a trial before it is run, and the centre of
a plateau reported, never a lone peak (canon B6).

A row's ranges (`Spec.ranges`, written in the catalogue and held to each block's declaration
by `Spec.parse`) each name one setting (its place and parameter) and the values to try,
lowest first. The variants are every combination of the ranges, 3 values and 4 make 12, in
the order of the ranges given, and the range's order is the plateau grid's (`lab.plateau`).

A variant is its row with other settings, so the row's known answers, which hold only at
the row's own, are not asked of it. Its name carries its settings and so tells it apart as a
trial; `find` makes it again from that name alone, and `enter` counts them all under the
question, and a variant never run counts as much as one that won. The pick is `lab.plateau`'s:
the deepest setting of the passing surface.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from itertools import product
from pathlib import Path
from types import MappingProxyType

from lab import plateau, trials
from lab.plateau import Chosen, Setting
from lab.rung import Verdict
from lab.spec import PLACES, Spec


@dataclass(frozen=True)
class Variant:
    """A row with other settings, and the settings that made it."""

    setting: Setting  #: one value for each range, in the ranges' order
    spec: Spec  #: the row with these settings, named by them


def variants(spec: Spec) -> tuple[Variant, ...]:
    """Every combination of the row's ranges as a spec of its own; a row without is refused."""
    if not spec.ranges:
        raise ValueError(f"spec {spec.name}: no ranges, so no variants")
    made = []
    for setting in product(*spec.ranges.values()):
        params = {place: dict(spec.params[place]) for place in PLACES}
        for (place, param), value in zip(spec.ranges, setting, strict=True):
            params[place][param] = value
        label = ",".join(
            f"{place}.{param}={v}" for (place, param), v in zip(spec.ranges, setting, strict=True)
        )
        frozen = MappingProxyType({place: MappingProxyType(p) for place, p in params.items()})
        named = f"{spec.name}[{label}]"  # a variant is tried as written: no ranges of its own
        made.append(Variant(setting, replace(spec, name=named, params=frozen, ranges={})))
    return tuple(made)


def find(specs: Mapping[str, Spec], name: str) -> Spec:
    """The variant of that name made again from its row, so a cell named by it can be run; a
    name no row's ranges make is refused."""
    row = specs.get(name.rpartition("[")[0])
    made = {v.spec.name: v.spec for v in variants(row)} if row and row.ranges else {}
    if name not in made:
        raise ValueError(f"no variant is called {name!r}")
    return made[name]


def enter(register: Path, question: str, made: Sequence[Variant]) -> int:
    """All the variants counted as trials under the question, before any is run; the
    question's count after them."""
    return trials.enter(register, question, [variant.spec.name for variant in made])


def centre(spec: Spec, surface: Mapping[Setting, Verdict]) -> Chosen:
    """The centre of the best plateau on the row's surface, as the plateau module finds it."""
    return plateau.choose(list(spec.ranges.values()), surface)
