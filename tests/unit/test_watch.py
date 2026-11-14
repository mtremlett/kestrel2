"""watch: one look reads each trading line's newest ended bar, or says why not; a crash halts
all buying at once, he is told once and the halt says why; the watch lifts its own halt only
when the market ends a day clear; a black swan is his alone, and is read twice before any
sale; one line's emergency halts nothing; a market that cannot be read is never calm."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from itertools import count
from pathlib import Path
from unittest.mock import Mock

import pytest

from desk import bars, halt, messenger, venues, watch
from desk.bars import Five
from desk.emergency import Level
from desk.lines import YARDSTICK, Line
from desk.store import Bar

#: Two whole sessions of both venues: London 08:00 to 16:30 UTC, New York 14:30 to 21:00.
WED, THU, FRI = (date(2025, 11, day) for day in (12, 13, 14))
THIN, TRIPLE = Line("THIN", "LSE", "GBP", 1), Line("THREE", "LSE", "GBP", 3)
ONE = Line("ONE", "US", "USD", 1)
CALM = (100,) * 20


def _at(clock: str, day: date = WED) -> datetime:
    return datetime.combine(day, time.fromisoformat(clock), UTC)


def _flat(close: int | str) -> tuple[Decimal, Decimal, Decimal, Decimal, int]:
    """A bar's prices and volume, with every price its close."""
    return (Decimal(close),) * 4 + (1,)


def _daily(day: date = WED, market: Sequence[int] = CALM) -> dict[Line, list[Bar]]:
    """Each line's daily bars before a day, every close 100 but the market's own."""
    kept = {}
    for line in (THIN, TRIPLE, YARDSTICK, ONE):
        closes = market if line == YARDSTICK else CALM
        days = venues.sessions(line.venue, day - timedelta(days=60), day)[-len(closes) - 1 : -1]
        kept[line] = [Bar(on, *_flat(c)) for on, c in zip(days, closes, strict=True)]
    return kept


def _trade(tmp: Path, line: Line, closes: Mapping[str, int | str], day: date = WED) -> None:
    """The line's five-minute bars into the fast store, each by the clock it starts at."""
    with bars.writing(tmp / "bars.db") as round_:
        round_.five(line, [Five(_at(at, day), *_flat(c)) for at, c in closes.items()])


def _look(
    tmp: Path, clock: str, post: Mock, day: date = WED, market: Sequence[int] = CALM
) -> watch.Look:
    return watch.look(tmp / "desk", tmp / "bars.db", _daily(day, market), _at(clock, day), post)


def _names(tmp: Path) -> list[str]:
    return [told.name for told in messenger.deliveries(tmp / "desk")]


def test_a_look_reads_each_trading_line_at_its_newest_ended_bar_or_says_why_not(
    tmp_path: Path,
) -> None:
    hot, daily = tmp_path / "bars.db", _daily()
    _trade(tmp_path, YARDSTICK, {"08:00": 99, "10:00": 98, "10:05": 95})
    _trade(tmp_path, THIN, {"08:30": 97})
    _trade(tmp_path, ONE, {"14:30": 99, "16:40": 96})
    early = watch.read(hot, daily, _at("08:03"))  #: no bar has ended yet, and none is late
    assert early.falls == () and set(early.unread) == {YARDSTICK, THIN, TRIPLE}
    assert early.blind is None, "blind before any bar could have ended"
    seen = watch.read(hot, daily, _at("10:07"))
    #: 10:05's bar has not ended (it would be a crash); THIN last traded at 08:30, and its
    #: venue has been heard from since; THREE, never in the store, has no bar
    assert {f.line: f.day for f in seen.falls} == {
        YARDSTICK: Decimal("0.02"),
        THIN: Decimal("0.03"),
    }
    assert seen.ended == {YARDSTICK: _at("10:05"), THIN: _at("08:35")}
    assert list(seen.unread) == [TRIPLE] and "no bar" in seen.unread[TRIPLE]
    crash = watch.read(hot, daily, _at("10:10"))  #: ended, and read
    assert crash.falls[-1].level is Level.CRASH and crash.blind is None
    assert watch.read(hot, daily, _at("10:30")).falls == crash.falls, "twenty minutes is not late"
    quiet = watch.read(hot, daily, _at("10:31"))  #: nothing from London for over twenty
    assert quiet.falls == () and set(quiet.unread) == {YARDSTICK, THIN, TRIPLE}
    assert quiet.blind is not None and "nothing heard of VUAG since 10:10 UTC" in quiet.blind
    _trade(tmp_path, THIN, {"10:25": 96})  #: London is heard from, the market itself is not
    deaf = watch.read(hot, daily, _at("10:31"))
    assert [f.line for f in deaf.falls] == [THIN] and deaf.blind == quiet.blind
    _trade(tmp_path, YARDSTICK, {"16:05": 99})  #: the closing auction makes no bar: none is late
    assert watch.read(hot, daily, _at("16:34")).blind is None, "blind in the closing auction"
    #: London shut and New York open: its line is read, and no market is owed
    evening = watch.read(hot, daily, _at("16:46"))
    assert {f.line: f.day for f in evening.falls} == {ONE: Decimal("0.04")}
    assert evening.unread == {} and evening.blind is None
    night = watch.read(hot, daily, _at("22:00"))
    assert (night.falls, night.unread, night.ended) == ((), {}, {})
    lone = {line: kept for line, kept in daily.items() if line != YARDSTICK}
    for kept, now in ((daily, datetime(2025, 11, 12, 10, 7)), (lone, _at("10:07"))):
        with pytest.raises(ValueError, match="no look at 2025-11-12 10:07"):
            watch.read(hot, kept, now)


