"""rung_placebo - THE LADDER'S BLOCK PLACEBO (rung 9): did the rule time its line, or would
it have made as much of the same line with its fortnights in any order?

The rule's own trades are read from its TAPE (`lab/tape.py`). Each day of the cell's window is
kept whole, its prices as moves from the close before and its volume; the days are cut into
blocks of BLOCK, the odd oldest ones left where they are with every bar before the window, and
the blocks are put in a random order PLACEBOS times. The rule is run on each history that
makes, through `cell.run`: under the ladder each is a tape too, simulated once. Every placebo
is the same line: its warm-up as it was, all the window's rise and what each fortnight held
(a run, a cluster of wild days), and no order beyond.

WHAT IS RANKED is what the trades made over the window's own rise for the days they held, as a
log, open after the buy to open after the sale: riding a rising line longer earns nothing here.
It is before costs: it ranks orders of one line and reports no profit (costs are the first
rung's). The share is the placebos that made as much as the rule, itself among them, over
PLACEBOS + 1; SHARE or under passes, and it stops once a pass is out of reach (the share is
then a floor). Of noise at most SHARE passes, whatever the rule: each order was as likely.

FAILING FAIRLY: a tape with no trade, or under FEWEST blocks, has no share: not judged, never
failed. WHAT IT CANNOT SEE: an edge that lives inside one block is in every placebo, and reads
as no timing; and a window that changes character (flat, then rising) is no noise: a rule in
for the rise passes, which says the order mattered, not that it will again. KEYED by the
tape's key and this module's code (`Key.rung`); the draw is seeded by the bars and the cell,
never the code, so a tape judged again meets the same placebos.
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
FEWEST = 6  #: blocks: fewer have under 720 orders, and the line's own is drawn too often


@dataclass(frozen=True)
class Placebo:
    """What its placebos say of one tape."""

    key: Key  #: the tape's, and this module's code
    blocks: int  #: whole blocks of days put in a new order
    run: int  #: placebos run: none where there is nothing to judge, not all once it cannot pass
    made: Decimal | None  #: what the rule's own trades made over the window's rise, as a log
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
    kept = max(1, sum(bar.day < c.start for bar in read))  #: the bars before the window stay
    blocks = (len(read) - kept) // BLOCK
    if blocks < FEWEST or not tape.trades:
        return Placebo(key, blocks, 0, None, None)
    ride = (read[-1].close / read[kept - 1].close).ln() / (len(read) - kept)  #: its rise, a day
    own = _made(tape, read, ride)
    quoted = [price for b in read for price in (b.open, b.high, b.low, b.close)]
    places = max(0, *(-int(price.as_tuple().exponent) for price in quoted))  #: the line's own
    prices = np.array(quoted, dtype=np.float64).reshape(-1, 4)
    moves = prices[1:] / prices[:-1, 3:]  #: each day's four prices over the close before
    stay = len(moves) - blocks * BLOCK  #: the days that keep their place
    rng = np.random.default_rng([int(tape.key.data, 16), *str(c).encode()])
    as_good, run = 1, 0  #: the rule itself
    while run < PLACEBOS and as_good <= SHARE * (PLACEBOS + 1):
        order = (rng.permutation(blocks)[:, None] * BLOCK + np.arange(BLOCK)).ravel()
        made = _history(read, moves, np.r_[:stay, stay + order], places)
        as_good += _made(cell.run(c, made), made, ride) >= own
        run += 1
    return Placebo(key, blocks, run, own, Decimal(as_good) / (PLACEBOS + 1))


def _made(tape: Record, read: Sequence[Bar], ride: Decimal) -> Decimal:
    """What the tape's trades made over the window's rise for the days they held, as a log:
    in at the open after each buy, out at the open after its sale or at the last open shown."""
    at = {bar.day: n for n, bar in enumerate(read)}
    total, last = Decimal(0), len(read) - 1
    for trade in tape.trades:
        bought = min(at[trade.bought] + 1, last)
        sold = last if trade.sold is None else min(at[trade.sold] + 1, last)
        total += (read[sold].open / read[bought].open).ln() - (sold - bought) * ride
    return total


def _history(
    read: Sequence[Bar], moves: NDArray[np.float64], order: NDArray[np.int_], places: int
) -> list[Bar]:
    """The first bar, then the dates in their place under the days in their new order, each
    price rounded as the line's own are."""
    before = float(read[0].close) * np.cumprod(np.r_[1.0, moves[order[:-1], 3]])
    rows = (before[:, None] * moves[order]).tolist()  #: the close before each day, times its moves
    made = [[Decimal(f"{price:.{places}f}") for price in row] for row in rows]
    return [read[0]] + [
        Bar(bar.day, o, h, low, c, read[took + 1].volume)
        for bar, (o, h, low, c), took in zip(read[1:], made, order.tolist(), strict=True)
    ]
