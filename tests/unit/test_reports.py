"""What the paper broker reports: today's fills read exactly as the gateway gives them, the
desk's own under the broker's id and priced in the line's currency, and the desk's own
fills, orders and stops told from anyone else's."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import date
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
#: Fills as the published client reads them in the door's one version: none has been made on
#: the paper account to copy. A buy of the desk's own in London, and its stop's sale in the US.
BOUGHT = (
    "11|1|7|212969319|IITU|STK||0.0|||LSEETF|GBP|IITU|EUE2|0000e0d5.6553f2a1.01.01|"
    "20261113 08:00:07 Europe/London|DU0000001|LSEETF|BOT|26|3755.0|1234567|222|0|26|3755.0|"
    "20261113-rsi2-IITU||||1"
).split("|")
SOLD = (
    "11|1|9|265598|AAPL|STK||0.0|||NASDAQ|USD|AAPL|NMS|0000e0d5.6553f2a9.01.01|"
    "20261113  14:31:02|DU0000001|NASDAQ|SLD|10|171.5|1234570|222|0|10|171.5|"
    "20261112-rsi2-AAPL-stop||||2"
).split("|")
FEE = ("59", "1", "0000e0d5.6553f2a1.01.01", "3.0", "GBP", "1.7976931348623157E308", "", "")
END = ("55", "1", "1")
DAY = date(2026, 11, 13)


def _made(part: str, ref: str, contract: str, symbol: str, shares: int, price: str) -> Execution:
    """A fill of the desk's own client on the paper account that day."""
    made = f"0000e0d5.{part}.01.01", "222", ref, "DU0000001", contract, symbol
    return Execution(*made, Decimal(shares), Decimal(price), DAY)


BUY = _made("6553f2a1", "20261113-rsi2-IITU", "212969319", "IITU", 26, "3755.0")
SALE = _made("6553f2a9", "20261112-rsi2-AAPL-stop", "265598", "AAPL", -10, "171.5")
OURS = replace(AAPL_STOP, client="222")  # the desk's own stop: its client, its order id


def _but(fields: Sequence[str], at: int, value: str) -> list[str]:
    return [*fields[:at], value, *fields[at + 1 :]]


def _read(*messages: Sequence[str]) -> tuple[tuple[Execution, ...], list[bytes]]:
    sent: list[bytes] = []
    return reports.converse(_wire(HELLO, ACCOUNTS, READY, *messages), sent.append), sent


def test_todays_fills_are_read_as_the_gateway_gives_them_and_only_a_question_is_sent() -> None:
    fills, sent = _read(FEED, BOUGHT, FEE, SOLD, END)
    assert fills == (BUY, SALE)
    # after the greeting and the start: every client's fills on the account, and no order
    assert sent[2:] == [_wire("7|3|1|0||||||".split("|")).getvalue()]
    assert _read(END)[0] == ()  # a day with no fill is an answer, and whole


def test_the_desks_own_fills_are_the_ledgers_priced_in_the_lines_currency() -> None:
    assert reports.fills((BUY, SALE), LISTED) == Fills(
        (
            # 3755 pence at the broker is 37.55 pounds on the desk's line
            Fill(BUY.execution_id, "20261113-rsi2-IITU", "IITU", 26, Decimal("37.55"), DAY),
            Fill(SALE.execution_id, "20261112-rsi2-AAPL-stop", "AAPL", -10, Decimal("171.5"), DAY),
        ),
        (),
    )


@pytest.mark.parametrize(
    "theirs",
    [
        replace(BUY, client="31"),  # another program, though under an order id of the desk's
        replace(BUY, client="0"),  # a hand at the broker's own screen
        replace(BUY, ref=""),  # the desk's client, under no order id of the desk's
        replace(BUY, ref=" "),
        replace(BUY, client="2222"),
        replace(BUY, client="31", contract="999", shares=Decimal("0.5")),  # not the desk's to read
    ],
)
def test_a_fill_that_is_not_the_desks_own_is_kept_apart_as_the_broker_gave_it(
    theirs: Execution,
) -> None:
    told = reports.fills((theirs, SALE), LISTED)
    assert told.others == (theirs,) and [fill.symbol for fill in told.ours] == ["AAPL"]


