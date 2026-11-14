"""The desk's day as the runner asks for it: one step, the morning's pre-flight and the
rehearsal, each one line and a code; and the real doors a step is given, the price store's and
the day's pounds per dollar, with the archive and the Gateway played at their own doors."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import BinaryIO

import pytest
import test_placing as tp
from test_paper import ACCOUNTS, HELLO, NEXT, Said, _wire
from test_reports import END, LISTED
from test_running import MADE

from desk import (
    archive,
    book,
    clearance,
    command,
    day,
    halt,
    listing,
    messenger,
    paper,
    running,
    venues,
)
from desk.lines import LINES, Line
from desk.store import Bar

MON = datetime(2026, 11, 16, 7, 15, tzinfo=UTC)
FRI, SUNDAY = date(2026, 11, 13), datetime(2026, 11, 15, 18, tzinfo=UTC)
KEYS = {"TELEGRAM_BOT_TOKEN": "1:a", "TELEGRAM_CHAT_ID": "5"}
Fetch = Callable[[Line, date], tuple[Bar, ...]]


def _flat(on: date, price: str) -> Bar:
    return Bar(on, *(Decimal(price),) * 4, 0)


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
    patch.setattr(paper, "dial", dial)
    patch.setattr(listing, "read", lambda _: LISTED)
    return answers


def _run(root: Path, now: datetime, *argv: str, **env: str) -> int:
    return command.main(argv, {"KESTREL2_DATA": str(root)} | env, lambda: now)


def test_a_step_does_the_days_work_under_the_data_folder_and_fails_by_name_without_his_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _world(monkeypatch)
    assert _run(tmp_path, MON) == 0  # he sleeps: a knock
    assert capsys.readouterr().out == "STEP Mon 16 Nov 07:15 UTC: done.\n"
    # London open, and no key of his: the round is made on the store's bars at the pound's
    # rate, and only then the step fails, naming what he must set
    with pytest.raises(messenger.Undelivered, match="no TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID"):
        _run(tmp_path, MON.replace(hour=8, minute=5))
    desk = tmp_path / "desk"
    (note,) = running.notes(desk)
    assert note.what == "orders LSE" and "none sent in this round" in note.words
    assert book.rate(desk, "USD", MON.date()) == Decimal("0.8") and not messenger.deliveries(desk)
    assert (desk / "store" / "VUAG.csv").exists()
    with pytest.raises(SystemExit, match="--preflight"):
        _run(tmp_path, MON, "--now")


def test_the_doors_refuse_an_archive_that_answers_for_no_line_and_a_pound_they_cannot_trust(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    lost, today = set[str](), MON.date()

    def fetch(line: Line, before: date) -> tuple[Bar, ...]:
        if line.symbol in lost:
            raise OSError("no network")
        return _fetch(line, before)

    _world(monkeypatch, fetch)
    saved, parked = command.bars(tmp_path, today)
    assert set(saved) == set(LINES) and not parked
    assert {series[-1].day for series in saved.values()} == {FRI}
    lost.add("ISF")  # a line the archive cannot be reached for is parked alone, with no bar
    saved, parked = command.bars(tmp_path, today)
    assert parked == {"ISF"} and [s for line, s in saved.items() if line.symbol == "ISF"] == [()]
    lost |= {line.symbol for line in LINES}
    with pytest.raises(OSError, match="gave no line's bars, so none are stored: OSError: no net"):
        command.bars(tmp_path, today)
    # the pound: a rate on the day's record is the day's, whatever the archive says later
    assert command.rates(tmp_path, today) == {"GBP": 1, "USD": Decimal("0.8")}
    book.record_rates(tmp_path, today, {"USD": Decimal("0.75")})
    assert command.rates(tmp_path, today)["USD"] == Decimal("0.75")
    old, ask = today - timedelta(days=5), today + timedelta(days=1)
    # no close; one too old; the day's own, still moving; and one in pounds per dollar
    for given in ((), (_flat(old, "1.25"),), (_flat(ask, "1.25"),), (_flat(today, "0.8"),)):
        monkeypatch.setattr(archive, "fetch", lambda _line, _day, given=given: given)
        with pytest.raises(ValueError, match="no pound in dollars to trust"):
            command.rates(tmp_path, ask)
    moving = (_flat(today, "1.25"), _flat(ask, "1.3"))  # the day's own bar is passed over
    monkeypatch.setattr(archive, "fetch", lambda _line, _day: moving)
    assert command.rates(tmp_path, ask)["USD"] == Decimal("0.8")
    with pytest.raises(SystemExit, match="KESTREL2_DATA names no whole path to a folder"):
        command.main([], {"KESTREL2_DATA": ""})


def test_the_preflight_says_ready_or_names_each_thing_that_is_not_and_sends_no_order(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    answers, desk = _world(monkeypatch), tmp_path / "desk"
    assert _run(tmp_path, MON, "--preflight", **KEYS) == 0
    assert capsys.readouterr().out == (
        "PREFLIGHT Mon 16 Nov: READY. his phone: its key is set; the Gateway: it answered; the "
        "kill switch: off, and drilled today; the paper account: it is the desk's book; prices: "
        "22 lines to trade on; the pound: a dollar is £0.800000; halts: none in force.\n"
    )
    assert clearance.checks(desk)[-1].found == () and not running.notes(desk)
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
    assert ". Ready: the Gateway: it answered; prices: 22 lines to trade on; the pound" in line

    def shut(_talk: object) -> object:
        raise ConnectionRefusedError

    monkeypatch.setattr(paper, "dial", shut)  # a Gateway that does not answer, and no prices
    monkeypatch.setattr(archive, "fetch", lambda _line, _day: ())
    assert _run(tmp_path, MON + timedelta(minutes=2), "--preflight", **KEYS) == 1
    line = capsys.readouterr().out
    assert "the Gateway: ConnectionError: The paper Gateway does not answer: its port" in line
    assert "prices: ValueError: no line has a bar of the session before" in line


def test_the_rehearsal_lives_the_last_session_again_on_its_own_record_with_no_market_trading(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    answers, whole, script = _world(monkeypatch), running.step, dict[int, dict[bytes, Said]]()

    def step(desk: running.Desk, now: datetime) -> None:
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
        "and cancelled, none filled; the account left as found, the day's record made, 4 messages "
        "written and none sent to his phone. NO ORDER REACHED THE BROKER: this rehearsal does not "
        "prove the sending.\n",
    )
    (scratch,) = (tmp_path / "desk" / "rehearsals").iterdir()
    assert [record.day for record in day.records(scratch)] == [FRI]
    assert [note.what for note in running.notes(scratch)] == ["orders LSE", "orders US"]
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
    # not begun: on a day a market trades, with the desk's own kill switch on, or with
    # anything on the paper account, which the rehearsal's empty book would not hold
    book.turn(tmp_path / "desk", book.Switch.ON, MON, "his word")
    answers[tp.ACCOUNT] = tp.BARE
    assert _run(tmp_path, MON.replace(hour=22), "--rehearse") == 1
    line = capsys.readouterr().out
    assert line.startswith("REHEARSAL NO-GO: not begun: London and New York trade today, and an")
    assert "; the kill switch is on, pulled at 2026-11-16 07:15 UTC: his word; the paper" in line
    assert "account is not empty, as the rehearsal's book is: ['IITU STK GBP']." in line
