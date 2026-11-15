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
a trial out. A cell's name is its rule and the first twelve letters of the hash of the rule's code
(its class in `desk/strategy.py` and all it names there), its line and venue and its window,
so the same cell run again (a restart, mended bars) is the same trial, and the same rule on
another line or window is another. A rule that is changed is new trials, never a free second
look: the hash is in the name. A fold is no trial of its own: nothing is picked from it.
A candidate that is no cell is entered
under any name that tells it apart. A trial asked of two questions counts in each.

Nothing begins a count without a word. A register that is not there, or is empty, is
refused: a new one is started on purpose, once, with `start`. A question is opened on
purpose, once, with `ask`, and a trial or a verdict under any other wording is refused, so
a question spelled anew cannot begin again at nothing.

The register holds one JSON line per question and per trial, appended and forced to disk
before `enter` returns. A line a stop cut short is an entry that never finished: it is cut
off, and its batch never ran. A whole line that is not a question or a trial is damage, and
is refused. One process at a time writes, which is the caller's to keep; a stale read is caught.

ONE CLUSTERED SET (L14; Lopez de Prado and Lewis, "Detection of false investment strategies
using unsupervised learning methods", 2019). Fifty copies of one strategy are one look at the
data, and fifty strangers are fifty: the deflated Sharpe's bar (`lab/deflated.py`) is set by
the looks, not the names. `clusters` reads the looks from how the trials' daily returns move
together. Two trials are one look where their returns correlate by LINK or more, and A CLUSTER
IS TRIALS ALIKE IN EVERY PAIR: the two groups whose least-alike pair is most alike are joined
while that pair reaches LINK, so no chain of likenesses joins two strangers and the count errs
towards more looks, on purpose. A rule run the other way round is another look: its Sharpe is
as likely to be the lucky best. The paper picks the number of clusters by a score blind to
how alike the trials are: tried on fifty strangers it most often calls them two clusters, and
it cannot answer on copies; the level fixed here answers both. (`lab/bets.py` clusters a
book's lines the other way, by a chain and either sign, towards fewer bets: there the danger
is a book called more spread than it is; here, a set called fewer looks than it took.) As in
the paper, a cluster's returns are its trials' weighed by one over each one's variance, THE
EFFECTIVE NUMBER OF TRIALS is the clusters, and THE SPREAD is the variance of the clusters'
Sharpes, restated from a day to the picked trial's own trades (the paper's yearly variance
over its trades a year).

THE PICK INSIDE A CLUSTER IS LUCK TOO. The paper judges a cluster's own returns; the desk
judges the one trial picked, and the best of fifty near-copies stands above their cluster by
luck. So A TRIAL IS JUDGED NO BETTER THAN ITS CLUSTER: whatever the Sharpe it is judged on, a
trade, stands above its cluster's restated to a trade (`Clustered.above`) is added to its bar,
which is the paper's judging of the cluster, whatever the cluster is made of and however its
trials book their trades. Nothing is added for a trial alone or one no better than its cluster.

A trial that left no returns (a cell that failed, a rule that never traded) cannot be set
beside the others: it is counted aloud as a look of its own, as on the luck rung, and
`clustered` takes that count from the register. THE RETURNS TO HAND IN are each trial's on
every day of the one window all were judged over, nothing on a day it held nothing: fewer
days than the window understate the spread among trials whose true Sharpes differ. A Sharpe
a day is restated to a trade as the yearly Sharpe is (`lab/deflated.py`): one day's return
taken to tell nothing of the next.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import os
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from lab import luck, rulebook
from lab.cell import Cell
from lab.luck import Corrected
from lab.rung import Verdict

HEAD = b'{"register": "trials"}\n'  #: a register's first line: an empty file is not one
#: Fixed before any result. Two trials whose daily returns correlate by LINK or more are one
#: look: in the paper's distance, the root of half of one less the correlation, they stand
#: no nearer to strangers than to copies. FEWEST days are asked so that no two strangers reach
#: LINK by chance, however many pairs a set holds.
LINK, FEWEST = 0.75, 60


def name(cell: Cell) -> str:
    """The cell as a trial: its rule, its line on its venue, its window. The register's own
    wording, kept apart from how a cell is printed, which may change."""
    line, window = cell.line, f"{cell.start.isoformat()} to {cell.end.isoformat()}"
    return f"{cell.strategy} {rule_hash(cell.strategy)} on {line.symbol} on {line.venue}, {window}"


@cache
def rule_hash(rule: str) -> str:
    """The first twelve letters of the hash of the rule's code as this process loaded it."""
    made = rulebook.rule(rule)
    return code_hash(inspect.getsource(sys.modules[made.__module__]), made.__name__)


