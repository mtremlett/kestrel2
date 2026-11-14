"""day: decisions dated that day only, each rule's position read from the book, its sales
first, each buy sized from the book after the send before it, and no line bought again the
morning its stop or its rule sold it. Then the day's record: the book's gain after every cost
beside the market's, to the penny, or the lines on which the book is not the broker's."""

from __future__ import annotations

from dataclasses import astuple, replace
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book, day, halt, venues
from desk.broker import Broker, Crash, Fault, Pretend, Report
from desk.halt import Blocker
from desk.lines import YARDSTICK, Line
from desk.orders import Charges, Order, Refused, Sale, Settings
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
#: the same, with the yardstick too young for any rule: it closes at 10, 10, 10.2 and 10.1,
#: a pound under each open
MARKET = {
    **ARCHIVE,
    YARDSTICK: tuple(
        Bar(on, c + 1, c + 1, c, c, 1)
        for on, c in zip(DAYS[19:], map(Decimal, ("10", "10", "10.2", "10.1")), strict=True)
    ),
}


ARCHIVE_LINES = {line.symbol: line for line in ARCHIVE}


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
    assert bought[5].blocker is Blocker.GATE and not any(s.blocker for s in bought[:5])
    assert [s.order_id[-1] for s in sold] == list("ABCDH"), "a decision left unanswered"
    assert all(s.reason is None and s.filled > 0 for s in sold[:4])
    again = (sold[4].filled, sold[4].blocker)  #: H is not bought again the morning its stop sold
    assert again == (0, Blocker.HELD) and "H was sold this morning" in str(sold[4].reason)
    assert book.positions(tmp_path) == {} == dict(broker.holdings())
    trips = book.round_trips(tmp_path, tuple(ARCHIVE))
    assert sorted(t.buy.symbol for t in trips) == list("ABCDH")
    broker.open(date(2025, 2, 6))
    with pytest.raises(ValueError, match="GBP"):
        day.trade(tmp_path, ARCHIVE, broker, Settings(Decimal(10_000)), date(2025, 2, 6), {})

    def shut(order: Order | Sale) -> Report:
        raise Refused(f"{order.order_id}: not sent, the account was not checked today")

    door = Door(Pretend(ARCHIVE, {}))  #: a refusal at the broker's own door is the broker's
    door.place = shut
    assert {s.blocker for s in _trade(tmp_path / "shut", door, DAYS[21])} == {Blocker.BROKER}
    hand, first = Pretend(ARCHIVE, {}), next(iter(ARCHIVE))  #: A, bought by hand before the day
    hand.open(DAYS[21])
    order = Order("x-hand-A", first, 1, Decimal(10), Decimal(1), Decimal(9))
    book.send(tmp_path / "hand", hand, order, Settings(Decimal(10_000)))
    held = _trade(tmp_path / "hand", hand, DAYS[21])[0]  #: a line held is not bought: said so
    assert held.blocker is Blocker.HELD and "A is held already" in str(held.reason)


