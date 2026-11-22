"""intraday - THE ONE ENGINE, INTRADAY (R-RUNNER-199, his ruling of 16 November 2026): a rule
declares the span of the bar it decides on, and is shown one bar at a time, after its close,
only the bars of its venue's session; a bar outside the session, or of another span, is
refused, never skipped. The template is strategy.py's: a change of mind is a BUY or a SELL,
every other bar a HOLD, and only what is held is sold. `run` is the backtest; `latest` is the
desk's step at one bar, the rule worked up to it with the position the book holds. The two
agree bar for bar (the parity test), and no rule here trades until it passes the ladder."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import ClassVar, Protocol

from desk import bars, rollup, venues
from desk import eponymous_bands as bands
from desk import eponymous_bollinger_squeeze as squeeze
from desk import eponymous_breakouts as breakouts
from desk import eponymous_clenow_momentum as clenow
from desk import eponymous_connors as connors
from desk import eponymous_connors_three_day_high_low as three_day
from desk import eponymous_faber_tactical as faber
from desk import eponymous_keltner_channel_trend as keltner
from desk import eponymous_momentum as momentum
from desk import eponymous_raschke_swing as raschke
from desk import eponymous_williams_r as williams
from desk.grimes import GRIMES
from desk.lines import LINES, Line
from desk.rollup import Candle
from desk.spans import Five, Timed
from desk.strategy import WIRING, Action, Rule
from desk.strategy_parts import ZERO, _Exponential, _Wilder, rsi


class Span(Enum):
    """The bar an intraday rule decides on, as minutes."""

    ONE_MINUTE = 1
    FIVE_MINUTES = 5
    FIFTEEN_MINUTES = 15  #: rolled from the session's five-minute bars, never asked for apart


@dataclass(frozen=True)
class IntradayDecision:
    """What a rule said of a line on one bar."""

    strategy: str
    symbol: str
    at: datetime  #: when the bar decided on began, timezone-aware UTC
    action: Action


class IntradayRule(Protocol):
    """A rule shown one bar at a time, declaring the span it decides on."""

    span: ClassVar[Span]

    def step(self, bar: Candle, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        ...


def _checked(venue: str, span: Span, bars: Sequence[Candle]) -> None:
    """Refuse a bar that is not whole, in time order, inside one session of the venue."""
    last: datetime | None = None
    for bar in bars:
        found = venues.open_at(venue, bar.start)
        length = timedelta(minutes=span.value)
        if found is None or not found.open <= bar.start <= found.close - length:
            raise ValueError(f"{bar.start}: not a {span.value}-minute bar in {venue}'s session")
        if last is not None and bar.start <= last:
            raise ValueError(f"{bar.start}: not after the bar before it, {last}")
        last = bar.start


def _closing(venue: str, span: Span, bar: Candle) -> bool:
    """Whether the bar is one of the session's last two: a day-trading rule (`flat`) is sold at
    the close of the second-last, so its sale meets an open market, and buys nothing after."""
    found = venues.open_at(venue, bar.start)
    return found is not None and bar.start >= found.close - 2 * timedelta(minutes=span.value)


def session(path: Path, line: Line, span: Span, day: date) -> tuple[Candle, ...]:
    """One venue session's bars of the span the store holds for the line, from the open up to
    the close, as candles in time order; a span the store never held raises its LookupError."""
    found = venues.hours(line.venue, day)
    if span is Span.ONE_MINUTE:
        held: Sequence[Five | Timed] = bars.timed(path, line, "1m", found.open, found.close)
    else:
        held = bars.five(path, line, found.open, found.close)
    made = tuple(Candle(b.start, b.open, b.high, b.low, b.close, b.volume, "store") for b in held)
    if span is Span.FIFTEEN_MINUTES:
        made = tuple(rollup.rollup(line.venue, list(made), "15m", "5m"))
    _checked(line.venue, span, made)
    return made


def run(
    name: str,
    rule: IntradayRule,
    venue: str,
    symbol: str,
    bars: Sequence[Candle],
    last: bool | None = None,
) -> Iterator[IntradayDecision]:
    """The rule's decision on every bar, holding what it last chose; on the last bar,
    holding `last` instead when it is given."""
    _checked(venue, rule.span, bars)
    holding, flat = False, getattr(rule, "flat", False)  #: test doubles declare no `flat`
    for n, bar in enumerate(bars):
        if last is not None and n == len(bars) - 1:
            holding = last
        wants = rule.step(bar, holding) and not (flat and _closing(venue, rule.span, bar))
        action = (
            Action.SELL
            if holding and not wants
            else Action.BUY
            if wants and not holding
            else Action.HOLD
        )
        holding = wants
        yield IntradayDecision(name, symbol, bar.start, action)


def latest(
    name: str,
    make: Callable[[], IntradayRule],
    venue: str,
    symbol: str,
    bars: Sequence[Candle],
    held: bool,
) -> IntradayDecision:
    """The desk's step at the last bar: a fresh rule worked up the bars to it, the position
    on that bar read from the book (`held`), not from the rule."""
    return [*run(name, make(), venue, symbol, bars, held)][-1]


#: The intraday rules the desk may trade: none, until one passes the ladder.
RULES: Mapping[str, Callable[[], IntradayRule]] = {}


def today(
    venue: str,
    bars: Mapping[str, Sequence[Candle]],
    held: Mapping[str, str],
    rules: Mapping[str, Callable[[], IntradayRule]] = RULES,
) -> tuple[IntradayDecision, ...]:
    """Every rule's decision at each line's last bar, as `strategy.today` does for the day:
    the position read from `held` (line to the rule holding it), a line with no bars skipped."""
    return tuple(
        latest(name, make, venue, symbol, series, held.get(symbol) == name)
        for symbol, series in bars.items()
        if series
        for name, make in rules.items()
    )


# THE ZOO (the operator, 21 November 2026): thirty textbook rules kept as MACHINERY, NOT EDGE,
# to exercise the desk on every regime and on daily, 15- and 5-minute bars while the ladder
# looks for edge. None is in STRATEGIES or RULES; none reaches money without the whole ladder.
GAP = Decimal("0.01")  #: a gap: the session opens a hundredth or more from the last close
STRETCH = Decimal("0.005")  #: the VWAP scalp buys a close this share under the session's VWAP


class Regime(Enum):
    """The market a zoo rule is written for."""

    TREND = "trend"
    MEAN_REVERSION = "mean reversion"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    RANGE = "range"
    GAPPER = "morning gapper"
    SCALP = "scalp"


class _Day:
    """A day-trading rule: five-minute bars, sold before the close (`flat`), its memory reset
    each session but for the last close of the session before, so a backtest over many days
    and the desk's step over the day before and this one decide alike. A session whose first
    bar is not its venue's opening one is not `whole`, and the session before counts only if
    it was the venue's last: a gap in the store never passes for the open or a gap up."""

    span: ClassVar[Span] = Span.FIVE_MINUTES
    flat: ClassVar[bool] = True

    def __init__(self) -> None:
        self.day: date | None = None
        self.before: Decimal | None = None  #: the session before's last close
        self.whole = False  #: whether this session's first bar is its venue's opening bar
        self.last: Decimal | None = None
        self.first = Candle(datetime.min, ZERO, ZERO, ZERO, ZERO, 0, "")  #: each session's first

    def see(self, bar: Candle) -> bool:
        """Take the bar in; whether it opens a session (and the rule's memory is reset)."""
        day, fresh = bar.start.date(), bar.start.date() != self.day
        if fresh:
            venue = next((v for v in venues.RULES if _opens(v, bar.start)), "")
            past = venue and venues.sessions(venue, day - timedelta(14), day - timedelta(1))
            self.whole = bool(venue)
            self.before = self.last if past and past[-1] == self.day else None
            self.day, self.first = day, bar
            self.reset()
        self.last = bar.close
        return fresh

    def reset(self) -> None:
        """Forget the last session's indicators; the rules that keep none keep this."""


