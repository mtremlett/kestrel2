"""The desk unattended: one step does what is owed at its moment, once, from the desk's records
alone; what a desk that died part-way left at the broker is put right before any order; and he
is told what was done, and of a step that failed."""

from __future__ import annotations

import csv
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
import test_placing as tp
from test_paper import FLAT, Said, _account, _but, _gateway, _order
from test_reports import AAPL, BOUGHT, DONE, END, IITU, LISTED, SMGB

from desk import book, clearance, day, kill, listing, paper, running, venues
from desk.bars import Five, writing
from desk.book import Switch
from desk.book_parts import keep
from desk.broker import Fill, Pretend
from desk.clearance import Check
from desk.lines import YARDSTICK
from desk.orders import Settings
from desk.running import Desk, Note
from desk.store import Bar

MON, ID, OLD = tp.AT, "20261113-bollinger_pullback-IITU", "20261112-rsi2_pullback-IITU"
OPEN, SHUT = MON.replace(hour=14, minute=35), MON.replace(hour=21, minute=39)
DAY = timedelta(days=1)
SPAN = date(2026, 7, 1), date(2026, 11, 30)
DAYS = [date(2026, 10, 16) + timedelta(days=n) for n in range(29)]
ACCOUNT, FILLS, ASKED = tp.ACCOUNT, tp.FILLS, tp.ASKED
#: Twenty-one sessions to Friday the 13th: flat, and with a last close Bollinger's rule buys.
FLAT_, DIP = (
    tuple(
        Bar(on, c, c + 1, c - 1, c, 1)
        for on, c in zip([d for d in DAYS if d.weekday() < 5], map(Decimal, closes), strict=True)
    )
    for closes in ([40] * 21, [*[40] * 20, 36])
)
#: The buy of 26 at 36 and its stop a tenth under, in pence, as the gateway is sent them; the
#: stop as the broker then lists it, the buy ended, and its fill of that morning.
BOTH = tp._msg({16: "BUY", 26: ID, 27: "0"}) + tp._msg(
    tp.AT_STOP | {1: "42", 20: "3240.00", 26: f"{ID}-stop", 28: "41"}
)
CHILD = _order("42", "SELL STP 3240.0", f"{ID}-stop", "PreSubmitted")
UNDER, ENDED = _account([tp.HELD, FLAT], *CHILD), [_but(DONE, 22, ID), ("102",)]
MADE = _but(_but(BOUGHT, 26, ID), 15, "20261116 09:05:06 MET")
FILL = Fill(BOUGHT[14], ID, "IITU", 26, Decimal("37.55"), MON.date())
SOLD = _but(_but(_but(MADE, 18, "SLD"), 14, "0000e859.6553f2a9.01.01"), 26, "a-sale")
BEFORE = Fill("0000e859.6553f2a0.01.01", OLD, "IITU", 26, Decimal(36), date(2026, 11, 13))
STOP_7 = _order("7", "SELL STP", f"{OLD}-stop", "PreSubmitted")  # the line's stop, at 171.5
NAMED = "IITU: the desk's own stop resting at the broker is for 26, the desk's book 0"
RATES = {"GBP": Decimal(1), "USD": Decimal("0.8")}
#: The same bars with Monday's and Tuesday's, each a pound up; and a round's last words.
UP = Decimal(41)
WEEK = (*FLAT_, *(Bar(SHUT.date() + timedelta(days=n), UP, UP, UP, UP, 1) for n in (0, 1)))
JULY = tuple(
    Bar(d, *(Decimal(40),) * 4, 1)
    for d in venues.sessions("LSE", date(2026, 6, 1), date(2026, 7, 3))
)
OUT = "Left out, parked or with no bar of {} Nov: {}."


