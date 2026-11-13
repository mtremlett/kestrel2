"""strategy - THE FIVE FROZEN DAILY STRATEGIES, chosen by the operator on 13 November 2026:
five textbook rules at their published settings, long only, untuned.

THE TEMPLATE. A strategy is a rule that is shown one bar at a time, after its close, and
says whether it wants to be in the market. It is never handed the series, so it cannot
read a later bar: being blind to the future is how it is built, not a promise it keeps.
The template turns each change of mind into a BUY or a SELL, and every other day into a
HOLD. Each rule starts out of the market and holds nothing until its indicators are full.
It sees only bars: never the clock, a vendor or the broker.

THE DECLARATION. Each rule says, before it is ever tested, what it is: its bar, the longest
it holds, the lines it is to be judged on and the numbers of the bar it reads (STR-03). It
has no word for a side: a rule is in a line or out of it, and the template sells only what
is held, so no rule can ask for a short sale, whatever it answers (STR-06). An order to
sell that any other hand writes is the gate's to refuse (`orders.gate`).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from enum import Enum
from typing import ClassVar, Protocol

from desk.lines import LINES, Line
from desk.store import Bar

ZERO = Decimal(0)
#: The one arithmetic every rule runs under, whatever the caller has set: 28 digits,
#: halves to even. A different setting elsewhere cannot move a decision.
ARITHMETIC = Context(prec=28, rounding=ROUND_HALF_EVEN)


class Action(Enum):
    """What a strategy says of a line each day. A sale is of what is held: there is no word
    for selling short, and none for how many."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass(frozen=True)
class Decision:
    strategy: str
    symbol: str
    day: date
    action: Action


class Timeframe(Enum):
    """The bar a strategy is shown and decides on. The desk keeps daily bars and no other."""

    DAILY = "daily"


class Field(Enum):
    """A number of the bar: the data a rule may read."""

    OPEN = "open"
    HIGH = "high"
    LOW = "low"
    CLOSE = "close"
    VOLUME = "volume"


#: What the five read: the close alone, or the day's range with it.
CLOSES = frozenset({Field.CLOSE})
RANGES = frozenset({Field.HIGH, Field.LOW, Field.CLOSE})


@dataclass(frozen=True)
class Declared:
    """What a strategy says of itself before it is tested. It moves no decision; the tests
    hold what it says of its data and its holding period to what its rule does on their series."""

    bar: Timeframe
    #: The most sessions from its buy to its sale. None: it has no time limit of its own; so
    #: each of the five, for no published rule of theirs has one.
    hold: int | None
    #: The lines it is to be judged on: the desk trades each of the five on every line of the
    #: instrument master, so each declares them all.
    universe: tuple[Line, ...]
    reads: frozenset[Field]  #: its data: the numbers of each bar it reads

    def __post_init__(self) -> None:
        if self.hold is not None and self.hold < 1:
            raise ValueError(f"a holding period of {self.hold} sessions")
        if not self.universe or len(set(self.universe)) != len(self.universe):
            raise ValueError("a test universe names at least one line, and none twice")
        if not self.reads:
            raise ValueError("a strategy reads at least one number of the bar")


class Rule(Protocol):
    declared: ClassVar[Declared]

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        ...


class _Window:
    """The last `size` values, with their running sum."""

    def __init__(self, size: int) -> None:
        self._values: deque[Decimal] = deque(maxlen=size)
        self._sum = ZERO

    def add(self, value: Decimal) -> None:
        if self.full:
            self._sum -= self._values[0]
        self._values.append(value)
        self._sum += value

    @property
    def full(self) -> bool:
        return len(self._values) == self._values.maxlen

    def mean(self) -> Decimal:
        return self._sum / len(self._values)

    def deviation(self) -> Decimal:
        """The population standard deviation, as Bollinger defines his bands."""
        mean = self.mean()
        return (sum(((v - mean) ** 2 for v in self._values), ZERO) / len(self._values)).sqrt()

    def high(self) -> Decimal:
        return max(self._values)

    def low(self) -> Decimal:
        return min(self._values)


class _Wilder:
    """Wilder's smoothing: the plain average of the first `size` values, then each new
    value weighted one part in `size`. None until it has `size` values."""

    def __init__(self, size: int) -> None:
        self._size, self._first = size, _Window(size)
        self.value: Decimal | None = None

    def add(self, value: Decimal) -> Decimal | None:
        if self.value is not None:
            self.value = (self.value * (self._size - 1) + value) / self._size
        else:
            self._first.add(value)
            self.value = self._first.mean() if self._first.full else None
        return self.value


