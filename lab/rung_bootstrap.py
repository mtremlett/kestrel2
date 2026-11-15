"""rung_bootstrap - THE LADDER'S BLOCK BOOTSTRAP RUNG (R-RUNNER-121): does the rule still earn
when its days are drawn again in blocks?

The first rung's standard errors take each trade for a draw of its own. A rule's days are not:
the good and the bad come in runs. This rung keeps the runs. The rule's days (each day's gain
after every cost, as a part of the pounds its trade took: `market.daily`), from its first
judged trade's buy to its last one's sale, are taken in blocks of BLOCK days in a row, a block
that runs off the end going on from the start, and DRAWS histories as long are made of blocks
drawn with replacement. THE SHARE is the part of those histories that made nothing or lost.
The rung PASSES a share of at most RATE: of rules with no edge about RATE pass, its stated
rate. It gates. The Monte Carlo rung (`lab/montecarlo.py`) draws single trades and only
measures; blocks of one day would be that rung again, and pass noise that comes in runs.

IT READS THE TAPE (`lab/tape.py`): it is handed a cell's record, the trades a tape holds, and
simulates nothing. KEYED (`key`) by what keys the tape (the rule's code, the engine's, the
bars, the window), by this module's code and all it reaches (the cost model and the capital
with it), and by each day's rate for a line not in pounds: change any and it is drawn again.

FAILING FAIRLY (LAD-06). Where the first rung found too few trades, or none, the answer is the
first rung's and nothing is drawn; days too few to fill BLOCKS blocks are THIN, never a fail.
The draw is seeded by the cell's name, so a cell judged again is drawn the same. Nothing calls
this rung yet: the verdict's wiring is owed.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from desk.command import CAPITAL
from desk.orders import Settings
from desk.store import Bar
from lab import cell, market, rung, tape
from lab.cell import Record
from lab.reproduce import Reproduction
from lab.rung import Answer, Rates

ME = "lab.rung_bootstrap"  #: this module as the cell knows it
BLOCK = 20  #: days in a row to a block: a month of sessions, longer than most trades are held
BLOCKS = 30  #: the fewest blocks of days to draw from, as the first rung asks thirty trades
DRAWS = 5_000
RATE = 0.025  #: the stated rate, one in forty: the first rung's two standard errors, one side


@dataclass(frozen=True)
class Redrawn:
    """The rung's answer on one cell, with the share it was given on."""

    days: int  #: the rule's days, first buy to last sale; none where the first rung answered
    share: float | None  #: the part of the redrawn histories that made nothing or lost
    answer: Answer  #: PASS or FAIL; THIN or FAULT where there was too little to draw


def share(returns: Sequence[float], seed: int, block: int = BLOCK) -> float:
    """The part of DRAWS histories, each of whole blocks of `block` of the days in a row drawn
    with replacement, that made nothing or lost."""
    days = np.asarray(returns, dtype=float)
    wrapped = np.take(days, np.arange(len(days) + block - 1), mode="wrap")
    sums = sliding_window_view(wrapped, block).sum(axis=1)  #: each block's gain, by its first day
    drawn = np.random.default_rng(seed).integers(0, len(days), (DRAWS, -(-len(days) // block)))
    return float((sums[drawn].sum(axis=1) <= 0).mean())


def judge(
    record: Record, bars: Sequence[Bar], rates: Rates, reproduced: Sequence[Reproduction] = ()
) -> Redrawn:
    """The tape's trades priced by the first rung, and their days drawn again in blocks."""
    first = rung.judge(record, bars, Settings(CAPITAL), rates, reproduced)
    if first.answer in (Answer.FAULT, Answer.THIN):
        return Redrawn(0, None, first.answer)
    c = record.key.cell
    made = market.daily(first.trades, cell.shown(c, bars), c.line, rates)
    begun, ended = min(made), max(made)  #: its first judged buy's fill, and its last sale's
    held = [bar.day for bar in bars if begun <= bar.day <= ended]
    if len(held) < BLOCKS * BLOCK:
        return Redrawn(len(held), None, Answer.THIN)
    seed = int(hashlib.sha256(str(c).encode()).hexdigest()[:16], 16)
    part = share([float(made.get(day, 0)) for day in held], seed)
    return Redrawn(len(held), part, Answer.PASS if part <= RATE else Answer.FAIL)


def key(record: Record, rates: Rates) -> str:
    """What made the answer: the parts of the tape's key, this module's code with them, and
    the rates a line not in pounds is priced at."""
    made, c = record.key, record.key.cell
    days = sorted(day for day in rates if day <= c.end and c.line.currency != "GBP")
    parts = [tape.rule_code(c.strategy), made.rung(ME).code, made.data, str(c)]
    parts += [f"{day} {rates[day]}" for day in days]
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()
