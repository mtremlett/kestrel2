"""placing - THE PAPER ACCOUNT BEHIND THE SEND PATH: what the desk asks of any broker
(broker.Broker), answered by the paper account through the one door (desk/paper.py): what
the broker did with an order, the desk's fills, what the account holds, the stops resting on
it, the kill switch's cancel, and the placing of an order. NO BUY GOES WITHOUT ITS STOP: the
two are sent together, the stop to wait on the buy; and after any order the line is left
under one stop of the desk's own, for the shares the account then holds of it, once the
broker's word, its fills and the account's shares agree.

Each answer is read from the gateway afresh. The fills, open orders and stops are the desk's
own alone (desk/reports.py): anyone else's is named by the day's check (desk/clearance.py).
The holdings are the whole account's. An answer that cannot be read whole is an error raised.

Two things are sent that are no question: an order, by `place` alone, once the kill switch
was drilled, the day's check came back clean, the gateway is ready and no other order is open
(`_before`); and the stop a line is left under (`settle`), by `place` and, after a restart,
desk/running.py. And a cancel of an order of the desk's own: by the kill switch, of each still
working but a stop resting to sell what is held; by `place`, of what the broker did not fill
and of a line's stop before a sale; by `settle`, of a stop only once its replacement rests."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import BinaryIO

from desk import clearance, gateway, kill, order_times, paper, reports, venues
from desk import placing_parts as parts
from desk.broker import Disconnected, Fill, Report
from desk.listing import Listing, Unlisted
from desk.orders import Order, Refused, Sale
from desk.paper import Resting
from desk.placing_parts import GONE as GONE
from desk.placing_parts import OVER
from desk.placing_parts import Stop as Stop

MARKET = ("MKT", "", "", "DAY")  #: an order's kind: at the market, no price, for the day


class NotCancelled(Exception):
    """The broker refused to cancel an order of the desk's own, and still lists it working."""


class Unprotected(Exception):
    """The desk cannot say a line is under the stop due on it: the broker ended a stop sent to
    it, or what it says of an order does not agree with the account."""


def _working(order: Resting) -> bool:
    """Whether an order of the desk's own is the kill switch's to cancel: not one that is over,
    nor a stop to sell (reports.stop_to_sell), whose line would be unprotected."""
    return not reports.stop_to_sell(order) and order.state not in OVER


def _with(listed: Listing, order: Order) -> Stop:
    """The stop a buy goes with: its shares, at the order's stop put onto the broker's step
    and unit, under the order's id and "-stop"."""
    return Stop(Decimal(order.quantity), listed.floor(order.stop), f"{order.order_id}-stop")


def _place(
    wire: BinaryIO,
    send: paper.Send,
    listed: Listing,
    order: Order | Sale,
    door: paper.Door,
    times: order_times.Times,
) -> tuple[str, str | None, tuple[str, ...]]:
    """Send an order over an open connection, once, and read the broker's word of it: the
    number it went under, the state the broker says it is over in (filled, or cancelled), or
    None, and every notice the broker gave of it. It goes at the market, for the day, under
    the number the gateway gave at the start. A BUY GOES WITH ITS STOP (_with): the buy held
    back, and behind it, under the next number, the stop, which waits on the buy and sends
    both on. The reading ends when the order is over, or when the gateway has said nothing
    for as long as an order is given to fill (paper.FILL_SECONDS): the order is then not over
    (None), and is the desk's to cancel. A gateway that hangs up first is an error: the order
    may have arrived. The moments it was sent, accepted and filled are taken down (times)."""
    wire = times.watch(wire)
    first, ref, shares = paper.start(wire, send, door), order.order_id, order.quantity
    number, numbers = str(first), [str(first)]
    times.sent(number)
    if isinstance(order, Sale):
        send(parts.message(number, listed, ("SELL", *MARKET), shares, ref))
    else:
        numbers.append(str(first + 1))
        buy = parts.message(number, listed, ("BUY", *MARKET), shares, ref, "0")
        send(buy + parts.selling(numbers[1], listed, _with(listed, order), "1", number))
    notices: list[str] = []
    try:
        for told, word, code in parts.told(wire, numbers, door):
            if code is not None:
                notices.append(f"{code}: {word}")
            elif told == number:
                return number, word, tuple(notices)
    except TimeoutError:  #: the door's wait ran out in silence: its answer is "not over"
        pass
    return number, None, tuple(notices)


def _withdrawn(report: Report) -> Report:
    """An order the desk cancelled after its wait, told as the desk's own act: it went at the
    market (MARKET) and was not filled within the door's wait. What the broker then says of it
    follows; an order the broker ends itself keeps the broker's own words (Paper.report)."""
    if report.reason is None:
        return report
    why = f"{report.order_id}: withdrawn by the desk: not filled at the market within "
    why += f"{paper.FILL_SECONDS} seconds"
    broker = report.reason.removeprefix(f"{report.order_id}: ")
    if broker.startswith("the broker says "):
        why += f"; {broker}"
    return replace(report, reason=why)


