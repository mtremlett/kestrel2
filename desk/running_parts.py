"""running_parts - what running is built of, apart from the step: the recovery of a desk that
died part-way through an order (`recover`) and the one stop a line is left under (`_due`)."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path

from desk import book, kill, paper, placing
from desk.listing import Listing, Unlisted
from desk.paper import Resting
from desk.reports import HELD

PUT_RIGHT = "The desk put right what a desk that stopped part-way left at the paper broker: {}."


def recover(
    root: Path,
    broker: placing.Paper,
    listings: Mapping[str, Listing | Unlisted],
    today: date,
    door: paper.Door,
) -> tuple[str, ...]:
    """AFTER A RESTART: what a desk that died part-way through an order left at the broker,
    put right by the order's own rules (desk/placing.py), each thing done named. Every order
    of the desk's own still working is cancelled: what `place` did not see filled is never
    left working. The ledger takes the fills the broker made meanwhile. Then each line with
    a stop of the desk's own open on it, now or before that cancel (the broker ends a buy's
    stop with the buy), if its shares at the broker are the book's, is left under the one
    stop due (_due, Paper.settle). A line whose shares are not the book's is left as it is,
    for the day's check to name; so is one held under no stop at all and no level
    kept in the book; one with a level kept is given its newest buy's stop back. Nothing is
    done while the kill switch is on, or undrilled: the desk sends nothing then."""
    if book.killed(root) or not kill.drilled(root, today):
        return ()
    before = paper.read(door)
    did = [f"cancelled {name}, left working" for name in broker.cancel()]
    book.collect(root, broker)
    held, account = book.positions(root), paper.read(door)
    newest = {f.symbol: f.order_id for f in book.fills(root) if f.quantity > 0}
    bought, kept = set(newest.values()), book.levels(root)
    for listed in listings.values():
        if isinstance(listed, Listing):
            shares, stops = placing.on(account, listed, door)
            was = placing.on(before, listed, door)[1]
            symbol = listed.line.symbol
            lost = f"{newest.get(symbol)}-stop"  #: the stop the book kept a level for (R-MONEY-30)
            back = placing.Stop(shares, listed.floor(kept[lost]), lost) if lost in kept else None
            mine = (stops or was or back) and shares == held.get(symbol, 0)
            for due in _due(shares, stops, was, bought, back) if mine else ():
                broker.settle(listed, shares, stops, due)
                under = f"one stop for {shares} shares" if due else "no stop, none of it held"
                did.append(f"{listed.line.symbol} left under {under}")
    return tuple(did)


def _due(
    shares: Decimal,
    stops: Sequence[Resting],
    was: Sequence[Resting],
    bought: Collection[str],
    back: placing.Stop | None,
) -> tuple[placing.Stop | None, ...]:
    """The one stop a line found after a restart is to be left under, or None for none; and
    nothing at all for a line to be left as it is. The stop is for the shares held, at the
    level and under the name of the newest of the line's stops, open now (stops) or before
    the dead desk's orders were cancelled (was), whose buy the ledger holds a fill of: a
    stop that came with a buy that bought nothing gives no level, as after any order
    (placing._due). No share held, and no stop is due: one left resting could sell short.
    A line held with no stop at all is given back (back) the stop of its newest buy at the
    level the book kept (R-MONEY-30). Left as it is: a line already under one stop the broker
    holds for exactly its shares, a line held with no level kept, and one with no share and no
    stop."""
    if [(o.left, o.state in HELD) for o in stops] == [(shares, True)]:
        return ()
    levels = [
        (int(o.number), placing.Stop(shares, o.level, o.ref))
        for o in (*stops, *was)
        if o.level is not None and o.ref.removesuffix("-stop") in bought
    ]
    if not shares:
        return (None,) if stops else ()
    return (max(levels)[1],) if levels else (back,) if back and shares else ()
