"""store - THE ONE PRICE STORE AND ITS ONE WRITER. Bars are cleaned once, on entry; a line
that cannot be made clean is parked with a reason and a date, and the others carry on.

The store is rebuilt from the archive on every prepare, so a parked line comes back out on the
first day its bars are clean. One file per line, written whole, then swapped in."""

from __future__ import annotations

import csv
from bisect import bisect_right
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import astuple, dataclass, replace
from datetime import date, timedelta
from decimal import Decimal
from itertools import groupby
from pathlib import Path
from types import MappingProxyType

from desk import venues
from desk.lines import Line

#: Neighbouring bars further apart than this factor (a fall of 37.5%, a rise of 60%) are no
#: market move: a wrong unit (pence among pounds is 100), a bad print, or a 2-for-1 or larger
#: split the archive did not adjust. A smaller wrong factor cannot be told from a move, and passes.
JUMP = Decimal("1.6")
#: London prints its auctions apart from the day's trading, so an open or close can sit just
#: outside the high and low: within this fraction it is the official price and the range is
#: stretched to hold it (the operator's ruling of 13 November 2026); further out, it is false.
STRETCH = Decimal("0.03")
#: Only a fault in the last this-many sessions parks a line; an older bad day is dropped and
#: listed, for a line's history never changes (the operator's ruling of 13 November 2026).
RECENT = 60
#: The longest run of bars a hundredfold out of line with both neighbours that is bad days in
#: the wrong unit, not a lasting step. Any other fall and recovery may be real, and parks.
BLIP = 20
#: A run of this many sessions, each repeating the one before or flat with no volume, is a
#: frozen feed (the longest real run since 2010 is three).
FROZEN = 5
#: A price this many times, or this fraction of, its neighbour's close is in another unit.
FAR = 100 / JUMP
#: A one-for-one line's neighbouring closes in the ratio of that day's pound in dollars,
#: within FX_STEP, are a bar in dollars beside one in pounds (IITU, VUAG, 14 November 2026); a
#: leveraged line's real crashes sit as near (5QQQ x0.770): only its stray bar is tested.
FX_STEP, FX_FAR = Decimal("0.05"), Decimal("0.10")
#: The pound's rate a day is judged on is at most this old.
RATE_AGE = timedelta(days=7)
#: A recorded split is adopted when the bar's jump is within this fraction of its ratio.
SPLIT_NEAR = Decimal("0.25")
Rates = Mapping[date, Decimal]  #: the pound's close in dollars, by day
NO_RATES: Rates = MappingProxyType({})
NO_BARS: Mapping[date, Bar] = MappingProxyType({})  #: a second source's bars, by day: none
UNRECORDED = "a gap in the archive, or a suspension the line does not record"
ASTRAY = "is out of line with the days either side: a wrong unit"
COLUMNS = ("day", "open", "high", "low", "close", "volume")
#: Where a line's older bars wait, under the store's: the store is rebuilt from the archive on
#: every prepare, so bars brought from elsewhere are joined to it, the archive's winning.
HISTORY = "history"


@dataclass(frozen=True)
class Bar:
    day: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


@dataclass(frozen=True)
class Fault:
    day: date  #: the session it concerns
    what: str
    lasting: bool = False  #: a step in the price: wrong for every bar before it, however old
    mended: bool = False  #: listed, but mended: the line is not parked for it


@dataclass(frozen=True)
class Refused:
    """The archive's answer for a line it would not, or could not, give."""

    reason: str


@dataclass(frozen=True)
class Parked:
    symbol: str
    reason: str
    day: date


def _once(bars: Sequence[Bar], faults: list[Fault]) -> list[Bar]:
    """One bar per date. A date given twice the same keeps one; given twice differently,
    neither, because the store cannot know which is true."""
    by_day: dict[date, list[Bar]] = {}
    for bar in bars:
        by_day.setdefault(bar.day, []).append(bar)
    once = []
    for day, given in sorted(by_day.items()):
        if len(set(given)) > 1:
            faults.append(Fault(day, f"{day} given {len(given)} times, differently; none kept"))
            continue
        if len(given) > 1:
            faults.append(Fault(day, f"{day} given {len(given)} times"))
        once.append(given[0])
    return once