def test_a_crash_halts_all_buying_at_once_tells_him_once_and_the_halt_says_why(
    tmp_path: Path,
) -> None:
    root, post = tmp_path / "desk", Mock(side_effect=count(1))
    _trade(tmp_path, YARDSTICK, {"10:00": 95, "10:05": 97, "11:00": 94})
    with pytest.raises(messenger.Undelivered):  #: his phone's door is down: halted all the same
        _look(tmp_path, "10:05", Mock(side_effect=messenger.Undelivered("no line")))
    (called,) = halt.in_force(root)
    fall = watch.read(tmp_path / "bars.db", _daily(), _at("10:05")).falls[0]
    assert (called.at, called.why) == (_at("10:05"), fall.words())
    assert (called.by, called.his) == (watch.WATCH, False)
    assert "CRASH" in called.why and "5.0% below its last close" in called.why
    #: the next look reads no crash: the halt stands, and he is owed its message all the same
    assert not _look(tmp_path, "10:10", post).cash and halt.in_force(root) == (called,)
    (told,) = messenger.deliveries(root)
    assert told.name == "watch 2025-11-12 VUAG CRASH" and told.text.startswith(called.why)
    assert "DONE: a halt is in force" in told.text
    _look(tmp_path, "10:15", post)
    assert halt.kept(root) == (called,) and post.call_count == 1, "called or told twice"
    #: he lifts it himself: the watch calls no other that day, says no more of it, and does
    #: the next day
    halt.lift(root, called, _at("10:50"), "his word")
    _look(tmp_path, "11:05", post)
    assert halt.in_force(root) == () and post.call_count == 1
    _trade(tmp_path, YARDSTICK, {"08:00": 90}, THU)
    _look(tmp_path, "08:05", post, THU, (*CALM[1:], 94))
    (again,) = halt.in_force(root)
    assert again.at == _at("08:05", THU) and "4.2% below its last close" in again.why
    assert _names(tmp_path) == [told.name, "watch 2025-11-13 VUAG CRASH"]


def test_the_watch_lifts_its_own_crash_halt_only_once_the_market_ends_a_day_clear(
    tmp_path: Path,
) -> None:
    root, post, after = tmp_path / "desk", Mock(side_effect=count(1)), (*CALM[1:], 95)
    other = halt.call(root, _at("07:00"), "another part's", by="the keeper", his=False)
    _trade(tmp_path, YARDSTICK, {"10:00": 95, "16:10": 99, "16:25": 95})
    for clock in ("10:05", "16:20", "16:36"):  #: called; calm near the close; it ended a crash
        _look(tmp_path, clock, post)
    _, crash = halt.in_force(root)  #: a reading within the day lifts nothing
    _trade(tmp_path, YARDSTICK, {"08:00": 96, "15:00": 91, "16:20": 96}, THU)
    _look(tmp_path, "15:05", post, THU, after)  #: a crash again: he is told, and no second halt
    _look(tmp_path, "16:36", post, THU, after)  #: its last bar has not landed: the end is unread
    assert halt.in_force(root) == (other, crash), "a second halt, or lifted on an end not read"
    _trade(tmp_path, YARDSTICK, {"16:25": "91.1"}, THU)  #: the day ended 4.1% down
    _look(tmp_path, "16:36", post, THU, after)
    assert halt.in_force(root) == (other, crash), "lifted on a day that ended a crash"
    _trade(tmp_path, YARDSTICK, {"16:25": 96}, THU)  #: restated: it ended clear
    _look(tmp_path, "16:33", post, THU, after)  #: in the closing auction the day is not over
    assert halt.in_force(root) == (other, crash), "lifted before the session ended"
    _look(tmp_path, "07:00", post, FRI, (*after, 96))  #: the first look since, next morning
    (ended,) = (called for called in halt.kept(root) if called.lifted)
    assert halt.in_force(root) == (other,) and ended.at == crash.at, "another's halt lifted"
    #: lifted as of the end of the day that ended clear, whenever the look came
    assert ended.lifted is not None and ended.lifted[0] == _at("16:35", THU)
    assert "the crash watch: the market ended 2025-11-13 clear of a crash" in ended.lifted[1]
    crashes = ["watch 2025-11-12 VUAG CRASH", "watch 2025-11-13 VUAG CRASH"]
    assert _names(tmp_path) == [*crashes, "watch 2025-11-13 VUAG lifted"]
    assert "HALT LIFTED at 2025-11-13 16:35 UTC" in messenger.deliveries(root)[-1].text


