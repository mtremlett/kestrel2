"""A conversation with the real Gateway, re-enacted in the tests' own shapes as it went on 14
November 2026, the markets shut (the conformance tapes), and the adapter's answer to it."""

from __future__ import annotations

from pathlib import Path

import pytest
import test_placing as tp
from test_paper import Said, _but, _gateway, _order
from test_reports import CUT, END

from desk.broker import Report


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
