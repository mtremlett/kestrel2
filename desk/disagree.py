"""disagree - WHEN THE BROKER'S WORD, FILLS AND ACCOUNT DO NOT AGREE after an order has gone
(R-PAPER-11). The order is not sent again (the broker has it, and is asked first), buying
stops by a halt only he lifts, and he is told at once, naming the order and what disagrees.
Sales and the resting stops go on, so nothing held is left unprotected."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from desk import halt
from desk.broker import Broker, Report
from desk.orders import Order, Sale

SENDER = "the send path"  #: who calls the halt
Tell = Callable[[str, str], None]  #: the door to his phone: a message's name, then its words


def halted(
    root: Path,
    broker: Broker,
    order: Order | Sale,
    error: Exception,
    tell: Tell | None,
) -> Report | None:
    """None unless the error is the paper door's word that these do not agree (Unprotected).
    Otherwise buying is halted (halt.call), he is told once, and the broker's own report of the
    order is given back; the order, which has gone, is never judged unsent."""
    from desk import placing  # noqa: PLC0415 - placing reaches book through paper: a cycle at load

    if not isinstance(error, placing.Unprotected):
        return None
    words = f"{order.order_id}: the broker's word, fills and account do not agree: {error}"
    halt.call(root, datetime.now(UTC), f"{words}; no buy goes until he lifts this", by=SENDER)
    if tell is not None:
        tell(f"disagree {order.order_id}", f"{words}. Buying is halted; sales and stops go on.")
    return broker.report(order.order_id) or Report(order.order_id, (), words)