@pytest.mark.parametrize(
    ("fill", "saying"),
    [
        (replace(BUY, contract="999"), "999"),  # the desk's own, on no line of the desk's
        (replace(BUY, contract="458512497", symbol="SMGB"), "SMGB"),  # a line now unlisted
        (replace(BUY, shares=Decimal("25.5")), "25.5"),  # the desk orders whole shares
    ],
)
def test_a_fill_of_the_desks_own_that_it_cannot_give_whole_stops_the_reading(
    fill: Execution, saying: str
) -> None:
    with pytest.raises(ValueError, match=saying):
        reports.fills((SALE, fill), LISTED)


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
        ((_but(BOUGHT, 16, "U7654321"), END), paper.NotPaper, "U7654321"),
        ((_but(BOUGHT, 18, "SSHORT"), END), ValueError, "SSHORT"),
        ((_but(BOUGHT, 18, ""), END), ValueError, "cannot trust"),
        ((_but(BOUGHT, 15, "20261113-08:00:07"), END), ValueError, "20261113-08:00:07"),
        ((_but(BOUGHT, 15, "1794556807"), END), ValueError, "1794556807"),
        ((_but(BOUGHT, 15, "20261113"), END), ValueError, "cannot trust"),
        ((_but(BOUGHT, 15, ""), END), ValueError, "cannot trust"),
        ((_but(BOUGHT, 15, "20261332 08:00:07"), END), ValueError, "20261332|month"),
        ((_but(BOUGHT, 14, ""), END), ValueError, "cannot trust"),
        ((_but(BOUGHT, 19, "0"), END), ValueError, "cannot trust"),
        ((_but(BOUGHT, 19, "-26"), END), ValueError, "cannot trust"),
        ((_but(BOUGHT, 19, "NaN"), END), ValueError, "NaN"),
        ((_but(BOUGHT, 19, "Infinity"), END), ValueError, "Infinity"),
        ((_but(BOUGHT, 20, "0.0"), END), ValueError, "cannot trust"),
        ((_but(BOUGHT, 20, "-3755.0"), END), ValueError, "cannot trust"),
        ((_but(BOUGHT, 20, "NaN"), END), ValueError, "NaN"),
        ((_but(BOUGHT, 20, "Infinity"), END), ValueError, "Infinity"),
        # one fill given twice, or a fill and the broker's correction of it: counted once only
        ((BOUGHT, SOLD, BOUGHT, END), ValueError, "0000e0d5.6553f2a1.01"),
        ((BOUGHT, _but(BOUGHT, 14, "0000e0d5.6553f2a1.01.02"), END), ValueError, "corrected"),
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
    hand = replace(OURS, ref="")  # the desk's client under no order id of the desk's
    more = replace(OURS, broker_id="10", shares=Decimal(4))
    assert reports.orders((AAPL_STOP, OURS, buying, hand, limit, more), LISTED) == Orders(
        stops=(("AAPL", Decimal(10)), ("AAPL", Decimal(4))),  # entry by entry, never added up
        working=(buying, limit),
        others=(AAPL_STOP, hand),  # another client's, though under an order id of the desk's
    )
    assert reports.orders((), LISTED) == Orders((), (), ())
    for contract in ("999", "458512497"):  # the desk's own, on no line the broker lists for it
        with pytest.raises(ValueError, match=contract):
            reports.orders((replace(OURS, contract=contract),), LISTED)


def test_the_fills_are_asked_through_the_one_door(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[bytes] = []
    wire = _wire(HELLO, ACCOUNTS, READY, SOLD, END)
    monkeypatch.setattr(paper, "dial", lambda talk: talk(wire, sent.append))
    assert reports.read() == (SALE,) and len(sent) == 3
