"""broker - THE PRETEND BROKER the desk trades against in simulation. It behaves like the
real one: its own execution ids, stops resting at the broker, and faults on request."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from enum import Enum

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


class Crash(Exception):
    """The desk died mid-send: the broker has the order and the desk has no answer."""


class Disconnected(ConnectionError):
    """The connection dropped before the order reached the broker: it was never received."""


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

    def open(self, day: date) -> None:
        """The market opens on day: orders fill at its prices and resting stops are tested."""
        if self._day is not None and day <= self._day:
            raise ValueError(f"the market last opened on {self._day}; it cannot open on {day}")
        self._day = day
        for symbol in sorted(self._stops):
            self._test(symbol, self._bars.get((symbol, day)))

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
        report = self._execute(order, fault, bar)
        self._reports[order.order_id] = report
        if fault is Fault.CRASH:
            raise Crash(f"{order.order_id}: the desk died before the broker's answer reached it")
        return report

    def report(self, order_id: str) -> Report | None:
        """What the broker did with an order id, or None if it never received it."""
        return self._reports.get(order_id)

    def submitted(self) -> tuple[str, ...]:
        """Every order id received, once for each time it was received."""
        return tuple(self._received)

    def fills(self) -> tuple[Fill, ...]:
        return tuple(self._fills)

    def positions(self) -> dict[str, int]:
        return {symbol: held for symbol, held in sorted(self._held.items()) if held}

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
