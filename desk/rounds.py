"""rounds - EACH VENUE'S ORDERS FOR THE DAY, as the desk unattended makes them: the venues
whose round is owed (`_pending`), the round itself by the money path's own day on the bars
saved before today (`_round`), and the round owed once more of orders the desk itself
cancelled or the round cap carried (`_again`, R-RUNNER-395)."""

from __future__ import annotations

import csv
from collections.abc import Collection, Sequence
from datetime import date, datetime
from pathlib import Path

from desk import bar_rounds, book, conformance_tape, day, halt, placing, restop, venues, watch
from desk.lines import LINES, YARDSTICK, Line
from desk.orders import is_zoo
from desk.running_notes import DAY, MACHINERY, ORDERS, VENUES, Desk, Saved, _note, notes
from desk.store import Bar


def _pending(root: Path, now: datetime, seen: watch.Look | None, once: bool = True) -> list[str]:
    """The venues whose round is owed now: in continuous trading, with no round of today's on
    the record (not once: the intraday rounds, whatever is), and, of the market's own venue,
    once the look has read a bar of the session (watch.EARLY). A failed look holds every round."""
    if seen is None:
        return []
    done = {note.what for note in notes(root) if note.at.date() == now.date()}
    trading = {venue: venues.open_at(venue, now) for venue in VENUES}
    return [
        venue
        for venue, hours in trading.items()
        if hours and now < hours.close and not (once and ORDERS.format(venue) in done)
        if venues.uk_time(now).time() >= conformance_tape.STARTS[venue]
        if not (venue == YARDSTICK.venue and seen.unread.get(YARDSTICK) == watch.EARLY)
    ]


def _again(root: Path, now: datetime, seen: watch.Look | None) -> dict[str, set[str]]:
    """THE ROUND OWED ONCE MORE (R-RUNNER-395): of a venue still trading whose round is on the
    record and not yet made again, the symbols of today's orders the desk ITSELF cancelled,
    or the round cap carried (the morning's list), with nothing filled under the id or its -r1;
    only those go again, as <id>-r1."""
    path = root / book.CANCELS
    if seen is None:
        return {}
    mine = set[str]()
    if path.exists():
        with path.open(newline="", encoding="utf-8") as rows:
            mine = {row[0] for row in csv.reader(rows) if row[1:] == [now.date().isoformat()]}
    if (root / halt.BLOCKED / f"{now.date()}.csv").exists():  #: R-RUNNER-473: the round cap's own
        mine |= {b.order_id for b in halt.morning(root, now.date())[halt.Blocker.CARRIED]}
    done = {note.what for note in notes(root) if note.at.date() == now.date()}
    filled = {fill.order_id for fill in book.fills(root) if fill.day == now.date()}
    out = dict[str, set[str]]()
    for venue in VENUES:
        hours = venues.open_at(venue, now)
        if not hours or now >= hours.close or ORDERS.format(venue) not in done:
            continue
        if f"{ORDERS.format(venue)} again" in done:
            continue
        stamp = f"{now:%Y%m%d}-"
        cut = {
            line.symbol
            for line in LINES
            if line.venue == venue
            for oid in mine
            if oid.startswith(stamp) and oid.endswith(f"-{line.symbol}")
            if not {oid, f"{oid}-r1"} & filled
        }
        if cut:
            out[venue] = cut
    return out


def _fit(
    saved: Saved, venue: str, today: date
) -> tuple[dict[Line, Sequence[Bar]], list[str], date]:
    """Of the bars saved before today, a venue's lines fit to decide on; the lines left out,
    by name (parked, or no bar of the session before today); and that session."""
    bars, parked = saved
    last = venues.sessions(venue, today - 9 * DAY, today)[-2]
    mine = {line: series for line, series in bars.items() if line.venue == venue}
    stale = {line for line, series in mine.items() if [bar.day for bar in series][-1:] != [last]}
    out = sorted(line.symbol for line in mine if line in stale or line.symbol in parked)
    return {line: series for line, series in mine.items() if line.symbol not in out}, out, last


def _round(
    desk: Desk, broker: placing.Paper, venue: str, now: datetime, only: Collection[str] = ()
) -> None:
    """A venue's orders for today, by the money path's own day, on the bars saved before today;
    the round goes on the record with the answer to each order. A line parked by the store, or
    with no bar of the session before, is left out and named. Then each held line's stop is
    moved to 10% under its fill once (restop). A desk that dies in it runs it again."""
    today = now.date()
    kept = desk.held(today)
    saved, out, last = _fit(kept, venue, today)
    if only:  #: the round again: just the lines whose orders the desk cancelled
        saved, out = {ln: s for ln, s in saved.items() if ln.symbol in only}, []

    def tell(
        name: str, words: str
    ) -> None:  #: kept as a note: told at his next step until delivered
        _note(desk.root, now, name, words)

    rates = desk.rates(today)
    sent = day.trade(desk.root, saved, broker, desk.room, today, rates, tell, zoo=desk.zoo)
    restop.move(desk.root, broker, LINES)  #: each held line's stop, under its fill (R-RUNNER-220)
    said, zoo = [
        [
            f"{s.order_id}, {s.filled} shares done" + f" ({s.reason})" * bool(s.reason)
            for s in sent
            if is_zoo(s.order_id) == machine
        ]
        for machine in (False, True)
    ]
    hourly = {True: [f"{w} ({MACHINERY})" for w in zoo]}
    bar_rounds._bar_notes(desk.root, now, venue, hourly)  #: hourly alone
    words = f"{VENUES[venue]}, today's orders: {'; '.join(said) or 'none sent in this round'}."
    held = _held_out(desk.root, out, kept[1], last)
    out = [symbol for symbol in out if symbol not in held]
    left = f" Left out, parked or with no bar of {last:%a %d %b}: {', '.join(out)}."
    name = ORDERS.format(venue) + " again" * bool(only)
    _note(desk.root, now, name, words + left * bool(out) + "".join(held.values()))


def _held_out(
    root: Path, out: Sequence[str], parked: Collection[str], last: date
) -> dict[str, str]:
    """Of the lines left out, those the desk HOLDS, each with why its sell rule was not
    checked today and the level its stop rests at (R-RUNNER-312)."""
    held, levels, buys = book.positions(root), book.levels(root), dict[str, str]()
    for fill in book.fills(root):
        if fill.quantity > 0:
            buys[fill.symbol] = fill.order_id
    why = {s: "parked by the store" if s in parked else f"no bar of {last:%a %d %b}" for s in out}
    return {
        s: f" {s} held, not judged today: {why[s]}; its stop rests at "
        f"{levels.get(f'{buys[s]}-stop', 'a level the desk has not kept')}."
        for s in out
        if held.get(s)
    }
