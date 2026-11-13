"""The paper account behind the send path: the money path's own questions (the ledger, the
reconciliation, the kill switch) answered from what the gateway gives, the desk's own told
from anyone else's, and nothing sent but questions and the kill switch's cancels."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import BinaryIO

import pytest
from test_paper import ACCOUNTS, ENDS, FLAT, HELLO, READY, STOP, _but, _wire
from test_reports import BOUGHT, BUY, CUT, DONE, END, FEE, IITU, LISTED

from desk import book, kill, paper, placing
from desk.broker import Broker, Fill, Report
from desk.orders import Sale

ID = "20261113-rsi2-IITU"
HELD = "61 3 DU0000001 212969319 IITU STK  0.0   LSEETF GBP IITU EUE2 26 37.5".split(" ")
FILL = Fill(BUY.execution_id, ID, "IITU", 26, Decimal("37.55"), BUY.made.date())
#: What the desk asks in a conversation, after its greeting and its start: of the account
#: (its holdings; every open order), of the day's ended orders, of the day's fills.
ACCOUNT = _wire(("61", "1"), ("16", "1")).getvalue()
ENDED, FILLS = _wire(("99", "0")).getvalue(), _wire("7|3|1|0||||||".split("|")).getvalue()
STOPPED = _but(_but(BOUGHT, 18, "SLD"), 26, f"{ID}-stop")  # the desk's stop on the line, sold
AFTER = _but(DONE, 22, f"{ID}-stop")  # and that stop's own order, ended: not the order asked of
AT = datetime(2026, 11, 16, 8, 5, tzinfo=UTC)


def _order(
    number: str, deal: str, ref: str, state: str, left: int = 26, client: str = "222"
) -> tuple[Sequence[str], Sequence[str]]:
    """An order open on IITU and the broker's last word of it: deal is its action and kind."""
    said = (number, "212969319", *deal.split(), ref, client, f"100{number}")
    order: dict[int, str] = dict(zip((1, 2, 13, 15, 23, 24, 25), said, strict=True))
    status = ("3", number, state, "0", str(left), "0", f"100{number}", "0", "0", client, "", "0")
    return [order.get(n, field) for n, field in enumerate(STOP)], status


def _account(holdings: Sequence[Sequence[str]], *orders: Sequence[str]) -> list[Sequence[str]]:
    return [*holdings, ENDS[0], *orders, ENDS[1]]


def _gateway(patch: pytest.MonkeyPatch, *answers: Sequence[Sequence[str]]) -> list[bytes]:
    """A gateway that answers each conversation the desk opens with the next of answers, and
    none after them; what the desk sent in each, after its greeting and its start."""
    left, sent = list(answers), list[bytes]()

    def dial(talk: Callable[[BinaryIO, paper.Send], object]) -> object:
        said: list[bytes] = []
        try:
            return talk(_wire(HELLO, ACCOUNTS, READY, *left.pop(0)), said.append)
        finally:
            sent.append(b"".join(said[2:]))

    patch.setattr(paper, "dial", dial)
    return sent


PROTECTED = _account([HELD, FLAT], *_order("7", "SELL STP", f"{ID}-stop", "PreSubmitted"))


