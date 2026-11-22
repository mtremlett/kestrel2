"""story: each decision of the day is kept as one chain line, under the id its order and fills
carry, with the bar its signal read and the send path's answer."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import NoReturn

import pytest
from test_day import ARCHIVE, DAYS

from desk import book, day
from desk.broker import Pretend
from desk.orders import Order, Sale, Settings


def test_every_decision_of_the_day_is_chained_to_its_order_and_the_bar_it_read(
    tmp_path: Path,
) -> None:
    on, broker = DAYS[21], Pretend(ARCHIVE, {})
    broker.open(on)
    seen = {line: tuple(b for b in bars if b.day < on) for line, bars in ARCHIVE.items()}
    sent = day.trade(tmp_path, seen, broker, Settings(Decimal(10_000)), on, {"GBP": Decimal(1)})
    chains = list(book.chains(tmp_path))
    assert chains and [c.order_id for c in chains] == [s.order_id for s in sent]
    bought = {f.order_id for f in book.fills(tmp_path)}
    for chain in chains:
        assert chain.bar_day < on
        assert (chain.filled > 0) == (chain.order_id in bought)
        assert chain.asked >= chain.filled


class _Raises(Pretend):
    def place(self, _order: Order | Sale) -> NoReturn:
        raise RuntimeError("the line went down mid-send")


def test_a_send_that_raises_still_leaves_its_chain_naming_the_order(tmp_path: Path) -> None:
    on, broker = DAYS[21], _Raises(ARCHIVE, {})
    broker.open(on)
    seen = {line: tuple(b for b in bars if b.day < on) for line, bars in ARCHIVE.items()}
    with pytest.raises(book.Alarm):
        day.trade(tmp_path, seen, broker, Settings(Decimal(10_000)), on, {"GBP": Decimal(1)})
    kept = list(book.chains(tmp_path))
    assert kept and kept[-1].blocker == book.SENDING and kept[-1].order_id and kept[-1].strategy
