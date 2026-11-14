"""The paper account behind the send path: the money path's own questions answered from what
the gateway gives, the desk's own told from anyone else's; and an order sent once, on a clear
day, a buy with its stop, the line left under one stop of the desk's for the shares held."""

from __future__ import annotations

import io
from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import BinaryIO
from unittest.mock import Mock

import pytest
from test_paper import ACCOUNTS, ENDS, FLAT, HELLO, STOP, _but, _wire
from test_reports import AAPL, BOUGHT, BUY, CUT, DONE, END, FEE, IITU, LISTED, SMGB

from desk import book, kill, paper, placing
from desk.broker import Broker, Disconnected, Fill, Report
from desk.orders import Order, Refused, Sale

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
NEXT = ("9", "1", "41")  # the gateway, ready: the number its next order goes under
Said = Sequence[Sequence[str]]  # what the gateway says in one conversation


def _order(
    number: str, deal: str, ref: str, state: str, left: int = 26, client: str = "222"
) -> tuple[Sequence[str], Sequence[str]]:
    """An order open on IITU and the broker's last word of it: deal is its action, kind, level."""
    action, kind, *level = deal.split()
    said = (number, "212969319", action, kind, *(level or ["171.5"]), ref, client, f"100{number}")
    order: dict[int, str] = dict(zip((1, 2, 13, 15, 17, 23, 24, 25), said, strict=True))
    status = ("3", number, state, "0", str(left), "0", f"100{number}", "0", "0", client, "", "0")
    return [order.get(n, field) for n, field in enumerate(STOP)], status


def _account(holdings: Sequence[Sequence[str]], *orders: Sequence[str]) -> list[Sequence[str]]:
    return [*holdings, ENDS[0], *orders, ENDS[1]]


class _Silent(io.BytesIO):
    """A gateway that has said its last and does not hang up: the door's wait runs out."""

    def read(self, size: int | None = -1) -> bytes:
        if self.tell() == len(self.getvalue()):
            raise TimeoutError("timed out")
        return super().read(size)


def _gateway(
    patch: pytest.MonkeyPatch, *answers: Sequence[Sequence[str]], silent: bool = False
) -> list[bytes]:
    """A gateway that answers each conversation the desk opens with the next of answers, and
    none after them; what the desk sent in each, after its greeting and its start. Its
    answer given, it hangs up; or, silent, says no more and does not."""
    left, sent = list(answers), list[bytes]()

    def dial(talk: Callable[[BinaryIO, paper.Send], object]) -> object:
        said: list[bytes] = []
        wire = _wire(HELLO, ACCOUNTS, NEXT, *left.pop(0))
        try:
            return talk(_Silent(wire.getvalue()) if silent else wire, said.append)
        finally:
            sent.append(b"".join(said[2:]))

    patch.setattr(paper, "dial", dial)
    return sent


def _paper(root: Path = Path("unread"), at: datetime = AT) -> placing.Paper:
    return placing.Paper(LISTED, root, lambda: at)


def _ready(root: Path) -> Path:
    """A desk whose kill switch was drilled, and whose check came back clean today."""
    book.turn(root, book.Switch.DRILLED, AT, "every promise kept")
    (root / "checks.csv").write_text(f"at,result,found\n{AT.isoformat()},clean\n", "utf-8")
    return root


PROTECTED = _account([HELD, FLAT], *_order("7", "SELL STP", f"{ID}-stop", "PreSubmitted"))


def test_the_book_is_reconciled_with_the_paper_account_by_questions_alone(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    broker: Broker = _paper()
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
    told = _paper().report(ID)
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
    ("4", "2", "12", "10148", "cannot be cancelled, state: Cancelled", ""),  # it already is
    _but(BOUGHT, 1, "-1"),  # a fill told unasked, and its fee: the day's fills give them
    FEE,
    _order("9", "SELL MKT", "c", "Filled", 0)[1],  # it filled before the cancel reached it
    _order("8", "BUY MKT", "a", "Cancelled")[1],
)
CANCELS = _wire(*(("4", "1", number, "") for number in ("8", "9", "12"))).getvalue()


