"""One contract for the desk's Broker: the pretend broker and the paper account, replayed from
a gateway tape, give the same answers to the same orders (R-RUNNER-142)."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from decimal import Decimal
from pathlib import Path

import pytest
import test_placing as tp
from test_paper import _account, _gateway
from test_reports import BOUGHT, BUY, DONE, END, IITU

from desk import book, paper
from desk.broker import Broker, Disconnected, Pretend, Report, Restopping
from desk.orders import Settings
from desk.store import Bar

DAY, LEVEL = BUY.made.date(), Decimal(33)
BARS = {IITU: (Bar(DAY, Decimal("37.55"), Decimal(39), Decimal(37), Decimal(38), 1),)}
UNDER = _account([tp.HELD], *tp.CHILD)  # 26 held, under the buy's one stop
#: What each kind is told by its gateway for each question, in the order the desk asks them.
PAPER_TAPE: dict[str, list[Sequence[Sequence[str]]]] = {
    "place": [[], tp.EMPTY, tp.FILLING, UNDER, [DONE, ("102",)], [BOUGHT, END], UNDER],
    "unknown": [_account([]), [("102",)], [END]],
    "fills": [[BOUGHT, END]],
    "held": [UNDER, UNDER],
    "restop": [UNDER, tp.RESTS, [tp.ENDED_42]],
    "idle": [_account([])],
}
Tape = Callable[[str], object]


@pytest.fixture(params=["pretend", "paper"])
def desk(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> tuple[Restopping, Tape]:
    """The broker under test, and the tape that tells the paper one what its gateway says."""
    if request.param == "pretend":
        pretend = Pretend(BARS, {})
        pretend.open(DAY)
        return pretend, lambda _: None
    return tp._paper(tp._ready(tmp_path)), lambda ask: _gateway(monkeypatch, *PAPER_TAPE[ask])


def _words(told: Broker | Report) -> tuple[object, ...]:
    """Each fill but for the broker's own execution id, which differs by design."""
    return tuple(
        (f.order_id, f.symbol, f.quantity, f.price, f.day)
        for f in (told.fills if isinstance(told, Report) else told.fills())
    )


def test_a_buy_is_placed_filled_and_left_under_one_stop(desk: tuple[Restopping, Tape]) -> None:
    broker, tape = desk
    tape("unknown")
    assert broker.report(tp.ID) is None  # never received
    tape("place")
    report = broker.place(tp.BUY_IT)
    mine = (tp.ID, "IITU", 26, Decimal("37.55"), DAY)
    assert report.reason is None and report.order_id == tp.ID and len(report.fills) == 1
    tape("fills")
    assert _words(report) == _words(broker) == (mine,)
    tape("held")
    assert tuple(broker.holdings()) == (("IITU", 26),) == tuple(broker.stops())


def test_a_stop_is_moved_and_none_working_is_cancelled(desk: tuple[Restopping, Tape]) -> None:
    broker, tape = desk
    tape("place")
    broker.place(tp.BUY_IT)
    tape("restop")
    broker.restop("IITU", LEVEL)
    tape("held")
    assert tuple(broker.stops()) == (("IITU", 26),)  # still one stop, for all the shares
    tape("idle")
    assert tuple(broker.cancel()) == ()


def test_gateway_news_of_a_broken_link_after_an_order_is_unknown_and_the_kill_switch_stays_off(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root, none, link = (
        tp._ready(tmp_path),
        _account([]),
        ("4", "2", "-1", "2157", "farm broken", ""),
    )
    _gateway(monkeypatch, none, [("102",)], [END], [END], none, none, [], tp.EMPTY, [link])
    sent = book.send(root, tp._paper(root), tp.BUY_IT, Settings(Decimal(10_000)))
    assert "2157" in str(sent.reason) and sent.filled == 0
    assert (root / book.GOING).exists()  # the note stays: the next step's recover settles it
    assert book.switch(root)[-1][1] is book.Switch.DRILLED  # and the kill switch is not turned on
    with pytest.raises(Disconnected, match="2110"):
        paper.other(["4", "2", "-1", "2110", "link broken", ""])
