"""grimes - ADAM GRIMES'S SETUPS, A MACHINERY TEST ON PAPER (his ruling, 22 November 2026): the
catalogue (kestrel2_research/grimes/catalogue.md v3, review 9.8), *The Art and Science of Technical
Analysis* (2012) at its defaults, long only, daily, under the one engine (`desk.strategy`): blocks
(section 1) worked once a bar by `Chart` and `Setup`, MGMT (section 2) by `Trade`. A resting order
is a bar trading through its level, filled next open; one share: partials sell nothing; sizing
by risk, the jitter's symbol, weekly contexts, shorts and sweeps are the ladder's. NEVER EVIDENCE:
none is in STRATEGIES or the ladder's book; only the ladder judges (CANON B6)."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from itertools import pairwise
from statistics import median
from typing import ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import RANGES, Declared, Field, Timeframe
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
        while self.pivots and self.pivots[0].n < self.marks[0].n:  #: none outlives its bar
            self.pivots.popleft()
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
    if not prior or _x(end.price, side) <= _x(prior[0].price, side):
        return False  #: DIV needs a new swing extreme in price
    if _x(end.fast, side) > _x(prior[0].fast, side):
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


@dataclass
class Trade:
    """MGMT (section 2), long: one position from the open after its signal to its exit. A stop
    never widens; the stop counts first when a bar reaches both it and a target."""

    stop: Decimal
    limit: int  #: T: out if +1R is not touched by the close of bar T after entry
    first: Decimal = FIRST  #: partial 1, at +1R
    floor: Decimal | None = None  #: a close under it is out (AG-04: the breakout failed)
    start: Decimal | None = None  #: AG-05: no time stop until a close over this level
    back: Decimal | None = None  #: the fakeout re-entry's level: a close back over it
    entry: Decimal | None = None
    risk: Decimal = ZERO
    best: Decimal = ZERO
    bars: int = 0
    left: Decimal = Decimal(1)
    touched: bool = False
    stopped: bool = False
    free: int = 0

    def step(self, mark: Mark) -> bool:
        """The next bar after its close: whether the position is still held."""
        bar = mark.bar
        if self.entry is None:
            self.entry, self.best, self.risk = bar.open, bar.open, bar.open - self.stop
        if self.risk <= 0 or bar.low <= self.stop:
            self.stopped = True
            return False
        self.bars += 1
        if self.start is not None and bar.close > self.start:
            self.start, self.bars = None, 0
        self._manage(mark)
        out = self.floor is not None and bar.close < self.floor
        late = self.start is None and not self.touched and self.bars >= self.limit
        return not (out or late)

    def _manage(self, mark: Mark) -> None:
        """Partials, breakeven, the chandelier on the remainder and the parabolic stop."""
        bar, entry = mark.bar, self.entry or ZERO
        if not self.touched and bar.high > entry + self.risk:
            self.touched, self.left = True, self.left - self.first
            self._raise(entry - JITTER * mark.atr)
        if bar.high > entry + 2 * self.risk:
            self.left = min(self.left, THIRD)
        self.best = max(self.best, bar.close)
        if self.left <= THIRD:
            self._raise(self.best - CHANDELIER * mark.atr)
        self.free += mark.free(1)
        if self.free >= 2:
            self._raise(bar.low)

    def _raise(self, level: Decimal) -> None:
        """Move the stop up to the level, never down."""
        self.stop = max(self.stop, level)


class Grimes:
    """The template of the ten: a chart worked every bar, a setup's Trade when it fires, MGMT
    until it ends. A line the book holds that this replay never bought is sold (`holding` with
    no trade); a trade the book never took (not `holding`) is forgotten."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, BARS)
    code: ClassVar[str] = ""
    limit: ClassVar[int] = 5
    first: ClassVar[Decimal] = FIRST
    narrow: ClassVar[bool] = False  #: whether the min-stop filter applies

    def __init__(self) -> None:
        self.chart = Chart()
        self.trade: Trade | None = None
        self._armed: tuple[Decimal, Decimal] | None = None
        self._back: tuple[Decimal, int] | None = None

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        mark = self.chart.add(bar)
        if mark is None:
            return False
        if holding and self.trade is None:
            return False
        if holding and self.trade is not None:
            if self.trade.step(mark) and self.keep(mark):
                return True
            if self.trade.stopped and self.trade.back is not None:
                self._back = (self.trade.back, mark.n)
        self.trade = self._again(mark) or self.signal(mark)
        return self.trade is not None

    def _again(self, mark: Mark) -> Trade | None:
        """MGMT's fakeout re-entry, once: a close back over the level on the stop's bar or the
        next, its stop beyond the new extreme."""
        back, self._back = self._back, None
        if back is None or mark.n - back[1] > 1:
            return None
        if mark.bar.close <= back[0]:
            self._back = back if mark.n == back[1] else None
            return None
        low = min(m.bar.low for m in self.chart.since(back[1] - 1))
        return self.open(self.stop(low, mark))

    def keep(self, _mark: Mark) -> bool:
        """A rule's own exit beside MGMT's; none unless it says."""
        return True

    def signal(self, mark: Mark) -> Trade | None:
        """A trade from the order armed at the bar before, when this bar trades through it; then
        the order for the next bar armed."""
        armed, self._armed = self._armed, self.arm(mark)
        if armed is None or mark.bar.high <= armed[0] or mark.bar.low <= armed[1]:
            return None
        self._armed = None
        return self.open(armed[1])

    def arm(self, _mark: Mark) -> tuple[Decimal, Decimal] | None:
        """The buy-stop for the next bar and its stop, if the setup holds at this one."""
        return None

    def open(self, stop: Decimal, **more: Decimal | None) -> Trade:
        """MGMT's trade for this rule from its stop."""
        return Trade(stop, self.limit, self.first, **more)  # type: ignore[arg-type]

    def stop(self, level: Decimal, mark: Mark) -> Decimal:
        """The initial stop beyond a structural low: BUFFER ATRb and a jitter of up to JITTER ATRb,
        seeded from the rule's code and the day, so runs reproduce."""
        seed = int(sha256(f"{self.code}{mark.bar.day}".encode()).hexdigest()[:8], 16) % 1001
        return level - (BUFFER + JITTER * seed / 1000) * mark.atr

    def room(self, entry: Decimal, stop: Decimal, mark: Mark) -> bool:
        """The min-stop filter, where the rule applies it: a stop under MIN_STOP ATRb skips."""
        return not self.narrow or entry - stop >= MIN_STOP * mark.atr


