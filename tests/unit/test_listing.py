"""Each line as the paper broker lists it, an unlisted line named, a price put on its step."""

from __future__ import annotations

import io
import struct
from collections.abc import Sequence
from decimal import Decimal

import pytest

from desk import listing, paper
from desk.lines import Line
from desk.listing import Listing, Unlisted

IITU, AAPL = Line("IITU", "LSE", "GBP", 1), Line("AAPL", "US", "USD", 1)
OPEN = (("176", "20261113 19:31:25 Greenwich Mean Time"), ("15", "1", "DU0000001"), ("9", "1", "1"))
#: Answers as the real gateway sent them on 13 November 2026, each question's number made the
#: test's, the long lists (order kinds, hours, AAPL's 27 exchanges) cut short, and IITU's
#: rules turned round so that the one where an order goes differs from the other exchanges'.
IITU_IS = (
    "10|0|IITU|STK||0||SMART|GBP|IITU|EUE2|EUE2|212969319|0.0005||MKT,STP|"
    "SMART,LSEETF,EUIBSI,TRWBUKETF|100|0|ISHARES S&P 500 IT SECTOR|LSEETF|||||MET|"
    "20261113:0900-20261113:1850|20261113:0900-20261113:1750|||1|ISIN|IE00B3WJKG14|3|||"
    "3051,984,984,984||ETF|0.0001|0.0001|1"
).split("|")
AAPL_IS = (
    "10|1|AAPL|STK||0||SMART|USD|AAPL|NMS|NMS|265598|0.01||MKT,STP|SMART,NYSE,NASDAQ|1|0|"
    "APPLE INC|NASDAQ||Technology|Computers|Computers|US/Eastern|20261112:0400-20261112:2000|"
    "20261112:0930-20261112:1600|||1|ISIN|US0378331005|1|||4563,4563,4563||COMMON|0.0001|"
    "0.0001|40"
).split("|")
PENCE = "93 3051 5 0 0.0005 0.1 0.001 5 0.0025 10 0.005 25 0.01".split()
CENTS = "93 4563 1 0 0.01".split()
ENDS = (("52", "1", "0"), ("52", "1", "1"))
UNKNOWN = ("4", "2", "0", "200", "No security definition has been found for the request", "")
FEED = ("4", "2", "-1", "2158", "Sec-def data farm connection is OK:secdefeu", "")
RULE = [Decimal(n) for n in "0 0.0005 0.1 0.001 5 0.0025 10 0.005 25 0.01".split()]
IN_PENCE = Listing(IITU, "212969319", "LSEETF", 100, tuple(zip(RULE[::2], RULE[1::2], strict=True)))
IN_CENTS = Listing(AAPL, "265598", "NASDAQ", 1, ((Decimal(0), Decimal("0.01")),))
REST = (AAPL_IS, ENDS[1], CENTS)  #: the second line's answers, whatever the first line's were


def _frame(*messages: Sequence[str]) -> bytes:
    bodies = ("".join(f"{field}\0" for field in fields).encode() for fields in messages)
    return b"".join(struct.pack(">I", len(body)) + body for body in bodies)


def _read(*messages: Sequence[str]) -> tuple[dict[str, Listing | Unlisted], list[bytes]]:
    sent: list[bytes] = []
    wire = io.BytesIO(_frame(*OPEN, *messages))
    return listing.converse(wire, sent.append, (IITU, AAPL)), sent


def _but(fields: Sequence[str], at: int, value: str) -> list[str]:
    return [*fields[:at], value, *fields[at + 1 :]]


def test_each_line_is_read_as_the_gateway_gives_it_and_only_questions_are_sent() -> None:
    listed, sent = _read(FEED, IITU_IS, ENDS[0], FEED, PENCE, *REST)
    assert listed == {"IITU": IN_PENCE, "AAPL": IN_CENTS}
    assert sent[2:] == [  # after the greeting and the start: a line, its price steps, the next
        _frame("9|8|0|0|IITU|STK||0.0|||SMART||GBP|||0|||".split("|")),
        _frame(("91", "3051")),  # the steps where the order will go, not another exchange's
        _frame("9|8|1|0|AAPL|STK||0.0|||SMART||USD|||0|||".split("|")),
        _frame(("91", "4563")),
    ]


