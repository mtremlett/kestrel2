"""book: an order whose answers do not agree after it has gone (R-PAPER-11)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book, halt
from desk.broker import Pretend, Report
from desk.halt import Blocker, Stopped
from desk.lines import Line
from desk.orders import Order, Sale, Settings
from desk.placing import Unprotected
from desk.store import Bar

A, B, MON = Line("A", "LSE", "GBP", 1), Line("B", "LSE", "GBP", 1), date(2025, 11, 10)
WEEK = {
    line: (Bar(MON, Decimal(50), Decimal(51), Decimal(49), Decimal(51), 1),) * 2 for line in (A, B)
}
ROOM = Settings(Decimal(10_000))


def _buy(root: Path, broker: Pretend, name: str, line: Line) -> book.Sent:
    return book.send(root, broker, Order(name, line, 10, *map(Decimal, (50, 1, 45))), ROOM)


def test_an_order_whose_answers_do_not_agree_is_gone_halts_buying_and_names_what_differs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    place = Pretend.place

    def disagree(self: Pretend, order: Order | Sale) -> Report:
        place(self, order)
        raise Unprotected("these do not agree")

    broker = Pretend(WEEK, {})
    broker.open(MON)
    monkeypatch.setattr(Pretend, "place", disagree)
    sent = _buy(tmp_path, broker, "o-1", A)
    assert (sent.filled, sent.blocker) == (10, Blocker.BROKER)
    assert "o-1" in str(sent.reason) and "do not agree" in str(sent.reason)
    assert len(halt.in_force(tmp_path)) == 1 and book.killed(tmp_path) is None
    assert not (tmp_path / book.GOING).exists()
    assert _buy(tmp_path, broker, "o-1", A).filled == 10 and broker.submitted() == (
        "o-1",
    ), "resent"
    with pytest.raises(Stopped, match="halt is in force"):
        _buy(tmp_path, broker, "o-2", B)
    monkeypatch.undo()
    assert book.send(tmp_path, broker, Sale("s-1", A, 10), ROOM).filled == 10, "sale stopped"
