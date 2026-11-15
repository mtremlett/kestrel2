"""rung_placebo - THE LADDER'S BLOCK PLACEBO (rung 9): did the rule time its line, or would
it have made as much of the same line with its fortnights in any order?

The rule's own trades are read from its TAPE (`lab/tape.py`). Each day after the first is kept
whole, its prices as moves from the close before and its volume; the days are cut into blocks
of BLOCK, the odd oldest ones left where they are, and the blocks are put in a random order
PLACEBOS times. The rule is run on each history that makes, through `cell.run`, so under the
ladder each is a tape too and a rung changed runs none again. Every placebo is the same line:
all its rise and what each fortnight held (a run, a cluster of wild days), and no order beyond.

WHAT IS RANKED is what the trades made over the line's own rise for the days they held, as a
log, open after the buy to open after the sale: riding a rising line longer earns nothing here.
It is before costs: it ranks orders of one line and reports no profit (costs are the first
rung's). The share is the placebos that made as much as the rule, itself among them, over
PLACEBOS + 1; SHARE or under passes, and it stops once a pass is out of reach. Of noise at
most SHARE passes, whatever the rule: each order was as likely as the real one.

FAILING FAIRLY: a tape with no trade, or under FEWEST blocks, is not judged and never failed.
WHAT IT CANNOT SEE: an edge that lives inside one block is in every placebo, and is read here
as no timing. KEYED by the tape's key and this module's code (`Key.rung`); the draw is seeded
by the bars and the cell, never the code, so a tape judged again meets the same placebos.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

import numpy as np
from numpy.typing import NDArray

from desk.store import Bar
from lab import cell
from lab.cell import Key, Record

ME = "lab.rung_placebo"  #: this module as the cell knows it
BLOCK = 10  #: days to a block: a trading fortnight
PLACEBOS = 19  #: the fewest that can pass at SHARE: the rule must beat every one
SHARE = Decimal("0.05")  #: at most this share of the placebos, itself among them, does as well
FEWEST = 4  #: blocks: four have 24 orders, and fewer could never be as rare as SHARE
PLACES = 4  #: decimal places a made price is rounded to: the fast engine refuses longer ones


@dataclass(frozen=True)
class Placebo:
    """What its placebos say of one tape."""

    key: Key  #: the tape's, and this module's code
    blocks: int  #: whole blocks of days put in a new order
    run: int  #: placebos run: none where there is nothing to judge, not all once it cannot pass
    share: Decimal | None  #: those run that did as well, itself among them, over PLACEBOS + 1

    @property
    def passed(self) -> bool:
        """THE DECISION: at most SHARE of the placebos, itself among them, did as well."""
        return self.share is not None and self.share <= SHARE


def judge(tape: Record, bars: Sequence[Bar]) -> Placebo:
    """The tape among its placebos, on the bars that made it."""
    c, key = tape.key.cell, tape.key.rung(ME)
    if cell.key(c, bars) != tape.key:
        raise ValueError(f"{c}: these bars or this code did not make the tape")
    read = cell.shown(c, bars)
    blocks = (len(read) - 1) // BLOCK
    if blocks < FEWEST or not tape.trades:
        return Placebo(key, blocks, 0, None)
    ride = (read[-1].close / read[0].close).ln() / (len(read) - 1)  #: the line's rise, a day
    own = _made(tape, read, ride)
    prices = np.array([[float(p) for p in (b.open, b.high, b.low, b.close)] for b in read])
    moves = prices[1:] / prices[:-1, 3:]  #: each day's four prices over the close before
    odd = len(moves) - blocks * BLOCK
    rng = np.random.default_rng([int(tape.key.data, 16), *str(c).encode()])
    as_good, run = 1, 0  #: the rule itself
    while run < PLACEBOS and as_good <= SHARE * (PLACEBOS + 1):
        order = (rng.permutation(blocks)[:, None] * BLOCK + np.arange(BLOCK)).ravel()
        made = _history(read, moves, np.r_[:odd, odd + order])
        as_good += _made(cell.run(c, made), made, ride) >= own
        run += 1
    return Placebo(key, blocks, run, Decimal(as_good) / (PLACEBOS + 1))


def _made(tape: Record, read: Sequence[Bar], ride: Decimal) -> Decimal:
    """What the tape's trades made over the line's own rise for the days they held, as a log:
    in at the open after each buy, out at the open after its sale or at the last open shown."""
    at = {bar.day: n for n, bar in enumerate(read)}
    total, last = Decimal(0), len(read) - 1
    for trade in tape.trades:
        bought = min(at[trade.bought] + 1, last)
        sold = last if trade.sold is None else min(at[trade.sold] + 1, last)
        total += (read[sold].open / read[bought].open).ln() - (sold - bought) * ride
    return total


def _history(read: Sequence[Bar], moves: NDArray[np.float64], order: NDArray[np.int_]) -> list[Bar]:
    """The first bar, then the dates in their place under the days in their new order."""
    before = float(read[0].close) * np.cumprod(np.r_[1.0, moves[order[:-1], 3]])
    rows = (before[:, None] * moves[order]).tolist()  #: the close before each day, times its moves
    made = [[Decimal(f"{price:.{PLACES}f}") for price in row] for row in rows]
    return [read[0]] + [
        Bar(bar.day, o, h, low, c, read[took + 1].volume)
        for bar, (o, h, low, c), took in zip(read[1:], made, order.tolist(), strict=True)
    ]
