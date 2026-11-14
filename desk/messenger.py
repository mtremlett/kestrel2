"""messenger - THE DESK'S ONE VOICE. Every word the desk says to the operator goes through one
door, to his phone by Telegram, and onto one delivery record with Telegram's own number for
it. A message has a name and is delivered once under it, however often it is asked for. One
the door did not take is an error raised, is not on the record, and so is asked again.

Two messages are owed on every day a venue of the desk's trades, each by an hour on a UK
clock inside his waking day (he sleeps 22:00 to 08:00, docs/DECISIONS.md). THE MORNING
MESSAGE, from 08:00 and owed by 08:30: whether anything stops the desk trading today, asked
as the send path asks it. THE EVENING MESSAGE, from 21:00, by when London and New York have
both closed, and owed by 21:30: the day's fills, what is held, and the last day on record.
One that is late still goes, until 22:00; after that it is news, and waits for the morning's.

THE ALARM ON SILENCE. A desk that has died says nothing, so its silence is judged from
outside its own process (`watch`): a daily message not on the record by its hour is told to
him, once, at any hour, for that needs him. And if on a trading day neither the morning
message nor the alarm has come by 08:30, that is itself the sign: nothing on the PC runs.

Nothing here dials the broker or reads the clock: whoever runs the day gives the moment and
what the gateway said, and has brought the ledger up to date first."""

from __future__ import annotations

import csv
import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import Decimal
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from desk import book, clearance, day, gateway, kill, venues
from desk.gateway import Known
from desk.lines import LINES
from desk.orders import Refused

MESSAGES = "messages.csv"
COLUMNS = ("at", "name", "number", "text")
HOST = "api.telegram.org"
#: The bot's key and his chat's id: his alone, kept outside the repository and given to the
#: desk in its environment. The key's shape is checked on entry, so a bad paste is refused by
#: name and never reaches an address, where an error could show it.
SECRETS = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")
BOT_KEY = re.compile(r"\d+:[A-Za-z0-9_-]+")
SECONDS = 30  #: how long the door waits for Telegram
LIMIT = 4096  #: the most characters Telegram takes in one message
CUT = " ... (cut short here: the whole of it is on the desk's delivery record)"
SILENT = (
    "THE DESK IS SILENT. Its {} message for {} was owed by {:%H:%M} UK and is not on its "
    "delivery record at {:%H:%M}. Please look at the PC: the desk may not be running."
)
CLEAR = (
    "Nothing stops the desk trading on paper today: the Gateway answered, today's check of "
    "the account named nothing, and the kill switch is off and drilled."
)
Post = Callable[[str], int]  #: the door: words to his phone, Telegram's number for them back


class Undelivered(Exception):
    """The door did not take a message: it is on no record, and is to be asked again."""


def _sound(at: datetime, name: str, text: str) -> None:
    if at.utcoffset() != timedelta(0) or not name.strip() or not text.strip():
        raise ValueError(f"the message {name!r} at {at}: no UTC time, name or words")


@dataclass(frozen=True)
class Delivery:
    """One message the door took, as the record keeps it."""

    at: datetime  #: when the desk asked for it, in UTC
    name: str  #: the message's own name: one delivery under each
    number: int  #: Telegram's own number for it
    text: str  #: every word of it, though the door cuts what Telegram would refuse for length

    def __post_init__(self) -> None:
        _sound(self.at, self.name, self.text)


@dataclass(frozen=True)
class Daily:
    """A message owed on every day a venue of the desk's trades, by hours on a UK clock."""

    name: str
    start: time  #: not sent before: he sleeps, or a market is still open
    owed: time  #: not on the record by then, and the desk is silent


MORNING = Daily("morning", gateway.WAKES, time(8, 30))
EVENING = Daily("evening", time(21), time(21, 30))
SLEEPS = time(22)  #: the hour he sleeps, on a UK clock: from then a late daily message waits


def telegram(env: Mapping[str, str]) -> Post:
    """THE ONE REAL DOOR: his phone, by Telegram's bot service, with the key and the chat id
    the environment gives. Either missing, or a key of no key's shape, is refused here by
    name and never shown. What it posts is Undelivered when Telegram refuses it, gives no
    answer in SECONDS or says anything but yes, in words that never hold the key."""
    missing = [name for name in SECRETS if not env.get(name, "").strip()]
    if missing:
        raise Undelivered(f"no {' or '.join(missing)} in the desk's environment: his to set")
    key, chat = (env[name].strip() for name in SECRETS)
    if not BOT_KEY.fullmatch(key):
        raise Undelivered(f"{SECRETS[0]} is not a bot key: his to set again")

    def post(text: str) -> int:
        form = urlencode({"chat_id": chat, "text": text}).encode()
        request = Request(f"https://{HOST}/bot{key}/sendMessage", data=form)  # noqa: S310
        try:
            with urlopen(request, timeout=SECONDS) as reply:  # noqa: S310
                said = json.load(reply)
        except HTTPError as refused:
            said = f"refused, {refused.code}: {refused.read().decode(errors='replace')}"
        except (OSError, HTTPException, ValueError) as lost:  #: the network's, or no JSON
            said = f"no answer: {lost}"
        if not isinstance(said, dict) or said.get("ok") is not True:
            #: raised clear of the network's own error, which holds the address and so the key
            raise Undelivered(f"{HOST} did not deliver: {said}".replace(key, "(his key)"))
        return int(said["result"]["message_id"])

    return post


