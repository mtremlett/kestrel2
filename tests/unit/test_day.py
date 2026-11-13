"""day: decisions dated that day only, each rule's position read from the book, its sales
first, each buy sized from the book after the send before it, and no line bought again the
morning its stop or its rule sold it. Then the day's record: the book's gain after every cost
beside the market's, to the penny, or the lines on which the book is not the broker's."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book, day, venues
from desk.broker import Broker, Crash, Fault, Pretend
from desk.lines import YARDSTICK, Line
from desk.orders import Charges, Settings
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
#: the same, with the yardstick too young for any rule: it closes at 10, 10.2 and 10.1
MARKET = {
    **ARCHIVE,
    YARDSTICK: tuple(
        Bar(on, c, c, c, c, 1)
        for on, c in zip(DAYS[20:], map(Decimal, ("10", "10.2", "10.1")), strict=True)
    ),
}


def _trade(root: Path, broker: Broker, on: date) -> tuple[book.Sent, ...]:
    before = {line: tuple(b for b in bars if b.day < on) for line, bars in ARCHIVE.items()}
    return day.trade(root, before, broker, Settings(Decimal(10_000)), on, {"GBP": Decimal(1)})


class Door:
    """Any broker, not the pretend one by name."""

    def __init__(self, inner: Pretend) -> None:
        self.report, self.place, self.fills = inner.report, inner.place, inner.fills
        self.holdings, self.stops, self.cancel = inner.holdings, inner.stops, inner.cancel


def test_the_day_sells_what_each_rule_holds_then_buys_from_the_book_after_each_send(
    tmp_path: Path,
) -> None:
    broker, sent = Pretend(ARCHIVE, {}), []
    for on in DAYS[21:]:
        broker.open(on)
        sent.append(_trade(tmp_path, Door(broker), on))
    bought, sold = sent
    assert [s.order_id[-1] for s in bought] == list("ABCDHF"), "G acted on a day not its last"
    assert all(s.reason is None for s in bought[:5]) and "5 holdings" in str(bought[5].reason)
    assert [s.order_id[-1] for s in sold] == list("ABCD"), "H bought again the morning it sold"
    assert all(s.reason is None and s.filled > 0 for s in sold)
    assert book.positions(tmp_path) == {} == dict(broker.holdings())
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


def test_a_day_with_the_kill_switch_on_sends_nothing_and_every_answer_says_so(
    tmp_path: Path,
) -> None:
    broker = Pretend(ARCHIVE, {})
    broker.open(DAYS[21])
    _trade(tmp_path, broker, DAYS[21])
    book.turn(tmp_path, book.Switch.ON, datetime(2025, 2, 5, 7, tzinfo=UTC), "his word")
    broker.open(DAYS[22])  #: H's stop sells at the broker, switch or no switch
    answers = _trade(tmp_path, Door(broker), DAYS[22])
    assert [s.order_id[-1] for s in answers] == list("ABCD"), "a decision left unanswered"
    assert all(s.filled == 0 and "kill switch" in str(s.reason) for s in answers)
    assert len(broker.submitted()) == 5 and list(book.positions(tmp_path)) == list("ABCD")


def _run(root: Path, broker: Pretend, on: date) -> day.Record:
    """The day whole, handed every bar there is: it must use none after the day's own."""
    broker.open(on)
    return day.run(root, MARKET, broker, Settings(Decimal(10_000)), on, {"GBP": Decimal(1)})


def test_the_days_record_is_the_books_gain_after_every_cost_beside_the_markets(
    tmp_path: Path,
) -> None:
    broker = Pretend(MARKET, {})
    pounds = [tuple(map(Decimal, row.split())) for row in ("15 5.58 5.58 0 0", "15 5.52 7.29 0 0")]
    #: 221 each of A to D bought at 10.5 and of H at 8.5, where each closes: the costs alone
    assert _run(tmp_path, broker, DAYS[21]) == day.Record(
        DAYS[21], Decimal("-26.16"), Charges(*pounds[0]), Decimal("200.00"), ()
    )
    #: A to D sold where they closed, and H by its stop at 8: 110.50 lost, and 27.818 of costs
    assert _run(tmp_path, broker, DAYS[22]) == day.Record(
        DAYS[22], Decimal("-138.32"), Charges(*pounds[1]), Decimal("-98.04"), ()
    )
    with pytest.raises(ValueError, match="VUAG"):  #: no yardstick, no record
        day.run(tmp_path, ARCHIVE, broker, Settings(Decimal(10_000)), DAYS[22], {"GBP": Decimal(1)})
    for profit, differ in ((Decimal(1), ("A",)), (None, ())):
        with pytest.raises(ValueError, match="2025-02-05"):  #: a number, or the lines: never both
            day.Record(DAYS[22], profit, Charges(*pounds[0]), Decimal(0), differ)


def test_a_day_whose_book_is_not_the_brokers_names_the_lines_and_withholds_its_profit(
    tmp_path: Path,
) -> None:
    broker = Pretend(MARKET, {})
    assert _run(tmp_path, broker, DAYS[21]).mismatches == ()
    broker.inject("G", 5)  #: bought by hand, after the day's record
    record = _run(tmp_path, broker, DAYS[22])
    assert (record.profit, record.mismatches) == (None, ("G",)), "a mismatched day given a number"
    assert (record.costs.commission, record.market) == (
        Decimal(15),
        Decimal("-98.04"),
    ), "A to D still sold"
