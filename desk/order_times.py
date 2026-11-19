"""order_times - WHEN THE BROKER DID WHAT WITH AN ORDER AT THE MARKET: for each order the desk
sends, the moment it was sent, the moment the broker first reports it PreSubmitted or
Submitted, each fill's moment and size, and the moment the desk cancelled it, all UTC. They
are read off the messages the desk already reads (the wire is watched, nothing is asked) and
kept beside the day's orders, in `order_times.csv` under the desk's root, one row per event
under the order's id, so the wait an order is given (paper.FILL_SECONDS) is set from them."""

from __future__ import annotations

import csv
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

from desk import paper, reports

TIMES = "order_times.csv"
COLUMNS = ("order_id", "event", "at", "shares")
FILLED_SHARES = 19  #: where a fill message names its size


class Times:
    """The events of one order, as they happen: sent, accepted (the first time only), each
    fill, cancelled. Rows are (event, UTC moment, shares or an empty word)."""

    def __init__(self, clock: Callable[[], datetime], client: int) -> None:
        self._clock, self._client = clock, str(client)
        self._number: str | None = None
        self.rows = list[tuple[str, str, str]]()

    def note(self, event: str, shares: str = "") -> None:
        """Take down an event at this moment."""
        self.rows.append((event, self._clock().isoformat(), shares))

    def sent(self, number: str) -> None:
        """The order goes now, under this number at the gateway: its messages are heeded."""
        self._number = number
        self.note("sent")

    def heed(self, fields: list[str]) -> None:
        """Take down what a message of the gateway says of the order, if it does."""
        if self._number is None:
            return
        if fields[0] == paper.STATUS and len(fields) == 12 and fields[1] == self._number:
            first = all(event != "accepted" for event, _, _ in self.rows)
            if fields[9] == self._client and fields[2] in reports.HELD and first:
                self.note("accepted")
        elif fields[:2] == [paper.FILL, paper.UNASKED] and len(fields) == 31:
            if fields[2] == self._number:
                self.note("fill", fields[FILLED_SHARES])

    def watch(self, wire: BinaryIO) -> BinaryIO:
        """The wire, as it was, with each message heeded as it is read."""
        return _Watched(wire, self)  # type: ignore[return-value]  # reads only: all that is used

    def keep(self, root: Path, order_id: str) -> None:
        """Append the events to the day's record under the order's id; none, nothing."""
        path = root / TIMES
        fresh = not path.exists()
        with path.open("a", newline="", encoding="utf-8") as out:
            writer = csv.writer(out)
            if fresh:
                writer.writerow(COLUMNS)
            writer.writerows((order_id, *row) for row in self.rows)


class _Watched:
    """A wire whose messages are read alike (a length of four bytes, then the body) and
    heeded when whole."""

    def __init__(self, wire: BinaryIO, times: Times) -> None:
        self._wire, self._times, self._size = wire, times, 0

    def read(self, size: int = -1) -> bytes:
        data = self._wire.read(size)
        if self._size == 0:
            self._size = int.from_bytes(data, "big") if len(data) == 4 else 0
        else:
            self._size = 0
            if len(data) == size:
                self._times.heed(data.decode().split("\0")[:-1] or [""])
        return data
