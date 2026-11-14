"""watch - THE CRASH WATCH (EMG-01, EMG-03). Every five minutes, at every hour, whoever runs
the desk asks for one look. A look reads, in the one fast store, the newest five-minute bar of
every line it is given whose venue is trading (every line of the desk's, so every one it
holds, and the market's own with them) and measures each fall as the three emergencies
define it (desk/emergency.py). The market is read twice over: as it trades, and as its last
session ended, at that session's very last bar once its closing auction is over; so a fall
the desk slept through, or one made at the close, is still read. Then, at once:

- A CRASH, at either reading: a halt is called (desk/halt.py), and the send path sends no
  buy on any line. Only an end lifts it: the watch lifts its own halt once the market has
  ended a day clear of a crash, as of that day's end. An end that cannot be read does
  neither, and he is told so, once.
- A BLACK SWAN: the same, with a halt that only he lifts. Read at the market's two newest
  bars while that halt stands, it is read twice (Look.cash), which is what the sale of every
  position waits for. That sale is not built (STP-07): nothing is sold, and he is told so.
- AN EMERGENCY, one line's: he is told. Nothing parks one line yet (the send path asks only
  for the halts on the whole desk), and he is told that too.

HIS WORD. A halt of the watch's that he lifts stays lifted: the watch calls no other as
grave or less until the market has ended a day clear, and tells him each day it reads so
and buys on his word. A black swan is a crash too; a crash's lift is no word on a black swan.

WHAT HE IS TOLD, through the desk's one voice, at any hour, each message once under its
name: each halt of the watch's while it stands, in the fall's own words with what was done
and what was not; its lift, with every halt still in force; each line's emergency, once a
day. A standing halt is owed its message whatever the market reads now, so one his phone's
door did not take is made good by the next look. The halt's reason is the record of why.

THE CLOCK. A bar is read once it has ended. Five minutes in which a line did not trade have
no bar, so a line's newest bar of the session is its price for as long as its venue is heard
from: when the newest bar of any of its lines ended, or at its open. Past STALE of that no
line of the venue is read, and the market must be heard from itself. A line not read is said
to be unread, with why, never taken for calm. A market that is trading and cannot be read
makes the watch BLIND: he is told, once in each hour it lasts, and no halt is called for
that, for a feed that stops is far commoner than a crash.

A look remembers nothing: what it did is on the halts' record and the delivery record. It is
one of the desk's steps, one process at a time; a store that is not there is an error."""

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
BACK = timedelta(days=10)  #: the market's last session is looked for no further back
WATCH = "the crash watch"  #: who calls the watch's halts, and lifts its own
EARLY = "no bar of its own has ended this session"
PARK = (
    "NOT DONE: the desk cannot yet park one line, so its rules may still buy this one. A "
    "holding's stop rests at the broker as ever."
)
DONE = {
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
    "BLACK SWAN, READ TWICE: the market's two newest bars both say so. {} NOT DONE: nothing "
    "is sold, for the sale of every position is not built. The stops rest at the broker; the "
    "rest is yours."
)
WORD = (
    "{} NOT DONE: no halt is called, and the desk buys, on your word: you lifted the watch's "
    "halt at {:%Y-%m-%d %H:%M} UTC, and the market has not ended a day clear since."
)
BLIND = (
    "THE CRASH WATCH IS BLIND: it cannot read the market. {}. No halt is called for that, "
    "and a crash now would not be seen. This is told once in each hour it lasts."
)
UNENDED = (
    "THE CRASH WATCH CANNOT READ HOW THE MARKET ENDED {}: its last five-minute bar is not in "
    "the store, or its daily closes are not whole. If it ended in a crash no halt is called "
    "for that, and no halt of the watch's is lifted by it. This is told once."
)
Owed = list[tuple[str, str]]  #: messages he is owed: each one's name, and its words


@dataclass(frozen=True)
class Look:
    """One look: every line given whose venue was trading, its fall read or why it was not."""

    at: datetime
    falls: tuple[Fall, ...]
    unread: Mapping[Line, str]  #: why no fall was read of a line: that line is not calm
    #: A black swan read twice, at the market's two newest bars, while its halt stands: what
    #: the sale of every position waits for.
    cash: bool = False

    @property
    def blind(self) -> str | None:
        """Why the market, trading, was not read. None when it was read, when no bar of its
        session could have ended yet, and when its venue is shut."""
        why = self.unread.get(YARDSTICK)
        return None if why == EARLY else why


def _ended(hot: Path, line: Line, session: Hours, now: datetime) -> list[Five]:
    """The line's bars of the session that had ended by now, oldest first."""
    until = min(now, session.auction)
    try:
        found = bars.five(hot, line, session.open, until)
    except LookupError:  #: the store never held a bar of the line: it has none
        return []
    return [bar for bar in found if bar.start + BAR <= until]


def _swan(market: Sequence[Bar], bar: Five) -> bool:
    """Whether the market reads a black swan at a bar; one that cannot be read is none."""
    try:
        return emergency.measure(YARDSTICK, market, bar).level is Level.BLACK_SWAN
    except Unread:  #: a second reading that is not one confirms nothing
        return False


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
    ended = {line: _ended(hot, line, hours, now) for line, hours in trading.items()}
    heard = {
        line: got[-1].start + BAR if got else trading[line].open for line, got in ended.items()
    }
    falls, unread, twice = [], {}, False
    for line, got in ended.items():
        own, venue = (
            line == YARDSTICK,
            [heard[other] for other in heard if other.venue == line.venue],
        )
        last = heard[line] if own else max(venue)
        if min(now, trading[line].close) - last > STALE:
            whom = line.symbol if own else f"any line of {line.venue}"
            unread[line] = f"{line.symbol}: nothing heard of {whom} since {last:%H:%M} UTC"
        elif not got:
            unread[line] = EARLY
        else:
            try:
                falls.append(emergency.measure(line, daily[line], got[-1]))
            except Unread as why:
                unread[line] = str(why)
        if own and len(got) > 1:
            twice = all(_swan(daily[line], bar) for bar in got[-2:])
    return Look(now, tuple(falls), unread, twice and YARDSTICK not in unread)