def code_hash(source: str, name: str) -> str:
    """The hash of what the class `name` in this module's text is made of: its syntax tree
    and that of every class, function and constant of the module it names, however deep, so
    a change in the logic changes it and a comment, a blank line or an unrelated edit does not."""
    defined: dict[str, ast.stmt] = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.ClassDef | ast.FunctionDef):
            defined[node.name] = node
        elif isinstance(node, ast.Assign | ast.AnnAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            defined |= {t.id: node for t in targets if isinstance(t, ast.Name)}
    if name not in defined:
        raise ValueError(f"no class called {name!r} in the module's code")
    reached, waiting = set(), [name]
    while waiting:
        if (here := waiting.pop()) not in reached:
            reached.add(here)
            waiting += [
                n.id for n in ast.walk(defined[here]) if isinstance(n, ast.Name) and n.id in defined
            ]
    text = "\n".join(ast.dump(defined[n]) for n in sorted(reached))
    return hashlib.sha256(text.encode()).hexdigest()[:12]


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
    names = [name(verdict.key.cell) for verdict in verdicts]
    rest = _rest(register, question, names)
    if len(set(names)) < len(names):
        twice = sorted({trial for trial in names if names.count(trial) > 1})
        raise ValueError(f"{question!r}: one trial judged twice in one set: {twice}")
    return luck.correct(verdicts, rest)


@dataclass(frozen=True)
class Clustered:
    """One set of trials as the looks it took: what the deflated Sharpe's bar is set by."""

    clusters: tuple[tuple[str, ...], ...]  #: every trial with returns, by name, in its cluster
    sharpes: tuple[float, ...]  #: each cluster's Sharpe a day, cluster for cluster
    unjudged: int  #: the trials that left no returns, each a look of its own
    days: int  #: the days the returns were given on

    @property
    def trials(self) -> int:
        """The effective number of trials: the clusters, and every trial without returns."""
        return len(self.clusters) + self.unjudged

    @property
    def held(self) -> int:
        """Every trial of the set, with returns or without."""
        return sum(map(len, self.clusters)) + self.unjudged

    def spread(self, trades: int) -> float:
        """The variance of the looks' Sharpes, for a trial of so many trades on the set's
        days: the variance a day times the days a trade. Nothing for one look alone."""
        if self.trials == 1:
            return 0.0
        measured = float(np.var(self.sharpes, ddof=1)) if len(self.sharpes) > 1 else 0.0
        if not measured > 0:
            raise ValueError(
                f"{self.trials} trials, {len(self.clusters)} of them clusters with returns: "
                "no spread measured among them, so nothing to deflate by"
            )
        return measured * self.days / trades

    def above(self, cell: Cell, sharpe: float, trades: int) -> float:
        """How far the Sharpe the cell's trial is judged on, a trade over so many trades,
        stands above its cluster's restated to a trade: the luck of the pick inside the
        cluster. Nothing where it is no higher, and nothing for a trial alone in its cluster."""
        trial = name(cell)
        for members, cluster in zip(self.clusters, self.sharpes, strict=True):
            if trial in members:
                stand = sharpe - cluster * float(np.sqrt(self.days / trades))
                return max(0.0, stand) if len(members) > 1 else 0.0
        raise ValueError(f"{trial}: not a trial this set was clustered from")


def clusters(returns: Mapping[str, Sequence[float]], unjudged: int) -> Clustered:
    """The set as the looks it took: each trial's daily returns by its name, on the same days
    for every trial, and how many trials more left none, which count as much as any."""
    names = sorted(returns)
    lengths = {len(returns[trial]) for trial in names}
    if not names or unjudged < 0 or len(lengths) != 1 or min(lengths) < FEWEST:
        raise ValueError(
            f"{len(names)} trials with returns on {sorted(lengths)} days and {unjudged} with "
            f"none: a set is clustered on the same days for every trial, {FEWEST} or more"
        )
    days = np.array([returns[trial] for trial in names], dtype=np.float64)
    moved = [bool(np.isfinite(row).all() and row.max() > row.min()) for row in days]
    if still := [trial for trial, it in zip(names, moved, strict=True) if not it]:
        raise ValueError(
            f"{still}: returns that never moved, or are no number: nothing to set beside "
            "the others; a trial that left no returns is counted among the unjudged"
        )
    own = days.var(axis=1, ddof=1)
    groups = _groups(np.atleast_2d(np.corrcoef(days)))
    weighed = [(days[group] / own[group, None]).sum(axis=0) for group in groups]
    return Clustered(
        tuple(tuple(names[n] for n in group) for group in groups),
        tuple(float(made.mean() / made.std(ddof=1)) for made in weighed),
        unjudged,
        days.shape[1],
    )


def clustered(register: Path, question: str, returns: Mapping[str, Sequence[float]]) -> Clustered:
    """The question's trials as one clustered set: those with returns as their clusters, and
    every other trial the register holds a look of its own."""
    return clusters(returns, _rest(register, question, returns))


def _groups(alike: NDArray[np.float64]) -> list[list[int]]:
    """The trials, by their place, in groups alike by LINK or more in every pair."""
    least = alike.copy()  #: group against group, the correlation of their least-alike pair
    np.fill_diagonal(least, -np.inf)
    groups = {n: [n] for n in range(len(least))}
    while least[(pair := divmod(int(least.argmax()), len(least)))] >= LINK:
        a, b = sorted(pair)
        groups[a] = sorted(groups[a] + groups.pop(b))
        least[a] = least[:, a] = np.minimum(least[a], least[b])
        least[b] = least[:, b] = -np.inf
    return list(groups.values())


def _rest(register: Path, question: str, names: Iterable[str]) -> int:
    """How many of the question's trials are not among these, each of which must be one."""
    known, judged = _asked(_read(register)[0], question), set(names)
    if strangers := sorted(judged - known):
        raise ValueError(f"{question!r}: judged but never entered as trials: {strangers}")
    return len(known) - len(judged)


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
