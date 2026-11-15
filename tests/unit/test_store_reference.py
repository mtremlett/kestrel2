"""The reference series: SPY from its first session, studied and never traded (R-RUNNER-94)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from desk import archive, store
from desk.store import Bar
from lab import universe

D = Decimal
FIRST = Bar(date(1993, 1, 29), D("43.97"), D("43.97"), D("43.75"), D("43.94"), 1_003_200)
NEXT = Bar(date(1993, 2, 1), D("43.97"), D("44.25"), D("43.97"), D("44.25"), 480_500)
SUNDAY = Bar(date(1993, 1, 31), D("44"), D("44"), D("44"), D("44"), 1)


def test_spy_is_kept_from_its_first_session_as_a_reference_and_is_no_traded_line(
    tmp_path: Path,
) -> None:
    asked: list[tuple[date, date]] = []

    def archive_from_1993(_line: object, day: date, since: date) -> tuple[Bar, ...]:
        asked.append((day, since))
        return (FIRST, SUNDAY, NEXT)

    kept = universe.keep_reference(tmp_path, date(2026, 11, 13), archive_from_1993)

    assert asked == [(date(2026, 11, 13), date(1993, 1, 29))]
    (line,) = kept
    assert line.symbol == "SPY"
    assert archive.read_reference(tmp_path / "US", "SPY") == (FIRST, NEXT)
    assert [fault.day for fault in kept[line]] == [SUNDAY.day]
    with pytest.raises(FileNotFoundError):
        store.read(tmp_path / "US", "SPY")  # a traded read finds no such line


def test_the_archive_is_asked_back_to_the_first_session_only_when_told_to() -> None:
    line = universe.REFERENCE[0]
    day = date(2026, 11, 13)

    def starts(address: str) -> int:
        return int(parse_qs(urlparse(address).query)["period1"][0])

    assert starts(archive.address(line, day, archive.REFERENCE_SINCE)) == 728_265_600
    assert starts(archive.address(line, day)) == 1_262_304_000  # 1 January 2010
