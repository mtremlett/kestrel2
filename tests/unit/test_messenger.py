"""The desk's one voice: each message asked on the delivery record, then through the one door
once; the morning and the evening message of a trading day, in his waking hours; his weekly
login's reminder; and the alarm when a daily message is not delivered by its hour."""

from __future__ import annotations

import io
import sqlite3
from contextlib import closing
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from email.message import Message
from http.client import IncompleteRead
from pathlib import Path
from typing import Any
from unittest.mock import Mock
from urllib.error import HTTPError, URLError

import pytest

from desk import book, clearance, day, gateway, messenger, venues
from desk.book import Switch
from desk.broker import Fill
from desk.clearance import Check
from desk.gateway import Known, State
from desk.messenger import Delivery, Undelivered
from desk.orders import Charges

KEY = "123456:AAH-his_key"
ENV = {"TELEGRAM_BOT_TOKEN": f" {KEY}\n", "TELEGRAM_CHAT_ID": "42"}
URL = f"https://api.telegram.org/bot{KEY}/sendMessage"
YES = '{"ok": true, "result": {"message_id": %s}}'  #: Telegram's yes, with its number
STALLED = Mock(read=Mock(side_effect=TimeoutError("its own words stalled")))
MON = datetime(2026, 11, 16, 8, tzinfo=UTC)  #: a Monday both venues trade; a UK clock is UTC
HALF, NINE = MON.replace(minute=30), MON.replace(hour=21, minute=5)
READY = Known(State.READY, gateway.ANSWERED)
GONE = gateway.known(MON, Mock(side_effect=ConnectionRefusedError))  #: his to look at
NOTHING = "Held: nothing. No day is on the desk's record yet."
SILENT = (
    "THE DESK IS SILENT. Its {} message for {} was owed by {} UK and is not on its delivery "
    "record at {}. Please look at the PC: the desk may not be running."
)


def _at(text: str) -> datetime:
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


def _posts() -> Mock:
    return Mock(side_effect=range(1, 99))  #: a door that takes everything, numbering as it goes


def _keep(root: Path, *days: tuple[str | None, str, tuple[str, ...]]) -> None:
    """A record for each day from Thursday 12 November: its profit, the market's, what differs."""
    costs, none = Charges(*map(Decimal, ("1.25", ".5", "0", "0", ".25"))), Decimal(0)
    kept = [
        day.Record(date(2026, 11, 12 + n), Decimal(p) if p else None, costs, Decimal(m), d, none, 0)
        for n, (p, m, d) in enumerate(days)
    ]
    book._write(root / day.RECORDS, [day.HEADER, *map(day._row, kept)])


def test_a_message_is_delivered_once_and_kept_with_telegrams_number(tmp_path: Path) -> None:
    post, words = _posts(), 'Good morning.\nTwo lines, one "quoted", for £5.'
    first = messenger.send(tmp_path, MON, "morning 2026-11-16", words, post)
    assert first == Delivery(MON, "morning 2026-11-16", 1, words)
    assert messenger.send(tmp_path, HALF, first.name, "other words", post) == first
    fits, long = (messenger.send(tmp_path, HALF, f"{n}", "x" * n, post) for n in (4096, 4097))
    assert messenger.deliveries(tmp_path) == (first, fits, long) and long.text == "x" * 4097
    said, whole, cut = (call.args[0] for call in post.call_args_list)  # the door, asked thrice
    assert (said, whole) == (words, "x" * 4096) and len(cut) == 4096 and cut.startswith("x" * 4000)
    assert cut.endswith(" ... (cut short here: the whole of it is on the desk's delivery record)")


def test_a_message_the_door_did_not_take_stays_asked_and_goes_next_time(tmp_path: Path) -> None:
    post = Mock(side_effect=[Undelivered("no network"), 5])
    with pytest.raises(Undelivered, match="no network"):
        messenger.send(tmp_path, MON, "a", "words", post)
    assert messenger.deliveries(tmp_path) == ()  # asked, and not delivered
    assert messenger.send(tmp_path, HALF, "a", "newer", post) == Delivery(HALF, "a", 5, "newer")
    paris, naive = MON.astimezone(timezone(timedelta(hours=1))), MON.replace(tzinfo=None)
    for at, name, text in ((naive, "b", "w"), (paris, "b", "w"), (MON, " ", "w"), (MON, "b", "\n")):
        with pytest.raises(ValueError, match="no UTC time, name or words"):
            messenger.send(tmp_path, at, name, text, post)
    assert post.call_count == 2  # each refused before the door: nothing half-said to him


