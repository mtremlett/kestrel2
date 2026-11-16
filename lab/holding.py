"""holding - EACH STRATEGY BESIDE SIMPLY HOLDING ITS MARKET (R-RUNNER-148, Q6): what the
strategy made over its window, and what the same pounds would have made left in the market,
after the same costs, and the difference.

THE STRATEGY'S FIGURE is the first rung's own (`lab/rung.py`): every judged trade's pounds
after every cost, summed, as a part of the capital. THE MARKET'S is the same capital put into
the market the desk's way: sized by the desk's sizer (`orders.size`) and bought at the open of
the window's first bar, sold at the close of its last, each leg charged by the desk's one cost
model (`orders.charges`) at its own day's rate. So holding pays the broker's commission, the
spread, the slippage and the tax of one buy and one sale, and the rule has no cost the market
lacks. The DIFFERENCE is the strategy's figure less the market's, in a part of the capital:
above nothing, the rule earned more than leaving the money alone.

Refused loudly: bars that did not make the verdict; a market with no bar in the window; a day
whose rate is missing; a capital that cannot buy one share of the market.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, localcontext

from desk import orders
from desk.lines import Line
from desk.orders import Leg, Settings
from desk.store import Bar
from desk.strategy import ARITHMETIC, Action, Decision
from lab import cell, rung
from lab.rung import Rates, Verdict


@dataclass(frozen=True)
class Beside:
    """A strategy's result and its market's over one window, both after the same costs."""

    verdict: Verdict  #: the first rung's, whose trades these are
    market: Line
    strategy: Decimal  #: the strategy's pounds after costs, as a part of the capital
    held: Decimal  #: the market's, held through the same window after the same costs
    shares: int  #: what the capital bought of the market

    @property
    def difference(self) -> Decimal:
        """The strategy's figure less the market's: above nothing, the rule beat holding."""
        return self.strategy - self.held

    def row(self) -> str:
        """The three figures as one line of a table row, in percent of the capital."""
        return (
            f"{self.strategy:+.2%} strategy, {self.held:+.2%} holding {self.market.symbol}, "
            f"{self.difference:+.2%} difference"
        )


def beside(
    verdict: Verdict,
    bars: Sequence[Bar],
    market: Line,
    held: Sequence[Bar],
    rates: Rates,
    settings: Settings,
) -> Beside:
    """The verdict's strategy set beside the market held over the cell's window: the line's
    bars that made the verdict, the market's own, oldest first, the capital the one number."""
    c = verdict.key.cell
    if cell.key(c, bars) != verdict.key:
        raise ValueError(f"{c}: these bars or this code did not make the verdict")
    window = [bar for bar in held if c.start <= bar.day <= c.end]
    if not window:
        raise ValueError(f"{market.symbol} has no bar from {c.start} to {c.end} to hold through")
    first, last = window[0], window[-1]
    with localcontext(ARITHMETIC):
        made = sum((p.gross - p.costs.total for p in verdict.trades), Decimal(0))
        decision = Decision(c.strategy, market.symbol, first.day, Action.BUY)
        order = orders.size(
            decision, market, first.open, rung.rate(market, rates, first.day), settings, {}
        )
        shares = order.quantity
        bought, buying = _leg(market, rates, shares, Leg.BUY, first.open, first)
        sold, selling = _leg(market, rates, shares, Leg.SALE, last.close, last)
        gain = sold - bought - buying - selling
        return Beside(verdict, market, made / settings.capital, gain / settings.capital, shares)


def _leg(
    market: Line, rates: Rates, shares: int, leg: Leg, price: Decimal, bar: Bar
) -> tuple[Decimal, Decimal]:
    """A leg's value and its every cost, in pounds at the day's rate."""
    at = rung.rate(market, rates, bar.day)
    return shares * price * at, orders.charges(market, leg, shares, price, at).total
