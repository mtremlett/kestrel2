"""watch: one look reads each trading line's newest ended bar, or says why not; a crash, as
the market trades or as its day ended, halts all buying at once, he is told once and the
halt says why; only a day that ends clear lifts it; his own lift is his word; a black swan
is his alone, and is read twice before any sale; one line's emergency halts nothing; a
market that cannot be read is never calm."""

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

#: Three whole sessions of both venues: London 08:00 to 16:30 UTC, New York 14:30 to 21:00.
WED, THU, FRI = (date(2025, 11, day) for day in (12, 13, 14))
THIN, TRIPLE = Line("THIN", "LSE", "GBP", 1), Line("THREE", "LSE", "GBP", 3)
ONE = Line("ONE", "US", "USD", 1)
CALM = (100,) * 21  #: the market's daily closes up to the Tuesday before; a fall reads twenty


@pytest.fixture(autouse=True)
def _tuesday(tmp_path: Path) -> None:
    """The store holds the last bar of the session before the first: it ended calm."""
    _trade(tmp_path, YARDSTICK, {"16:25": 100}, date(2025, 11, 11))


def _at(clock: str, day: date = WED) -> datetime:
    return datetime.combine(day, time.fromisoformat(clock), UTC)


def _flat(close: int | str) -> tuple[Decimal, Decimal, Decimal, Decimal, int]:
    """A bar's prices and volume, with every price its close."""
    return (Decimal(close),) * 4 + (1,)


def _daily(day: date = WED, market: Sequence[int] = CALM) -> dict[Line, list[Bar]]:
    """Each line's daily bars before a day, every close 100 but the market's own."""
    kept = {}
    for line in (THIN, TRIPLE, YARDSTICK, ONE):
        closes = market if line == YARDSTICK else CALM[1:]
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
    assert (night.falls, night.unread, night.cash) == ((), {}, False)
    lone = {line: kept for line, kept in daily.items() if line != YARDSTICK}
    for kept, now in ((daily, datetime(2025, 11, 12, 10, 7)), (lone, _at("10:07"))):
        with pytest.raises(ValueError, match="no look at 2025-11-12 10:07"):
            watch.read(hot, kept, now)


def test_a_crash_halts_all_buying_at_once_tells_him_once_and_his_lift_is_his_word(
    tmp_path: Path,
) -> None:
    root, post = tmp_path / "desk", Mock(side_effect=count(1))
    _trade(tmp_path, YARDSTICK, {"10:00": 95, "10:05": 97, "11:00": 94, "16:25": 94})
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
    assert told.name == "watch 2025-11-12 10:05 CRASH" and told.text.startswith(called.why)
    assert "DONE: a halt is in force" in told.text
    _look(tmp_path, "10:15", post)
    assert halt.kept(root) == (called,) and post.call_count == 1, "called or told twice"
    #: HIS WORD: he lifts it, and while the market has not ended a day clear the watch calls
    #: no other, telling him once a day that it reads a crash and buys
    halt.lift(root, called, _at("10:50"), "his word")
    for clock in ("11:05", "11:10", "16:36"):  #: a crash at each, and the day ended one
        _look(tmp_path, clock, post)
    _trade(tmp_path, YARDSTICK, {"08:00": 90, "16:25": 93}, THU)
    _look(tmp_path, "08:05", post, THU, (*CALM, 94))  #: the next day too, which ends clear
    assert halt.in_force(root) == (), "a halt called over his word"
    word = messenger.deliveries(root)[1]
    assert "NOT DONE: no halt is called" in word.text and "2025-11-12 10:50 UTC" in word.text
    _trade(tmp_path, YARDSTICK, {"08:00": 89}, FRI)  #: a day ended clear: a crash is new
    _look(tmp_path, "08:05", post, FRI, (*CALM, 94, 93))
    (again,) = halt.in_force(root)
    assert again.at == _at("08:05", FRI) and "4.3% below its last close" in again.why
    assert _names(tmp_path) == [
        told.name,
        "watch 2025-11-12 CRASH on his word",
        "watch 2025-11-13 CRASH on his word",
        "watch 2025-11-14 08:05 CRASH",
    ]


