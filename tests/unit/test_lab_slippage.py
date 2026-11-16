"""The slippage command: fixture fills with a known slip give that slip, and the model's charge."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from desk import orders
from desk.broker import Fill
from desk.lines import LINES
from desk.store import Bar
from lab import slippage

LINE = LINES[0]
DAY = date(2026, 11, 10)
CLOSE = Decimal(100)


def _fill(n: str, shares: int, price: str, order: str = "o-x-1", day: date = DAY) -> Fill:
    return Fill(n, order, LINE.symbol, shares, Decimal(price), day)


def _bars(_line: object) -> list[Bar]:
    return [Bar(DAY, CLOSE, CLOSE, CLOSE, CLOSE, 1)]


def test_known_slips_are_measured_beside_the_models_charge() -> None:
    fills = [
        _fill("a", 10, "100.20"),  # bought 0.2% over the close
        _fill("b", -10, "99.90", "o-x-1-stop"),  # stop sold 0.1% under
        _fill("c", 5, "100", day=date(2026, 11, 11)),  # no bar yet
    ]
    rows, waiting = slippage.measure(fills, _bars)
    assert waiting == 1
    (row,) = rows
    assert row.fills == 2 and row.measured == Decimal("0.0015")
    model = [
        slippage.charge(LINE, fills[0]),
        slippage.charge(LINE, fills[1]),
    ]
    assert row.model == sum(model) / 2
    buy = orders.charges(LINE, orders.Leg.BUY, 10, Decimal("100.20"), Decimal(1))
    assert model[0] * 10 * Decimal("100.20") == buy.spread + buy.slippage
    assert model[1] > model[0] * 3 / 2  # a stop slips further than a buy
    assert row.gap == row.measured - row.model
    assert "1 waiting" in slippage.report(rows, waiting)


def test_a_fill_of_no_line_is_refused() -> None:
    odd = Fill("z", "o-x-1", "NOSUCH", 1, CLOSE, DAY)
    with pytest.raises(ValueError, match="NOSUCH"):
        slippage.measure([odd], _bars)