def test_no_word_goes_unless_the_record_can_be_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    post = _posts()

    def watch() -> tuple[Delivery, ...]:
        return messenger.watch(tmp_path, HALF, post)

    def door(_text: str) -> int:  # the watch speaks while the desk is at the door
        return messenger.send(tmp_path, MON, "the watch's", "words", post).number + 8

    messenger.send(tmp_path, MON, "the desk's", "words", door)
    assert [done.number for done in messenger.deliveries(tmp_path)] == [9, 1]  # both are kept
    monkeypatch.setattr(messenger, "WAIT", 0.05)
    with closing(sqlite3.connect(tmp_path / "messages.db")) as other:
        other.execute("BEGIN EXCLUSIVE")  # the record held by another: it cannot be written
        for ask in (lambda: messenger.send(tmp_path, MON, "new", "words", post), watch):
            with pytest.raises(sqlite3.OperationalError, match="locked"):
                ask()
    (tmp_path / "bad").mkdir()
    (tmp_path / "bad" / "messages.db").write_text("at,name,number,text\n" * 99, encoding="utf-8")
    with pytest.raises(sqlite3.DatabaseError, match="not a database"):  # nor a damaged one
        messenger.send(tmp_path / "bad", MON, "a", "words", post)
    assert post.call_count == 1 and len(watch()) == 1  # and once it can be, the alarm is told


def _network(monkeypatch: pytest.MonkeyPatch, reply: Any) -> list[tuple[Any, ...]]:
    """The network, faked at its one edge: it says reply, or raises it. Returns what was asked."""
    asked: list[tuple[Any, ...]] = []

    def urlopen(request: Any, timeout: float) -> io.BytesIO:
        asked.append((request.full_url, request.data, timeout))
        if isinstance(reply, Exception):
            raise reply
        return io.BytesIO(reply.encode())

    monkeypatch.setattr(messenger, "urlopen", urlopen)
    return asked


def test_the_real_door_is_telegram_with_a_time_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    asked = _network(monkeypatch, YES % 31)
    assert messenger.telegram(ENV)("Morning & all") == 31
    assert asked == [(URL, b"chat_id=42&text=Morning+%26+all", 30)]
    for env, named in (
        ({}, "no TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in the desk's environment"),
        (ENV | {"TELEGRAM_CHAT_ID": " "}, "no TELEGRAM_CHAT_ID in"),
        (ENV | {"TELEGRAM_BOT_TOKEN": "123456:a bad paste"}, "TELEGRAM_BOT_TOKEN is not a bot key"),
    ):
        with pytest.raises(Undelivered, match=named) as refused:
            messenger.telegram(env)
        assert "bad paste" not in str(refused.value)
    assert len(asked) == 1


@pytest.mark.parametrize(
    ("reply", "said"),
    [
        ('{"ok": false, "description": "gone"}', "{'ok': False, 'description': 'gone'}"),
        ('{"ok": 1, "result": {"message_id": 3}}', "{'ok': 1, 'result': {'message_id': 3}}"),
        (YES % '"3"', "{'ok': True, 'result': {'message_id': '3'}}"),  # never a number made up
        ('["ok"]', "['ok']"),
        ("<html>", "no answer: Expecting value: line 1 column 1 (char 0)"),
        (HTTPError(URL, 400, "", Message(), io.BytesIO(b"no")), "refused, 400: no"),
        (HTTPError(URL, 502, "", Message(), STALLED), "no answer: its own words stalled"),
        (URLError(f"lost near {URL}"), "no answer: <urlopen error lost near WHERE>"),
        (TimeoutError("timed out"), "no answer: timed out"),
        (IncompleteRead(b"{"), "no answer: IncompleteRead(1 bytes read)"),
    ],
)
def test_what_telegram_does_not_take_is_undelivered_and_the_key_is_never_shown(
    monkeypatch: pytest.MonkeyPatch, reply: Any, said: str
) -> None:
    _network(monkeypatch, reply)
    with pytest.raises(Undelivered) as no:
        messenger.telegram(ENV)("words")
    # raised clear of the network's own error, which holds the address and so the key
    said = said.replace("WHERE", "https://api.telegram.org/bot(his key)/sendMessage")
    assert (str(no.value), no.value.__context__) == (
        f"api.telegram.org did not deliver: {said}",
        None,
    )