@pytest.mark.parametrize(
    ("known", "price", "taken"),
    [
        (IN_PENCE, "37.556", "3755"),  # pounds at the desk, whole pence at the broker
        (IN_PENCE, "1.3979", "139.7"),  # a cheaper line's finer step
        (IN_PENCE, "5", "500"),
        (IN_PENCE, "4.9999", "499.9"),  # just under a change of step
        (IN_PENCE, "7.4474", "744.5"),
        (IN_PENCE, "0.0507", "5.05"),
        (IN_CENTS, "171.519", "171.51"),
    ],
)
def test_a_price_is_put_down_onto_the_brokers_step_in_the_brokers_unit(
    known: Listing, price: str, taken: str
) -> None:
    assert known.floor(Decimal(price)) == Decimal(taken)


@pytest.mark.parametrize("price", ["0.0004", "0", "-1"])
def test_a_price_with_no_step_at_or_below_it_is_refused(price: str) -> None:
    with pytest.raises(ValueError, match="IITU"):
        IN_PENCE.floor(Decimal(price))


@pytest.mark.parametrize(
    ("answers", "reason"),
    [
        ((UNKNOWN,), "No security definition"),
        ((IITU_IS, _but(IITU_IS, 12, "999"), ENDS[0]), "2 contracts"),
        ((ENDS[0],), "0 contracts"),
        ((_but(IITU_IS, 20, "AEB"), ENDS[0]), "on AEB"),
        ((_but(IITU_IS, 8, "EUR"), ENDS[0]), "EUR"),
        ((_but(IITU_IS, 3, "CFD"), ENDS[0]), "CFD"),
        ((_but(IITU_IS, 2, "IITV"), ENDS[0]), "IITV"),
    ],
)
def test_a_line_the_broker_does_not_list_as_the_desks_is_named_and_the_rest_carry_on(
    answers: tuple[Sequence[str], ...], reason: str
) -> None:
    listed, sent = _read(*answers, *REST)
    unlisted = listed["IITU"]
    assert isinstance(unlisted, Unlisted) and unlisted.line == IITU and reason in unlisted.reason
    assert listed["AAPL"] == IN_CENTS and len(sent) == 5  # no steps asked for a line unlisted


@pytest.mark.parametrize(
    ("messages", "error", "saying"),
    [
        ((), ConnectionError, "hung up"),
        ((IITU_IS, ENDS[0]), ConnectionError, "hung up"),
        ((_but(IITU_IS, 1, "1"),), ValueError, "does not read"),
        ((IITU_IS, ENDS[1]), ValueError, "does not read"),
        ((IITU_IS[:-1], ENDS[0]), ValueError, "shape"),
        (([*IITU_IS, ""], ENDS[0]), ValueError, "shape"),
        ((IITU_IS[:30], ENDS[0]), ValueError, "shape"),
        ((_but(IITU_IS, 36, "3051,984"), ENDS[0]), ValueError, "shorter"),
        ((_but(IITU_IS, 17, "0"), ENDS[0], PENCE), ValueError, "steps"),
        ((IITU_IS, ENDS[0], _but(PENCE, 1, "984")), ValueError, "does not read"),
        ((IITU_IS, ENDS[0], PENCE[:-1]), ValueError, "shape"),
        ((IITU_IS, ENDS[0], PENCE[:2]), ValueError, "shape"),
        ((IITU_IS, ENDS[0], "93 3051 1 5 0.01".split()), ValueError, "steps"),
        ((IITU_IS, ENDS[0], "93 3051 2 0 0.01 0 0.02".split()), ValueError, "steps"),
        ((IITU_IS, ENDS[0], "93 3051 2 0 0.01 5 0".split()), ValueError, "steps"),
        ((IITU_IS, ENDS[0], "93 3051 0".split()), ValueError, "steps"),
        ((_but(UNKNOWN, 3, "321"),), ConnectionError, "321"),
        ((_but(UNKNOWN, 2, "1"),), ConnectionError, "200"),
        ((IITU_IS, ENDS[0], ("4", "2", "-1", "322", "no such rule", "")), ConnectionError, "322"),
        ((("15", "1", "U7654321"),), paper.NotPaper, "U7654321"),
    ],
)
def test_an_answer_the_desk_cannot_trust_stops_the_reading(
    messages: tuple[Sequence[str], ...], error: type[Exception], saying: str
) -> None:
    with pytest.raises(error, match=saying):
        _read(*messages)


def test_the_lines_are_asked_through_the_one_door(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[bytes] = []
    wire = io.BytesIO(_frame(*OPEN, IITU_IS, ENDS[0], PENCE))
    monkeypatch.setattr(paper, "dial", lambda talk: talk(wire, sent.append))
    assert listing.read((IITU,)) == {"IITU": IN_PENCE} and len(sent) == 4