def _entered(line: Line, bar: Bar, open_days: set[date], faults: list[Fault]) -> Bar | str:
    """The bar as it enters the store, or why it cannot be true on its own. A bar whose only
    fault is an impossible high or low is kept, clamped and listed. A fall the close shares
    stands."""
    prices = (bar.open, bar.high, bar.low, bar.close)
    if bar.day in line.suspended:
        return f"{bar.day} has a bar, yet {line.symbol} records it as suspended"
    if bar.day not in open_days:
        return f"{bar.day} is not a closed session on the {line.venue} calendar"
    if not all(p.is_finite() and p > 0 for p in prices) or bar.volume < 0:
        return f"{bar.day} has a price or volume that cannot be"
    ends = (bar.open, bar.close)
    reach = (bar.low * (1 - STRETCH), bar.high * (1 + STRETCH))
    if not bar.low <= bar.high or not reach[0] <= min(ends) <= max(ends) <= reach[1]:
        return f"{bar.day} has an open or close outside its high and low"
    high = max(bar.high, *ends)
    if high >= JUMP * max(ends):
        faults.append(Fault(bar.day, f"{bar.day} high repaired: was {bar.high}"))
        high = max(ends)
    low = min(bar.low, *ends)
    if low <= min(ends) / JUMP:
        faults.append(Fault(bar.day, f"{bar.day} low repaired: was {bar.low}"))
        low = min(ends)
    return replace(bar, high=high, low=low)


def _rate(rates: Rates, day: date) -> Decimal | None:
    """The pound's newest close in dollars on or before day, if no older than RATE_AGE."""
    days = sorted(rates)
    at = bisect_right(days, day)
    return rates[days[at - 1]] if at and day - days[at - 1] <= RATE_AGE else None


def _fx(ratio: Decimal, rate: Decimal | None, near: Decimal) -> bool:
    """The ratio of two closes is the pound's rate, or one over it, within near."""
    return rate is not None and any(abs(ratio / r - 1) <= near for r in (rate, 1 / rate))


def _agree(line: Line, before: Bar, after: Bar, rates: Rates) -> bool:
    """Two neighbouring bars could both be true: each one's range lies within a market's move
    of the other's close, or the line records this close as a real move. A plain line's step as
    large as that day's pound in dollars is a change of currency."""

    def near(bar: Bar, close: Decimal) -> bool:
        return close / JUMP <= bar.low and bar.high <= close * JUMP

    confirmed = dict(line.real_moves).get(after.day)
    if confirmed is not None:
        return after.close == confirmed and near(after, after.close)
    if line.leverage == 1 and _fx(after.close / before.close, _rate(rates, after.day), FX_STEP):
        return False
    return near(after, before.close) and near(before, after.close)


def moves(line: Line, bars: Sequence[Bar], rates: Rates = NO_RATES) -> tuple[date, ...]:
    """The days in a line's kept bars whose bar and the one kept before it cannot both be true:
    a move the store does not believe and the line does not record, judged on the bars as kept."""
    pairs = zip(bars, bars[1:], strict=False)
    return tuple(after.day for before, after in pairs if not _agree(line, before, after, rates))


def _far(bar: Bar, close: Decimal, rate: Decimal | None) -> bool:
    """Some price of the bar sits in another unit from close: no market moves that far. The
    pound's rate is another unit's, unless the rate is None (a leveraged line)."""
    hundredfold = any(
        p >= close * FAR or p * FAR <= close for p in (bar.open, bar.high, bar.low, bar.close)
    )
    return hundredfold or _fx(bar.close / close, rate, FX_FAR)


def _stray(at: int, links: Sequence[bool]) -> bool:
    """A bar out of line with every neighbour, where links[n] says bars n and n+1 agree. An end
    bar is a stray only if its one neighbour agrees with the bar beyond it."""
    left = links[at - 1] if at > 0 else None
    right = links[at] if at < len(links) else None
    if left is None or right is None:
        own, beyond = (right, links[1:2]) if left is None else (left, links[-2:-1])
        return own is False and list(beyond) == [True]
    return not left and not right