def test_the_morning_message_says_whether_anything_stops_the_desk_today(tmp_path: Path) -> None:
    post = _posts()
    book.turn(tmp_path, Switch.DRILLED, MON - timedelta(days=31), "the drill")  # a month to the day
    clearance._keep(tmp_path, (Check(MON - timedelta(minutes=55), ()),))
    _keep(tmp_path, ("5", "8", ()), ("0", "-8", ()))
    told = (
        "Morning, Mon 16 Nov, 08:00 UK. The desk is set for today on paper: the Gateway answered, "
        "today's check of the account named nothing, and the kill switch is off and drilled. "
        "Held: nothing. The last day on record, Fri 13 Nov: after £2.00 of costs the book made "
        "£0.00; simply holding the market would have lost £8.00."
    )
    sent = messenger.morning(tmp_path, MON, READY, post)
    assert sent == Delivery(MON, "morning 2026-11-16", 1, told)
    assert messenger.morning(tmp_path, HALF, GONE, post) == sent  # one a day, as first told
    # each thing that would refuse every order today, in the refuser's own words
    stopped, named = tmp_path / "stopped", "AAPL: the broker holds 10, the desk's book 0"
    book.turn(stopped, Switch.DRILLED, MON - timedelta(days=32), "the drill")
    book.turn(stopped, Switch.ON, MON - timedelta(hours=9), "his word")
    clearance._keep(stopped, (Check(MON - timedelta(hours=1), (named,)),))
    _keep(stopped, ("5", "8", ()), (None, "8", ("AAPL", "VUSA")))
    told = (
        "Morning, Mon 16 Nov, 08:30 UK. The desk is NOT trading today: the kill switch is on, "
        "pulled at 2026-11-15 23:00 UTC: his word; the kill switch was not drilled in the last 31 "
        f"days; today's orders: not sent, the check at 07:00 UTC today named: {named}; "
        f"{GONE.words} Held: nothing. The last day on record, Fri 13 Nov: no profit "
        "published, the book is not the broker's on AAPL, VUSA."
    )
    assert messenger.morning(stopped, HALF, GONE, post) == Delivery(HALF, sent.name, 2, told)


@pytest.mark.parametrize(
    ("moment", "owed", "trades"),
    [
        ("2026-11-16 07:59:59", False, True),  # he sleeps until 08:00, and news waits for him
        ("2026-11-16 08:00", True, True),
        ("2026-11-16 21:59:59", True, True),  # late is better than never, while he is awake
        ("2026-11-16 22:00", False, True),  # then he sleeps, and it is not sent
        ("2026-07-01 06:59:59", False, True),  # summer: 08:00 on a UK clock is 07:00 UTC
        ("2026-07-01 07:00", True, True),
        ("2026-11-14 12:00", False, False),  # a Saturday
        ("2026-12-25 12:00", False, False),  # Christmas Day, a Friday: no venue trades
        ("2026-11-26 12:00", True, True),  # Thanksgiving: London trades, so the desk does
        ("2026-08-31 12:00", True, True),  # the UK's summer bank holiday: New York trades
    ],
)
def test_a_daily_message_is_owed_on_each_day_a_venue_trades_and_never_in_his_night(
    tmp_path: Path, moment: str, owed: bool, trades: bool
) -> None:
    now = _at(moment)
    sent, uk = messenger.morning(tmp_path, now, READY, _posts()), gateway._uk(now)
    assert (sent and (sent.name, sent.at)) == ((f"morning {uk.date()}", now) if owed else None)
    early = now.replace(hour=21, minute=4, second=59) + (now - uk.replace(tzinfo=UTC))
    assert messenger.evening(tmp_path, early, READY, _posts()) is None
    told = messenger.evening(tmp_path, early + timedelta(seconds=1), READY, _posts())
    assert (told and told.name) == (f"evening {uk.date()}" if trades else None)


def test_the_evening_message_never_goes_within_five_minutes_of_a_close(tmp_path: Path) -> None:
    for venue in ("LSE", "US"):  # by the one calendar, every session of two years
        for session in venues.sessions(venue, date(2026, 1, 1), date(2027, 12, 31)):
            last = venues.hours(venue, session).auction + timedelta(minutes=4, seconds=59)
            assert messenger.evening(tmp_path, last, READY, _posts()) is None, (venue, session)


