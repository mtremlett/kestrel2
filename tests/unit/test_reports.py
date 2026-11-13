"""What the paper broker reports: today's fills read exactly as the gateway gives them, the
desk's own under the broker's id and priced in the line's currency, and the desk's own
fills, orders and stops told from anyone else's."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal

import pytest
from test_paper import AAPL_STOP, ACCOUNTS, FEED, HELLO, READY, _wire

from desk import paper, reports
from desk.broker import Fill
from desk.lines import NO_TAX, Line
from desk.listing import Listing, Unlisted
from desk.reports import Execution, Fills, Orders

IITU, AAPL = Line("IITU", "LSE", "GBP", 1, NO_TAX), Line("AAPL", "US", "USD", 1, NO_TAX)
SMGB = Line("SMGB", "LSE", "GBP", 1, NO_TAX)
CENT = ((Decimal(0), Decimal("0.01")),)
LISTED: dict[str, Listing | Unlisted] = {
    "IITU": Listing(IITU, "212969319", "LSEETF", 100, CENT),  # priced in pence at the broker
    "AAPL": Listing(AAPL, "265598", "NASDAQ", 1, CENT),
    "SMGB": Unlisted(SMGB, "the broker lists 0 contracts under the name"),
}
#: Fills in the shape the real gateway gave on 13 November 2026 (twenty-one that day, all the
#: old desk's): the time on the exchange's own clock, the price as the broker writes it, each
#: fill's fee noted after them all. The account's code, the ids and the amounts are changed, the
#: client and reference made the desk's own (a buy in London, in pence, and a stop's sale), and
#: AAPL's local name, so that a reader taking it for the symbol is caught.
BOUGHT = (
    "11|1|2872|212969319|IITU|STK||0.0|||LSEETF|GBP|IITU|EUE2|0000e859.6553f2a1.01.01|"
    "20261113 09:22:06 MET|DU0000001|LSEETF|BOT|26|3755.00|1234567|222|0|26|3755.00|"
    "20261113-rsi2-IITU||||2"
).split("|")
SOLD = (
    "11|1|2852|265598|AAPL|STK||0.0|||IBKRATS|USD|AAPL.O|NMS|0000dc8f.6553f2a9.01.01|"
    "20261113 09:30:11 US/Eastern|DU0000001|IBKRATS|SLD|10|171.5|1234570|222|0|10|171.5|"
    "20261112-rsi2-AAPL-stop||||1"
).split("|")
UNSET = "1.7976931348623157E308"  #: the broker's own way of writing "no number"
FEE = ("59", "1", BOUGHT[14], "3.0", "GBP", UNSET, UNSET, "")
END = ("55", "1", "1")
DAY = date(2026, 11, 13)


def _made(*told: str, shares: int, price: str) -> Execution:
    """A fill of the desk's own client on the paper account that day."""
    made, ref, contract, symbol, at, clock = told
    when = datetime.fromisoformat(f"{DAY} {at}")
    amount = Decimal(shares), Decimal(price)
    return Execution(made, "222", ref, "DU0000001", contract, symbol, *amount, when, clock)


IN_LONDON = ("20261113-rsi2-IITU", "212969319", "IITU", "09:22:06", "MET")
IN_NEW_YORK = ("20261112-rsi2-AAPL-stop", "265598", "AAPL", "09:30:11", "US/Eastern")
BUY = _made(BOUGHT[14], *IN_LONDON, shares=26, price="3755.00")
SALE = _made(SOLD[14], *IN_NEW_YORK, shares=-10, price="171.5")
OURS = replace(AAPL_STOP, client="222")  # the desk's own stop: its client, its order id


def _but(fields: Sequence[str], at: int, value: str) -> list[str]:
    return [*fields[:at], value, *fields[at + 1 :]]


def _read(*messages: Sequence[str]) -> tuple[tuple[Execution, ...], list[bytes]]:
    sent: list[bytes] = []
    return reports.converse(_wire(HELLO, ACCOUNTS, READY, *messages), sent.append), sent


def test_todays_fills_are_read_as_the_gateway_gives_them_and_only_a_question_is_sent() -> None:
    # the gateway's next free number reads as the list's end does, but for its kind: no end
    fills, sent = _read(FEED, BOUGHT, READY, FEE, SOLD, END)
    assert fills == (BUY, SALE)
    # after the greeting and the start: every client's fills on the account, and no order
    assert sent[2:] == [_wire("7|3|1|0||||||".split("|")).getvalue()]
    assert _read(END)[0] == ()  # a day with no fill is an answer, and whole
    assert _read(BOUGHT, BOUGHT, END)[0] == (BUY, BUY)  # as given: whose it is comes after


