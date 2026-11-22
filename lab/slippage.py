"""slippage - WHAT THE PAPER BROKER'S FILLS COST AGAINST THE BAR'S CLOSE, BESIDE THE MODEL (Q2).

`orders.charges` ASSUMES half the spread and the slippage of each leg. This reads the desk's
ledger of real paper fills and measures what each lost against the close of the session it was
made in: a purchase's price over the close, a sale's close over its price, less one, so that a
positive figure is a cost. Beside it, per line, the model's charge for the same legs (the one
cost model, at the same prices), and the gap. Only the model's spread and slippage are set
beside it: the close is no commission.

A fill of a symbol the desk has no line for is refused; a fill whose session has no bar yet is
counted as waiting, never dropped silently. Prints one line per line and a line of counts.
    python -m lab.slippage            reads KESTREL2_DATA's ledger and daily database
"""

from __future__ import annotations

import os
import sys
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from desk import bars, book, keeper, orders
from desk.broker import Fill
from desk.lines import LINES, Line
from desk.store import Bar

Bars = Callable[[Line], Sequence[Bar]]


@dataclass(frozen=True)
class Slip:
    """One line's fills: the mean slip measured and the model's charge, both as parts of value."""

    line: Line
    fills: int
    measured: Decimal
    model: Decimal

    @property
    def gap(self) -> Decimal:
        """Measured less modelled: positive when the broker cost more than the model said."""
        return self.measured - self.model


def slip(fill: Fill, close: Decimal) -> Decimal:
    """What one fill lost against the close, as a part of its price; positive is a cost."""
    return fill.price / close - 1 if fill.quantity > 0 else 1 - fill.price / close


def charge(line: Line, fill: Fill) -> Decimal:
    """The model's spread and slippage on the fill's leg, as a part of its value."""
    shares = abs(fill.quantity)
    leg = orders.leg_of(fill.order_id, fill.quantity)
    got = orders.charges(line, leg, shares, fill.price, Decimal(1))
    return (got.spread + got.slippage) / (shares * fill.price)


def measure(fills: Sequence[Fill], bars: Bars) -> tuple[tuple[Slip, ...], int]:
    """Each line's slip beside the model's, in the lines' order, and the fills waiting for a bar."""
    by_symbol = {line.symbol: line for line in LINES}
    found: dict[Line, list[tuple[Decimal, Decimal]]] = defaultdict(list)
    waiting = 0
    for fill in fills:
        if fill.symbol not in by_symbol:
            raise ValueError(f"fill {fill.execution_id}: no line for {fill.symbol}")
        line = by_symbol[fill.symbol]
        close = {bar.day: bar.close for bar in bars(line)}.get(fill.day)
        if close is None:
            waiting += 1
            continue
        found[line].append((slip(fill, close), charge(line, fill)))
    rows = tuple(
        Slip(
            line,
            len(pairs),
            *(sum(part, Decimal(0)) / len(pairs) for part in zip(*pairs, strict=True)),
        )
        for line, pairs in sorted(found.items(), key=lambda item: LINES.index(item[0]))
    )
    return rows, waiting


def report(rows: Sequence[Slip], waiting: int) -> str:
    """One line per line, in per cent of value, and the line of counts."""
    cent = Decimal(100)
    lines = [
        f"{r.line.symbol}: {r.fills} fills, measured {r.measured * cent:.4f}% "
        f"model {r.model * cent:.4f}% gap {r.gap * cent:+.4f}%"
        for r in rows
    ]
    total = sum(r.fills for r in rows)
    return "\n".join([*lines, f"slippage: {total} fills on {len(rows)} lines, {waiting} waiting"])


def stored(home: Path) -> Bars:
    """A line's daily bars from the store's one daily database, read once per line."""
    path = bars.files(home / keeper.HOT)[bars.DAILY]
    return lambda line: bars.daily(path, line)


def main(env: Mapping[str, str]) -> int:
    """Measure the ledger under KESTREL2_DATA and print the report."""
    if not env.get("KESTREL2_DATA"):
        sys.exit("slippage: KESTREL2_DATA names no data folder, so there are no fills to read")
    home = Path(env["KESTREL2_DATA"])
    fills = book.fills(home / "desk")
    sys.stdout.write(report(*measure(fills, stored(home))) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(os.environ))
