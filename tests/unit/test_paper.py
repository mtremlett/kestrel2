"""The paper broker's door: the account is read exactly as the gateway gives it, only a
paper account is read at all, and every difference from the desk's book is named."""

from __future__ import annotations

import io
import struct
from collections.abc import Sequence
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book, paper
from desk.lines import Line
from desk.paper import Account, Holding, Resting

LINES = (Line("AAPL", "US", "USD", 1), Line("SMGB", "LSE", "GBP", 1))
#: Messages as the real gateway sent them on 13 November 2026, the account's code changed.
HELLO = ("176", "20261113 17:42:38 Greenwich Mean Time")
ACCOUNTS, READY = ("15", "1", "DU0000001"), ("9", "1", "1")
FEED = ("4", "2", "-1", "2104", "Market data farm connection is OK:eufarm", "")
FLAT = "61 3 DU0000001 265598 AAPL STK  0.0   NASDAQ USD AAPL NMS 0 0.0".split(" ")
HELD = "61 3 DU0000001 458512497 SMGB STK  0.0   LSEETF GBP SMGB EUE2 25 31.5".split(" ")
#: An open order as the published client reads it; no order rested on the account to copy.
STOP = (
    "5 7 265598 AAPL STK  0 ?  SMART USD AAPL NMS SELL 10 STP 0.0 171.5 GTC  DU0000001  0"
    "  31 1234567 0 0 0".split(" ")
)
STATUS = ("3", "7", "PreSubmitted", "0", "10", "0", "1234567", "0", "0", "31", "", "0")
ENDS = (("62", "1"), ("53", "1"))
SMGB = Holding("DU0000001", "SMGB", "STK", "GBP", Decimal(25))
AAPL_STOP = Resting("1234567", "31", "DU0000001", "AAPL", "SELL", Decimal(10), "STP")


def _wire(*messages: Sequence[str]) -> io.BytesIO:
    """What the gateway sends: each message's length, then its fields ended by a zero byte."""
    bodies = ("".join(f"{field}\0" for field in fields).encode() for fields in messages)
    return io.BytesIO(b"".join(struct.pack(">I", len(body)) + body for body in bodies))


def _read(*messages: Sequence[str]) -> tuple[Account, list[bytes]]:
    sent: list[bytes] = []
    return paper.converse(_wire(HELLO, *messages), sent.append), sent


def test_the_account_is_read_as_the_gateway_gives_it_and_nothing_else_is_sent() -> None:
    account, sent = _read(ACCOUNTS, FEED, READY, FEED, FLAT, HELD, ENDS[0], STOP, STATUS, ENDS[1])
    assert account == Account(
        (Holding("DU0000001", "AAPL", "STK", "USD", Decimal(0)), SMGB), (AAPL_STOP,)
    )
    assert sent == [
        b"API\x00\x00\x00\x00\x04v176",  # the one version offered
        b"\x00\x00\x00\x0a71\x002\x00222\x00\x00",  # start, as the desk's own client
        b"\x00\x00\x00\x0561\x001\x00\x00\x00\x00\x0516\x001\x00",  # positions; open orders
    ]


@pytest.mark.parametrize("codes", ["U7654321", "DU0000001,U7654321"])
def test_an_account_that_is_not_a_paper_one_is_asked_nothing(codes: str) -> None:
    sent: list[bytes] = []
    with pytest.raises(paper.NotPaper, match="U7654321"):
        paper.converse(_wire(HELLO, ("15", "1", codes), READY, *ENDS), sent.append)
    assert len(sent) == 2  # the greeting and the start: no question about the account


