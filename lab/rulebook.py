"""rulebook - THE LAB'S ONE LIST OF RULES BY NAME: the desk's five (`desk.strategy.STRATEGIES`)
and every rule of every `desk/eponymous_*.py`, found by the folder, each file naming its rules
in an `EPONYMOUS` mapping of name to class.

Only the five are the A-GATE's candidates: promotion, sweep and transfer stay on `STRATEGIES`.
A file that names its rules in no `EPONYMOUS` is not read here: its rules are not in the book
until it does, and the ladder refuses it loudly, by name, where it lists the eponymous rules.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import desk
from desk.strategy import STRATEGIES, Rule

DESK = Path(desk.__file__).parent  #: the folder of eponymous files


def eponymous(folder: Path | None = None) -> dict[str, type[Rule]]:
    """Every rule of every eponymous file in the folder, by name; a name twice is refused."""
    found: dict[str, type[Rule]] = {}
    for path in sorted((folder or DESK).glob("eponymous_*.py")):
        module = importlib.import_module(f"{desk.__name__}.{path.stem}")
        for name, make in getattr(module, "EPONYMOUS", {}).items():
            if name in found or name in STRATEGIES:
                raise ValueError(f"{module.__name__}: the rule {name!r} is named twice")
            found[name] = make
    return found


def rules(folder: Path | None = None) -> dict[str, type[Rule]]:
    """The desk's five, then the eponymous rules, by name."""
    return {**STRATEGIES, **eponymous(folder)}


def rule(name: str, folder: Path | None = None) -> type[Rule]:
    """The class of the rule of that name; a name the book does not know is refused."""
    book = rules(folder)
    if name not in book:
        raise ValueError(f"no strategy is called {name!r}")
    return book[name]
