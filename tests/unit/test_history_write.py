"""The pulled bars let into the database: kept under the broker's source, none from a refusal."""

from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk import bars, conformance_tape, history
from desk import keeper as rounds
from desk.history_write import clashes, held, keeper, main, roll
from desk.lines import LINES, Line
from desk.rollup import Candle
from desk.spans import EPOCH
from desk.store import Bar, Refused

LINE = next(line for line in LINES if line.symbol == "VUAG")
PRICE = Decimal("110.5")


def test_a_pulled_answer_lands_under_the_brokers_source_and_a_refusal_adds_nothing(
    tmp_path: Path,
) -> None:
    live, keep = tmp_path / bars.LIVE, keeper(tmp_path / bars.LIVE, {"VUAG": 1})
    day = Bar(date(2026, 11, 12), PRICE, PRICE, PRICE, PRICE, 7)
    assert keep(LINE, "1d", Refused("none")) == 0 and not live.exists()
    assert keep(LINE, "1d", (day,)) == 1 and keep(LINE, "1d", (day,)) == 1
    assert bars.daily(live, LINE) == (day,)
    assert bars.sources(live, LINE, bars.DAILY) == {bars.Source.IBKR: 1}
    start = datetime(2026, 11, 12, 9, 30, tzinfo=UTC)
    candle = Candle(start, PRICE, PRICE, PRICE, PRICE, 3, "ibkr")
    assert keep(LINE, "5m", (candle,)) == 1 and keep(LINE, "30m", (candle,)) == 1
    assert bars.five(live, LINE, start, datetime(2026, 11, 13, tzinfo=UTC))[0].volume == 3
    assert bars.timed(live, LINE, "30m", start, datetime(2026, 11, 13, tzinfo=UTC))[0].volume == 3
    with pytest.raises(ValueError, match="mark"):
        keep(LINE, "4h", (candle,))


