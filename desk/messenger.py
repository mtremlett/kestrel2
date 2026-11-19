"""messenger - THE DESK'S ONE VOICE. Every word the desk says to the operator goes through one
door, to his phone by Telegram, and onto one delivery record. A message has a name. It goes
on the record as asked before the door is tried, so a record that cannot be written stops it
unsaid; once the door takes it Telegram's own number is kept, and under that name it is never
sent again. One the door did not take is an error raised, and is asked again. The record is
one SQLite file: the desk and the watch outside it are two processes, each write whole.

Two messages are owed on every day a venue of the desk's trades, each by an hour on a UK
clock inside his waking day (he sleeps 22:00 to 08:00, docs/DECISIONS.md). THE MORNING
MESSAGE, from 08:00 and owed by 08:30: whether what the desk can ask before the open would
stop today's orders. THE EVENING MESSAGE, from 21:05, five minutes past New York's latest
bell, and owed by 21:30: the day's fills, what is held, and the last day on record. One that
is late still goes, until 22:00; after that it is not sent.

THE ALARM ON SILENCE (`watch`), judged from outside the desk's process: a daily message not
delivered by its hour is told to him, once, at any hour. Each daily message says the kill
switch and halts, read and never written (_gate). THE EMAIL FALLBACK (with_mail, summary):
after two Telegram refusals in a row every line also goes by email; one summary each day."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections.abc import Callable, Iterator, Mapping
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from desk import book, clearance, day, gateway, halt, kill, venues
from desk.gateway import Known
from desk.halt import Blocker
from desk.lines import LINES
from desk.messenger_parts import SECONDS as SECONDS
from desk.messenger_parts import Daily, Mail, sound
from desk.messenger_parts import Undelivered as Undelivered
from desk.messenger_parts import smtp as smtp
from desk.orders import Leg, Refused, leg_of
from desk.supervisor import WAIT

MESSAGES = "messages.db"
TABLES = (
    "CREATE TABLE IF NOT EXISTS messages (at, name PRIMARY KEY, number, text)",
    "CREATE TABLE IF NOT EXISTS mails (at, name PRIMARY KEY, text)",  #: each email sent
    "CREATE TABLE IF NOT EXISTS door (id INTEGER PRIMARY KEY CHECK (id = 1), fails)",
)
ASK = (
    "INSERT INTO messages VALUES (:at, :name, NULL, :text) "
    "ON CONFLICT (name) DO UPDATE SET at = :at, text = :text WHERE number IS NULL"
)
HOST = "api.telegram.org"
#: The bot's key and his chat's id: his alone, kept outside the repository and given to the
#: desk in its environment. The key's shape is checked on entry, so a bad paste is refused by
#: name and never reaches an address, where an error could show it.
SECRETS = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")
BOT_KEY = re.compile(r"[0-9]+:[A-Za-z0-9_-]+")
READ, LIMIT = 65536, 4096  #: most bytes read, most characters sent
CUT = " ... (cut short here: the whole of it is on the desk's delivery record)"
SILENT = (
    "THE DESK IS SILENT. Its {} message for {:%a %d %b} was owed by {:%H:%M} UK and is not on "
    "its delivery record at {:%H:%M}. Please look at the PC: the desk may not be running."
)
CLEAR = (
    "As things stand the desk is set for today on paper: the Gateway answered, today's check "
    "of the account named nothing, and the kill switch is off and drilled."
)
PUT_BACK = "; put back "  #: where day._bare's reason names the stop to put back
STALE = "The paper Gateway was not ready just now, so this is the desk's ledger as last read ({}). "
Post = Callable[[str], int]  #: the door: words to his phone, Telegram's number for them back
DOWN = 2  #: strikes


@dataclass(frozen=True)
class Delivery:
    """One message the door took, as the record keeps it."""

    at: datetime  #: when the desk asked for it, in UTC
    name: str  #: the message's own name: one delivery under each
    number: int  #: Telegram's own number for it
    text: str  #: every word of it, though the door cuts what Telegram would refuse for length

    def __post_init__(self) -> None:
        sound(self.at, self.name, self.text)
        if type(self.number) is not int or not 0 < self.number < 2**63:
            raise ValueError(f"the message {self.name!r}: {self.number!r} is not Telegram's number")


MORNING = Daily("morning", gateway.WAKES, time(8, 30))
EVENING = Daily("evening", time(21, 5), time(21, 30))
SLEEPS = time(22)  #: the hour he sleeps, on a UK clock: from then a late daily message is not sent


def telegram(env: Mapping[str, str]) -> Post:
    """THE ONE REAL DOOR: his phone, by Telegram's bot service, with the key and the chat id
    the environment gives. Either missing, or a key of no key's shape, is refused here by
    name and never shown. What it posts is Undelivered unless Telegram says yes and gives the
    message's number, each step inside SECONDS. Its words never hold the key: of what the far
    end said they repeat the refusal's number and Telegram's own description, no more."""
    missing = [name for name in SECRETS if not env.get(name, "").strip()]
    if missing:
        raise ValueError(f"no {' or '.join(missing)} in the desk's environment: his to set")
    key, chat = (env[name].strip() for name in SECRETS)
    if not BOT_KEY.fullmatch(key):
        raise ValueError(f"{SECRETS[0]} is not a bot key: his to set again")
    secret = key.partition(":")[2]  #: the half that is secret, however an address spells it

    def post(text: str) -> int:
        form = urlencode({"chat_id": chat, "text": text}).encode()
        request = Request(f"https://{HOST}/bot{key}/sendMessage", data=form)  # noqa: S310 - https
        code, why = "", "an answer the desk cannot read"
        try:
            try:
                with urlopen(request, timeout=SECONDS) as reply:  # noqa: S310 - one fixed host
                    said = json.loads(reply.read(READ))
            except HTTPError as refused:  #: Telegram refuses in JSON too, with its description
                code = f"refused, {refused.code}: "
                said = json.loads(refused.read(READ))
        except (OSError, HTTPException, ValueError) as lost:  #: the network's, or no JSON
            said = {"description": f"no answer the desk can read ({lost})"}
        match said:
            case {"ok": True, "result": {"message_id": int(number)}} if not code:
                return number
            case {"description": str(told)}:
                why = told[:200]
        #: raised clear of the network's own error, which holds the address and so the key
        raise Undelivered(f"{HOST} did not deliver: {code}{why}".replace(secret, "(his key)"))

    return post


@contextmanager
def _record(root: Path) -> Iterator[sqlite3.Connection]:
    """The delivery record, opened: each statement is written whole or not at all."""
    root.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(root / MESSAGES, timeout=WAIT, isolation_level=None)) as record:
        for table in TABLES:
            record.execute(table)
        yield record


def deliveries(root: Path) -> tuple[Delivery, ...]:
    """Every message the door took, in the order first asked. One asked that the door has
    not taken is not among them. No record is a desk that has said nothing."""
    with _record(root) as record:
        taken = "SELECT at, name, number, text FROM messages WHERE number IS NOT NULL"
        rows = record.execute(f"{taken} ORDER BY rowid").fetchall()
    return tuple(Delivery(datetime.fromisoformat(at), *rest) for at, *rest in rows)


def send(root: Path, now: datetime, name: str, text: str, post: Post) -> Delivery:
    """A MESSAGE THROUGH THE ONE DOOR, ONCE. It is written on the record as asked first: a
    record that cannot be written is an error raised with nothing said. Already delivered
    under its name, it is not sent again and the delivery made is given back. Else it goes,
    cut where Telegram would refuse its length, and its number is kept. Undelivered, it stays
    asked and goes at the next asking; so does one whose number was never kept (the desk died
    at the door), which he may be told twice, never not at all. A moment not in UTC, or no
    name or words, is refused before anything."""
    sound(now, name, text)
    with _record(root) as record:
        record.execute(ASK, {"at": now.isoformat(), "name": name, "text": text})
        kept = "SELECT at, number, text FROM messages WHERE name = ?"
        at, number, words = record.execute(kept, (name,)).fetchone()
        if number is None:
            number = post(words if len(words) <= LIMIT else words[: LIMIT - len(CUT)] + CUT)
            Delivery(datetime.fromisoformat(at), name, number, words)  #: or no number is kept
            record.execute("UPDATE messages SET number = ? WHERE name = ?", (number, name))
    return Delivery(datetime.fromisoformat(at), name, number, words)


def _today(daily: Daily, now: datetime) -> tuple[str | None, datetime]:
    """The daily message's name today, None on a day no venue trades; and the UK moment."""
    sound(now, daily.name, daily.name)
    local = gateway._uk(now)
    today = local.date()
    trades = any(venues.sessions(venue, today, today) for venue in {line.venue for line in LINES})
    return (f"{daily.name} {today}" if trades else None), local


