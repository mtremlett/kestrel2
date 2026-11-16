"""The ladder's bars come from the history database alone: its lines, each line's bars and the
pound are read there with no grid/store folder, and a line it lacks is named."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk import bars
from desk.lines import POUND
from desk.store import Bar
from lab import history_bars, ladder, universe

ONE, TWO = universe.UNIVERSE[0], universe.UNIVERSE[1]
DAYS = [ladder.END - timedelta(n) for n in range(10, -3, -1)]  #: two days run past the window


def _series(price: str) -> list[Bar]:
    close = Decimal(price)
    return [Bar(d, close, close, close, close, 0) for d in DAYS]


def test_each_set_reads_lines_bars_and_pound_from_the_history_database_and_names_a_lack(
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError, match=bars.HISTORY):
        history_bars.lines(tmp_path)
    with bars.writing(tmp_path / bars.LIVE) as opened:
        opened.days(ONE, _series("10"))
    assert not (tmp_path / "grid").exists()
    assert history_bars.lines(tmp_path) == (ONE,)
    read = history_bars.reader(tmp_path)
    assert [b.day for b in read(ONE)] == [d for d in DAYS if d <= ladder.END]
    with pytest.raises(LookupError, match=TWO.symbol):
        read(TWO)
    with pytest.raises(LookupError, match=POUND.symbol):
        history_bars.pounds(tmp_path)
    with bars.writing(tmp_path / bars.LIVE) as opened:
        opened.days(POUND, _series("1.25"))
    rates = history_bars.pounds(tmp_path)
    assert rates[ladder.END] == Decimal("0.8") and min(rates) > DAYS[0]
    assert max(rates) == ladder.END and isinstance(next(iter(rates)), date)