def _rest(wire: BinaryIO, send: paper.Send, listed: Listing, stop: Stop, door: paper.Door) -> None:
    """Send a stop to sell over an open connection, alone, and read until the broker says it
    holds it. One it ends instead is an error with its notices; so are silence and a hang-up."""
    number = str(paper.start(wire, send, door))
    send(parts.selling(number, listed, stop))
    notices: list[str] = []
    for _, word, code in parts.told(wire, (number,), door, OVER | reports.HELD):
        if code is not None:
            notices.append(f"{code}: {word}")
        elif word in reports.HELD:
            return
        else:
            raise Unprotected(f"{stop.ref}: the broker ended the stop, {word}; it said: {notices}")


def on(account: paper.Account, listed: Listing, door: paper.Door) -> tuple[Decimal, list[Resting]]:
    """A line in one reading of the account: the shares the account holds of it, and the
    door's own stops to sell open on it, held by the broker or not yet."""
    name = paper.own(listed.line)
    held = sum((h.shares for h in account.holdings if h.name == name), Decimal(0))
    stops = [
        o
        for o in account.orders
        if o.contract == listed.contract and o.state not in OVER
        if reports.ours(door, o.client, o.ref) and reports.stop_to_sell(o)
    ]
    return held, stops


class Paper:
    """The paper account, as a broker the send path, the day run and the kill switch can
    stand on."""

    def __init__(
        self,
        listings: Mapping[str, Listing | Unlisted],
        root: Path,
        clock: Callable[[], datetime],
        door: paper.Door,
        stamp: Callable[[], datetime] = lambda: datetime.now(UTC),
        within: bool = False,
    ) -> None:
        """listings is each of the desk's lines as the broker lists it now (listing.read): by them
        a fill, an order and a holding are known as a line's. root holds the desk's record, the
        day's checks among it; clock gives the moment, in UTC: read only before a send; stamp is
        the real moment, taken on each event of an order for its trail; door is who the broker
        is spoken to as, and what of the account is its own; within, a bar's round's broker."""
        self._listings, self._root, self._clock = dict(listings), root, clock
        self._stamp, self._door, self._within = stamp, door, within

    def _orders(self) -> reports.Orders:
        return reports.orders(paper.read(self._door).orders, self._listings, self._door)

    def report(self, order_id: str) -> Report | None:
        """What the broker did today with an order id, or None if it tells nothing of it. Its
        open orders are read first, then the day's ended ones, then the day's fills, so that
        an order which ends or fills between the readings is in one of them: read the other
        way round it could be in none, and be sent again. (Seen on real orders, 14 November
        2026: the ended list had each at once after its cancel, and keeps one refused on
        entry, as cancelled; a fill is still unseen.) The reason is None only for an order
        the broker lists once, ended and filled whole, with fills that come to the shares it
        says were filled; otherwise it is everything the broker says of it."""
        listed = [o for o in self._orders().unsettled if o.ref == order_id]
        ended = [e for e in reports.ended(self._door) if e.ref == order_id]
        fills = tuple(fill for fill in self.fills() if fill.order_id == order_id)
        if not (listed or ended or fills):
            return None
        done = sum(abs(fill.quantity) for fill in fills)
        whole = reports.Ended(order_id, "Filled", Decimal(done), Decimal(0))
        if fills and not listed and ended == [whole]:
            return Report(order_id, fills, None)
        said = [f"{o.state}, {o.left} shares still to be done" for o in listed]
        said += [f"{e.state}, {e.filled} shares filled and {e.left} not" for e in ended]
        told = "; ".join(said) or "nothing of the order"
        reason = f"{order_id}: the broker says {told}; its fills today come to {done} shares"
        return Report(order_id, fills, reason)

    def place(self, order: Order | Sale) -> Report:
        """Send an order to the paper broker and give its last answer (_place) as the broker
        then reports it (report), with the notices it gave. A buy goes with its stop, and the
        line is then left under the one stop due on it (_due, settle), but only once the
        account's shares of it have moved by exactly the order's fills, and an order called
        filled has fills for all its shares; otherwise
        Unprotected, the stops left as they are. Nothing is sent unless the order is cleared
        (_cleared) and the line settled (_before): Refused, or Disconnected. A sale that
        errs after its stop was cancelled puts the stop back, for the shares held."""
        listed, new = self._cleared(order)
        was, before = self._before(listed, order)
        ref, times = order.order_id, order_times.Times(self._stamp, self._door.client)
        try:
            number, last, notices = paper.dial(
                lambda wire, send: _place(wire, send, listed, order, self._door, times),
                paper.FILL_SECONDS,
            )
            silent = last is None
            if silent:
                last = self._cancelled({number: ref})[number]
                times.note("cancelled")
            report = self.report(ref) or Report(ref, (), f"{ref}: the broker tells nothing of it")
            if (
                silent and last in GONE
            ):  #: the broker found it working, and cancelled it for the desk
                report = _withdrawn(report)
            moved = sum(fill.quantity for fill in report.fills)
            held, stops = on(paper.read(self._door), listed, self._door)
            if held != was + moved or (last == "Filled" and abs(moved) != order.quantity):
                raise Unprotected(
                    f"{ref}: the broker's last word of it was {last}, its fills come to {moved} "
                    f"shares, and the account's {listed.line.symbol} went from {was} to {held}: "
                    "these do not agree, and the line's stops are left as they are"
                )
        except Exception:  #: a sale cancelled its stop: put it back for what is held, re-raise
            if isinstance(order, Sale) and before:
                self._putback(listed, before)
            raise
        finally:
            times.keep(self._root, ref)
        self.settle(listed, held, stops, parts.due(before, held, moved, new))
        if report.reason is None or not notices:
            return report
        return replace(report, reason=f"{report.reason}; it said: {'; '.join(notices)}")

    def _cleared(self, order: Order | Sale) -> tuple[Listing, Stop | None]:
        """The line as the broker lists it, and the stop a buy goes with (_with), for an order
        cleared to go: the broker lists the line and its price is above the buy's stop (an error
        raised), the order is DUE today (dated the venue's session before today's; within a bar's
        round, today's), the kill switch was drilled within its month and today's check came back
        clean (Refused, all), and the gateway says it is ready: Disconnected."""
        symbol, now = order.line.symbol, self._clock()
        listed = self._listings.get(symbol)
        if not isinstance(listed, Listing):
            why = listed.reason if listed else "it was not asked for the line"
            raise Refused(f"{order.order_id}: not sent, the broker does not list {symbol}: {why}")
        new = _with(listed, order) if isinstance(order, Order) else None
        if order.session is None:
            raise ValueError(f"{order.order_id}: not sent, the order is dated no session")
        last = venues.sessions(order.line.venue, now.date() - timedelta(days=9), now.date())[-2:]
        if last[1:] != (now.date(),) or order.session != last[-1 if self._within else 0]:
            why = "is not the session of" + f" {order.line.venue}'s next after" * (not self._within)
            raise Refused(f"{order.order_id}: not sent, {now:%Y-%m-%d} {why} the one it is dated")
        if not kill.drilled(self._root, now.date()):
            why = f"the kill switch was not drilled in the last {kill.DRILL_DAYS} days"
            raise Refused(f"{order.order_id}: not sent, {why}")
        clearance.require(self._root, now, order.order_id)
        if not (known := gateway.known(now, door=self._door)):
            raise Disconnected(f"{order.order_id}: not sent, {known.words}")
        return listed, new

    def _before(self, listed: Listing, order: Order | Sale) -> tuple[Decimal, Stop | None]:
        """A line before an order goes: the shares the account holds of it and the one stop of
        the desk's own it is under, or None. Refused: two stops open on it, or one the broker
        is not holding; and WHILE ANY OTHER ORDER IS OPEN AT THE BROKER, on any line, anyone's.
        A SALE GOES ONLY WHEN NO STOP RESTS UNDER THE SAME SHARES (R-MONEY-17): the line's stop
        is cancelled first (not tied at the broker, both could sell); if it ended another way
        meanwhile, the stop is put back for the shares held, Refused; if it sold, Unprotected."""
        order_id, account = order.order_id, paper.read(self._door)
        (held, stops), told = (
            on(account, listed, self._door),
            reports.orders(account.orders, self._listings, self._door),
        )
        kept = [o for o in stops if o.state in reports.HELD]
        rests = [Stop(o.left, o.level, o.ref) for o in kept if o.level is not None]
        if len(stops) > 1 or len(rests) != len(stops):
            said = [f"{o.ref} ({o.state})" for o in stops]
            where = f"the desk's own stops on {listed.line.symbol} are not settled: {said}"
            raise Refused(f"{order_id}: not sent, {where}")
        idle = [f"{o.ref} ({o.state})" for o in told.unsettled + told.others if o.state not in OVER]
        if idle:
            raise Refused(f"{order_id}: not sent, orders are still open at the broker: {idle}")
        if isinstance(order, Sale) and kept:
            ours = rests[0]
            try:
                ends = self._cancelled({o.number: o.ref for o in kept})
                now = on(paper.read(self._door), listed, self._door)[0]
            except Exception:  #: silent, hung up or unread: the stop may be gone
                self._putback(listed, ours)
                raise
            if "Filled" in ends.values():
                raise Unprotected(f"{order_id}: not sent, its stop sold as it was cancelled")
            if now != held or not GONE.issuperset(ends.values()):
                self._putback(listed, ours)
                raise Refused(f"{order_id}: not sent, its stop ended: {ends}, {now} held")
        return held, (rests[0] if rests else None)

    def _putback(self, listed: Listing, stop: Stop) -> None:
        """Put a line under its stop again, for the shares the account now holds."""
        held, stops = on(paper.read(self._door), listed, self._door)
        self.settle(listed, held, stops, parts.due(stop, held, 0, None))

    def settle(
        self, listed: Listing, held: Decimal, stops: Sequence[Resting], due: Stop | None
    ) -> None:
        """Leave a line under the one stop due on it, or none; held is the account's shares of
        it and stops the desk's own open on it, as just read. One the broker holds for those
        shares at that level is kept, whatever its reference. With none, the stop due is
        sent to rest first (_rest) and only then is every other cancelled: never under none
        meanwhile. A stop that sold as it was cancelled is Unprotected."""
        resting = (o for o in stops if o.state in reports.HELD)
        kept = next((o for o in resting if due and (o.left, o.level) == due[:2]), None)
        if due is not None and kept is None:
            paper.dial(lambda wire, send: _rest(wire, send, listed, due, self._door))
        spare = {o.number: o.ref for o in stops if o is not kept}
        said = self._cancelled(spare) if spare else {}
        odd = {spare[number]: word for number, word in said.items() if word not in GONE}
        if odd and (
            "Filled" in odd.values() or on(paper.read(self._door), listed, self._door)[0] != held
        ):
            raise Unprotected(
                f"a stop of the desk's own on {listed.line.symbol} ended another way as it was "
                f"being cancelled, sold perhaps: {odd}"
            )

    def restop(self, symbol: str, level: Decimal) -> None:
        """MOVE A RESTING STOP: the line's one stop is moved to level (the line's currency), for
        all the shares held, by resting the new one first and cancelling the old one after
        (settle): never unprotected meanwhile. One already at that level sends nothing."""
        if not isinstance(listed := self._listings[symbol], Listing):
            raise ValueError(f"{symbol}: the broker does not list it, no stop is moved")
        held, stops = on(paper.read(self._door), listed, self._door)
        self.settle(listed, held, stops, parts.moved(listed, held, stops, level))

    def fills(self) -> tuple[Fill, ...]:
        """The desk's own fills of today, as its ledger keeps them (reports.fills)."""
        return reports.fills(reports.read(self._door), self._listings, self._door).ours

    def holdings(self) -> tuple[tuple[str, Decimal], ...]:
        """Every holding of the account, entry by entry: one of a line of the desk's under
        the line's symbol, anything else under its own name (paper.Holding.name)."""
        lines = {paper.own(listed.line): symbol for symbol, listed in self._listings.items()}
        return tuple((lines.get(h.name, h.name), h.shares) for h in paper.read(self._door).holdings)

    def stops(self) -> tuple[tuple[str, Decimal], ...]:
        """The desk's own stops the broker is holding to sell, entry by entry."""
        return self._orders().stops

    def cancel(self) -> tuple[str, ...]:
        """THE KILL SWITCH'S QUESTION: every order of the desk's own still working is sent
        a cancel, and each the broker then says is cancelled is named by the desk's order
        id, in the order listed; one that filled first is not named, and its fill is in the
        day's fills. None working: nothing is sent, and none named. A cancel the broker
        refuses is settled by the account read again: an order no longer working there was
        over before the cancel reached it; one still working is an error raised."""
        working = {o.number: o.ref for o in self._orders().unsettled if _working(o)}
        said = self._cancelled(working) if working else {}
        return tuple(ref for number, ref in working.items() if said[number] in GONE)

    def _cancelled(self, working: Mapping[str, str]) -> dict[str, str]:
        """Send a cancel for each of the desk's own orders given, its order id by its number,
        and give the broker's last word of each. A cancel refused is settled by the account
        read again; an order still open there, a stop included, is an error raised."""
        said = paper.dial(lambda wire, send: parts.cancel(wire, send, tuple(working), self._door))
        refused = {number: word for number, word in said.items() if word not in OVER}
        listed = paper.read(self._door).orders if refused else ()
        still = [
            f"{o.ref} ({refused[o.number]})"
            for o in listed
            if o.number in refused and o.client == str(self._door.client) and o.state not in OVER
        ]
        if still:
            raise NotCancelled(f"the broker still lists as working, its cancel refused: {still}")
        return said
