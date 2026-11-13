"""gateway - THE GATEWAY KNOWN BEFORE ANY ORDER. IB Gateway on his PC keeps a week of its
own. This module knows that week and answers two questions about it; it sends nothing to
anyone: whoever sends an order asks `known` first, and the messenger carries the lines.

Every day at 03:00 on a UK clock the gateway restarts itself and is back within seconds,
logged in on the week's own token. `known` waits that out: in the twenty minutes around it
the gateway is restarting whatever it would answer, and is not even dialled.

Once a week, after the broker's weekend reset, the next login needs his password. That
login is his alone: the desk keeps no password, types none and starts no program.
`reminder` gives the line for him, due on Sunday from 08:00 on a UK clock: the first hour
he is awake in which a login lasts the whole week.

At any other time a gateway from which nothing comes back is his to look at, and `known`
gives his line, at any hour (his ruling, docs/DECISIONS.md). One that is there but does not
say it is ready (the client id taken, the broker's link lost) is unwell: no order, and no
login of his. One the desk cannot trust (another version, an account that is not a paper
one) is a fault, and is raised as one."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta, timezone
from enum import Enum

from desk import paper
from desk.venues import CLOCKS, _sunday

#: The gateway's own daily restart, on a UK clock (its setting on his PC), and the time the
#: desk gives it either side: an order sent into it could be lost, and the runner's own
#: watch calls fifteen minutes of silence longer than a restart.
FROM, RESTART, UNTIL = time(2, 55), time(3), time(3, 15)
SUNDAY, WAKES = 6, time(8)  #: the weekly login's day, and the hour he wakes (docs/DECISIONS.md)
Knock = Callable[[], object]  #: what asks the gateway whether it is ready: an OSError if not

ANSWERED = "the paper Gateway answered the desk's knock"
WAITING = (
    f"the paper Gateway restarts itself at {RESTART:%H:%M} UK each day: until {UNTIL:%H:%M} "
    "the desk does not dial it and sends nothing"
)
UNWELL = "the paper Gateway is there but did not say it is ready: {}"
SILENT = (
    f"The paper Gateway does not answer, and this is more than its {RESTART:%H:%M} restart, "
    f"which the desk waits out until {UNTIL:%H:%M}. Please look at the PC: if the Gateway "
    "is showing its login, that login is yours (the desk keeps no password). The desk saw: {}"
)
WEEKLY = (
    "Sunday: the paper Gateway's weekly login is yours today. Once a week, after its weekend "
    "reset, the broker asks for the password again; the desk keeps no password and will not "
    "try. Please close the Gateway on the PC and log in again today, even if it still looks "
    "logged in. If you have done so since 06:00 this morning, it is done. Left undone, the "
    f"Gateway may not come back from its {RESTART:%H:%M} restart tonight."
)


class State(Enum):
    READY = "ready"  #: it answered the desk's knock, clear of its restart: all that is known
    RESTARTING = "restarting"  #: its own daily restart: the desk waits, nobody need be told
    UNWELL = "unwell"  #: there, but it did not say it is ready: no order, and no login of his
    HIS = "his"  #: nothing came back, and it is no restart: the operator's to look at


@dataclass(frozen=True)
class Known:
    """What the desk knows of the gateway at one moment."""

    state: State
    words: str  #: the same in plain words; when it is his, the line for him

    @property
    def ready(self) -> bool:
        """The one question before an order. Every other state is a reason not to send."""
        return self.state is State.READY


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
    """The gateway now, asked before any order: ready only if it answers the desk's knock
    outside its own restart, in which it is not dialled at all. Otherwise, when nothing came
    back (the port closed, or silence), it is his and the words are his line; when it
    answered anything else, or broke off, it is unwell and the words say what it said."""
    if FROM <= _uk(now).time() < UNTIL:
        return Known(State.RESTARTING, WAITING)
    try:
        ask()
    except (ConnectionRefusedError, TimeoutError) as nothing:
        return Known(State.HIS, SILENT.format(nothing))
    except OSError as said:
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
