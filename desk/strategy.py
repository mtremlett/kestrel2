"""strategy - THE FIVE FROZEN DAILY STRATEGIES, chosen by the operator on 13 November 2026:
five textbook rules at their published settings, long only, untuned. A sixth, `ema_9_21`, is
a WIRING strategy (his request, 14 November): it is here to test the desk's wiring while the
ladder looks for real edge, it is listed apart (`WIRING`), and it is never an A-GATE candidate.

THE TEMPLATE. A strategy is a rule shown one bar at a time, after its close, that says whether
it wants to be in the market. It is never handed the series, so it cannot read a later bar. The
template turns each change of mind into a BUY or a SELL, and every other day into a HOLD. Each
rule starts out of the market, holds nothing until its indicators are full, and sees only bars.
SETTINGS. Each rule is made at its published settings unless `decide` is given others.

THE DECLARATION. Each rule says, before it is ever tested, what it is: its bar, the longest
it holds, the lines it is to be judged on and the numbers of the bar it reads (STR-03). It
has no word for a side: a rule is in a line or out of it, and the template sells only what
is held, so no rule can ask for a short sale, whatever it answers (STR-06). An order to
sell that any other hand writes is the gate's to refuse (`orders.gate`).
"""

from __future__ import annotations

import inspect
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from enum import Enum
from typing import ClassVar, Protocol

from desk.lines import LINES, Line
from desk.store import Bar
from desk.strategy_parts import ZERO as ZERO  # re-exported: callers import from here
from desk.strategy_parts import _Exponential as _Exponential
from desk.strategy_parts import _Wilder as _Wilder
from desk.strategy_parts import _Window as _Window
from desk.strategy_parts import lower_band as lower_band
from desk.strategy_parts import rsi as rsi

#: The one arithmetic every rule runs under, whatever is set: 28 digits, halves to even.
ARITHMETIC = Context(prec=28, rounding=ROUND_HALF_EVEN)


class Action(Enum):
    """What a strategy says of a line each day: no word for selling short, or for how many."""

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
    """The bar a strategy decides on: the desk keeps daily bars and no other."""

    DAILY = "daily"


class Field(Enum):
    """A number of the bar: the data a rule may read."""

    OPEN = "open"
    HIGH = "high"
    LOW = "low"
    CLOSE = "close"
    VOLUME = "volume"


#: What the rules read: the close alone, or the day's range with it.
CLOSES = frozenset({Field.CLOSE})
RANGES = frozenset({Field.HIGH, Field.LOW, Field.CLOSE})


@dataclass(frozen=True)
class Declared:
    """What a strategy says of itself before it is tested; the tests hold it to its rule."""

    bar: Timeframe
    #: The most sessions from its buy to its sale; None: no time limit of its own, as the five.
    hold: int | None
    #: The lines it is to be judged on: each of the five declares every line of the master.
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


class _Rsi2:
    """Connors' RSI-2 (Short Term Trading Strategies That Work, 2008): buy when the close is
    above its 200-day average and the 2-day RSI is under 5; sell on a close above the
    5-day average. The four numbers are its settings, those here the published ones."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, CLOSES)

    def __init__(
        self, length: int = 2, trend: int = 200, exit_length: int = 5, below: Decimal = Decimal(5)
    ) -> None:
        self._long, self._short, self._below = _Window(trend), _Window(exit_length), below
        self._gain, self._loss = _Wilder(length), _Wilder(length)
        self._last: Decimal | None = None

    def step(self, bar: Bar, holding: bool) -> bool:
        close, last, index = bar.close, self._last, None
        self._long.add(close)
        self._short.add(close)
        self._last = close
        if last is not None:
            gain = self._gain.add(max(close - last, ZERO))
            loss = self._loss.add(max(last - close, ZERO))
            if gain is not None and loss is not None:
                index = rsi(gain, loss)
        if holding:
            return close <= self._short.mean()
        return (
            index is not None
            and self._long.full
            and close > self._long.mean()
            and index < self._below
        )


class _Bollinger:
    """Bollinger's bands at his settings, 20 days and 2 deviations: buy a close under the
    lower band; sell a close over the middle, the 20-day average. Settings: the days and the
    width in deviations."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, CLOSES)

    def __init__(self, length: int = 20, width: Decimal = Decimal(2)) -> None:
        self._closes, self._width = _Window(length), width

    def step(self, bar: Bar, holding: bool) -> bool:
        self._closes.add(bar.close)
        if not self._closes.full:
            return False
        mean = self._closes.mean()
        if holding:
            return bar.close <= mean
        return bar.close < lower_band(mean, self._closes.deviation(), self._width)


class _Breakout:
    """The Turtles' system 1 (Faith, Way of the Turtle, 2007), on the close: buy a close over
    the highest high of the 20 days before; sell a close under the lowest low of the 10
    days before. Settings: the two lengths."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, RANGES)

    def __init__(self, entry: int = 20, exit_length: int = 10) -> None:
        self._highs, self._lows = _Window(entry), _Window(exit_length)

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
    one it saw, so it waits for the next. Settings: the two lengths."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, CLOSES)

    def __init__(self, fast: int = 50, slow: int = 200) -> None:
        self._fast, self._slow = _Window(fast), _Window(slow)
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
    under yesterday's lower band. Settings: the days and the multiple."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, RANGES)

    def __init__(self, length: int = 10, multiple: Decimal = Decimal(3)) -> None:
        self._range, self._multiple = _Wilder(length), multiple
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
            self._upper, self._lower = (
                middle + self._multiple * width,
                middle - self._multiple * width,
            )
            if last is not None and upper is not None and last < upper:
                self._upper = min(self._upper, upper)
            if last is not None and lower is not None and last > lower:
                self._lower = max(self._lower, lower)
        self._last = bar.close
        return wants


class _EmaCross:
    """The 9/21-day exponential cross, a WIRING strategy: buy the day the 9-day exponential
    average closes above the 21-day; sell the day it closes below. Level is neither. As with
    the 50/200, a cross that happened before both averages existed is not one it saw."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, CLOSES)

    def __init__(self) -> None:
        self._fast, self._slow = _Exponential(9), _Exponential(21)
        self._above: bool | None = None

    def step(self, bar: Bar, holding: bool) -> bool:
        fast, slow = self._fast.add(bar.close), self._slow.add(bar.close)
        if fast is None or slow is None:
            return False
        was, self._above = self._above, fast > slow
        return fast >= slow if holding else fast > slow and was is False


