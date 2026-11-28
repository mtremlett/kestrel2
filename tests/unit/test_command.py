"""The desk's day as the runner asks for it: one step, the morning's pre-flight and the
rehearsal, each one line and a code; and the real doors a step is given, the price store's and
the day's pounds per dollar, with the archive and the Gateway played at their own doors."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from contextlib import suppress
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import BinaryIO
from unittest.mock import Mock

import pytest
import test_placing as tp
from test_paper import ACCOUNTS, HELLO, NEXT, Said, _account, _but, _order, _wire
from test_reports import BOUGHT, END, LISTED
from test_running import MADE, fast_store

from desk import (
    archive,
    bars,
    book,
    clearance,
    command,
    command_parts,
    day,
    gateway,
    halt,
    history,
    keeper,
    listing,
    messenger,
    paper,
    placing,
    pnl,
    running,
    running_notes,
    venues,
)
from desk.lines import LINES, Line
from desk.messenger_parts import SMTP
from desk.store import Answer, Bar, Refused

MON = datetime(2026, 11, 16, 7, 15, tzinfo=UTC)
FRI, SUNDAY = date(2026, 11, 13), datetime(2026, 11, 15, 18, tzinfo=UTC)
KEYS = {"TELEGRAM_BOT_TOKEN": "1:a", "TELEGRAM_CHAT_ID": "5"}
Fetch = Callable[[Line, date], tuple[Bar, ...]]
ASKED: list[tuple[Path, date]] = []  #: the keeper's store, each time the desk read it


def _flat(on: date, price: str) -> Bar:
    return Bar(on, *(Decimal(price),) * 4, 0)


def _ibkr(given: Answer, _lines: object, _day: date) -> dict[Line, Answer]:
    return {command.POUND: given}


def _fetch(line: Line, before: date) -> tuple[Bar, ...]:
    """The archive: clean bars for every line, no rule buying; and a pound at $1.25."""
    if line == command.POUND:
        return (_flat(before - timedelta(days=1), "1.25"),)
    days = venues.sessions(line.venue, date(2026, 6, 1), before - timedelta(days=1))
    move = [(d, Decimal(n % 3)) for n, d in enumerate(days)]
    return tuple(Bar(d, 50 + m, 52 + m, 49 + m, Decimal(51), 900) for d, m in move)


def _world(patch: pytest.MonkeyPatch, fetch: Fetch = _fetch) -> dict[bytes, Said]:
    """The archive, and a quiet Gateway that answers each question the desk asks as the
    table given back has it."""
    answers: dict[bytes, Said] = {b"": [], tp.FILLS: [END], tp.ACCOUNT: tp.EMPTY}

    def dial(talk: Callable[[BinaryIO, paper.Send], object]) -> object:
        asked: list[bytes] = []
        with suppress(ConnectionError):  # what it asks is learnt from a gateway that hangs up
            talk(_wire(HELLO, ACCOUNTS, NEXT), asked.append)
        return talk(_wire(HELLO, ACCOUNTS, NEXT, *answers[b"".join(asked[2:])]), lambda _: None)

    patch.setattr(archive, "fetch", fetch)
    #: IBKR's answer for the pound, by default none: the gateway of the day says it was not asked
    ibkr = {command.POUND: Refused("the broker was not asked")}
    patch.setattr(
        history, "daily", lambda _now, **_kw: lambda lines, _day: {n: ibkr[n] for n in lines}
    )

    def saved(home: Path, day: date) -> tuple[dict[Line, tuple[Bar, ...]], set[str]]:
        ASKED.append((home, day))
        return {n: fetch(n, day) for n in LINES}, set()

    patch.setattr(keeper, "saved", saved)
    patch.setattr(keeper, "pound", lambda _home, _day: Decimal("0.800000"))
    patch.setattr(paper, "dial", dial)
    patch.setattr(listing, "read", lambda _, _door: LISTED)
    return answers


def _run(root: Path, now: datetime, *argv: str, **env: str) -> int:
    return command.main(argv, {"KESTREL2_DATA": str(root)} | env, lambda: now)


def test_a_step_does_the_days_work_under_the_data_folder_and_fails_by_name_without_his_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _world(monkeypatch)
    fast_store(tmp_path / keeper.HOT, 51)
    assert _run(tmp_path, MON.replace(hour=5, minute=35)) == 0  # he sleeps: a knock
    assert capsys.readouterr().out == "STEP Mon 16 Nov 05:35 UTC: done.\n"
    # London open, and no key of his: the round is made on the store's bars at the pound's
    # rate, and only then the step fails, naming what he must set
    with pytest.raises(messenger.Undelivered, match="no TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID"):
        _run(tmp_path, MON.replace(hour=9, minute=5))
    desk = tmp_path / "desk"
    (note,) = running_notes.notes(desk)
    assert note.what == "orders LSE" and "none sent in this round" in note.words
    assert book.rate(desk, "USD", MON.date()) == Decimal("0.8") and not messenger.deliveries(desk)
    assert ASKED and {home for home, _ in ASKED} == {tmp_path}
    with pytest.raises(SystemExit, match="--preflight"):
        _run(tmp_path, MON, "--now")


def test_the_dollar_band_has_one_home_desk_lines() -> None:
    assert not hasattr(command, "DOLLARS")
    assert not hasattr(command_parts, "DOLLARS")


def test_the_pound_is_read_from_the_price_store_alone_the_broker_and_archive_never_asked(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    today = MON.date()
    monkeypatch.setattr(archive, "fetch", lambda *_: pytest.fail("the archive was asked"))

    def broker(*_: object) -> dict[Line, Answer]:
        pytest.fail("the broker was asked")

    with bars.writing(tmp_path / keeper.HOT) as round_:
        round_.daily(command.POUND, [_flat(FRI, "1.25")])
    desk = tmp_path / "desk"
    assert command.rates(tmp_path, today, broker) == {"GBP": 1, "USD": Decimal("0.8")}
    book.record_rates(desk, today, {"USD": Decimal("0.75")})  # a file's rate is not asked first
    assert command.rates(tmp_path, today)["USD"] == Decimal("0.8")
    rehearsal = desk / command.REHEARSALS / "20261122T180044"  # records deeper than the store
    assert command._desk(rehearsal, Mock(), tmp_path).rates(today)["USD"] == Decimal("0.8")
    with pytest.raises(ValueError, match="no pound in dollars is held fresh"):
        command.rates(tmp_path, today + timedelta(days=30))
    with pytest.raises(SystemExit, match="KESTREL2_DATA names no whole path to a folder"):
        command.main([], {"KESTREL2_DATA": ""})


def test_the_preflight_says_ready_or_names_each_thing_that_is_not_and_sends_no_order(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    answers, desk = _world(monkeypatch), tmp_path / "desk"
    assert _run(tmp_path, MON, "--preflight", **KEYS) == 0
    assert capsys.readouterr().out == (
        "PREFLIGHT Mon 16 Nov: READY. his phone: its key is set; "
        "the email: no SMTP_ setting, his phone alone; the Gateway: it answered; "
        "the kill switch: off, and drilled today; the paper account: it is the desk's book; "
        "prices: "
        "22 lines to trade on; the pound: a dollar is £0.800000, kept for the day "
        "(kept before); halts: "
        "none in force.\n"
    )
    assert clearance.checks(desk)[-1].found == () and not running_notes.notes(desk)
    assert book.rate(desk, "USD", MON.date()) == Decimal("0.8")  # the pound is kept
    called = halt.call(desk, MON, "a crash")  # a halt: ready, and said at the front
    assert _run(tmp_path, MON, "--preflight", **KEYS) == 0
    assert "Nov: READY, BUT NO BUY GOES: a halt is in force. his" in capsys.readouterr().out
    halt.lift(desk, called, MON, "over")
    # no key, the switch pulled, and shares on the account that are not the book's: each named
    answers[tp.ACCOUNT] = tp.BARE
    book.turn(desk, book.Switch.ON, MON, "his word")
    assert _run(tmp_path, MON + timedelta(minutes=1), "--preflight") == 1
    line = capsys.readouterr().out
    assert line.startswith("PREFLIGHT Mon 16 Nov: NOT READY. his phone: ValueError: no TELEGRAM")
    assert "the kill switch: ValueError: the kill switch is on, pulled at" in line
    assert "the paper account: ValueError: it is not the desk's book: IITU" in line
    assert ". Ready: the email: no SMTP_ setting, his phone alone; the Gateway: it answered" in line
    assert "prices: 22 lines to trade on; the pound" in line

    def shut(_talk: object) -> object:
        raise ConnectionRefusedError

    monkeypatch.setattr(paper, "dial", shut)  # a Gateway that does not answer, and no prices
    monkeypatch.setattr(keeper, "saved", lambda _home, _day: ({n: () for n in LINES}, set()))
    assert _run(tmp_path, MON + timedelta(minutes=2), "--preflight", **KEYS) == 1
    line = capsys.readouterr().out
    assert "the Gateway: ConnectionError: The paper Gateway does not answer: its port" in line
    assert "prices: ValueError: no line has a bar of the session before" in line
    # an untrusted pound is named in the line and nothing is kept for the day
    tue = MON + timedelta(days=1)
    monkeypatch.setattr(keeper, "pound", lambda *_: (_ for _ in ()).throw(keeper.Stale("none")))
    assert _run(tmp_path, tue, "--preflight", **KEYS) == 1
    assert "the pound: ValueError: none" in capsys.readouterr().out
    assert str(tue.date()) not in (desk / book.RATES).read_text(encoding="utf-8")


def test_the_rehearsal_lives_the_last_session_again_on_its_own_record_with_no_market_trading(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    answers, whole, script = _world(monkeypatch), running.step, dict[int, dict[bytes, Said]]()
    fast_store(tmp_path / keeper.HOT, 51)

    def step(desk: running_notes.Desk, now: datetime) -> None:
        answers.update(script.get(now.hour * 100 + now.minute, {}))
        whole(desk, now)

    def rehearse(at: int, **changes: dict[bytes, Said]) -> tuple[int, str]:
        answers.update({tp.FILLS: [END], tp.ACCOUNT: tp.EMPTY})
        script.clear()
        script.update({int(moment[1:]): change for moment, change in changes.items()})
        return _run(tmp_path, SUNDAY + timedelta(seconds=at), "--rehearse"), capsys.readouterr().out

    monkeypatch.setattr(running, "step", step)
    assert rehearse(0) == (
        0,
        "REHEARSAL GO: Fri 13 Nov lived again in 199 steps at the paper Gateway (0 failed and "
        "the next carried on), no market trading: 0 orders decided, 0 of them sent to the broker "
        "and cancelled, none filled; the account left as found, the day's record made, 5 messages "
        "written and none sent to his phone. NO ORDER REACHED THE BROKER: this rehearsal does not "
        "prove the sending.\n",
    )
    (scratch,) = (tmp_path / "desk" / "rehearsals").iterdir()
    assert [record.day for record in day.records(scratch)] == [FRI]
    assert [note.what for note in running_notes.notes(scratch)] == ["orders LSE", "orders US"]
    assert [path.name for path in (tmp_path / "desk").iterdir()] == ["rehearsals"]
    # a step that fails is named and the next carries on, as in the day: one bad reading at
    # London's open and it is GO all the same, saying so; every reading bad, and it is not
    bad: dict[bytes, Said] = {tp.FILLS: [("99", "1")]}
    code, line = rehearse(1, _800=bad, _805={tp.FILLS: [END]})
    assert code == 0 and "199 steps at the paper Gateway (1 failed and the next" in line
    code, line = rehearse(2, _800=bad)
    assert code == 1 and "the day's record was not made; steps that failed: 08:00 UTC Val" in line
    # a fill, and shares on the account at its end: each is NO-GO in its own words
    code, line = rehearse(3, _1200={tp.FILLS: [MADE, END], tp.ACCOUNT: tp.BARE})
    assert code == 1 and line.startswith("REHEARSAL NO-GO: New York's round of orders was not")
    for said in ("FILLED, the markets shut: ['20261113-bollinger", "account is not as found"):
        assert said in line
    assert "The paper account is not the desk's book, so no order goes." in line
    # orders of the desk's own still working at its end are cancelled, and named: NO-GO
    code, line = rehearse(4, _2200={tp.ACCOUNT: tp.WORKING, tp.CANCELS: tp.GONE})
    assert code == 1 and "not as found; left working, now cancelled: ('a', 'f')" in line
    # the desk's zoo switch is rehearsed too: on in the desk, on at every rehearsed step
    zoos: list[bool] = []
    monkeypatch.setattr(running, "step", lambda desk, _now: zoos.append(desk.zoo))
    (tmp_path / "desk" / running.ZOO_ON).touch()
    rehearse(5)
    assert zoos and all(zoos)
    (tmp_path / "desk" / running.ZOO_ON).unlink()
    zoos.clear()
    rehearse(6)
    assert zoos and not any(zoos)  #: off by default: no file, no zoo (CANON B6)
    # not begun: on a day a market trades, or with the desk's own kill switch on; and with
    # the kill switch on
    book.turn(tmp_path / "desk", book.Switch.ON, MON, "his word")
    answers[tp.ACCOUNT] = tp.BARE
    assert _run(tmp_path, MON.replace(hour=13), "--rehearse") == 1
    line = capsys.readouterr().out
    assert line.startswith(
        "REHEARSAL NO-GO: not begun: London and New York trade now, soon or just"
    )
    assert "; the kill switch is on, pulled at 2026-11-16 07:15 UTC: his word." in line


def test_a_stalled_account_read_ends_no_go_naming_the_read_and_the_step_tally(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _world(monkeypatch)
    fast_store(tmp_path / keeper.HOT, 51)
    reads, whole = [0], paper.whole
    monkeypatch.setattr(running, "step", lambda *_: None)

    def stall(door: paper.Door | None = None) -> paper.Account:
        reads[0] += 1
        if reads[0] == stalls[0]:
            raise TimeoutError("no answer in 30 s")
        return whole(door)

    stalls = [1]
    monkeypatch.setattr(paper, "whole", stall)
    assert _run(tmp_path, SUNDAY, "--rehearse") == 1
    assert capsys.readouterr().out == (
        "REHEARSAL NO-GO: the account read before the run stalled: no answer in 30 s.\n"
    )
    reads[0], stalls[0] = 0, 3  #: the cancel reads once between
    assert _run(tmp_path, SUNDAY + timedelta(seconds=1), "--rehearse") == 1
    line = capsys.readouterr().out
    assert "the account read after the run stalled: no answer in 30 s" in line
    assert "199 of 199 steps passed" in line
    # a rehearsal stopped at its tenth step tells 9 passed and 190 not run, never 198 of 199
    ran = [0]
    monkeypatch.setattr(running, "step", lambda *_: ran.append(0))
    each = (command.RUN_SECONDS - command.STEP_BOUND) / 8.5
    clock = lambda: SUNDAY + timedelta(seconds=2 + each * (len(ran) - 1))  # noqa: E731
    reads[0], stalls[0] = 0, 3
    assert command.main(["--rehearse"], {"KESTREL2_DATA": str(tmp_path)}, clock) == 1
    assert "(9 of 199 steps passed, 190 not run)" in capsys.readouterr().out


def test_a_rehearsal_whose_next_step_would_pass_its_time_stops_and_names_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ticks, steps = iter(range(0, 10_000_000, 600)), list[datetime]()
    monkeypatch.setattr(running, "step", lambda _desk, at: steps.append(at))
    moments = command._moments(FRI)
    desk = command._desk(tmp_path, Mock(), tmp_path)
    clock = lambda: SUNDAY + timedelta(seconds=next(ticks))  # noqa: E731 - ten minutes a call
    failed, unrun = command._live(desk, moments, clock)
    assert unrun == len(moments) - len(steps)
    spent = f"the rehearsal's {command.RUN_SECONDS} s were spent"
    assert 0 < len(steps) < len(moments) and failed == [
        f"{moments[len(steps)]:%H:%M} UTC stopped, {spent}"
    ]


def test_a_rehearsal_of_many_orders_ends_inside_its_time_with_none_working(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A Friday: 313 orders, each its wait and 6 s more (5 s ran out at 17:50), three 30 s dials;
    every step runs, so the run ends by itself and the cancel after it (rehearse) finds none."""
    moments = command._moments(FRI)
    cost = (313 * (placing.SHUT_SECONDS + 6) + 3 * 30) / len(moments)
    now = [SUNDAY]
    monkeypatch.setattr(running, "step", lambda *_: now.append(now[-1] + timedelta(seconds=cost)))
    desk = command._desk(tmp_path, Mock(), tmp_path)
    assert command._live(desk, moments, lambda: now[-1]) == ([], 0)