def _goes(daily: Daily, now: datetime) -> tuple[str | None, str]:
    """The name the daily message goes under now (none off-day, early, asleep), and its opening."""
    name, local = _today(daily, now)
    opens = f"{daily.name.capitalize()}, {local:%a %d %b, %H:%M} UK."
    return (name if daily.start <= local.time() < SLEEPS else None), opens


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


def _lost(root: Path, today: date) -> str:
    """The stops lost today and still to be put back, each once, by order id, shares and level,
    as the day's list holds them (day._bare); no word at all on a day with none."""
    if halt.stopped(root, today) is None:
        return ""
    found = halt.morning(root, today)[Blocker.BOOK]
    back = [b.reason.rpartition(PUT_BACK)[2] for b in found if PUT_BACK in b.reason]
    return f"Lost stops to put back: {'; '.join(back)}. " if back else ""


def _stopped(root: Path, today: date) -> str:
    """Each stop that filled today, told with its money: the shares and price sold, the average
    price bought, the result in pounds after every cost (book.round_trips); no word, and no
    pricing asked, on a day with none."""
    if not any(
        f.day == today and leg_of(f.order_id, f.quantity) is Leg.STOP for f in book.fills(root)
    ):
        return ""
    by_fill: dict[str, list[book.RoundTrip]] = {}
    for trip in book.round_trips(root, LINES):
        if trip.sell.day == today and leg_of(trip.sell.order_id, trip.sell.quantity) is Leg.STOP:
            by_fill.setdefault(trip.sell.execution_id, []).append(trip)
    told = []
    for trips in by_fill.values():
        sold, shares = trips[0].sell, sum(t.sell.quantity for t in trips)
        paid = sum(t.buy.price * t.buy.quantity for t in trips) / -shares
        result = _made(sum((t.profit for t in trips), Decimal(0)))
        told.append(
            f"{sold.symbol}'s stop filled: {-shares} sold @ {sold.price:,.2f} "
            f"(bought {paid:,.2f}), {result} after costs. "
        )
    return "".join(told)