@pytest.mark.parametrize(
    ("messages", "error", "saying"),
    [
        ((), ConnectionError, "hung up"),
        ((ACCOUNTS, READY, FLAT), ConnectionError, "hung up"),
        ((("4", "2", "-1", "326", "client id is already in use", ""),), ConnectionError, "326"),
        ((ACCOUNTS, READY, ("4", "2", "-1", "1100", "lost", "")), ConnectionError, "1100"),
        ((ACCOUNTS, ("99", "1")), ValueError, "99"),
        ((ACCOUNTS, READY, FLAT[:-1]), ValueError, "AAPL"),
        ((ACCOUNTS, READY, STOP[:25]), ValueError, "AAPL"),
        ((ACCOUNTS, READY, [*STOP[:13], "SSHORT", *STOP[14:]]), ValueError, "SSHORT"),
        ((ACCOUNTS, READY, [*FLAT[:2], "U7654321", *FLAT[3:]]), paper.NotPaper, "U7654321"),
        ((ACCOUNTS, READY, [*STOP[:20], "U7654321", *STOP[21:]]), paper.NotPaper, "U7654321"),
    ],
)
def test_an_answer_the_desk_cannot_trust_stops_the_reading(
    messages: tuple[Sequence[str], ...], error: type[Exception], saying: str
) -> None:
    with pytest.raises(error, match=saying):
        _read(*messages)


def test_another_version_of_the_gateways_language_is_refused() -> None:
    with pytest.raises(ValueError, match="178"):
        paper.converse(_wire(("178", HELLO[1]), ACCOUNTS, READY, *ENDS), lambda _: None)


def test_half_a_message_is_a_gateway_that_hung_up() -> None:
    with pytest.raises(ConnectionError, match="hung up"):
        paper.converse(io.BytesIO(_wire(HELLO, ACCOUNTS).getvalue()[:-3]), lambda _: None)


def test_a_book_that_is_the_brokers_is_quiet() -> None:
    flat = Holding("DU0000001", "AAPL", "STK", "USD", Decimal(0))
    assert paper.quiet(Account((SMGB, flat), ()), {"SMGB": 25}, LINES) == ()
    parts = (
        Holding("DU0000001", "SMGB", "STK", "GBP", Decimal(20)),
        replace(SMGB, shares=Decimal(5)),
    )
    assert paper.quiet(Account(parts, ()), {"SMGB": 25}, LINES) == ()


@pytest.mark.parametrize(
    ("account", "held", "named"),
    [
        (Account((SMGB,), ()), {}, "SMGB STK GBP: the broker holds 25, the desk's book 0"),
        (Account((), ()), {"SMGB": 25}, "SMGB STK GBP: the broker holds 0, the desk's book 25"),
        (
            Account((SMGB,), ()),
            {"SMGB": 24},
            "SMGB STK GBP: the broker holds 25, the desk's book 24",
        ),
        (
            Account((Holding("DU0000001", "SMGB", "STK", "EUR", Decimal(25)),), ()),
            {"SMGB": 25},
            "SMGB STK EUR: the broker holds 25, the desk's book 0",
        ),
        (
            Account((Holding("DU0000001", "SMGB", "CFD", "GBP", Decimal("0.5")),), ()),
            {},
            "SMGB CFD GBP: the broker holds 0.5, the desk's book 0",
        ),
        (
            Account((), (AAPL_STOP,)),
            {},
            "AAPL: an order resting at the broker to SELL 10 (STP, the broker's id 1234567, "
            "client 31)",
        ),
    ],
)
def test_every_difference_from_the_book_is_named(
    account: Account, held: dict[str, int], named: str
) -> None:
    assert named in paper.quiet(account, held, LINES)


def test_a_held_line_the_desk_was_not_given_is_refused() -> None:
    with pytest.raises(ValueError, match="XXXX"):
        paper.quiet(Account((), ()), {"XXXX": 1}, LINES)


def test_the_check_reads_the_desks_own_ledger(tmp_path: Path) -> None:
    rows = (",".join(book.COLUMNS), "X1,20251114-rsi2-SMGB,SMGB,25,31.5,2025-11-14")
    (tmp_path / book.LEDGER).write_text("\n".join(rows), encoding="utf-8")
    assert paper.check(tmp_path, lambda: Account((SMGB,), ())) == ()
    assert len(paper.check(tmp_path, lambda: Account((SMGB,), (AAPL_STOP,)))) == 1
    assert len(paper.check(tmp_path, lambda: Account((), ()))) == 1