def test_what_the_database_holds_from_the_broker_is_done_and_the_command_stops_in_a_round(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert held(tmp_path / bars.LIVE, [LINE]) == set()
    keeper(tmp_path / bars.LIVE, {"VUAG": 1})(
        LINE, "1d", (Bar(date(2026, 11, 12), PRICE, PRICE, PRICE, PRICE, 7),)
    )
    assert held(tmp_path / bars.LIVE, [LINE]) == {(LINE, "1d")}
    assert (LINE, "1d") not in history.plan([LINE], held(tmp_path / bars.LIVE, [LINE]))
    first = datetime.combine(date(2026, 11, 16), conformance_tape.ROUNDS[0][0], UTC)
    assert main(tmp_path, first + timedelta(minutes=10), ["3"]) == 1
    assert "desk round" in capsys.readouterr().err


def test_a_pulled_bar_is_turned_from_the_brokers_unit_into_the_lines_currency(
    tmp_path: Path,
) -> None:
    pence = Bar(date(2026, 11, 12), PRICE, PRICE, PRICE, PRICE, 7)
    keeper(tmp_path / bars.LIVE, {"VUAG": 100})(LINE, "1d", (pence,))
    assert bars.daily(tmp_path / bars.LIVE, LINE)[0].close == Decimal("1.105")
    with pytest.raises(KeyError):
        keeper(tmp_path / bars.LIVE, {})(LINE, "1d", (pence,))


def test_hourly_four_hourly_and_weekly_bars_are_rolled_never_over_a_pulled_one(
    tmp_path: Path,
) -> None:
    live, keep = tmp_path / bars.LIVE, keeper(tmp_path / bars.LIVE, {"VUAG": 1})
    open_ = datetime(2026, 11, 12, 8, 0, tzinfo=UTC)  # a London session, 08:00 to 16:30
    halves = tuple(
        Candle(open_ + timedelta(minutes=30 * n), PRICE, PRICE, PRICE, PRICE, 1, "ibkr")
        for n in range(17)
    )
    days = tuple(Bar(date(2026, 11, d), PRICE, PRICE, PRICE, PRICE, 5) for d in range(9, 14))
    keep(LINE, "30m", halves[1:])  # the opening half hour is missing: no 08:00 hour, no 4h bar
    keep(LINE, "1d", days)
    assert (
        roll(live, LINE, open_ + timedelta(days=1)) == 8 + 2 + 1
    )  # 1h 09-16, 4h 12 and 16, a week
    keep(LINE, "1h", (Candle(open_ + timedelta(hours=1), PRICE, PRICE, PRICE, PRICE, 99, "ibkr"),))
    assert clashes(live, LINE, open_ + timedelta(days=1)) == []  # same prices: no fault
    other = Candle(open_ + timedelta(hours=2), PRICE, PRICE, PRICE, PRICE + 1, 99, "ibkr")
    keep(LINE, "1h", (other,))
    assert clashes(live, LINE, open_ + timedelta(days=1)) == [
        "VUAG 1h 2026-11-12 10:00: rolled and held differ"
    ]
    assert roll(live, LINE, open_ + timedelta(days=1)) == 0
    assert bars.sources(live, LINE, "1h") == {bars.Source.IBKR: 2, bars.Source.ROLLUP_30M: 6}
    assert bars.sources(live, LINE, "1wk") == {bars.Source.ROLLUP_1D: 1}


def test_fifteen_and_thirty_minute_bars_are_rolled_from_whole_five_minute_runs(
    tmp_path: Path,
) -> None:
    live, keep = tmp_path / bars.LIVE, keeper(tmp_path / bars.LIVE, {"VUAG": 1})
    open_ = datetime(2026, 11, 12, 8, 0, tzinfo=UTC)
    fives = tuple(
        Candle(open_ + timedelta(minutes=5 * n), PRICE, PRICE, PRICE, PRICE, 1, "ibkr")
        for n in range(12)
        if n != 4  # 08:20 is missing: no 08:15 quarter, no 08:00 half hour
    )
    keep(LINE, "5m", fives)
    assert roll(live, LINE, open_ + timedelta(days=1)) == 3 + 1  # quarters 08:00 30 45; half 08:30
    assert bars.sources(live, LINE, "15m") == {bars.Source.ROLLUP_5M: 3}
    assert bars.timed(live, LINE, "30m", open_, open_ + timedelta(hours=1))[0].volume == 6


def test_two_and_ten_minute_bars_are_rolled_from_whole_one_minute_runs(tmp_path: Path) -> None:
    live, keep = tmp_path / bars.LIVE, keeper(tmp_path / bars.LIVE, {"VUAG": 1})
    open_ = datetime(2026, 11, 12, 8, 0, tzinfo=UTC)
    ones = tuple(
        Candle(open_ + timedelta(minutes=n), PRICE, PRICE, PRICE, PRICE, 1, "ibkr")
        for n in range(10)
        if n != 3  # 08:03 is missing: no 08:02 pair, no 08:00 ten
    )
    keep(LINE, "1m", ones)
    roll(live, LINE, open_ + timedelta(days=1))
    assert bars.sources(live, LINE, "2m") == {bars.Source.ROLLUP_1M: 4}
    assert not bars.sources(live, LINE, "10m")


def test_five_minute_bars_are_rolled_from_whole_one_minute_runs_and_a_held_one_stays(
    tmp_path: Path,
) -> None:
    live, keep = tmp_path / bars.LIVE, keeper(tmp_path / bars.LIVE, {"VUAG": 1})
    open_ = datetime(2026, 11, 12, 8, 0, tzinfo=UTC)
    keep(LINE, "1m", tuple(
        Candle(open_ + timedelta(minutes=n), PRICE, PRICE, PRICE, PRICE, 1, "ibkr")
        for n in range(10) if n != 7))  # fmt: skip
    roll(live, LINE, open_ + timedelta(days=1))
    fives = bars.five(live, LINE, open_, open_ + timedelta(hours=1))
    assert [(b.start, b.volume) for b in fives] == [(open_, 5)]


def test_the_keepers_round_reads_and_tells_only_its_recent_window(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    live, keep = tmp_path / bars.LIVE, keeper(tmp_path / bars.LIVE, {"VUAG": 1})
    old, now = datetime(2025, 11, 12, 8, tzinfo=UTC), datetime(2026, 11, 12, 18, tzinfo=UTC)
    for day in (old, now.replace(hour=8)):
        keep(LINE, "5m", tuple(Candle(day + timedelta(minutes=5 * n), PRICE, PRICE, PRICE, PRICE,
                                      1, "ibkr") for n in range(24)))  # fmt: skip
    keep(LINE, "1d", (Bar(now.date(), PRICE, PRICE, PRICE, PRICE, 5),))
    keep(LINE, "15m", (Candle(old, PRICE, PRICE, PRICE, PRICE + 1, 9, "ibkr"),))  # an old clash
    firsts: list[int] = []
    reading = bars._read

    def counted(path: Path, line: Line, span: str, first: int, *rest: int | str) -> list[object]:
        firsts.extend([first] * (span != bars.DAILY))
        return list(reading(path, line, span, first, *rest))  # type: ignore[arg-type]

    monkeypatch.setattr(bars, "_read", counted)
    told = rounds.rolled(live, [LINE], now)  # the 5-minute round, as the keeper takes it
    assert firsts and min(firsts) >= (now - timedelta(weeks=3) - EPOCH).total_seconds()
    assert not [t for t in told if t.startswith("FAULT")]  # the year-old clash is not told again
    assert rounds.rolled(live, [LINE], now) == []  # the window rolled again: nothing new lands
    assert clashes(live, LINE, now) == ["VUAG 15m 2025-11-12 08:00: rolled and held differ"]


def test_the_archive_never_replaces_a_day_the_broker_holds_but_fills_the_day_it_lacks(
    tmp_path: Path,
) -> None:
    live, other = tmp_path / bars.LIVE, PRICE + 3
    keeper(live, {"VUAG": 1})(LINE, "1d", (Bar(date(2026, 11, 20), PRICE, PRICE, PRICE, PRICE, 7),))
    with bars.writing(live, bars.Source.ARCHIVE) as round_:
        round_.daily(LINE, [Bar(date(2026, 11, 19), other, other, other, other, 9),
                            Bar(date(2026, 11, 20), other, other, other, other, 90)])  # fmt: skip
    assert [(b.day.day, b.close, b.volume) for b in bars.daily(live, LINE)] == [
        (19, other, 9), (20, PRICE, 7)]  # fmt: skip
    assert bars.sources(live, LINE, bars.DAILY) == {bars.Source.IBKR: 1, bars.Source.ARCHIVE: 1}
    with sqlite3.connect(bars.files(live)[bars.DAILY]) as raw:
        assert raw.execute("SELECT count(*) FROM correction").fetchone() == (0,)