def _pivot(chart: Chart, side: int, back: int = 0) -> Setup | None:
    """The setup whose leg ends at the latest pivot on that side (`back` more before it)."""
    k = chart.last(side, back)
    return None if k is None else Setup(chart, k)


def _anchor(chart: Chart) -> Setup | None:
    """The setup whose leg ends at the latest higher high: a pullback's own bounces skipped."""
    p = chart.pivots
    highs = [i for i, pivot in enumerate(p) if pivot.side > 0]
    found = [b for a, b in pairwise(highs) if p[b].price > p[a].price]
    return Setup(chart, found[-1]) if found else None


class _Ag01(Grimes):
    """AG-01, the pullback bought on a breakout [ch6] [ch10]: PQ holds on a simple pullback (no
    high pivot inside it); a buy-stop OVER ATRb above a high 2-3 pullback bars share (trigger a);
    the stop beyond the pullback's low; the min-stop filter on; T = 5."""

    code, narrow = "AG-01", True

    def arm(self, mark: Mark) -> tuple[Decimal, Decimal] | None:
        """AG-01(a)'s buy-stop while PQ holds."""
        setup = _pivot(self.chart, 1)
        if setup is None or not setup.quality(mark.n):
            return None
        trigger = shared(setup.pullback(mark.n))
        stop = self.stop(setup.low(mark.n), mark)
        return (trigger, stop) if trigger and self.room(trigger, stop, mark) else None


class _Ag02(Grimes):
    """AG-02, a wash-out of the pullback's support bought [ch6] [ch3]: PQ holds at the bar before;
    the boundary is the last confirmed pivot low inside the pullback (a bounce made it); a bar
    trading under it and closing back over it (w = 1) buys at the next open; the stop beyond the
    wash-out's low; a boundary tested 3 times or more is skipped; the min-stop filter on; T = 5."""

    code, narrow = "AG-02", True

    def signal(self, mark: Mark) -> Trade | None:
        """The wash-out's close back over the boundary."""
        setup, k = _anchor(self.chart), self.chart.last(-1)
        if setup is None or k is None or k < setup.k or not setup.quality(mark.n - 1):
            return None
        boundary = self.chart.pivots[k]
        before = self.chart.since(boundary.n, mark.n - 1)
        if tested(before, boundary.price, 1) >= 3:
            return None
        if not mark.bar.low < boundary.price < mark.bar.close:
            return None
        stop = self.stop(mark.bar.low, mark)
        return self.open(stop) if self.room(mark.bar.close, stop, mark) else None


