"""The pound's rate across a UK-only holiday (desk.carry), through book.rate."""

from collections.abc import Iterator
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book
from desk.broker import Fill


def test_the_pound_is_carried_across_a_uk_only_holiday_and_no_further(tmp_path: Path) -> None:
    for on, usd in ((date(2025, 4, 17), "0.76"), (date(2025, 12, 24), "0.74")):
        book.record_rates(tmp_path, on, {"USD": Decimal(usd)})
    easter, boxing = date(2025, 4, 21), date(2025, 12, 26)  # London shut, New York open
    assert book.rate(tmp_path, "USD", easter) == Decimal("0.76")  # Thursday's, over Good Friday
    assert book.rate(tmp_path, "USD", boxing) == Decimal("0.74")
    for none in (date(2025, 4, 18), date(2025, 4, 19), date(2025, 4, 22), date(2025, 12, 25)):
        with pytest.raises(ValueError, match="no USD rate kept"):  # both shut, weekend, both open
            book.rate(tmp_path, "USD", none)


class _Told:
    def __init__(self, *told: Fill) -> None:
        self.told = told

    def fills(self) -> tuple[Fill, ...]:
        return self.told


def test_the_brokers_correction_of_a_fill_is_one_fill_in_the_ledger_never_two(
    tmp_path: Path,
) -> None:
    day = date(2025, 11, 10)
    one, other = (
        Fill("0001.65.01", "o-1", "A", 10, Decimal(50), day),
        Fill("0002.65.01", "o-2", "B", 5, Decimal(9), day),
    )
    fixed = replace(one, execution_id="0001.65.02", price=Decimal(51))
    for told in ((one, other), (one,), (fixed,), (one, fixed), (fixed,), (one,)):  # stale .01 last
        book.collect(tmp_path, _Told(*told))  # type: ignore[arg-type]  # a stub broker
    assert book.fills(tmp_path) == (fixed, other)
    assert book.positions(tmp_path) == {"A": 10, "B": 5}


def test_the_keeper_of_records_writes_whole_and_a_death_mid_write_leaves_the_old_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "sub" / "records.csv"
    book.keep(path, [("a", "b"), ("1", "2")])
    assert path.read_text(encoding="utf-8").split() == ["a,b", "1,2"]

    def dies() -> Iterator[tuple[str, ...]]:
        yield ("x", "y")
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        book.keep(path, dies())
    assert path.read_text(encoding="utf-8").split() == ["a,b", "1,2"]
    assert [p.name for p in path.parent.iterdir()] == ["records.csv"]  # no part file left

    def second_writer() -> Iterator[tuple[str, ...]]:
        yield ("first",)
        book.keep(path, [("second",)])  # lands while the first is half written
        yield ("done",)

    book.keep(path, second_writer())  # two writers, two temp files, no unreadable record
    assert path.read_text(encoding="utf-8").split() == ["first", "done"]


def test_shares_under_the_brokers_stop_are_no_stranger_to_sell_twice(tmp_path: Path) -> None:
    from desk.broker import Pretend

    broker = Pretend({}, {})
    broker.inject("H", 5)
    broker.inject("Z", 3)
    broker.put_stop_back("H", Decimal(1))  #: world 4: shares the book lacks, a stop over them
    assert book.strangers(tmp_path, broker) == (("Z", 3),)
