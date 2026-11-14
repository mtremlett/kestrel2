"""trials - THE REGISTER OF TRIALS: every trial ever tried on a question, kept from batch to
batch, so a winner is corrected for all of them and no later batch starts the count again.

The luck rung (`lab/luck.py`) multiplies a winner's chance by the number of trials it was
picked from. Left to each batch, that number forgets: ten batches of five trials are fifty
looks at one question, and each batch alone would own up to five. So the count lives here, in
one file that outlasts every batch, and this module's `correct` takes it from that file alone.
The file's home is the caller's to give: one fixed path in the desk's data folder, never one
inside a working copy, which a session throws away.

A trial is entered under the question it was asked of, by name, BEFORE it is run: then one
that fails, gives no verdict or is dropped has been counted already, and nothing here takes
a trial out. A cell's name is its rule, its line and venue and its window, so the same cell
run again (a restart, mended bars) is the same trial, and the same rule on another line or
window is another. A rule that is changed is a new trial and must be given a new name: the
register cannot see a change made under an old one. A candidate that is no cell is entered
under any name that tells it apart. A trial asked of two questions counts in each.

Nothing begins a count without a word. A register that is not there, or is empty, is
refused: a new one is started on purpose, once, with `start`. A question is opened on
purpose, once, with `ask`, and a trial or a verdict under any other wording is refused, so
a question spelled anew cannot begin again at nothing.

The register holds one JSON line per question and per trial, appended and forced to disk
before `enter` returns. A line a stop cut short is an entry that never finished: it is cut
off, and its batch never ran. A whole line that is not a question or a trial is damage, and
is refused. One process at a time writes, which is the caller's to keep; a stale read is caught.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable, Sequence
from pathlib import Path

from lab import luck
from lab.cell import Cell
from lab.luck import Corrected
from lab.rung import Verdict

HEAD = b'{"register": "trials"}\n'  #: a register's first line: an empty file is not one


def name(cell: Cell) -> str:
    """The cell as a trial: its rule, its line on its venue, its window. The register's own
    wording, kept apart from how a cell is printed, which may change."""
    line, window = cell.line, f"{cell.start.isoformat()} to {cell.end.isoformat()}"
    return f"{cell.strategy} on {line.symbol} on {line.venue}, {window}"


def start(register: Path) -> None:
    """A new register with no question in it; refused where a file already is."""
    with register.open("xb") as out:
        out.write(HEAD)


def ask(register: Path, question: str) -> None:
    """The question opened, with no trial yet; refused if it has been asked before."""
    entered, text = _read(register)
    if not question or question != question.strip() or question in entered:
        raise ValueError(f"{question!r}: asked already, or not a plain question")
    _append(register, text, [{"question": question}])


def enter(register: Path, question: str, trials: Iterable[str]) -> int:
    """These trials counted under the question, each once however often it is entered; the
    question's count after them."""
    entered, text = _read(register)
    known = _asked(entered, question)
    names = tuple(trials)
    if isinstance(trials, str) or not all(trial.strip() for trial in names):
        raise ValueError(f"{question!r}: a trial without a name cannot be counted")
    new = [trial for trial in dict.fromkeys(names) if trial not in known]
    _append(register, text, [{"question": question, "trial": trial} for trial in new])
    return len(known) + len(new)


def count(register: Path, question: str) -> int:
    """Every trial ever entered under the question."""
    return len(_asked(_read(register)[0], question))


def correct(register: Path, question: str, verdicts: Sequence[Verdict]) -> tuple[Corrected, ...]:
    """The luck rung's correction of these verdicts, for every trial the register holds on
    the question: the verdicts are among them, and the rest count as trials without one."""
    known = _asked(_read(register)[0], question)
    names = [name(verdict.key.cell) for verdict in verdicts]
    if strangers := sorted(set(names) - known):
        raise ValueError(f"{question!r}: judged but never entered as trials: {strangers}")
    if len(set(names)) < len(names):
        twice = sorted({trial for trial in names if names.count(trial) > 1})
        raise ValueError(f"{question!r}: one trial judged twice in one set: {twice}")
    return luck.correct(verdicts, len(known) - len(names))


def _asked(entered: dict[str, set[str]], question: str) -> set[str]:
    if question not in entered:
        raise ValueError(
            f"{question!r} was never asked: the register's questions are {sorted(entered)}; "
            "a new one is opened on purpose with trials.ask"
        )
    return entered[question]


def _read(register: Path) -> tuple[dict[str, set[str]], bytes]:
    """Each question's trials, and the register as read."""
    if not register.exists():
        raise FileNotFoundError(
            f"no register of trials at {register}: a count is never begun again without a "
            "word; if this is truly the first, start one with trials.start"
        )
    text = register.read_bytes()
    lines = text[: text.rfind(b"\n") + 1].splitlines(keepends=True)
    if lines[:1] != [HEAD]:
        raise ValueError(f"{register}: not a register of trials; it is damaged or was emptied")
    book: dict[str, set[str]] = {}
    for n, line in enumerate(lines[1:], 2):
        try:
            row = json.loads(line)
        except ValueError:
            row = None
        match row:
            case {"question": str(q), "trial": str(t)} if len(row) == 2 and q in book and t.strip():
                book[q].add(t)
            case {"question": str(q)} if len(row) == 1 and q.strip() and q not in book:
                book[q] = set()
            case _:
                raise ValueError(f"{register}, line {n}: not a trial; the register is damaged")
    return book, text


def _append(register: Path, text: bytes, rows: Sequence[dict[str, str]]) -> None:
    """The rows written after the last whole line of the register as it was read."""
    with register.open("r+b") as out:
        if out.read() != text:
            raise RuntimeError(f"{register}: written by another process meanwhile; nothing added")
        out.seek(text.rfind(b"\n") + 1)
        out.truncate()
        out.write(b"".join(json.dumps(row).encode() + b"\n" for row in rows))
        out.flush()
        os.fsync(out.fileno())