class _Ag03(Grimes):
    """AG-03, the complex (two-legged) pullback [ch6] [ch10]: legs AB down, BC up, CD down; PQ
    items 0-2, 4, 7 and 8 at A with LEG <= 5, a climax allowed; in the D zone (CD/AB in 0.8 to
    1.25) AG-01(a)'s buy-stop; the stop just beyond D; no min-stop filter; partial 1 is 25%."""

    code, first = "AG-03", Decimal("0.25")

    def arm(self, mark: Mark) -> tuple[Decimal, Decimal] | None:
        """AG-01(a)'s buy-stop in the D zone of a complex pullback."""
        setup, last = _pivot(self.chart, 1, 1), _pivot(self.chart, 1)
        if setup is None or last is None or last.k != setup.k + 2:
            return None
        a, b, c = setup.end, self.chart.pivots[setup.k + 1], last.end
        if c.price >= a.price or not last.live(mark.n):
            return None
        d = last.low(mark.n)
        if not Decimal("0.8") <= (c.price - d) / (a.price - b.price) <= Decimal("1.25"):
            return None
        if not setup.quality(mark.n, 5, frozenset({5, 6})):
            return None
        trigger = shared(last.pullback(mark.n))
        return (trigger, self.stop(d, mark)) if trigger else None


def level(chart: Chart, side: int, mark: Mark) -> tuple[Decimal, int] | None:
    """AG-04's level (side +1: a resistance) at a bar, from the bars before it: the latest swing
    price tested twice or more within NEAR ATRb (its run of matching pivots) over 20 bars or more,
    with 2 closes or fewer beyond it; and the bar of its first test."""
    ends = [p for p in chart.pivots if p.side == side]
    if not ends:
        return None
    tests = [p for p in ends if abs(p.price - ends[-1].price) <= NEAR * mark.atr]
    first = tests[0].n
    beyond = sum(
        _x(m.bar.close, side) > _x(ends[-1].price, side) for m in chart.since(first, mark.n - 1)
    )
    if len(tests) < 2 or mark.n - first < 20 or beyond > 2:
        return None
    return ends[-1].price, first


def thrust(chart: Chart, side: int, mark: Mark) -> Decimal | None:
    """The first close beyond AG-04's level toward the side: the level it broke, else None."""
    found, before = level(chart, side, mark), chart.since(mark.n - 2, mark.n - 1)
    if found is None or not before or _x(mark.bar.close, side) <= _x(found[0], side):
        return None
    return None if _x(before[0].bar.close, side) > _x(found[0], side) else found[0]


def _wide(chart: Chart, mark: Mark) -> Decimal:
    """The bar's range over the mean range of the 10 bars before it."""
    before = chart.since(mark.n - 11, mark.n - 1)
    return mark.range() / (_mean(m.range() for m in before) or Decimal(1))


class _Ag04(Grimes):
    """AG-04, the first pullback after a breakout [ch5] [ch6]: a close over AG-04's level on a bar
    1.25 times the mean range (r); the first reaction retracing 50% (x) or less of the thrust, then
    AG-01(a)'s buy-stop; the stop beyond the reaction's low; out on a close under the base's last
    pivot low (the breakout failed); the min-stop filter on; T = 5."""

    code, narrow = "AG-04", True

    def __init__(self) -> None:
        super().__init__()
        self._run: tuple[Decimal, Decimal, int] | None = None  #: the base's floor, low, top bar

    def arm(self, mark: Mark) -> tuple[Decimal, Decimal] | None:
        """The breakout's first reaction's buy-stop."""
        k = self.chart.last(-1)
        if thrust(self.chart, 1, mark) and _wide(self.chart, mark) >= Decimal("1.25") and k:
            self._run = (self.chart.pivots[k].price, mark.bar.low, mark.n)
            return None
        if self._run is None:
            return None
        floor, low, top = self._run
        after = self.chart.since(top - 1, mark.n)
        high = max(after, key=lambda m: m.bar.high)
        reaction = self.chart.since(high.n, mark.n)
        dip = min((m.bar.low for m in reaction), default=high.bar.high)
        if high.bar.high - dip > (high.bar.high - low) / 2:
            self._run = None
            return None
        trigger = shared(reaction)
        stop = self.stop(dip, mark)
        return (trigger, stop) if trigger and self.room(trigger, stop, mark) else None

    def open(self, stop: Decimal, **more: Decimal | None) -> Trade:
        """MGMT's trade, out on a close under the base's last pivot low; the first reaction only."""
        floor, self._run = (self._run or (None,))[0], None
        return super().open(stop, floor=floor, **more)


