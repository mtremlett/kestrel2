"""rulebook - THE LAB'S ONE LIST OF RULES BY NAME: the desk's five (`desk.strategy.STRATEGIES`),
their variants (`desk.strategy.VARIANTS`) and every rule of every `desk/eponymous_*.py`,
found by the folder, each file naming its rules in an `EPONYMOUS` mapping of name to class.

Only the five are the A-GATE's candidates: promotion, sweep and transfer stay on `STRATEGIES`.
A file that names its rules in no `EPONYMOUS` is not read here: its rules are not in the book
until it does, and the ladder refuses it loudly, by name, where it lists the eponymous rules.
"""

from __future__ import annotations

import importlib
import tomllib
from pathlib import Path

import desk
from desk.strategy import STRATEGIES, VARIANTS, Rule
from lab import variants
from lab.spec import Spec, SpecRule

DESK = Path(desk.__file__).parent  #: the folder of eponymous files
CATALOGUE = Path(__file__).parent / "catalogue.toml"  #: the spec book


def eponymous(folder: Path | None = None) -> dict[str, type[Rule]]:
    """Every rule of every eponymous file in the folder, by name; a name twice is refused."""
    found: dict[str, type[Rule]] = {}
    for path in sorted((folder or DESK).glob("eponymous_*.py")):
        module = importlib.import_module(f"{desk.__name__}.{path.stem}")
        for name, make in getattr(module, "EPONYMOUS", {}).items():
            if name in found or name in STRATEGIES or name in VARIANTS:
                raise ValueError(f"{module.__name__}: the rule {name!r} is named twice")
            found[name] = make
    return found


def specs(book: Path | None = None, folder: Path | None = None) -> dict[str, Spec]:
    """Every rule the catalogue names, as a parsed spec (each proven on its own known answers
    by `Spec.parse`); a name that is no rule of the Python files is refused."""
    table = tomllib.loads((book or CATALOGUE).read_text(encoding="utf-8"))
    python = eponymous(folder)
    unknown = sorted(set(table) - set(python))
    if unknown:
        raise ValueError(f"the catalogue names {unknown}, no rule of desk/eponymous_*.py")
    return {name: Spec.parse({"name": name, **row}) for name, row in table.items()}


def rules(folder: Path | None = None) -> dict[str, type[Rule]]:
    """The desk's five, their variants, then the eponymous rules, by name."""
    return {**STRATEGIES, **VARIANTS, **eponymous(folder)}


def rule(name: str, folder: Path | None = None) -> type[Rule]:
    """The class of the rule of that name: a book rule, or a catalogue variant by its name
    (`<row>[<place>.<param>=<v>,...]`), a `SpecRule` on that variant's spec; any other name
    is refused."""
    book = rules(folder)
    if name in book:
        return book[name]
    if "[" in name:
        try:
            return _variant(variants.find(specs(folder=folder), name))
        except ValueError as error:
            raise ValueError(f"no strategy is called {name!r}: {error}") from error
    raise ValueError(f"no strategy is called {name!r}")


def _variant(spec: Spec) -> type[Rule]:
    """A rule class that makes the spec's rule with no arguments, as every book rule does."""

    class VariantRule(SpecRule):
        def __init__(self) -> None:
            super().__init__(spec)

    return VariantRule
