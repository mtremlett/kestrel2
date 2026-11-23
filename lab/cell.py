"""cell - THE LADDER'S UNIT OF WORK: one strategy on one line over one window, and the record
of what it did there, keyed by the versions of the code and the bars that produced it.

The trades are the desk's own decisions. The fast grid engine (`lab/grid.py`) works them out
wherever it can; it holds what the desk's engine holds after every bar or it refuses, and a
cell it refuses is decided by the desk's own engine (`strategy.decide`), the same record
either way. The rule is shown every bar the line has up to the window's end, so the history
before the window warms it, and nothing after the end is read. A trade belongs to the window
it was bought in. The record holds days only: a price, a profit or a verdict is a later
rung's, and none is reported without its costs.

A cell names its line, not a symbol: one symbol can be two companies (BA is Boeing in New
York and BAE Systems in London), so the venue is part of what a cell is. Any line may be
studied, one of the research list as much as one of the twenty; studying it trades nothing.

Two records with the same key are the same result. The code version is every file of this
repository this module reaches through its imports, read once as the process loads it, so a key
never claims code the process is not running. The data version is every bar the rule read.

A rung makes something of a record (a verdict, a correction), and what it makes has a key of
its own (`Key.rung`): the record's, and every file the rung's module reaches. The first rung
reaches the desk's cost model, so a change of costs gives every verdict a new key and leaves
the trades theirs: only what a change touches is run again.
"""

from __future__ import annotations

import ast
import hashlib
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import date
from decimal import localcontext
from pathlib import Path

from desk import strategy
from desk.lines import Line
from desk.store import Bar
from desk.strategy import ARITHMETIC, STRATEGIES, Action, _run
from lab import grid, rulebook

ROOT = Path(__file__).parents[1]
CELL = "lab.cell"  #: this module, the foot of the ladder


@dataclass(frozen=True, init=False)
class Cell:
    strategy: str
    line: Line  #: the ticker on its venue, with its facts
    start: date  #: the first day whose buys belong to the cell
    end: date  #: the last bar the rule is shown

    def __init__(self, strategy: str, line: Line, start: date, end: date) -> None:
        if not isinstance(line, Line):
            raise TypeError(f"a cell names a Line, not {type(line).__name__} {line!r}")
        if strategy not in STRATEGIES:
            rulebook.rule(strategy)  #: refuses a name the rule book does not know
        if end < start:
            raise ValueError(f"{line.symbol} on {line.venue}: a window that ends before it starts")
        made = (("strategy", strategy), ("line", line), ("start", start), ("end", end))
        for field, value in made:
            object.__setattr__(self, field, value)

    def __str__(self) -> str:
        on = f"{self.line.symbol} on {self.line.venue}"
        return f"{self.strategy} on {on}, {self.start} to {self.end}"


@dataclass(frozen=True)
class Trade:
    bought: date
    sold: date | None  #: None while still held at the window's end


@dataclass(frozen=True)
class Key:
    cell: Cell
    code: str  #: sha256 of the code that produced the record
    data: str  #: sha256 of every bar the rule was shown

    def rung(self, module: str) -> Key:
        """The key of what the rung in that module makes of what this key names: its code is
        this key's and everything the rung's module reaches, the cost model with the rest."""
        if module not in RUNGS:
            raise ValueError(f"{module} is not a rung: no module of lab/ that reaches the cell")
        made = hashlib.sha256(f"{self.code}\n{RUNGS[module]}".encode()).hexdigest()
        return replace(self, code=made)


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


def _closure(root: Path, graph: dict[str, set[str]], start: set[str], out: set[str]) -> set[str]:
    """The files reachable from start through the graph, never entering a file in `out`."""
    seen, waiting = set(), set(start)
    while waiting:
        path = waiting.pop()
        seen.add(path)
        if path not in graph:
            graph[path] = _imports(root, path)
        waiting |= graph[path] - seen - out
    return seen


def reached(
    root: Path, module: str = CELL, graph: dict[str, set[str]] | None = None
) -> tuple[str, ...]:
    """The module's file, its packages', and every file under root they reach through imports,
    except the files that reach the module in turn: they run it, they do not judge for it, so
    a change to a runner of the module is not a change to what it makes. `graph` is shared by
    callers that ask for many modules, so each file is parsed once (R-GRID-7)."""
    if (own := _file(root, module)) is None:
        raise ValueError(f"{module}: no module of that name under {root}")
    graph = {} if graph is None else graph
    start = _files(root, module)
    everything = _closure(root, graph, start, set())
    upward: set[str] = (
        set()
    )  # the files that reach the module, found walking the imports backwards once
    waiting = {own}
    while waiting:
        waiting = {p for p in everything if graph[p] & waiting} - upward
        upward |= waiting
    return tuple(sorted(_closure(root, graph, start, upward - start)))


