"""The messenger's email fallback: after two Telegram refusals in a row every line also goes
by email, one summary email goes each trading day whatever Telegram does, and the SMTP
settings come from the environment alone."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from desk import messenger
from desk.messenger import Undelivered

ENV = {
    "SMTP_HOST": "mail.example",
    "SMTP_PORT": "587",
    "SMTP_USER": "desk@example",
    "SMTP_PASS": "hunter2",
    "SMTP_TO": "him@example",
}
NOON = datetime(2026, 11, 16, 12, tzinfo=UTC)  #: a Monday both venues trade
NINE = datetime(2026, 11, 16, 21, 10, tzinfo=UTC)


def test_two_refusals_in_a_row_and_the_next_line_also_goes_by_email(tmp_path: Path) -> None:
    telegram = Mock(side_effect=[Undelivered("no"), Undelivered("no"), 7, 8])
    mail = Mock()
    door = messenger.with_mail(tmp_path, NOON, telegram, mail)
    for _ in range(2):
        with pytest.raises(Undelivered):
            door("a")
    assert mail.call_count == 0  # two refusals so far: no email yet
    assert door("b") == 7 and mail.call_count == 1  # Telegram took it, the email went too
    assert door("c") == 8 and mail.call_count == 1  # Telegram took one: strikes clear, no email
    with closing(sqlite3.connect(tmp_path / messenger.MESSAGES)) as record:
        assert record.execute("SELECT text FROM mails").fetchall() == [("b",)]


def test_an_email_the_server_refuses_is_not_kept_and_both_reasons_are_told(tmp_path: Path) -> None:
    telegram = Mock(side_effect=Undelivered("telegram said no"))
    mail = Mock(side_effect=Undelivered("smtp said no"))
    door = messenger.with_mail(tmp_path, NOON, telegram, mail)
    for _ in range(3):
        with pytest.raises(Undelivered) as told:
            door("a")
    assert "telegram said no; smtp said no" in str(told.value)
    with closing(sqlite3.connect(tmp_path / messenger.MESSAGES)) as record:
        assert record.execute("SELECT * FROM mails").fetchall() == []


def test_the_daily_summary_goes_once_by_email_and_never_before_its_hour(tmp_path: Path) -> None:
    mail = Mock()
    messenger.summary(tmp_path, NOON, mail)
    messenger.summary(tmp_path, NINE, mail)
    messenger.summary(tmp_path, NINE, mail)
    assert mail.call_count == 1 and "Held: nothing" in mail.call_args.args[1]


def test_the_smtp_door_takes_its_settings_from_the_environment_and_never_shows_the_password() -> (
    None
):
    with pytest.raises(ValueError, match="SMTP_TO"):
        messenger.smtp({k: v for k, v in ENV.items() if k != "SMTP_TO"})
    server = MagicMock()
    with patch("smtplib.SMTP", return_value=server) as dialled:
        messenger.smtp(ENV)("subject", "words")
    dialled.assert_called_once_with("mail.example", 587, timeout=messenger.SECONDS)
    login = server.login
    login.assert_called_once_with("desk@example", "hunter2")
    server.send_message.assert_called_once()
    login.side_effect = OSError("bad hunter2")
    with pytest.raises(Undelivered) as refused, patch("smtplib.SMTP", return_value=server):
        messenger.smtp(ENV)("subject", "words")
    assert "hunter2" not in str(refused.value) and "(his password)" in str(refused.value)