def _made(amount: Decimal) -> str:
    return f"{'lost' if amount < 0 else 'made'} £{abs(amount):,.2f}"


def morning(root: Path, now: datetime, known: Known, post: Post) -> Delivery | None:
    """THE MORNING MESSAGE, once on each day a venue trades, from the hour he wakes: whether
    anything the desk can ask stops today's orders (stops), as of the moment it says; what it
    holds; the stops lost and still to be put back; the last day on record. known is the gateway as it
    was just asked. None when no message goes now."""
    name, opens = _goes(MORNING, now)
    if name is None:
        return None
    reasons = "; ".join(reason.rstrip(".") for reason in stops(root, now, known))
    said = f"As things stand the desk would send NO order today: {reasons}." if reasons else CLEAR
    lost = _lost(root, gateway._uk(now).date())
    return send(root, now, name, f"{opens} {said} {lost}{_gate(root)} {_state(root)}", post)


def evening(root: Path, now: datetime, known: Known, post: Post) -> Delivery | None:
    """THE EVENING MESSAGE, once on each day a venue trades, once every market has been shut
    five minutes: the fills the ledger holds for the day, what the desk holds and the last
    day on record; and, when the gateway just asked was not ready, that the ledger may be
    behind the broker. None when no message goes now."""
    name, opens = _goes(EVENING, now)
    if name is None:
        return None
    today = gateway._uk(now).date()
    dealt = ", ".join(
        f"{'bought' if fill.quantity > 0 else 'sold'} {abs(fill.quantity)} {fill.symbol}"
        for fill in book.fills(root)
        if fill.day == today
    )
    stale = "" if known else STALE.format(known.words.rstrip("."))
    fills = (
        f"{_stopped(root, today)}The desk's fills today: {dealt or 'none'}. {_lost(root, today)}"
    )
    told = f"{opens} {stale}{fills}{_gate(root)} {_state(root)}"
    return send(root, now, name, told, post)