def fast_store(hot: Path, price: int = 40) -> None:
    """The fast store at hot, with the market heard from all through every session, five
    minutes at a time, from July to November."""
    sessions = (venues.hours("LSE", on) for on in venues.sessions("LSE", *SPAN))
    every = [hours.open + n * timedelta(minutes=5) for hours in sessions for n in range(102)]
    with writing(hot) as round_:
        round_.five(YARDSTICK, [Five(at, *(Decimal(price),) * 4, 1) for at in every])


def _desk(root: Path, **bars: Sequence[Bar]) -> tuple[Desk, Mock]:
    """A desk of £4,750 whose kill switch was never drilled, a door that takes every message,
    and the bars saved for its lines: SMGB's the store has parked."""
    lines, post = {"IITU": IITU, "AAPL": AAPL, "SMGB": SMGB, "VUAG": YARDSTICK}, Mock()
    post.side_effect = range(1, 99)
    given = {lines[name]: series for name, series in ({"VUAG": FLAT_} | bars).items()}
    saved, hot = Mock(return_value=(given, {"SMGB"})), root.parent / f"{root.name}.db"
    fast_store(hot)
    return Desk(
        root,
        Settings(Decimal(4750)),
        post,
        Mock(return_value=RATES),
        hot,
        saved,
        paper.Door(paper.DESK),
    ), post


def _step(patch: pytest.MonkeyPatch, desk: Desk, now: datetime, *answers: Said) -> list[bytes]:
    """One step at a gateway that lists the desk's lines and answers each conversation in turn."""
    patch.setattr(listing, "read", lambda _, _door: LISTED)
    sent = _gateway(patch, [], *answers)
    running.step(desk, now)
    return sent[1:]  # after the knock


def _told(door: object) -> list[Any]:
    """What a door of the desk's was given, in order: his words, or the days asked for."""
    assert isinstance(door, Mock)
    return [call.args[0] for call in door.call_args_list]


