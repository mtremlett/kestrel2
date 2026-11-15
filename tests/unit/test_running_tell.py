"""The running step hands the messenger to the day's money path: a broker whose word, fills and
account disagree after an order has gone reaches him once, naming the order; no disagreement
sends nothing new."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from test_reports import IITU
from test_running import DIP, ID, MON, _desk, _told

from desk import halt, running
from desk.broker import Pretend
from desk.messenger import Undelivered
from desk.orders import Order, Sale
from desk.placing import Unprotected
from desk.store import Bar


def test_a_broker_that_disagrees_after_an_order_has_gone_reaches_him_once_naming_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    desk, post = _desk(tmp_path, IITU=DIP)
    today = Bar(MON.date(), *[Decimal(36)] * 4, 1)
    broker = Pretend({IITU: (*DIP, today)}, {})
    broker.open(MON.date())
    place = broker.place

    def disagree(order: Order | Sale) -> object:
        place(order)  #: the order has gone, then the account does not agree
        raise Unprotected(f"{order.order_id}: these do not agree")

    monkeypatch.setattr(broker, "place", disagree)
    running._round(desk, broker, "LSE", MON)  # type: ignore[arg-type]
    post.side_effect = [
        1,
        Undelivered("down"),
        7,
        8,
        9,
        10,
    ]  #: the morning goes, the disagreement fails once
    with pytest.raises(Undelivered):
        running._say(desk, MON, running.UNASKED)
    for _ in range(2):
        running._say(desk, MON, running.UNASKED)
    told = [words for words in _told(post) if "do not agree" in words]
    assert len(told) == 2 and told[0] == told[1] and ID in told[0], "asked again, then once"
    assert len(halt.in_force(tmp_path)) == 1
    quiet, door = _desk(tmp_path / "quiet", IITU=DIP)
    fine = Pretend({IITU: (*DIP, today)}, {})
    fine.open(MON.date())
    running._round(quiet, fine, "LSE", MON)  # type: ignore[arg-type]
    assert not any("do not agree" in words for words in _told(door)) and not halt.in_force(
        quiet.root
    )
