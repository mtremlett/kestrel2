"""The store's keeper: one command does whatever the store is owed when it is called. Each
venue's daily bars are refreshed in the morning and again once its day has settled, the
five-minute round is taken in its hours, a refused line is parked alone and asked again, and
a venue the archive answers nothing for is a miss."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk import archive, bars, keeper, venues
from desk.bars import Five
from desk.lines import Line
from desk.store import Bar

UK, US, TWIN = (
    Line("BBB", "LSE", "GBP", 1),
    Line("AAA", "US", "USD", 1),
    Line("CCC", "US", "USD", 1),
)
LINES = (UK, US, TWIN)
MON = date(2026, 11, 16)  #: a session of both venues: London to 16:35, New York to 21:00 UTC
ROUND = (
    "LSE: five-minute round: {} of 1 lines kept, 0 of them with faults listed, {} refused by "
    "the archive"
)
SAT, YULE = date(2026, 11, 14), date(2026, 12, 25)  #: no venue trades on either


def _at(hour: int, minute: int = 0, day: date = MON) -> datetime:
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=UTC)


def _bars(line: Line, day: date) -> tuple[Bar, ...]:
    """A line's sessions since August up to, not including, a day: no two alike."""
    days = venues.sessions(line.venue, date(2026, 8, 3), day - timedelta(1))
    prices = [Decimal(100 + n % 5) for n in range(len(days))]
    return tuple(
        Bar(d, p, p + 1, p - 1, p, 1000 + n)
        for n, (d, p) in enumerate(zip(days, prices, strict=True))
    )


class Archive:
    """The archive, pretended: what it was asked, the lines it refuses and those it is a
    session short on, and a clock that reads seventy seconds more each time it is looked at."""

    def __init__(self) -> None:
        self.asked: list[str] = []
        self.refuses: set[str] = set()
        self.short: set[str] = set()
        self.looks = 0

    def daily(self, line: Line, day: date) -> tuple[Bar, ...]:
        self.asked.append(line.symbol)
        if line.symbol in self.refuses:
            raise OSError("no route to the archive")
        return _bars(line, day)[: -1 if line.symbol in self.short else None]

    def five(self, line: Line, now: datetime) -> tuple[Five, ...]:
        self.asked.append(f"{line.symbol} 5m")
        if line.symbol in self.refuses:
            raise OSError("no route to the archive")
        return (Five(now - timedelta(minutes=5), *(Decimal(10),) * 4, 7),)

    def clock(self) -> float:
        self.looks += 1
        return 70.0 * self.looks

    def keep(self, home: Path, now: datetime, slow: bool = False) -> tuple[list[str], list[str]]:
        """One call of the keeper, and what it asked is all that `asked` then holds."""
        self.asked.clear()
        clock = self.clock if slow else lambda: 0.0
        return keeper.keep(home, now, LINES, self.daily, self.five, clock)


def test_a_trading_day_is_kept_each_venue_on_its_own_hours(tmp_path: Path) -> None:
    pretend, tue = Archive(), MON + timedelta(1)
    said, missed = pretend.keep(tmp_path, _at(6))
    assert (pretend.asked, missed) == (["BBB", "AAA", "CCC"], [])
    assert said[1] == (
        "US: daily bars before 2026-11-16: 2 of 2 lines clean, 0 refused by the archive "
        "(asked 1 times today)"
    )
    assert keeper.saved(tmp_path, MON, LINES) == (
        {line: _bars(line, MON) for line in LINES},
        frozenset(),
    )
    with pytest.raises(keeper.Stale, match="BBB: no LSE bars before 2026-11-17 .* for 2026-11-16"):
        keeper.saved(tmp_path, tue, LINES)
    assert pretend.keep(tmp_path, _at(6, 5)) == ([], []) and pretend.asked == []
    said, missed = pretend.keep(tmp_path, _at(9))  # London is open, New York is not
    assert (pretend.asked, missed) == (["BBB 5m"], [])
    assert said == [ROUND.format(1, 0)]
    assert [bar.start for bar in bars.five(tmp_path / keeper.HOT, UK, _at(0), _at(9))] == [
        _at(8, 55)
    ]
    pretend.keep(tmp_path, _at(17))  # London is over; its last bars are still coming in
    assert pretend.asked == ["BBB 5m", "AAA 5m", "CCC 5m"]
    pretend.keep(tmp_path, _at(17, 5))  # its day has settled: the closes, and the last round
    assert pretend.asked == ["BBB", "BBB 5m", "AAA 5m", "CCC 5m"]
    pretend.keep(tmp_path, _at(17, 10))
    assert pretend.asked == ["AAA 5m", "CCC 5m"]
    assert keeper.saved(tmp_path, tue, [UK])[0][UK][-1].day == MON  # London's close is held
    with pytest.raises(keeper.Stale, match="AAA: no US bars before 2026-11-17"):
        keeper.saved(tmp_path, tue, LINES)
    pretend.keep(tmp_path, _at(21, 30))
    assert pretend.asked == ["AAA", "CCC", "AAA 5m", "CCC 5m"]
    assert keeper.saved(tmp_path, tue, LINES)[0] == {line: _bars(line, tue) for line in LINES}
    assert keeper.saved(tmp_path, MON, LINES)[0][US] == _bars(US, MON)  # a day back: no bar of it
    pretend.keep(tmp_path, _at(6, day=tue))  # the evening's bars are asked again in the morning
    assert pretend.asked == ["BBB", "AAA", "CCC"]


