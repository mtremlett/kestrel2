"""broker - WHAT THE DESK ASKS OF ANY BROKER, and THE PRETEND BROKER it trades against in
simulation, which behaves like the real one: its own execution ids, stops resting at the
broker, and faults on request."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Protocol

from desk.lines import Line
from desk.orders import Order, Sale
from desk.store import Bar


@dataclass(frozen=True)
class Fill:
    execution_id: str  #: the broker's own id, never the desk's
    order_id: str
    symbol: str
    quantity: int  #: positive bought, negative sold
    price: Decimal
    day: date  #: the session the broker made it in


@dataclass(frozen=True)
class Report:
    """What the broker says of an order it received: its fills, and why it did not fill
    completely; the reason is None only when it did."""

    order_id: str
    fills: tuple[Fill, ...]
    reason: str | None


class Fault(Enum):
    REJECT = "reject"
    PARTIAL = "partial fill"
    DISCONNECT = "disconnection"
    CRASH = "the desk dies after the broker has the order"
    STRAND = "the desk dies after the broker has the order, which is left working, unfilled"


class Crash(Exception):
    """The desk died mid-send: the broker has the order and the desk has no answer."""


class Disconnected(ConnectionError):
    """The connection dropped before the order reached the broker: it was never received."""


class Broker(Protocol):
    """Any broker the send path and the day run can stand on: the pretend one below, the
    paper account behind its door. They ask it five questions, and the kill switch a sixth.
    An answer it cannot give whole is an error raised, never a shorter answer."""

    def report(self, order_id: str) -> Report | None:
        """What the broker did with an order id, or None if it never received it. It knows
        an order from the moment it has it, for as long as the desk might send it again; of
        one a dead desk left working its reason says so, until it fills or is cancelled."""

    def place(self, order: Order | Sale) -> Report:
        """Receive the order and give its last answer: what it did not fill is cancelled,
        never left working. A buy leaves one stop resting on its line, for all the shares
        held, at the order's stop; a sale takes its shares off that stop. Disconnected, and
        nothing else, says the order never arrived: only then is it sent again."""

    def fills(self) -> Iterable[Fill]:
        """The fills of the desk's own orders and their stops, in the order they were made:
        each under the broker's execution id, the same at every reading, with the desk's
        order id, its line's symbol and a price in the line's currency."""

    def holdings(self) -> Iterable[tuple[str, Decimal | int]]:
        """What the account holds, entry by entry as the broker gives them and never added
        together: a name and its shares. A line's symbol names that line and nothing else;
        anything else held goes under a name of its own."""

    def stops(self) -> Iterable[tuple[str, Decimal | int]]:
        """Every stop resting at the broker to sell, entry by entry: a name, as a
        holding's, and the shares it would sell."""

    def cancel(self) -> Iterable[str]:
        """Cancel every order of the desk's own still working at the broker, and name each
        by the desk's order id once the broker says it is cancelled; none working, none
        named. The stops resting to sell what is held are not working orders and stay: the
        kill switch leaves nothing held unprotected. No one else's order is touched."""


@dataclass(frozen=True)
class _Stop:
    order_id: str  #: the stop's own id: the order that set it, with "-stop"
    shares: int
    level: Decimal