def test_a_day_the_book_is_not_the_brokers_buys_nothing_and_sells_only_lines_that_agree(
    tmp_path: Path,
) -> None:
    broker = Pretend(ARCHIVE, {})
    broker.open(DAYS[21])
    broker.inject("G", 5)  #: bought by hand
    stale = {line: bars[:20] for line, bars in ARCHIVE.items()}  #: no bar yet for the day before
    room, pounds = Settings(Decimal(10_000)), {"GBP": Decimal(1)}
    assert day.trade(tmp_path, stale, broker, room, DAYS[21], pounds) == (), "decided on old bars"
    unread = halt.morning(tmp_path, DAYS[21])[Blocker.UNREAD]  #: no silence: every line is named
    assert [b.order_id for b in unread] == list("ABCDHFG")
    refused = _trade(tmp_path, broker, DAYS[21])
    assert [s.order_id[-1] for s in refused] == list("ABCDHF") and broker.submitted() == ()
    assert all(s.filled == 0 and "['G']" in str(s.reason) for s in refused), "no reason given"
    assert {s.blocker for s in refused} == {Blocker.BOOK}
    broker.inject("G", -5)
    assert len(halt.morning(tmp_path, DAYS[21])[Blocker.BOOK]) == 6
    bought = _trade(tmp_path, broker, DAYS[21])  #: the same morning, once the books agree
    assert [s.filled > 0 for s in bought] == [True] * 5 + [False]
    #: the morning's list as its last run left it: G unread, F at the gate, no order at the book
    assert [len(b) for b in halt.morning(tmp_path, DAYS[21]).values()] == [1, 0, 0, 0, 0, 1, 0]
    broker.open(DAYS[22])
    broker.inject("A", -1)  #: one share of A sold by hand
    sold = _trade(tmp_path, broker, DAYS[22])
    assert [s.order_id[-1] for s in sold] == list("ABCDH"), "a decision left unanswered"
    assert [s.filled > 0 for s in sold[:4]] == [False, True, True, True], "A sold, or B to D kept"
    assert [s.blocker for s in sold] == [Blocker.BOOK, None, None, None, Blocker.HELD]
    assert "['A']" in str(sold[0].reason) and list(book.positions(tmp_path)) == ["A"]
    listed = halt.morning(tmp_path, DAYS[22])  #: a sale refused is on the list like a buy
    assert [b.order_id[-1] for b in listed[Blocker.BOOK] + listed[Blocker.HELD]] == ["A", "H"]
    dying = Pretend(ARCHIVE, {"A": Fault.CRASH})
    dying.open(DAYS[21])
    with pytest.raises(Crash):  #: only a refusal is an answer: the desk dying is not
        _trade(tmp_path / "dying", dying, DAYS[21])
    opened = halt.morning(tmp_path / "dying", DAYS[21])  #: its list opened before any order went
    assert [b.order_id for b in opened[Blocker.UNREAD]] == ["G"]
    dying.open(DAYS[22])  #: the fill it died on is the broker's alone: the first record its day's
    with pytest.raises(ValueError, match="no record yet for .*2025, 2, 4"):
        day.publish(tmp_path / "dying", MARKET, dying, Settings(Decimal(10_000)), DAYS[22])
    part = Pretend(ARCHIVE, {"A": Fault.PARTIAL, "C": Fault.CRASH})
    part.open(DAYS[21])
    with pytest.raises(Crash):
        _trade(tmp_path / "part", part, DAYS[21])
    #: A's part fill is on the list the moment it is answered, and stays when the desk is
    #: started again and its rule, holding A now, asks for no more
    for again in (False, True):
        kept = halt.morning(tmp_path / "part", DAYS[21])[Blocker.BROKER]
        assert [(b.order_id[-1], b.filled) for b in kept] == [("A", 110)], f"dropped: {again}"
        _trade(tmp_path / "part", part, DAYS[21])


def test_a_day_with_the_kill_switch_on_sends_nothing_and_every_order_is_answered_so(
    tmp_path: Path,
) -> None:
    broker = Pretend(ARCHIVE, {})
    broker.open(DAYS[21])
    _trade(tmp_path, broker, DAYS[21])
    book.turn(tmp_path, book.Switch.ON, datetime(2025, 2, 5, 7, tzinfo=UTC), "his word")
    broker.open(DAYS[22])  #: H's stop sells at the broker, switch or no switch
    answers = _trade(tmp_path, Door(broker), DAYS[22])
    assert [s.order_id[-1] for s in answers] == list("ABCDH"), "a decision left unanswered"
    assert all(s.filled == 0 and "kill switch" in str(s.reason) for s in answers[:4])
    assert [s.blocker for s in answers] == [*[Blocker.KILL] * 4, Blocker.HELD]
    assert halt.stopped(tmp_path, DAYS[22]) == 4, "what the switch refused, not counted"
    assert len(broker.submitted()) == 5 and list(book.positions(tmp_path)) == list("ABCD")


def _run(root: Path, broker: Pretend, on: date) -> day.Record:
    """The day whole, handed every bar there is: it must use none after the day's own."""
    broker.open(on)
    return day.run(root, MARKET, broker, Settings(Decimal(10_000)), on, {"GBP": Decimal(1)})