def _over(since: datetime, now: datetime) -> list[Hours]:
    """The market's sessions whose closing auctions fell from since up to now, oldest first."""
    venue = YARDSTICK.venue
    days = (venues.hours(venue, day) for day in venues.sessions(venue, since.date(), now.date()))
    return [hours for hours in days if since <= hours.auction < now]


def _end(hot: Path, market: Sequence[Bar], session: Hours) -> Fall | None:
    """The market's fall as a session of its own ended: at its very last bar, the one that
    ended at the close. None when that bar is not in the store or cannot be read: an end
    unread, which is neither a crash nor clear of one."""
    got = _ended(hot, YARDSTICK, session, session.auction)
    if not got or got[-1].start + BAR != session.close:
        return None
    try:
        return emergency.measure(YARDSTICK, market, got[-1])
    except Unread:  #: said above: neither a crash nor clear
        return None


def _clear(hot: Path, market: Sequence[Bar], session: Hours) -> bool:
    """Whether the market ended the session clear of a crash, as read: unread is not clear."""
    end = _end(hot, market, session)
    return end is not None and end.level is None


def _lift(root: Path, end: Fall, session: Hours) -> Owed:
    """THE WATCH LIFTS ITS OWN crash halts, called by the end of a session that ended clear
    of a crash, as of that end, whenever the look comes: the day after is a day with no
    halt. A halt that is his alone, a black swan's, is never the watch's to lift. Given
    back: the lift's message, which says every halt still in force too."""
    told: Owed = []
    for called in halt.in_force(root):
        if called.by == WATCH and not called.his and called.at <= session.auction:
            why = f"{WATCH}: the market ended {end.on} clear of a crash. {end.words()}"
            halt.lift(root, called, session.auction, why, by=WATCH)
            told.append((f"watch {called.at:%Y-%m-%d %H:%M} lifted", str(halt.said(root, end.on))))
    return told


def _call(root: Path, hot: Path, market: Sequence[Bar], fall: Fall, now: datetime) -> Owed:
    """THE MARKET'S FALL HALTS ALL BUYING: a halt of the watch's is called, his alone to lift
    for a black swan, unless one as grave stands, or his word does: the last such halt was
    lifted, and the market has not ended a day clear since. The watch's own lift is made as
    of a clear end, so it is never his word. Given back: what he is owed if no halt is
    called on his word, once for the fall's day."""
    his = fall.level is Level.BLACK_SWAN
    mine = [h for h in halt.kept(root) if h.by == WATCH and (h.his or not his)]
    lifts = [h.lifted[0] for h in mine if h.lifted is not None]
    if len(lifts) < len(mine):
        return []
    if lifts and not any(_clear(hot, market, session) for session in _over(max(lifts), now)):
        name = f"watch {fall.on} {YARDSTICK.symbol} on his word"
        return [(name, WORD.format(fall.words(), max(lifts)))]
    halt.call(root, now, fall.words(), by=WATCH, his=his)
    return []


def _halts(root: Path, hot: Path, market: Sequence[Bar], live: Fall | None, now: datetime) -> Owed:
    """THE MARKET'S HALTS, PUT RIGHT: read as its last session ended, and as it trades now
    (live, when it was read). A clear end lifts, an end unread is said, and a crash or a
    black swan at either reading calls. Given back: what he is owed for what was done."""
    owed: Owed = []
    last = _over(now - BACK, now)[-1:]
    end = _end(hot, market, last[0]) if last else None
    if end is not None and end.level is None:
        owed += _lift(root, end, last[0])
    if last and end is None and now - last[0].auction > STALE:
        day = last[0].close.date()
        owed.append((f"watch {day} end unread", UNENDED.format(day)))
    for fall in (end, live):
        if fall is not None and fall.level is not None:
            owed += _call(root, hot, market, fall, now)
    return owed


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
    halt; a message it did not take is an error raised."""
    seen = read(hot, daily, now)
    live = next((fall for fall in seen.falls if fall.market), None)
    owed = _halts(root, hot, daily[YARDSTICK], live, now)
    standing = [called for called in halt.in_force(root) if called.by == WATCH]
    for called in standing:
        level = Level.BLACK_SWAN if called.his else Level.CRASH
        name = f"watch {called.at:%Y-%m-%d %H:%M} {level.name}"
        owed.append((name, f"{called.why} {DONE[level]}"))
    cash = seen.cash and any(called.his for called in standing)
    if cash and live is not None:
        owed.append((f"watch {live.on} BLACK_SWAN twice", TWICE.format(live.words())))
    owed += [
        (f"watch {fall.on} {fall.line.symbol} EMERGENCY", f"{fall.words()} {PARK}")
        for fall in seen.falls
        if not fall.market and fall.level is not None
    ]
    if seen.blind:
        owed.append((f"watch {now:%Y-%m-%d %H}h blind", BLIND.format(seen.blind)))
    for name, words in owed:
        messenger.send(root, now, name, words, post)
    return replace(seen, cash=cash)
