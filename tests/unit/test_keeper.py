"""The store's keeper: one command does whatever the store is owed when it is called. Each
venue's daily bars are refreshed in the morning and again once its day has settled, the
five-minute round is taken in its hours, a refused line is parked alone and asked again, and
a venue the archive answers nothing for is a miss."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk import archive, bars, keeper, keeper_live, paper, store, venues
from desk.bars import Five, Source
from desk.lines import POUND, YARDSTICK, Line
from desk.spans import Timed
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
    "the broker ({}); past days backfilled from the archive for 1 of 1 lines; {}"
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
        self.silent: set[str] = set()  #: lines the broker gives no bar for
        self.looks = 0

    def daily(self, line: Line, day: date) -> tuple[Bar, ...]:
        self.asked.append(line.symbol)
        if line.symbol in self.refuses:
            raise OSError("no route to the archive")
        return _bars(line, day)[: -1 if line.symbol in self.short else None]

    def five(self, line: Line, now: datetime) -> tuple[Five, ...]:
        """The broker's: the ended bar of the moment, or silence."""
        self.asked.append(f"{line.symbol} 5m")
        if line.symbol in self.refuses | self.silent:
            raise ValueError("no IBKR real-time data on paper")
        return (Five(now - timedelta(minutes=5), *(Decimal(10),) * 4, 7),)

    def past(self, _line: Line, now: datetime) -> tuple[Five, ...]:
        """The archive's: a bar of today, which must never land, and one of Friday."""
        return tuple(
            Five(now - back, *(Decimal(20),) * 4, 9) for back in (timedelta(0), timedelta(3))
        )

    def clock(self) -> float:
        self.looks += 1
        return 70.0 * self.looks

    def keep(
        self, home: Path, now: datetime, slow: bool = False, series: tuple[Line, ...] = ()
    ) -> tuple[list[str], list[str]]:
        """One call of the keeper, and what it asked is all that `asked` then holds."""
        self.asked.clear()
        clock = self.clock if slow else lambda: 0.0
        return keeper.keep(
            home, now, LINES, self.daily, self.five, clock, self.daily, series, None, self.past
        )


def test_a_shelved_history_joins_the_archive_and_a_database_not_yet_written_is_stale(
    tmp_path: Path,
) -> None:
    older = tuple(replace(bar, day=bar.day.replace(month=6)) for bar in _bars(UK, MON)[:2])
    store.shelve(tmp_path / keeper.DAILY / UK.venue, UK, older)
    Archive().keep(tmp_path, _at(6))
    assert keeper.saved(tmp_path, MON, [UK])[0][UK][:2] == older  # parked for the gap, kept
    (tmp_path / bars.HISTORY).unlink()
    with pytest.raises(keeper.Stale, match="BBB: the long database holds no LSE bars"):
        keeper.saved(tmp_path, MON, [UK])


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
    files = {f.name for f in tmp_path.rglob("*") if f.is_file()}
    assert files == {"market_history.db", "market_live.db", keeper.RECORD}  # two databases, no CSV
    assert not any("kestrel" in name for name in files)
    with pytest.raises(keeper.Stale, match="BBB: no LSE bars before 2026-11-17 .* for 2026-11-16"):
        keeper.saved(tmp_path, tue, LINES)
    assert pretend.keep(tmp_path, _at(6, 5)) == ([], []) and pretend.asked == []
    said, missed = pretend.keep(tmp_path, _at(9))  # London is open, New York is not
    assert (pretend.asked, missed) == (["BBB 5m"], [])
    assert said == [ROUND.format(1, 0, "none", "newest bar landed 0 minutes after it ended")]
    assert [bar.start for bar in bars.five(tmp_path / keeper.HOT, UK, _at(0), _at(9))] == [
        _at(8, 55)
    ]
    hot = tmp_path / keeper.HOT
    assert bars.sources(hot, UK, bars.FIVE) == {Source.IBKR: 1, Source.BACKFILL: 1}
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


