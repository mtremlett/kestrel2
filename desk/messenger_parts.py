"""messenger_parts - what the messenger is built of, apart from its record and its doors to
Telegram: the refusal of a door, the soundness of a message, the daily message's hours and
the email door. Whoever needs them imports them from desk.messenger."""

from __future__ import annotations

import smtplib
import ssl
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from email.message import EmailMessage

SECONDS = 30  #: wait per step
SMTP = ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "SMTP_TO")
Mail = Callable[[str, str], None]  #: the email door: a subject and the words, or Undelivered


class Undelivered(Exception):
    """The door did not take a message: it has no number on the record, and is asked again."""


def sound(at: datetime, name: str, text: str) -> None:
    """Refuse a moment not in UTC, or a message without a name or words."""
    if at.utcoffset() != timedelta(0) or not name.strip() or not text.strip():
        raise ValueError(f"the message {name!r} at {at}: no UTC time, name or words")


@dataclass(frozen=True)
class Daily:
    """A message owed on every day a venue of the desk's trades, by hours on a UK clock."""

    name: str
    start: time  #: not sent before: he sleeps, or a market has not closed five minutes since
    owed: time  #: not delivered by then, and the desk is silent


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
