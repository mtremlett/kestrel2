"""order_reads - WHAT THE GATE READS OF THE ARCHIVE'S BARS: the daily returns of a line and of the
lines held (the correlation gate), and the pounds a line traded (the liquidity gate)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal

from desk.lines import Line
from desk.store import Bar

TRADED_DAYS = 20  #: the sessions the liquidity gate (orders.TRADED_SHARE) counts
MOVES_DAYS, MOVES_FROM = 60, 20  #: the daily returns kept for the correlation gate, and the fewest


def moves(
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


def traded_value(bars: Sequence[Bar], fx: Decimal) -> Decimal:
    """THE POUNDS A LINE TRADED over its last TRADED_DAYS bars (close times volume, at fx); a
    line with fewer bars has traded less, and is judged on what it has."""
    return sum((bar.close * bar.volume * fx for bar in bars[-TRADED_DAYS:]), Decimal(0))