def test_the_desks_own_fills_are_the_ledgers_priced_in_the_lines_currency() -> None:
    named = replace(BUY, symbol="iitu")  # a line is known by the broker's number for it
    later = replace(BUY, execution_id="0000e859.6553f2a1.02.01", shares=Decimal(-26))
    ledger = (
        # 3755 pence at the broker is 37.55 pounds on the desk's line
        Fill(BUY.execution_id, "20261113-rsi2-IITU", "IITU", 26, Decimal("37.55"), DAY),
        Fill(SALE.execution_id, "20261112-rsi2-AAPL-stop", "AAPL", -10, Decimal("171.5"), DAY),
        Fill(later.execution_id, "20261113-rsi2-IITU", "IITU", -26, Decimal("37.55"), DAY),
    )
    # each line's fills in the order made; New York's clock is not London's to be set against
    assert reports.fills((named, SALE, later), LISTED) == Fills(ledger, ())
    plain = reports.fills((replace(BUY, execution_id="A"), replace(BUY, execution_id="B")), LISTED)
    assert [fill.execution_id for fill in plain.ours] == ["A", "B"]  # no last part: two fills


@pytest.mark.parametrize(
    "theirs",
    [
        replace(BUY, client="31"),  # another program, though under an order id of the desk's
        replace(BUY, client="0"),  # a hand at the broker's own screen
        replace(BUY, ref=""),  # the desk's client, under no order id of the desk's
        replace(BUY, ref=" "),
        replace(BUY, client="2222"),
        # not the desk's to read: no line of its own, a part of a share, another clock
        replace(BUY, client="31", contract="999", shares=Decimal("0.5"), clock="Asia/Tokyo"),
    ],
)
def test_a_fill_that_is_not_the_desks_own_is_kept_apart_as_the_broker_gave_it(
    theirs: Execution,
) -> None:
    late = replace(SALE, client="31")
    told = reports.fills((theirs, SALE, late, late), LISTED)  # theirs to explain, twice or not
    assert told.others == (theirs, late, late) and [fill.symbol for fill in told.ours] == ["AAPL"]


@pytest.mark.parametrize(
    ("fills", "saying"),
    [
        ((replace(BUY, contract="999"),), "999"),  # the desk's own, on no line of the desk's
        ((replace(BUY, contract="458512497", symbol="SMGB"),), "SMGB"),  # a line now unlisted
        ((replace(BUY, shares=Decimal("25.5")),), "whole shares"),  # the desk orders whole shares
        # a day told on another clock than its exchange's may not be its session's day
        ((replace(BUY, clock="US/Eastern"),), "exchange's clock"),
        ((replace(SALE, clock="MET"),), "exchange's clock"),
        ((replace(BUY, clock="Asia/Tokyo"),), "exchange's clock"),
        # a line's fills out of the order made would close a sale against a buy not yet made
        ((BUY, replace(BUY, execution_id="B", made=datetime(2026, 11, 13, 9, 22, 5))), "before"),
        ((BUY, replace(BUY, execution_id="B", made=datetime(2026, 11, 12, 16, 0))), "before"),
        # one fill given twice, or a fill and the broker's correction of it: counted once only
        ((BUY, SALE, BUY), "0000e859.6553f2a1.01"),
        ((BUY, replace(BUY, execution_id="0000e859.6553f2a1.01.02")), "corrected"),
    ],
)
def test_a_fill_of_the_desks_own_that_it_cannot_give_whole_and_once_stops_the_reading(
    fills: tuple[Execution, ...], saying: str
) -> None:
    with pytest.raises(ValueError, match=saying):
        reports.fills((SALE, *fills), LISTED)


