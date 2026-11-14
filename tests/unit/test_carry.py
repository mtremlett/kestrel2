"""The pound's rate from its closes (desk.carry.pounds_per_dollar), across Easter 2025's hole."""

from datetime import date
from decimal import Decimal

from desk.carry import pounds_per_dollar
from desk.venues import sessions


def test_a_long_holiday_weekend_is_fresh_but_two_shared_sessions_missing_is_stale() -> None:
    closes = {d: Decimal("1.25") for d in sessions("LSE", date(2025, 1, 1), date(2025, 6, 30))}
    for day in sessions("US", date(2025, 1, 3), date(2025, 6, 30)):
        assert pounds_per_dollar(closes, day) == Decimal("0.8"), day
    assert pounds_per_dollar(closes, date(2025, 4, 22)) == Decimal("0.8")  # after Easter
    assert pounds_per_dollar(closes, date(2025, 1, 1)) is None  # no close before it
    assert pounds_per_dollar({date(2025, 6, 2): Decimal("1.25")}, date(2025, 6, 5)) is None
    assert pounds_per_dollar({date(2025, 6, 2): Decimal("1.25")}, date(2025, 6, 4)) is None
    assert pounds_per_dollar({date(2025, 6, 2): Decimal("1.25")}, date(2025, 6, 3)) == Decimal(
        "0.8"
    )
