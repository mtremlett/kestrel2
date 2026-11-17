"""R-RUNNER-270: the keeper's command asks the broker first for a day the archive lacks."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk import archive, history, keeper, paper, venues
from desk.lines import LINES, Line
from desk.store import Answer, Bar, Refused

UK = Line("BBB", "LSE", "GBP", 1)
TUE = date(2026, 11, 17)
MON = date(2026, 11, 16)
NOW = datetime(2026, 11, 16, 21, 45, tzinfo=UTC)  # both venues settled: Monday's close is owed


def _bars(line: Line, day: date) -> tuple[Bar, ...]:
    days = venues.sessions(line.venue, date(2026, 8, 3), day - timedelta(1))
    prices = [Decimal(100 + n % 5) for n in range(len(days))]
    return tuple(
        Bar(d, p, p + 1, p - 1, p, 1000 + n)
        for n, (d, p) in enumerate(zip(days, prices, strict=True))
    )


def _no_gateway(_talk: object) -> object:
    raise ConnectionRefusedError("no gateway in a test")


def _broker(lines: Sequence[Line], day: date) -> dict[Line, Answer]:
    return {line: _bars(line, day) for line in lines}


def test_a_day_the_archive_lacks_is_filled_from_the_broker_else_the_line_parks_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def away(address: str) -> bytes:
        raise OSError(f"no route to {address[:13]}")

    monkeypatch.setattr(archive, "_ask", away)
    monkeypatch.setattr(paper, "dial", _no_gateway)
    given, bare, one = tmp_path / "given", tmp_path / "bare", LINES[0]
    assert keeper.main(given, NOW, [], _broker) == 0
    held, parked = keeper.saved(given, TUE, [one])
    assert held[one] == _bars(one, TUE) and not parked
    assert keeper.main(bare, NOW, [], history.daily(NOW)) == 1  # no broker answer: as before
    assert keeper.saved(bare, TUE, [one])[1] == {one.symbol}  # parked, and the line is named


def test_the_broker_is_asked_only_for_lines_the_archive_is_short_of_and_a_closed_door_is_words(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    asked: list[list[Line]] = []

    def broker(lines: Sequence[Line], day: date) -> dict[Line, Answer]:
        asked.append(list(lines))
        return _broker(lines, day)

    whole = _bars  # the archive lacks nothing
    keeper.keep(tmp_path / "a", NOW, (UK,), whole, lambda *_: (), lambda: 0.0, broker=broker)
    assert asked == []

    def short(line: Line, day: date) -> tuple[Bar, ...]:
        return _bars(line, day)[:-1]  # Monday missing

    keeper.keep(tmp_path / "b", NOW, (UK,), short, lambda *_: (), lambda: 0.0, broker=broker)
    assert asked == [[UK]]
    monkeypatch.setattr(paper, "dial", _no_gateway)
    nothing = history.daily(NOW)([UK], MON)  # no gateway here: dial refuses
    refusal = nothing[UK]
    assert isinstance(refusal, Refused) and "not asked" in refusal.reason