def test_at_each_open_the_step_checks_the_account_and_sends_the_days_orders_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    desk, post = _desk(tmp_path, IITU=DIP, AAPL=DIP, SMGB=DIP)
    assert _step(monkeypatch, desk, MON.replace(hour=5, minute=35)) == []  # he sleeps: a knock
    assert not (clearance.checks(tmp_path) or post.called or book.switch(tmp_path))
    # London is open: the ledger, the kill switch's drill (till then no order goes: this desk
    # was never drilled), the day's check, then London's lines through the money path.
    # It asks the broker of the order, sets the book against the account, and sends the buy
    # with its stop; New York's line waits for its own open, and a parked line is left out, named
    asks: list[Said] = [tp.EMPTY, [("102",)], [END]]
    none: Said = [END]
    place: list[Said] = [[], tp.EMPTY, tp.FILLING, UNDER, ENDED, [MADE, END], UNDER, [MADE, END]]
    stop: list[Said] = [UNDER, UNDER, tp.RESTS, [tp.ENDED_42], UNDER]  # and the stop moved
    sent = _step(
        monkeypatch, desk, MON, none, tp.EMPTY, none, *asks, none, *asks[:1] * 2, *place, *stop
    )
    assert sent[:10] == [FILLS, ACCOUNT, FILLS, *ASKED, FILLS, ACCOUNT, ACCOUNT, b""]
    assert sent[10:-4] == [ACCOUNT, BOTH, *ASKED, ACCOUNT, FILLS]
    # filled at 37.55, its stop is moved to a tenth under (3379p): the new one before the old goes
    assert sent[-4:-2] == [ACCOUNT] * 2 and b"3379.00" in sent[-2] and sent[-1] == tp.CANCEL_42
    assert book.fills(tmp_path) == (FILL,) and clearance.checks(tmp_path) == (Check(MON, ()),)
    words = f"London, today's orders: {ID}, 26 shares done. {OUT.format('Fri 13', 'SMGB')}"
    assert running.notes(tmp_path) == (Note(MON, "orders LSE", words),)
    morning, orders = _told(post)  # he is told, each thing once
    assert morning.startswith("🌅 Morning Mon 16 Nov 08:05 UK\n✅ Ready for today (paper)")
    assert "📒 Held: IITU 26" in morning and orders == words
    # the next step sends nothing: while a market is open the broker's fills are read, no more
    later = MON + timedelta(minutes=5)
    assert _step(monkeypatch, desk, later, [MADE, END]) == [FILLS] and post.call_count == 2
    # New York opens, the kill switch on: the account is checked again, and its round is done
    # with every order refused in the switch's words. Nothing of it is asked for again today
    book.turn(tmp_path, Switch.ON, later, "his word")
    answers: list[Said] = [[MADE, END], UNDER, [MADE, END], UNDER, [("102",)], [MADE, END]]
    assert _step(monkeypatch, desk, OPEN, *answers) == [FILLS, ACCOUNT, FILLS, *ASKED]
    said = running.notes(tmp_path)[-1]
    assert said[:2] == (OPEN, "orders US") and len(clearance.checks(tmp_path)) == 2
    assert "bollinger_pullback-AAPL, 0 shares done" in said.words and "his word" in said.words
    assert _step(monkeypatch, desk, OPEN, [MADE, END]) == [FILLS] and _told(post)[2:] == [said[2]]
    assert _told(desk.held) == [MON.date()] * 7  # five looks of the crash watch, two rounds
    assert [(at, to) for at, to, _ in book.switch(tmp_path)][:-1] == [(MON, Switch.DRILLED)]
    # yesterday's round is not today's, and a line with no bar of the session before is left
    # out and named, never passed over in silence
    quiet, _ = _desk(tmp_path / "quiet", IITU=FLAT_)
    for now in (MON, MON + DAY):
        assert _step(monkeypatch, quiet, now, none, tp.EMPTY, none) == [FILLS, ACCOUNT, FILLS]
    first, second = running.notes(quiet.root)
    assert first[::2] == (MON, "London, today's orders: none sent in this round.")
    assert second[::2] == (MON + DAY, f"{first.words} {OUT.format('Mon 16', 'IITU, VUAG')}")
    # a round is owed only while its venue trades: in London's closing auction none is begun
    # (Thanksgiving: New York is shut all day)
    auction = MON.replace(day=26, hour=16, minute=31)
    assert _step(monkeypatch, quiet, auction, none, tp.EMPTY) == [FILLS, ACCOUNT]
    assert len(running.notes(quiet.root)) == 2
    days = [MON, MON + DAY, auction]  # the drill is each day's own, made once
    assert [turn[:2] for turn in book.switch(quiet.root)] == [(at, Switch.DRILLED) for at in days]
    # the hour he wakes is on a UK clock: 07:00 UTC in summer (a Saturday: the check alone)
    (summer, door), july = (
        _desk(tmp_path / "summer", VUAG=JULY),
        datetime(2026, 7, 4, 6, 59, tzinfo=UTC),
    )
    for seconds, news in enumerate(("news kept for the hour he wakes", "and more, a second on")):
        running._note(summer.root, july + timedelta(seconds=seconds), "recovered", news)
    assert _step(monkeypatch, summer, july) == [] and not door.called
    with pytest.raises(ConnectionError):  # and a check that did not come back is run again
        _step(monkeypatch, summer, july + timedelta(minutes=1), none, [])
    assert _told(door)[:2] == ["news kept for the hour he wakes", "and more, a second on"]
    july += timedelta(minutes=5)
    sent = _step(monkeypatch, summer, july + timedelta(minutes=1), none, tp.EMPTY)
    assert sent == [FILLS, ACCOUNT] and len(book.switch(summer.root)) == 1  # its drill, once