#: The five, by name, each with its declaration. A call makes a fresh rule that has seen nothing.
#: These, and no other, are the A-GATE's candidates: `ema_9_21` is not among them.
STRATEGIES: Mapping[str, type[Rule]] = {
    "rsi2_pullback": _Rsi2,
    "bollinger_pullback": _Bollinger,
    "breakout_20_10": _Breakout,
    "trend_50_200": _Trend,
    "supertrend_10_3": _Supertrend,
}

#: The WIRING strategies, listed apart from the five: rules kept to test the desk's wiring
#: end to end, tested as the five are, and NEVER A-GATE candidates, whatever they earn.
WIRING: Mapping[str, type[Rule]] = {"ema_9_21": _EmaCross}


#: The settings the grid may try, each rule's published one at the centre, its neighbours beside.
SWEEPS: Mapping[str, Mapping[str, tuple[int | Decimal, ...]]] = {
    "rsi2_pullback": {
        "length": (2, 3, 4),
        "trend": (150, 200, 250),
        "exit_length": (4, 5, 6),
        "below": (Decimal(3), Decimal(5), Decimal(10)),
    },
    "bollinger_pullback": {
        "length": (15, 20, 25),
        "width": (Decimal("1.5"), Decimal(2), Decimal("2.5")),
    },
    "breakout_20_10": {"entry": (15, 20, 25), "exit_length": (8, 10, 12)},
    "trend_50_200": {"fast": (40, 50, 60), "slow": (150, 200, 250)},
    "supertrend_10_3": {"length": (8, 10, 12), "multiple": (Decimal(2), Decimal(3), Decimal(4))},
}


def _variant(base: type[Rule], setting: Mapping[str, int | Decimal]) -> type[Rule]:
    """A no-argument maker of `base` at one setting, carrying its declaration."""

    class Variant(base):  # type: ignore[misc, valid-type]  # a Protocol class, made to be built
        def __init__(self) -> None:
            super().__init__(**setting)

    return Variant


#: Each rule at one other setting of its sweep, named `breakout_20_10[entry=15]`; listed apart
#: from STRATEGIES, so nothing here trades. The published setting is the rule's own name.
VARIANTS: Mapping[str, type[Rule]] = {
    f"{name}[{key}={value}]": _variant(STRATEGIES[name], {key: value})
    for name, grid in SWEEPS.items()
    for key, values in grid.items()
    for value in values
    if value != inspect.signature(STRATEGIES[name]).parameters[key].default
}


#: A rule's settings by argument name; any left out keep the published one. Lengths are whole
#: days (`int`); widths and multiples are `Decimal`.
Settings = Mapping[str, Mapping[str, int | Decimal]]


def _make(name: str, settings: Settings) -> Rule:
    """A fresh rule at its settings; a rule or an argument the desk does not have is refused."""
    if unknown := set(settings) - set(STRATEGIES):
        raise ValueError(f"settings for rules the desk does not have: {sorted(unknown)}")
    return STRATEGIES[name](**settings.get(name, {}))


def _run(
    name: str, rule: Rule, symbol: str, bars: Sequence[Bar], last: bool | None = None
) -> Iterator[Decision]:
    """The rule's decisions, holding what it last chose; on the last bar, holding `last`
    instead when it is given. A rule that declares a holding period is sold out of at its end,
    whatever it answered."""
    declared = getattr(rule, "declared", None)  #: test doubles of a Rule declare nothing
    holding, since, limit = False, 0, declared.hold if declared else None
    for n, bar in enumerate(bars):
        if last is not None and n == len(bars) - 1:
            holding = last
        wants = rule.step(bar, holding)
        since = since + 1 if holding else 0
        if limit is not None and since >= limit:  #: STP-11: out after the declared sessions
            wants = False
        #: a sale only of what is held, a buy only of what is not, whatever the rule answered
        sells, buys = holding and not wants, wants and not holding
        action = Action.SELL if sells else Action.BUY if buys else Action.HOLD
        holding = wants
        yield Decision(name, symbol, bar.day, action)


def decide(
    bars: Mapping[str, Sequence[Bar]], settings: Settings | None = None
) -> tuple[Decision, ...]:
    """A decision from every strategy for every line and day the bars cover."""
    given = settings or {}
    with localcontext(ARITHMETIC):
        return tuple(
            d
            for s, series in bars.items()
            for n in STRATEGIES
            for d in _run(n, _make(n, given), s, series)
        )


def today(
    bars: Mapping[str, Sequence[Bar]], held: Mapping[str, str], settings: Settings | None = None
) -> tuple[Decision, ...]:
    """Every strategy's decision on each line's last bar, its position read from the book:
    held names, for each line the book holds, the strategy that holds it. A rule the book
    holds nothing for may buy again after a stop or a refusal; one it holds for may sell."""
    given = settings or {}
    with localcontext(ARITHMETIC):
        return tuple(
            [*_run(name, _make(name, given), symbol, series, held.get(symbol) == name)][-1]
            for symbol, series in bars.items()
            for name in STRATEGIES
        )