def _priced(line: Line, sound: Sequence[Bar], faults: list[Fault], rates: Rates) -> list[Bar]:
    """Drop a bar, or a short run, a hundredfold out of line with the days either side or in the
    other currency; keep any other move as a lasting fault until the line records it."""
    links = [_agree(line, a, b, rates) for a, b in zip(sound, sound[1:], strict=False)]
    kept: list[Bar] = []
    resume = 0
    for at, bar in enumerate(sound):
        if at < resume:
            continue
        rate = _rate(rates, bar.day) if line.leverage == 1 else None
        if _stray(at, links) and _far(bar, sound[at - 1 if at else 1].close, rate):
            faults.append(Fault(bar.day, f"{bar.day} {ASTRAY}"))
            continue
        if kept and not _agree(line, kept[-1], bar, rates):
            back = at + 1 < len(sound) and _agree(line, kept[-1], sound[at + 1], rates)
            if bar.volume == 0 and back:  # no trade states no price (2MU, 24 October 2025)
                faults.append(Fault(bar.day, f"{bar.day} {ASTRAY}: it has no volume"))
                continue
            unit = _far(bar, kept[-1].close, rate)
            dollars = _fx(bar.close / kept[-1].close, rate, FX_FAR)  # the pound's rate holds a run
            reach = len(sound) if dollars else min(at + 1 + BLIP, len(sound))
            ahead = range(at + 1, reach if unit else at + 1)
            resume = next((n for n in ahead if not _far(sound[n], kept[-1].close, rate)), at)
            for odd in sound[at:resume]:
                faults.append(Fault(odd.day, f"{odd.day} {ASTRAY}"))
            if resume > at:
                continue
            what = (
                f"{bar.day} moved from {kept[-1].close} to {bar.close}: a split the archive "
                "did not adjust, a change of currency, or a real move the line does not record"
            )
            faults.append(Fault(bar.day, what, lasting=True))
        kept.append(bar)
    return kept


def _split(bars: list[Bar], day: date, ratio: Decimal, faults: list[Fault]) -> None:
    """Multiply the prices before day by ratio (and divide their volume), if the jump across day
    is the ratio, within SPLIT_NEAR. A market-sized jump is a split already adjusted; any other
    leaves the bars, and a fault."""
    at = next((n for n, bar in enumerate(bars) if bar.day >= day), 0)
    if at == 0:
        return
    jump = bars[at].close / bars[at - 1].close
    if 1 / JUMP <= jump <= JUMP:
        return
    if abs(jump / ratio - 1) > SPLIT_NEAR:
        what = f"{day} is recorded as a split of {ratio}, yet the bar's jump is {jump:.4f}"
        faults.append(Fault(day, what, lasting=True))
        return
    for n, bar in enumerate(bars[:at]):
        shares = (Decimal(bar.volume) / ratio).to_integral_value()
        prices = (bar.open * ratio, bar.high * ratio, bar.low * ratio, bar.close * ratio)
        bars[n] = Bar(bar.day, *prices, int(shares))


def _still(before: Bar, bar: Bar) -> bool:
    """The bar repeats the one before it, its volume too or with none, or sits flat at its
    close with none: no market prints the same bar day after day."""
    prices = (bar.open, bar.high, bar.low, bar.close)
    repeated = prices == (before.open, before.high, before.low, before.close)
    flat = all(p == before.close for p in prices)
    return (repeated and bar.volume in (0, before.volume)) or (flat and bar.volume == 0)


def _thawed(kept: Sequence[Bar], faults: list[Fault]) -> list[Bar]:
    """Drop and list every run of FROZEN or more still bars, by the run's last day."""
    still = [at > 0 and _still(kept[at - 1], bar) for at, bar in enumerate(kept)]
    thawed: list[Bar] = []
    for frozen, pairs in groupby(zip(kept, still, strict=True), key=lambda pair: pair[1]):
        run = [bar for bar, _ in pairs]
        if frozen and len(run) >= FROZEN:
            what = f"{run[0].day} to {run[-1].day} repeat one price with no volume: a frozen feed"
            faults.append(Fault(run[-1].day, what))
        else:
            thawed.extend(run)
    return thawed


def _clean(
    line: Line,
    bars: Sequence[Bar],
    day: date,
    since: date,
    rates: Rates = NO_RATES,
    second: Mapping[date, Bar] = NO_BARS,
) -> tuple[list[Bar], list[Fault]]:
    """THE SECOND SOURCE'S RULE, then the bars of one line that can be true. The first source
    rules: the second fills a session only where the first kept none; where both hold one their
    closes must agree within STRETCH, else it is a fault and neither bar is kept."""
    mine = {b.day: b.close for b in bars if b.close.is_finite() and b.close > 0}
    apart = {
        d for d, b in second.items() if d in mine and abs(b.close - mine[d]) > STRETCH * mine[d]
    }
    faults = [Fault(d, f"{d} the sources disagree: {mine[d]} and {second[d].close}; none kept")
              for d in sorted(apart)]  # fmt: skip
    bars = [b for b in bars if b.day not in apart]
    first = min((b.day for b in bars if b.day.year in venues.KNOWN), default=day)
    every = venues.sessions(line.venue, first, day - timedelta(1))
    expected = [d for d in every if d not in line.suspended]
    open_days, sound = set(expected), []
    for bar in _once(bars, faults):
        entered = _entered(line, bar, open_days, faults)
        if isinstance(entered, str):
            faults.append(Fault(bar.day, entered))
        else:
            sound.append(entered)
    for split_day, ratio in sorted(line.splits):
        _split(sound, split_day, ratio, faults)
    kept = _thawed(_priced(line, sound, faults, rates), faults)
    held = {b.day for b in kept}
    missing = [d for d in expected if d not in held]
    if filling := [second[d] for d in missing if d in second and d not in apart]:
        gone = {b.day for b in filling}
        kept, found = _clean(
            line, [*(b for b in bars if b.day not in gone), *filling], day, since, rates
        )
        said = [
            Fault(b.day, f"{b.day} filled from the second source", mended=True) for b in filling
        ]
        return kept, [*faults[: len(apart)], *said, *found]
    if not kept:
        faults.append(Fault(day, "no clean bar: every session missing"))
    for gap in ([d for d in missing if d < since], [d for d in missing if d >= since]):
        if kept and gap:
            what = f"{len(gap)} sessions missing, the first {gap[0]}: {UNRECORDED}"
            faults.append(Fault(gap[0], what))
    return kept, faults


