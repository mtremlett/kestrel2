"""Go flat: the flag appears mid-day, the next step sells every held line and buys nothing, the
state reads 'go flat since HH:MM', and taking the flag away resumes nothing until his lift."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book, goflat, halt
from desk.broker import Pretend
from desk.halt import OPERATOR, Stopped
from desk.lines import LINES
from desk.orders import Order, Settings
from desk.store import Bar

ROOM, FRI, MON = Settings(Decimal(100_000)), date(2026, 11, 13), date(2026, 11, 16)
LINE = next(line for line in LINES if line.venue == "LSE" and line.currency == "GBP")
NOON = datetime(2026, 11, 16, 12, 5, tzinfo=UTC)


def test_the_flag_sells_every_held_line_and_the_lift_alone_resumes(tmp_path: Path) -> None:
    bars = tuple(Bar(d, Decimal(50), Decimal(51), Decimal(49), Decimal(50), 1) for d in (FRI, MON))
    broker = Pretend({LINE: bars}, {})
    broker.open(FRI)
    buy = Order(f"{FRI:%Y%m%d}-test-{LINE.symbol}", LINE, 10, Decimal(50), Decimal(1), Decimal(45))
    book.send(tmp_path, broker, buy, ROOM)
    broker.open(MON)

    assert goflat.step(tmp_path, broker, ROOM, NOON) == []  # no flag: nothing happens
    assert goflat.state(tmp_path) is None
    (tmp_path / goflat.FLAG).touch()
    assert "10 of 10 shares sold" in goflat.step(tmp_path, broker, ROOM, NOON)[0]
    assert book.positions(tmp_path) == {}
    assert broker.submitted() == (buy.order_id, f"20261113-goflat-{LINE.symbol}")
    assert goflat.state(tmp_path) == "go flat since 12:05"

    (tmp_path / goflat.FLAG).unlink()
    goflat.step(tmp_path, broker, ROOM, NOON)
    with pytest.raises(Stopped, match="halt is in force"):
        book.send(tmp_path, broker, replace(buy, order_id="20261116-test-x"), ROOM)
    assert (calling := goflat.called(tmp_path))
    halt.lift(tmp_path, calling, NOON, "his lift", OPERATOR)
    assert goflat.state(tmp_path) is None


class Spy(Pretend):
    """A pretend broker that counts the cancels asked of it."""

    asked = 0

    def cancel(self) -> tuple[str, ...]:
        """Count the ask."""
        self.asked += 1
        return super().cancel()


def test_the_flag_also_asks_the_broker_to_cancel_working_buys(tmp_path: Path) -> None:
    broker = Spy({}, {})
    (tmp_path / goflat.FLAG).touch()
    goflat.step(tmp_path, broker, ROOM, NOON)
    assert broker.asked == 1