def test_the_days_record_is_the_books_gain_after_every_cost_beside_the_markets(
    tmp_path: Path,
) -> None:
    broker, capital = Pretend(MARKET, {}), Settings(Decimal(10_000))
    pounds = [tuple(map(Decimal, row.split())) for row in ("15 5.58 5.58 0 0", "15 5.52 7.29 0 0")]
    #: 221 each of A to D bought at 10.5 and of H at 8.5, where each closes: the costs alone,
    #: and five fills' shares worth 11,160.50 for the next day to open from
    first = (DAYS[21], Decimal("-26.16"), pounds[0], Decimal("200.00"), (), Decimal("11160.5"), 5)
    assert astuple(_run(tmp_path, broker, DAYS[21])) == (*first, (), 0, True), "no halt: it counts"
    with pytest.raises(ValueError, match="the day is over"):  #: the ledger has later fills
        day.run(tmp_path, MARKET, broker, capital, DAYS[19], {"GBP": Decimal(1)})
    assert len(broker.submitted()) == 5, "orders sent on old decisions, for a day that is over"
    #: A to D sold where they closed, and H by its stop at 8: 110.50 lost, and 27.818 of costs
    last = (DAYS[22], Decimal("-138.32"), pounds[1], Decimal("-98.04"), (), Decimal(0), 10)
    assert astuple(_run(tmp_path, broker, DAYS[22])) == (*last, (), 0, True)
    with pytest.raises(ValueError, match="VUAG"):  #: a desk given no yardstick has no record
        bare = Pretend(ARCHIVE, {})
        bare.open(DAYS[21])
        day.run(tmp_path / "bare", ARCHIVE, bare, capital, DAYS[21], {"GBP": Decimal(1)})
    for profit, differ in ((Decimal(1), ("A",)), (None, ())):
        with pytest.raises(ValueError, match="2025-02-05"):  #: a number, or the lines: never both
            day.Record(
                DAYS[22], profit, Charges(*pounds[0]), Decimal(0), differ, Decimal(0), 0, (), 0
            )
    unsaid = day.Record(DAYS[22], Decimal(1), Charges(*pounds[0]), Decimal(0), (), Decimal(0), 0)
    assert (unsaid.halted, unsaid.stopped, unsaid.counts) == ((), None, False), "counted"


def test_a_day_with_a_halt_in_force_buys_nothing_says_so_in_its_record_and_does_not_count(
    tmp_path: Path,
) -> None:
    broker, capital = Pretend(MARKET, {}), Settings(Decimal(10_000))
    early = datetime(2025, 2, 3, 18, tzinfo=UTC)
    called = halt.call(tmp_path, early, "the market fell 5%")
    quiet = _run(tmp_path, broker, DAYS[21])
    assert broker.submitted() == (), "bought while a halt was in force"
    said = (quiet.profit, quiet.halted, quiet.stopped, quiet.counts)
    assert said == (Decimal("0.00"), (early,), 6, False)
    blocked = halt.morning(tmp_path, DAYS[21])  #: every buy the rules asked for, and why not
    assert [b.order_id[-1] for b in blocked[Blocker.HALT]] == list("ABCDHF")
    assert all("a halt is in force, called 2025-02-03" in b.reason for b in blocked[Blocker.HALT])
    #: and G, whose bars end too soon for any rule to decide: nothing else
    unread = blocked[Blocker.UNREAD]
    assert [b.order_id for b in unread] == ["G"] and "G: no bar" in unread[0].reason
    assert sum(map(len, blocked.values())) == 7
    halt.lift(tmp_path, called, datetime(2025, 2, 5, 7, tzinfo=UTC), "calm again")
    lifted = _run(tmp_path, broker, DAYS[22])  #: nor does the day it was lifted on count
    assert (lifted.halted, lifted.stopped, lifted.counts) == ((early,), 0, False)
    assert day.records(tmp_path) == (quiet, lifted), "the halt not kept as it was published"
    assert "halted,stopped" in (tmp_path / day.RECORDS).read_text("utf-8").splitlines()[0]
    #: a halt lifted after the morning it stopped, the lift dated the evening before: the day
    #: still does not count, for its own list says what the send path did
    dated, door = tmp_path / "dated", Pretend(MARKET, {})
    wrong = halt.call(dated, early, "his word")
    door.open(DAYS[21])
    assert {s.blocker for s in _trade(dated, door, DAYS[21])} == {Blocker.HALT}
    halt.lift(dated, wrong, early, "dated the evening before")
    misdated = day.publish(dated, MARKET, door, capital, DAYS[21])
    assert (misdated.halted, misdated.stopped, misdated.counts) == ((), 6, False)
    other, selling = tmp_path / "other", Pretend(MARKET, {})
    bought = _run(other, selling, DAYS[21])
    assert (bought.halted, bought.stopped, bought.counts) == ((), 0, True)
    assert [b.order_id[-1] for b in halt.morning(other, DAYS[21])[Blocker.GATE]] == ["F"]
    late = datetime(2025, 2, 5, 6, tzinfo=UTC)
    halt.call(other, late, "his word")
    sold = _run(other, selling, DAYS[22])  #: the rules and the stops sell as ever: the same number
    assert (sold.profit, sold.halted, sold.counts) == (Decimal("-138.32"), (late,), False)
    assert book.positions(other) == {} and day.records(other) == (bought, sold)