def tight(chart: Chart, mark: Mark) -> tuple[Decimal, Decimal] | None:
    """AG-05's tight base at a bar: a run of 3 bars or more [P] whose lows sit in the top quarter
    of the 20-bar range, under a top the range's first half touched; 2 closes or fewer over the
    top. Its low and the top (the level)."""
    marks = chart.since(mark.n - 20, mark.n)
    if len(marks) < 20:
        return None
    top, bottom = max(m.bar.high for m in marks), min(m.bar.low for m in marks)
    edge = top - (top - bottom) / 4
    run = [m for m in marks if m.n > max((x.n for x in marks if x.bar.low < edge), default=-1)]
    early = any(m.bar.high >= edge for m in marks[:10])
    over = sum(m.bar.close > top for m in marks)
    if len(run) < 3 or not early or over > 2:
        return None
    return min(m.bar.low for m in run), top


class _Ag05(Grimes):
    """AG-05, the breakout entered in its base [ch5] [ch6]: a tight base; a spring (a probe under
    its low closing back inside, trigger a) buys at the next open; stop plan A, BUFFER ATRb under
    the base low, with MGMT's fakeout re-entry; no time stop until a close over the level, then
    T = 5."""

    code = "AG-05"

    def __init__(self) -> None:
        super().__init__()
        self._base: tuple[Decimal, Decimal] | None = None

    def signal(self, mark: Mark) -> Trade | None:
        """The spring under the base standing at the bar before."""
        base, self._base = self._base, tight(self.chart, mark)
        if base is None or not mark.bar.low < base[0] < mark.bar.close:
            return None
        return self.open(self.stop(base[0], mark), start=base[1], back=base[0])


def ncl(chart: Chart) -> int:
    """NCL: the median length in bars of the last 5 swings [P: the book's pullbacks, any swing]."""
    lengths = [bars for _, bars, _ in chart.swings()][-6:-1]
    return int(median(lengths)) if lengths else KEEP


def context(chart: Chart, k: int, mark: Mark) -> bool:
    """AG-06's context at the low pivot k, any of: (i) LEG 3 or more down with DIV; (ii) a
    consolidation just over it (closes within REACH + 1 ATRb) for 3 NCL bars or more; (iii) it
    is a CLX's extreme; (iv) a CoC up since it. The higher timeframe's (v, vi) are the ladder's."""
    low, setup = chart.pivots[k], Setup(chart, k)
    after = chart.since(low.n, mark.n - 1)
    just = all(m.bar.close - low.price <= (REACH + 1) * m.atr for m in after)
    held = all(m.bar.low >= low.price for m in after) and len(after) >= 3 * ncl(chart)
    return (
        (setup.legs >= 3 and diverged(chart, k, mark.n - 1))
        or (just and held)
        or climax(chart, -1, low.n)
        or (chart.last(1) is not None and chart.last(1) > k and coc(chart, 1))  # type: ignore[operator]
    )


class _Ag06(Grimes):
    """AG-06, the failure test (spring, the "2B") [ch6] [ch10]: at the latest confirmed swing low in
    one of the contexts, a bar trading under it and closing back over it buys at the next open;
    the stop BUFFER ATRb beyond the probe; out after 2 closes running within 0.5 ATRb of the level
    before +0.5R; MGMT's fakeout re-entry always on; T = 3."""

    code, limit = "AG-06", 3

    def __init__(self) -> None:
        super().__init__()
        self._level, self._near = ZERO, 0

    def signal(self, mark: Mark) -> Trade | None:
        """The probe under the level that closes back over it, in context."""
        k = self.chart.last(-1)
        if k is None or not context(self.chart, k, mark):
            return None
        price = self.chart.pivots[k].price
        if not mark.bar.low < price < mark.bar.close:
            return None
        self._level, self._near = price, 0
        return self.open(self.stop(mark.bar.low, mark), back=price)

    def keep(self, mark: Mark) -> bool:
        """Out on 2 closes running near the level before +0.5R: it must work fast."""
        trade = self.trade
        if trade is None or trade.entry is None:
            return True
        reached = trade.best >= trade.entry + trade.risk / 2
        near = abs(mark.bar.close - self._level) <= mark.atr / 2
        self._near = self._near + 1 if near and not reached else 0
        return self._near < 2


#: The coded setups by name: the zoo's names are `zoo_<name>` (desk/intraday.py ZOO).
GRIMES: dict[str, type[Grimes]] = {
    "ag01_pullback_breakout": _Ag01,
    "ag02_washout": _Ag02,
    "ag03_complex_pullback": _Ag03,
    "ag04_first_pullback": _Ag04,
    "ag05_base_spring": _Ag05,
    "ag06_failure_test": _Ag06,
}
