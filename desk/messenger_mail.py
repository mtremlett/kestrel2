"""messenger_mail - THE EMAIL FALLBACK of the desk's one voice (desk/messenger.py): after two
Telegram refusals in a row every line also goes by email; one summary email goes each trading
day, whatever Telegram does; the SMTP settings come from the environment alone."""

from __future__ import annotations

import hashlib
import smtplib
import ssl
from collections.abc import Callable, Mapping
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from desk.messenger import EVENING, SECONDS, Post, Undelivered, _goes, _record, _sound, _state

Mail = Callable[[str, str], None]  #: the email door: a subject and the words, or Undelivered
SMTP, DOWN = ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "SMTP_TO"), 2  #: DOWN: strikes


def smtp(env: Mapping[str, str]) -> Mail:
    """THE EMAIL DOOR, from the five SMTP_ settings of the environment (one missing is refused
    by name, never shown). A server that refuses is Undelivered, in words that never hold the
    password. Port 465 speaks TLS from the first byte, any other starts it by STARTTLS."""
    if missing := [name for name in SMTP if not env.get(name, "").strip()]:
        raise ValueError(f"no {' or '.join(missing)} in the desk's environment: his to set")
    host, port, user, secret, to = (env[name].strip() for name in SMTP)
    tls_first = port == "465"

    def mail(subject: str, text: str) -> None:
        note, tls = EmailMessage(), ssl.create_default_context()
        note["Subject"], note["From"], note["To"] = subject, user, to
        note.set_content(text)
        try:
            server = (
                smtplib.SMTP_SSL(host, 465, timeout=SECONDS, context=tls)
                if tls_first
                else (smtplib.SMTP(host, int(port), timeout=SECONDS))
            )
            with server:
                if not tls_first:
                    server.starttls(context=tls)
                server.login(user, secret)
                server.send_message(note)
        except (OSError, smtplib.SMTPException) as lost:
            why = f"{type(lost).__name__}: {lost}".replace(secret, "(his password)")
            raise Undelivered(f"{host} did not take the email: {why[:200]}") from None

    return mail


def _mailed(root: Path, now: datetime, name: str, text: str, mail: Mail) -> None:
    """One email under its name, once, kept on the record only after the server took it."""
    _sound(now, name, text)
    with _record(root) as record:
        if not record.execute("SELECT 1 FROM mails WHERE name = ?", (name,)).fetchone():
            mail(f"Kestrel desk: {name}", text)
            record.execute("INSERT INTO mails VALUES (?, ?, ?)", (now.isoformat(), name, text))


def with_mail(root: Path, now: datetime, post: Post, mail: Mail) -> Post:
    """THE FALLBACK: the Telegram door, counted. A refusal is a strike on the record, a taking
    clears them; from DOWN strikes every line also goes by email, once, before Telegram is
    tried. A refused email does not stop Telegram; both refusing, both reasons are raised."""

    def go(text: str) -> int:
        failed, line = "", "line " + hashlib.sha256(text.encode()).hexdigest()[:16]
        with _record(root) as record:
            strikes = (record.execute("SELECT fails FROM door").fetchone() or (0,))[0]
        try:
            if strikes >= DOWN:
                _mailed(root, now, line, text, mail)
        except Undelivered as lost:
            failed = f"; {lost}"
        try:
            number = post(text)
        except Undelivered as refused:
            with _record(root) as record:
                record.execute("INSERT OR REPLACE INTO door VALUES (1, ?)", (strikes + 1,))
            raise Undelivered(f"{refused}{failed}") from None
        with _record(root) as record:
            record.execute("DELETE FROM door")
        return number

    return go


def summary(root: Path, now: datetime, mail: Mail) -> None:
    """THE DAILY SUMMARY EMAIL, whatever Telegram does: the evening's hour until he sleeps."""
    name, opens = _goes(EVENING, now)
    if name:
        _mailed(root, now, f"summary {name}", f"{opens} {_state(root)}", mail)
