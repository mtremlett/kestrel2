"""tape - THE LADDER'S EXPENSIVE STAGE, KEPT (R-RUNNER-118): a rule's trades on a line, one file
each, keyed by what made them (rule's code, engine's, bars, window), so an edited rung runs no
simulation. Written whole or not at all: aside, forced to disk, renamed."""

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

FOLDER = "tapes"
Run = Callable[[Cell, Sequence[Bar]], Record]


@cache
def rule_code(strategy: str) -> str:
    """sha256 of the code of the rule's module and what it reaches."""
    return cell.code_version(module=rulebook.rule(strategy).__module__)


def kept(folder: Path, run: Run, code_of: Callable[[str], str] = rule_code) -> Run:
    """`run` with each answer kept as a tape under folder, read back when held."""

    def tape(c: Cell, bars: Sequence[Bar]) -> Record:
        now = cell.key(c, bars)
        text = f"{code_of(c.strategy)}\n{now.code}\n{now.data}\n{c}"
        path = folder / f"{hashlib.sha256(text.encode()).hexdigest()}.tape"
        if path.exists():  # our own file, written whole by this module
            return Record(now, *pickle.loads(path.read_bytes()))  # noqa: S301
        record = run(c, bars)
        folder.mkdir(parents=True, exist_ok=True)
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