@pytest.mark.parametrize(
    ("messages", "error", "saying"),
    [
        ((BOUGHT,), ConnectionError, "hung up"),
        ((BOUGHT[:-1], END), ValueError, "shape"),
        (([*BOUGHT, ""], END), ValueError, "shape"),
        ((_but(BOUGHT, 1, "2"), END), ValueError, "does not read"),  # another question's answer
        ((_but(BOUGHT, 1, "-1"), END), ValueError, "does not read"),  # a fill told of unasked
        ((BOUGHT, ("55", "1", "2")), ValueError, "does not read"),
        ((BOUGHT, ("99", "1"), END), ValueError, "99"),
        ((BOUGHT, ("4", "2", "1", "321", "no such question", "")), ConnectionError, "321"),
        ((BOUGHT, ("4", "2", "-1", "1100", "lost", "")), ConnectionError, "1100"),
        ((_but(BOUGHT, 16, "UD654321"), END), paper.NotPaper, "UD654321"),
        ((_but(BOUGHT, 18, "SSHORT"), END), ValueError, "SSHORT"),
        ((_but(BOUGHT, 18, ""), END), ValueError, "cannot trust"),
        ((_but(BOUGHT, 15, "20261113-08:22:06"), END), ValueError, "20261113-08:22:06"),
        ((_but(BOUGHT, 15, "1794556807"), END), ValueError, "1794556807"),
        ((_but(BOUGHT, 15, "20261113"), END), ValueError, "cannot trust"),
        ((_but(BOUGHT, 15, ""), END), ValueError, "cannot trust"),
        ((_but(BOUGHT, 15, "20261113 09:22:06"), END), ValueError, "cannot trust"),  # no clock
        ((_but(BOUGHT, 15, "20261113 09:22:06 "), END), ValueError, "cannot trust"),
        ((_but(BOUGHT, 15, "20261113  09:22:06"), END), ValueError, "cannot trust"),
        ((_but(BOUGHT, 15, "20261113 09:22:06  MET"), END), ValueError, "cannot trust"),
        ((_but(BOUGHT, 15, "20261132 09:22:06 MET"), END), ValueError, "20261132"),  # no such day
        ((_but(BOUGHT, 15, "20261113 24:22:06 MET"), END), ValueError, "24:22:06"),
        ((_but(BOUGHT, 14, ""), END), ValueError, "cannot trust"),
        ((_but(BOUGHT, 19, "0"), END), ValueError, "cannot trust"),
        ((_but(BOUGHT, 19, "-26"), END), ValueError, "cannot trust"),
        ((_but(BOUGHT, 19, "NaN"), END), ValueError, "NaN"),
        ((_but(BOUGHT, 19, "1_0"), END), ValueError, "plain number"),
        ((_but(BOUGHT, 19, ""), END), ValueError, "plain number"),
        ((_but(BOUGHT, 20, "0.0"), END), ValueError, "cannot trust"),
        ((_but(BOUGHT, 20, "-3755.0"), END), ValueError, "cannot trust"),
        ((_but(BOUGHT, 20, "Infinity"), END), ValueError, "Infinity"),
        ((_but(BOUGHT, 20, UNSET), END), ValueError, "plain number"),
        ((_but(BOUGHT, 20, "3755."), END), ValueError, "plain number"),
        ((_but(BOUGHT, 20, "٣755"), END), ValueError, "plain number"),  # no digit of ours
    ],
)
def test_an_answer_the_desk_cannot_trust_stops_the_reading(
    messages: tuple[Sequence[str], ...], error: type[Exception], saying: str
) -> None:
    with pytest.raises(error, match=saying):
        _read(*messages)


def test_the_desks_own_orders_and_stops_are_told_from_anyone_elses() -> None:
    buying = replace(OURS, broker_id="8", contract="212969319", action="BUY", kind="MKT")
    limit = replace(OURS, broker_id="9", kind="STP LMT")  # to sell, but no plain stop
    covering = replace(OURS, broker_id="10", action="BUY")  # a stop, but to buy
    hand = replace(OURS, ref="", contract="999")  # the desk's client, no order id of the desk's
    part = replace(OURS, broker_id="11", state="Submitted", left=Decimal(4), symbol="aapl")
    # listed as open, but the broker is not holding it: refused, going, or its state unread
    idle = tuple(replace(OURS, broker_id=s, state=s) for s in ("Inactive", "PendingCancel", ""))
    resting = (AAPL_STOP, OURS, buying, hand, limit, part, covering, *idle)
    assert reports.orders(resting, LISTED) == Orders(
        # entry by entry, never added up; for the shares still to be sold; known by its number
        stops=(("AAPL", Decimal(10)), ("AAPL", Decimal(4))),
        unsettled=(buying, limit, covering, *idle),
        others=(AAPL_STOP, hand),  # another client's, though under an order id of the desk's
    )
    assert reports.orders((), LISTED) == Orders((), (), ())
    # the desk's own, stop or not, on no line the broker lists for it
    for unknown in (replace(OURS, contract="999"), replace(buying, contract="458512497")):
        with pytest.raises(ValueError, match=unknown.contract):
            reports.orders((unknown,), LISTED)


def test_the_fills_are_asked_through_the_one_door(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[bytes] = []
    wire = _wire(HELLO, ACCOUNTS, READY, BOUGHT, SOLD, END)
    monkeypatch.setattr(paper, "dial", lambda talk: talk(wire, sent.append))
    assert reports.read() == (BUY, SALE) and len(sent) == 3