def _opens(venue: str, start: datetime) -> bool:
    """Whether a bar starting then is the venue's opening bar of a day it trades."""
    day = start.date()
    return venues.sessions(venue, day, day) == (day,) and venues.hours(venue, day).open == start


class _OpeningRange(_Day):
    """Crabel's opening range breakout (1990) on 15-minute bars: buy a close over the first
    bar's high; sell a close under its low."""

    span: ClassVar[Span] = Span.FIFTEEN_MINUTES

    def step(self, bar: Candle, holding: bool) -> bool:
        if self.see(bar) or not self.whole:
            return False
        return bar.close >= self.first.low if holding else bar.close > self.first.high


class _GapAndGo(_Day):
    """Gap and go: a session opened a gap up (`GAP`); buy a close over the first bar's high,
    sell a close under its low."""

    def step(self, bar: Candle, holding: bool) -> bool:
        if self.see(bar) or self.before is None or self.first.open < self.before * (1 + GAP):
            return False
        return bar.close >= self.first.low if holding else bar.close > self.first.high


class _GapFade(_Day):
    """Gap fill: a session opened a gap down whose first bar closes up; buy that close, sell
    when a close fills the gap to the last session's close or breaks the first bar's low."""

    def step(self, bar: Candle, holding: bool) -> bool:
        fresh, before, first = self.see(bar), self.before, self.first
        if before is None or first.open > before * (1 - GAP) or first.close <= first.open:
            return False  #: `before` is None too when the session is not whole
        return before > bar.close >= first.low if holding else fresh


