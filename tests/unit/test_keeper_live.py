"""The live keeper: one round of 1-minute bars of the lines in hours into the live store, a
stale or refused line a miss, the watchlist cut to his hundred lines, the day rolled."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk import archive, keeper, keeper_live
from desk.lines import LINES as MASTER
from desk.lines import Line

UK, US, TWIN = (
    Line("BBB", "LSE", "GBP", 1),
    Line("AAA", "US", "USD", 1),
    Line("CCC", "US", "USD", 1),
)
LINES = (UK, US, TWIN)
MON, SAT = date(2026, 11, 16), date(2026, 11, 14)


def _at(hour: int, minute: int = 0, day: date = MON) -> datetime:
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=UTC)


def test_a_live_round_keeps_the_minutes_of_lines_in_hours_and_misses_a_stale_or_refused_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    now, late, away = _at(10, 30), Line("DDD", "LSE", "GBP", 1), Line("EEE", "LSE", "GBP", 1)
    ago = {"BBB": 1, "DDD": 9}  # minutes since the line's newest bar started

    def ask(line: Line, when: datetime) -> tuple[archive.Row, ...]:
        if line == away:
            raise OSError("HTTP Error 429: Too Many Requests")
        start = int((when - timedelta(minutes=ago.get(line.symbol, 1))).timestamp()) // 60 * 60
        one = (Decimal(10),) * 4
        return ((start, *one, 7), (start - 60, *one[:3], Decimal(0), 7))  # the second is unsound

    lines = (*LINES, late)  # New York is shut: AAA and CCC are not asked
    done, missed, pacing = keeper_live.live(tmp_path, now, lines, ask)
    assert done == ["live round: 2 bars kept for 2 of 2 lines, 2 dropped as impossible, 0 refused"]
    assert [m.split(":")[0] for m in missed] == ["DDD on LSE"] and pacing == 0
    assert keeper_live.live(tmp_path, _at(3), lines, ask) == (
        [],
        [],
        0,
    )  # nobody open: nothing asked
    with closing(sqlite3.connect(tmp_path / keeper_live.LIVE)) as held:
        assert held.execute("SELECT count(*) FROM bar").fetchone() == (2,)
    (tmp_path / keeper_live.WATCHLIST).write_text(
        "# mine" + chr(10) + "LSE EEE" + chr(10) + "LSE BBB" + chr(10), "utf-8"
    )
    assert keeper_live.watch(tmp_path, lines) == [away]
    assert keeper.main(tmp_path, now, ["--live"], ask) == 1  # the real lines: BBB alone is open
    out, err = capsys.readouterr()
    assert out.splitlines()[-1] == "pacing 1" and "MISSED: EEE on LSE: refused" in err
    assert keeper.main(tmp_path, _at(10, 30, SAT), ["--live"], ask) == 0
    assert capsys.readouterr().out.splitlines() == ["pacing 0"]
    assert keeper.main(tmp_path, now, ["--roll"]) == 0
    with closing(sqlite3.connect(tmp_path / keeper_live.LIVE)) as held:
        total = held.execute("SELECT count(*) FROM bar").fetchone()[0]
    assert capsys.readouterr().out.splitlines() == [f"rolled {total} bars into market_history.db"]
    assert keeper_live.roll(tmp_path) == total  # rolled again: the same bars, none twice
    with pytest.raises(SystemExit, match="usage"):
        keeper.main(tmp_path, now, ["--now"])
    (tmp_path / keeper_live.WATCHLIST).write_text(chr(10).join(["US ZZ"] * 120), "utf-8")
    assert len(keeper_live.watch(tmp_path)) == keeper_live.HOLDS - len(MASTER)
