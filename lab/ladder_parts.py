"""ladder_parts - the ladder's plain parts, which judge nothing: the results file read as far as
its last whole line, each cell's last row, the counts of a run's rows, when a failed cell is due
again, and the files of the eponymous rules (their code's hash, their names).

Split out of `lab/ladder.py` to keep it under its cap; `lab/ladder.py` imports them and its
callers keep importing from it.
"""

from __future__ import annotations

import hashlib
import importlib
import inspect
import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

import desk
from desk.strategy import Rule
from lab import rulebook, verdict

DESK = Path(desk.__file__).parent  #: the one list of eponymous files: this folder
#: A cell that waits on data is tried again no sooner than this after its last try.
RETRY = timedelta(minutes=30)


def _whole(results: Path) -> bytes:
    """The results file as far as its last whole line: a line a stop cut short is cut off."""
    text = results.read_bytes() if results.exists() else b""
    return text[: text.rfind(b"\n") + 1]


def _last(whole: bytes) -> dict[tuple[str, ...], verdict.Row]:
    """Each cell's last line in the results: its answer now."""
    return {tuple(row["cell"]): row for row in map(json.loads, whole.splitlines())}


def _count(tally: Counter[str], row: verdict.Row, was: verdict.Row | None) -> None:
    """Add one cell's line to the counts."""
    fate = next((k for k in ("error", "refused") if k in row), "kept" if row is was else "judged")
    tally[fate] += 1
    tally[row.get("answer", "none")] += 1
    tally["missed"] += fate in ("kept", "judged") and "unrun" not in row
    tally["short"] += "unrun" in row and "answer" not in row
    tally["every"] += row.get("every", False)
    tally["behind"] += row.get("every", False) and "reproduce" in row["rungs"]


def _due(was: verdict.Row, now: datetime) -> bool:
    """A failed cell is tried again once its last try is 30 minutes old."""
    return "error" in was and now - datetime.fromisoformat(was["tried"]) >= RETRY


def code(folder: Path = DESK) -> str:
    """sha256 of every eponymous file's text, line endings aside: part of every key."""
    texts = [p.read_bytes().replace(b"\r\n", b"\n") for p in sorted(folder.glob("eponymous_*.py"))]
    return hashlib.sha256(b"\0".join(texts)).hexdigest()


def eponymous(folder: Path = DESK, book: Path | None = None) -> tuple[str, ...]:
    """Every rule of every `desk/eponymous_*.py`, then any the catalogue's specs add; a file with no
    `EPONYMOUS` is refused. A rule that takes data (Zweig's breadth) is left out. A name in both is
    one rule, listed once: the specs are read beside the Python rules, so none goes unregistered
    when the Python ones go."""
    for path in sorted(folder.glob("eponymous_*.py")):
        module = importlib.import_module(f"{desk.__name__}.{path.stem}")
        if not hasattr(module, "EPONYMOUS"):
            raise ValueError(f"{module.__name__} names its rules in no EPONYMOUS mapping")
    python = tuple(n for n, make in rulebook.eponymous(folder).items() if not _needs_data(make))
    return python + tuple(n for n in rulebook.specs(book, folder) if n not in python)


def _needs_data(make: type[Rule]) -> bool:
    """Whether the rule cannot be made without an argument."""
    return any(p.default is p.empty for p in inspect.signature(make).parameters.values())