def test_a_line_unanswered_keeps_what_its_day_holds_is_asked_again_and_a_blind_venue_is_a_miss(
    tmp_path: Path,
) -> None:
    pretend, tue, wed = Archive(), MON + timedelta(1), MON + timedelta(2)
    with pytest.raises(keeper.Stale, match="AAA: no US bars before 2026-11-16 .* never refreshed"):
        keeper.saved(tmp_path, MON, [US])
    pretend.short = {"CCC"}
    assert pretend.keep(tmp_path, _at(6))[1] == []  # a line a session short is a fault, no miss
    held, parked = keeper.saved(tmp_path, MON, LINES)
    assert (held[TWIN], parked) == (_bars(TWIN, MON)[:-1], frozenset({"CCC"}))
    for call in range(2, keeper.TRIES + 3):  # a fault is asked again TRIES times, then left
        pretend.keep(tmp_path, _at(6, 5 * call))
        assert pretend.asked == ["CCC"] * (call <= keeper.TRIES)
    pretend.keep(tmp_path, _at(21, 30))  # the evening, readied for Tuesday: CCC still short
    pretend.refuses, pretend.short = {"AAA", "BBB"}, set()  # and whole again by the morning
    for minute in (0, 5):  # Tuesday morning the archive is away for two: what is held stands
        said, missed = pretend.keep(tmp_path, _at(6, minute, tue))
        assert pretend.asked == ["BBB", "AAA", "CCC"][: 3 - minute // 5]  # only the two again
        assert missed == [said[0]] and said[0].startswith("LSE: daily bars before 2026-11-17: 1 of")
        held, parked = keeper.saved(tmp_path, tue, LINES)
        assert held == {line: _bars(line, tue) for line in LINES} and not parked
    said, missed = pretend.keep(tmp_path, _at(17, 5, tue))  # a new day's bars: none stand for it
    assert missed == [said[0], ROUND.format(0, 1)]
    assert keeper.saved(tmp_path, wed, [UK]) == ({UK: ()}, frozenset({"BBB"}))
    pretend.refuses, pretend.short = set(), {"BBB"}
    for call in range(keeper.TRIES + 2):  # answered, yet no line clean: a miss, and never left
        said, missed = pretend.keep(tmp_path, _at(18, 5 * call, tue))
        assert pretend.asked[0] == "BBB" and missed == [said[0]]


def test_nothing_is_asked_on_a_day_no_venue_trades_nor_once_the_calls_time_is_spent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    pretend = Archive()
    for shut in (SAT, YULE):
        assert pretend.keep(tmp_path, _at(9, day=shut)) == ([], []) and pretend.asked == []
    assert list(tmp_path.iterdir()) == [] and keeper.main(tmp_path, _at(9, day=SAT)) == 0
    said, missed = pretend.keep(tmp_path, _at(15), slow=True)  # both open; its time spent in two
    assert pretend.asked == ["BBB", "BBB 5m"] and missed == said[2:] and len(said) == 4
    assert keeper.saved(tmp_path, MON, LINES)[1] == {"AAA", "CCC"}
    with pytest.raises(ValueError, match="not a moment in UTC"):
        keeper.keep(tmp_path, datetime(2026, 11, 16, 6))

    week = int((_at(9) - keeper.RECENT).timestamp())  # a round asks the week kept hot, no more

    def unreachable(address: str) -> bytes:
        assert ("interval=5m" in address) == (f"period1={week}&" in address)
        raise OSError(f"no route to {address[:13]}")

    monkeypatch.setattr(archive, "_ask", unreachable)
    assert keeper.main(tmp_path / "real", _at(9)) == 1  # the command itself, the archive away
    out, err = capsys.readouterr()
    assert len(out.splitlines()) == 3 and err.count("MISSED: ") == 3 and "MISSED: US: daily" in err