def test_what_a_desk_that_died_part_way_left_at_the_broker_is_put_right(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def recover(root: Path, *answers: Said) -> tuple[tuple[str, ...], list[bytes]]:
        sent = _gateway(monkeypatch, *answers[:1], *answers)  # the account as found is read first
        return running.recover(
            root, tp._paper(root), LISTED, MON.date(), paper.Door(paper.DESK)
        ), sent[1:]

    idle, part, unheld = (tmp_path / name for name in ("idle", "part", "unheld"))
    for root in (tmp_path, idle, part, unheld):
        kill.drill(root, MON)
    book._record(tmp_path, [BEFORE])
    # it died once its buy had filled: the line is under two stops, the old and the buy's. One
    # for all the shares, at the buy's level, is rested first; only then are the two cancelled
    two, lots = _account([tp.LOTS], *CHILD, *STOP_7), tp._msg(tp.AT_STOP | {17: "52"})
    all_ = tp._msg(tp.AT_STOP | {17: "52", 20: "3240.0", 26: f"{ID}-stop"})
    did, sent = recover(tmp_path, two, [MADE, END], two, tp.RESTS, [tp.ENDED_7, tp.ENDED_42])
    assert did == ("IITU left under one stop for 52 shares",) and lots != all_
    assert sent == [ACCOUNT, FILLS, ACCOUNT, all_, tp.CANCEL_42 + tp.CANCEL_7]
    # it died with its buy still working: the buy is cancelled, and the stop that came with it,
    # of a buy that bought nothing, gives the line no level: the line keeps its own
    book._record(idle, [BEFORE])
    buying = _order("41", "BUY MKT", ID, "Submitted")
    working = _account([tp.HELD], *STOP_7, *buying, *CHILD)
    gone, left = [_but(tp.MINE[1], 2, "Cancelled")], _account([tp.HELD], *STOP_7, *CHILD)
    did, sent = recover(idle, working, gone, [END], left, [tp.ENDED_42])
    assert did == (f"cancelled {ID}, left working", "IITU left under one stop for 26 shares")
    assert sent == [ACCOUNT, tp.CANCEL, FILLS, ACCOUNT, tp.CANCEL_42]
    assert [row[0] for row in csv.reader((idle / book.CANCELS).open())] == [ID]  # R-RUNNER-394
    # that buy had bought ten, and the broker ended its stop with it: the ten are given a stop
    # at the level the buy's own had, known from the account as it was found
    ten = [_but(tp.HELD, 14, "10")]
    found, bare = _account(ten, *buying, *CHILD), _account(ten)
    did, sent = recover(part, found, gone, [_but(MADE, 19, "10"), END], bare, tp.RESTS)
    rested = tp._msg(tp.AT_STOP | {17: "10", 20: "3240.0", 26: f"{ID}-stop"})
    assert sent == [ACCOUNT, tp.CANCEL, FILLS, ACCOUNT, rested] and "for 10 shares" in did[1]
    # and had it bought nothing, on a line not held: with the buy cancelled nothing is left
    did, sent = recover(unheld, _account([FLAT], *buying, *CHILD), gone, [END], _account([FLAT]))
    assert did == (f"cancelled {ID}, left working",) and sent[1:] == [tp.CANCEL, FILLS, ACCOUNT]
    # a stop the broker is not holding protects nothing: one is rested, then that one cancelled
    limbo = _account([tp.HELD], *_order("7", "SELL STP", f"{OLD}-stop", "Inactive"))
    did, sent = recover(idle, limbo, [END], limbo, tp.RESTS, [tp.ENDED_7])
    rested = tp._msg(tp.AT_STOP | {20: "171.5", 26: f"{OLD}-stop"})
    assert sent == [ACCOUNT, FILLS, ACCOUNT, rested, tp.CANCEL_7] and len(did) == 1
    # held with no stop at all, its shares the book's: the newest buy's stop goes back at the
    # level the book kept for it (R-MONEY-30); with no level kept, it is left as it is
    lost, bare = tmp_path / "lost", _account([tp.HELD])
    kill.drill(lost, MON)
    book._record(lost, [BEFORE])
    assert recover(lost, bare, [END], bare) == ((), [ACCOUNT, FILLS, ACCOUNT])
    keep(lost / book.STOPS, [book.LEVELS, (f"{OLD}-stop", Decimal("324"))])
    did, sent = recover(lost, bare, [END], bare, tp.RESTS)
    want = tp._msg(tp.AT_STOP | {17: "26", 20: "32400.00", 26: f"{OLD}-stop"})
    assert want in sent
    assert did == ("IITU left under one stop for 26 shares",)
    # a line settled is left alone; so is one whose shares are not the book's (here the sale
    # the broker made is in no answer), and one whose only stop is of a buy the ledger lacks
    stranger = _account([tp.HELD], *_order("7", "SELL STP", "x-stop", "PreSubmitted", 20))
    for account in (_account([tp.HELD], *STOP_7), _account([FLAT], *STOP_7), stranger):
        did, sent = recover(idle, account, [END], account)
        assert (did, sent) == ((), [ACCOUNT, FILLS, ACCOUNT])
    # nothing is asked while the kill switch is on, or on a desk never drilled
    book.turn(idle, Switch.ON, MON, "his word")
    for root in (idle, tmp_path / "new"):
        assert recover(root) == ((), [])


def test_a_check_that_names_what_a_dead_desk_left_is_run_again_once_it_is_put_right(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # it died once its sale had filled: the line's stop still rests, for shares no longer held,
    # and could sell short. The check names it, the stop is cancelled, the next check is clean
    bare, sold = _account([FLAT], *STOP_7), [SOLD, END]
    put: list[Said] = [sold, bare, bare, bare, sold, bare, [tp.ENDED_7], tp.EMPTY, sold]
    wire = [FILLS, ACCOUNT, ACCOUNT, ACCOUNT, FILLS, ACCOUNT, tp.CANCEL_7, ACCOUNT, FILLS]
    desk, post = _desk(tmp_path, IITU=FLAT_)
    late, door = _desk(tmp_path / "late", IITU=WEEK, VUAG=WEEK)
    for root in (tmp_path, late.root):  # Friday's buy, and Friday's record of it
        book._record(root, [BEFORE])
        book._write(root / day.RECORDS, [day.HEADER, (BEFORE.day, *[0] * 7, 936, 1)])
    assert _step(monkeypatch, desk, MON, *put) == wire
    assert clearance.checks(tmp_path) == (Check(MON, (NAMED,)), Check(MON, ()))
    what = [note.what for note in running.notes(tmp_path)]
    assert what == ["recovered", "orders LSE"] and book.positions(tmp_path) == {}
    assert "IITU left under no stop, none of it held" in _told(post)[1]
    assert _told(post)[2] == "London, today's orders: none sent in this round."
    # started again only once the markets are shut, it is put right before the day's record,
    # which then carries a profit: the book is the broker's
    assert _step(monkeypatch, late, SHUT, *put, tp.EMPTY, tp.EMPTY) == [*wire, ACCOUNT, ACCOUNT]
    (_, record), (note,) = day.records(late.root), running.notes(late.root)
    assert record.day == MON.date() and record.profit is not None and not record.mismatches
    assert note.what == "recovered" and _told(door)[-1] == note.words
    # someone else's order is nothing the desk can put right: no order goes, he is told once
    # that day, and the account is checked again at each step while a round is owed
    other, bell = _desk(tmp_path / "other", IITU=DIP)
    theirs = _account([FLAT], *_order("7", "SELL STP", "x", "PreSubmitted", client="31"))
    for now in (MON, MON + timedelta(minutes=5)):
        sent = _step(monkeypatch, other, now, [END], theirs, theirs, theirs, [END], theirs)
        assert sent == [FILLS, ACCOUNT, ACCOUNT, ACCOUNT, FILLS, ACCOUNT]
    (unclean,) = running.notes(other.root)
    assert unclean[:2] == (MON, "unclean") and "not the desk's own" in unclean.words
    assert len(clearance.checks(other.root)) == 2
    morning, told = _told(bell)
    assert "would send NO order today" in morning and told == unclean.words


def test_the_days_record_is_made_once_every_market_is_shut_and_a_missed_session_first(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    desk, post = _desk(tmp_path, IITU=WEEK, VUAG=WEEK)
    clearance._keep(tmp_path, (Check(MON, ()),))
    assert (
        _step(monkeypatch, desk, SHUT - timedelta(minutes=1)) == []
    )  # 21:39: New York's closes are kept
    # the account is checked, then the book set against the broker's for the record
    read: list[Said] = [[END], tp.EMPTY, [END], tp.EMPTY, tp.EMPTY]
    assert _step(monkeypatch, desk, SHUT, *read) == [FILLS, ACCOUNT, FILLS, ACCOUNT, ACCOUNT]
    (record,) = day.records(tmp_path)
    assert (record.day, record.profit, record.market) == (MON.date(), Decimal(0), Decimal("118.75"))
    assert "No day on the desk's record yet" in _told(post)[-1]  # the evening, told at 21:05
    assert _step(monkeypatch, desk, SHUT + timedelta(minutes=5)) == []  # made once
    # an account that is not the book does not hold the record back: it is made, the profit
    # withheld (someone's shares on the account: nothing the desk can put right)
    odd, _ = _desk(tmp_path / "odd", VUAG=WEEK)
    theirs: list[Said] = [[END], tp.BARE, tp.BARE, tp.BARE, [END], tp.BARE, [END], tp.BARE, tp.BARE]
    assert len(_step(monkeypatch, odd, SHUT, *theirs)) == 9
    (withheld,) = day.records(odd.root)
    assert withheld.profit is None and withheld.mismatches == ("IITU",)
    # a desk that was off since Friday's buy: each session it missed gets its own record, the
    # oldest first, from the bars saved by that day's end and at that day's own kept rates
    missed, tuesday = _desk(tmp_path / "missed", IITU=WEEK, VUAG=WEEK)
    book._record(missed.root, [BEFORE])
    held: list[Said] = [[END], *[_account([tp.HELD], *STOP_7)] * 2]  # the line under its stop
    sent = _step(monkeypatch, missed, SHUT + timedelta(days=1), *held[:2], *held * 3)
    assert sent == [FILLS, ACCOUNT, *[FILLS, ACCOUNT, ACCOUNT] * 3]
    days = [date(2026, 11, n) for n in (13, 16, 17)]
    assert [r.day for r in day.records(missed.root)] == days
    assert "📅 Last day on record Tue 17 Nov" in _told(tuesday)[-1]
    assert _told(missed.rates) == days
    assert _told(missed.held)[1:] == [  # after the crash watch's look
        on + timedelta(days=1) for on in days
    ]
    assert [book.rate(missed.root, "GBP", on) for on in days] == [1, 1, 1]


def test_a_step_that_fails_tells_him_once_and_is_an_error_and_a_silent_gateway_is_his(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    desk, post = _desk(tmp_path, IITU=DIP)
    for now in (MON, MON + timedelta(minutes=5)):  # the gateway hangs up in the day's check
        with pytest.raises(ConnectionError, match="hung up"):
            _step(monkeypatch, desk, now, [END], [])
    with pytest.raises(ValueError, match="does not read"):  # then it fails another way
        _step(monkeypatch, desk, MON + timedelta(minutes=10), [END], [("99", "1")])
    trouble, another = running.notes(tmp_path)  # the first of each kind, that day
    assert trouble[:2] == (MON, "trouble ConnectionError") and another.what == "trouble ValueError"
    assert "ConnectionError: the gateway hung up" in trouble.words
    assert "(in desk.paper.receive)" in trouble.words  # a failure names the call it came from
    morning, *told = _told(post)  # the morning message still goes, and says no order would
    assert "not come back" in morning and told == [trouble.words, another.words]
    assert [check.found for check in clearance.checks(tmp_path)] == [None] * 3
    # one in his night is kept for the hour he wakes, and told then with the new day's first;
    # news a day old by then is not told
    night, door = _desk(tmp_path / "night", VUAG=WEEK)
    running._note(night.root, MON - timedelta(hours=15), "recovered", "news a day old by then")
    for now, told_by_then in ((MON.replace(hour=22, minute=30), 0), (MON + DAY, 3)):
        with pytest.raises(ConnectionError, match="hung up"):
            _step(monkeypatch, night, now, [END], [])
        assert door.call_count == told_by_then
    assert [words[:6] for words in _told(door)] == ["🌅 Morn", "A step", "A step"]
    # a gateway the desk cannot trust is an error too, told as one that did not say it is ready
    monkeypatch.setattr(paper, "dial", Mock(side_effect=paper.NotPaper("account 'U1' is live")))
    live, door = _desk(tmp_path / "live")
    with pytest.raises(paper.NotPaper):
        running.step(live, MON)
    morning, said = _told(door)
    assert "did not say it is ready: the desk's knock on it failed" in morning
    assert "NotPaper: account 'U1' is live" in said
    # a gateway from which nothing comes back: nothing is asked of it, and his line goes at any
    # hour, once from each hour he wakes to the next. In its own restart no knock is made
    dial = Mock(side_effect=ConnectionRefusedError)
    monkeypatch.setattr(paper, "dial", dial)
    silent, door = _desk(tmp_path / "silent", VUAG=WEEK)
    for hours, told_by_then in ((15, 1), (16, 1), (19, 1), (24, 3)):  # 23:05, 00:05, 03:05, 08:05
        running.step(silent, MON + timedelta(hours=hours))
        assert door.call_count == told_by_then
    his, again, morning = _told(door)
    assert his.startswith("The paper Gateway does not answer: its port is closed.")
    assert again == his and dial.call_count == 3
    assert "would send NO order today" in morning and running.notes(silent.root) == ()
    sunday, bell = _desk(tmp_path / "sunday")  # his login's reminder waits for his waking hours
    running.step(sunday, MON.replace(day=15, hour=23, minute=30))
    assert _told(bell) == [his]
    running.step(sunday, MON.replace(day=15, hour=12))  # and goes in them
    assert _told(bell)[1].startswith("Sunday: the paper Gateway's weekly login is yours")
    with pytest.raises(ValueError, match="the desk's day is kept in UTC"):  # before any asking
        running.step(silent, MON.astimezone(timezone(timedelta(hours=1))))
    (tmp_path / "silent" / running.NOTES).write_text("not,the,record\n", "utf-8")
    with pytest.raises(ValueError, match="not the record of what the desk did"):
        running.step(silent, MON)
    # a drill of the kill switch that broke a promise is such a failure, and nothing but the
    # ledger comes before it: no check is run, so no order goes, and no record is made at the
    # day's end, when the step drills again. Yesterday's drill is not today's, nor is his pull
    broken, bell = _desk(tmp_path / "broken", IITU=DIP)
    book.turn(broken.root, Switch.DRILLED, MON - timedelta(days=1), "every promise kept")
    book.turn(broken.root, Switch.ON, MON, "his word")
    monkeypatch.setattr(Pretend, "cancel", lambda _: ())  # a broker that cancels nothing
    for now in (MON, SHUT):
        with pytest.raises(kill.Failed, match="was cancelled"):
            _step(monkeypatch, broken, now, [MADE, END])
    assert book.fills(broken.root) == (FILL,) and len(book.switch(broken.root)) == 2
    assert not (clearance.checks(broken.root) or day.records(broken.root))
    _, failed, _ = _told(bell)  # the morning message, one line of it in his words, the evening's
    assert "Failed: today's rehearsal of the kill switch did not pass, so the desk" in failed
    assert "NOT kept: the kill switch's drill at 2026-11-16 08:05 UTC broke: ['the ord" in failed
