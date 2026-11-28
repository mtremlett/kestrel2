"""incident unreachable: SimCity's scenario for one real night (see `git log`, DECISIONS)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from desk import conformance, paper, venues

if TYPE_CHECKING:
    from desk.simcity import _Life

SHUT = (
    "a closed Gateway port outside its restart: the run is not begun, nothing sent, his to look at"
)


def unreachable(life: _Life, on: date) -> None:
    """The paper Gateway's port is closed in the market's hours, outside its 03:00 restart (18
    November, conformance-us). The run must be refused, nothing sent, in the words that tell
    him the Gateway is his to look at; it asks the Gateway once and the desk goes on."""
    market, asked = "us", []
    if venues.sessions(conformance.MARKETS[market], on, on) != (on,):
        life.live(on)  #: the venue keeps a holiday: no run is due
        return
    now = venues.hours(conformance.MARKETS[market], on).open + timedelta(hours=2)

    def refused(talk: object, *_seconds: float) -> None:
        asked.append(talk)
        raise ConnectionRefusedError(f"port {paper.PORT} is closed")

    dial, paper.dial = paper.dial, refused  # type: ignore[assignment]
    try:
        well, words = conformance.trade(life.desk, market, lambda: now)
    finally:
        paper.dial = dial
    head = f"CONFORMANCE {market} NOT BEGUN, nothing sent: The paper Gateway does not answer: "
    life.promise(
        SHUT, not well and words.startswith(head + "its port is closed") and len(asked) == 1
    )
    life.live(on)
