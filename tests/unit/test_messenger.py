"""The desk's one voice: each message through the one door once, and on the delivery record
with Telegram's number; the morning and the evening message of a trading day, in his waking
hours; his weekly login's reminder; and the alarm when a daily message is not delivered."""

from __future__ import annotations

import io
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from email.message import Message
from http.client import IncompleteRead
from pathlib import Path
from typing import Any
from unittest.mock import Mock
from urllib.error import HTTPError, URLError

import pytest

from desk import book, clearance, day, gateway, messenger
from desk.book import Switch
from desk.broker import Fill
from desk.clearance import Check
from desk.gateway import Known, State
from desk.messenger import Delivery, Undelivered
from desk.orders import Charges

KEY = "123456:AAH-his_key"
ENV = {"TELEGRAM_BOT_TOKEN": f" {KEY}\n", "TELEGRAM_CHAT_ID": "42"}
URL = f"https://api.telegram.org/bot{KEY}/sendMessage"
MON = datetime(2026, 11, 16, 8, tzinfo=UTC)  #: a Monday both venues trade; a UK clock is UTC
HALF, NINE = MON.replace(minute=30), MON.replace(hour=21)
READY = Known(State.READY, gateway.ANSWERED)
HEAD, AT = "at,name,number,text\n", "2026-11-16T08:00:00+00:00"
NOTHING = "Held: nothing. No day is on the desk's record yet."
CLEAR = (
    "Morning, Mon 16 Nov. Nothing stops the desk trading on paper today: the Gateway "
    "answered, today's check of the account named nothing, and the kill switch is off and "
    f"drilled. {NOTHING}"
)
SILENT = (
    "THE DESK IS SILENT. Its {} message for {} was owed by {} UK and is not on its delivery "
    "record at {}. Please look at the PC: the desk may not be running."
)


def _at(text: str) -> datetime:
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


def _posts() -> Mock:
    return Mock(side_effect=range(1, 99))  #: a door that takes everything, numbering as it goes


def _record(root: Path, profit: str | None, *differ: str) -> None:
    """The desk's one day on record: Friday the 13th, its profit, or the lines that differ."""
    costs, gain = (
        Charges(*map(Decimal, ("1.25", ".5", "0", "0", ".25"))),
        profit and Decimal(profit),
    )
    kept = day.Record(date(2026, 11, 13), gain or None, costs, Decimal(8), differ, Decimal(0), 0)
    book._write(root / day.RECORDS, [day.HEADER, day._row(kept)])


def test_a_message_is_delivered_once_and_kept_with_telegrams_number(tmp_path: Path) -> None:
    post, words = _posts(), 'Good morning.\nTwo lines, one "quoted".'
    first = messenger.send(tmp_path, MON, "morning 2026-11-16", words, post)
    assert first == Delivery(MON, "morning 2026-11-16", 1, words)
    assert messenger.send(tmp_path, HALF, first.name, "other words", post) == first
    long = messenger.send(tmp_path, HALF, "long", "x" * 5000, post)  # more than Telegram takes
    assert messenger.deliveries(tmp_path) == (first, long) and long.text == "x" * 5000
    (said,), (cut,) = (call.args for call in post.call_args_list)  # the door, asked twice
    assert said == words and len(cut) == 4096 and cut.startswith("x" * 4000)
    assert cut.endswith(" ... (cut short here: the whole of it is on the desk's delivery record)")
    kept = (tmp_path / "messages.csv").read_text(encoding="utf-8")
    assert kept.startswith(f'{HEAD}{AT},morning 2026-11-16,1,"Good morning.\nTwo lines, one ""q')


def test_a_message_the_door_did_not_take_is_raised_and_asked_again(tmp_path: Path) -> None:
    post = Mock(side_effect=[Undelivered("no network"), 5])
    with pytest.raises(Undelivered, match="no network"):
        messenger.send(tmp_path, MON, "a", "words", post)
    assert messenger.deliveries(tmp_path) == () and not (tmp_path / "messages.csv").exists()
    assert messenger.send(tmp_path, MON, "a", "words", post).number == 5
    paris, naive = MON.astimezone(timezone(timedelta(hours=1))), MON.replace(tzinfo=None)
    for at, name, text in ((naive, "b", "w"), (paris, "b", "w"), (MON, " ", "w"), (MON, "b", "\n")):
        with pytest.raises(ValueError, match="no UTC time, name or words"):
            messenger.send(tmp_path, at, name, text, post)
    assert post.call_count == 2  # each refused before the door: nothing half-said to him


