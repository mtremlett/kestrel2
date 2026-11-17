"""The live session's source: the broker's ended bars in the line's own unit, paced, and its
silence said in words."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk import listing, live
from desk.bars import Five
from desk.lines import Line
from desk.spans import Timed

UK, NOW = Line("BBB", "LSE", "GBP", 1), datetime(2026, 11, 16, 9, 10, tzinfo=UTC)
PENCE = listing.Listing(UK, "123", "LSE", 100, ((Decimal(0), Decimal("0.5")),))


def _bar(minute: int, price: str) -> Five:
    return Five(NOW.replace(minute=minute), *(Decimal(price),) * 4, 5)


def test_the_brokers_bars_are_ended_ones_in_pounds_and_its_silence_is_said(
    tmp_path: Path,
) -> None:
    waits: list[float] = []
    given = {"BBB": [_bar(0, "250"), _bar(5, "260"), _bar(10, "270")]}  # the last still forming
    ask = live.ibkr(
        tmp_path,
        waits.append,
        lambda line, _contract, _route, _count, _door: tuple(given[line.symbol]),
        lambda *_: {"BBB": PENCE},
    )
    got = ask(UK, NOW)
    assert [b.close for b in got] == [Decimal("2.5"), Decimal("2.6")]
    given["BBB"] = []
    with pytest.raises(ValueError, match="no IBKR real-time data on paper for BBB: no bars"):
        ask(UK, NOW)
    assert waits == [live.PACING]  # the second ask waited, the first did not


def test_the_one_minute_question_reaches_back_to_the_last_held_and_keeps_ended_minutes(
    tmp_path: Path,
) -> None:
    asked: list[int] = []
    price = Decimal("250")
    both = (Timed("1m", NOW - timedelta(minutes=1), price, price, price, price, 1),) * 2

    def newest(
        _line: Line, _contract: str, _route: str, seconds: int, _door: object
    ) -> tuple[Timed, ...]:
        asked.append(seconds)
        return (*both, replace(both[0], start=NOW))  # the last one still forming

    ask = live.minutes(
        tmp_path, tmp_path / "hot.db", lambda _s: None, newest, lambda *_: {"BBB": PENCE}
    )
    assert [b.close for b in ask(UK, NOW)] == [Decimal("2.5")] * 2 and asked == [live.FIRST]
