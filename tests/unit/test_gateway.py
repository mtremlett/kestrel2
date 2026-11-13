"""The gateway known before any order: its daily restart waited out without a dial, a
gateway from which nothing comes back his at any hour, one that is there but not ready no
login of his, and the weekly login's reminder due on Sunday when he wakes."""

from __future__ import annotations

import socket
from collections.abc import Sequence
from contextlib import nullcontext
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from test_paper import ACCOUNTS, FEED, HELLO, LIVE, READY, _wire

from desk import gateway, paper
from desk.gateway import Known, State

REFUSED = ConnectionRefusedError("[WinError 10061] actively refused")  #: as Windows says it
TAKEN = ConnectionError("the gateway says 326: client id is already in use")


def _at(text: str) -> datetime:
    moment = datetime.fromisoformat(text)
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


@pytest.mark.parametrize(
    ("moment", "restarting"),
    [
        ("2026-11-13 02:54:59", False),  # winter: a UK clock is UTC
        ("2026-11-13 02:55", True),
        ("2026-11-13 03:14:59", True),
        ("2026-11-13 03:15", False),
        ("2026-07-01 01:55", True),  # summer: 03:00 on a UK clock is 02:00 UTC
        ("2026-07-01 02:15", False),
        ("2026-03-29 02:00", True),  # the day the clocks go forward
        ("2026-03-28T23:00-03:00", True),  # the same moment, told on a clock a day behind
        ("2026-03-29 03:00", False),
        ("2027-03-28 02:00", True),  # another year's own Sunday
        ("2026-10-25 02:00", False),  # the day they go back: 03:00 comes an hour later
        ("2026-10-25 03:00", True),
    ],
)
def test_ready_when_it_answers_and_waited_for_in_its_restart(moment: str, restarting: bool) -> None:
    # whatever it would answer: in the twenty minutes of its restart it is not even dialled
    knock = Mock(side_effect=AssertionError("dialled in its restart") if restarting else None)
    known = gateway.known(_at(moment), knock)
    if not restarting:
        assert known == Known(State.READY, "the paper Gateway answered the desk's knock")
    said = all(word in known.words for word in ("03:00", "until 03:15", "sends nothing"))
    assert [known.state is State.RESTARTING, said, not known.ready] == [restarting] * 3


@pytest.mark.parametrize(
    ("failure", "state"),
    [
        (REFUSED, State.HIS),
        (TimeoutError("timed out"), State.HIS),
        (TAKEN, State.UNWELL),  # the desk's own other conversation: no login of his
        (ConnectionError("the gateway says 1100: the broker's link is lost"), State.UNWELL),
        (OSError("it broke off"), State.UNWELL),
    ],
)
def test_silence_is_his_and_a_gateway_there_but_unready_is_not(
    failure: OSError, state: State
) -> None:
    # 03:15 on a Monday, in his night: the restart that did not come back
    known = gateway.known(_at("2026-11-16 03:15"), Mock(side_effect=failure))
    assert (known.state, known.ready) == (state, False) and str(failure) in known.words
    his = all(said in known.words for said in ("yours", "no password", "more than its 03:00"))
    assert his == (state is State.HIS) and ("login" in known.words) == his


def test_a_gateway_the_desk_cannot_trust_is_a_fault_and_a_moment_needs_its_clock() -> None:
    with pytest.raises(ValueError, match="176 only"):
        gateway.known(_at("2026-11-13 12:00"), Mock(side_effect=ValueError("176 only")))
    for ask in (lambda moment: gateway.known(moment, Mock()), gateway.reminder):
        with pytest.raises(ValueError, match="no time zone"):
            ask(datetime(2026, 11, 15, 12))


def test_the_knock_only_greets_on_the_paper_port(monkeypatch: pytest.MonkeyPatch) -> None:
    noon, dialled = _at("2026-11-13 12:00"), []
    sent: list[bytes] = []

    def answering(*messages: Sequence[str]) -> None:
        def dial(address: tuple[str, int], timeout: float) -> nullcontext[SimpleNamespace]:
            dialled.append((address, timeout))
            wire = _wire(HELLO, *messages)
            return nullcontext(SimpleNamespace(makefile=lambda _: wire, sendall=sent.append))

        monkeypatch.setattr(socket, "create_connection", dial)

    answering(ACCOUNTS, FEED, READY)
    assert gateway.known(noon).ready
    assert dialled == [(("127.0.0.1", 4002), 15)]
    assert sent == [b"API\x00\x00\x00\x00\x04v176", b"\x00\x00\x00\x0a71\x002\x00222\x00\x00"]
    answering(ACCOUNTS)  # it hangs up before it is ready
    assert gateway.known(noon).state is State.UNWELL
    answering(LIVE, READY)
    with pytest.raises(paper.NotPaper, match="U7654321"):
        gateway.known(noon)


@pytest.mark.parametrize(
    ("moment", "due"),
    [
        ("2026-11-14 12:00", None),  # Saturday: the weekend's reset would spend a login made now
        ("2026-11-15 07:59:59", None),  # Sunday, and he sleeps
        ("2026-11-15 08:00", "2026-11-15 08:00"),
        ("2026-11-15 23:59:59", "2026-11-15 08:00"),  # one reminder that Sunday, however often
        ("2026-11-16T04:00+08:00", "2026-11-15 08:00"),  # Sunday evening, told from Singapore
        ("2026-11-16 00:00", None),  # Monday: a reminder no longer, the gateway's state speaks
        ("2026-07-05 06:59:59", None),  # summer: 08:00 on a UK clock is 07:00 UTC
        ("2026-07-05 22:59:59", "2026-07-05 07:00"),
        ("2026-07-05 23:00", None),
    ],
)
def test_the_weekly_reminder_is_due_on_sunday_when_he_wakes(moment: str, due: str | None) -> None:
    reminder = gateway.reminder(_at(moment))
    assert (reminder and (reminder.due, reminder.due.tzinfo)) == (due and (_at(due), UTC))
    asked = ("yours today", "no password", "log in again today", "since 06:00", "03:00")
    assert reminder is None or all(said in reminder.line for said in asked)
