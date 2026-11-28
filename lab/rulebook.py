"""rulebook - THE LAB'S ONE LIST OF RULES BY NAME: the desk's five (`desk.strategy.STRATEGIES`),
their variants (`desk.strategy.VARIANTS`) and every rule of every `desk/eponymous_*.py`,
found by the folder, each file naming its rules in an `EPONYMOUS` mapping of name to class.

Only the five are the A-GATE's candidates: promotion, sweep and transfer stay on `STRATEGIES`.
A file that names its rules in no `EPONYMOUS` is not read here: its rules are not in the book
until it does, and the ladder refuses it loudly, by name, where it lists the eponymous rules.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import tomllib
from pathlib import Path
from typing import Any

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


#: The book read once per text of the file: its rows as written and as proven specs, keyed
#: by the file and its bytes' sha256, so an edited file is read again and never served stale.
_SPEC_BOOKS: dict[tuple[Path, str], tuple[dict[str, Any], dict[str, Spec]]] = {}


def _read(book: Path | None) -> tuple[dict[str, Any], dict[str, Spec]]:
    """The catalogue's rows by name as written, and each parsed (`Spec.parse` proves its known
    answers), read again only when the file's bytes change (S1: every cell asks)."""
    path = book or CATALOGUE
    text = path.read_bytes()  # bounded: the spec book, one file of the code
    at = (path, hashlib.sha256(text).hexdigest())
    if at not in _SPEC_BOOKS:
        table = tomllib.loads(text.decode("utf-8"))
        made = {name: Spec.parse({"name": name, **r}) for name, r in table.items()}
        _SPEC_BOOKS[at] = (table, made)
    return _SPEC_BOOKS[at]


def specs(book: Path | None = None, folder: Path | None = None) -> dict[str, Spec]:
    """Every rule the catalogue names, as a parsed spec (each proven on its own known answers
    by `Spec.parse`); a row needs no Python file. `folder` is kept for the ladder's callers."""
    del folder
    return dict(_read(book)[1])


def row(name: str, book: Path | None = None) -> bytes:
    """The catalogue row a rule of that name is made from (a variant's, `row[settings]`, its
    row's), as canonical text for a key; a name with no row is refused."""
    table = _read(book)[0]
    if (base := name.partition("[")[0]) not in table:
        raise ValueError(f"no catalogue row is called {base!r}")
    return json.dumps(table[base], sort_keys=True, default=str).encode()


def _made(spec: Spec) -> type[Rule]:
    """The rule a spec makes with no arguments, `SpecRule` by module and name (as a variant's)."""
    return type(
        "SpecRule",
        (SpecRule,),
        {"__init__": lambda self: SpecRule.__init__(self, spec), "__module__": SpecRule.__module__},
    )


def rules(folder: Path | None = None) -> dict[str, type[Rule]]:
    """The desk's five, their variants, the eponymous rules, then each catalogue row with no
    Python rule, made from its spec."""
    python = {**STRATEGIES, **VARIANTS, **eponymous(folder)}
    return {**{n: _made(s) for n, s in specs().items() if n not in python}, **python}


def rule(name: str, folder: Path | None = None) -> type[Rule]:
    """The class of the rule of that name; a variant of a row (`row[settings]`) the book lacks
    is made again from its row, kept out of `rules()`; any other name is refused."""
    book = rules(folder)
    if name not in book and "[" in name:
        return variants.rule(specs(folder=folder), name)
    if name not in book:
        raise ValueError(f"no strategy is called {name!r}")
    return book[name]