def test_a_black_swan_is_his_alone_to_lift_and_is_read_twice_before_any_sale(
    tmp_path: Path,
) -> None:
    root, post, after = tmp_path / "desk", Mock(side_effect=count(1)), (*CALM[1:], 99)
    hand = halt.call(root, _at("07:00"), "his word")
    _trade(tmp_path, YARDSTICK, {"09:55": 95, "10:00": 89})
    _look(tmp_path, "10:00", post)  #: a crash first, and its halt
    assert not _look(tmp_path, "10:05", post).cash, "sold on one reading"
    _, crash, swan = halt.in_force(root)  #: neither his own halt nor the crash's stands for it
    assert (swan.by, swan.his) == (watch.WATCH, True) and "BLACK SWAN" in swan.why
    assert not _look(tmp_path, "10:10", post).cash, "the same bar read again is one reading"
    _trade(tmp_path, YARDSTICK, {"10:10": 97})  #: a print the market took back
    assert not _look(tmp_path, "10:15", post).cash
    _trade(tmp_path, YARDSTICK, {"10:15": 88, "16:25": 99})
    _trade(tmp_path, TRIPLE, {"10:15": 70})  #: one line's emergency in the same look
    assert _look(tmp_path, "10:20", post).cash, "a later bar said so too, and it is not read twice"
    _, once, twice, _ = messenger.deliveries(root)
    assert _names(tmp_path) == [
        "watch 2025-11-12 VUAG CRASH",
        "watch 2025-11-12 VUAG BLACK_SWAN",
        "watch 2025-11-12 VUAG BLACK_SWAN twice",
        "watch 2025-11-12 THREE EMERGENCY",
    ], "the market's is not told first, or another line's fall is said to be read twice"
    assert all("NOT DONE: nothing is sold" in told.text for told in (once, twice))
    assert twice.text.startswith("BLACK SWAN, READ TWICE") and "12.0% below" in twice.text
    _look(tmp_path, "16:36", post)  #: the day ended clear: the crash's is lifted, never his
    assert halt.in_force(root) == (hand, swan) and post.call_count == 5  #: and tells him so
    #: next day his halt still stands, so the day's first reading is its second
    _trade(tmp_path, YARDSTICK, {"08:00": 88, "08:05": 88, "08:10": 94}, THU)
    assert _look(tmp_path, "08:05", post, THU, after).cash
    halt.lift(root, swan, _at("08:07", THU), "his word")  #: he says so, and it stands that day
    #: a black swan still, then a crash: no sale, and no halt of either kind
    sold = [_look(tmp_path, clock, post, THU, after).cash for clock in ("08:10", "08:15")]
    assert sold == [False, False], "sold on a black swan he lifted"
    assert halt.in_force(root) == (hand,), "called again on the day he lifted it"


def test_one_lines_emergency_halts_nothing_and_a_market_unread_is_told_and_never_calm(
    tmp_path: Path,
) -> None:
    root, post = tmp_path / "desk", Mock(side_effect=count(1))
    _trade(tmp_path, YARDSTICK, {"10:00": 99})
    _trade(tmp_path, TRIPLE, {"10:00": 70})
    _trade(tmp_path, ONE, {"16:40": 90})
    seen = _look(tmp_path, "10:05", post)
    assert [fall.level for fall in seen.falls] == [Level.EMERGENCY, None]
    #: blind, still blind, blind into another hour, then New York alone
    for clock in ("10:31", "10:36", "11:01", "16:45"):
        _look(tmp_path, clock, post)
    _trade(tmp_path, YARDSTICK, {"08:00": 50}, THU)  #: no market halves: unread, not a black swan
    _look(tmp_path, "08:05", post, THU)
    shock, blind, _, alone, unbelieved = messenger.deliveries(root)
    assert _names(tmp_path) == [
        "watch 2025-11-12 THREE EMERGENCY",
        "watch 2025-11-12 10h blind",
        "watch 2025-11-12 11h blind",
        "watch 2025-11-12 ONE EMERGENCY",
        "watch 2025-11-13 08h blind",
    ]
    assert "30.0% below its last close" in shock.text and "NOT DONE" in shock.text
    assert "THE CRASH WATCH IS BLIND" in blind.text and "since 10:05 UTC" in blind.text
    assert "ONE, on 2025-11-12, is 10.0% below" in alone.text
    assert "no fall is read from its bar of 2025-11-13 08:00" in unbelieved.text
    assert halt.kept(root) == (), "a halt called for one line, or for a market not read"
