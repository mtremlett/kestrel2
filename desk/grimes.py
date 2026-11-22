"""grimes - ADAM GRIMES'S SETUPS AS A MACHINERY TEST ON PAPER (his ruling, 22 November 2026): the
strategy catalogue (kestrel2_research/grimes/catalogue.md, version 3, reviewed at 9.8) of *The Art
and Science of Technical Analysis* (Wiley, 2012), at its defaults, long only, on the daily bar,
under the desk's one engine (`desk.strategy`). Its shared blocks (section 1) are worked once a bar
by `Chart` and `Setup`; its one management module, MGMT (section 2), is `Trade`.

WHAT THE ENGINE MAKES OF IT. The engine holds a line or not, deciding at a bar's close, filled at
the next open: so a resting order (a buy-stop trigger, a protective stop) is a bar trading through
its level, filled at the next open; the partials keep the share left (`Trade.left`) and sell
nothing of one share; sizing by risk, the jitter's symbol, the higher-timeframe contexts, shorts
(section 5) and every sweep are the ladder's. NONE IS EVIDENCE OF AN EDGE: none is in STRATEGIES
or the ladder's rule book, and only the ladder judges (CANON B6)."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from itertools import pairwise

from desk.store import Bar
from desk.strategy import RANGES, Field
from desk.strategy_parts import ZERO, _Exponential, _Wilder, _Window

WIDTH = Decimal("2.25")  #: K: the bands sit this many ATRb either side of the EMA20 [ch3] [ch7]
REACH = Decimal(2)  #: SW: a swing turns on a reversal of this many ATRb (z) [P]
BUFFER, JITTER = Decimal("0.15"), Decimal("0.1")  #: a structural stop's buffer and most jitter [P]
SHARED, OVER = Decimal("0.1"), Decimal("0.05")  #: AG-01(a): highs this near share one; over it
MIN_STOP = Decimal(2)  #: the min-stop filter: a stop nearer than this many ATRb skips [ch8]
FIRST, THIRD = Decimal("0.33"), Decimal(1) / 3  #: partial 1 at +1R; what is left by +2R [ch8]
CHANDELIER = Decimal(3)  #: the remainder's stop: this many ATRb under the best close [ch8] [P]
NEAR = Decimal("0.25")  #: a test of a level or a support: within this many ATRb of it [P]
KEEP = 250  #: the bars a chart keeps: a leg, its pullback and the 40-bar windows, with room
BARS = RANGES | {Field.OPEN}  #: the rules read the whole bar: MGMT fills at the open


def _x(value: Decimal, side: int) -> Decimal:
    """A price as seen from a side: itself for +1 (higher is further), negated for -1."""
    return value * side


def _far(bar: Bar, side: int) -> Decimal:
    """The bar's extreme on that side: its high for +1, its low for -1."""
    return bar.high if side > 0 else bar.low


def _mean(values: Iterable[Decimal]) -> Decimal:
    """The plain average; nothing averages to zero."""
    got = list(values)
    return sum(got, ZERO) / len(got) if got else ZERO


@dataclass(frozen=True)
class Mark:
    """One bar at its close with its blocks: K's middle (the EMA20), ATRb, M's fast line (SMA3 less
    SMA10) and MX (+1: the fast line at a new 40-bar high, -1 a new low, 0 neither)."""

    n: int
    bar: Bar
    mid: Decimal
    atr: Decimal
    fast: Decimal
    mx: int

    def band(self, side: int) -> Decimal:
        """K's upper band (side +1) or lower (-1)."""
        return self.mid + side * WIDTH * self.atr

    def free(self, side: int) -> bool:
        """FB: the whole bar outside K on that side."""
        return _x(_far(self.bar, -side), side) > _x(self.band(side), side)

    def range(self) -> Decimal:
        """The bar's high less its low."""
        return self.bar.high - self.bar.low


@dataclass(frozen=True)
class Pivot:
    """A confirmed swing extreme (SW): a high (side +1) or a low (-1), its bar and fast line."""

    n: int
    price: Decimal
    side: int
    fast: Decimal


