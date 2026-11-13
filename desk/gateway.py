"""gateway - THE GATEWAY KNOWN BEFORE ANY ORDER. IB Gateway on his PC keeps a week of its
own. This module knows that week and answers two questions about it. It sends nothing to
anyone and nothing calls it yet: whoever sends an order is to ask `known` first, and
whoever writes to him is to carry its lines (docs/STATUS.md).

Every day at 03:00 on a UK clock the gateway restarts itself and is back within seconds,
logged in on the week's own token. `known` waits that out: in the twenty minutes around it
the gateway is restarting whatever it would answer, and `known` does not dial it.

Once a week, after the broker's weekend reset, the next login needs his password. That
login is his alone: the desk keeps no password, types none and starts no program.
`reminder` gives the line for him, due on Sunday from 08:00 on a UK clock: the first hour
he is awake in which a login lasts the whole week.

At any other time a gateway from which nothing comes back is his to look at, and `known`
gives his line, whatever the hour (his ruling, docs/DECISIONS.md). One that is there but
does not say it is ready (the client id taken; the broker's link lost, when the gateway
says so before it greets) is unwell: no order, and not known to be his. One the desk
cannot trust (another version, an account that is not a paper one), and any other fault of
the machine's, is raised."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta, timezone
from enum import Enum

from desk import paper
from desk.venues import CLOCKS, _sunday

#: The gateway's own daily restart, on a UK clock (its setting on his PC), and the time
#: `known` gives it either side: an order sent into it could be lost, and the runner's own
#: watch calls fifteen minutes of silence longer than a restart.
FROM, RESTART, UNTIL = time(2, 55), time(3), time(3, 15)
#: The weekly login, on a UK clock: its day, the hour by which the broker's weekend reset is
#: over (01:00 in New York: 05:00 or 06:00 here), and the hour he wakes (docs/DECISIONS.md).
SUNDAY, RESET, WAKES = 6, time(6), time(8)
Knock = Callable[[], object]  #: what asks the gateway whether it is ready; it raises if not

ANSWERED = "the paper Gateway answered the desk's knock"
WAITING = (
    f"the paper Gateway restarts itself at {RESTART:%H:%M} UK each day: from {FROM:%H:%M} "
    f"until {UNTIL:%H:%M} it is not ready, and the desk's knock is not made"
)
UNWELL = "the paper Gateway is there but did not say it is ready: {}"
SILENT = (
    f"The paper Gateway does not answer: {{}}. This is outside the {FROM:%H:%M} to "
    f"{UNTIL:%H:%M} the desk allows for its daily restart. Please look at the PC: if the "
    "Gateway is showing its login, that login is yours (the desk keeps no password)."
)
WEEKLY = (
    "Sunday: the paper Gateway's weekly login is yours today. After its weekend reset the "
    "broker asks for the password again; the desk keeps no password and will not try. "
    "Please close the Gateway on the PC and log in again today, even if it looks logged in; "
    f"if you have since {RESET:%H:%M} this morning, it is done. Left undone, it may not "
    f"come back from its {RESTART:%H:%M} restart tonight."
)


class State(Enum):
    READY = "ready"  #: it greeted the desk's knock, clear of its restart: all that is known
    RESTARTING = "restarting"  #: its own daily restart: the desk waits, nobody need be told
    UNWELL = "unwell"  #: there, but it did not say it is ready: no order; not known to be his
    HIS = "his"  #: nothing came back, outside its restart's time: the operator's to look at


@dataclass(frozen=True)
class Known:
    """What the desk knows of the gateway at one moment. It is true only when ready, so no
    way of asking reads a gateway that is not ready as one that is."""

    state: State
    words: str  #: the same in plain words; when it is his, the line for him

    @property
    def ready(self) -> bool:
        """Asked before an order: any other state is a reason not to send. Ready is the
        gateway's greeting and no more; the day's own readings must still come back whole."""
        return self.state is State.READY

    def __bool__(self) -> bool:
        return self.ready


@dataclass(frozen=True)
class Reminder:
    """His weekly login's reminder: one is owed for each due, however often it is asked for."""

    due: datetime  #: Sunday at the hour he wakes, UTC: the reminder's own name
    line: str


def _uk(moment: datetime) -> datetime:
    """A moment on a UK clock, by the one calendar's rule for London's. The clocks change at
    01:00 UTC on their two Sundays; taken here from that whole day, which moves neither the
    restart nor the hour he wakes."""
    if moment.tzinfo is None:
        raise ValueError(f"{moment} has no time zone: the desk cannot place it on a UK clock")
    clock, day = CLOCKS["LSE"], moment.astimezone(UTC).date()
    forward, back = (_sunday(date(day.year, month, n)) for month, n in clock.summer)
    return moment.astimezone(timezone(timedelta(hours=clock.winter + (forward <= day < back))))


def knock() -> None:
    """Knock on the paper door and leave: the gateway must greet the desk's own client in
    the desk's one version, be ready, and name paper accounts only. Nothing is asked."""
    paper.dial(paper.start)


def known(now: datetime, ask: Knock = knock) -> Known:
    """The gateway now, asked before any order: ready only if it greets the desk's knock
    outside its own restart, in which the knock is not made at all. Otherwise, when nothing
    came back (its port closed, or silence), it is his and the words are his line; when it
    said anything else, or broke off, it is unwell and the words say what it said."""
    if FROM <= _uk(now).time() < UNTIL:
        return Known(State.RESTARTING, WAITING)
    try:
        ask()
    except ConnectionRefusedError:
        return Known(State.HIS, SILENT.format("its port is closed"))
    except TimeoutError:
        return Known(State.HIS, SILENT.format(f"it said nothing for {paper.SECONDS} seconds"))
    except ConnectionError as said:
        return Known(State.UNWELL, UNWELL.format(said))
    return Known(State.READY, ANSWERED)


def reminder(now: datetime) -> Reminder | None:
    """His weekly login's reminder, due all of Sunday on a UK clock from the hour he wakes;
    none at any other time. It is due whether or not the gateway answers: the desk cannot
    see whether he has logged in since the weekend's reset, and a gateway still answering
    on last week's token may not come back from its next restart."""
    local = _uk(now)
    if local.weekday() != SUNDAY or local.time() < WAKES:
        return None
    return Reminder(datetime.combine(local.date(), WAKES, local.tzinfo).astimezone(UTC), WEEKLY)
