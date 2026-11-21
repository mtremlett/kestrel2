"""The live session's source: the broker's ended bars in the line's own unit, paced, and its
silence said in words."""

from __future__ import annotations

import io
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk import listing, live, paper
from desk.bars import Five
from desk.lines import Line
from desk.spans import Timed

BAR = live.BAR
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
    close = datetime(2026, 11, 16, 16, 25, tzinfo=UTC)  # London's last bar ends at 16:30
    given["BBB"] = [Five(close + BAR * i, *(Decimal(250),) * 4, 5) for i in range(2)]
    assert [b.start for b in ask(UK, close + BAR * 2)] == [close]  # kept; the auction's is not
    given["BBB"] = []
    with pytest.raises(ValueError, match="no IBKR real-time data on paper for BBB: no bars"):
        ask(UK, NOW)
    assert waits == [live.PACING] * 2  # the second ask waited, the first did not


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


def _answer(*minutes: int) -> io.BytesIO:
    feeds = (
        "176|20261117 10:40:00 UTC",
        "4|2|-1|2104|Market data farm OK:eu",
        "9|1|7",
        "15|1|DU0000001",
    )
    stamps = [int(datetime(2026, 11, 17, 10, m, tzinfo=UTC).timestamp()) for m in minutes]
    rows = "|".join(f"{t}|5|6|4|5|9|5|1" for t in stamps)
    told = [*feeds, f"17|1|20261117 10:30:00 UTC|20261117 10:40:00 UTC|{len(stamps)}|{rows}"]
    return io.BytesIO(b"".join(paper.message(*m.split("|")) for m in told))


def test_one_minute_bars_off_a_five_minute_mark_are_kept_and_the_five_minute_ask_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(paper, "dial", lambda talk: talk(_answer(30, 31, 32), lambda _: None))
    got = live.newest_minutes(UK, "123", "LSE", 300, paper.Door(live.CLIENT))
    assert [(b.span, b.start.minute) for b in got] == [("1m", 30), ("1m", 31), ("1m", 32)]
    monkeypatch.setattr(paper, "dial", lambda talk: talk(_answer(30, 31), lambda _: None))
    with pytest.raises(ValueError, match="five-minute mark"):
        paper.newest(UK, "123", "LSE", 2, paper.Door(live.CLIENT))
