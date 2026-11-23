"""The live five-minute round asks every line of every venue in session, whatever the daily asks."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from desk import keeper, keeper_live
from desk.bars import Five
from desk.lines import Line

NOW = datetime(2026, 11, 16, 10, tzinfo=UTC)


def test_every_line_in_session_is_asked_its_five_minute_bar(tmp_path: Path) -> None:
    lines = [Line(f"S{k}", "LSE", "GBP", 1) for k in range(13)]
    asked: list[str] = []

    def ask(line: Line, _when: datetime) -> tuple[Five, ...]:
        asked.append(line.symbol)
        return ()

    told = keeper_live.rounds(tmp_path / keeper.HOT, lines, NOW, ask, lambda *_: (), keeper.SETTLED)
    assert sorted(asked) == sorted(line.symbol for line in lines) and len(told) == 1
    assert (
        keeper_live.rounds(
            tmp_path / keeper.HOT, lines, NOW + timedelta(hours=12), ask, ask, keeper.SETTLED
        )
        == []
    )
