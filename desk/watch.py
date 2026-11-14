"""watch - THE CRASH WATCH (EMG-01, EMG-03). Every five minutes, at every hour, whoever runs
the desk asks for one look. A look reads, in the one fast store, the newest five-minute bar of
every line it is given whose venue is trading (every line of the desk's, so every one it
holds, and the market's own with them) and measures each fall as the three emergencies
define it (desk/emergency.py). Then, at once:

- A CRASH raises a halt (desk/halt.py), and the send path sends no buy on any line. It is
  raised by any bar of the session the market is trading in, and of its last session unless
  that is read to have ended clear: so a fall made at the close, or one the desk slept
  through, still halts. Only an end lifts it: the watch lifts its own halt once the market
  has ended a day clear of a crash, read at that session's very last bar when its closing
  auction is over. An end that cannot be read lifts nothing, and he is told so, once.
- A BLACK SWAN: the same, with a halt that only he lifts. Read at the market's two newest
  bars while that halt stands, it is read twice (Look.cash), which is what the sale of every
  position waits for. That sale is not built (STP-07): nothing is sold, and he is told so.
- AN EMERGENCY, one line's: he is told, and that nothing parks one line yet.

THE WATCH'S HALTS FOLLOW THE MARKET, a crash's and a black swan's each on its own. One he
lifts while the market still raises it is called again at the next look, and he is told: his
lift holds once the market has ended a day clear. A way for his word to stand against the
market is not built. The record says who lifted each halt.

WHAT HE IS TOLD, through the desk's one voice, at any hour, each message once under its
name: each halt of the watch's while it stands, in the fall's own words (the halt's reason,
and so the record of why) with what was done and what was not; its lift, with every halt
still in force; each line's emergency, once a day. A standing halt is owed its message
whatever the market reads now, so one his phone's door did not take goes at the next look.

THE CLOCK. A bar is read once it has ended. Five minutes in which a line did not trade have
no bar, so a line's newest bar of the session is its price for as long as its venue is heard
from: when the newest bar of any of its lines ended, or at its open. Past STALE of that no
line of the venue is read, and the market must be heard from itself. A line not read is
unread, with why, never calm. A market that is trading and cannot be read makes the watch
BLIND: he is told, once in each hour it lasts, and no halt is called for that alone. A look
remembers nothing, and is one of the desk's steps: one process at a time."""

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
STALE = timedelta(minutes=20)  #: a venue, or the market, not heard from for longer is not read
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
        "DONE: a halt is in force that only you lift, and no buy goes on any line; lifted "
        "before the market has ended a day clear, the watch calls it again. NOT DONE: nothing "
        "is sold. The sale of every position is not built, and would wait for a second "
        "reading; the stops rest at the broker as ever."
    ),
}
TWICE = (
    "BLACK SWAN, READ TWICE: the market's two newest bars both say so. {} NOT DONE: nothing "
    "is sold, for the sale of every position is not built. The stops rest at the broker; the "
    "rest is yours."
)
BLIND = (
    "THE CRASH WATCH IS BLIND: it cannot read the market. {}. No halt is called for that, "
    "and a crash now would not be seen. This is told once in each hour it lasts."
)
UNENDED = (
    "THE CRASH WATCH CANNOT READ HOW THE MARKET ENDED {}: its last five-minute bar is not in "
    "the store, or its daily closes are not whole. No halt of the watch's is lifted by it, "
    "and one is called only if a bar of that day in the store read a crash. Told once."
)
Owed = list[tuple[str, str]]  #: messages he is owed: each one's name, and its words


@dataclass(frozen=True)
class Look:
    """One look: every line given whose venue was trading, its fall read or why it was not."""

    at: datetime
    falls: tuple[Fall, ...]
    unread: Mapping[Line, str]  #: why no fall was read of a line: that line is not calm
    cash: bool = False  #: a black swan read twice while its halt stands: the sale's signal

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


def _grave(market: Sequence[Bar], bar: Five) -> Fall | None:
    """The market's fall at a bar when it is a crash or a black swan; None when it is
    neither, and when the bar cannot be read: that raises nothing and confirms nothing."""
    try:
        fall = emergency.measure(YARDSTICK, market, bar)
    except Unread:
        return None
    return fall if fall.level is not None else None


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
    venue = {line.venue: max(heard[o] for o in heard if o.venue == line.venue) for line in heard}
    falls, unread, twice = [], {}, False
    for line, got in ended.items():
        own = line == YARDSTICK
        last = heard[line] if own else venue[line.venue]
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
            swans = [(fall := _grave(daily[line], bar)) and fall.level for bar in got[-2:]]
            twice = swans == [Level.BLACK_SWAN] * 2
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


