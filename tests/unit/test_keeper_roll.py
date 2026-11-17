"""The keeper's roll: the live day's one-minute and five-minute bars copied unchanged into the
long database, each with its source."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from desk import bars, keeper
from desk.bars import Five, Source
from desk.lines import Line
from desk.spans import Timed


def test_a_roll_leaves_the_long_database_holding_the_live_bars_with_their_sources(
    tmp_path: Path,
) -> None:
    hot, now, price = tmp_path / keeper.HOT, datetime(2026, 11, 16, 10, tzinfo=UTC), Decimal(5)
    line = Line("BBB", "LSE", "GBP", 1)
    with bars.writing(hot, Source.IBKR) as kept:
        kept.timed(line, "1m", (Timed("1m", now, price, price, price, price, 1),))
        kept.five(line, (Five(now, price, price, price, price, 1),))
    assert keeper.main(tmp_path, now, ["--roll"]) == 0
    assert keeper.main(tmp_path, now, ["--roll"]) == 0  # again: the same bars, not more
    found = []
    for file in (hot, bars.files(hot)[bars.DAILY]):
        with closing(sqlite3.connect(file)) as held:
            found.append(held.execute("SELECT * FROM bar ORDER BY span").fetchall())
    assert found[0] == found[1] and len(found[0]) == 2 and found[0][0][-1] == Source.IBKR.value
