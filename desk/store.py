"""store - THE ONE PRICE STORE AND ITS ONE WRITER. Bars are cleaned once, on entry; a line
that cannot be made clean is parked with a reason and a date, and the others carry on.

The store is rebuilt from the archive on every prepare, so a parked line comes back out by
itself on the first day its bars are clean. One file per line, written whole, then swapped
in, so a reader never sees half a write."""

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

#: Neighbouring bars further apart than this (a fall of 37.5%, a rise of 60%) are no market move:
#: a wrong unit (pence among pounds), a bad print, or an unadjusted split of 2-for-1 or more.
JUMP = Decimal("1.6")
#: London records its auctions apart from the day's trading, so an open or close can sit just
#: outside the day's range. Within this fraction the range stretches (his ruling, 13 Nov 2026).
STRETCH = Decimal("0.03")
RECENT = 60  #: only a fault in the last this-many sessions parks a line; older bad days are listed
#: The longest run a hundredfold out of line with its neighbours is bad days, not a lasting step.
BLIP = 20
#: A run of this many sessions, each repeating the bar before it or flat at its close with no
#: volume, is a frozen feed (the longest real run since 2010 is three): dropped and listed.
FROZEN = 5
#: A price this many times, or this fraction of, its neighbour's close is in another unit.
FAR = 100 / JUMP
#: A one-for-one line's closes in the ratio of the day's pound in dollars, within this fraction,
#: are dollars among pounds if the step lasts (IITU x0.662); a leveraged line's real crashes sit
#: as near (5QQQ x0.770), so only its stray bar is tested, within FX_FAR.
FX_STEP, FX_FAR = Decimal("0.05"), Decimal("0.10")
RATE_AGE = timedelta(days=7)  #: the newest pound in dollars a day is judged on is at most this old
AGREE = Decimal("0.02")  #: two sources' closes for a session must agree within this (R-RUNNER-189)
SPLIT_NEAR = Decimal("0.25")  #: a recorded split is adopted if the jump is this near its ratio
Rates = Mapping[date, Decimal]  #: the pound's close in dollars, by day
NO_RATES: Rates = MappingProxyType({})
UNRECORDED = "a gap in the archive, or a suspension the line does not record"
ASTRAY = "is out of line with the days either side: a wrong unit"
COLUMNS = ("day", "open", "high", "low", "close", "volume")
#: Where a line's older bars wait, under the store's: the store is rebuilt from the archive on
#: every prepare, so bars brought from elsewhere would be lost. Joined to the archive's, which wins.
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
    noted: bool = False  #: a repair kept beside the bar that parks no line, however recent


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
    """The bar as it enters the store, or why it cannot be true on its own. A wrong high or low is
    clamped to the open or close and parks the line; a stretch is only noted beside the bar."""
    prices = (bar.open, bar.high, bar.low, bar.close)
    if bar.day in line.suspended:
        return f"{bar.day} has a bar, yet {line.symbol} records it as suspended"
    if bar.day not in open_days:
        return f"{bar.day} is not a closed session on the {line.venue} calendar, or too early"
    if not all(p.is_finite() and p > 0 for p in prices) or bar.volume < 0:
        return f"{bar.day} has a price or volume that cannot be"
    ends, reach = (bar.open, bar.close), (bar.low * (1 - STRETCH), bar.high * (1 + STRETCH))
    if not bar.low <= bar.high or not reach[0] <= min(ends) <= max(ends) <= reach[1]:
        return f"{bar.day} has an open or close outside its high and low"
    high, low = max(bar.high, *ends), min(bar.low, *ends)
    bad = (high >= JUMP * max(ends), low <= min(ends) / JUMP)
    if bad[0] or high != bar.high:
        what = f"{bar.day} high {'repaired' if bad[0] else 'stretched'}: was {bar.high}"
        faults.append(Fault(bar.day, what, noted=not bad[0]))
    if bad[1] or low != bar.low:
        what = f"{bar.day} low {'repaired' if bad[1] else 'stretched'}: was {bar.low}"
        faults.append(Fault(bar.day, what, noted=not bad[1]))
    return replace(bar, high=max(ends) if bad[0] else high, low=min(ends) if bad[1] else low)


def pound_on(rates: Rates, day: date) -> Decimal | None:
    """The pound's newest close in dollars on or before day, if no older than RATE_AGE."""
    days = sorted(rates)
    last = days[bisect_right(days, day) - 1] if rates and day >= days[0] else None
    return rates[last] if last and day - last <= RATE_AGE else None


def same_as_pound(ratio: Decimal, pound: Decimal | None, within: Decimal) -> bool:
    """The ratio of two closes is the pound's rate, or one over it, within the given fraction."""
    return pound is not None and any(abs(ratio / r - 1) <= within for r in (pound, 1 / pound))


