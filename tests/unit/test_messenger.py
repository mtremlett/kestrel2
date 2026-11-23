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
from functools import partial
from http.client import IncompleteRead
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

import pytest

from desk import book, clearance, day, gateway, halt, messenger, venues
from desk.book import Switch
from desk.broker import Fill
from desk.clearance import Check
from desk.gateway import Known, State
from desk.lines import LINES
from desk.messenger import Delivery, Undelivered
from desk.orders import Charges

KEY = "123456:AAH-his_key"
ENV = {"TELEGRAM_BOT_TOKEN": f" {KEY}\n", "TELEGRAM_CHAT_ID": "42"}
URL = f"https://api.telegram.org/bot{KEY}/sendMessage"
ECHO = b"/bot123456%3AAAH-his_key/x"  #: the address as a page of the far end's might echo it
YES = '{"ok": true, "result": {"message_id": %s}}'  #: Telegram's yes, with its number
NO, LOST = "an answer the desk cannot read", "no answer the desk can read (%s)"
JUNK, PAD = LOST % "Expecting value: line 1 column %s", Mock(encode=Mock(return_value=b" " * 70000))
STALLED = Mock(read=Mock(side_effect=TimeoutError("it stalled")))
MON = datetime(2026, 11, 16, 8, tzinfo=UTC)  #: a Monday both venues trade; a UK clock is UTC
HALF, NINE, NAIVE = MON.replace(minute=30), MON.replace(hour=21, minute=5), MON.replace(tzinfo=None)
PARIS = datetime(2026, 11, 14, 12, tzinfo=timezone(timedelta(hours=1)))  #: a Saturday, on no UTC
CAP = Decimal(10_000)
READY = Known(State.READY, gateway.ANSWERED)
GONE = gateway.known(MON, Mock(side_effect=ConnectionRefusedError))  #: his to look at
OFF = "🔌 Kill: off · halts: none"
NOTHING = "📒 Held: nothing\n📅 No day on the desk's record yet"
STOPPED = "⛔ NOT ready: the desk would send NO order today"
SILENT = (
    "🚨 DESK SILENT\n{} message, {}: owed by {} UK, not on the delivery record at {}\n"
    "Please look at the PC: the desk may not be running"
)


def _at(text: str) -> datetime:
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


def _posts() -> Mock:
    return Mock(side_effect=range(1, 99))  #: a door that takes everything, numbering as it goes


def _refused(code: int, body: bytes) -> HTTPError:
    return HTTPError(URL, code, "", Message(), io.BytesIO(body))