@pytest.mark.parametrize(
    "record",
    [
        "",
        "at,name,number\n",
        HEAD + AT + ",a,7\n",
        HEAD + AT + ",a,7,words,more\n",
        HEAD + "2026-11-16T08:00:00,a,7,words\n",  # a moment on no clock
        HEAD + "this morning,a,7,words\n",
        HEAD + AT + ",a,seven,words\n",
        HEAD + AT + ",a,7,\n",
    ],
)
def test_a_damaged_record_is_an_error_and_nothing_is_sent(tmp_path: Path, record: str) -> None:
    (tmp_path / "messages.csv").write_text(record, encoding="utf-8")
    post = _posts()
    with pytest.raises(ValueError, match="messages.csv: not the desk's delivery record"):
        messenger.send(tmp_path, MON, "a", "words", post)
    with pytest.raises(ValueError, match="so nothing is sent"):  # nor read as a desk gone silent
        messenger.watch(tmp_path, HALF, post)
    post.assert_not_called()


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
    asked = _network(monkeypatch, '{"ok": true, "result": {"message_id": 31}}')
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
        (
            '{"ok": "yes", "result": {"message_id": 3}}',
            "{'ok': 'yes', 'result': {'message_id': 3}}",
        ),
        ('["ok"]', "['ok']"),
        ("<html>", "no answer: Expecting value: line 1 column 1 (char 0)"),
        (
            HTTPError(URL, 400, "Bad", Message(), io.BytesIO(b'{"ok":false}')),
            'refused, 400: {"ok":false}',
        ),
        (
            URLError(f"lost on the way to {URL}"),
            "no answer: <urlopen error lost on the way to WHERE>",
        ),
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
    sent = messenger.morning(tmp_path, MON, READY, post)
    assert sent == Delivery(MON, "morning 2026-11-16", 1, CLEAR)
    gone = gateway.known(MON, Mock(side_effect=ConnectionRefusedError))
    assert messenger.morning(tmp_path, HALF, gone, post) == sent  # one a day, as first told
    # each thing that would refuse an order today, in the refuser's own words
    stopped, named = tmp_path / "stopped", "AAPL: the broker holds 10, the desk's book 0"
    book.turn(stopped, Switch.DRILLED, MON - timedelta(days=32), "the drill")
    book.turn(stopped, Switch.ON, MON - timedelta(hours=9), "his word")
    clearance._keep(stopped, (Check(MON - timedelta(hours=1), (named,)),))
    _record(stopped, None, "AAPL", "VUSA")
    told = (
        "Morning, Mon 16 Nov. The desk is NOT trading today: the kill switch is on, pulled at "
        "2026-11-15 23:00 UTC: his word; the kill switch was not drilled in the last 31 days; "
        f"today's orders: not sent, the check at 07:00 UTC today named: {named}; "
        f"{gone.words} Held: nothing. The last day on record, Fri 13 Nov: no profit "
        "published, the book is not the broker's on AAPL, VUSA."
    )
    assert messenger.morning(stopped, MON, gone, post) == Delivery(MON, sent.name, 2, told)


@pytest.mark.parametrize(
    ("moment", "owed", "trades"),
    [
        ("2026-11-16 07:59:59", False, True),  # he sleeps until 08:00, and news waits for him
        ("2026-11-16 08:00", True, True),
        ("2026-11-16 21:59:59", True, True),  # late is better than never, while he is awake
        ("2026-11-16 22:00", False, True),  # then it is news, and waits for the morning's
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
    late = now.replace(hour=20, minute=59, second=59) + (now - uk.replace(tzinfo=UTC))
    assert messenger.evening(tmp_path, late, _posts()) is None  # New York may still be open
    told = messenger.evening(tmp_path, late + timedelta(seconds=1), _posts())
    assert (told and told.name) == (f"evening {uk.date()}" if trades else None)


def test_the_evening_message_tells_the_fills_the_holdings_and_last_record(tmp_path: Path) -> None:
    said = f"Evening, Mon 16 Nov. The desk's fills today: none. {NOTHING}"
    quiet = Delivery(NINE, "evening 2026-11-16", 1, said)
    assert messenger.evening(tmp_path, NINE, _posts()) == quiet
    traded, fills = tmp_path / "traded", (("VUSA", 10, 13), ("AAPL", 9, 13), ("VUSA", 2, 16))
    ledger = [Fill(f"{n}{d}", "o", s, n, Decimal(80), date(2026, 11, d)) for s, n, d in fills]
    book._record(traded, [*ledger, Fill("X4", "o", "AAPL", -4, Decimal(81), MON.date())])
    _record(traded, "-1234.5")
    said = (
        "Evening, Mon 16 Nov. The desk's fills today: bought 2 VUSA, sold 4 AAPL. Held: AAPL 5, "
        "VUSA 12. The last day on record, Fri 13 Nov: after £2.00 of costs the book made "
        "-£1,234.50; the market simply held, £8.00."
    )
    assert messenger.evening(traded, NINE, _posts()) == Delivery(NINE, quiet.name, 1, said)


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
    assert messenger.evening(summer, sunny + timedelta(hours=13, minutes=30), post)
    assert messenger.watch(summer, sunny + timedelta(hours=15), post) == () and post.call_count == 6


def test_his_weekly_login_reminder_is_delivered_once_each_sunday(tmp_path: Path) -> None:
    post, sunday = _posts(), _at("2026-11-15 08:00")
    assert messenger.remind(tmp_path, sunday - timedelta(seconds=1), post) is None
    sent = messenger.remind(tmp_path, sunday, post)
    assert sent == Delivery(sunday, "login 2026-11-15", 1, gateway.WEEKLY)
    assert messenger.remind(tmp_path, sunday + timedelta(hours=9), post) == sent
    again = messenger.remind(tmp_path, sunday + timedelta(days=7), post)
    assert again and again.name == "login 2026-11-22" and post.call_count == 2
