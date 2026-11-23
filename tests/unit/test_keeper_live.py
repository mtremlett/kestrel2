"""keeper_live: a line with no one-minute history yet is started from IBKR, not a failure."""

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from desk import bars, keeper, keeper_live, live
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


def test_a_polled_round_counts_its_requests_and_a_pacing_refusal_halves_the_rate(
    tmp_path: Path,
) -> None:
    hot, now = tmp_path / keeper.HOT, datetime(2026, 11, 17, 10, tzinfo=bars.EPOCH.tzinfo)
    lines = [Line(f"S{k}", "LSE", "GBP", 1) for k in range(40)]
    asked: list[str] = []

    def ask(one: Line, when: datetime) -> tuple[Timed, ...]:
        asked.append(one.symbol)
        if one.symbol == "S1":
            raise ValueError("pacing violation")
        return (
            Timed(
                "1m", when - timedelta(minutes=1), Decimal(5), Decimal(5), Decimal(5), Decimal(5), 1
            ),
        )

    words, requests, refusals = keeper_live.polled_round(hot, lines, now, ask, 5, 27)
    assert (requests, refusals, len(asked)) == (27, 1, 27) and "1 pacing refusals" in words
    assert keeper.pace(5, 27, refusals) == 27 and keeper.pace(5, 100, refusals) == 50


def test_a_line_the_broker_has_no_definition_for_is_untradeable_not_a_miss(tmp_path: Path) -> None:
    hot, now = tmp_path / keeper.HOT, datetime(2026, 11, 17, 10, tzinfo=bars.EPOCH.tzinfo)
    line = Line("IDTL", "LSE", "USD", 1)

    def ask(one: Line, _: datetime) -> tuple[Timed, ...]:
        raise live.Untradeable(f"no IBKR real-time data on paper for {one.symbol}: no definition")

    words, stale = keeper_live.minute_round(hot, (line,) * 2, now, ask)
    assert stale == [] and "untradeable: IDTL" in words
