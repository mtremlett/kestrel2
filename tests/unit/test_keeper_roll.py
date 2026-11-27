"""The keeper's roll: the live day's bars of every span copied unchanged into the long database,
each with its source."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
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
        for span in ("15m", "30m"):  # every span the live store holds, none listed
            kept.timed(line, span, (Timed(span, now, price, price, price, price, 1),))
    assert keeper.main(tmp_path, now, ["--roll"]) == 0
    assert keeper.main(tmp_path, now, ["--roll"]) == 0  # again: the same bars, not more
    found = []
    for file in (hot, bars.files(hot)[bars.DAILY]):
        with closing(sqlite3.connect(file)) as held:
            found.append(held.execute("SELECT * FROM bar ORDER BY span").fetchall())
    assert found[0] == found[1] and len(found[0]) == 4 and found[0][0][-1] == Source.IBKR.value


def test_a_round_writes_the_hour_the_five_minute_bars_complete_and_no_partial_span(
    tmp_path: Path,
) -> None:
    hot, open_, price = tmp_path / keeper.HOT, datetime(2026, 11, 16, 8, tzinfo=UTC), Decimal(5)
    line = Line("BBB", "LSE", "GBP", 1)
    minutes = [open_ + timedelta(minutes=5 * n) for n in range(16)]  # 08:00-09:15: one whole hour
    with bars.writing(hot, Source.IBKR) as kept:
        kept.five(line, [Five(at, price, price, price, price, 1) for at in minutes])
    keeper.rolled(hot, [line], minutes[-1] + timedelta(minutes=5))
    for span, count, source in (
        ("15m", 5, Source.ROLLUP_5M),
        ("30m", 2, Source.ROLLUP_5M),
        ("1h", 1, Source.ROLLUP_30M),
        ("4h", 0, None),
    ):
        got = bars.timed(hot, line, span, open_, open_ + timedelta(hours=3))
        assert len(got) == count
        assert not count or set(bars.sources(hot, line, span)) == {source}
    assert keeper.rolled(hot, [line], minutes[-1] + timedelta(minutes=5)) == []  # nothing differs
    late, other = open_ + timedelta(hours=5), price + 1  # a held hour the fives do not make
    with bars.writing(hot, Source.IBKR) as kept:
        kept.timed(line, "1h", (Timed("1h", late, other, other, other, other, 1),))
        kept.five(line, [Five(late + timedelta(minutes=5 * n), price, price, price, price, 1)
                         for n in range(12)])  # fmt: skip
    told = keeper.rolled(hot, [line], late + timedelta(hours=2))
    assert any(t.startswith("FAULT BBB 1h") for t in told)


def test_a_round_leaves_each_rolled_span_as_fresh_as_its_base(tmp_path: Path) -> None:
    hot, open_, price = tmp_path / keeper.HOT, datetime(2026, 11, 16, 8, tzinfo=UTC), Decimal(5)
    line, ends = Line("BBB", "LSE", "GBP", 1), open_ + timedelta(hours=2)
    with bars.writing(hot, Source.IBKR) as kept:
        kept.five(line, [Five(open_ + timedelta(minutes=5 * n), price, price, price, price, 1)
                         for n in range(24)])  # fmt: skip
    keeper.rolled(hot, [line], ends)
    for span, length in (("15m", 15), ("30m", 30), ("1h", 60)):
        got = bars.timed(hot, line, span, open_, ends)
        assert got[-1].start + timedelta(minutes=length) == ends  # the base's last bar is in it


def test_every_keeper_round_leaves_its_newest_five_minute_bar_in_the_long_database(
    tmp_path: Path,
) -> None:
    now, price = datetime(2026, 11, 16, 10, 5, tzinfo=UTC), Decimal(5)
    line, newest = Line("BBB", "LSE", "GBP", 1), datetime(2026, 11, 16, 10, tzinfo=UTC)
    planted = (Five(newest, price, price, price, price, 1),)
    keeper.keep(tmp_path, now, [line], lambda _line, _day: (), lambda _line, _at: planted)
    with closing(sqlite3.connect(bars.files(tmp_path / keeper.HOT)[bars.DAILY])) as long:
        seen = long.execute("SELECT COUNT(*) FROM bar WHERE span = ?", (bars.FIVE,)).fetchone()
    assert seen == (1,)
