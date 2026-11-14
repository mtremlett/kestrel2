"""The pound's rate across a UK-only holiday (desk.carry), through book.rate."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book


def test_the_pound_is_carried_across_a_uk_only_holiday_and_no_further(tmp_path: Path) -> None:
    for on, usd in ((date(2025, 4, 17), "0.76"), (date(2025, 12, 24), "0.74")):
        book.record_rates(tmp_path, on, {"USD": Decimal(usd)})
    easter, boxing = date(2025, 4, 21), date(2025, 12, 26)  # London shut, New York open
    assert book.rate(tmp_path, "USD", easter) == Decimal("0.76")  # Thursday's, over Good Friday
    assert book.rate(tmp_path, "USD", boxing) == Decimal("0.74")
    for none in (date(2025, 4, 18), date(2025, 4, 19), date(2025, 4, 22), date(2025, 12, 25)):
        with pytest.raises(ValueError, match="no USD rate kept"):  # both shut, weekend, both open
            book.rate(tmp_path, "USD", none)