def test_the_reference_series_is_kept_once_a_day_after_the_us_close(tmp_path: Path) -> None:
    pretend, spy = Archive(), Line("SPY", "US", "USD", 1)
    for early in (_at(6), _at(20, 55), _at(9, day=SAT)):  # no US close yet, or no US day
        pretend.keep(tmp_path, early, series=(spy,))
        assert "SPY" not in pretend.asked
    pretend.keep(tmp_path, _at(21, 30), series=(spy,))
    assert pretend.asked.count("SPY") == 1
    assert len(bars.daily(tmp_path / keeper.HOT, spy)) > 50
    pretend.keep(tmp_path, _at(21, 35), series=(spy,))  # the same day again: nothing new
    assert "SPY" not in pretend.asked
    pretend.refuses = {"SPY"}
    pretend.keep(tmp_path, _at(6, day=MON + timedelta(1)), series=(spy,))
    done, missed = pretend.keep(tmp_path, _at(21, 30, MON + timedelta(1)), series=(spy,))
    assert missed == [] and "SPY: reference series not kept" in done[-1]  # told, asked again
    pretend.refuses = set()
    pretend.keep(tmp_path, _at(21, 35, MON + timedelta(1)), series=(spy,))
    assert pretend.asked.count("SPY") == 1


def test_the_days_pounds_per_dollar_is_read_for_any_session_and_stale_when_none_is_held(
    tmp_path: Path,
) -> None:
    def pounds(_line: Line, day: date) -> tuple[Bar, ...]:
        days = venues.sessions("US", date(2026, 9, 1), day - timedelta(1))
        close = [Decimal("1.25") + Decimal(n % 4) / 100 for n in range(len(days))]
        return tuple(Bar(d, c, c, c, c, 0) for d, c in zip(days, close, strict=True))

    with pytest.raises(keeper.Stale):
        keeper.pound(tmp_path, MON)  # nothing kept yet
    args = (tmp_path, _at(21, 30), (), Archive().daily, Archive().five, lambda: 0.0, pounds)
    keeper.keep(*args, series=(POUND,))
    last = venues.sessions("US", date(2026, 9, 1), MON - timedelta(1))  #: the close before MON
    want = 1 / (Decimal("1.25") + Decimal((len(last) - 1) % 4) / 100)
    assert keeper.pound(tmp_path, MON) == want.quantize(Decimal("0.000001"))
    assert keeper.pound(tmp_path, date(2026, 10, 14)) > 0  # a past session reads as well
    with pytest.raises(keeper.Stale):
        keeper.pound(tmp_path, MON + timedelta(14))  # a fortnight on, nothing fresh


