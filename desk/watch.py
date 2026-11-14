"""watch - THE CRASH WATCH (EMG-01, EMG-03). Every five minutes, at every hour, whoever runs
the desk asks for one look. A look reads, in the one fast store, the newest five-minute bar of
every line it is given whose venue is trading (every line of the desk's, so every one it
holds, and the market's own with them), measures each fall as the three emergencies define
it (desk/emergency.py), and does at once what a fall that is one of them calls for:

- A CRASH: a halt is called (desk/halt.py), so the send path sends no buy on any line, and
  he is told. The watch lifts its own halt once the market has ended a day clear of a crash,
  read at that session's last bar and never within a day. He may lift it sooner, and then
  the watch calls no other that day.
- A BLACK SWAN: the same, with a halt that only he lifts. Read again that day at a later
  bar it is read twice (Look.cash), which is what the sale of every position waits for.
  That sale is not built (STP-07): nothing is sold, and he is told so both times.
- AN EMERGENCY, one line's: he is told. Nothing parks one line yet (the send path asks only
  for the halts on the whole desk), and he is told that too.

The halt's reason and the message are the fall in its own words, with what was done and
what was not: that is the record of why. Each message goes once, through the desk's one
voice, at any hour, under its day, its line and its level.

THE CLOCK. A bar is read once it has ended. Five minutes in which a line did not trade have
no bar, so a line's newest bar of the session is its price for as long as its venue is
heard from: a venue is last heard from when the newest bar of any of its lines ended, or at
its open. Past STALE of that, no line of the venue is read. The market must be heard from
itself. A line not read is said to be unread, with why, and is never taken for calm. A
market that is owed and cannot be read makes the watch BLIND: he is told, once a day, and
no halt is called, for a feed that stops is far commoner than a crash.

A look remembers nothing: what it did is on the halts' record and the delivery record, so a
look repeated does nothing twice, and one that failed is made good by the next. It is one of
the desk's steps, one process at a time; a store that is not there is an error raised."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from pathlib import Path

from desk import bars, emergency, halt, messenger, venues
from desk.bars import Five
from desk.emergency import Fall, Level, Unread
from desk.lines import YARDSTICK, Line
from desk.store import Bar
from desk.venues import Hours

BAR = timedelta(minutes=5)
#: A venue, or the market, not heard from for longer than this is not read: three rounds
#: missed and a fourth late. So a fall is seen within twenty-five minutes of its trade.
STALE = timedelta(minutes=20)
WATCH = "the crash watch"  #: who calls the watch's halts, and lifts its own
EARLY = "no bar of its own has ended this session"
DONE = {
    Level.EMERGENCY: (
        "NOT DONE: the desk cannot yet park one line, so its rules may still buy this one. "
        "Its stop rests at the broker as ever."
    ),
    Level.CRASH: (
        "DONE: a halt is in force, and no buy goes on any line. The watch lifts it once the "
        "market ends a day clear of a crash; you may lift it sooner."
    ),
    Level.BLACK_SWAN: (
        "DONE: a halt is in force that only you lift, and no buy goes on any line. NOT DONE: "
        "nothing is sold. The sale of every position is not built, and would wait for a "
        "second reading; the stops rest at the broker as ever."
    ),
}
TWICE = (
    "BLACK SWAN, READ TWICE: a later bar says so too. {} NOT DONE: nothing is sold, for the "
    "sale of every position is not built. The stops rest at the broker; the rest is yours."
)
BLIND = (
    "THE CRASH WATCH IS BLIND: it cannot read the market. {}. It has called no halt, and a "
    "crash now would not be seen. This is told once a day."
)


@dataclass(frozen=True)
class Look:
    """One look: every line given whose venue was trading, its fall read or why it was not."""

    at: datetime
    falls: tuple[Fall, ...]
    ended: Mapping[str, datetime]  #: by symbol, when the bar its fall was read at ended
    unread: Mapping[str, str]  #: by symbol, why no fall was read: that line is not calm
    cash: bool = False  #: a black swan read twice: what the sale of every position waits for

    @property
    def blind(self) -> str | None:
        """Why the market, owed, was not read. None when it was read, when no bar of its
        session could have ended yet, and when its venue is shut: then no market is owed."""
        why = self.unread.get(YARDSTICK.symbol)
        return None if why == EARLY else why


def _newest(hot: Path, line: Line, session: Hours, now: datetime) -> tuple[Five | None, datetime]:
    """The line's newest bar of the session to have ended by now, and when the line was last
    heard from: as that bar ended, or with none at the open."""
    until = min(now, session.auction)
    try:
        found = bars.five(hot, line, session.open, until)
    except LookupError:  #: the store never held a bar of the line: it has none
        found = ()
    ended = [bar for bar in found if bar.start + BAR <= until]
    return (ended[-1], ended[-1].start + BAR) if ended else (None, session.open)


def _measure(
    line: Line, daily: Sequence[Bar], bar: Five | None, heard: datetime, at: datetime
) -> Fall | None:
    """The line's fall at its newest bar, as of a moment of its session; None while it has no
    bar and its venue is heard from. Unread once the line (the market), or its venue (any
    other), was last heard from more than STALE before."""
    if at - heard > STALE:
        whom = line.symbol if line == YARDSTICK else f"any line of {line.venue}"
        raise Unread(f"{line.symbol}: nothing heard of {whom} since {heard:%H:%M} UTC")
    return None if bar is None else emergency.measure(line, daily, bar)


def read(hot: Path, daily: Mapping[Line, Sequence[Bar]], now: datetime) -> Look:
    """WHAT ONE LOOK READS, and nothing done about it: the fall of each line given whose
    venue is trading at now, at its newest bar in the fast store at hot, or why it is unread.
    daily gives each line's daily bars from the price store, the market's among them."""
    if now.utcoffset() != timedelta(0) or YARDSTICK not in daily:
        raise ValueError(
            f"no look at {now:%Y-%m-%d %H:%M}: it needs a moment in UTC, and the market's "
            f"own bars ({YARDSTICK.symbol}) among the lines it is given"
        )
    trading = {line: hours for line in daily if (hours := venues.open_at(line.venue, now))}
    newest = {line: _newest(hot, line, hours, now) for line, hours in trading.items()}
    heard = {
        venue: max(end for line, (_, end) in newest.items() if line.venue == venue)
        for venue in {line.venue for line in trading}
    }
    falls, ended, unread = [], {}, {}
    for line, (bar, end) in newest.items():
        last, at = end if line == YARDSTICK else heard[line.venue], min(now, trading[line].close)
        try:
            fall = _measure(line, daily[line], bar, last, at)
        except Unread as why:
            unread[line.symbol] = str(why)
            continue
        if fall is None:
            unread[line.symbol] = EARLY
        else:
            falls.append(fall)
            ended[line.symbol] = end
    return Look(now, tuple(falls), ended, unread)


def _lift(root: Path, hot: Path, market: Sequence[Bar], now: datetime) -> None:
    """THE WATCH LIFTS ITS OWN crash halt once the market has ended a day clear of a crash:
    the last of its sessions to have ended by now, from the halt's day on, read at its last
    bar as any look reads it. A reading within a day lifts nothing, nor does an end that is
    unread; and a halt that is his alone, a black swan's, is never the watch's to lift."""
    venue = YARDSTICK.venue
    for called in halt.in_force(root):
        days = venues.sessions(venue, called.at.date(), now.date())
        over = [day for day in days if venues.hours(venue, day).auction < now]
        if called.by != WATCH or called.his or not over:
            continue
        session = venues.hours(venue, over[-1])
        try:
            fall = _measure(
                YARDSTICK, market, *_newest(hot, YARDSTICK, session, now), session.close
            )
        except Unread:  #: a day's end that cannot be read lifts nothing
            continue
        if fall is not None and fall.level is None:
            why = f"{WATCH}: the market ended {fall.on} clear of a crash. {fall.words()}"
            halt.lift(root, called, now, why, by=WATCH)


def _call(root: Path, fall: Fall, his: bool, ended: datetime, now: datetime) -> bool:
    """THE MARKET'S FALL HALTS ALL BUYING: a halt of the watch's is called, his alone to lift
    for a black swan, unless one such is in force, or was called on the fall's day: a halt he
    lifted stands lifted that day. Given back: whether a black swan is now read twice, at a
    bar that ended after its halt, still in force, was called that day."""
    mine = [h for h in halt.kept(root) if h.by == WATCH and h.his == his]
    today = [h for h in mine if h.at.date() == fall.on]
    if not today and all(h.lifted for h in mine):
        halt.call(root, now, fall.words(), by=WATCH, his=his)
    return his and any(h.lifted is None and h.at < ended for h in today)


def look(
    root: Path,
    hot: Path,
    daily: Mapping[Line, Sequence[Bar]],
    now: datetime,
    post: messenger.Post,
) -> Look:
    """ONE LOOK, AND WHAT IT CALLS FOR, DONE AT ONCE: the desk's records at root, the fast
    store at hot, each line's daily bars, the moment in UTC and the door to his phone. The
    halt is called before he is told, so a door that is down stops no halt; the message it
    did not take is an error raised, and goes at the next look."""
    seen, cash = read(hot, daily, now), False
    _lift(root, hot, daily[YARDSTICK], now)
    grave = [(fall, level) for fall in seen.falls if (level := fall.level) is not None]
    for fall, level in sorted(grave, key=lambda found: not found[0].market):
        name, words = f"watch {fall.on} {fall.line.symbol} {level.name}", fall.words()
        ended, his = seen.ended[fall.line.symbol], level is Level.BLACK_SWAN
        twice = fall.market and _call(root, fall, his, ended, now)
        messenger.send(root, now, name, f"{words} {DONE[level]}", post)
        if twice:
            messenger.send(root, now, f"{name} twice", TWICE.format(words), post)
        cash = cash or twice
    if seen.blind:
        messenger.send(root, now, f"watch {now.date()} blind", BLIND.format(seen.blind), post)
    return replace(seen, cash=cash)