def test_a_crash_the_desk_slept_through_is_halted_whenever_it_next_looks(
    tmp_path: Path,
) -> None:
    root, post = tmp_path / "desk", Mock(side_effect=count(1))
    _trade(tmp_path, YARDSTICK, {"13:50": 99})
    _look(tmp_path, "13:55", post)  #: calm, and then the desk is down as the market falls
    _trade(tmp_path, YARDSTICK, {"15:00": 95, "15:05": 99, "16:20": 99})  #: and comes back
    for clock in ("16:36", "17:00"):  #: one bar read a crash; the day's last has not landed
        _look(tmp_path, clock, post)
    (slept,) = halt.in_force(root)
    assert slept.at == _at("16:36") and "5.0% below its last close" in slept.why
    assert _names(tmp_path) == ["watch 2025-11-12 16:36 CRASH", "watch 2025-11-12 end unread"]
    _trade(tmp_path, YARDSTICK, {"16:25": 99})  #: it lands: the day ended clear after all
    _look(tmp_path, "07:55", post, THU, (*CALM, 99))
    assert halt.in_force(root) == (), "a day read to have ended clear did not lift its halt"
    _trade(tmp_path, YARDSTICK, {"16:25": 95}, THU)  #: a day that fell at its last bar alone
    _look(tmp_path, "20:00", post, THU, (*CALM, 99))  #: seen that evening, London long shut
    (ended,) = halt.in_force(root)
    assert ended.at == _at("20:00", THU) and "4.0% below its last close" in ended.why
    assert _names(tmp_path)[2:] == ["watch 2025-11-12 16:36 lifted", "watch 2025-11-13 20:00 CRASH"]


def test_the_watch_lifts_its_own_crash_halt_only_once_the_market_ends_a_day_clear(
    tmp_path: Path,
) -> None:
    root, post, after = tmp_path / "desk", Mock(side_effect=count(1)), (*CALM, 95)
    other = halt.call(root, _at("07:00"), "another part's", by="the keeper", his=False)
    _trade(tmp_path, YARDSTICK, {"10:00": 95, "16:10": 99, "16:25": 95})
    for clock in ("10:05", "16:20", "16:36"):  #: called; calm near the close; it ended a crash
        _look(tmp_path, clock, post)
    _, crash = halt.in_force(root)  #: a reading within the day lifts nothing
    _trade(tmp_path, YARDSTICK, {"08:00": 96, "15:00": 91, "16:20": 96}, THU)
    _look(tmp_path, "15:05", post, THU, after)  #: a crash again: no second halt, no more said
    _look(tmp_path, "16:36", post, THU, after)  #: its last bar has not landed: the end is unread
    assert halt.in_force(root) == (other, crash), "a second halt, or lifted on an end not read"
    _trade(tmp_path, YARDSTICK, {"16:25": "91.1"}, THU)  #: the day ended 4.1% down
    _look(tmp_path, "16:36", post, THU, after)
    assert halt.in_force(root) == (other, crash), "lifted on a day that ended a crash"
    _trade(tmp_path, YARDSTICK, {"16:25": 96}, THU)  #: restated: it ended clear
    _look(tmp_path, "16:33", post, THU, after)  #: in the closing auction the day is not over
    assert halt.in_force(root) == (other, crash) and post.call_count == 1
    _look(tmp_path, "07:00", post, FRI, (*after, 96))  #: the first look since, next morning
    (ended,) = (called for called in halt.kept(root) if called.lifted)
    assert halt.in_force(root) == (other,) and ended.at == crash.at, "another's halt lifted"
    #: lifted as of the end of the day that ended clear, whenever the look came
    assert ended.lifted is not None and ended.lifted[0] == _at("16:35", THU)
    assert "the crash watch: the market ended 2025-11-13 clear of a crash" in ended.lifted[1]
    assert _names(tmp_path) == ["watch 2025-11-12 10:05 CRASH", "watch 2025-11-12 10:05 lifted"]
    lifted = messenger.deliveries(root)[-1].text  #: with what still stops the desk buying
    assert "HALT LIFTED at 2025-11-13 16:35 UTC" in lifted and "HALT IN FORCE, day 3" in lifted
    #: the watch's own lift is no word of his: its day restated to a crash, and a new one
    _trade(tmp_path, YARDSTICK, {"16:25": "91.1"}, THU)
    _trade(tmp_path, YARDSTICK, {"08:00": 91}, FRI)
    _look(tmp_path, "08:05", post, FRI, (*after, 96))
    assert len(halt.in_force(root)) == 2 and _names(tmp_path)[2:] == [
        "watch 2025-11-14 08:05 CRASH"
    ]


