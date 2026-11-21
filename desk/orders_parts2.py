"""orders_parts2 - the pre-trade gate's helper checks (loss limits, underlying cap, correlation),
the daily returns the correlation gate reads, and the refusal they raise; desk.orders gives
them to its callers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import TYPE_CHECKING

from desk.lines import Line
from desk.risk import Standing, correlated_with, loss_limit, underlying_limit
from desk.store import Bar

if TYPE_CHECKING:
    from desk.orders import Order, Settings


class Refused(Exception):
    """The desk refused an order before sending it, saying why: the pre-trade gate, or the
    send path while the book is not the broker's."""


def _within_limits(
    order: Order, settings: Settings, held: Mapping[str, int], standing: Standing
) -> None:
    """Refuses a buy past a loss limit, or a new line past the day's count, naming the limit."""
    reached = loss_limit(standing, settings.capital, settings.day_loss, settings.week_loss)
    if reached is not None:
        raise Refused(f"{order.order_id}: no buy past {reached}")
    if order.line.symbol not in held and standing.new_lines >= settings.new_lines:
        raise Refused(
            f"{order.order_id}: {standing.new_lines} new lines entered today, the limit is "
            f"{settings.new_lines} a day"
        )


def _within_underlying(order: Order, settings: Settings, exposure: Mapping[str, Decimal]) -> None:
    """Refuses a buy that takes its underlying market past the cap, counted at its leverage."""
    line = order.line
    added = order.quantity * order.price * order.fx * line.leverage
    key = line.underlying or line.symbol
    over = underlying_limit(exposure, key, added, settings.capital, settings.underlying)
    if over is not None:
        raise Refused(f"{order.order_id}: {over}")


def _apart(
    order: Order,
    settings: Settings,
    held: Mapping[str, int],
    moves: Mapping[str, tuple[float, ...]],
) -> None:
    """Refuses a buy that moves with a line already held above the correlation cap."""
    symbol = order.line.symbol
    if symbol not in moves:
        return
    others = {s: moves[s] for s in held if s != symbol and s in moves}
    together = correlated_with(moves[symbol], others, float(settings.correlation))
    if together is not None:
        raise Refused(f"{order.order_id}: {symbol} is {together}")


MOVES_DAYS, MOVES_FROM = 60, 20  #: the daily returns kept for the correlation gate, and the fewest


def daily_moves(
    held: set[str], archive: Mapping[Line, Sequence[Bar]], symbol: str
) -> dict[str, tuple[float, ...]]:
    """THE DAILY RETURNS OF A LINE AND OF THE LINES HELD (risk.correlated_with), by symbol, over
    the last sessions all of them have a bar for. All are left out when the days they share are
    under MOVES_FROM (nothing to judge by); a line whose price never moved is left out alone."""
    closes = {
        line.symbol: {bar.day: bar.close for bar in bars}
        for line, bars in archive.items()
        if line.symbol == symbol or line.symbol in held
    }
    if symbol not in closes:
        return {}
    shared = sorted(set.intersection(*(set(c) for c in closes.values())))[-MOVES_DAYS - 1 :]
    if len(shared) <= MOVES_FROM:
        return {}
    rows = {
        s: tuple(float(c[b] / c[a] - 1) for a, b in zip(shared, shared[1:], strict=False))
        for s, c in closes.items()
    }
    return {s: r for s, r in rows.items() if len(set(r)) > 1}
