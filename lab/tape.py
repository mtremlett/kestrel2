"""tape - THE LADDER'S EXPENSIVE STAGE, KEPT (R-RUNNER-118): a rule's trades on a line, one small
file each, keyed by what made them alone (the rule's code, the engine's, the bars, the window), so
a rung edited runs no simulation. Written whole or not at all: aside, forced to disk, renamed."""

from __future__ import annotations

import hashlib
import os
import pickle
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from functools import cache
from pathlib import Path

from desk.store import Bar
from lab import cell, rulebook
from lab.cell import Cell, Record

FOLDER = "tapes"  #: under the ladder's folder in the data home
Run = Callable[[Cell, Sequence[Bar]], Record]


@cache
def rule_code(strategy: str) -> str:
    """sha256 of the code of the rule's module and every file it reaches."""
    return cell.code_version(module=rulebook.rule(strategy).__module__)


def kept(folder: Path, run: Run, code_of: Callable[[str], str] = rule_code) -> Run:
    """`run` with each answer kept as a tape under folder, and read from it when held."""

    def tape(c: Cell, bars: Sequence[Bar]) -> Record:
        now = cell.key(c, bars)
        parts = (code_of(c.strategy), now.code, now.data, str(c))
        name = hashlib.sha256("\n".join(parts).encode()).hexdigest()
        path = folder / name[:2] / f"{name}.tape"
        if path.exists():  # our own file, written whole by this module
            return Record(now, *pickle.loads(path.read_bytes()))  # noqa: S301
        record = run(c, bars)
        path.parent.mkdir(parents=True, exist_ok=True)
        with (fresh := path.with_suffix(".new")).open("wb", buffering=0) as out:
            out.write(pickle.dumps((record.bars, record.trades)))
            os.fsync(out.fileno())
        fresh.replace(path)
        return record

    return tape


@contextmanager
def on(folder: Path) -> Iterator[None]:
    """`cell.run` keeps tapes under folder for the length of the block."""
    before = cell.run
    cell.run = kept(folder, before)  # type: ignore[assignment]  # the one place it is swapped
    try:
        yield
    finally:
        cell.run = before