def test_a_day_whose_book_is_not_the_brokers_names_the_lines_and_withholds_its_profit(
    tmp_path: Path,
) -> None:
    after, capital = date(2025, 2, 6), Settings(Decimal(10_000))  #: a day more, no price moving
    longer = {line: (*bars, replace(bars[-1], day=after)) for line, bars in MARKET.items()}
    broker = Pretend(longer, {})
    assert _run(tmp_path, broker, DAYS[21]).mismatches == ()
    broker.inject("G", 5)  #: bought by hand, after the day's record
    record = _run(tmp_path, broker, DAYS[22])
    withheld = (record.profit, record.mismatches, record.counts)
    assert withheld == (None, ("G",), False), "a mismatched day given a number, or counted"
    sold = (record.costs.commission, record.market)
    assert sold == (Decimal(15), Decimal("-98.04")), "A to D still sold, their costs still shown"
    broker.inject("G", -5)  #: put right the day after: the day stays without a plain number
    for on in DAYS[20:]:  #: no record is made again, and none before one already published
        with pytest.raises(ValueError, match="never rewritten"):
            day.publish(tmp_path, MARKET, broker, capital, on)
    assert day.records(tmp_path)[-1] == record, "the day not kept as it was published"
    #: nothing sent the day after, the books agreeing again: the two days' number, published whole
    book.record_rates(tmp_path, after, {"GBP": Decimal(1)})
    whole = astuple(day.publish(tmp_path, longer, broker, capital, after))
    costs = tuple(map(Decimal, "15 5.52 7.29 0 0".split()))
    assert whole[1:8] == (Decimal("-138.32"), costs, Decimal("-98.04"), (), Decimal(0), 10, ())
    #: a desk whose first day is withheld: its next number runs from before that first day
    other, late = tmp_path / "other", Pretend(MARKET, {})
    late.inject("G", 5)
    assert _run(other, late, DAYS[21]).profit is None
    late.inject("G", -5)  #: the yardstick closed at 10 before the first day, and at 10.1 now
    with pytest.raises(ValueError, match="the day is over"):  #: its record made, no fill since
        day.run(other, MARKET, late, capital, DAYS[21], {"GBP": Decimal(1)})
    assert late.submitted() == (), "orders sent on old decisions, for a day whose record is made"
    assert _run(other, late, DAYS[22]).market == Decimal("100.00")
    with pytest.raises(ValueError, match="the day is over"):  #: nor the newest of two records
        day.run(other, MARKET, late, capital, DAYS[22], {"GBP": Decimal(1)})
    (tmp_path / day.RECORDS).write_text("2025-02-05,1,0,0,0,0,0,0,0,0", encoding="utf-8")
    with pytest.raises(ValueError, match="not the desk's records"):  #: its first line not the names
        day.records(tmp_path)
    #: a row kept without its halts and its stopped signals is a record made without them
    bare = day.Record(DAYS[22], Decimal(1), Charges(*costs), Decimal(0), (), Decimal(0), 0)
    book._write(tmp_path / day.RECORDS, [day.HEADER, day._row(bare)[:10]])
    assert day.records(tmp_path) == (bare,) and not bare.counts, "a day nobody sent for counted"


