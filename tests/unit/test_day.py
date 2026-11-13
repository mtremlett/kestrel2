"""day: decisions dated that day only, each rule's position read from the book, its sales
first, each buy sized from the book after the send before it, and no line bought again the
morning its stop or its rule sold it."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book, day, venues
from desk.broker import Crash, Fault, Pretend
from desk.lines import Line
from desk.orders import Settings
from desk.store import Bar

DAYS = venues.sessions("LSE", date(2025, 1, 6), date(2025, 2, 28))[:23]
#: Bollinger buys the close of 9 under its lower band, and sells 10.5 over its middle
BOTH, FLAT = [9, 10.5, 10.5], [10] * 20


def _line(
    symbol: str, closes: list[int | float], reach: str = "0.5"
) -> tuple[Line, tuple[Bar, ...]]:
    half = Decimal(reach)
    return Line(symbol, "LSE", "GBP", 1), tuple(
        Bar(on, c, c + half, c - half, c, 1)
        for on, c in zip(DAYS, map(Decimal, map(str, closes)), strict=False)
    )


#: A to D and F alike; H falls to its stop of 8.1 at the last open; G's bars end too soon
ARCHIVE = dict(
    [*(_line(s, FLAT + BOTH) for s in "ABCD"), _line("H", [*FLAT, 9, 8.5, 8], "0.3")]
    + [_line("F", FLAT + BOTH), _line("G", [*FLAT[1:], 9])]
)


def _trade(root: Path, broker: Pretend, on: date) -> tuple[book.Sent, ...]:
    before = {line: tuple(b for b in bars if b.day < on) for line, bars in ARCHIVE.items()}
    return day.trade(root, before, broker, Settings(Decimal(10_000)), on, {"GBP": Decimal(1)})


def test_the_day_sells_what_each_rule_holds_then_buys_from_the_book_after_each_send(
    tmp_path: Path,
) -> None:
    broker, sent = Pretend(ARCHIVE, {}), []
    for on in DAYS[21:]:
        broker.open(on)
        sent.append(_trade(tmp_path, broker, on))
    bought, sold = sent
    assert [s.order_id[-1] for s in bought] == list("ABCDHF"), "G acted on a day not its last"
    assert all(s.reason is None for s in bought[:5]) and "5 holdings" in str(bought[5].reason)
    assert [s.order_id[-1] for s in sold] == list("ABCD"), "H bought again the morning it sold"
    assert all(s.reason is None and s.filled > 0 for s in sold)
    assert book.positions(tmp_path) == {} == broker.positions()
    trips = book.round_trips(tmp_path, tuple(ARCHIVE))
    assert sorted(t.buy.symbol for t in trips) == list("ABCDH")
    broker.open(date(2025, 2, 6))
    with pytest.raises(ValueError, match="GBP"):
        day.trade(tmp_path, ARCHIVE, broker, Settings(Decimal(10_000)), date(2025, 2, 6), {})


def test_a_day_the_book_is_not_the_brokers_buys_nothing_and_sells_only_lines_that_agree(
    tmp_path: Path,
) -> None:
    broker = Pretend(ARCHIVE, {})
    broker.open(DAYS[21])
    broker.inject("G", 5)  #: bought by hand
    refused = _trade(tmp_path, broker, DAYS[21])
    assert [s.order_id[-1] for s in refused] == list("ABCDHF") and broker.submitted() == ()
    assert all(s.filled == 0 and "['G']" in str(s.reason) for s in refused), "no reason given"
    broker.inject("G", -5)
    bought = _trade(tmp_path, broker, DAYS[21])  #: the same morning, once the books agree
    assert [s.filled > 0 for s in bought] == [True] * 5 + [False]
    broker.open(DAYS[22])
    broker.inject("A", -1)  #: one share of A sold by hand
    sold = _trade(tmp_path, broker, DAYS[22])
    assert [s.order_id[-1] for s in sold] == list("ABCD"), "a sale left unanswered"
    assert [s.filled > 0 for s in sold] == [False, True, True, True], "A sold, or B to D kept"
    assert "['A']" in str(sold[0].reason) and list(book.positions(tmp_path)) == ["A"]
    dying = Pretend(ARCHIVE, {"A": Fault.CRASH})
    dying.open(DAYS[21])
    with pytest.raises(Crash):  #: only a refusal is an answer: the desk dying is not
        _trade(tmp_path / "dying", dying, DAYS[21])