def test_the_evening_message_tells_the_fills_the_holdings_and_last_record(tmp_path: Path) -> None:
    said = f"Evening, Mon 16 Nov, 21:05 UK. The desk's fills today: none. {NOTHING}"
    quiet = Delivery(NINE, "evening 2026-11-16", 1, said)
    assert messenger.evening(tmp_path, NINE, READY, _posts()) == quiet
    traded, fills = tmp_path / "traded", (("VUSA", 10, 13), ("AAPL", 9, 13), ("VUSA", 2, 16))
    ledger = [Fill(f"{n}{d}", "o", s, n, Decimal(80), date(2026, 11, d)) for s, n, d in fills]
    book._record(traded, [*ledger, Fill("X4", "o", "AAPL", -4, Decimal(81), MON.date())])
    _keep(traded, (None, "8", ("VUSA",)), ("-1234.5", "8", ()))
    said = (
        "Evening, Mon 16 Nov, 21:05 UK. The paper Gateway was not ready just now, so this is the "
        f"desk's ledger as last read ({GONE.words[:-1]}). The desk's fills today: bought 2 VUSA, "
        "sold 4 AAPL. Held: AAPL 5, VUSA 12. The last day on record, Fri 13 Nov, with the withheld "
        "days before it: after £2.00 of costs the book lost £1,234.50; simply holding the market "
        "would have made £8.00."
    )
    assert messenger.evening(traded, NINE, GONE, _posts()) == Delivery(NINE, quiet.name, 1, said)


def test_a_daily_message_not_delivered_by_its_hour_is_told_once(tmp_path: Path) -> None:
    post, late = _posts(), NINE.replace(minute=47)
    assert messenger.watch(tmp_path, HALF - timedelta(seconds=1), post) == ()
    assert messenger.watch(tmp_path, _at("2026-11-14 12:00"), post) == ()  # a Saturday owes none
    (alarm,) = messenger.watch(tmp_path, HALF, post)
    words = SILENT.format("morning", "Mon 16 Nov", "08:30", "08:30")
    assert alarm == Delivery(HALF, "silence morning 2026-11-16", 1, words)
    assert messenger.watch(tmp_path, HALF + timedelta(minutes=5), post) == (alarm,)  # no storm
    # the desk back: its late morning message is delivered, and the morning is silent no more
    assert messenger.morning(tmp_path, MON.replace(hour=9), READY, post)
    assert messenger.watch(tmp_path, NINE.replace(minute=29, second=59), post) == ()
    words = SILENT.format("evening", "Mon 16 Nov", "21:30", "21:47")
    missed = Delivery(late, "silence evening 2026-11-16", 3, words)
    assert messenger.watch(tmp_path, late, post) == (missed,)
    # a desk whose messages came by their hours is never called silent, summer or winter
    summer, sunny = tmp_path / "summer", _at("2026-07-01 07:29:59")
    assert messenger.morning(summer, sunny, READY, post)
    assert messenger.watch(summer, sunny + timedelta(hours=13), post) == ()  # 21:29:59 there
    (missed,) = messenger.watch(summer, sunny + timedelta(hours=13, seconds=1), post)
    assert missed.text == SILENT.format("evening", "Wed 01 Jul", "21:30", "21:30")
    assert messenger.watch(summer, sunny + timedelta(hours=15), post) == (missed,)  # at any hour
    assert messenger.evening(summer, sunny + timedelta(hours=13, minutes=30), READY, post)
    assert messenger.watch(summer, sunny + timedelta(hours=15), post) == () and post.call_count == 6


def test_his_weekly_login_reminder_is_delivered_once_each_sunday(tmp_path: Path) -> None:
    post, sunday = _posts(), _at("2026-11-15 08:00")
    assert messenger.remind(tmp_path, sunday - timedelta(seconds=1), post) is None
    sent = messenger.remind(tmp_path, sunday, post)
    assert sent == Delivery(sunday, "login 2026-11-15", 1, gateway.WEEKLY)
    assert messenger.remind(tmp_path, sunday + timedelta(hours=9), post) == sent
    again = messenger.remind(tmp_path, sunday + timedelta(days=7), post)
    assert again and again.name == "login 2026-11-22" and post.call_count == 2
