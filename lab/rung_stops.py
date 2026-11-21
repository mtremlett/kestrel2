"""rung_stops - THE STOP-RULE RUNG (research only, R-RUNNER-408): does a stop set from the line's
own range beat today's fixed one, after the broker's costs, in and out of sample?

The rivals, the judging rule and the trial count are pre-registered in `docs/DECISIONS.md`
(21 Nov 2026) before this module was run: today's stop (10% under the market's fall, three times
that on a 3x line), an ATR(20) stop at k = 2 and at k = 3 set at the fill, and a chandelier trail
(ATR(20), k = 3). Each is sized by risk: shares = the risk budget over the stop's distance, never
more than the desk's room, the budget being what today's stop risks, so today's rule is sized as
it is. The trades are the cell's own (`lab/cell.py`); the folds, the worst-fold rule and the first
rung's bar are `lab/folds.py`'s and `lab/rung.py`'s. Nothing here changes a live stop.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext

from desk import orders
from desk.lines import Line
from desk.orders import Leg
from desk.store import Bar
from desk.strategy import ARITHMETIC
from lab import cell, folds, rung
from lab.cell import Cell, Trade
from lab.folds import Fold, Walked
from lab.rung import Answer, Rates

WINDOW = 20  #: the ATR's days, and the history a trade needs before its fill to be judged
CAPITAL = Decimal(10_000)  #: pounds a trade's full room; every rule's gain is on it
#: name -> (k in ATRs, trailing); k None is today's fixed stop
RULES: dict[str, tuple[int | None, bool]] = {
    "fixed": (None, False),
    "atr2": (2, False),
    "atr3": (3, False),
    "chandelier3": (3, True),
}
TRIALS = len(RULES)  #: the count the luck correction is made for, per line and fold


@dataclass(frozen=True)
class Side:
    """One side of a fold for one rule: what the first rung's bar needs."""

    trades: int
    t: Decimal | None
    answer: Answer


def atr(bars: Sequence[Bar]) -> Decimal:
    """The mean true range of the last WINDOW bars (the bar before each one gives its gap)."""
    if len(bars) <= WINDOW:
        raise ValueError(f"{len(bars)} bars: an ATR({WINDOW}) needs {WINDOW + 1}")
    last = bars[-WINDOW - 1 :]
    ranges = (
        max(b.high, a.close) - min(b.low, a.close) for a, b in zip(last, last[1:], strict=False)
    )
    return sum(ranges, Decimal(0)) / WINDOW


def stop_at(rule: str, line: Line, fill: Decimal, spread: Decimal) -> Decimal:
    """Where the rule rests its stop for a fill; `spread` is the ATR at the signal close."""
    k = RULES[rule][0]
    stop = orders.stop_under(line, fill) if k is None else fill - k * spread
    if not 0 < stop < fill:
        raise ValueError(f"{line.symbol}: the {rule} stop {stop} is not under the fill {fill}")
    return stop


def exit_of(
    rule: str, line: Line, held: Sequence[Bar], out: Bar, spread: Decimal
) -> tuple[Leg, Decimal, date, Decimal]:
    """The sale of a trade whose buy filled on held[0]: its leg, price, day and the first stop's
    distance as a share of the fill. A bar opening at or under the stop sells at its open, one
    trading through it at the stop; a chandelier lifts its stop to its highest close less k ATRs,
    never down; otherwise the sale is the open of `out`."""
    k, trailing = RULES[rule]
    fill = held[0].open
    stop = stop_at(rule, line, fill, spread)
    share, top = (fill - stop) / fill, fill
    for bar in held[1:]:
        if bar.open <= stop or bar.low <= stop:
            return Leg.STOP, min(bar.open, stop), bar.day, share
        top = max(top, bar.close)
        if trailing and k is not None:
            stop = max(stop, top - k * spread)
    leg = Leg.STOP if out.open <= stop else Leg.SALE
    return leg, out.open, out.day, share


def gain(
    rule: str, line: Line, held: Sequence[Bar], out: Bar, spread: Decimal, rates: Rates
) -> Decimal | None:
    """One trade's return after every cost on its full room, sized by risk; None for no share."""
    leg, price, day, share = exit_of(rule, line, held, out, spread)
    risk = orders.STOP_FALL * line.leverage
    weight = min(Decimal(1), risk / share)
    fx_in, fx_out = rung.rate(line, rates, held[0].day), rung.rate(line, rates, day)
    shares = int(CAPITAL * weight / (held[0].open * fx_in))
    if shares < 1:
        return None
    buy = orders.charges(line, Leg.BUY, shares, held[0].open, fx_in).total
    sell = orders.charges(line, leg, shares, price, fx_out).total
    return (shares * (price * fx_out - held[0].open * fx_in) - buy - sell) / CAPITAL


def gains(c: Cell, trade: Trade, read: Sequence[Bar], rates: Rates) -> dict[str, Decimal] | None:
    """Every rule's gain for one trade, or None when the trade is unfinished, has too little
    history for an ATR, or any rival could not buy a share: the rivals judge the same trades."""
    at = {bar.day: n for n, bar in enumerate(read)}
    if trade.sold is None or at[trade.sold] + 1 >= len(read) or at[trade.bought] < WINDOW:
        return None
    first, last = at[trade.bought], at[trade.sold] + 1
    spread = atr(read[: first + 1])
    made = {r: gain(r, c.line, read[first + 1 : last], read[last], spread, rates) for r in RULES}
    return None if None in made.values() else {r: g for r, g in made.items() if g is not None}


def side(c: Cell, bars: Sequence[Bar], rates: Rates) -> dict[str, Side]:
    """Each rule judged on a cell's trades by the first rung's bar."""
    read = cell.shown(c, bars)
    found = [gains(c, t, read, rates) for t in cell.run(c, bars).trades]
    with localcontext(ARITHMETIC):
        out = {}
        for rule in RULES:
            mine = [g[rule] for g in found if g is not None]
            t = rung.standard_errors(mine) if len(mine) > 1 else None
            out[rule] = Side(len(mine), t, rung.decide(len(mine), t))
        return out


def judge(
    window: Cell, bars: Sequence[Bar], rates: Rates, count: int
) -> Mapping[str, Walked[Side]]:
    """Each rule's folds, in-sample and out-of-sample side by side; `.worst` is the one judged."""
    walked = [
        (side(i, bars, rates), side(o, bars, rates)) for i, o in folds.cut(window, bars, count)
    ]
    return {r: Walked(tuple(Fold(i[r], o[r]) for i, o in walked)) for r in RULES}