def _keep(root: Path, *days: tuple[str | None, str, tuple[str, ...]]) -> None:
    """A record for each day from Wednesday 11 November: its profit, the market's, what differs."""
    costs, none = Charges(*map(Decimal, ("1001.25", ".5", "0", "0", ".25"))), Decimal(0)
    kept = [
        day.Record(date(2026, 11, 11 + n), Decimal(p) if p else None, costs, Decimal(m), d, none, 0)
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
    taken = Delivery(HALF, "a", 5, "newer")
    assert messenger.send(tmp_path, HALF, "a", "newer", post) == taken
    for at, name, text in ((NAIVE, "b", "w"), (PARIS, "b", "w"), (MON, " ", "w"), (MON, "b", "")):
        with pytest.raises(ValueError, match="no UTC time, name or words"):
            messenger.send(tmp_path, at, name, text or "\n", post)
    assert post.call_count == 2  # each refused before the door: nothing half-said to him
    pytest.raises(ValueError, Delivery, NAIVE, "a", 1, "words")  # nor read back from a record
    for odd in (True, 0, 2**63, "7", None):  # a door's answer that is no number is never kept
        with pytest.raises(ValueError, match="'odd': .* is not Telegram's number"):
            messenger.send(tmp_path, MON, "odd", "words", Mock(return_value=odd))
    assert messenger.deliveries(tmp_path) == (taken,)
    for ask in (messenger.watch, messenger.remind):  # a wrong clock is refused at the first asking
        with pytest.raises(ValueError, match="no UTC time"):
            ask(tmp_path, PARIS, post)


def test_no_word_goes_unless_the_record_can_be_written(tmp_path: Path) -> None:
    post = _posts()
    watch = partial(messenger.watch, tmp_path, HALF, post)

    def door(_text: str) -> int:  # the watch speaks while the desk is at the door
        return messenger.send(tmp_path, MON, "the watch's", "words", post).number + 8

    messenger.send(tmp_path, MON, "the desk's", "words", door)
    assert [done.number for done in messenger.deliveries(tmp_path)] == [9, 1]  # both are kept
    held = closing(sqlite3.connect(tmp_path / "messages.db"))
    with patch.object(messenger, "WAIT", 0.05), held as other:
        other.execute("BEGIN EXCLUSIVE")  # the record held by another: it cannot be written
        for ask in (lambda: messenger.send(tmp_path, MON, "new", "words", post), watch):
            with pytest.raises(sqlite3.OperationalError, match="locked"):
                ask()
    assert post.call_count == 1 and len(watch()) == 1  # and once it can be, the alarm is told


def _network(monkeypatch: pytest.MonkeyPatch, reply: Any) -> Mock:
    says = reply if isinstance(reply, Exception) else lambda *_, **__: io.BytesIO(reply.encode())
    monkeypatch.setattr(messenger, "urlopen", urlopen := Mock(side_effect=says))
    return urlopen


def test_the_real_door_is_telegram_with_a_time_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    urlopen = _network(monkeypatch, YES % 31)
    assert messenger.telegram(ENV)("Morning & all") == 31
    (request,), limit = urlopen.call_args
    assert (request.full_url, request.data) == (URL, b"chat_id=42&text=Morning+%26+all")
    for env, named in (
        ({}, "no TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in the desk's environment"),
        (ENV | {"TELEGRAM_CHAT_ID": " "}, "no TELEGRAM_CHAT_ID in"),
        (ENV | {"TELEGRAM_BOT_TOKEN": "123456:a bad paste"}, "TELEGRAM_BOT_TOKEN is not a bot key"),
        (ENV | {"TELEGRAM_BOT_TOKEN": "\u0661\u0662\u0663:in-no-plain-digits"}, "is not a bot key"),
    ):
        with pytest.raises(ValueError, match=named) as refused:
            messenger.telegram(env)
        assert "bad paste" not in str(refused.value)
    assert limit == {"timeout": 30} and urlopen.call_count == 1


@pytest.mark.parametrize(
    ("reply", "said"),
    [
        ('{"ok": false, "description": "gone"}', "gone"),
        ('{"ok": 1, "result": {"message_id": 3}}', NO),  # yes is true, and nothing like it
        (YES % '"3"', NO),  # never a number made up
        ('{"description": "' + "y" * 300 + '"}', "y" * 200),  # Telegram's reason, and no essay
        (PAD, JUNK % "65537 (char 65536)"),  # no more of an answer is read than that
        (_refused(400, PAD.encode()), "refused, 400: " + JUNK % "65537 (char 65536)"),
        (_refused(400, b'{"ok": false, "description": "chat gone"}'), "refused, 400: chat gone"),
        (_refused(500, (YES % 3).encode()), f"refused, 500: {NO}"),  # a refusal is never a yes
        (_refused(404, b"no page " + ECHO), "refused, 404: " + JUNK % "1 (char 0)"),
        (_refused(404, b'{"description": "' + ECHO + b'"}'), "refused, 404: /bot123456%3AWHO/x"),
        (HTTPError(URL, 502, "", Message(), STALLED), f"refused, 502: {LOST % 'it stalled'}"),
        (URLError(f"lost {URL}"), LOST % "<urlopen error lost https://WHERE:WHO/sendMessage>"),
        (IncompleteRead(b"{"), LOST % "IncompleteRead(1 bytes read)"),
    ],
)
def test_what_telegram_does_not_take_is_undelivered_and_the_key_is_never_shown(
    monkeypatch: pytest.MonkeyPatch, reply: Any, said: str
) -> None:
    _network(monkeypatch, reply)
    with pytest.raises(Undelivered) as no:
        messenger.telegram(ENV)("words")
    told = said.replace("WHERE", "api.telegram.org/bot123456").replace("WHO", "(his key)")
    assert str(no.value) == f"api.telegram.org did not deliver: {told}"  # and not a word more
    assert "his_key" not in told and no.value.__context__ is None  # clear of the network's


def test_the_morning_message_says_whether_anything_stops_the_desk_today(tmp_path: Path) -> None:
    post = _posts()
    book.turn(tmp_path, Switch.DRILLED, MON - timedelta(days=31), "the drill")  # a month to the day
    clearance._keep(tmp_path, (Check(MON - timedelta(minutes=55), ()),))
    _keep(tmp_path, (None, "8", ("VUSA",)), ("5", "8", ()), ("0", "-0.5", ()))
    told = (
        f"🌅 Morning Mon 16 Nov 08:00 UK\n✅ Ready for today (paper)\nGateway answered · account "
        f"check clean · kill switch off, drilled\n{OFF}\n📒 Held: nothing\n📅 Last day on "
        f"record Fri 13 Nov\n⚪ Book made £0.00 after £1,002.00 costs\n🔴 Holding the market "
        "lost £0.50\n🏁 Verdict: does not count · "
        "0 of 10 clean days in a row, since 2026-11-13 did not count."
    )
    sent = messenger.morning(tmp_path, MON, READY, post, CAP)
    assert sent == Delivery(MON, "morning 2026-11-16", 1, told)
    assert messenger.morning(tmp_path, HALF, GONE, post, CAP) == sent  # one a day, as first told
    # each thing that would refuse every order today, in the refuser's own words
    stopped, named = tmp_path / "stopped", "AAPL: the broker holds 10, the desk's book 0"
    book.turn(stopped, Switch.DRILLED, MON - timedelta(days=32), "the drill")
    book.turn(stopped, Switch.ON, MON - timedelta(hours=9), "his word")
    clearance._keep(stopped, (Check(MON - timedelta(hours=1), (named,)),))
    _keep(stopped, ("5", "8", ()), (None, "8", ("AAPL", "VUSA")))
    told = (
        f"🌅 Morning Mon 16 Nov 08:30 UK\n{STOPPED}\n• the kill switch is on, pulled at "
        f"2026-11-15 23:00 UTC: his word\n• the kill switch was not drilled in the last 31 days"
        f"\n• today's orders: not sent, the check at 07:00 UTC today named: {named}"
        f"\n• {GONE.words.rstrip('.')}\n🔌 Kill: on, pulled at 2026-11-15 23:00 UTC: his word "
        f"· halts: none\n📒 Held: nothing\n📅 Last day on record Thu 12 Nov\n⏸️ No profit "
        "published: book differs from broker on AAPL, VUSA\n🏁 Verdict: does not count · "
        "0 of 10 clean days in a row, since 2026-11-12 did not count."
    )
    assert messenger.morning(stopped, HALF, GONE, post, CAP) == Delivery(HALF, sent.name, 2, told)


def test_the_morning_message_tells_the_heat_of_the_last_day_in_pounds_and_share(
    tmp_path: Path,
) -> None:
    costs, none = Charges(*map(Decimal, ("1", "0", "0", "0", "0"))), Decimal(0)
    kept = day.Record(date(2026, 11, 13), none, costs, none, (), none, 0, heat=Decimal(230))
    book._write(tmp_path / day.RECORDS, [day.HEADER, day._row(kept)])
    sent = messenger.morning(tmp_path, MON, READY, _posts(), CAP)
    assert sent and "heat £230 (2.3%)" in sent.text


@pytest.mark.parametrize(
    ("moment", "owed", "trades"),
    [
        ("2026-11-16 05:39:59", False, True),  # the start-of-day card goes at 05:40, not before
        ("2026-11-16 05:40", True, True),
        ("2026-11-16 21:59:59", True, True),  # late is better than never, while he is awake
        ("2026-11-16 22:00", False, True),  # then he sleeps, and it is not sent
        ("2026-07-01 04:39:59", False, True),  # summer: 05:40 on a UK clock is 04:40 UTC
        ("2026-07-01 04:40", True, True),
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
    sent, uk = messenger.morning(tmp_path, now, READY, _posts(), CAP), gateway._uk(now)
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
    said = f"🌙 Evening Mon 16 Nov 21:05 UK\n🧾 Fills today: none\n{OFF}\n{NOTHING}"
    quiet = Delivery(NINE, "evening 2026-11-16", 1, said)
    assert messenger.evening(tmp_path / "new" / "desk", NINE, READY, _posts()) == quiet
    traded, fills = tmp_path / "traded", (("VUSA", 10, 13), ("AAPL", 9, 13), ("VUSA", 2, 16))
    ledger = [Fill(f"{n}{d}", "o", s, n, Decimal(80), date(2026, 11, d)) for s, n, d in fills]
    book._record(traded, [*ledger, Fill("X4", "o", "AAPL", -4, Decimal(81), MON.date())])
    _keep(traded, (None, "8", ("VUSA",)), ("-1234.5", "8", ()))
    said = (
        f"🌙 Evening Mon 16 Nov 21:05 UK\n⚠️ Paper Gateway not ready just now: ledger as last "
        f"read ({GONE.words[:-1]})\n🧾 Fills today\n🟢 bought 2 VUSA\n🔴 sold 4 AAPL\n"
        f"💷 Costs, last 7 days: £2,004.00\n🔴 Net profit lost £1,234.50 in them\n{OFF}\n"
        "📒 Held: AAPL 5, VUSA 12\n"
        "📅 Last day on record Thu 12 Nov (withheld days "
        f"before it)\n🔴 Book lost £1,234.50 after £1,002.00 costs\n🟢 Holding the market "
        "made £8.00\n🏁 Verdict: does not count · "
        "0 of 10 clean days in a row, since 2026-11-12 did not count."
    )
    assert messenger.evening(traded, NINE, GONE, _posts()) == Delivery(NINE, quiet.name, 1, said)
    clean = tmp_path / "clean"  # a clean last day: the streak is above 0
    zero, costs = Decimal(0), Charges(*[Decimal(0)] * 5)
    kept = [day.Record(date(2026, 11, 12), Decimal(5), costs, zero, (), zero, 0, (), 0)]
    book._write(clean / day.RECORDS, [day.HEADER, *map(day._row, kept)])
    told = messenger.evening(clean, NINE, READY, _posts())
    assert told and "Verdict: counts · 1 of 10 clean days in a row." in told.text
    assert "Costs, last 7 days: £0.00" in told.text
    assert "🟢 Net profit made £5.00" in told.text
    assert "Blocked signals" not in told.text  # none today: no word
    kept.append(day.Record(MON.date(), Decimal(2), costs, zero, (), zero, 0, (), 3))
    book._write(clean.parent / "blocked" / day.RECORDS, [day.HEADER, *map(day._row, kept)])
    told = messenger.evening(clean.parent / "blocked", NINE, READY, _posts())
    assert told and "🚧 Blocked signals today: 3" in told.text
    assert "Net profit made £7.00" in told.text


def test_each_daily_message_names_the_halts_in_force_beside_the_kill_switch(tmp_path: Path) -> None:
    halt.call(tmp_path, MON - timedelta(hours=2), "his word")
    morning = messenger.morning(tmp_path, MON, READY, _posts(), CAP)
    assert morning and "🔌 Kill: off · halts: in force since 2026-11-16 06:00 UTC" in morning.text
    evening = messenger.evening(tmp_path, NINE, READY, _posts())
    assert evening and "🔌 Kill: off · halts: in force since 2026-11-16 06:00 UTC" in evening.text


def test_a_daily_message_not_delivered_by_its_hour_is_told_once(tmp_path: Path) -> None:
    post, late, nearly = _posts(), NINE.replace(minute=47), NINE.replace(minute=29, second=59)
    with pytest.raises(Undelivered):  # asked, and the door did not take it: that is silence too
        messenger.morning(tmp_path, MON, READY, Mock(side_effect=Undelivered("no network")), CAP)
    assert messenger.watch(tmp_path, HALF - timedelta(seconds=1), post) == ()
    assert messenger.watch(tmp_path, _at("2026-11-14 12:00"), post) == ()  # a Saturday owes none
    (alarm,) = messenger.watch(tmp_path, HALF, post)
    words = SILENT.format("Morning", "Mon 16 Nov", "08:30", "08:30")
    assert alarm == Delivery(HALF, "silence morning 2026-11-16", 1, words)
    assert messenger.watch(tmp_path, nearly, post) == (alarm,)  # no storm
    words = SILENT.format("Evening", "Mon 16 Nov", "21:30", "21:47")
    missed = Delivery(late, "silence evening 2026-11-16", 2, words)
    assert messenger.watch(tmp_path, late, post) == (alarm, missed)
    # the desk back: its late morning message is delivered, and the morning is silent no more
    assert messenger.morning(tmp_path, late, READY, post, CAP) and post.call_count == 3
    assert messenger.watch(tmp_path, late, post) == (missed,)
    # a desk whose messages came by their hours is never called silent, summer or winter
    summer, sunny = tmp_path / "summer", _at("2026-07-01 07:29:59")
    book._record(summer, [Fill("X1", "o", "VUSA", 2, Decimal(80), date(2026, 6, 30))])
    told = (
        f"🌅 Morning Wed 01 Jul 08:29 UK\n{STOPPED}\n• the kill switch was not drilled in the "
        f"last 31 days\n• today's orders: not sent, the paper account has not been checked "
        f"today, 2026-07-01\n{OFF}\n📒 Held: VUSA 2\n📅 No day on the desk's record yet"
    )
    woke = messenger.morning(summer, sunny, READY, post, CAP)
    assert woke and (woke.name, woke.number, woke.text) == ("morning 2026-07-01", 4, told)
    assert messenger.watch(summer, sunny + timedelta(hours=13), post) == ()  # 21:29:59 there
    (missed,) = messenger.watch(summer, sunny + timedelta(hours=13, seconds=1), post)
    assert missed.text == SILENT.format("Evening", "Wed 01 Jul", "21:30", "21:30")
    assert messenger.watch(summer, sunny + timedelta(hours=15), post) == (missed,)  # at any hour
    assert messenger.evening(summer, sunny + timedelta(hours=13, minutes=30), READY, post)
    assert messenger.watch(summer, sunny + timedelta(hours=15), post) == () and post.call_count == 6


def test_the_desk_not_trading_is_told_once_from_half_past_nine_on_a_day_with_no_fill(
    tmp_path: Path,
) -> None:
    post, half = _posts(), MON.replace(hour=9, minute=30)
    assert messenger.idle(tmp_path, half - timedelta(seconds=1), post) is None
    assert messenger.idle(tmp_path, _at("2026-11-14 10:00"), post) is None  # a Saturday
    told = messenger.idle(tmp_path, half, post)
    assert told and told.name == "idle morning 2026-11-16" and "not trading" in told.text
    assert messenger.idle(tmp_path, half, post) == told and post.call_count == 1
    book._record(tmp_path, [Fill("X1", "o", "VUSA", 2, Decimal(80), date(2026, 11, 16))])
    assert messenger.idle(tmp_path, half.replace(hour=11), post) is None


def test_his_weekly_login_reminder_is_delivered_once_each_sunday(tmp_path: Path) -> None:
    post, sunday = _posts(), _at("2026-11-15 08:00")
    assert messenger.remind(tmp_path, sunday - timedelta(seconds=1), post) is None
    sent = messenger.remind(tmp_path, sunday, post)
    assert sent == Delivery(sunday, "login 2026-11-15", 1, gateway.WEEKLY)
    assert messenger.remind(tmp_path, sunday + timedelta(hours=9), post) == sent
    again = messenger.remind(tmp_path, sunday + timedelta(days=7), post)
    assert again and again.name == "login 2026-11-22" and post.call_count == 2


def test_the_hourly_pnl_goes_once_an_hour_while_a_market_trades(tmp_path: Path) -> None:
    post, words = _posts(), Mock(return_value="the day so far")
    asked = [
        messenger.hourly(tmp_path, _at(f"2026-11-16T{clock}"), words, post)
        for clock in ("07:55", "08:00", "08:40", "09:00", "21:00", "21:05", "22:00")
    ]
    assert [d and d.name for d in asked] == [
        None, "pnl 2026-11-16 08", None, "pnl 2026-11-16 09", "pnl 2026-11-16 21", None, None,
    ]  # fmt: skip
    assert words.call_count == 3 and post.call_count == 3  # the hour's second asking is not made
    sunday = messenger.hourly(tmp_path, _at("2026-11-15T14:00"), words, post)
    assert sunday is None and post.call_count == 3


def test_the_evening_message_names_each_lost_stop_once_and_none_on_a_day_without(
    tmp_path: Path,
) -> None:
    lost = halt.Blocked(
        "B1-stop",
        halt.Blocker.BOOK,
        0,
        "VUSA: 5 held, 0 under a stop; put back B1-stop, selling 5 at 79",
    )
    quiet, loud = tmp_path / "quiet", tmp_path / "loud"
    halt.note(quiet, MON.date(), [])
    halt.note(loud, MON.date(), [lost])
    said = messenger.evening(quiet, NINE, READY, _posts())
    assert said is not None and "Lost stops" not in said.text
    tell = messenger.evening(loud, NINE, READY, _posts())
    assert tell is not None and tell.text.count("B1-stop, selling 5 at 79") == 1
    assert "🔻 Lost stops to put back: B1-stop, selling 5 at 79" in tell.text
    early = messenger.morning(loud, _at("2026-11-16T08:05"), READY, _posts(), CAP)
    assert early is not None and early.text.count("B1-stop, selling 5 at 79") == 1


def test_the_evening_message_tells_a_stops_fill_with_its_buy_and_result_after_costs(
    tmp_path: Path,
) -> None:
    buy, stop = date(2026, 11, 13), MON.date()
    for on in (buy, stop):
        book.record_rates(tmp_path, on, {"GBP": Decimal(1)})
    ledger = [
        Fill("B1", "o-1", "VUSA", 23, Decimal("104.92"), buy),
        Fill("S1", "o-1-stop", "VUSA", -20, Decimal("94.38"), stop),
        Fill("S2", "s-9", "VUSA", -3, Decimal("95"), stop),
    ]
    book._record(tmp_path, ledger)
    told = messenger.evening(tmp_path, NINE, READY, _posts())
    trip = book.round_trips(tmp_path, LINES)[0]  #: the stop's 20 shares, priced by the cost model
    assert trip.sell.order_id == "o-1-stop" and trip.profit < 0
    assert (
        told
        and (
            f"🛑 VUSA's stop filled: 20 sold @ 94.38 (bought 104.92)\n🔴 Result lost "
            f"£{-trip.profit:,.2f} after costs\n🧾 Fills today\n🔴 sold 20 VUSA\n🔴 sold 3 VUSA"
        )
        in told.text
    )
