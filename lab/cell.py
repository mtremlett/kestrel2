"""cell - THE LADDER'S UNIT OF WORK: one strategy on one line over one window, and the record
of what it did there, keyed by the versions of the code and the bars that produced it.

The trades are the desk's own decisions. The fast grid engine (`lab/grid.py`) works them out
wherever it can; it holds what the desk's engine holds after every bar or it refuses, and a
cell it refuses is decided by the desk's own engine (`strategy.decide`), the same record
either way. The rule is shown every bar the line has up to the window's end, so the history
before the window warms it, and nothing after the end is read. A trade belongs to the window
it was bought in. The record holds days only: a price, a profit or a verdict is a later
rung's, and none is reported without its costs.

Two records with the same key are the same result. The code version is every file of this
repository this module reaches through its imports, read once as the process loads it, so a key
never claims code the process is not running. The data version is every bar the rule read.
"""

from __future__ import annotations

import ast
import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from desk import strategy
from desk.lines import LINES
from desk.store import Bar
from desk.strategy import Action
from lab import grid

ROOT = Path(__file__).parents[1]


@dataclass(frozen=True)
class Cell:
    strategy: str
    symbol: str
    start: date  #: the first day whose buys belong to the cell
    end: date  #: the last bar the rule is shown

    def __post_init__(self) -> None:
        if self.strategy not in strategy.STRATEGIES:
            raise ValueError(f"no strategy is called {self.strategy!r}")
        if self.symbol not in {line.symbol for line in LINES}:
            raise ValueError(f"{self.symbol!r} is not a line in the instrument master")
        if self.end < self.start:
            raise ValueError(f"{self.symbol}: a window that ends before it starts")


@dataclass(frozen=True)
class Trade:
    bought: date
    sold: date | None  #: None while still held at the window's end


@dataclass(frozen=True)
class Key:
    cell: Cell
    code: str  #: sha256 of the code that produced the record
    data: str  #: sha256 of every bar the rule was shown


@dataclass(frozen=True)
class Record:
    key: Key
    bars: int  #: bars inside the window
    trades: tuple[Trade, ...]


def _file(root: Path, name: str) -> str | None:
    """The file under root that the dotted module name is loaded from, if it is one."""
    parts = name.split(".")
    for candidate in ("/".join(parts) + "/__init__.py", "/".join(parts) + ".py"):
        if (root / candidate).is_file():
            return candidate
    return None


def _imports(root: Path, path: str) -> set[str]:
    """Every file under root that the file at path imports, its packages included."""
    names: set[str] = set()
    for node in ast.walk(ast.parse((root / path).read_bytes(), path)):
        if isinstance(node, ast.ImportFrom):
            if node.level:
                raise ValueError(f"{path}: a relative import the code version cannot follow")
            module = node.module or ""
            names |= {module} | {f"{module}.{alias.name}" for alias in node.names}
        elif isinstance(node, ast.Import):
            names |= {alias.name for alias in node.names}
    return set().union(*(_files(root, name) for name in names))


def _files(root: Path, name: str) -> set[str]:
    """The files under root loaded to import the dotted name: its packages', and its own."""
    parts = name.split(".")
    found = {_file(root, ".".join(parts[:n])) for n in range(1, len(parts) + 1)}
    return {f for f in found if f is not None}


def reached(root: Path) -> tuple[str, ...]:
    """lab/cell.py, its package, and every file under root they reach through imports."""
    seen, waiting = set(), _files(root, "lab.cell")
    while waiting:
        path = waiting.pop()
        seen.add(path)
        waiting |= _imports(root, path) - seen
    return tuple(sorted(seen))


def code_version(root: Path = ROOT) -> str:
    """sha256 of the text of every file reached; a Windows line ending is not a change."""
    digest = hashlib.sha256()
    for path in reached(root):
        digest.update((root / path).read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return digest.hexdigest()


#: The code this process loaded, read once as it loads it.
LOADED = code_version()


def _data_version(bars: Sequence[Bar]) -> str:
    digest = hashlib.sha256()
    for bar in bars:
        row = (bar.day, bar.open, bar.high, bar.low, bar.close, bar.volume)
        digest.update((",".join(str(field) for field in row) + "\n").encode())
    return digest.hexdigest()


def _held(cell: Cell, bars: Sequence[Bar]) -> list[bool]:
    """Whether the rule is in the market after each bar: the grid's answer, and the desk's
    own engine's wherever the grid refuses to give one."""
    try:
        held: list[bool] = grid.held(cell.strategy, grid.prices(bars)).tolist()
    except grid.TooClose:
        held = []
        for decision in strategy.decide({cell.symbol: bars}):
            if decision.strategy == cell.strategy:
                was = held[-1] if held else False
                held.append({Action.BUY: True, Action.SELL: False}.get(decision.action, was))
    return held


def _trades(cell: Cell, bars: Sequence[Bar]) -> tuple[Trade, ...]:
    held = _held(cell, bars)
    #: the days it went in or came out, by turns: it starts out, so a buy comes first
    before = [False, *held[:-1]]
    turns = [bar.day for bar, now, was in zip(bars, held, before, strict=True) if now != was]
    pairs = zip(turns[::2], [*turns[1::2], None], strict=False)
    return tuple(Trade(bought, sold) for bought, sold in pairs if bought >= cell.start)


def shown(cell: Cell, bars: Sequence[Bar]) -> tuple[Bar, ...]:
    """The bars the rule is shown: the line's, oldest first, up to the window's end."""
    if any(later.day <= bar.day for bar, later in zip(bars, bars[1:], strict=False)):
        raise ValueError(f"{cell.symbol}: bars not one a day, oldest first")
    return tuple(bar for bar in bars if bar.day <= cell.end)


def key(cell: Cell, bars: Sequence[Bar]) -> Key:
    """The key the cell's record from these bars would carry, without running the rule."""
    return Key(cell, LOADED, _data_version(shown(cell, bars)))


def run(cell: Cell, bars: Sequence[Bar]) -> Record:
    """The cell's record from the line's bars, oldest first; bars after its end are not read."""
    read = shown(cell, bars)
    inside = sum(1 for bar in read if bar.day >= cell.start)
    if not inside:
        raise ValueError(
            f"{cell.strategy} on {cell.symbol}, {cell.start} to {cell.end}: no bars in the window"
        )
    return Record(Key(cell, LOADED, _data_version(read)), inside, _trades(cell, read))
