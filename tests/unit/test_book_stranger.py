"""R-RUNNER-517: shares under a working broker stop are sheltered, never sold as a stranger."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from desk import book
from desk.broker import Pretend
from desk.lines import Line
from desk.store import Bar

A, MON = Line("H", "LSE", "GBP", 1), date(2025, 11, 10)


def test_a_stranger_under_a_working_stop_is_sheltered_not_sold_and_one_without_is_still_sold(
    tmp_path: Path,
) -> None:
    bar = Bar(MON, Decimal(50), Decimal(51), Decimal(49), Decimal(51), 1)
    broker = Pretend({A: (bar,)}, {})
    broker.open(MON)
    broker.inject("H", 5)
    broker.put_stop_back("H", Decimal(40))
    broker.inject("H", 2)  #: two more, with no stop of their own
    assert book.sheltered(tmp_path, broker) == (("H", 5),)
    assert book.strangers(tmp_path, broker) == (("H", 2),)