class Chart:
    """The blocks of section 1 worked once a bar, from data up to its close only: K, ATRb, M, MX
    and the zigzag swings (SW), a pivot usable only once a reversal of REACH ATRb confirms it."""

    def __init__(self) -> None:
        self._mid, self._atr = _Exponential(20), _Wilder(20)
        self._three, self._ten = _Window(3), _Window(10)
        self._fasts: deque[Decimal] = deque(maxlen=40)
        self.marks: deque[Mark] = deque(maxlen=KEEP)
        self.pivots: deque[Pivot] = deque(maxlen=24)
        self._close: Decimal | None = None
        self._n, self._side = -1, 1  #: the bar's count; the side the swing under way moves to
        self._top: Mark | None = None  #: the swing under way's extreme

    def add(self, bar: Bar) -> Mark | None:
        """Take the next bar in: its mark, or None while the blocks warm up (50 bars)."""
        last, self._close, self._n = self._close, bar.close, self._n + 1
        true = bar.high - bar.low if last is None else max(bar.high, last) - min(bar.low, last)
        atr, mid = self._atr.add(true), self._mid.add(bar.close)
        self._three.add(bar.close)
        self._ten.add(bar.close)
        if atr is None or mid is None or not self._ten.full:
            return None
        fast, full = self._three.mean() - self._ten.mean(), len(self._fasts) == 40
        mx = (fast > max(self._fasts)) - (fast < min(self._fasts)) if full else 0
        self._fasts.append(fast)
        mark = Mark(self._n, bar, mid, atr, fast, mx)
        self.marks.append(mark)
        self._swing(mark)
        return mark if full else None

    def _swing(self, mark: Mark) -> None:
        """SW: extend the swing under way, or confirm its extreme as a pivot on a reversal."""
        top, side = self._top, self._side
        if top is None or _x(_far(mark.bar, side), side) >= _x(_far(top.bar, side), side):
            self._top = mark
        elif _x(_far(top.bar, side) - _far(mark.bar, -side), side) >= REACH * mark.atr:
            self.pivots.append(Pivot(top.n, _far(top.bar, side), side, top.fast))
            after = self.since(top.n)
            self._side, self._top = -side, max(after, key=lambda m: _x(_far(m.bar, -side), -side))

    def since(self, n: int, upto: int | None = None) -> list[Mark]:
        """The marks after bar n, up to bar `upto` (this one when None)."""
        return [m for m in self.marks if n < m.n and (upto is None or m.n <= upto)]

    def last(self, side: int, back: int = 0) -> int | None:
        """The index in `pivots` of the latest pivot on that side (`back` more before it)."""
        found = [i for i, p in enumerate(self.pivots) if p.side == side]
        return found[-1 - back] if len(found) > back else None

    def swings(self) -> list[tuple[int, int, Decimal]]:
        """Every swing, oldest first, the one under way included: the side it moved toward, its
        length in bars and its length in price."""
        ends = [*self.pivots]
        if self._top is not None:
            ends.append(Pivot(self._top.n, _far(self._top.bar, self._side), self._side, ZERO))
        return [(b.side, b.n - a.n, abs(b.price - a.price)) for a, b in pairwise(ends)]


def climax(chart: Chart, side: int, n: int) -> bool:
    """CLX toward a side in the 10 bars to bar n: at least two of 2 free bars or more; a swing 2.5
    times the mean of the 5 before it; 3 closes running in the bar's outer tenth; an MX bar."""
    window = chart.since(n - 10, n)
    swings = [size for toward, _, size in chart.swings() if toward == side][-6:]
    outer = [(_x(m.bar.close - _far(m.bar, -side), side)) >= m.range() * 9 / 10 for m in window]
    runs = any(all(outer[i : i + 3]) for i in range(len(outer) - 2))
    big = len(swings) == 6 and swings[-1] >= Decimal("2.5") * _mean(swings[:-1])
    found = [sum(m.free(side) for m in window) >= 2, big, runs, any(m.mx == side for m in window)]
    return sum(found) >= 2


def diverged(chart: Chart, k: int, upto: int) -> bool:
    """DIV at pivot k, seen at bar `upto`: its fast line fails to beat the prior same-side pivot's,
    valid only if the fast line came within 0.1 ATRb of zero between them, and reset when price
    returns to the EMA20, the fast line crosses zero, or 10 bars pass."""
    end, side = chart.pivots[k], chart.pivots[k].side
    prior = [p for p in list(chart.pivots)[:k] if p.side == side][-1:]
    if not prior or _x(end.fast, side) > _x(prior[0].fast, side):
        return False
    between, after = chart.since(prior[0].n, end.n), chart.since(end.n, upto)
    if not after or min(abs(m.fast) for m in between) > JITTER * after[-1].atr:
        return False
    back = any(_x(_far(m.bar, -side), side) <= _x(m.mid, side) for m in after)
    crossed = any(_x(m.fast, side) <= 0 for m in after)
    return not (back or crossed or len(after) >= 10)


def coc(chart: Chart, side: int) -> bool:
    """CoC toward a side: the latest swing that way is longer, in price or in bars, than the swing
    before it, for the first time in 4 swings or more."""
    swings = chart.swings()
    pairs = [(b, a) for a, b in pairwise(swings) if b[0] == side][-5:]
    beats = [b[1] > a[1] or b[2] > a[2] for b, a in pairs]
    return len(beats) == 5 and beats[-1] and not any(beats[:-1])


