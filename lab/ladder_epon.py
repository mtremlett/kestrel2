"""ladder_epon - THE EPONYMOUS RULES THE LADDER LISTS: every rule of every `desk/eponymous_*.py`,
then any the catalogue's specs add, each listed once; a rule that takes data is left out. Split out
of `lab/ladder.py` (O79), whose sets judge them; it never imports the ladder."""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path

import desk
from desk.strategy import Rule
from lab import rulebook

DESK = Path(desk.__file__).parent  #: the one list of eponymous files: this folder


def eponymous(folder: Path = DESK, book: Path | None = None) -> tuple[str, ...]:
    """Every rule of every `desk/eponymous_*.py`, then any the catalogue's specs add; a file with no
    `EPONYMOUS` is refused. A rule that takes data (Zweig's breadth) is left out. A name in both is
    one rule, listed once: the specs are read beside the Python rules, so none goes unregistered
    when the Python ones go."""
    for path in sorted(folder.glob("eponymous_*.py")):
        module = importlib.import_module(f"{desk.__name__}.{path.stem}")
        if not hasattr(module, "EPONYMOUS"):
            raise ValueError(f"{module.__name__} names its rules in no EPONYMOUS mapping")
    every = rulebook.eponymous(folder)
    python = tuple(n for n, make in every.items() if not _needs_data(make))
    return python + tuple(
        n
        for n, spec in rulebook.specs(book, folder).items()
        if n not in python and not _needs_data(every.get(n) or rulebook._made(spec))
    )


def _needs_data(make: type[Rule]) -> bool:
    """Whether the rule cannot be made without an argument."""
    return any(p.default is p.empty for p in inspect.signature(make).parameters.values())
