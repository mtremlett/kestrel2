"""weather.macro: VIXCLS days named stormy or calm from published-next-day observations only."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk import bars
from desk.store import Bar
from lab import history_bars, weather

D = date(2024, 1, 1)
VIX = {D + timedelta(days=n): Decimal(v) for n, v in enumerate([10, 20, 12, 30, 5])}


def test_labels_are_hand_worked_and_blind_to_the_day_itself_and_later(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(weather, "VOL_RANK", 2)
    days = [D + timedelta(days=n) for n in range(6)]
    got = weather.macro(VIX, days)
    # day 3 sees 10, 20, 12: 12 is not above median(10, 20) = 15; day 4 sees 30 > median(20, 12)
    # = 16; day 5 sees 5, not above median(12, 30) = 21. Days 0 to 2 lack two earlier values.
    assert [got[d] for d in days] == ["warming"] * 3 + ["calm", "stormy", "calm"]
    assert (
        weather.macro({**VIX, days[3]: Decimal(99)}, days)[days[3]] == got[days[3]]
    )  # not on its own day
    assert weather.macro({d: v for d, v in VIX.items() if d <= days[3]}, days[:4]) == {
        d: got[d] for d in days[:4]
    }


def test_the_reader_takes_one_series_and_the_contest_says_too_short(tmp_path: Path) -> None:
    file = bars.files(history_bars.database(tmp_path))[bars.DAILY]
    with closing(sqlite3.connect(file)) as db:
        db.execute("CREATE TABLE fact (kind, source, subject, at, value)")
        db.executemany(
            "INSERT INTO fact VALUES ('macro', 'fred', ?, ?, ?)",
            [("VIXCLS", "2024-01-01", "10.5"), ("DGS10", "2024-01-01", "4")],
        )
        db.commit()
    assert history_bars.facts(tmp_path, "VIXCLS") == {D: Decimal("10.5")}
    market = [
        Bar(D + timedelta(days=n), Decimal(1), Decimal(1), Decimal(1), Decimal(1), 1)
        for n in range(3)
    ]
    got = {e.layer: e for e in weather.contest(market, {"a": market}, vix={D: Decimal(1)})}
    assert got["macro"].why == "too short"
