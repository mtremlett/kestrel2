"""rung_ci - THE LADDER'S THIRD RUNG: is the mean gain of a rule's trades, after costs, clear
of nothing by its whole confidence interval?

The interval is the mean plus and minus T_PASS standard errors (Wasserman, All of Statistics,
6.3.2), the sample's own deviation estimating the spread. The rung answers on the whole interval,
not on a sign: wholly above nothing PASS, wholly below FAIL, holding nothing DOUBT. Under MIN_TRADES
gains it is THIN, never a fail; no gain at all is a FAULT in the test (LAD-06, LAD-09); gains
with no spread are refused loudly. Its two errors and thirty trades are the first rung's own
(`lab/rung.py`), read from there. It does not call `rung.band`: the interval is open at both
ends (strictly above or below nothing), `band` is closed at T_PASS, so folding would move a
boundary case.

THE BLOCK BOOTSTRAP (rung 11, R-RUNNER-121), folded in here (decision e): does the rule still
earn when its days are drawn again in blocks?


The first rung's standard errors take each trade for a draw of its own. A rule's days are not:
the good and the bad come in runs. This rung keeps the runs. The rule's days (each day's gain
after every cost, as a part of the pounds its trade took: `market.daily`), from its first
judged trade's buy to its last one's sale, are taken in blocks of BLOCK days in a row, a block
that runs off the end going on from the start, and DRAWS histories are made of whole blocks
drawn with replacement, as many as cover the days. THE SHARE is the part of those histories
that made nothing or lost, and the rung PASSES a share of at most RATE. It gates. The Monte
Carlo rung (`lab/montecarlo.py`) draws single trades and only measures; blocks of one day
would be that rung again.

ITS STATED RATE is RATE: of rules with no edge, about that part pass, WHILE THEIR RUNS ARE
SHORTER THAN A BLOCK. Measured over 3,000 edgeless cells of 1,500 days: 0.024 of plain noise
passed, 0.03 of noise in runs of five days, 0.06 in runs of twenty, 0.15 in runs of sixty. A
rule whose luck lasts for months is the folds' and the regimes' to catch, not this rung's.

IT READS THE TAPE (`lab/tape.py`): it is handed a cell's record, the trades a tape holds, and
simulates nothing. KEYED (`key`) by what keys the tape (the rule's code, the engine's, the
bars, the window), by this module's code and all it reaches (the cost model and the capital
with it), by the numpy that draws, and by each day's rate for a line not in pounds.

FAILING FAIRLY (LAD-06). Where the first rung found too few trades, or none, the answer is the
first rung's and nothing is drawn; days too few to fill BLOCKS blocks are THIN, never a fail.
The draw is seeded by the cell's name, so a cell judged again is drawn the same. Nothing calls
the bootstrap yet: the verdict's wiring is owed.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from desk.command import CAPITAL
from desk.orders import Settings
from desk.store import Bar
from lab import cell, market, rung, tape
from lab.cell import Record
from lab.reproduce import Reproduction
from lab.rung import MIN_TRADES, T_PASS, Answer, Rates, Rung


def judge(gains: Sequence[Decimal]) -> Answer:
    """The rung's answer on the gains of the judged trades."""
    if not gains:
        return Answer.FAULT
    if len(gains) < MIN_TRADES:
        return Answer.THIN
    _, low, high = rung.interval(gains)
    if low > 0:
        return Answer.PASS
    return Answer.FAIL if high < 0 else Answer.DOUBT


def _judged(first: rung.Verdict) -> tuple[Answer, str]:
    """The interval rung as the ladder reads it: its answer, and the interval in words."""
    answer = judge(first.gains)
    if answer in (Answer.FAULT, Answer.THIN):
        return answer, f"{len(first.gains)} gains: under {MIN_TRADES} the interval is not read"
    _, low, high = rung.interval(first.gains)
    return answer, f"the mean gain lies in {low:.4f} to {high:.4f} after costs; needs above nothing"


RUNG = Rung("ci", f"the mean gain is clear of nothing by {T_PASS} standard errors", _judged)

ME = "lab.rung_ci"  #: this module as the cell knows it
BLOCK = 20  #: days in a row to a block: a month of sessions, longer than most trades are held
BLOCKS = 30  #: the fewest blocks of days to draw from, as the first rung asks thirty trades
DRAWS = 5_000
RATE = 0.025  #: the stated rate, one in forty: 1.96 standard errors on one side


@dataclass(frozen=True)
class Redrawn:
    """The rung's answer on one cell, with the share it was given on."""

    days: int  #: the rule's days, first buy to last sale; none where the first rung answered
    share: float | None  #: the part of the redrawn histories that made nothing or lost
    answer: Answer  #: PASS or FAIL; THIN or FAULT where there was too little to draw


def share(returns: Sequence[float], seed: int) -> float:
    """The part of DRAWS histories, each of whole blocks of BLOCK of the days in a row drawn
    with replacement, that made nothing or lost."""
    days = np.asarray(returns, dtype=float)
    wrapped = np.take(days, np.arange(len(days) + BLOCK - 1), mode="wrap")
    sums = sliding_window_view(wrapped, BLOCK).sum(axis=1)  #: each block's gain, by its first day
    drawn = np.random.default_rng(seed).integers(0, len(days), (DRAWS, -(-len(days) // BLOCK)))
    return float((sums[drawn].sum(axis=1) <= 0).mean())


def redrawn(returns: Sequence[float], seed: int) -> Redrawn:
    """THE RUNG'S ONE DECISION, on a rule's days in their order: THIN under BLOCKS blocks of
    them, else PASS on a share of at most RATE and FAIL on more."""
    if len(returns) < BLOCKS * BLOCK:
        return Redrawn(len(returns), None, Answer.THIN)
    part = share(returns, seed)
    return Redrawn(len(returns), part, Answer.PASS if part <= RATE else Answer.FAIL)


def bootstrap(
    record: Record, bars: Sequence[Bar], rates: Rates, reproduced: Sequence[Reproduction] = ()
) -> Redrawn:
    """The tape's trades priced by the first rung, and their days drawn again in blocks."""
    first = rung.judge(record, bars, Settings(CAPITAL), rates, reproduced)
    if first.answer in (Answer.FAULT, Answer.THIN):
        return Redrawn(0, None, first.answer)
    c = record.key.cell
    made = market.daily(first.trades, cell.shown(c, bars), c.line, rates)
    begun, ended = min(made), max(made)  #: its first judged buy's fill, and its last sale's
    days = [float(made.get(bar.day, 0)) for bar in bars if begun <= bar.day <= ended]
    return redrawn(days, int(hashlib.sha256(str(c).encode()).hexdigest()[:16], 16))


def bootstrap_key(record: Record, rates: Rates) -> str:
    """What made the answer: the parts of the tape's key, this module's code with them, the
    numpy whose draws they are, and the rates a line not in pounds is priced at."""
    made, c = record.key, record.key.cell
    days = sorted(day for day in rates if day <= c.end and c.line.currency != "GBP")
    parts = [tape.rule_code(c.strategy), made.rung(ME).code, made.data, str(c), np.__version__]
    parts += [f"{day} {rates[day]}" for day in days]
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()
