"""The weather the desk records each day (desk/weather.py)."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk import weather
from desk.store import Bar


def _bars(closes: list[int]) -> list[Bar]:
    start = date(2024, 1, 1)
    return [
        Bar(start + timedelta(n), Decimal(c), Decimal(c), Decimal(c), Decimal(c), 1)
        for n, c in enumerate(closes)
    ]


CLOSES = [100 + (n * 7) % 11 for n in range(40)]


def test_realised_volatility_is_recorded_each_day_before_it_acts(tmp_path: Path) -> None:
    bars = _bars(CLOSES)
    readings = weather.realised_volatility(bars)
    assert len(readings) == len(CLOSES) - weather.VOL_DAYS
    assert bars[weather.VOL_DAYS - 1].day not in readings  # too few returns: no guess
    assert weather.record(tmp_path, "VUSA", bars) == len(readings)
    assert weather.record(tmp_path, "VUSA", bars) == 0  # a second call adds nothing
    assert len((tmp_path / "VUSA.jsonl").read_text().splitlines()) == len(readings)


def test_a_reading_never_reads_a_later_bar() -> None:
    whole = weather.realised_volatility(_bars(CLOSES))
    cut = weather.realised_volatility(_bars(CLOSES[:30]))
    assert cut and all(whole[day] == vol for day, vol in cut.items())


def test_bars_out_of_order_are_refused() -> None:
    bars = _bars(CLOSES)
    with pytest.raises(ValueError, match="oldest first"):
        weather.realised_volatility(bars[::-1])