def test_a_session_the_desk_missed_is_named_and_gets_its_record_before_any_later_day(
    tmp_path: Path,
) -> None:
    broker, capital = Pretend(MARKET, {}), Settings(Decimal(10_000))
    broker.open(DAYS[21])
    _trade(tmp_path, broker, DAYS[21])  #: the desk dies before the day's record
    with pytest.raises(ValueError, match="the day is over"):  #: with no record yet, all the same
        _trade(tmp_path, broker, DAYS[19])
    broker.open(DAYS[22])  #: and is off: H's stop sells at the broker all the same
    with pytest.raises(ValueError, match="the day is over"):  #: that sale not yet collected
        _trade(tmp_path, broker, DAYS[21])
    assert len(broker.submitted()) == 5, "orders sent on old decisions, for a day that is over"
    with pytest.raises(ValueError, match="no record yet for .*2025, 2, 4"):  #: the first is its
        day.publish(tmp_path, MARKET, broker, capital, DAYS[22])
    bought = day.publish(tmp_path, MARKET, broker, capital, DAYS[21])
    #: the record made late is the day's own: the stop's sale, in the ledger by now, is not its
    assert (bought.profit, bought.worth, bought.counted) == (
        Decimal("-26.16"),
        Decimal("11160.5"),
        5,
    )
    with pytest.raises(ValueError, match=r"2025-02-06: no record yet for .*2025, 2, 5"):
        day.publish(tmp_path, MARKET, broker, capital, date(2025, 2, 6))
    book.record_rates(tmp_path, DAYS[22], {"GBP": Decimal(1)})
    first = next(iter(MARKET))  #: A, still held: its bar for the day is owed, not yesterday's
    with pytest.raises(ValueError, match="no close of A for"):
        day.publish(tmp_path, {**MARKET, first: MARKET[first][:-1]}, broker, capital, DAYS[22])
    halted = replace(first, suspended=frozenset({DAYS[22]}))  #: unless it did not trade
    rest = {line: bars for line, bars in MARKET.items() if line != first}
    missed = day.publish(tmp_path, {**rest, halted: MARKET[first][:-1]}, broker, capital, DAYS[22])
    #: H's 110.50 lost and its stop's 3.00, 0.884 and 2.652 of costs, in the missed day's record
    assert (missed.profit, missed.costs.total) == (Decimal("-117.04"), Decimal("6.53"))
    assert day.records(tmp_path) == (bought, missed), "a record lost, or not kept in order"
    never = (bought.stopped, missed.stopped, missed.counts)  #: its orders were never sent
    assert never == (0, None, False), "a day the desk sent no orders on, counted"