def deliveries(root: Path) -> tuple[Delivery, ...]:
    """The delivery record, oldest first. No record is a desk that has said nothing; one that
    is there and is not as the desk writes it is an error, never a message to send again."""
    path = root / MESSAGES
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8") as record:
        rows = list(csv.reader(record))
    try:
        if rows[:1] != [list(COLUMNS)]:
            raise ValueError(f"its first line is {rows[:1]}")
        return tuple(
            Delivery(datetime.fromisoformat(at), name, int(number), text)
            for at, name, number, text in rows[1:]
        )
    except ValueError as fault:
        why = f"{path}: not the desk's delivery record, so nothing is sent: {fault}"
        raise ValueError(why) from fault


def send(root: Path, now: datetime, name: str, text: str, post: Post) -> Delivery:
    """A MESSAGE THROUGH THE ONE DOOR, ONCE. Already on the record under its name, it is not
    sent again and the delivery made is given back. Else it goes, cut where Telegram would
    refuse its length, and is kept whole with Telegram's number. Undelivered, it is on no
    record; delivered and then not written (the desk died there), he may be told twice,
    never not at all. A moment not in UTC, or no name or words, is refused before the door."""
    _sound(now, name, text)
    for done in deliveries(root):
        if done.name == name:
            return done
    fits = text if len(text) <= LIMIT else text[: LIMIT - len(CUT)] + CUT
    done = Delivery(now, name, post(fits), text)
    kept = (*deliveries(root), done)  #: read again: the watch may have spoken meanwhile
    book._write(
        root / MESSAGES, [COLUMNS, *((d.at.isoformat(), d.name, d.number, d.text) for d in kept)]
    )
    return done


def _today(daily: Daily, now: datetime) -> tuple[str | None, time]:
    """The daily message's own name today, None on a day no venue of the desk's trades; and
    the time on a UK clock."""
    local = gateway._uk(now)
    today = local.date()
    trades = any(venues.sessions(venue, today, today) for venue in {line.venue for line in LINES})
    return (f"{daily.name} {today}" if trades else None), local.time()


def _goes(daily: Daily, now: datetime) -> str | None:
    """The name the daily message goes under now: None on a day no venue trades, before its
    hour, and once he sleeps."""
    name, clock = _today(daily, now)
    return name if daily.start <= clock < SLEEPS else None


def stops(root: Path, now: datetime, known: Known) -> tuple[str, ...]:
    """Everything that stops the desk trading today, each in the words of whoever would
    refuse the order: the kill switch on, no drill of it within its month, today's check of
    the paper account not clean, the gateway not ready. None, and nothing does."""
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
    last = kept[-1]
    if last.profit is None:
        told = f"no profit published, the book is not the broker's on {', '.join(last.mismatches)}"
    else:
        costs, profit, market = (_pounds(n) for n in (last.costs.total, last.profit, last.market))
        told = f"after {costs} of costs the book made {profit}; the market simply held, {market}"
    return f"Held: {held or 'nothing'}. The last day on record, {last.day:%a %d %b}: {told}."


def _pounds(amount: Decimal) -> str:
    return f"{'-' if amount < 0 else ''}£{abs(amount):,.2f}"


def morning(root: Path, now: datetime, known: Known, post: Post) -> Delivery | None:
    """THE MORNING MESSAGE, once on each day a venue trades, from the hour he wakes: whether
    anything stops the desk trading today (stops), what it holds and the last day on record.
    known is the gateway as it was just asked. None when none is owed, or goes now."""
    name = _goes(MORNING, now)
    if name is None:
        return None
    reasons = "; ".join(reason.rstrip(".") for reason in stops(root, now, known))
    verdict = f"The desk is NOT trading today: {reasons}." if reasons else CLEAR
    return send(root, now, name, f"Morning, {_day(now)}. {verdict} {_state(root)}", post)


def evening(root: Path, now: datetime, post: Post) -> Delivery | None:
    """THE EVENING MESSAGE, once on each day a venue trades, from 21:00 on a UK clock: the
    fills the ledger holds for the day, what the desk holds and the last day on record.
    None when none is owed, or goes now."""
    name = _goes(EVENING, now)
    if name is None:
        return None
    today = gateway._uk(now).date()
    dealt = ", ".join(
        f"{'bought' if fill.quantity > 0 else 'sold'} {abs(fill.quantity)} {fill.symbol}"
        for fill in book.fills(root)
        if fill.day == today
    )
    fills = f"The desk's fills today: {dealt or 'none'}."
    return send(root, now, name, f"Evening, {_day(now)}. {fills} {_state(root)}", post)


def _day(now: datetime) -> str:
    return f"{gateway._uk(now):%a %d %b}"


def remind(root: Path, now: datetime, post: Post) -> Delivery | None:
    """His weekly login's reminder (gateway.reminder), delivered once for each Sunday's due."""
    due = gateway.reminder(now)
    return send(root, now, f"login {due.due:%Y-%m-%d}", due.line, post) if due else None


def watch(root: Path, now: datetime, post: Post) -> tuple[Delivery, ...]:
    """THE ALARM ON SILENCE, asked from outside the desk's own process every few minutes:
    each daily message owed by now and not on the delivery record is told to him, once, at
    any hour. Given back: every such alarm standing, told now or before; none, and the desk
    has said all it owes. A late message ends its own alarm."""
    said = {done.name for done in deliveries(root)}
    owed = [(daily, *_today(daily, now)) for daily in (MORNING, EVENING)]
    return tuple(
        send(root, now, f"silence {name}", _silent(daily, now), post)
        for daily, name, clock in owed
        if name and clock >= daily.owed and name not in said
    )


def _silent(daily: Daily, now: datetime) -> str:
    return SILENT.format(daily.name, _day(now), daily.owed, gateway._uk(now))
