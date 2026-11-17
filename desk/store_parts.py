"""store_parts - what judges a line's neighbouring bars for the one store, split from desk/store.py:
the bar and fault types, the limits of a move, and the pass that drops a bar or a run out of line
with its neighbours (a wrong unit, another currency) or keeps the move as a lasting fault."""

from __future__ import annotations

from bisect import bisect_right
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from types import MappingProxyType

from desk.lines import Line

#: Neighbouring bars further apart than this (a fall of 37.5%, a rise of 60%) are no market move:
#: a wrong unit (pence among pounds), a bad print, or an unadjusted split of 2-for-1 or more.
JUMP = Decimal("1.6")
RECENT = 60  #: only a fault in the last this-many sessions parks a line; older bad days are listed
BLIP = 20  #: the longest run a hundredfold out of line with its neighbours that is bad days
FAR = 100 / JUMP  #: a price this many times, or this fraction of, its neighbour's close: a unit
#: A one-for-one line's closes in the day's pound-in-dollars ratio, within FX_STEP, are dollars
#: among pounds if the step lasts (IITU x0.662); a leveraged line's real crashes sit as near
#: (5QQQ x0.770), so only its stray bar is tested, within FX_FAR.
FX_STEP, FX_FAR = Decimal("0.05"), Decimal("0.10")
RATE_AGE = timedelta(days=7)  #: the newest pound in dollars a day is judged on is at most this old
Rates = Mapping[date, Decimal]  #: the pound's close in dollars, by day
NO_RATES: Rates = MappingProxyType({})
ASTRAY = "is out of line with the days either side: a wrong unit"


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
            faults += [Fault(odd.day, f"{odd.day} {ASTRAY}") for odd in sound[at:resume]]
            if resume > at:
                continue
            what = (
                f"{bar.day} moved from {kept[-1].close} to {bar.close}: a split the archive "
                "did not adjust, a change of currency, or a real move the line does not record"
            )
            faults.append(Fault(bar.day, what, lasting=True))
        kept.append(bar)
    return kept
