"""The ladder's rates are one kept table (spec decision 7): the archive is asked once, for the
pound to the window's end, and a day's rate is one over the pound's last close BEFORE it."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from desk.command import POUND
from desk.lines import Line
from desk.store import Bar
from lab import ladder


def test_the_rates_are_one_kept_table_never_asked_for_twice(tmp_path: Path) -> None:
    day, asked = date(2020, 1, 6), []

    def ask(line: Line, before: date) -> list[Bar]:
        asked.append((line, before))
        closes = [(day, "1.25"), (day + timedelta(1), "1.6"), (ladder.END, "1.28")]
        return [Bar(d, Decimal(c), Decimal(c), Decimal(c), Decimal(c), 0) for d, c in closes]

    def gone(line: Line, before: date) -> list[Bar]:
        raise AssertionError(f"{line.symbol} before {before}: asked for again, and it is kept")

    first = ladder.rates(ask, home=tmp_path)
    assert asked == [(POUND, ladder.END + timedelta(1))] and any((tmp_path / "ladder").iterdir())
    assert (first[day + timedelta(1)], first[day + timedelta(2)]) == (
        Decimal("0.8"),
        Decimal("0.625"),
    )
    assert day not in first and ladder.rates(gone, home=tmp_path) == first
