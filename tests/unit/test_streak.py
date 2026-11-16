"""FIRST-LIGHT is ten consecutive clean days from the desk's own records (NS-10)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from desk import book, day, streak
from desk.day import Record
from desk.orders import Charges

START = date(2026, 11, 2)


def made(n: int, stopped: int | None = 0, halted: bool = False) -> Record:
    """Day n's record: reconciled, with `stopped` signals refused, perhaps under a halt."""
    cut = (datetime(2026, 11, 2, 9, tzinfo=UTC),) if halted else ()
    zero = Decimal(0)
    return Record(
        START + timedelta(n), Decimal(1), Charges(*[zero] * 5), zero, (), zero, 0, cut, stopped
    )


def kept(root: Path, records: list[Record]) -> None:
    """Write records as the desk keeps them."""
    book._write(root / day.RECORDS, [day.HEADER, *(day._row(r) for r in records)])


def test_ten_clean_days_in_a_row_are_first_light_and_nothing_less_is(tmp_path: Path) -> None:
    nine = [made(n) for n in range(9)]
    kept(tmp_path, nine)
    assert streak.clean(day.records(tmp_path)) == 9 and not streak.first_light(tmp_path)
    kept(tmp_path, [*nine, made(9)])
    assert streak.first_light(tmp_path)


def test_a_day_that_sent_nothing_halted_or_stopped_orders_breaks_the_run(tmp_path: Path) -> None:
    for bad in (made(5, stopped=None), made(5, halted=True), made(5, stopped=1)):
        days = [made(n) if n != 5 else bad for n in range(12)]
        assert streak.clean(days) == 6
        kept(tmp_path, days)
        assert not streak.first_light(tmp_path)
    assert streak.clean([]) == 0 and not streak.first_light(tmp_path / "none")