def test_a_black_swan_is_his_alone_to_lift_and_is_read_twice_before_any_sale(
    tmp_path: Path,
) -> None:
    root, post, after = tmp_path / "desk", Mock(side_effect=count(1)), (*CALM, 99)
    hand = halt.call(root, _at("07:00"), "his word")
    _trade(tmp_path, YARDSTICK, {"09:55": 95, "10:00": 89})
    _look(tmp_path, "10:00", post)  #: a crash first, and its halt
    assert not _look(tmp_path, "10:05", post).cash, "sold on one reading"
    _, crash, swan = halt.in_force(root)  #: neither his own halt nor the crash's stands for it
    assert (swan.by, swan.his) == (watch.WATCH, True) and "BLACK SWAN" in swan.why
    assert not _look(tmp_path, "10:09", post).cash, "the same bar read again is one reading"
    _trade(tmp_path, YARDSTICK, {"10:05": 97})  #: a print the market took back
    assert not _look(tmp_path, "10:10", post).cash
    _trade(tmp_path, YARDSTICK, {"10:10": 88})  #: and one more, after a calm bar: one reading
    assert not _look(tmp_path, "10:15", post).cash, "two readings that another came between"
    _trade(tmp_path, YARDSTICK, {"10:15": 88, "16:25": 99})
    _trade(tmp_path, TRIPLE, {"10:15": 70})  #: one line's emergency in the same look
    assert _look(tmp_path, "10:20", post).cash, "its two newest bars said so: read twice"
    stale = watch.read(tmp_path / "bars.db", _daily(), _at("10:41"))
    assert stale.blind and not stale.cash, "sold on a market no longer heard from"
    _, once, twice, _ = messenger.deliveries(root)
    assert _names(tmp_path) == [
        "watch 2025-11-12 10:00 CRASH",
        "watch 2025-11-12 10:05 BLACK_SWAN",
        "watch 2025-11-12 BLACK_SWAN twice",
        "watch 2025-11-12 THREE EMERGENCY",
    ]
    assert all("NOT DONE: nothing is sold" in told.text for told in (once, twice))
    assert twice.text.startswith("BLACK SWAN, READ TWICE") and "12.0% below" in twice.text
    _look(tmp_path, "16:36", post)  #: the day ended clear: the crash's is lifted, never his
    assert halt.in_force(root) == (hand, swan) and post.call_count == 5  #: and he is told so
    assert messenger.deliveries(root)[-1].text.count("HALT IN FORCE, day 1") == 2
    #: next day his halt stands: read twice again; then he lifts it, and that is his word
    _trade(tmp_path, YARDSTICK, {"08:00": 88, "08:05": 88, "08:10": 94}, THU)
    assert [_look(tmp_path, at, post, THU, after).cash for at in ("08:05", "08:10")] == [
        False,
        True,
    ]
    halt.lift(root, swan, _at("08:12", THU), "his word")
    #: a black swan still, then a crash: no sale, and no halt of either kind
    sold = [_look(tmp_path, at, post, THU, after).cash for at in ("08:13", "08:15")]
    assert sold == [False, False], "sold on a black swan he lifted"
    assert halt.in_force(root) == (hand,), "a halt called over his word"
    assert _names(tmp_path)[5:] == [
        "watch 2025-11-13 BLACK_SWAN twice",
        "watch 2025-11-13 BLACK_SWAN on his word",
    ]


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
    shock, blind, _, alone, _, unbelieved = messenger.deliveries(root)
    assert _names(tmp_path) == [
        "watch 2025-11-12 THREE EMERGENCY",
        "watch 2025-11-12 10h blind",
        "watch 2025-11-12 11h blind",
        "watch 2025-11-12 ONE EMERGENCY",
        "watch 2025-11-12 end unread",  #: the day's last bar never came
        "watch 2025-11-13 08h blind",
    ]
    assert "30.0% below its last close" in shock.text and "NOT DONE" in shock.text
    assert "THE CRASH WATCH IS BLIND" in blind.text and "since 10:05 UTC" in blind.text
    assert "ONE, on 2025-11-12, is 10.0% below" in alone.text
    assert "no fall is read from its bar of 2025-11-13 08:00" in unbelieved.text
    assert halt.kept(root) == (), "a halt called for one line, or for a market not read"
