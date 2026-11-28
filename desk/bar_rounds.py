"""bar_rounds - THE INTRADAY ROUNDS (R-RUNNER-202) of the desk unattended: each intraday rule
at each whole bar of its span, through the same check, gate, stops and records as the day's
own; with the paper switch the zoo's rules too, one share each, said to be a MACHINERY TEST,
NOT EVIDENCE OF AN EDGE (CANON B6, his 22 Nov ruling); and the zoo's hour for his message."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from desk import book, day, intraday, placing, restop
from desk.lines import LINES, Line
from desk.orders import ZOO_DAY, Order, Refused, Sale, Settings, size, strategy_of
from desk.rollup import Candle
from desk.running_notes import HOUR, MACHINERY, VENUES, ZOO_NOTE, Desk, Rules, _note, notes
from desk.strategy import Action, Decision


def _latest(
    desk: Desk, lines: Mapping[str, Line], span: intraday.Span, now: datetime
) -> dict[str, list[Candle]]:
    """The venue's lines whose latest whole bar of the span just closed, with the session's bars."""
    length, bars = timedelta(minutes=span.value), dict[str, list[Candle]]()
    for symbol, line in lines.items():
        try:
            whole = intraday.session(desk.hot, line, span, now.date())
            made = [c for c in whole if c.start + length <= now]
        except LookupError:  # the store never held this span for the line: not decided on
            continue
        if made and made[-1].start + 2 * length > now:
            bars[symbol] = made
    return bars


def _rules(desk: Desk) -> Rules:
    """The intraday rules a step trades: the desk's, and the zoo's behind its switch."""
    return {**desk.rules, **(intraday.ZOO_RULES if desk.zoo else {})}


def _intraday(
    desk: Desk, broker: placing.Paper, venue: str, now: datetime, placed: list[book.Sent]
) -> None:
    """THE INTRADAY ROUND (R-RUNNER-202): each rule decides on each line of the venue at its
    latest whole bar (a zoo rule, on the zoo's lines); its orders go by the one send path, each
    id dated with its bar's start, so a bar seen twice sends once. A buy is refused as the
    daily one is (day.refusal). The day's rates are kept first, so every fill can be priced.
    Stops are then moved; a round sending nothing is unkept. `placed` is the step's orders put to
    the broker, shared by its venues: capped at MAX_ORDERS."""
    book.record_rates(desk.root, now.date(), desk.rates(now.date()))
    said: dict[bool, list[str]] = {False: [], True: []}  #: the desk's rules' words; the zoo's
    for name, make in _rules(desk).items():
        machine = name in intraday.ZOO_RULES
        said[machine] += _rule_round(desk, broker, venue, now, name, make, placed)
    if said[False] or said[True]:
        restop.move(desk.root, broker, LINES)
    _bar_notes(desk.root, now, venue, said)


def _rule_round(
    desk: Desk,
    broker: placing.Paper,
    venue: str,
    now: datetime,
    name: str,
    make: Callable[[], intraday.IntradayRule],
    placed: list[book.Sent],
) -> list[str]:
    """One rule's orders at the bar, each said, the book read afresh. A zoo rule decides on the
    zoo's lines and buys one share on ZOO_DAY, its total within day._zoo_full's pounds. An order
    the broker has not seen counts in `placed`; past MAX_ORDERS it is carried to the next round."""
    root, today, said = desk.root, now.date(), list[str]()
    machine, held = name in intraday.ZOO_RULES, book.positions(desk.root)
    owner = {f.symbol: strategy_of(f.order_id) for f in book.fills(root) if f.quantity > 0}
    pool = intraday.zoo_lines() if machine else LINES
    lines = {ln.symbol: ln for ln in pool if ln.venue == venue}
    room = ZOO_DAY if machine else desk.room
    bars = _latest(desk, lines, make().span, now)
    mine = {s: owner[s] for s in held if s in owner}
    for d in intraday.today(venue, bars, mine, {name: make}):
        if d.action is Action.HOLD:
            continue
        oid = f"{today:%Y%m%d}-{name}-{d.symbol}-{d.at:%H%M}{d.action.name[0]}"
        order = _order(desk, room, d, lines[d.symbol], oid, bars[d.symbol][-1].close, held)
        if machine and isinstance(order, Order):  #: tiny: one share, never the room
            order = replace(order, quantity=1)
            order = day._zoo_full(root, order, desk.rates(today)) or order
        if isinstance(order, str):
            said.append(order)
            continue
        new = broker.report(order.order_id) is None
        stand = day.standing(root, today, machine)
        sent = day._send(root, broker, order, room, None, stand, round_=placed)
        placed += [sent] * new
        tag = f" ({MACHINERY})" * machine
        said.append(f"{sent.order_id}, {sent.filled} shares done ({sent.reason or 'sent'}){tag}")
    return said


def _bar_notes(root: Path, now: datetime, venue: str, said: Mapping[bool, list[str]]) -> None:
    """A bar's orders on the record: the desk's rules' under `intraday`, the zoo's under its own
    name (ZOO_NOTE), told in his hourly message, never at each bar."""
    for machine, words in said.items():
        if words:
            name = f"{ZOO_NOTE if machine else 'intraday'} {venue} {now:%H%M}"
            _note(root, now, name, f"{VENUES[venue]}, this bar's orders: {'; '.join(words)}.")


def zoo_hour(root: Path, now: datetime, down: bool = False) -> str:
    """The zoo's last hour for his hourly message, in one line (none: no words): its orders
    filled and those not, never a message of its own at each bar. With the Gateway down its
    orders are not sent, never 'not filled'."""
    if down:
        return f"\nZoo ({MACHINERY}): its orders are not sent while the Gateway is down."
    words = [n.words for n in notes(root) if n.what.split()[0] == ZOO_NOTE and now - n.at < HOUR]
    if not words:
        return ""
    done = sum(w.count(" shares done") - w.count(", 0 shares done") for w in words)
    told = sum(w.count("; ") + 1 for w in words)
    return f"\nZoo ({MACHINERY}): {done} of {told} orders filled in the last hour."


def _order(
    desk: Desk,
    room: Settings,
    d: intraday.IntradayDecision,
    line: Line,
    oid: str,
    close: Decimal,
    held: Mapping[str, int],
) -> Order | Sale | str:
    """An intraday decision's order, under its bar's id; or, of a buy refused, why."""
    today = d.at.date()
    if d.action is Action.SELL:
        return Sale(oid, line, held[d.symbol], session=today)
    if no := day.refusal(desk.root, oid, line, held):  #: the daily buy's own refusals
        return no[0]
    buy, mine = Decision(d.strategy, d.symbol, today, d.action), book.side(desk.root, held, oid)
    try:
        return replace(
            size(buy, line, close, desk.rates(today)[line.currency], room, mine), order_id=oid
        )
    except Refused as refused:
        return str(refused)
