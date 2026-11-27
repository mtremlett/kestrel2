"""rung_late - ONE BAR LATE (E13): would the rule still earn had every trade been made a bar later?

An edge that is real lasts longer than the one open after its signal: a fill a day late (a missed
order, a slow broker, the desk restarting) costs some of it, never all. One paid only on the next
open is a fill the desk cannot rely on, and often a bar-timing fault in the test itself.

Each trade the first rung judged (`lab/rung.py`) is made one bar later: decided on the bar after
the one it was decided on, and its sale decided a bar after its own, so it is bought and sold at
the opens after those. A trade whose late sale falls past the bars the rule was shown is not
judged, as the first rung judges none still held. The late trades are priced by the first rung's
own pricing (`rung.judge`: the desk's sizing, its pretend broker's fills and stop, the broker's
costs, each leg at its own day's rate) and judged by the first rung's own rule (`rung.decide`:
MIN_TRADES judged trades whose mean gain after costs is T_PASS standard errors above nothing).
Its answer is that rule's: PASS, FAIL, THIN or FAULT. No new bar is set here.

IT ONLY LOWERS A PASS (as the costs rung does): a cell the first rung did not pass keeps its
answer, and nothing is priced again for it (LAD-06). The reason names both, on time and a bar
late: the trades, their mean gain after costs and its standard errors.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from desk.command import CAPITAL
from desk.orders import Settings
from desk.store import Bar
from lab import cell, rung
from lab.cell import Record, Trade
from lab.rung import Answer, Rates, Rung, Verdict

KEPT = "the first rung did not pass it, so nothing is priced a bar late"


def late(first: Verdict, bars: Sequence[Bar], rates: Rates) -> Verdict:
    """The first rung's verdict on its judged trades, each made one bar later."""
    c = first.key.cell
    read = cell.shown(c, bars)
    if cell.key(c, bars).data != first.key.data:
        raise ValueError(f"{c}: these bars did not make the first rung's verdict")
    at = {bar.day: n for n, bar in enumerate(read)}
    later = []
    for priced in first.trades:
        bought, sold = at[priced.trade.bought] + 1, priced.trade.sold
        if sold is not None and at[sold] + 1 < len(read):
            later.append(Trade(read[bought].day, read[at[sold] + 1].day))
    inside = sum(1 for bar in read if bar.day >= c.start)
    record = Record(cell.key(c, bars), inside, tuple(later))
    return rung.judge(record, bars, Settings(CAPITAL), rates, first.reproduced)


def _judged(first: Verdict, bars: Sequence[Bar], rates: Rates) -> tuple[Answer, str]:
    """The rung as the ladder reads it: the first rung's rule on the late trades."""
    if first.answer is not Answer.PASS:
        return first.answer, KEPT
    made = late(first, bars, rates)
    return made.answer, (
        f"a bar late, {_side(made)}; on time, {_side(first)};"
        f" {rung.T_PASS} standard errors asked on {rung.MIN_TRADES} or more trades"
    )


def _side(verdict: Verdict) -> str:
    """A verdict's trades, their mean gain after costs and its standard errors above nothing."""
    n = len(verdict.trades)
    mean = sum((p.gain for p in verdict.trades), Decimal(0)) / n if n else Decimal(0)
    t = "none" if verdict.t is None else f"{verdict.t:.2f}"
    return f"{n} trades, mean gain {mean:.2%} after costs, {t} standard errors"


def _unread(first: Verdict) -> tuple[Answer, str]:
    """The rung without the bars: it cannot make a trade late, so only a kept answer is given."""
    if first.answer is Answer.PASS:
        raise ValueError(f"{first.key.cell}: the one-bar-late rung prices on the bars")
    return first.answer, KEPT


RUNG = Rung("late", f"{rung.T_PASS} standard errors a bar late", _unread, _judged)
