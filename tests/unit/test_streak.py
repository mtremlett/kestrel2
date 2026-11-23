"""streak: ten consecutive counting days are FIRST-LIGHT; a day that does not count, a day that
sent nothing included, ends the run; the run is read from the end of the records."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from desk import streak
from desk.day import Record
from desk.orders import Charges

START = date(2025, 1, 6)
COSTS = Charges(*[Decimal(0)] * 5)


def _days(shape: str) -> list[Record]:
    """One record a day: C counts, N sent nothing, H had a halt in force, M mismatched."""
    made = []
    for n, kind in enumerate(shape):
        halted = (datetime(2025, 1, 6, 8, tzinfo=UTC),) if kind == "H" else ()
        stopped = None if kind == "N" else 0
        profit = None if kind == "M" else Decimal(1)
        lines = ("X",) if kind == "M" else ()
        made.append(
            Record(
                START + timedelta(days=n),
                profit,
                COSTS,
                Decimal(0),
                lines,
                Decimal(0),
                0,
                halted,
                stopped,
            )
        )
    return made


def test_ten_in_a_row_is_first_light() -> None:
    run = streak.count(_days("C" * 10))
    assert (run.days, run.broke, run.reached) == (10, None, True)
    assert run.says() == "FIRST-LIGHT: 10 clean days in a row."


def test_each_kind_of_bad_day_ends_the_run() -> None:
    for bad in "NHM":
        run = streak.count(_days("C" * 12 + bad + "C" * 3))
        assert (run.days, run.broke, run.reached) == (3, START + timedelta(days=12), False)
    assert streak.count(_days("C" * 9)).says() == "9 of 10 clean days in a row."
    assert streak.count(_days("NCC")).says() == (
        f"2 of 10 clean days in a row, since {START} did not count."
    )


def test_a_desk_with_no_records_has_no_run() -> None:
    assert streak.count(()) == streak.Streak(0, None)
    assert streak.count(_days("N")).days == 0
