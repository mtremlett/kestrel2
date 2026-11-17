"""ended - THE DAY'S CANCELLED ORDERS AND THE BROKER'S WORDS OF WHY, read-only over an open
connection, and the plain name of what a step did (split from conformance for its 400 lines)."""

from __future__ import annotations

import re
from typing import BinaryIO

from desk import paper, placing, reports


def cancelled(wire: BinaryIO, send: paper.Send, door: paper.Door) -> dict[str, str]:
    """Ask over an open connection for the day's ended orders, read-only, and give each that
    was cancelled by the order id it was placed under, with the broker's own words of why it
    ended: the last field of the list's entry for it ("Cancelled by Trader")."""
    paper.start(wire, send, door)
    send(paper.message(reports.ASK_ENDED, 0))
    said: dict[str, str] = {}
    while True:
        fields = paper.receive(wire)
        if fields == [reports.ENDED_END]:
            return said
        if fields[0] != reports.ENDED:
            paper.other(fields)
        elif len(fields) != 101:
            raise ValueError(f"an ended order of a shape the desk does not read: {fields}")
        elif fields[77] in placing.GONE:
            said[fields[22]] = fields[95]


def reasons(door: paper.Door) -> dict[str, str]:
    """Every order cancelled on the account today, with the broker's words of why."""
    return paper.dial(lambda wire, send: cancelled(wire, send, door))


def action(said: str, ended: str) -> str:
    """What a step did, in the broker's plain terms: each fill as a buy, a sale or a stop fill.
    A stop the broker says was cancelled and sold by hand ("Cancelled by Trader") is not a
    stop fill. No fill at all is 'no fill'."""
    kinds = []
    for found in re.finditer(r"(\S+) ([+-]\d+) at ", said.split("held:")[0]):
        name, shares = found.groups()
        stop = name.endswith("-stop")
        gone = f"{name}:" in ended
        kinds.append(
            ("stop cancelled, sold at market" if gone else "stop fill")
            if stop
            else ("buy" if shares[0] == "+" else "sale")
        )
    return ", ".join(kinds) or "no fill"
