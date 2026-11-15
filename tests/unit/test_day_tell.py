"""day.trade hands its door to his phone to every send, so a place the broker disagrees with
(R-PAPER-11) reaches him."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from test_day import ARCHIVE, DAYS

from desk import book, day
from desk.broker import Pretend
from desk.orders import Settings


def test_every_send_of_the_day_carries_the_door(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    doors: list[object] = []

    def send(*args: object) -> book.Sent:
        doors.append(args[4])
        return book.Sent("x", 0, None, None)

    monkeypatch.setattr(book, "send", send)
    on, tell, broker = DAYS[21], print, Pretend(ARCHIVE, {})
    broker.open(on)
    before = {line: tuple(b for b in bars if b.day < on) for line, bars in ARCHIVE.items()}
    day.trade(tmp_path, before, broker, Settings(Decimal(10_000)), on, {"GBP": Decimal(1)}, tell)
    assert doors and all(door is tell for door in doors)