class _VwapReversion(_Day):
    """VWAP reversion scalp: buy a close `STRETCH` under the session's volume-weighted average
    price, sell a close back at it."""

    def reset(self) -> None:
        self._paid, self._volume = ZERO, 0

    def step(self, bar: Candle, holding: bool) -> bool:
        self.see(bar)
        self._paid += (bar.high + bar.low + bar.close) / 3 * bar.volume
        self._volume += bar.volume
        if not self._volume:
            return False
        vwap = self._paid / self._volume
        return bar.close < vwap if holding else bar.close <= vwap * (1 - STRETCH)


class _MicroPullback(_Day):
    """Micro pullback scalp: while the 9-bar exponential average is over the 21-bar, buy a bar
    that dips to the 9 and closes over it; sell a close under the 21."""

    def reset(self) -> None:
        self._fast, self._slow = _Exponential(9), _Exponential(21)

    def step(self, bar: Candle, holding: bool) -> bool:
        self.see(bar)
        was = self._fast.value
        fast, slow = self._fast.add(bar.close), self._slow.add(bar.close)
        if fast is None or slow is None or was is None:
            return False
        if holding:
            return bar.close >= slow
        return fast > slow and bar.low <= was < bar.close


class _Rsi2Scalp(_Day):
    """Connors' RSI(2) taken to five-minute bars: in a session trading over its open, buy a
    2-bar RSI under 10; sell it over 70."""

    def reset(self) -> None:
        self._gain, self._loss = _Wilder(2), _Wilder(2)

    def step(self, bar: Candle, holding: bool) -> bool:
        prior = self.last
        if self.see(bar) or prior is None:  #: a session's RSI starts at its first bar
            return False
        gain = self._gain.add(max(bar.close - prior, ZERO))
        loss = self._loss.add(max(prior - bar.close, ZERO))
        if gain is None or loss is None:
            return False
        index = rsi(gain, loss)
        return index <= 70 if holding else index < 10 and self.whole and bar.close > self.first.open


class _EmaCross(_Day):
    """The 9/21 exponential cross on five-minute bars: buy the cross up it saw, sell the cross
    down."""

    def reset(self) -> None:
        self._fast, self._slow = _Exponential(9), _Exponential(21)
        self._above: bool | None = None

    def step(self, bar: Candle, holding: bool) -> bool:
        self.see(bar)
        fast, slow = self._fast.add(bar.close), self._slow.add(bar.close)
        if fast is None or slow is None:
            return False
        was, self._above = self._above, fast > slow
        return fast >= slow if holding else fast > slow and was is False


@dataclass(frozen=True)
class Machine:
    """One zoo rule, MACHINERY NOT EDGE: its name, the regime it is for, its bar (None: the
    daily bar, decided by `desk.strategy`'s engine; a span: this one's), its maker, source."""

    name: str
    regime: Regime
    span: Span | None
    rule: type[Rule] | type[_Day]
    source: str

    def __post_init__(self) -> None:
        if getattr(self.rule, "span", None) is not self.span:
            raise ValueError(f"{self.name}: declared {self.span}, its rule decides on another bar")


_FILES = (bands, squeeze, breakouts, clenow, connors, three_day, faber, keltner, momentum, raschke)
#: The desk's daily rules the zoo may name: the wiring rule and the eponymous files' rules.
_DAILY: Mapping[str, type[Rule]] = {
    **WIRING,
    **{name: rule for file in (*_FILES, williams) for name, rule in file.EPONYMOUS.items()},
    **GRIMES,  #: Grimes's ten setups (desk/grimes.py), a MACHINERY TEST since his 22 Nov ruling
}


