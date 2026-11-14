"""halt: a typed record, in force from the moment it is called until it is lifted and never
because time passed; said every day, louder by the day; and each morning's one list of every
blocker with the signals it blocked."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from desk import halt
from desk.halt import Blocked, Blocker, Halt

MON, TUE, WED = (date(2025, 11, day) for day in (10, 11, 12))
NOW, LATER = (datetime(2025, 11, 10, hour, 30, tzinfo=UTC) for hour in (9, 15))


def test_a_halt_is_in_force_from_its_call_until_it_is_lifted_and_never_expires(
    tmp_path: Path,
) -> None:
    assert halt.kept(tmp_path) == halt.in_force(tmp_path) == halt.on(tmp_path, MON) == ()
    first = halt.call(tmp_path, NOW, "the market fell 5% today")
    second = halt.call(tmp_path, LATER, "his word")
    assert halt.kept(tmp_path) == halt.in_force(tmp_path) == (first, second)
    assert first == Halt(NOW, "the market fell 5% today") and first.lifted is None
    year = MON + timedelta(days=365)  #: no halt ends because time has passed
    assert [halt.on(tmp_path, on) for on in (date(2025, 11, 9), MON, year)] == [
        (),
        (first, second),
        (first, second),
    ]
    assert halt.call(tmp_path, NOW, "the market fell 5% today") == first  #: the same halt
    assert halt.kept(tmp_path) == (first, second), "one halt called twice is kept twice"
    gone = halt.lift(tmp_path, first, datetime(2025, 11, 12, 7, tzinfo=UTC), "the market is calm")
    assert halt.in_force(tmp_path) == (second,) and halt.kept(tmp_path) == (gone, second)
    assert gone.lifted == (datetime(2025, 11, 12, 7, tzinfo=UTC), "the market is calm")
    #: in force on the day it was lifted, whatever the hour, and on no day after
    assert [first.at in {h.at for h in halt.on(tmp_path, on)} for on in (TUE, WED, year)] == [
        True,
        True,
        False,
    ]
    for which, at, why in (
        (first, LATER, "lifted already, as it stood"),
        (gone, LATER, "lifted already, as it stands"),
        (Halt(NOW, "his word"), LATER, "never called: another's moment, another's reason"),
        (second, NOW, "before it was called"),
        (second, datetime(2025, 11, 12, 7), "no zone"),
        (second, datetime(2025, 11, 12, 7, tzinfo=UTC), " "),
    ):
        with pytest.raises(ValueError, match="halt"):
            halt.lift(tmp_path, which, at, why)
    paris = timezone(timedelta(hours=1))
    for at, why in (
        (datetime(2025, 11, 13, 9), "no zone"),
        (datetime(2025, 11, 13, 9, tzinfo=paris), "not UTC"),
        (datetime(2025, 11, 13, 9, tzinfo=UTC), " "),
    ):
        with pytest.raises(ValueError, match="halt"):
            halt.call(tmp_path, at, why)
    assert halt.kept(tmp_path) == (gone, second), "a refused call or lift changed the record"
    #: no well-made halt is refused: one before the record's newest, one at another's moment,
    #: one called again once lifted; and of two at one moment each is lifted alone
    late = [halt.call(tmp_path, at, why) for at, why in ((NOW, "his word"), (NOW, first.why))]
    assert halt.in_force(tmp_path) == (second, *late) and len(halt.kept(tmp_path)) == 4
    halt.lift(tmp_path, late[0], LATER, "his word again")
    assert halt.in_force(tmp_path) == (second, late[1]), "the wrong halt lifted, or both"


def test_a_record_of_halts_that_cannot_be_read_is_an_error_and_never_no_halt(
    tmp_path: Path,
) -> None:
    halt.call(tmp_path, NOW, "his word")
    whole = (tmp_path / halt.HALTS).read_text("utf-8")
    stamp = "2025-11-10T09:30:00"
    for torn in (
        "",
        whole.split("\n", 1)[1],  #: its first line not the record's own names
        whole.replace("+00:00", ""),  #: a moment with no zone
        whole.replace("his word", " "),  #: no reason
        whole + f"{stamp}+00:00,x\n",  #: a row cut short
        whole.replace(",,", f",{stamp}+00:00,"),  #: lifted, and no reason given
        whole.replace(stamp, "2025-11-10 09:30:00"),  #: not as the desk writes a moment
    ):
        (tmp_path / halt.HALTS).write_text(torn, "utf-8")
        for read in (halt.kept, halt.in_force):
            with pytest.raises(ValueError, match="halt"):
                read(tmp_path)
        with pytest.raises(ValueError, match="halt"):
            halt.on(tmp_path, MON)


def test_while_a_halt_is_in_force_the_desk_says_so_every_day_and_louder_by_the_day(
    tmp_path: Path,
) -> None:
    assert halt.said(tmp_path, MON) is None
    halt.call(tmp_path, NOW, "the market fell 5% today")
    first = halt.said(tmp_path, MON)
    assert first is not None and all(
        part in first
        for part in ("HALT IN FORCE, day 1", "2025-11-10 09:30 UTC", "fell 5%", "buys nothing")
    )
    assert halt.said(tmp_path, date(2025, 11, 9)) is None, "said before it was called"
    days = [halt.said(tmp_path, MON + timedelta(days=n)) for n in range(40)]
    assert all(
        said is not None and f"HALT IN FORCE, day {n + 1}, " in said for n, said in enumerate(days)
    ), "a day on which the desk did not say so, or did not count the days"
    halt.call(tmp_path, LATER, "his word")
    both = str(halt.said(tmp_path, TUE))
    assert both.count("HALT IN FORCE, day 2") == 2 and "his word" in both and "fell 5%" in both
    one, two = halt.in_force(tmp_path)
    halt.lift(tmp_path, one, datetime(2025, 11, 12, 7, tzinfo=UTC), "the market is calm")
    assert "HALT IN FORCE" in str(halt.said(tmp_path, TUE)), "the day before it was lifted"
    lifted = str(halt.said(tmp_path, WED))  #: the day it is lifted the desk says that too
    assert "HALT LIFTED at 2025-11-12 07:00 UTC (the market is calm)" in lifted
    assert lifted.count("HALT IN FORCE, day 3") == 1 and "his word" in lifted
    halt.lift(tmp_path, two, datetime(2025, 11, 12, 8, tzinfo=UTC), "his word again")
    assert "IN FORCE" not in str(halt.said(tmp_path, WED))
    assert halt.said(tmp_path, date(2025, 11, 13)) is None, "said after every halt was lifted"


def test_each_morning_one_list_names_every_blocker_and_every_signal_it_blocked(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="2025-11-10"):  #: no list is not a morning with none
        halt.morning(tmp_path, MON)
    assert halt.stopped(tmp_path, MON) is None, "orders never sent is not none stopped"
    held = Blocked("20251110-bollinger-A", Blocker.HALT, 0, "not sent, a halt is in force")
    part = Blocked("20251110-rsi-B", Blocker.BROKER, 5, "5 of 10, filled in part")
    late = Blocked("C", Blocker.UNREAD, 0, "C: no bar for the session before")
    halt.note(tmp_path, MON, [late])
    halt.note(tmp_path, MON, [held, part, Blocked("20251110-rsi-C", Blocker.KILL, 0, "the same")])
    halt.note(tmp_path, TUE, [])
    listed = halt.morning(tmp_path, MON)
    assert list(listed) == list(Blocker), "a blocker left off the list"
    assert listed[Blocker.HALT] == (held,) and listed[Blocker.BROKER] == (part,)
    assert [len(blocked) for blocked in listed.values()] == [1, 1, 1, 0, 0, 0, 1]
    assert halt.stopped(tmp_path, MON) == 2, "what the switch and a halt refused, not counted"
    words = halt.listed(tmp_path, MON)
    #: three signals: the line that was not read is listed, and is no signal
    assert "2025-11-10: 3 signals blocked" in words and all(b.value in words for b in Blocker)
    assert "The line has no bar for the session before: C." in words
    assert "A halt is in force: 20251110-bollinger-A." in words
    assert "The book is not the broker's: none." in words
    assert not any(halt.morning(tmp_path, TUE).values()), "another morning's signals listed"
    assert "2025-11-11: 0 signals blocked" in halt.listed(tmp_path, TUE)
    #: the morning run again: one answered whole leaves the list, one answered again is listed
    #: once, as its last answer, and what is not answered again stays as it was
    again = replace(part, filled=7)
    halt.note(tmp_path, MON, [again], [held.order_id, "an order never listed"])
    assert [*halt.morning(tmp_path, MON).values()][:3] == [(late,), (listed[Blocker.KILL][0],), ()]
    assert (
        halt.morning(tmp_path, MON)[Blocker.BROKER] == (again,) and halt.stopped(tmp_path, MON) == 1
    )
    path = next((tmp_path / halt.BLOCKED).glob("2025-11-10*"))
    path.write_text(path.read_text("utf-8").replace("BROKER", "WEATHER"), "utf-8")
    for read in (halt.morning, halt.stopped, halt.listed):
        with pytest.raises(ValueError, match="blocker"):
            read(tmp_path, MON)
    with pytest.raises(ValueError, match="blocker"):  #: nor is anything added to such a list
        halt.note(tmp_path, MON, [held])