def _agree(line: Line, before: Bar, onward: Sequence[Bar], rates: Rates) -> bool:
    """Neighbouring bars could both be true: each one's range lies within a market's move of the
    other's close, or the line records this close. A step as large as the pound's that lasts, every
    close of the next RECENT sessions still in the new unit, is a currency. onward: after, on."""
    after, ahead = onward[0], onward[1:]

    def near(bar: Bar, close: Decimal) -> bool:
        return close / JUMP <= bar.low and bar.high <= close * JUMP

    confirmed = dict(line.real_moves).get(after.day)
    if confirmed is not None:
        return after.close == confirmed and near(after, after.close)
    pound = pound_on(rates, after.day)
    step = line.leverage == 1 and same_as_pound(after.close / before.close, pound, FX_STEP)
    if step and all(same_as_pound(b.close / before.close, pound, FX_FAR) for b in ahead[:RECENT]):
        return False  # every close stays in the new unit: a move that came back is the market's
    return near(after, before.close) and near(before, after.close)


def moves(line: Line, bars: Sequence[Bar], rates: Rates = NO_RATES) -> tuple[date, ...]:
    """The days in a line's kept bars whose bar and the bar kept before it cannot both be
    true, by a move further than the store believes a market makes that the line does not
    record. They are the moves a line is parked for until confirmed, judged on the bars as
    kept: where a frozen run was dropped, the bars either side of it are neighbours here."""
    links = [_agree(line, bars[n], bars[n + 1 :], rates) for n in range(len(bars) - 1)]
    return tuple(bar.day for bar, ok in zip(bars[1:], links, strict=True) if not ok)


def _far(bar: Bar, close: Decimal, rate: Decimal | None) -> bool:
    """Some price of the bar sits in another unit from close: no market moves that far. The
    pound's rate is another unit's (dollars among pounds), when the bar's close is so; a
    rate of None, for a leveraged line whose real crashes sit as near it, is not tried."""
    hundredfold = any(
        p >= close * FAR or p * FAR <= close for p in (bar.open, bar.high, bar.low, bar.close)
    )
    return hundredfold or same_as_pound(bar.close / close, rate, FX_FAR)


def _stray(at: int, links: Sequence[bool]) -> bool:
    """A bar out of line with every neighbour, where links[n] says bars n and n+1 agree. An end
    bar is a stray only if its one neighbour agrees with the bar beyond; of two, neither is."""
    left = links[at - 1] if at > 0 else None
    right = links[at] if at < len(links) else None
    if left is None or right is None:
        own, beyond = (right, links[1:2]) if left is None else (left, links[-2:-1])
        return own is False and list(beyond) == [True]
    return not left and not right


def _untraded(kept: list[Bar], bar: Bar, rate: Decimal | None, faults: list[Fault]) -> None:
    """No trade states no price: kept bars of no volume in another unit give way to a traded bar."""
    while kept and kept[-1].volume == 0 < bar.volume and _far(bar, kept[-1].close, rate):
        day = kept.pop().day
        faults.append(Fault(day, f"{day} {ASTRAY}: it has no volume"))


def _priced(line: Line, sound: Sequence[Bar], faults: list[Fault], rates: Rates) -> list[Bar]:
    """Drop a bar, or a short run, a hundredfold out of line with the days either side or in the
    other currency; keep any other move, a one-day crash too, as a lasting fault until recorded."""
    links = [_agree(line, sound[n], sound[n + 1 :], rates) for n in range(len(sound) - 1)]
    kept: list[Bar] = []
    resume = 0
    for at, bar in enumerate(sound):
        if at < resume:
            continue
        rate = pound_on(rates, bar.day) if line.leverage == 1 else None
        if _stray(at, links) and _far(bar, sound[at - 1 if at else 1].close, rate):
            faults.append(Fault(bar.day, f"{bar.day} {ASTRAY}"))
            continue
        _untraded(kept, bar, rate, faults)
        if kept and not _agree(line, kept[-1], sound[at:], rates):
            back = at + 1 < len(sound) and _agree(line, kept[-1], sound[at + 1 :], rates)
            if bar.volume == 0 and back:  # no trade states no price (2MU, 24 October 2025)
                faults.append(Fault(bar.day, f"{bar.day} {ASTRAY}: it has no volume"))
                continue
            unit = _far(bar, kept[-1].close, rate)
            dollars = same_as_pound(bar.close / kept[-1].close, rate, FX_FAR)  # a run in dollars
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
    """Multiply the prices before day by ratio (divide the volume), if the jump across day is the
    ratio within SPLIT_NEAR; a market-sized jump is adjusted already; any other is a fault."""
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
    line: Line, bars: Sequence[Bar], day: date, since: date, rates: Rates = NO_RATES
) -> tuple[list[Bar], list[Fault]]:
    """The bars of one line that can be true, and every fault found."""
    faults: list[Fault] = []
    first = min((b.day for b in bars if b.day.year in venues.KNOWN), default=day)
    every = venues.sessions(line.venue, max(first, line.starts or first), day - timedelta(1))
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


