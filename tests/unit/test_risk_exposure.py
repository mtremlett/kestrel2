"""risk: two lines correlated above the cap are not both entered; a volatile line is sized smaller
(R-RUNNER-147)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from desk.risk import correlated_with, shares_for_risk, volatility

UP = (0.01, -0.02, 0.03, -0.01, 0.02)
TWIN = (0.011, -0.019, 0.029, -0.012, 0.021)
OPPOSITE = tuple(-r for r in UP)
CALM = tuple(r / 4 for r in UP)


def test_a_correlated_line_is_not_entered_and_a_volatile_line_is_sized_smaller() -> None:
    assert "held A" in str(correlated_with(TWIN, {"A": UP}, 0.8))
    assert correlated_with(OPPOSITE, {"A": UP}, 0.8) is None
    assert correlated_with(UP, {}, 0.8) is None
    risk, price = Decimal(100), Decimal(50)
    calm, wild = (
        shares_for_risk(risk, price, volatility(CALM)),
        shares_for_risk(risk, price, volatility(UP)),
    )
    assert wild < calm and wild == 100 // (50 * float(volatility(UP))) // 1
    with pytest.raises(ValueError, match="positive"):
        shares_for_risk(risk, price, Decimal(0))
    with pytest.raises(ValueError, match="never move"):
        correlated_with((0.0,) * 5, {"A": UP}, 0.8)