def hourly(root: Path, now: datetime, words: Callable[[], str], post: Post) -> Delivery | None:
    """HIS HOURLY PROFIT AND LOSS (desk/pnl.py), once in each UK hour a venue of the desk's
    trades, at the first asking; words is asked only for one not yet delivered, else None."""
    sound(now, "pnl", "pnl")
    if not any(venues.open_at(v, now) for v in {line.venue for line in LINES}):
        return None
    name = f"pnl {gateway._uk(now):%Y-%m-%d %H}"
    with _record(root) as record:
        gone = record.execute(
            "SELECT 1 FROM messages WHERE name = ? AND number IS NOT NULL", (name,)
        )
        if gone.fetchone():
            return None
    return send(root, now, name, words(), post)


def remind(root: Path, now: datetime, post: Post) -> Delivery | None:
    """His weekly login's reminder (gateway.reminder), once for each Sunday's due."""
    sound(now, "login", "login")
    due = gateway.reminder(now)
    return send(root, now, f"login {due.due:%Y-%m-%d}", due.line, post) if due else None


def watch(root: Path, now: datetime, post: Post) -> tuple[Delivery, ...]:
    """THE ALARM ON SILENCE, asked from outside the desk's own process every few minutes:
    each daily message owed by now and not delivered is told to him, once, at any hour.
    Given back: every such alarm standing, told now or before; none, and the desk has said
    all it owes today. A late message ends its own alarm."""
    owed = [(daily, *_today(daily, now)) for daily in (MORNING, EVENING)]
    with _record(root) as record:
        taken = record.execute("SELECT name FROM messages WHERE number IS NOT NULL").fetchall()
    return tuple(
        send(root, now, f"silence {name}", SILENT.format(daily.name, at, daily.owed, at), post)
        for daily, name, at in owed
        if name and at.time() >= daily.owed and (name,) not in taken
    )


def _mailed(root: Path, now: datetime, name: str, text: str, mail: Mail) -> None:
    """One email under its name, once, kept on the record only after the server took it."""
    sound(now, name, text)
    with _record(root) as record:
        if not record.execute("SELECT 1 FROM mails WHERE name = ?", (name,)).fetchone():
            mail(f"Kestrel desk: {name}", text)
            record.execute("INSERT INTO mails VALUES (?, ?, ?)", (now.isoformat(), name, text))


def with_mail(root: Path, now: datetime, post: Post, mail: Mail) -> Post:
    """THE FALLBACK: the Telegram door, counted. A refusal is a strike on the record, a taking
    clears them; from DOWN strikes every line also goes by email, once, before Telegram is
    tried. A refused email does not stop Telegram; both refused, both reasons are raised."""

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
    """THE DAILY SUMMARY EMAIL, whatever Telegram does, from the evening's hour."""
    name, opens = _goes(EVENING, now)
    if name:
        _mailed(root, now, f"summary {name}", f"{opens} {_state(root)}", mail)