def tested(marks: Sequence[Mark], level: Decimal, side: int) -> int:
    """How many of the bars came within NEAR ATRb of a level from beyond it (side +1: a support
    under them, their lows reaching down to it)."""
    return sum(_x(_far(m.bar, -side) - level, side) <= NEAR * m.atr for m in marks)


@dataclass(frozen=True)
class Setup:
    """The with-trend leg into a pullback (side +1: a rise from `start` to `end`, then a dip),
    with the PQ check of section 1 on it at a bar."""

    chart: Chart
    k: int  #: the index in the chart's pivots of the leg's end

    @property
    def end(self) -> Pivot:
        """The setup leg's extreme."""
        return self.chart.pivots[self.k]

    @property
    def legs(self) -> int:
        """LEG: with-trend legs from the trend's origin, the setup leg included; 2 or more is TR."""
        p, i, count = self.chart.pivots, self.k, 1
        while i >= 3 and _x(p[i].price, p[i].side) > _x(p[i - 2].price, p[i].side):
            if _x(p[i - 1].price, p[i].side) <= _x(p[i - 3].price, p[i].side):
                break
            count, i = count + 1, i - 2
        return count

    def leg(self, back: int = 0) -> tuple[Pivot, Pivot]:
        """The setup leg's start and end pivots (`back` with-trend legs before it)."""
        i = self.k - 2 * back
        return self.chart.pivots[i - 1], self.chart.pivots[i]

    def pullback(self, upto: int) -> list[Mark]:
        """The bars after the leg's end, up to bar `upto`."""
        return self.chart.since(self.end.n, upto)

    def low(self, upto: int) -> Decimal:
        """The pullback's extreme so far (side +1: its lowest low)."""
        side = self.end.side
        values = [_far(m.bar, -side) for m in self.pullback(upto)]
        return min(values) if side > 0 else max(values)

    def live(self, upto: int) -> bool:
        """Whether no bar since the leg's end went beyond it: the pullback is still one."""
        side, marks = self.end.side, self.pullback(upto)
        beyond = any(_x(_far(m.bar, side), side) > _x(self.end.price, side) for m in marks)
        return bool(marks) and not beyond

    def quality(self, upto: int, lmax: int = 2, skip: frozenset[int] = frozenset()) -> bool:
        """PQ at bar `upto`: items 0 to 8 of section 1, those in `skip` dropped, LEG <= lmax."""
        if self.k < 3 or self.legs < 2 or not self.live(upto):  #: item 0, TR, never dropped
            return False
        checks = (self._impulse, self._strong, lambda _upto: self.legs <= lmax, self._calm)
        more = (self._calm_end, self._retrace, self._quiet, self._untested)
        return all(c(upto) for i, c in enumerate((*checks, *more), 1) if i not in skip)

    def _impulse(self, _upto: int) -> bool:
        """IMP: the setup leg holds a close outside K and an MX bar, toward the trend."""
        (start, end), side = self.leg(), self.end.side
        leg = self.chart.since(start.n, end.n)
        out = any(_x(m.bar.close, side) > _x(m.band(side), side) for m in leg)
        return out and any(m.mx == side for m in leg)

    def _strong(self, _upto: int) -> bool:
        """LS: the setup leg is at least as long as the with-trend leg before it."""
        (a, b), (c, d) = self.leg(), self.leg(1)
        return abs(b.price - a.price) >= abs(d.price - c.price)

    def _calm(self, upto: int) -> bool:
        """No DIV at the setup leg's end."""
        return not diverged(self.chart, self.k, upto)

    def _calm_end(self, upto: int) -> bool:
        """No CLX toward the trend in the last 10 bars."""
        return not climax(self.chart, self.end.side, upto)

    def _retrace(self, upto: int) -> bool:
        """The pullback retraces 25% to 75% of the setup leg."""
        start, end = self.leg()
        share = abs(end.price - self.low(upto)) / abs(end.price - start.price)
        return Decimal("0.25") <= share <= Decimal("0.75")

    def _quiet(self, upto: int) -> bool:
        """LA: the pullback's bars are smaller on average than the setup leg's."""
        start, end = self.leg()
        leg = _mean(m.range() for m in self.chart.since(start.n, end.n))
        return _mean(m.range() for m in self.pullback(upto)) < leg

    def _untested(self, upto: int) -> bool:
        """The pullback's support is tested fewer than 3 times."""
        return tested(self.pullback(upto), self.low(upto), self.end.side) < 3


def shared(marks: Sequence[Mark]) -> Decimal | None:
    """AG-01(a): OVER ATRb above a high the latest bar shares, within SHARED ATRb, with one or both
    of the 2 bars before it."""
    last = marks[-3:]
    if len(last) < 2:
        return None
    atr, ref = last[-1].atr, last[-1].bar.high
    group = [m.bar.high for m in last if abs(m.bar.high - ref) <= SHARED * atr]
    return max(group) + OVER * atr if len(group) >= 2 else None
