"""day: a position the desk did not make is named, taken into the book and sold (TRD-06)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from desk import book, day, halt, venues
from desk.broker import Pretend
from desk.halt import Blocker
from desk.lines import Line
from desk.orders import Settings
from desk.store import Bar

DAYS = venues.sessions("LSE", date(2025, 1, 6), date(2025, 1, 31))[:10]
TEN = Decimal(10)
LINE = Line("H", "LSE", "GBP", 1)
ARCHIVE = {LINE: tuple(Bar(d, TEN, TEN + 1, TEN - 1, TEN, 1) for d in DAYS)}


def _trade(root: Path, broker: Pretend, on: date, told: list[str]) -> tuple[book.Sent, ...]:
    before = {line: tuple(b for b in bars if b.day < on) for line, bars in ARCHIVE.items()}
    settings, pounds = Settings(Decimal(10_000)), {"GBP": Decimal(1)}
    return day.trade(root, before, broker, settings, on, pounds, lambda name, _: told.append(name))


def test_a_stranger_is_told_taken_into_the_book_and_sold_and_one_with_no_line_is_left_to_a_hand(
    tmp_path: Path,
) -> None:
    broker, told = Pretend(ARCHIVE, {}), list[str]()
    broker.open(DAYS[5])
    broker.inject("H", 5)  #: bought by hand
    sent = _trade(tmp_path, broker, DAYS[5], told)
    assert told == ["stranger"] and sent[0].order_id.endswith("-stranger-H")
    assert (sent[0].filled, sent[0].blocker) == (5, None)
    assert dict(broker.holdings()).get("H", 0) == 0 and "H" not in book.positions(tmp_path)
    assert book.strangers(tmp_path, broker) == ()
    broker.inject("Z", 2)  #: no line of the desk's
    assert book.strangers(tmp_path, broker) == (("Z", 2),)
    broker.open(DAYS[6])
    _trade(tmp_path, broker, DAYS[6], told)
    assert told[-1] == "stranger"
    assert [b.filled for b in halt.morning(tmp_path, DAYS[6])[Blocker.BOOK]] == [0]
    broker.inject("Z", -2)
    _trade(tmp_path, broker, DAYS[6], told)
    assert halt.morning(tmp_path, DAYS[6])[Blocker.BOOK] == (), "a stranger gone, still listed"
