"""messenger_parts - what the desk's voice is built of, apart from the door and the record:
the words of the desk's state (what would stop today's orders, what it holds, the kill switch
and halts) and the email door. Read only; nothing here writes the delivery record."""

from __future__ import annotations

import smtplib
import ssl
from collections.abc import Callable, Mapping
from datetime import datetime
from decimal import Decimal
from email.message import EmailMessage
from pathlib import Path

from desk import book, clearance, day, halt, kill
from desk.gateway import Known
from desk.orders import Refused

SECONDS = 30  #: wait per step
Mail = Callable[[str, str], None]  #: the email door: a subject and the words, or Undelivered
SMTP = ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "SMTP_TO")


class Undelivered(Exception):
    """The door did not take a message: it has no number on the record, and is asked again."""


def stops(root: Path, now: datetime, known: Known) -> tuple[str, ...]:
    """What the desk can ask before the open that would stop every order today, each in the
    words of whoever would refuse it: the kill switch on, no drill of it within its month,
    today's check of the paper account not clean, the gateway not ready. The send path
    also asks what the broker lists (desk/placing.py)."""
    try:
        clearance.require(root, now, "today's orders")
        unchecked = None
    except Refused as refusal:
        unchecked = str(refusal)
    drilled = kill.drilled(root, now.date())
    undrilled = f"the kill switch was not drilled in the last {kill.DRILL_DAYS} days"
    reasons = (book.killed(root), None if drilled else undrilled, unchecked)
    return (*filter(None, reasons), *(() if known else (known.words,)))


def _state(root: Path) -> str:
    """What the desk holds, by its ledger, and the last day it published a record of."""
    held = ", ".join(f"{symbol} {shares}" for symbol, shares in book.positions(root).items())
    kept = day.records(root)
    if not kept:
        return f"Held: {held or 'nothing'}. No day is on the desk's record yet."
    last, since = kept[-1], ""
    if last.profit is None:
        told = f"no profit published, the book is not the broker's on {', '.join(last.mismatches)}"
    else:
        since = ", with the withheld days before it" if any(r.mismatches for r in kept[-2:]) else ""
        told = (
            f"after £{last.costs.total:,.2f} of costs the book {_made(last.profit)}; simply "
            f"holding the market would have {_made(last.market)}"
        )
    return f"Held: {held or 'nothing'}. The last day on record, {last.day:%a %d %b}{since}: {told}."


def _gate(root: Path) -> str:
    """The kill switch's state and the halts in force, read only."""
    on = (
        "; ".join(f"in force since {h.at:%Y-%m-%d %H:%M} UTC" for h in halt.in_force(root))
        or "none"
    )
    killed = (book.killed(root) or "off").replace("the kill switch is ", "")
    return f"Kill: {killed}; halts: {on}."


def _made(amount: Decimal) -> str:
    return f"{'lost' if amount < 0 else 'made'} £{abs(amount):,.2f}"


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
