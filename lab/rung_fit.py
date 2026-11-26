"""rung_fit - FIT WITH THE BOOK: does the rule bring new return, or only more of a rule the
desk already trades on paper?

The rules running on paper are the desk's five (`strategy.STRATEGIES`) and the zoo's daily rules
(`intraday.ZOO_DAILY`), less any of the cell's own class. Each is run on the cell's own bars and
its days set beside the cell's. A day's return is the line's close-to-close move when the rule
held after the close before, and nothing when it did not: the same for both, so the costs, a
level and not a co-movement, do not enter. The cell's days are its judged trades' (the first
rung's); a running rule that never held over the cell's window says nothing and is passed over.

THE BARS (`docs/DECISIONS.md`, 26 Nov, before any EPON result): Pearson's correlation with the
closest running rule above HALF_SHARED (0.70, about half its day-to-day swings already in the
book) is WEAK (`Answer.DOUBT`): it adds risk without new return; above the desk's own
correlation gate (`Settings.correlation`, 0.90, one home) it FAILS: the desk would refuse to
hold it beside the other. Across lines is the desk's gate's and `lab/bets.py`'s, not this rung's.

IT ONLY LOWERS A PASS (as the costs rung does): a cell the first rung did not pass keeps its
answer, FAIL, THIN or FAULT, and no running rule is run for it (LAD-06). A running rule's days
on a line's bars are run once a process, by the rule and the bars' own hash.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import localcontext

import numpy as np

from desk import intraday
from desk.command import CAPITAL
from desk.orders import Settings
from desk.store import Bar
from desk.strategy import ARITHMETIC, STRATEGIES, Action, Rule, _run
from lab import cell, rulebook, rung
from lab.rung import Answer, Rates, Rung

#: The rules trading on paper, by name: the desk's five and the zoo's daily rules.
RUNNING: Mapping[str, type[Rule]] = {**STRATEGIES, **intraday.ZOO_DAILY}
HALF_SHARED = 0.70  #: above it, about half of the rule's daily swings are already in the book
TOO_CLOSE = float(Settings(CAPITAL).correlation)  #: the desk's own correlation gate, 0.90
_HELD: dict[tuple[str, str], tuple[bool, ...]] = {}  #: a running rule's days, by its name, bars


@dataclass(frozen=True)
class Fit:
    """The fit rung's answer on one cell, with the closest running rule behind it."""

    closest: str | None  #: the running rule that moves most with it; None: none read
    correlation: float | None
    answer: Answer


def held(name: str, rule: type[Rule], bars: Sequence[Bar]) -> tuple[bool, ...]:
    """Whether the rule is in the market after each bar, by the desk's own engine."""
    holding, out = False, []
    with localcontext(ARITHMETIC):
        for decision in _run(name, rule(), "fit", bars):
            holding = {Action.BUY: True, Action.SELL: False}.get(decision.action, holding)
            out.append(holding)
    return tuple(out)


def days(holding: Sequence[bool], bars: Sequence[Bar], first: int) -> np.ndarray:
    """Each day's return from bar `first` on: the close's move when held after the one before."""
    closes = np.array([float(bar.close) for bar in bars])
    moves = closes[first:] / closes[first - 1 : -1] - 1
    return moves * np.array(holding[first - 1 : -1], dtype=float)


def judge(first: rung.Verdict, bars: Sequence[Bar]) -> Fit:
    """The first rung's PASS, lowered where its days move with a running rule's past a bar."""
    if first.answer is not Answer.PASS:
        return Fit(None, None, first.answer)
    c = first.key.cell
    read = cell.shown(c, bars)
    if cell.key(c, bars).data != first.key.data:
        raise ValueError(f"{c}: these bars did not make the first rung's verdict")
    own = STRATEGIES.get(c.strategy) or rulebook.rule(c.strategy)
    trades = [p.trade for p in first.trades]
    mine = [any(t.bought <= bar.day < t.sold for t in trades if t.sold) for bar in read]
    start = max(1, next(n for n, bar in enumerate(read) if bar.day >= c.start))
    ours, found = days(mine, read, start), []
    for name, rule in RUNNING.items():
        if rule is own:
            continue
        if (name, first.key.data) not in _HELD:
            _HELD[name, first.key.data] = held(name, rule, read)
        theirs = days(_HELD[name, first.key.data], read, start)
        if theirs.std() > 0:
            found.append((float(np.corrcoef(ours, theirs)[0, 1]), name))
    if not found:
        return Fit(None, None, Answer.PASS)
    r, name = max(found)
    answer = Answer.FAIL if r > TOO_CLOSE else Answer.DOUBT if r > HALF_SHARED else Answer.PASS
    return Fit(name, r, answer)


def _judged(first: rung.Verdict, bars: Sequence[Bar], _rates: Rates) -> tuple[Answer, str]:
    """The fit rung as the ladder reads it: its answer, and the closest running rule in words."""
    fit = judge(first, bars)
    if fit.answer is not Answer.PASS and fit.correlation is None:
        return fit.answer, "the first rung did not pass it, so no running rule is set beside it"
    if fit.correlation is None:
        return fit.answer, "no rule running on paper held this line over its window"
    grade = {Answer.FAIL: "FAIL", Answer.DOUBT: "WEAK"}.get(fit.answer, "new")
    return (
        fit.answer,
        f"{grade}: moves {fit.correlation:.2f} with {fit.closest} on paper; WEAK above"
        f" {HALF_SHARED}, FAIL above {TOO_CLOSE}",
    )


def _unread(first: rung.Verdict) -> tuple[Answer, str]:
    """The rung without the bars: no running rule can be run, so only a kept answer is given."""
    if first.answer is Answer.PASS:
        raise ValueError(f"{first.key.cell}: the fit rung runs the paper rules on the bars")
    return first.answer, "the first rung did not pass it, so no running rule is set beside it"


RUNG = Rung("fit", f"moves with no rule on paper past {HALF_SHARED}", _unread, _judged)