def test_a_record_opens_from_what_the_last_one_closed_on_at_each_days_own_rate(
    tmp_path: Path,
) -> None:
    dollar, capital, (fri, mon) = Line("U", "US", "USD", 1), Settings(Decimal(10_000)), DAYS[19:21]
    #: three days' closes, each a dollar over its open
    closes = zip(DAYS[18:21], map(Decimal, (50, 51, 52)), strict=True)
    held = tuple(Bar(on, c - 1, c + 1, c - 2, c, 1) for on, c in closes)
    archive = {dollar: held, YARDSTICK: tuple(replace(bar, close=Decimal(10)) for bar in held)}
    broker, at = Pretend(archive, {}), {"USD": Decimal("0.8005"), "GBP": Decimal(1)}
    broker.open(fri)  #: ten bought by hand at the open of 50, through the send path
    book.send(
        tmp_path, broker, Order("o-1", dollar, 10, Decimal(50), at["USD"], Decimal(45)), capital
    )
    first = day.run(tmp_path, archive, broker, capital, fri, at)
    #: 400.25 pounds paid for what closes at 510 dollars, 408.255 pounds: 8.005 gained, 1.321
    #: of costs; the worth is kept exact, so the days after add up to the penny
    costs = Charges(*map(Decimal, ("0.8", "0.2", "0.2", "0.12", "0")))
    assert astuple(first)[1:7] == (
        Decimal("6.68"),
        astuple(costs),
        Decimal(0),
        (),
        Decimal("408.255"),
        1,
    )
    #: five more bought after Friday's record, and a rate kept on the Saturday: neither is lost
    book.send(
        tmp_path, broker, Order("o-2", dollar, 5, Decimal(50), at["USD"], Decimal(45)), capital
    )
    book.record_rates(tmp_path, date(2025, 2, 1), {"USD": Decimal("0.7")})
    broker.open(mon)
    with pytest.raises(ValueError, match="no USD rate kept for 2025-02-03"):  #: never Saturday's
        day.publish(tmp_path, archive, broker, capital, mon)
    second = day.run(tmp_path, archive, broker, capital, mon, {**at, "USD": Decimal("0.75")})
    #: 780 dollars at 0.75 are 585 pounds: Friday's 408.255 are 390, 18.255 fewer; the five
    #: that cost 200.125 pounds on Friday are 195, 5.125 fewer, and their 1.061 of costs are in
    #: this record, the first to count them
    assert (second.profit, second.costs.total) == (Decimal("-24.44"), Decimal("1.06"))
    assert (second.worth, second.counted) == (Decimal(585), 2)
    assert not any(halt.morning(tmp_path, mon).values()), "a morning that blocked nothing"
    shut = date(2025, 2, 17)  #: New York is shut, so U is owed no bar: the yardstick alone is
    assert day.trade(tmp_path, archive, broker, capital, shut, at) == ()
    assert [b.order_id for b in halt.morning(tmp_path, shut)[Blocker.UNREAD]] == [YARDSTICK.symbol]


def test_a_holding_whose_stop_was_lost_is_on_that_days_list_with_the_stop_to_put_back(
    tmp_path: Path,
) -> None:
    broker, room = Pretend(ARCHIVE, {}), Settings(Decimal(10_000))
    broker.open(DAYS[21])
    _trade(tmp_path, broker, DAYS[21])
    lost, more, half = (broker._stops[symbol] for symbol in "ACD")
    broker._faults["D"] = Fault.PARTIAL  #: half of D sold: what is left is the buy's
    book.send(tmp_path, broker, Sale("s-1", ARCHIVE_LINES["D"], half.shares), room)
    for symbol in "ABD":  #: by hand; and B's shares are not the book's, C's stop is for more
        broker.cancel_stop(symbol)
    broker.inject("B", 1)
    broker._stops["C"] = replace(more, shares=more.shares + 5)
    record = day.publish(tmp_path, MARKET, broker, room, DAYS[21])
    held, kept = book.positions(tmp_path), book.levels(tmp_path)
    assert kept[lost.order_id] == lost.level and record.mismatches == tuple("ABCD")
    assert held["D"] == half.shares - half.shares // 2, "D not half sold"
    put = "shares held, 0 under a stop at the broker; put back"
    assert [(b.order_id, b.reason) for b in halt.morning(tmp_path, DAYS[21])[Blocker.BOOK]] == [
        (stop.order_id, f"{s}: {held[s]} {put} {stop.order_id}, selling {held[s]} at {stop.level}")
        for s, stop in (("A", lost), ("D", half))
    ], "not told that day, told of shares the broker may not hold, or under another stop"
    broker.open(DAYS[22])  #: a session missed, A still bare: no list for a day nobody sent for
    book.record_rates(tmp_path, DAYS[22], {"GBP": Decimal(1)})
    day.publish(tmp_path, MARKET, broker, room, DAYS[22])
    assert halt.stopped(tmp_path, DAYS[22]) is None, "a list for a day whose orders never went"
