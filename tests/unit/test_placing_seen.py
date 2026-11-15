"""A conversation with the real Gateway, re-enacted in the tests' own shapes as it went on 14
November 2026, the markets shut (the conformance tapes), and the adapter's answer to it."""

from __future__ import annotations

from pathlib import Path

import pytest
import test_placing as tp
from test_paper import Said, _account, _but, _gateway, _order
from test_reports import CUT, END

from desk import paper, placing
from desk.broker import Report
from desk.listing import Listing
from desk.orders import Refused
from desk.placing import NotCancelled, Unprotected


def test_a_buy_the_broker_refuses_on_entry_is_answered_with_its_reason_and_nothing_is_left(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # SPY at 02:37 UK: the buy, then the stop behind it, each told "Inactive" and then why
    # (201); then silence. The desk's cancel finds no such order (10147), the account lists
    # neither, and the day's ended list has both as cancelled, none of their shares done
    both = (("41", "BUY MKT", tp.ID), ("42", "SELL STP 3600.0", f"{tp.ID}-stop"))
    refused = [
        said
        for number, deal, ref in both
        for said in (*_order(number, deal, ref, "Inactive"), _but(tp.REJECTED, 2, number))
    ]
    dead = _but(_but(CUT, 87, "0"), 13, "26")
    ended = [dead, _but(dead, 22, f"{tp.ID}-stop"), ("102",)]
    gone: list[Said] = [[tp.UNFOUND], tp.EMPTY, tp.EMPTY, ended, [END], tp.EMPTY]
    sent = _gateway(monkeypatch, [], tp.EMPTY, refused, *gone, silent=True)
    told = tp._paper(tp._ready(tmp_path)).place(tp.BUY_IT)
    why = "201: Order rejected - reason: closed"
    assert told == Report(
        tp.ID,
        (),
        f"{tp.ID}: the broker says Cancelled, 0 shares filled and 26 not; its fills today "
        f"come to 0 shares; it said: {why}; {why}",
    )
    placed = tp._msg({16: "BUY", 27: "0"}) + tp._msg(tp.AT_STOP | {1: "42", 28: "41"})
    assert sent == [b"", tp.ACCOUNT, placed, tp.CANCEL, tp.ACCOUNT, *tp.ASKED, tp.ACCOUNT]


def test_a_stop_that_sold_or_ended_as_it_was_cancelled_stops_the_sale_and_the_line_is_put_back(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # R-MONEY-17: the stop is cancelled before a sale goes. Sold meanwhile, ended unseen, or
    # part sold first: the sale is not sent, and the line is left under its stop for what is held
    broker = tp._paper(tp._ready(tmp_path))
    ended, bare, rests = _but(tp.ENDED_7, 2, "Filled"), tp.BARE, tp.RESTS
    sent = _gateway(monkeypatch, [], tp.PROTECTED, [ended], tp.EMPTY)
    with pytest.raises(Unprotected, match="sold as it was cancelled"):
        broker.place(tp.SALE)
    assert tp.PLACED not in sent
    sent = _gateway(
        monkeypatch, [], tp.PROTECTED, [_but(tp.UNFOUND, 2, "7")], bare, bare, bare, rests
    )
    with pytest.raises(Refused, match="its stop ended"):
        broker.place(tp.SALE)
    assert tp.PLACED not in sent
    sent = _gateway(monkeypatch, [], tp.PROTECTED, [tp.ENDED_7], tp.LEFT, tp.LEFT, rests)
    with pytest.raises(Refused, match="16 held"):
        broker.place(tp.SALE)
    assert sent[5] == tp.SMALLER and tp.PLACED not in sent
    # a cancel met with silence, the stop still resting: none is put beside it
    sent = _gateway(monkeypatch, [], tp.PROTECTED, [], tp.PROTECTED, tp.PROTECTED, silent=True)
    with pytest.raises(TimeoutError):
        broker.place(tp.SALE)
    assert not any(b"STP" in message for message in sent)
    # a sale that errs once its stop is cancelled puts the stop back for the shares held
    working = _account([tp.HELD], *tp.MINE)
    sent = _gateway(
        monkeypatch,
        [],
        tp.PROTECTED,
        [tp.ENDED_7],
        bare,
        [tp.REJECTED],
        [tp.UNFOUND],
        working,
        bare,
        rests,
        silent=True,
    )
    with pytest.raises(NotCancelled):
        broker.place(tp.SALE)
    assert b"\x00SELL\x0026\x00STP\x00\x00171.5" in sent[-1]


def test_a_stop_that_sold_or_ended_unseen_as_it_was_cancelled_by_settle_is_unprotected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # a stop left resting is cancelled once its replacement rests, or no share is left
    broker = tp._paper(tp._ready(tmp_path))
    listed = broker._listings[tp.SALE.line.symbol]
    assert isinstance(listed, Listing)
    gone = [_but(tp.UNFOUND, 2, "7")]
    for end in ([[_but(tp.ENDED_7, 2, "Filled")]], [gone, tp.EMPTY, tp.EMPTY]):
        _gateway(monkeypatch, tp.PROTECTED)
        held, stops = placing.on(paper.read(), listed)
        _gateway(monkeypatch, *end)
        with pytest.raises(Unprotected, match="ended another way"):
            broker.settle(listed, held, stops, None)
    _gateway(monkeypatch, tp.PROTECTED)
    held, stops = placing.on(paper.read(), listed)
    _gateway(monkeypatch, gone, tp.BARE, tp.BARE)
    broker.settle(listed, held, stops, None)