def _write(path: Path, header: Sequence[str], rows: Iterable[Sequence[object]]) -> None:
    part = path.with_suffix(".part")
    with part.open("w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(header)
        writer.writerows(rows)
    part.replace(path)


def prepare(
    root: Path,
    archive: Mapping[Line, Sequence[Bar] | Refused],
    day: date,
    rates: Rates = NO_RATES,
    second: Mapping[Line, Mapping[date, Bar]] = MappingProxyType({}),
) -> tuple[Parked, ...]:
    """Clean the archive's bars into the store at root, ready to trade on day. A refused line
    keeps no bars, so none from an earlier day can be read as today's. The pound's closes in
    dollars tell a change of currency from a move; a second source fills the archive's holes."""
    root.mkdir(parents=True, exist_ok=True)
    parked = []
    for line, bars in archive.items():
        since = venues.sessions(line.venue, day - timedelta(100), day - timedelta(1))[-RECENT]
        if isinstance(bars, Refused):
            kept: list[Bar] = []
            faults = [Fault(day, f"the archive refused it: {bars.reason}")]
        else:
            kept, faults = _clean(
                line, _joined(root, line, bars), day, since, rates, second.get(line, NO_BARS)
            )
        _write(root / f"{line.symbol}.csv", COLUMNS, (astuple(bar) for bar in kept))
        _write(root / f"{line.symbol}.faults.csv", ("fault",), ((f.what,) for f in faults))
        recent = [f.what for f in faults if f.lasting or (f.day >= since and not f.mended)]
        if recent:
            parked.append(Parked(line.symbol, "; ".join(recent), day))
    return tuple(parked)


def _load(path: Path) -> tuple[Bar, ...]:
    with path.open(newline="", encoding="utf-8") as stored:
        rows = list(csv.reader(stored))[1:]  # the header skipped
    return tuple(
        Bar(date.fromisoformat(d), Decimal(o), Decimal(hi), Decimal(lo), Decimal(c), int(v))
        for d, o, hi, lo, c, v in rows
    )


def shelve(root: Path, line: Line, bars: Iterable[Bar]) -> None:
    """A line's older bars, kept for every prepare to join to the archive's, replacing any."""
    (root / HISTORY).mkdir(parents=True, exist_ok=True)
    _write(root / HISTORY / f"{line.symbol}.csv", COLUMNS, (astuple(bar) for bar in bars))


def _joined(root: Path, line: Line, bars: Sequence[Bar]) -> list[Bar]:
    """The archive's bars and, for each day it gives none, the line's shelved bar. A frozen run
    in the archive's bars is filler: with a shelf none of it is kept."""
    shelved = root / HISTORY / f"{line.symbol}.csv"
    if not shelved.is_file():
        return list(bars)
    real = set(_thawed(bars, []))
    given = [bar for bar in bars if bar in real]
    held = {bar.day for bar in given}
    older = (bar for bar in _load(shelved) if bar.day not in held)
    return sorted([*older, *given], key=lambda bar: bar.day)


def read(root: Path, symbol: str) -> tuple[Bar, ...]:
    """Every bar the store kept for one line, oldest first (a parked line keeps them too)."""
    return _load(root / f"{symbol}.csv")


def faults(root: Path, symbol: str) -> tuple[str, ...]:
    """Every fault found in a line's bars on the last prepare, the old ones included."""
    with (root / f"{symbol}.faults.csv").open(newline="", encoding="utf-8") as stored:
        return tuple(row["fault"] for row in csv.DictReader(stored))