class Pretend:
    def __init__(self, archive: Mapping[Line, Sequence[Bar]], faults: Mapping[str, Fault]) -> None:
        """Fills at the archive's prices; a fault applies to a symbol's first order that
        meets a market."""
        self._bars = {(line.symbol, bar.day): bar for line, bars in archive.items() for bar in bars}
        unknown = set(faults) - {symbol for symbol, _ in self._bars}
        if unknown:
            raise ValueError(f"faults for symbols the archive does not hold: {sorted(unknown)}")
        self._faults = dict(faults)
        self._day: date | None = None
        self._received: list[str] = []
        self._reports: dict[str, Report] = {}
        self._fills: list[Fill] = []
        self._held: dict[str, int] = {}
        self._stops: dict[str, _Stop] = {}
        self._working: dict[str, Order | Sale] = {}

    def open(self, day: date) -> None:
        """The market opens on day: orders fill at its prices, resting stops are tested, and
        an order left working fills at the open of its line's next market."""
        if self._day is not None and day <= self._day:
            raise ValueError(f"the market last opened on {self._day}; it cannot open on {day}")
        self._day = day
        for symbol in sorted(self._stops):
            self._test(symbol, self._bars.get((symbol, day)))
        for order_id, order in tuple(self._working.items()):
            bar = self._bars.get((order.line.symbol, day))
            if bar is not None:
                del self._working[order_id]
                self._reports[order_id] = self._execute(order, None, bar)

    def place(self, order: Order | Sale) -> Report:
        """Receive an order at the market: it fills at the day's open. A buy leaves its stop
        resting for the shares filled, one stop a line at the newest level; a sale takes its
        shares off the line's stop."""
        bar = None if self._day is None else self._bars.get((order.line.symbol, self._day))
        fault = None if bar is None else self._faults.pop(order.line.symbol, None)
        if fault is Fault.DISCONNECT:
            raise Disconnected(f"{order.order_id}: the connection dropped before it was received")
        self._received.append(order.order_id)
        if order.order_id in self._reports:
            return Report(order.order_id, (), f"{order.order_id}: a duplicate order id, refused")
        if fault is Fault.STRAND:
            self._working[order.order_id] = order
            report = Report(order.order_id, (), f"{order.order_id}: working, none filled yet")
        else:
            report = self._execute(order, fault, bar)
        self._reports[order.order_id] = report
        if fault in (Fault.CRASH, Fault.STRAND):
            raise Crash(f"{order.order_id}: the desk died before the broker's answer reached it")
        return report

    def cancel(self) -> tuple[str, ...]:
        cancelled = tuple(self._working)
        for order_id in cancelled:
            self._reports[order_id] = Report(order_id, (), f"{order_id}: cancelled, none filled")
        self._working.clear()
        return cancelled

    def report(self, order_id: str) -> Report | None:
        """What the broker did with an order id, or None if it never received it."""
        return self._reports.get(order_id)

    def submitted(self) -> tuple[str, ...]:
        """Every order id received, once for each time it was received."""
        return tuple(self._received)

    def fills(self) -> tuple[Fill, ...]:
        return tuple(self._fills)

    def holdings(self) -> tuple[tuple[str, int], ...]:
        return tuple((symbol, held) for symbol, held in sorted(self._held.items()) if held)

    def stops(self) -> tuple[tuple[str, int], ...]:
        return tuple((symbol, shares) for symbol, (shares, _) in self.resting_stops().items())

    def resting_stops(self) -> dict[str, tuple[int, Decimal]]:
        """Every stop resting at the broker: the shares it would sell, and its level."""
        return {symbol: (s.shares, s.level) for symbol, s in sorted(self._stops.items())}

    def inject(self, symbol: str, quantity: int) -> None:
        """A position the desk did not make, as if bought by hand."""
        if quantity == 0:
            raise ValueError(f"{symbol}: a position of no shares injected")
        self._held[symbol] = self._held.get(symbol, 0) + quantity

    def cancel_stop(self, symbol: str) -> None:
        """A resting stop cancelled behind the desk's back, as if by hand."""
        if symbol not in self._stops:
            raise ValueError(f"{symbol}: no stop rests to be cancelled")
        del self._stops[symbol]

    def _execute(self, order: Order | Sale, fault: Fault | None, bar: Bar | None) -> Report:
        symbol, wanted = order.line.symbol, order.quantity
        if fault is Fault.REJECT:
            return Report(order.order_id, (), f"{order.order_id}: rejected by the broker")
        if bar is None:
            return Report(order.order_id, (), f"{order.order_id}: no market in {symbol} now")
        filled = wanted // 2 if fault is Fault.PARTIAL else wanted
        if filled == 0:
            return Report(order.order_id, (), f"{order.order_id}: none of {wanted} filled")
        reason = None if filled == wanted else f"{order.order_id}: {filled} of {wanted} filled"
        if isinstance(order, Sale):
            fill = self._fill(order.order_id, symbol, -filled, bar.open, bar.day)
            stop = self._stops.pop(symbol, None)
            if stop is not None and stop.shares > filled:
                self._stops[symbol] = replace(stop, shares=stop.shares - filled)
            return Report(order.order_id, (fill,), reason)
        fill = self._fill(order.order_id, symbol, filled, bar.open, bar.day)
        shares = filled + (self._stops[symbol].shares if symbol in self._stops else 0)
        self._stops[symbol] = _Stop(f"{order.order_id}-stop", shares, order.stop)
        self._test(symbol, bar)  #: the rest of the day's range can reach the new stop
        return Report(order.order_id, (fill,), reason)

    def _test(self, symbol: str, bar: Bar | None) -> None:
        """Sell the stop's shares if the day reached its level: at the level, or at the open
        when the day opened below it."""
        stop = self._stops[symbol]
        if bar is not None and bar.low <= stop.level:
            del self._stops[symbol]
            self._fill(stop.order_id, symbol, -stop.shares, min(bar.open, stop.level), bar.day)

    def _fill(self, order_id: str, symbol: str, quantity: int, price: Decimal, on: date) -> Fill:
        fill = Fill(f"X{len(self._fills) + 1:05}", order_id, symbol, quantity, price, on)
        self._fills.append(fill)
        self._held[symbol] = self._held.get(symbol, 0) + quantity
        return fill
