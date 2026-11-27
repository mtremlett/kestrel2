"""book: shares the book lacks that sit under the desk's own stop at the broker are no stranger."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from desk import book
from desk.broker import Pretend
from desk.lines import Line
from desk.store import Bar
from desk.venues import sessions

DAY = sessions("LSE", date(2025, 1, 6), date(2025, 1, 10))[0]
LINE = Line("H", "LSE", "GBP", 1)
TEN = Decimal(10)


def test_shares_under_a_broker_stop_are_not_taken_in_and_sold_on_top_of_it(tmp_path: Path) -> None:
    broker = Pretend({LINE: (Bar(DAY, TEN, TEN + 1, TEN - 1, TEN, 10**7),)}, {})
    broker.open(DAY)
    broker.inject("H", 5)
    broker.put_stop_back("H", Decimal(1))  #: the stop rests for all 5 the book lacks
    assert book.strangers(tmp_path, broker) == ()
    broker.inject("H", 3)  #: 3 more, under no stop
    assert book.strangers(tmp_path, broker) == (("H", 3),)
    book.adopt(tmp_path, LINE, 5, TEN, DAY)  #: the book now holds the 5 the stop rests under
    assert book.strangers(tmp_path, broker) == (("H", 3),)
    broker.inject("H", -3)
    assert book.strangers(tmp_path, broker) == ()