def _raised(hot: Path, market: Sequence[Bar], now: datetime) -> list[Fall]:
    """WHAT RAISES A HALT at a moment: the gravest fall the market read at any bar of its
    last session, unless that is read to have ended clear, and of the session it is trading
    in. A reading within a day raises, however late it is looked at, or stale."""
    sessions = [last for last in _over(now - BACK, now)[-1:] if not _clear(hot, market, last)]
    sessions += filter(None, [venues.open_at(YARDSTICK.venue, now)])
    falls = []
    for session in sessions:
        grave = [f for bar in _ended(hot, YARDSTICK, session, now) if (f := _grave(market, bar))]
        falls += [max(grave, key=lambda fall: fall.level is Level.BLACK_SWAN)] if grave else []
    return falls


def _lift(root: Path, end: Fall, session: Hours, now: datetime) -> Owed:
    """THE WATCH LIFTS ITS OWN crash halts when the market's last session ended clear of a
    crash: those called before the session it trades in now began, as of that end, whenever
    the look comes. A halt that is his alone, a black swan's, is never the watch's to lift.
    Given back: each lift's message, which says every halt still in force too."""
    trading, told = venues.open_at(YARDSTICK.venue, now), []
    for called in halt.in_force(root):
        if called.by == WATCH and not called.his and not (trading and called.at >= trading.open):
            why = f"{WATCH}: the market ended {end.on} clear of a crash. {end.words()}"
            lifted = halt.lift(root, called, max(session.auction, called.at), why, by=WATCH)
            said = " ".join(h.words(now.date()) for h in (lifted, *halt.in_force(root)))
            told.append((f"watch {called.at:%Y-%m-%d %H:%M} lifted", said))
    return told


def _call(root: Path, fall: Fall, now: datetime) -> None:
    """THE MARKET'S FALL HALTS ALL BUYING: a halt of the watch's is called, his alone to lift
    for a black swan, unless one of its kind stands already."""
    his = fall.level is Level.BLACK_SWAN
    if not any(h.by == WATCH and h.his == his for h in halt.in_force(root)):
        halt.call(root, now, fall.words(), by=WATCH, his=his)


def _halts(root: Path, hot: Path, market: Sequence[Bar], now: datetime) -> Owed:
    """THE MARKET'S HALTS, PUT RIGHT: a last session that ended clear lifts, an end unread
    is said, and what raises a halt calls one. Given back: what he is owed for it."""
    owed: Owed = []
    last = _over(now - BACK, now)[-1:]
    end = _end(hot, market, last[0]) if last else None
    if end is not None and end.level is None:
        owed += _lift(root, end, last[0], now)
    if last and end is None and now - last[0].auction > STALE:
        day = last[0].close.date()
        owed.append((f"watch {day} end unread", UNENDED.format(day)))
    for fall in _raised(hot, market, now):
        _call(root, fall, now)
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
    owed = _halts(root, hot, daily[YARDSTICK], now)
    standing = [called for called in halt.in_force(root) if called.by == WATCH]
    for called in standing:
        level = Level.BLACK_SWAN if called.his else Level.CRASH
        name = f"watch {called.at:%Y-%m-%d %H:%M} {level.name}"
        owed.append((name, f"{called.why} {DONE[level]}"))
    cash = seen.cash and any(called.his for called in standing)
    for fall in sorted(seen.falls, key=lambda fall: not fall.market):
        if fall.market and cash:
            owed.append((f"watch {fall.on} BLACK_SWAN twice", TWICE.format(fall.words())))
        elif not fall.market and fall.level is not None:
            name = f"watch {fall.on} {fall.line.symbol} EMERGENCY"
            owed.append((name, f"{fall.words()} {PARK}"))
    if seen.blind:
        owed.append((f"watch {now:%Y-%m-%d %H}h blind", BLIND.format(seen.blind)))
    for name, words in owed:
        messenger.send(root, now, name, words, post)
    return replace(seen, cash=cash)
