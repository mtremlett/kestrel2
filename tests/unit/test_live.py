"""The live session's source: the broker's ended bars in the line's own unit, paced, and its
silence said in words."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from desk import listing, live, paper
from desk.bars import Five
from desk.lines import Line

UK, NOW = Line("BBB", "LSE", "GBP", 1), datetime(2026, 11, 16, 9, 10, tzinfo=UTC)
PENCE = listing.Listing(UK, "123", "LSE", 100, ((Decimal(0), Decimal("0.5")),))


def _bar(minute: int, price: str) -> Five:
    return Five(NOW.replace(minute=minute), *(Decimal(price),) * 4, 5)


def test_the_brokers_bars_are_ended_ones_in_pounds_and_its_silence_is_said(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(paper, "CLIENT", paper.CLIENT)  # the ask makes this process the reader
    waits: list[float] = []
    given = {"BBB": [_bar(0, "250"), _bar(5, "260"), _bar(10, "270")]}  # the last still forming
    ask = live.ibkr(
        tmp_path,
        waits.append,
        lambda line, _contract, _route, _count: tuple(given[line.symbol]),
        lambda *_: {"BBB": PENCE},
    )
    got = ask(UK, NOW)
    assert [b.close for b in got] == [Decimal("2.5"), Decimal("2.6")] and paper.CLIENT == 226
    given["BBB"] = []
    with pytest.raises(ValueError, match="no IBKR real-time data on paper for BBB: no bars"):
        ask(UK, NOW)
    assert waits == [live.PACING]  # the second ask waited, the first did not