def test_the_book_is_reconciled_with_the_paper_account_by_questions_alone(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    broker: Broker = placing.Paper(LISTED)
    # the fills, then the stops, then the holdings: one conversation each, read afresh
    sent = _gateway(monkeypatch, [BOUGHT, END], PROTECTED, PROTECTED)
    assert book.reconcile(tmp_path, broker) == ()  # a line is known by its symbol alone
    assert book.fills(tmp_path) == (FILL,) and sent == [FILLS, ACCOUNT, ACCOUNT]
    theirs = _account([], *_order("7", "SELL STP", f"{ID}-stop", "PreSubmitted", client="31"))
    short = _order("7", "SELL STP", f"{ID}-stop", "Submitted", left=20)
    _gateway(monkeypatch, theirs, [END], theirs, _account([HELD, _but(HELD, 11, "EUR")]))
    assert broker.stops() == ()  # another client's stop protects nothing of the desk's
    # no stop on the line; and its name in another currency is no line of the desk's
    assert book.reconcile(tmp_path, broker) == ("IITU", "IITU STK EUR")
    _gateway(monkeypatch, _account([], *short, *short), _account([HELD, HELD]))
    assert broker.stops() == (("IITU", 20), ("IITU", 20))  # entry by entry, never added up
    assert broker.holdings() == (("IITU", 26), ("IITU", 26))
    sent = _gateway(monkeypatch)
    with pytest.raises(NotImplementedError, match="no order is sent"):
        broker.place(Sale(ID, IITU, 26))  # placing is not built: nothing reaches the gateway
    assert sent == []


@pytest.mark.parametrize(
    ("orders", "ended", "fills", "report"),
    [
        ((), (), (), None),  # the broker tells nothing of it: never received
        # someone else's order and fill under the desk's id, and the desk's stop under its own
        (_order("8", "BUY MKT", ID, "Submitted", client="31"), (), (_but(BOUGHT, 22, "31"),), None),
        (_order("7", "SELL STP", f"{ID}-stop", "PendingSubmit"), (AFTER,), (STOPPED,), None),
        (_order("8", "BUY MKT", ID, "Submitted", 16), (), (), ((), "Submitted, 16 shares still")),
        (_order("8", "BUY MKT", ID, "Inactive"), (), (BOUGHT,), ((FILL,), "Inactive, 26 shares")),
        ((), (DONE,), (BOUGHT,), ((FILL,), None)),  # ended, filled whole, and its fills say so
        ((), (DONE,), (_but(BOUGHT, 18, "SLD"),), ((replace(FILL, quantity=-26),), None)),  # a sale
        ((), (CUT,), (), ((), "Cancelled, 10 shares filled and 16 not; its fills today come to 0")),
        ((), (DONE,), (), ((), "Filled, 26 shares filled and 0 not; its fills today come to 0")),
        ((), (DONE, DONE), (BOUGHT,), ((FILL,), "Filled, 26 shares filled and 0 not; Filled")),
        ((), (_but(DONE, 13, "4"),), (BOUGHT,), ((FILL,), "Filled, 26 shares filled and 4 not")),
        ((), (_but(DONE, 87, "0"),), (), ((), "Filled, 0 shares filled and 0 not")),
        (_order("8", "BUY MKT", ID, "Filled", 0), (DONE,), (BOUGHT,), ((FILL,), "Filled, 0 sh")),
        ((), (), (BOUGHT,), ((FILL,), "nothing of the order; its fills today come to 26")),
    ],
)
def test_what_the_broker_did_with_an_order_is_told_from_its_orders_then_its_fills(
    monkeypatch: pytest.MonkeyPatch,
    orders: Sequence[Sequence[str]],
    ended: Sequence[Sequence[str]],
    fills: Sequence[Sequence[str]],
    report: tuple[tuple[Fill, ...], str | None] | None,
) -> None:
    # the open orders are read before the fills: one filling between is never taken as unknown
    sent = _gateway(monkeypatch, _account([], *orders), [*ended, ("102",)], [*fills, END])
    told = placing.Paper(LISTED).report(ID)
    assert sent == [ACCOUNT, ENDED, FILLS]
    if report is None or report[1] is None:
        assert told == (None if report is None else Report(ID, report[0], None))
    else:
        assert told is not None and told.fills == report[0]
        assert told.reason is not None and told.reason.startswith(f"{ID}: the broker says ")
        assert report[1] in told.reason


WORKING = _account(
    [HELD],
    *_order("7", "SELL STP", f"{ID}-stop", "PreSubmitted"),  # the stop on what is held stays
    *_order("8", "BUY MKT", "a", "Submitted"),
    *_order("8", "BUY MKT", "b", "Submitted", client="31"),  # no one else's is touched
    *_order("9", "SELL MKT", "c", "PreSubmitted"),
    *_order("10", "SELL STP", "d", "PendingSubmit"),  # a stop to sell is never cancelled
    *_order("11", "BUY MKT", "e", "Filled", 0),  # listed, but over
    *_order("12", "BUY LMT", "f", "Inactive"),
)
GONE = (
    _order("8", "BUY MKT", "b", "Filled", client="31")[1],  # theirs, of the same number
    _order("7", "SELL STP", f"{ID}-stop", "Filled", 0)[1],  # the desk's stop, sold meanwhile
    *_order("8", "BUY MKT", "a", "PendingCancel"),
    ("4", "2", "8", "202", "Order Canceled - reason:", ""),
    _order("12", "BUY LMT", "f", "ApiCancelled")[1],
    _but(BOUGHT, 1, "-1"),  # a fill told unasked, and its fee: the day's fills give them
    FEE,
    _order("9", "SELL MKT", "c", "Filled", 0)[1],  # it filled before the cancel reached it
    _order("8", "BUY MKT", "a", "Cancelled")[1],
)
CANCELS = _wire(*(("4", "1", number, "") for number in ("8", "9", "12"))).getvalue()


def test_the_kill_switch_cancels_the_desks_own_working_orders_and_names_each_once_cancelled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    broker = placing.Paper(LISTED)
    sent = _gateway(monkeypatch, WORKING, GONE, [BOUGHT, END], PROTECTED, PROTECTED)
    said = kill.pull(tmp_path, broker, AT, "the paper account's own drill")
    assert said.cancelled == ("a", "f") and said.differ == () and said.held == (("IITU", 26),)
    assert sent == [ACCOUNT, CANCELS, FILLS, ACCOUNT, ACCOUNT]
    sent = _gateway(monkeypatch, PROTECTED)  # none working: none named, and nothing is sent
    assert broker.cancel() == () and sent == [ACCOUNT]


def test_a_cancel_not_confirmed_whole_is_an_error(monkeypatch: pytest.MonkeyPatch) -> None:
    for answer, error, saying in [
        (GONE[:-1], ConnectionError, "hung up"),  # not every one is known to be over
        ([("4", "2", "-1", "1100", "lost", "")], ConnectionError, "1100"),
        ([GONE[-1][:-1]], ValueError, "shape"),
        ([("4", "2", "7", "202", "Order Canceled - reason:", "")], ConnectionError, "202"),
        ([("99", "1")], ValueError, "99"),
    ]:
        sent = _gateway(monkeypatch, WORKING, answer)
        with pytest.raises(error, match=saying):
            placing.Paper(LISTED).cancel()
        assert sent == [ACCOUNT, CANCELS]
    # a cancel refused is settled by the account read again: over before the cancel, or working
    refusal = ("4", "2", "9", "10148", "cannot be cancelled, state: Filled", "")
    answer = [refusal, GONE[-1], _order("12", "BUY LMT", "f", "Cancelled")[1]]
    over = _account([HELD], *PROTECTED[3:5], *_order("9", "SELL MKT", "c", "Filled", 0))
    sent = _gateway(monkeypatch, WORKING, answer, over, WORKING, answer, WORKING)
    assert placing.Paper(LISTED).cancel() == ("a", "f")
    with pytest.raises(placing.NotCancelled, match="c .10148: cannot be cancelled"):
        placing.Paper(LISTED).cancel()
    assert sent == [ACCOUNT, CANCELS, ACCOUNT] * 2