def test_the_rehearsal_runs_beside_a_held_account_and_leaves_its_holdings_and_stops_as_found(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    answers = _world(monkeypatch)
    fast_store(tmp_path / keeper.HOT, 51)
    whole = running.step
    held = [_but(tp.HELD, 4, name) for name in ("MSTR", "IB1T")]

    def stop(number: str, level: str) -> tuple[Sequence[str], Sequence[str]]:
        return _order(number, f"SELL STP {level}", f"old-{number}-stop", "PreSubmitted")

    both = (stop("7", "171.5"), stop("8", "30.5"))
    account = _account(held, *(part for pair in both for part in pair))
    cases = {  # the account at the rehearsal's end: what it says
        "REHEARSAL GO": account,
        "old-8-stop (AAPL) was cancelled": _account(held, *both[0]),
        "old-8-stop (AAPL) was moved": _account(held, *both[0], *stop("8", "29.5")),
        "shares held, now 0": _account(held[:1], *both[0], *both[1]),
        "its own order a-stop (AAPL) is still working": _account(
            held, *both[0], *both[1], *_order("9", "SELL STP", "a-stop", "PreSubmitted")
        ),
    }
    # Fri 13 Nov: the real desk's buys of the held lines, under the ids the rehearsal decides
    real = [
        _but(
            _but(_but(BOUGHT, 4, n), 14, f"e859.{n}.01.01"), 26, f"20261113-bollinger_pullback-{n}"
        )
        for n in ("IB1T", "MSTR")
    ]
    for said, end in cases.items():
        answers[tp.ACCOUNT], answers[tp.FILLS] = account, [*real, END]

        def step(desk: running_notes.Desk, now: datetime, end: Said = end) -> None:
            whole(desk, now)
            if (now.hour, now.minute) == (22, 0):
                answers[tp.ACCOUNT] = end

        monkeypatch.setattr(running, "step", step)
        code = _run(tmp_path, SUNDAY, "--rehearse")
        out = capsys.readouterr().out
        assert (said in out, code) == (True, int(said != "REHEARSAL GO")), out


def test_the_rehearsal_may_begin_on_a_weekday_once_the_markets_are_shut_and_far_from_the_next_open(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    answers = _world(monkeypatch)
    fast_store(tmp_path / keeper.HOT, 51)
    answers.update({tp.FILLS: [END], tp.ACCOUNT: tp.EMPTY})
    monkeypatch.setattr(running, "step", lambda *_: None)
    for hour, minute, begins in (
        (13, 0, 0),
        (6, 31, 0),
        (8, 0, 0),
        (21, 15, 0),
        (22, 30, 0),
        (23, 30, 0),
        (6, 30, 1),
    ):
        _run(tmp_path, MON.replace(hour=hour, minute=minute), "--rehearse")
        assert ("not begun" in capsys.readouterr().out) == (not begins), (hour, minute)


def test_a_real_step_is_followed_by_the_hourly_pnl_once_an_hour(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    told, post = Mock(return_value="the day so far"), Mock(side_effect=range(1, 9))
    monkeypatch.setattr(pnl, "told", told)
    _world(monkeypatch)
    desk, open_london = command._desk(tmp_path, post, tmp_path), MON.replace(hour=9, minute=0)
    for moment in (open_london, open_london + timedelta(minutes=5), open_london.replace(hour=10)):
        command.hourly(desk, moment)
    assert [call.args[0] for call in post.call_args_list] == ["the day so far"] * 2
    assert told.call_args.args[-1] == open_london.replace(hour=10)


def test_with_the_broker_unreachable_the_hourly_says_not_trading_and_counts_no_fills(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    post = Mock(side_effect=range(1, 9))
    monkeypatch.setattr(pnl, "told", Mock(side_effect=AssertionError("profit told while down")))
    monkeypatch.setattr(gateway, "known", Mock(return_value=gateway.Known(gateway.State.HIS, "x")))
    desk, at = command._desk(tmp_path, post, tmp_path), MON.replace(hour=9, minute=0)
    command.hourly(desk, at)
    said = post.call_args.args[0]
    assert "NOT trading: the paper Gateway is down since 09:00 UK" in said
    assert "orders are not sent" in said and "filled" not in said and "✅" not in said


def test_the_email_fallback_is_wired_only_when_his_smtp_settings_are_set(tmp_path: Path) -> None:
    now = MON.replace(hour=21)
    env = {"TELEGRAM_BOT_TOKEN": "t", "TELEGRAM_CHAT_ID": "1"}
    assert command._doors(env, tmp_path, now)[1] is None
    smtp = dict(zip(SMTP, ("h", "465", "u", "p", "to"), strict=True))
    assert command._doors(env | smtp, tmp_path, now)[1] is not None
    with pytest.raises(ValueError, match="SMTP_TO"):
        command._doors(env | smtp | {"SMTP_TO": ""}, tmp_path, now)


def test_the_evening_summary_goes_by_email_once_when_the_desk_has_a_mail_door(
    tmp_path: Path,
) -> None:
    desk, mail = command._desk(tmp_path, Mock(side_effect=range(1, 9)), tmp_path), Mock()
    for moment in (MON.replace(hour=21, minute=40), MON.replace(hour=21, minute=45)):
        running._say(replace(desk, mail=mail), moment, running.UNASKED)
    (call,) = mail.call_args_list
    assert call.args[0].startswith("Kestrel desk: summary")
