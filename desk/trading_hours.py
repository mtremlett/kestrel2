"""trading_hours - WHEN A REAL MARKET COULD FILL AN ORDER, regular session and extended hours
alike: a rehearsal's order must never meet a fill (the 22:04 rehearsal buy of MSTR filled
after-hours, R-RUNNER-415). The one calendar is desk.venues; the margins are kept here."""

from __future__ import annotations

from datetime import datetime, timedelta

from desk import venues
from desk.running import VENUES

RUN = timedelta(minutes=30)  #: the rehearsal's longest run, as the runner allows it
HOUR = timedelta(minutes=60)
#: How long before the open and after the uncrossing a venue's orders can fill: New York's
#: pre-market (04:00 New York) and after-hours (to 20:00 New York); London's auctions only.
BEFORE = {"LSE": RUN + HOUR, "US": RUN + timedelta(hours=5, minutes=30)}
AFTER = {"LSE": timedelta(minutes=30), "US": timedelta(hours=4)}


def trading(now: datetime) -> list[str]:
    """The markets whose orders could fill at now: inside the window before the open, the
    session, or the hours after its uncrossing."""
    return [
        VENUES[venue]
        for venue in VENUES
        for on in venues.sessions(venue, now.date(), now.date())
        if (hours := venues.hours(venue, on)).open < now + BEFORE[venue]
        and hours.auction + AFTER[venue] >= now
    ]