def code_version(
    root: Path = ROOT, module: str = CELL, graph: dict[str, set[str]] | None = None
) -> str:
    """sha256 of the text of every file reached; a Windows line ending is not a change."""
    digest = hashlib.sha256()
    for path in reached(root, module, graph):
        digest.update((root / path).read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return digest.hexdigest()


def rungs(root: Path = ROOT, graph: dict[str, set[str]] | None = None) -> dict[str, str]:
    """The code version of each rung: a module of lab/ that reaches this one, whose trades
    it makes something of. One import graph for all of them: each file parsed once."""
    graph = {} if graph is None else graph
    names = [f"lab.{path.stem}" for path in sorted((root / "lab").glob("[!_]*.py"))]
    upon = [
        name for name in names if name != CELL and _file(root, CELL) in reached(root, name, graph)
    ]
    return {name: code_version(root, name, graph) for name in upon}


#: The code this process loaded, read once as it loads it: this module's, and each rung's,
#: so no key claims a cost model or a rung edited on disk since. One graph: each file parsed once.
_GRAPH: dict[str, set[str]] = {}
LOADED = code_version(ROOT, CELL, _GRAPH)
RUNGS = rungs(ROOT, _GRAPH)


def _data_version(bars: Sequence[Bar]) -> str:
    digest = hashlib.sha256()
    for bar in bars:
        row = (bar.day, bar.open, bar.high, bar.low, bar.close, bar.volume)
        digest.update((",".join(str(field) for field in row) + "\n").encode())
    return digest.hexdigest()


#: Each (line, end) hashed once: the bars object it was hashed from, its length, the digest.
#: Another bars object for the same line (a placebo's) is not the same bars: it is hashed again.
_HASHED: dict[tuple[Line, date], tuple[Sequence[Bar], int, str]] = {}


def _version(cell: Cell, bars: Sequence[Bar], read: Sequence[Bar]) -> str:
    """The data version of `read`, the bars shown up to the cell's end, hashed once per
    (line, end) while the same bars are asked about; the digest is the same as hashing anew."""
    at = (cell.line, cell.end)
    memo = _HASHED.get(at)
    if memo is not None and memo[0] is bars and memo[1] == len(bars):
        return memo[2]
    version = _data_version(read)
    _HASHED[at] = (bars, len(bars), version)
    return version


def _held(cell: Cell, bars: Sequence[Bar]) -> list[bool]:
    """Whether the rule is in the market after each bar: the grid's answer, and the desk's
    own engine's wherever the grid refuses to give one."""
    if cell.strategy not in STRATEGIES:  #: an eponymous rule has no array form: the desk's engine
        held: list[bool] = []
        with localcontext(ARITHMETIC):
            for decision in _run(
                cell.strategy, rulebook.rule(cell.strategy)(), cell.line.symbol, bars
            ):
                was = held[-1] if held else False
                held.append({Action.BUY: True, Action.SELL: False}.get(decision.action, was))
        return held
    try:
        held = grid.held(cell.strategy, grid.prices(bars)).tolist()
    except grid.TooClose:
        held = []
        for decision in strategy.decide({cell.line.symbol: bars}):
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
        raise ValueError(f"{cell}: bars not one a day, oldest first")
    return tuple(bar for bar in bars if bar.day <= cell.end)


def key(cell: Cell, bars: Sequence[Bar]) -> Key:
    """The key the cell's record from these bars would carry, without running the rule."""
    return Key(cell, LOADED, _version(cell, bars, shown(cell, bars)))


def run(cell: Cell, bars: Sequence[Bar]) -> Record:
    """The cell's record from the line's bars, oldest first; bars after its end are not read."""
    read = shown(cell, bars)
    inside = sum(1 for bar in read if bar.day >= cell.start)
    if not inside:
        raise ValueError(f"{cell}: no bars in the window")
    return Record(Key(cell, LOADED, _version(cell, bars, read)), inside, _trades(cell, read))
