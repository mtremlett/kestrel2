"""keeper_live: a line with no one-minute history yet is started from IBKR, not a failure."""

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from desk import bars, keeper, keeper_live
from desk.lines import Line
from desk.spans import Timed


def test_a_line_with_no_one_minute_history_is_started_and_the_job_is_clean(tmp_path: Path) -> None:
    hot, line = tmp_path / keeper.HOT, Line("EQQQ", "LSE", "GBP", 1)
    now = datetime(2026, 11, 17, 10, tzinfo=bars.EPOCH.tzinfo)
    price = Decimal(5)

    def ask(one: Line, when: datetime) -> tuple[Timed, ...]:
        bars.timed(hot, one, "1m", when - timedelta(hours=1), when)  # as live.minutes reads it
        return (Timed("1m", when - timedelta(minutes=1), price, price, price, price, 1),)

    words, stale = keeper_live.minute_round(hot, (line,) * 2, now, ask)
    assert stale == [] and words.startswith("live: ")
    assert len(bars.timed(hot, line, "1m", now - timedelta(hours=1), now)) == 1