Answer = Sequence[Bar] | Refused  #: what the archive gave for a line
Older = Sequence[Bar] | None  #: a line's older bars


def judge(
    line: Line,
    answer: Answer,
    day: date,
    rates: Rates = NO_RATES,
    shelf: Older = None,
    broker: Answer | None = None,
) -> tuple[list[Bar], list[Fault], Parked | None]:
    """THE ONE JUDGEMENT of a line's bars: those that can be true, every fault found and, if one
    is recent or lasting, the line parked, ready to trade on day. The broker's bars stand first
    (his ruling of 16 November), the archive's under them, the shelf's under those. A line none
    gave bars for keeps none, so none from an earlier day can be read as today's."""
    since = venues.sessions(line.venue, day - timedelta(100), day - timedelta(1))[-RECENT]
    top = None if broker is None or isinstance(broker, Refused) else broker
    if isinstance(answer, Refused) and top is None:
        kept: list[Bar] = []
        faults = [Fault(day, f"the archive refused it: {answer.reason}")]
    else:
        joined, faults = ([], []) if isinstance(answer, Refused) else _joined(shelf, answer)
        if top is not None:
            joined, over = _joined(joined, top, "broker", "archive")
            faults += over
        kept, found = _clean(line, joined, day, since, rates)
        faults = [*faults, *found]
    recent = [f.what for f in faults if not f.noted and (f.lasting or f.day >= since)]
    return kept, faults, Parked(line.symbol, "; ".join(recent), day) if recent else None


def prepare(
    root: Path, archive: Mapping[Line, Answer], day: date, rates: Rates = NO_RATES
) -> tuple[Parked, ...]:
    """Clean the archive's bars into the CSV store at root, ready to trade on day."""
    root.mkdir(parents=True, exist_ok=True)
    parked: list[Parked] = []
    for line, answer in archive.items():
        shelved = root / HISTORY / f"{line.symbol}.csv"
        older = read(root / HISTORY, line.symbol) if shelved.is_file() else None
        kept, faults, park = judge(line, answer, day, rates, older)
        _write(root / f"{line.symbol}.csv", COLUMNS, (astuple(bar) for bar in kept))
        _write(root / f"{line.symbol}.faults.csv", ("fault",), ((f.what,) for f in faults))
        parked += [park] if park else []
    return tuple(parked)


def shelve(root: Path, line: Line, bars: Iterable[Bar]) -> None:
    """A line's older bars, kept for every prepare to join to the archive's, replacing any
    shelved before. They are cleaned as the archive's are, with it, on each prepare."""
    (root / HISTORY).mkdir(parents=True, exist_ok=True)
    _write(root / HISTORY / f"{line.symbol}.csv", COLUMNS, (astuple(bar) for bar in bars))


def _joined(
    shelf: Older, bars: Sequence[Bar], over: str = "archive", under: str = "shelf"
) -> tuple[list[Bar], list[Fault]]:
    """The upper source's bars, a lower one's bar for each day it gives none; closes both give
    beyond AGREE are a fault naming both, the upper's standing. A frozen run is dropped."""
    if shelf is None:
        return list(bars), []
    real = set(_thawed(bars, []))
    given = {bar.day: bar for bar in bars if bar in real}
    both = [(b, given[b.day]) for b in shelf if b.day in given]
    fills = (bar for bar in shelf if bar.day not in given)
    return sorted([*fills, *given.values()], key=lambda x: x.day), [
        Fault(b.day, f"{b.day} close {a.close} ({over}), {b.close} ({under})")
        for b, a in both
        if abs(b.close / a.close - 1) > AGREE
    ]


def _bar(r: Mapping[str, str]) -> Bar:
    o, h, low, c = (Decimal(r[name]) for name in COLUMNS[1:5])
    return Bar(date.fromisoformat(r["day"]), o, h, low, c, int(r["volume"]))


def read(root: Path, symbol: str) -> tuple[Bar, ...]:
    """Every bar the store kept for one line, oldest first (a parked line's too)."""
    with (root / f"{symbol}.csv").open(newline="", encoding="utf-8") as stored:
        return tuple(_bar(r) for r in csv.DictReader(stored))


def faults(root: Path, symbol: str) -> tuple[str, ...]:
    """Every fault found in a line's bars on the last prepare, the old ones that no longer
    park it included."""
    with (root / f"{symbol}.faults.csv").open(newline="", encoding="utf-8") as stored:
        return tuple(row["fault"] for row in csv.DictReader(stored))
