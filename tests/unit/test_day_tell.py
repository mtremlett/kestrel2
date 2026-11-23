"""day.trade hands its door to his phone to every send, so a place the broker disagrees with
(R-PAPER-11) reaches him."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from test_day import ARCHIVE, DAYS

from desk import book, day, halt
from desk.broker import Fill, Pretend
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


def test_a_stop_that_gapped_past_the_loss_limit_halts_buying_once(tmp_path: Path) -> None:
    line = next(iter(ARCHIVE))
    cut = [Fill("1", "a", line.symbol, 700, Decimal(10), DAYS[1])]
    book._record(tmp_path, [*cut, Fill("2", "a-stop", line.symbol, -700, Decimal(8), DAYS[2])])
    book.record_rates(tmp_path, DAYS[1], {line.currency: Decimal(1)})
    tells: list[str] = []
    for _ in range(2):  #: 1,400 pounds lost is over 5% of 10,000; the second look adds nothing
        day._stand_down(
            tmp_path,
            ARCHIVE,
            Pretend(ARCHIVE, {}),
            Settings(Decimal(10_000)),
            lambda k, _w: tells.append(k),
        )
    assert len(halt.in_force(tmp_path)) == 1 and tells == ["gap a-stop"]
