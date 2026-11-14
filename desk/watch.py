"""watch - THE CRASH WATCH (EMG-01, EMG-03). Every five minutes, at every hour, whoever runs
the desk asks for one look. A look reads, in the one fast store, the newest five-minute bar of
every line it is given whose venue is trading (every line of the desk's, so every one it
holds, and the market's own with them), measures each fall as the three emergencies define
it (desk/emergency.py), and does at once what a fall that is one of them calls for:

- A CRASH: a halt is called (desk/halt.py), so the send path sends no buy on any line. The
  watch lifts its own halt once the market has ended a day clear of a crash: read at that
  session's very last bar, once its closing auction is over, never within a day; the halt
  ends with that day. He may lift it sooner, and then the watch calls no other, and says no
  more of it, on the day he does.
- A BLACK SWAN: the same, with a halt that only he lifts. Read again at a later bar while
  that halt stands, it is read twice (Look.cash), which is what the sale of every position
  waits for. That sale is not built (STP-07): nothing is sold, and he is told so both times.
- AN EMERGENCY, one line's: he is told. Nothing parks one line yet (the send path asks only
  for the halts on the whole desk), and he is told that too.

WHAT HE IS TOLD, through the desk's one voice, at any hour, each message once under its
name: every halt of the watch's that stands, in the fall's own words with what was done and
what was not, and again on each later day the market still reads so; the lift; each line's
emergency, once a day. A standing halt is owed its message whatever the market reads now,
so one his phone's door did not take, or a desk that died before telling, is made good by
the next look. The halt's reason is the fall in its own words: that is the record of why.

THE CLOCK. A bar is read once it has ended. Five minutes in which a line did not trade have
no bar, so a line's newest bar of the session is its price for as long as its venue is
heard from: a venue is last heard from when the newest bar of any of its lines ended, or at
its open. Past STALE of that, no line of the venue is read. The market must be heard from
itself. A line not read is said to be unread, with why, and is never taken for calm. A
market that is owed and cannot be read makes the watch BLIND: he is told, once in each hour
it lasts, and no halt is called, for a feed that stops is far commoner than a crash.

A look remembers nothing: what it did is on the halts' record and the delivery record, so a
look repeated does nothing twice. It is one of the desk's steps, one process at a time; a
store that is not there is an error raised."""

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
        "A holding's stop rests at the broker as ever."
    ),
    Level.CRASH: (
        "DONE: a halt is in force, and no buy goes on any line. The watch lifts it once the "
        "market ends a day clear of a crash, and tells you."
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
    "crash now would not be seen. This is told once in each hour it lasts."
)


@dataclass(frozen=True)
class Look:
    """One look: every line given whose venue was trading, its fall read or why it was not."""

    at: datetime
    falls: tuple[Fall, ...]
    ended: Mapping[Line, datetime]  #: when the bar each fall was read at ended
    unread: Mapping[Line, str]  #: why no fall was read of a line: that line is not calm
    cash: bool = False  #: a black swan read twice: what the sale of every position waits for

    @property
    def blind(self) -> str | None:
        """Why the market, owed, was not read. None when it was read, when no bar of its
        session could have ended yet, and when its venue is shut: then no market is owed."""
        why = self.unread.get(YARDSTICK)
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
    line: Line,
    daily: Sequence[Bar],
    bar: Five | None,
    heard: datetime,
    at: datetime,
    late: timedelta = STALE,
) -> Fall | None:
    """The line's fall at its newest bar, as of a moment of its session; None while it has no
    bar and its venue is heard from. Unread once the line (the market), or its venue (any
    other), was last heard from more than late before."""
    if at - heard > late:
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
            unread[line] = str(why)
            continue
        if fall is None:
            unread[line] = EARLY
        else:
            falls.append(fall)
            ended[line] = end
    return Look(now, tuple(falls), ended, unread)