def test_a_store_kept_under_older_rules_is_cleaned_again_and_a_current_one_is_not(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pretend = Archive()
    pretend.keep(tmp_path, _at(6))
    assert pretend.keep(tmp_path, _at(6, 5)) == ([], []) and pretend.asked == []  # current
    monkeypatch.setattr(keeper, "RULES", "an older set of rules")
    pretend.keep(tmp_path, _at(6, 10))  # the rules changed: every line, from the archive
    assert pretend.asked == ["BBB", "AAA", "CCC"]
    monkeypatch.undo()
    pretend.keep(tmp_path, _at(6, 15))
    assert pretend.asked == ["BBB", "AAA", "CCC"]  # kept under the other rules: again
    assert pretend.keep(tmp_path, _at(6, 20)) == ([], []) and pretend.asked == []


def test_the_live_session_is_the_brokers_alone_and_the_archive_only_backfills_a_past_day(
    tmp_path: Path,
) -> None:
    pretend, hot = Archive(), tmp_path / keeper.HOT
    pretend.silent = {"BBB"}
    said, missed = pretend.keep(tmp_path, _at(9))  # London is open and IBKR gives it nothing
    silence = "ValueError: no IBKR real-time data on paper"
    assert missed == [ROUND.format(0, 1, silence, "no bar landed")] and missed[0] in said
    today = bars.five(hot, UK, _at(0), _at(10))
    assert today == ()  # the archive's bar of this session never entered it
    assert bars.sources(hot, UK, bars.FIVE) == {Source.BACKFILL: 1}  # yesterday's gap, named
    pretend.silent = set()
    assert pretend.keep(tmp_path, _at(9, 5))[1] == []  # IBKR speaks again: the line comes back
    assert [b.close for b in bars.five(hot, UK, _at(0), _at(10))] == [Decimal(10)]


def test_the_yardstick_is_asked_first_in_the_five_minute_round(tmp_path: Path) -> None:
    pretend = Archive()
    args = (tmp_path, _at(9), (UK, YARDSTICK), pretend.daily, pretend.five, lambda: 0.0)
    keeper.keep(*args, series=(), back=pretend.past)
    assert [a for a in pretend.asked if a.endswith("5m")] == ["VUAG 5m", "BBB 5m"]


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
    assert missed == [
        said[0],
        ROUND.format(0, 1, "ValueError: no IBKR real-time data on paper", "no bar landed"),
    ]
    assert keeper.saved(tmp_path, wed, [UK]) == ({UK: ()}, frozenset({"BBB"}))
    pretend.refuses, pretend.short = set(), {"BBB"}
    for call in range(keeper.TRIES + 2):  # answered, yet no line clean: a miss, and never left
        said, missed = pretend.keep(tmp_path, _at(18, 5 * call, tue))
        assert pretend.asked[0] == "BBB" and missed == [said[0]]


def test_nothing_is_asked_on_a_day_no_venue_trades_nor_once_the_calls_time_is_spent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    pretend = Archive()
    said, missed = pretend.keep(tmp_path, _at(9, day=SAT))  # a store never filled is owed its bars
    assert pretend.asked == ["BBB", "AAA", "CCC"] and len(said) == 2 and missed == []
    assert keeper.saved(tmp_path, MON, LINES)[0][UK] == _bars(UK, MON)  # ready for Monday
    assert pretend.keep(tmp_path, _at(9, 5, SAT)) == ([], []) and pretend.asked == []
    monkeypatch.setattr(keeper, "LINES", LINES)  # the command judges these lines
    assert keeper.main(tmp_path, _at(9, day=SAT)) == 0  # held: nothing is owed, nothing asked
    other, pretend.refuses = tmp_path / "other", {"AAA"}
    for minute in (0, 5, 10):  # a line refused at a weekend is asked again, as on any day
        pretend.keep(other, _at(10, minute, SAT))
        pretend.refuses = set() if minute else pretend.refuses
        assert pretend.asked == (["AAA"] if minute else ["BBB", "AAA", "CCC"])
    assert keeper.saved(other, MON, LINES) == (
        {line: _bars(line, MON) for line in LINES},
        frozenset(),
    )
    pretend.refuses = {"AAA"}  # Monday morning AAA is away: no session since, its bars stand
    assert pretend.keep(other, _at(6))[1] == [] and pretend.asked == ["BBB", "AAA", "CCC"]
    assert keeper.saved(other, MON, [US]) == ({US: _bars(US, MON)}, frozenset())
    said, missed = pretend.keep(tmp_path, _at(15), slow=True)  # both open; its time spent in two
    assert pretend.asked == ["BBB", "BBB 5m"] and missed == said[2:] and len(said) == 4
    assert keeper.saved(tmp_path, MON, LINES)[1] == frozenset()  # the weekend's bars stand
    pretend.refuses = set()
    pretend.keep(tmp_path, _at(21, 30, YULE - timedelta(1)))  # Christmas Eve's closes are held
    assert pretend.keep(tmp_path, _at(9, day=YULE)) == ([], []) and pretend.asked == []
    with pytest.raises(ValueError, match="not a moment in UTC"):
        keeper.keep(tmp_path, datetime(2026, 11, 16, 6))

    week = int((_at(9) - keeper_live.RECENT).timestamp())  # a round asks the week kept hot, no more

    def unreachable(address: str) -> bytes:
        assert ("interval=5m" in address) == (f"period1={week}&" in address)
        raise OSError(f"no route to {address[:13]}")

    monkeypatch.setattr(archive, "_ask", unreachable)

    def no_gateway(_talk: object) -> object:
        raise ConnectionRefusedError("no gateway in a test")

    monkeypatch.setattr(paper, "dial", no_gateway)
    monkeypatch.setattr(paper, "CLIENT", paper.CLIENT)  # the live ask makes this process its reader
    assert keeper.main(tmp_path / "real", _at(9)) == 1  # the command itself, the archive away
    out, err = capsys.readouterr()
    assert len(out.splitlines()) == 4 and "parked live, not traded" in out
    assert err.count("MISSED: ") == 6 and "MISSED: US: daily" in err
    assert err.count("MISSED: stale: ") == 3  # nothing held: each line is staler than a session


def test_the_closes_are_held_within_the_named_figure_after_each_venues_close(
    tmp_path: Path,
) -> None:
    pretend, tue = Archive(), MON + timedelta(1)
    for venue, line in (("LSE", UK), ("US", US)):
        auction = venues.hours(venue, MON).auction
        pretend.keep(tmp_path / venue, _at(6, 5))
        start = auction + keeper.SETTLED - timedelta(seconds=1)  # the runner's worst luck
        for call in range(12):  # its calls, one in five minutes, each taking four to finish
            at = start + timedelta(minutes=5 * call)
            pretend.keep(tmp_path / venue, at)
            if keeper.target(venue, at) == tue:
                break
        assert keeper.saved(tmp_path / venue, tue, [line])[0][line][-1].day == MON
        held = at + timedelta(minutes=4) - auction
        assert keeper.HELD - timedelta(minutes=1) < held <= keeper.HELD
    for venue in venues.RULES:  # held before the runner's 22:00, UK time, on every session
        for day in venues.sessions(venue, date(2026, 11, 16), date(2027, 12, 31)):
            done = venues.hours(venue, day).auction + keeper.HELD
            assert done.astimezone(venues.zone("LSE", day)).hour < 22


def test_a_parked_yardstick_is_a_first_light_fault_never_silent(tmp_path: Path) -> None:
    """R-RUNNER-189: VUAG is the measure of everything; parked, the keeper says why and misses."""
    pretend = Archive()
    pretend.short = {YARDSTICK.symbol}
    kept = keeper.keep(tmp_path, _at(6), (YARDSTICK,), pretend.daily, pretend.five, lambda: 0.0)
    assert kept[1][-1].startswith(f"FIRST-LIGHT FAULT: the yardstick {YARDSTICK.symbol} is parked")


def test_a_line_the_archive_refuses_is_kept_from_the_brokers_bars_not_parked(
    tmp_path: Path,
) -> None:
    """R-RUNNER-189: the broker is the first source; the archive's refusal is no miss."""
    pretend = Archive()
    pretend.refuses = {UK.symbol}
    kept = keeper.keep(
        tmp_path, _at(6), (UK,), pretend.daily, pretend.five, lambda: 0.0,
        broker=lambda lines, day: {line: _bars(line, day) for line in lines},
    )  # fmt: skip
    assert kept[1] == [] and keeper.saved(tmp_path, MON, [UK])[0][UK] == _bars(UK, MON)


def test_the_kept_pound_tells_dollars_among_pounds_from_a_move_and_none_kept_parks_the_line(
    tmp_path: Path,
) -> None:
    """R-RUNGS-16 (SGLN, EQQQ): a London bar in dollars among pounds is dropped on the pound
    the long database holds; with no pound held the same bars are a lasting step, and park."""
    rate = Decimal("1.65")

    def dollars(bar: Bar) -> Bar:
        return Bar(bar.day, bar.open * rate, bar.high * rate, bar.low * rate, bar.close * rate, 9)

    tens = tuple(dollars(bar) if n in (3, 8, 12) else bar for n, bar in enumerate(_bars(UK, MON)))
    pretend = Archive()
    pretend.daily = lambda *_: tens  # type: ignore[method-assign]  # one canned answer
    both, bare = tmp_path / "both", tmp_path / "bare"
    with bars.writing(both / keeper.HOT) as round_:
        round_.daily(POUND, tuple(Bar(b.day, rate, rate, rate, rate, 0) for b in tens))
    for home in (both, bare):
        pretend.keep(home, _at(6))
    assert not keeper.saved(both, MON, [UK])[1]
    assert keeper.saved(bare, MON, [UK])[1] == {UK.symbol}


def test_a_live_run_asks_the_two_lines_due_keeps_their_minutes_and_names_a_stale_one(
    tmp_path: Path,
) -> None:
    rota = tuple(Line(f"L{n:02}", "LSE", "GBP", 1) for n in range(20))
    now, asked = _at(10), []

    def ask(line: Line, when: datetime) -> tuple[Timed, ...]:
        asked.append(line)
        start = when - timedelta(minutes=1 if line != rota[0] else 9)
        price = Decimal(5)
        return (Timed("1m", start, price, price, price, price, 1),)

    words, stale = keeper_live.minute_round(tmp_path / keeper.HOT, rota, now, ask)
    assert asked == list(keeper_live.due(rota, now)) and len(set(asked)) == 2
    held = [
        bars.timed(tmp_path / keeper.HOT, line, "1m", now - timedelta(1), now) for line in asked
    ]
    assert [len(h) for h in held] == [1, 1] and words.startswith("live: ")
    assert asked == [rota[0], rota[1]] and [s.split(":")[0] for s in stale] == ["L00"]
    assert keeper_live.due(rota, now + timedelta(minutes=10)) == tuple(asked)