class _Rsi2:
    """Connors' RSI-2 (Short Term Trading Strategies That Work, 2008): buy when the close is
    above its 200-day average and the 2-day RSI is under 5; sell on a close above the
    5-day average."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, CLOSES)

    def __init__(self) -> None:
        self._long, self._short = _Window(200), _Window(5)
        self._gain, self._loss = _Wilder(2), _Wilder(2)
        self._last: Decimal | None = None

    def step(self, bar: Bar, holding: bool) -> bool:
        close, last, rsi = bar.close, self._last, None
        self._long.add(close)
        self._short.add(close)
        self._last = close
        if last is not None:
            gain = self._gain.add(max(close - last, ZERO))
            loss = self._loss.add(max(last - close, ZERO))
            if gain is not None and loss is not None:
                rsi = Decimal(100) if loss == 0 else 100 - 100 / (1 + gain / loss)
        if holding:
            return close <= self._short.mean()
        return rsi is not None and self._long.full and close > self._long.mean() and rsi < 5


class _Bollinger:
    """Bollinger's bands at his settings, 20 days and 2 deviations: buy a close under the
    lower band; sell a close over the middle, the 20-day average."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, CLOSES)

    def __init__(self) -> None:
        self._closes = _Window(20)

    def step(self, bar: Bar, holding: bool) -> bool:
        self._closes.add(bar.close)
        if not self._closes.full:
            return False
        mean = self._closes.mean()
        if holding:
            return bar.close <= mean
        return bar.close < mean - 2 * self._closes.deviation()


class _Breakout:
    """The Turtles' system 1 (Faith, Way of the Turtle, 2007), on the close: buy a close over
    the highest high of the 20 days before; sell a close under the lowest low of the 10
    days before."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, RANGES)

    def __init__(self) -> None:
        self._highs, self._lows = _Window(20), _Window(10)

    def step(self, bar: Bar, holding: bool) -> bool:
        if holding:
            wants = bar.close >= self._lows.low()
        else:
            wants = self._highs.full and bar.close > self._highs.high()
        self._highs.add(bar.high)
        self._lows.add(bar.low)
        return wants


class _Trend:
    """The 50/200-day cross: buy the day the 50-day average closes above the 200-day; sell
    the day it no longer is. A cross that happened before both averages existed is not
    one it saw, so it waits for the next."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, CLOSES)

    def __init__(self) -> None:
        self._fast, self._slow = _Window(50), _Window(200)
        self._above: bool | None = None

    def step(self, bar: Bar, holding: bool) -> bool:
        self._fast.add(bar.close)
        self._slow.add(bar.close)
        if not self._slow.full:
            return False
        above, was = self._fast.mean() > self._slow.mean(), self._above
        self._above = above
        return above if holding else above and was is False


class _Supertrend:
    """Seban's Supertrend at 10 days and 3 times the average true range (Wilder's), with
    its bands carried as KivancOzbilgic's widely used TradingView script carries them, on
    the middle of the day's range: buy a close over yesterday's upper band; sell a close
    under yesterday's lower band."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, RANGES)

    def __init__(self) -> None:
        self._range = _Wilder(10)
        self._last: Decimal | None = None
        self._upper: Decimal | None = None
        self._lower: Decimal | None = None

    def step(self, bar: Bar, holding: bool) -> bool:
        last, upper, lower = self._last, self._upper, self._lower
        if holding:
            if lower is None:
                raise RuntimeError("supertrend: holding with no lower band, yet it bought")
            wants = bar.close >= lower
        else:
            wants = upper is not None and bar.close > upper
        spread = bar.high - bar.low
        if last is not None:
            spread = max(spread, abs(bar.high - last), abs(bar.low - last))
        width = self._range.add(spread)
        if width is not None:
            middle = (bar.high + bar.low) / 2
            self._upper, self._lower = middle + 3 * width, middle - 3 * width
            if last is not None and upper is not None and last < upper:
                self._upper = min(self._upper, upper)
            if last is not None and lower is not None and last > lower:
                self._lower = max(self._lower, lower)
        self._last = bar.close
        return wants


#: The five, by name, each with its declaration. Each call makes a fresh rule that has seen
#: nothing.
STRATEGIES: Mapping[str, type[Rule]] = {
    "rsi2_pullback": _Rsi2,
    "bollinger_pullback": _Bollinger,
    "breakout_20_10": _Breakout,
    "trend_50_200": _Trend,
    "supertrend_10_3": _Supertrend,
}


def _run(
    name: str, rule: Rule, symbol: str, bars: Sequence[Bar], last: bool | None = None
) -> Iterator[Decision]:
    """The rule's decisions, holding what it last chose; on the last bar, holding `last`
    instead when it is given."""
    holding = False
    for n, bar in enumerate(bars):
        if last is not None and n == len(bars) - 1:
            holding = last
        wants = rule.step(bar, holding)
        #: a sale only of what is held, a buy only of what is not, whatever the rule answered
        sells, buys = holding and not wants, wants and not holding
        action = Action.SELL if sells else Action.BUY if buys else Action.HOLD
        holding = wants
        yield Decision(name, symbol, bar.day, action)


def decide(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """A decision from every strategy for every line and every day the bars cover."""
    with localcontext(ARITHMETIC):
        return tuple(
            decision
            for symbol, series in bars.items()
            for name, make in STRATEGIES.items()
            for decision in _run(name, make(), symbol, series)
        )


def today(bars: Mapping[str, Sequence[Bar]], held: Mapping[str, str]) -> tuple[Decision, ...]:
    """Every strategy's decision on each line's last bar, its position read from the book:
    held names, for each line the book holds, the strategy that holds it. A rule the book
    holds nothing for may buy again after a stop or a refusal; one it holds for may sell."""
    with localcontext(ARITHMETIC):
        return tuple(
            [*_run(name, make(), symbol, series, held.get(symbol) == name)][-1]
            for symbol, series in bars.items()
            for name, make in STRATEGIES.items()
        )