def _daily(name: str, regime: Regime, source: str) -> Machine:
    """A daily rule of the desk's, by its own name, taken into the zoo."""
    return Machine(f"zoo_{name}", regime, None, _DAILY[name], source)


def _intraday(name: str, regime: Regime, rule: type[_Day], source: str) -> Machine:
    """A day-trading rule of the zoo's own, on the bar it declares."""
    return Machine(f"zoo_{name}", regime, rule.span, rule, source)


_T, _MR, _MO, _V, _R = (
    Regime.TREND,
    Regime.MEAN_REVERSION,
    Regime.MOMENTUM,
    Regime.VOLATILITY,
    Regime.RANGE,
)
_G, _S = Regime.GAPPER, Regime.SCALP
#: The twenty, their sources cited in full on the pull request that chose them (21 November 2026);
#: then Grimes's ten (22 November 2026), each a setup of his catalogue's section 3.
ZOO: tuple[Machine, ...] = (
    _daily("ema_9_21", _T, "the 9/21 exponential cross, the desk's wiring rule"),
    _daily("donchian_channel_breakout", _T, "Faith, Way of the Turtle (2007)"),
    _daily("faber_tactical", _T, "Faber (2007), the 10-month average"),
    _daily("keltner_channel_trend", _V, "Keltner (1960), average true range bands"),
    _daily("bollinger_squeeze", _V, "Bollinger on Bollinger Bands (2001)"),
    _daily("connors_rsi2", _MR, "Connors and Alvarez (2008)"),
    _daily("williams_r", _MR, "Williams (1973), %R"),
    _daily("connors_three_day_high_low", _MR, "Connors and Alvarez (2008)"),
    _daily("donchian_fade_chop", _R, "a Donchian channel faded in a range"),
    _daily("raschke_swing", _R, "Connors and Raschke, Street Smarts (1995), Turtle Soup"),
    _daily("darvas_box", _R, "Darvas, How I Made $2,000,000 in the Stock Market (1960)"),
    _daily("dual_momentum", _MO, "Moskowitz, Ooi, Pedersen (2012); Antonacci (2014)"),
    _daily("clenow_momentum", _MO, "Clenow, Stocks on the Move (2015)"),
    _intraday("opening_range_15m", _R, _OpeningRange, "Crabel (1990); Zarattini et al. (2024)"),
    _intraday("gap_and_go_5m", _G, _GapAndGo, "Plastun et al. (2020): gap-day momentum"),
    _intraday("gap_fade_5m", _G, _GapFade, "the gap-fill fade, a trader's rule"),
    _intraday("vwap_reversion_5m", _S, _VwapReversion, "VWAP (Berkowitz et al. 1988), reverted"),
    _intraday("micro_pullback_5m", _S, _MicroPullback, "the 9/21 pullback scalp"),
    _intraday("rsi2_scalp_5m", _S, _Rsi2Scalp, "Connors and Alvarez (2008), on 5-minute bars"),
    _intraday("ema_cross_5m", _S, _EmaCross, "the 9/21 exponential cross, on 5-minute bars"),
    *(
        _daily(
            name, regime, f"Grimes, The Art and Science of Technical Analysis (2012), {name[:4]}"
        )
        for name, regime in zip(GRIMES, (_T, _T, _T, _T, _V, _R, _MR, _MO, _R, _MO), strict=True)
    ),
)


#: The zoo's day-trading rules, which the desk trades on PAPER only behind its one switch
#: (desk/running.py ZOO_ON), one share each, as a MACHINERY TEST: never in RULES, never judged.
ZOO_RULES: Mapping[str, Callable[[], IntradayRule]] = {
    m.name: m.rule  # type: ignore[misc]  # each zoo _Day defines step: test_intraday_zoo runs it
    for m in ZOO
    if m.span and issubclass(m.rule, _Day)
}


def zoo_lines() -> tuple[Line, ...]:
    """The zoo's fixed lines, by the master's facts: London's plain (unleveraged) lines and every
    US security; the operator's ten US lines wait on a tenth in the master."""
    return tuple(
        line
        for line in LINES
        if (line.venue == "LSE" and line.leverage == 1) or (line.venue == "US" and line.isin)
    )