def _lift(root: Path, hot: Path, market: Sequence[Bar], now: datetime) -> list[tuple[str, str]]:
    """THE WATCH LIFTS ITS OWN crash halt once the market has ended a day clear of a crash:
    the last of its sessions to be over by now, its closing auction too, from the halt's day
    on, read at that session's very last bar. A reading within a day lifts nothing, nor does
    an end whose last bar is not in the store; and a halt that is his alone, a black swan's,
    is never the watch's to lift. The halt is lifted as of that session's end, whenever the
    look comes: the day after it is a day with no halt, and a lift dated today is only ever
    his. Given back: the message he is owed for each lift, under its name."""
    venue, told = YARDSTICK.venue, []
    for called in halt.in_force(root):
        days = venues.sessions(venue, called.at.date(), now.date())
        over = [day for day in days if venues.hours(venue, day).auction < now]
        if called.by != WATCH or called.his or not over:
            continue
        session = venues.hours(venue, over[-1])
        newest = _newest(hot, YARDSTICK, session, now)
        try:
            fall = _measure(YARDSTICK, market, *newest, session.close, timedelta(0))
        except Unread:  #: a day's end that cannot be read lifts nothing
            continue
        if fall is not None and fall.level is None:
            why = f"{WATCH}: the market ended {fall.on} clear of a crash. {fall.words()}"
            ended = halt.lift(root, called, session.auction, why, by=WATCH)
            told.append((f"watch {fall.on} {YARDSTICK.symbol} lifted", ended.words(fall.on)))
    return told


def _call(root: Path, fall: Fall, his: bool, ended: datetime, now: datetime) -> bool:
    """THE MARKET'S FALL HALTS ALL BUYING: a halt of the watch's is called, his alone to lift
    for a black swan, unless one as grave is in force, or was lifted on the fall's day: that
    is his word, and it stands for the day. A black swan is a crash too, so its halt, or his
    word on it, stands for a crash; a crash's does not for a black swan. Given back: whether
    a black swan is now read twice, at a bar that ended after its halt, still in force, was
    called."""
    mine = [h for h in halt.kept(root) if h.by == WATCH and (h.his or not his)]
    twice = his and any(h.lifted is None and h.at < ended for h in mine)
    if not any(h.lifted is None or h.lifted[0].date() == fall.on for h in mine):
        halt.call(root, now, fall.words(), by=WATCH, his=his)
    return twice


def _said(fall: Fall, level: Level) -> tuple[str, str]:
    """A fall's message, under its day, its line and its level: the fall in its own words,
    then what was done about it and what was not."""
    return f"watch {fall.on} {fall.line.symbol} {level.name}", f"{fall.words()} {DONE[level]}"


def look(
    root: Path,
    hot: Path,
    daily: Mapping[Line, Sequence[Bar]],
    now: datetime,
    post: messenger.Post,
) -> Look:
    """ONE LOOK, AND WHAT IT CALLS FOR, DONE AT ONCE: the desk's records at root, the fast
    store at hot, each line's daily bars, the moment in UTC and the door to his phone. The
    halts are lifted and called before he is told anything, so a door that is down stops no
    halt; a message it did not take is an error raised, and what a standing halt is owed
    goes at the next look."""
    seen, market = read(hot, daily, now), YARDSTICK.symbol
    owed = _lift(root, hot, daily[YARDSTICK], now)
    grave = {fall.line: (fall, level) for fall in seen.falls if (level := fall.level) is not None}
    fallen = grave.pop(YARDSTICK, None)
    cash = fallen is not None and _call(
        root, fallen[0], fallen[1] is Level.BLACK_SWAN, seen.ended[YARDSTICK], now
    )
    for called in halt.in_force(root):
        level = Level.BLACK_SWAN if called.his else Level.CRASH
        if called.by != WATCH:
            continue
        name = f"watch {called.at.date()} {market} {level.name}"  #: as it was called
        owed.append((name, f"{called.why} {DONE[level]}"))
        if fallen is not None and fallen[1] is level:  #: and as it reads on a later day
            owed.append(_said(*fallen))
    if fallen is not None and cash:
        owed.append((f"{_said(*fallen)[0]} twice", TWICE.format(fallen[0].words())))
    owed += [_said(fall, level) for fall, level in grave.values()]
    if seen.blind:
        owed.append((f"watch {now:%Y-%m-%d %H}h blind", BLIND.format(seen.blind)))
    for name, words in owed:
        messenger.send(root, now, name, words, post)
    return replace(seen, cash=cash)
