"""tape - THE LADDER'S EXPENSIVE STAGE, KEPT (R-RUNNER-118): a rule's trades on a line, one file
each, stored compressed, keyed by what made them (rule's code, engine's, bars), so an edited
rung runs no simulation. Written whole or not at all: aside, forced to disk, renamed.

ONE SIMULATION PER LINE (R-RUNNER-169): a rule is run once on a line, from its first bar to its
last, and every window (the first rung's, each fold's) is cut from that tape by date. A rule sees
no bar after the one it decides on (the future-blind property test), so the cut is the record the
window's own run would give: trades bought inside it, one still held at its end unsold.

THE RATES ARE NOT IN THE KEY (#398): a tape holds trades, not money; costs, capital and rates
price it afterwards in the rungs, so a change of settings re-prices the kept tape and simulates
nothing."""

from __future__ import annotations

import ast
import hashlib
import os
import pickle
import zlib
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from functools import cache
from pathlib import Path

from desk.store import Bar
from lab import cell, rulebook
from lab.cell import Cell, Record, Trade
from lab.spec import SpecRule

FOLDER = "tapes"
Run = Callable[[Cell, Sequence[Bar]], Record]


def _own_text(source: bytes, mine: type, others: set[str]) -> bytes:
    """The module's source with the top-level classes of the other rules cut out; a rule class
    not defined at the top level (made at run time) keys by the whole module."""
    tree = ast.parse(source)
    top = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
    if mine.__name__ not in top:
        return source
    lines = source.splitlines(keepends=True)
    for name in others & top.keys():
        node = top[name]
        last = node.end_lineno or node.lineno
        first = min([node.lineno, *(d.lineno for d in node.decorator_list)])
        lines[first - 1 : last] = [b""] * (last - first + 1)
    return b"".join(lines)


def code_of_rule(
    strategy: str, root: Path = cell.ROOT, folder: Path | None = None, book: Path | None = None
) -> str:
    """sha256 of the files the rule's module reaches, its own file without the other rules'
    classes, and for a rule made from a catalogue row that row as written (T1): an edited param
    is a new key. A Windows line ending is not a change."""
    known, mine = rulebook.rules(folder), rulebook.rule(strategy, folder)
    module = mine.__module__
    others = {c.__name__ for c in known.values() if c.__module__ == module and c is not mine}
    digest = hashlib.sha256()
    for path in cell.reached(root, module):
        data = (root / path).read_bytes()  # bounded: one source file of the code
        if path == module.replace(".", "/") + ".py":
            data = _own_text(data, mine, others)
        digest.update(data.replace(b"\r\n", b"\n") + b"\0")
    if issubclass(mine, SpecRule):  #: its trades are its row's: the row is its code too
        digest.update(rulebook.row(strategy, book))
    return digest.hexdigest()


@cache
def rule_code(strategy: str) -> str:
    """sha256 of the code of the rule's module (its siblings' classes cut) and what it reaches."""
    return code_of_rule(strategy)


def kept(folder: Path, run: Run, code_of: Callable[[str], str] = rule_code) -> Run:
    """`run` with each answer kept as a tape under folder, read back when held."""

    def tape(c: Cell, bars: Sequence[Bar]) -> Record:
        if not bars:
            return run(c, bars)  #: the cell engine refuses it, in its own words
        whole = Cell(c.strategy, c.line, bars[0].day, bars[-1].day)
        now = cell.key(whole, bars)
        text = "\n".join((code_of(c.strategy), now.code, now.data, str(whole)))
        path = folder / f"{hashlib.sha256(text.encode()).hexdigest()}.tape"
        if path.exists():  # our own file, written whole by this module
            raw = path.read_bytes()  # bounded: one rule on one line, written once, never added to
            held = Record(now, *pickle.loads(zlib.decompress(raw)))  # noqa: S301
        else:
            held = run(whole, bars)
            folder.mkdir(parents=True, exist_ok=True)
            aside = path.with_suffix(f".{os.getpid()}.new")  #: workers of a pass may share a tape
            with (fresh := aside).open("wb", buffering=0) as out:
                out.write(zlib.compress(pickle.dumps((held.bars, held.trades))))
                os.fsync(out.fileno())
            fresh.replace(path)
        return _cut(c, held, bars)

    return tape


def _cut(c: Cell, whole: Record, bars: Sequence[Bar]) -> Record:
    """The record of the window c from the tape of the whole line."""
    inside = sum(1 for bar in cell.shown(c, bars) if bar.day >= c.start)
    if not inside:
        raise ValueError(f"{c}: no bars in the window")
    trades = (
        Trade(t.bought, t.sold if t.sold is not None and t.sold <= c.end else None)
        for t in whole.trades
        if c.start <= t.bought <= c.end
    )
    return Record(cell.key(c, bars), inside, tuple(trades))


@contextmanager
def on(folder: Path) -> Iterator[None]:
    """`cell.run` keeps tapes under folder for the length of the block."""
    before = cell.run
    cell.run = kept(folder, before)  # type: ignore[assignment]  # the one place it is swapped
    try:
        yield
    finally:
        cell.run = before