def test_the_kill_switch_cancels_the_desks_own_working_orders_and_names_each_once_cancelled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    broker = _paper()
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
        # news that another order was cancelled is no fault, and no last word of these
        ([("4", "2", "7", "202", "Order Canceled - reason:", "")], ConnectionError, "hung up"),
        ([("99", "1")], ValueError, "99"),
    ]:
        sent = _gateway(monkeypatch, WORKING, answer)
        with pytest.raises(error, match=saying):
            _paper().cancel()
        assert sent == [ACCOUNT, CANCELS]
    # a cancel refused is settled by the account read again: over before the cancel, or working
    refusal = ("4", "2", "9", "10148", "cannot be cancelled, state: Filled", "")
    answer = [refusal, GONE[-1], _order("12", "BUY LMT", "f", "Cancelled")[1]]
    over = _account([HELD], *PROTECTED[3:5], *_order("9", "SELL MKT", "c", "Filled", 0))
    sent = _gateway(monkeypatch, WORKING, answer, over, WORKING, answer, WORKING)
    assert _paper().cancel() == ("a", "f")
    with pytest.raises(placing.NotCancelled, match="c .10148: cannot be cancelled"):
        _paper().cancel()
    assert sent == [ACCOUNT, CANCELS, ACCOUNT] * 2


SALE, SOLD, OUT = Sale(ID, IITU, 26), _but(BOUGHT, 18, "SLD"), replace(FILL, quantity=-26)
#: A market sale for the day as the published client writes one (ib_insync 0.9.86, its source
#: read and never imported), under the gateway's next number, 41: the line by the broker's
#: number for it, on the broker's router, the desk's order id its reference, sent at once.
ORDER = (
    f"3|41|212969319|IITU|STK||0.0|||SMART||GBP|||||SELL|26|MKT|||DAY|||O|0|{ID}|"
    "1|0|0|0|0|0|0|0||0.0||||||||0||-1|0|||0|||0|0||0||||||0|||||0|||||||||||0|||0|0|||0||0|0"
    "|0|0|||||||0|||||||||0|0|0|0|||0||"
).split("|")
PLACED, CANCEL = _wire(ORDER).getvalue(), _wire(("4", "1", "41", "")).getvalue()
MINE = _order("41", "SELL MKT", ID, "Submitted")  # the sale as the broker has it, and its state
BARE = _account([HELD])  # the line held, and under no stop of the desk's own
REJECTED = ("4", "2", "41", "201", "Order rejected - reason: closed", "")
BUY_IT = Order(ID, IITU, 26, Decimal(40), Decimal(1), Decimal("36.007"))  # its stop off the step
#: The stop that goes with the buy, as the broker lists it; and both as it tells them filling.
CHILD = _order("42", "SELL STP 3600.0", f"{ID}-stop", "PreSubmitted")
FILLING = [*_order("41", "BUY MKT", ID, "Submitted"), *CHILD, _but(MINE[1], 2, "Filled")]
RESTS = [_but(MINE[1], 2, "PreSubmitted")]  # the broker's word that it holds a stop sent alone
ENDED_7, ENDED_42 = (_order(n, "SELL STP", "x", "Cancelled", 0)[1] for n in ("7", "42"))


def _msg(but: dict[int, str]) -> bytes:
    """The sale's message, but for the places given: 16 its action, 17 its shares, 18 its kind,
    20 its level, 21 how long it stands, 26 its reference, 27 sent at once, 28 what it waits on."""
    return _wire(list((dict(enumerate(ORDER)) | but).values())).getvalue()


AT_STOP = {18: "STP", 20: "3600.00", 21: "GTC", 26: f"{ID}-stop"}  # 36.007 pounds, in pence
SMALLER = _msg(AT_STOP | {17: "16", 20: "171.5"})  # the line's stop, for sixteen shares
CANCEL_7, CANCEL_42 = (_wire(("4", "1", n, "")).getvalue() for n in ("7", "42"))
UNFOUND = ("4", "2", "41", "10147", "OrderId 41 that needs to be cancelled is not found", "")
FAR = _order("5", "SELL STP", "a-stop", "Submitted")
#: A sale cut at ten of 26 on the line under its stop, as the broker tells it; what is asked.
PART: list[Said] = [PROTECTED, [CUT, ("102",)], [_but(SOLD, 19, "10"), END], PROTECTED]
ASKED = [ACCOUNT, ENDED, FILLS]
#: No stop a sale of the line would leave: someone else's on it, the desk's own there that is
#: over, its own order there that is no stop, and its own stop on another line.
AROUND = _account(
    [HELD],
    *_order("7", "SELL STP", "x-stop", "PreSubmitted", client="31"),
    *_order("9", "SELL STP", f"{ID}-stop", "Cancelled", 0),
    *_order("12", "BUY LMT", "f", "Inactive"),
    *(_but(FAR[0], 2, "265598"), FAR[1]),
)


def test_a_sale_is_sent_once_and_answered_with_what_the_broker_did(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    broker: Broker = _paper(_ready(tmp_path))
    # told as it fills: the order, its fill under no question's number, the fee, a warning
    filling = [*MINE, _but(SOLD, 1, "-1"), FEE, ("4", "2", "41", "2109", "hours ignored", "")]
    filled = _order("41", "SELL MKT", ID, "Filled", 0)[1]
    did = [_account([FLAT], FEE), [DONE, ("102",)], [SOLD, END]]  # the fee, late and unasked
    sent = _gateway(monkeypatch, [], AROUND, [*filling, filled], *did, AROUND)
    assert broker.place(SALE) == Report(ID, (OUT,), None)
    # a knock; the line's stops; the sale, under the gateway's next number; what it then did;
    # and the line's stops again: none of the desk's own open on it, so nothing more is sent
    assert sent == [b"", ACCOUNT, PLACED, ACCOUNT, ENDED, FILLS, ACCOUNT]
    # refused on entry and ended by the broker itself: nothing to cancel, and no list has it
    over = [REJECTED, _but(MINE[1], 2, "Cancelled")]
    sent = _gateway(monkeypatch, [], BARE, over, BARE, [("102",)], [END], BARE)
    told = broker.place(SALE)
    assert told.fills == () and "201: Order rejected - reason: closed" in str(told.reason)
    assert sent == [b"", ACCOUNT, PLACED, ACCOUNT, ENDED, FILLS, ACCOUNT]


def test_a_sale_the_broker_falls_silent_on_is_cancelled_and_never_left_working(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    broker = _paper(_ready(tmp_path))
    late = ("4", "2", "41", "399", "not placed until the open", "")
    gone = [("4", "2", "41", "202", "Order Canceled - reason:", ""), _but(MINE[1], 2, "Cancelled")]
    # ten sold before the cancel: the line's stop is then for the sixteen left, at the level
    # and under the name it had, the smaller one sent to rest first and then the old cancelled
    then = [*PART, RESTS, [ENDED_7]]
    sent = _gateway(monkeypatch, [], PROTECTED, [*MINE, late], gone, *then, silent=True)
    told = broker.place(SALE)
    assert told.fills == (replace(OUT, quantity=-10),)
    assert all(s in str(told.reason) for s in ("10 shares filled and 16 not", "399: not placed"))
    assert sent == [b"", ACCOUNT, PLACED, CANCEL, *ASKED, ACCOUNT, SMALLER, CANCEL_7]
    # a cancel refused with the sale still working, and a cancel met with silence, are errors:
    # never an answer, whatever the broker would then say it did
    cases: list[tuple[Said, list[Said], type[Exception]]] = [
        ([UNFOUND], [_account([HELD], *MINE)], placing.NotCancelled),
        ([], [BARE, [("102",)], [END]], TimeoutError),
    ]
    for cancel, after, error in cases:
        sent = _gateway(monkeypatch, [], BARE, [REJECTED], cancel, *after, silent=True)
        with pytest.raises(error):
            broker.place(SALE)
        assert sent[2:4] == [PLACED, CANCEL]
    # a gateway that hangs up once a sale has gone: it may have arrived, so it is not said
    # never to have (Disconnected); the next start asks the broker what it did with it
    sent = _gateway(monkeypatch, [], BARE, MINE)
    with pytest.raises(ConnectionError, match="hung up") as lost:
        broker.place(Sale(ID, AAPL, 10))
    assert not isinstance(lost.value, Disconnected)
    assert sent == [b"", ACCOUNT, _msg({2: "265598", 3: "AAPL", 11: "USD", 17: "10"})]


def test_a_buy_goes_with_its_stop_and_the_line_is_left_under_one_stop_for_all_its_shares(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    broker: Broker = _paper(_ready(tmp_path))
    did, under = [[DONE, ("102",)], [BOUGHT, END]], _account([HELD], *CHILD)
    sent = _gateway(monkeypatch, [], BARE, FILLING, under, *did, under)
    assert broker.place(BUY_IT) == Report(ID, (FILL,), None)
    # the buy is held back until its stop is sent behind it, to wait on it: the stop put down
    # onto the broker's step, in pence. Filled whole, the stop is for the shares held: no more
    both = _msg({16: "BUY", 27: "0"}) + _msg(AT_STOP | {1: "42", 28: "41"})
    assert sent == [b"", ACCOUNT, both, *ASKED, ACCOUNT]
    # a line held under a stop already: one stop for all its shares at the buy's level is
    # sent to rest first, and only then are the two it replaces cancelled
    two = _account([HELD], *PROTECTED[3:5], *CHILD)
    sent = _gateway(monkeypatch, [], PROTECTED, FILLING, two, *did, two, RESTS, [ENDED_7, ENDED_42])
    assert broker.place(BUY_IT) == Report(ID, (FILL,), None)
    assert sent[6:] == [ACCOUNT, _msg(AT_STOP | {17: "52"}), CANCEL_7 + CANCEL_42]
    # a buy the broker does not fill is cancelled; the stop that waited on it, were it still
    # listed, is cancelled too, and the stop the line was under stays as it was
    none: list[Said] = [[_but(MINE[1], 2, "Cancelled")], two, [("102",)], [END], two, [ENDED_42]]
    sent = _gateway(monkeypatch, [], PROTECTED, [CHILD[1]], *none, silent=True)
    assert broker.place(BUY_IT).fills == ()
    assert sent[2:] == [both, CANCEL, *ASKED, ACCOUNT, CANCEL_42]


def test_a_sale_takes_its_shares_off_the_stop_and_a_stop_not_settled_is_an_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    broker = _paper(_ready(tmp_path))
    flat = _account([FLAT], *PROTECTED[3:5])
    sold: list[Said] = [[_but(MINE[1], 2, "Filled")], flat, [DONE, ("102",)], [SOLD, END], flat]
    sent = _gateway(monkeypatch, [], PROTECTED, *sold, [ENDED_7])
    assert broker.place(SALE) == Report(ID, (OUT,), None)
    assert sent[6:] == [ACCOUNT, CANCEL_7]  # all the line's shares sold: its stop is cancelled
    # a cancel the broker refuses, the stop still held there for shares no longer held
    sent = _gateway(monkeypatch, [], PROTECTED, *sold, [_but(UNFOUND, 2, "7")], flat)
    with pytest.raises(placing.NotCancelled, match="-stop .10147"):
        broker.place(SALE)
    # the stop a part sale leaves, ended by the broker or met with silence: an error, and the
    # stop the line was under is not cancelled
    cases: list[tuple[Said, type[Exception], str]] = [
        ([REJECTED, _but(MINE[1], 2, "Cancelled")], placing.Unprotected, "Cancelled.*201: Order"),
        ([REJECTED], TimeoutError, "timed out"),
    ]
    for answer, error, saying in cases:
        sent = _gateway(monkeypatch, [], PROTECTED, [], cases[0][0][1:], *PART, answer, silent=True)
        with pytest.raises(error, match=saying):
            broker.place(SALE)
        assert sent[7:] == [ACCOUNT, SMALLER]


def test_nothing_is_sent_without_a_drill_a_clean_day_a_ready_gateway_and_the_stops_settled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ready, unchecked, night = _ready(tmp_path), tmp_path / "unchecked", AT.replace(hour=3, minute=0)
    book.turn(unchecked, book.Switch.DRILLED, AT, "every promise kept")
    book.turn(tmp_path / "old", book.Switch.DRILLED, AT - timedelta(days=32), "every promise kept")
    either: tuple[Order | Sale, ...] = (BUY_IT, SALE)  # a buy is held to all a sale is
    refusals: list[tuple[placing.Paper, tuple[Order | Sale, ...], type[Exception], str]] = [
        (_paper(ready), (Sale(ID, SMGB, 5),), Refused, "does not list SMGB: the broker lists 0"),
        (_paper(ready), (Sale(ID, replace(SMGB, symbol="VUSA"), 5),), Refused, "VUSA: it was not"),
        (_paper(tmp_path / "new"), either, Refused, "was not drilled in the last 31 days"),
        (_paper(tmp_path / "old"), either, Refused, "was not drilled in the last 31 days"),
        (_paper(unchecked), either, Refused, "not been checked today"),
        (_paper(ready, night), either, Disconnected, "restarts itself"),  # and is not dialled
        (_paper(ready), (replace(BUY_IT, stop=Decimal("0.009")),), ValueError, "no price at or"),
    ]
    for broker, orders, error, saying in refusals:
        for order in orders:
            sent = _gateway(monkeypatch)
            with pytest.raises(error, match=saying):
                broker.place(order)
            assert sent == []
    # what the line is under must be settled first: a stop of the desk's own the broker is not
    # yet holding, or two of them, and nothing is sent. Known only by asking: a knock, the account
    unsettled = _account([HELD], *_order("7", "SELL STP", f"{ID}-stop", "PendingSubmit"))
    for stops in (unsettled, _account([HELD], *PROTECTED[3:5], *CHILD)):
        for order in either:
            sent = _gateway(monkeypatch, [], stops)
            with pytest.raises(Refused, match="stops on IITU are not settled: .*-stop .P"):
                _paper(ready).place(order)
            assert sent == [b"", ACCOUNT]
    monkeypatch.setattr(paper, "dial", Mock(side_effect=ConnectionRefusedError))
    with pytest.raises(Disconnected, match="port is closed"):  # never received: sent next time
        _paper(ready).place(BUY_IT)
