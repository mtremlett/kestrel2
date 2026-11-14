"""published - THE PUBLISHED RULES: a strategy is judged only by code proven to be the rule
its author published (STR-12).

A rule that is coded wrongly and then fails has told nothing about the rule: the old desk
threw strategies away on its own mistakes. So before the first rung (`lab/rung.py`) gives any
verdict on a strategy, the code is held to the publication. Each rule the ladder judges is
written down here with its author's source and its known answers: short series of prices on
which the published rule, worked by hand from its own words, buys and sells on stated bars
and on no other. The same series and days are pinned, with their working, in the
strategies' own contract test. Two pieces of code must give exactly those trades: the desk's
own engine (`strategy.decide`), which is what would trade, and the ladder's cell
(`lab/cell.py`), which is what is judged: the fast grid's answer wherever the grid gives
one, so each rule has a series with a trade that the grid answers itself (a tie it refuses
goes to the desk's engine).

Code that gives any other trade on any series is not the published rule, and it is refused
loudly: a fault in the test, never a verdict on the strategy. A rule with nothing written
here cannot be judged at all, so a new rule reaches the ladder only with its source and its
known answers. A handful of short series proves the rule's plain cases and the ties named
below, and no more: it is the gate at the ladder's door, not the whole proof, which is the
strategies' contract test on long walks.

THE INDICATORS. A rule is built of a few measurements, and a mistake in one of them is a
mistake in every rule that reads it: the old desk never checked one against a number it had
not worked itself. So the desk's measurements are held to tables printed by somebody else,
StockCharts' ChartSchool, whose spreadsheets give what each is worked from exactly and its
answers row by row (`INDICATORS`), at the tables' own lengths of 10, 20 and 14 days: the
desk's parts are one piece of code at any length. Held by name: the moving average, the
deviation of Bollinger's bands, the breakout's highest high and lowest low. Held as the
rule's own lines work them, the rule shown the table's days and its smoothing read after
each: the RSI's gains and losses, and the true range and its average, from prices alone.
No rule is proven while one of them gives another number. What a rule's own line works and
does not keep (the RSI's last ratio, a band's two deviations from its average) and
Supertrend's carried band, which no table here prints, are held by the known answers alone.

A series is its closes; each bar opens on its close, and its high and low lie `reach` either
side of it, one bar a day. Bars are counted from 0.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, localcontext
from functools import cache

from desk import strategy
from desk.lines import LINES
from desk.store import Bar
from desk.strategy import Action, Rule, _Rsi2, _Supertrend, _Wilder, _Window
from lab import cell
from lab.cell import Cell

Trades = tuple[tuple[int, int | None], ...]  #: each trade's bars: bought, sold (None: held)
_FIRST = date(2020, 1, 1)


@dataclass(frozen=True)
class Case:
    why: str  #: the working, by hand, from the rule's own words
    closes: tuple[Decimal, ...]
    trades: Trades  #: the bars the published rule buys and sells on, and no other
    reach: Decimal = Decimal("0.5")

    def bars(self) -> tuple[Bar, ...]:
        days, r = enumerate(self.closes), self.reach
        return tuple(Bar(_FIRST + timedelta(n), c, c + r, c - r, c, 1000) for n, c in days)


@dataclass(frozen=True)
class Published:
    source: str  #: the author and the work the rule is taken from
    cases: tuple[Case, ...]

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("a published rule with no source is nobody's rule")
        if not any(case.trades for case in self.cases):
            raise ValueError(
                f"{self.source}: on its known answers it buys nothing, which any code can do"
            )


def _case(why: str, closes: Sequence[int | str], trades: Trades, reach: str = "0.5") -> Case:
    return Case(why, tuple(Decimal(c) for c in closes), trades, Decimal(reach))


PUBLISHED: Mapping[str, Published] = {
    "rsi2_pullback": Published(
        "Connors and Alvarez, Short Term Trading Strategies That Work (2008): RSI-2",
        (
            _case(
                "bar 201: RSI(2) 9.1, not under 5; 202: 3.2 buys; 203: 285 is under its 5-day "
                "average of 290.8 and holds; 204: 300 is over 291 and sells",
                [*range(100, 300), 300, 290, 280, 285, 300],
                ((202, 204),),
            ),
            _case(
                "the same pullback under a falling 200-day average is never bought",
                [*range(400, 200, -1), 190, 180, 170, 185, 200],
                (),
            ),
            _case(
                "bar 209 falls to 110 with RSI(2) at 2.2, but the 200 days sum to 22,000: a "
                "close exactly on its average is not above it",
                [100] * 200 + [150, 200, 250, 300, 350, 410, 410, 410, 410, 110],
                (),
            ),
        ),
    ),
    "bollinger_pullback": Published(
        "Bollinger's bands at his settings, 20 days and 2 deviations (Bollinger on Bollinger "
        "Bands, 2001): a close under the lower band bought, one over the middle sold",
        (
            _case(
                "bar 20: mean 9.95, two deviations 0.436, so 9 is under 9.514 and buys; 21: "
                "9.5 is under the mean of 9.925 and holds; 22: 10.5 is over 9.95 and sells",
                [10] * 20 + [9, "9.5", "10.5"],
                ((20, 22),),
            ),
        ),
    ),
    "breakout_20_10": Published(
        "Faith, Way of the Turtle (2007): the Turtles' system 1, on the close",
        (
            _case(
                "highs of 10.5 for twenty days: bar 20's 10.4 does not clear them; bar 21's 11 "
                "clears bar 20's high of 10.9; bar 23's 9.4 is under the lows of 9.5, and sells",
                [10] * 20 + ["10.4", 11, 11, "9.4", "9.4"],
                ((21, 23),),
            ),
        ),
    ),
    "trend_50_200": Published(
        "the 50-day and 200-day moving-average cross (the golden cross), long only",
        (
            _case(
                "bar 200: the 50-day at 102 crosses over the 200-day at 100.5; from bar 250 at "
                "50 the 50-day is 197 - 3j and the 200-day 124.75 - j/4, first under at j = 27",
                [100] * 200 + [200] * 50 + [50] * 40,
                ((200, 277),),
            ),
            _case(
                "a 50-day already above when both averages first exist is no cross it saw",
                [*range(100, 360)],
                (),
            ),
        ),
    ),
    "supertrend_10_3": Published(
        "Seban's Supertrend, 10 days and 3 average true ranges, its bands carried as "
        "KivancOzbilgic's reference script carries them",
        (
            _case(
                "ten days with a true range of 2: bands 94 and 106. Bar 10 closes 110, over "
                "106, and buys; its lower band is 110 - 3 x 2.9 = 101.3. Bar 11 closes on it "
                "exactly and holds; the band is carried, and bar 12's 100 sells",
                [100] * 10 + [110, "101.3", 100],
                ((10, 12),),
                reach="1",
            ),
            _case(
                "the same with bar 11 at 102, clear of the band of 101.3, and held: no tie, "
                "so the fast grid answers this one itself and is held to the rule too",
                [100] * 10 + [110, 102, 100],
                ((10, 12),),
                reach="1",
            ),
        ),
    ),
}


Columns = Mapping[str, tuple[Decimal, ...]]
_SCHOOL = "StockCharts ChartSchool, the spreadsheet of its page on "


@dataclass(frozen=True)
class Table:
    """A table somebody else printed: what the indicator is given, and each column printed of
    it, from the first row that has an answer, to the places written here."""

    source: str
    given: Columns
    printed: Columns
    made: Callable[[Columns], Mapping[str, Sequence[Decimal]]]  #: the desk's own, by column

    def __post_init__(self) -> None:
        if not self.source.strip() or not self.printed:
            raise ValueError(f"a table of no source, or one that prints nothing: {self.source!r}")


def _columns(*columns: str) -> Columns:
    """Each column as it is written here: its heading, a colon, its numbers down the rows."""
    named = (column.split(":") for column in columns)
    return {name: tuple(Decimal(n) for n in numbers.split()) for name, numbers in named}


def _windows(size: int, values: Sequence[Decimal]) -> Iterator[_Window]:
    """The desk's window of `size` after each value, from the one that fills it."""
    window = _Window(size)
    for value in values:
        window.add(value)
        if window.full:
            yield window


def _fed(make: type[Rule], size: int, part: str, given: Columns) -> list[Decimal]:
    """What the rule's own lines feed its Wilder's smoothing `part` on the table's days (a
    gain, a loss, a true range), smoothed over `size` days, from the first day it has a value.
    Over 1 day the smoothing is the number fed itself. A table of closes has days of no range."""
    rule, closes = make(), given["Close"]
    smooth = {name: _Wilder(size) for name, was in vars(rule).items() if isinstance(was, _Wilder)}
    vars(rule).update(smooth)
    made = []
    days = zip(given.get("High", closes), given.get("Low", closes), closes, strict=True)
    for n, (high, low, close) in enumerate(days):
        rule.step(Bar(_FIRST + timedelta(n), close, high, low, close, 1000), False)
        made.append(smooth[part].value)
    return [value for value in made if value is not None]


INDICATORS: Mapping[str, Table] = {
    "moving average": Table(
        _SCHOOL + "moving averages (cs-movavg.xls): Intel, 24 March to 5 May 2010, 10 days",
        _columns(
            "Price: 22.2734 22.1940 22.0847 22.1741 22.1840 22.1344 22.2337 22.4323 22.2436 "
            "22.2933 22.1542 22.3926 22.3816 22.6109 23.3558 24.0519 23.7530 23.8324 23.9516 "
            "23.6338 23.8225 23.8722 23.6537 23.1870 23.0976 23.3260 22.6805 23.0976 22.4025 "
            "22.1725",
        ),
        _columns(
            "10-day SMA: 22.224750 22.212830 22.232690 22.262380 22.306060 22.423240 22.614990 "
            "22.766920 22.906930 23.077730 23.211780 23.378610 23.526570 23.653780 23.711390 "
            "23.685570 23.612980 23.505730 23.432250 23.277340 23.131210",
        ),
        lambda given: {"10-day SMA": [w.mean() for w in _windows(10, given["Price"])]},
    ),
    "Bollinger's bands": Table(
        _SCHOOL + "Bollinger Bands (cs-bbands.xls): SPY, 1 May to 30 June 2009, 20 days",
        _columns(
            "Price: 86.1557 89.0867 88.7829 90.3228 89.0671 91.1453 89.4397 89.1750 86.9302 "
            "87.6752 86.9596 89.4299 89.3221 88.7241 87.4497 87.2634 89.4985 87.9006 89.1260 "
            "90.7043 92.9001 92.9784 91.8021 92.6647 92.6843 92.3021 92.7725 92.5373 92.9490 "
            "93.2039 91.0669 89.8318 89.7435 90.3994 90.7387 88.0177 88.0867 88.8439 90.7781 "
            "90.5416 91.3894 90.6500",
        ),
        _columns(
            "Middle Band: 88.707940 89.045160 89.239745 89.390705 89.507800 89.688660 89.746500 "
            "89.913140 90.081255 90.382195 90.658630 90.863995 90.884090 90.905160 90.988925 "
            "91.153375 91.191090 91.120500 91.167665 91.250270 91.242135 91.166600 91.050180",
            "Standard Deviation: 1.2920 1.4521 1.6864 1.7717 1.9021 2.0199 2.0765 2.1766 2.2419 "
            "2.2024 2.1922 2.0218 2.0094 1.9951 1.9360 1.7601 1.6828 1.7791 1.7041 1.6420 1.6451 "
            "1.6013 1.5492",
        ),
        lambda given: {
            "Middle Band": [w.mean() for w in _windows(20, given["Price"])],
            "Standard Deviation": [w.deviation() for w in _windows(20, given["Price"])],
        },
    ),
    "gains and losses under the RSI": Table(
        _SCHOOL + "the RSI (cs-rsi.xls): QQQQ, 14 December 2009 to 1 February 2010, 14 days",
        _columns(
            "Close: 44.3389 44.0902 44.1497 43.6124 44.3278 44.8264 45.0955 45.4245 45.8433 "
            "46.0826 45.8931 46.0328 45.6140 46.2820 46.2820 46.0028 46.0328 46.4116 46.2222 "
            "45.6439 46.2122 46.2521 45.7137 46.4515 45.7835 45.3548 44.0288 44.1783 44.2181 "
            "44.5672 43.4205 42.6628 43.1314",
        ),
        _columns(
            "Gain: 0.0000 0.0595 0.0000 0.7154 0.4986 0.2691 0.3290 0.4188 0.2393 0.0000 0.1397 "
            "0.0000 0.6680 0.0000 0.0000 0.0300 0.3788 0.0000 0.0000 0.5683 0.0399 0.0000 0.7378 "
            "0.0000 0.0000 0.0000 0.1495 0.0398 0.3491 0.0000 0.0000 0.4686",
            "Loss: 0.2487 0.0000 0.5373 0.0000 0.0000 0.0000 0.0000 0.0000 0.0000 0.1895 0.0000 "
            "0.4188 0.0000 0.0000 0.2792 0.0000 0.0000 0.1894 0.5783 0.0000 0.0000 0.5384 0.0000 "
            "0.6680 0.4287 1.3260 0.0000 0.0000 0.0000 1.1467 0.7577 0.0000",
            "Avg Gain: 0.2384 0.2214 0.2077 0.2199 0.2042 0.1896 0.2167 0.2040 0.1895 0.2286 "
            "0.2123 0.1971 0.1831 0.1807 0.1706 0.1833 0.1703 0.1581 0.1803",
            "Avg Loss: 0.0996 0.1124 0.1044 0.0969 0.1035 0.1375 0.1276 0.1185 0.1485 0.1379 "
            "0.1758 0.1938 0.2747 0.2551 0.2369 0.2199 0.2861 0.3198 0.2970",
        ),
        lambda given: {
            "Gain": _fed(_Rsi2, 1, "_gain", given),
            "Loss": _fed(_Rsi2, 1, "_loss", given),
            "Avg Gain": _fed(_Rsi2, 14, "_gain", given),
            "Avg Loss": _fed(_Rsi2, 14, "_loss", given),
        },
    ),
    "true range": Table(
        _SCHOOL + "the average true range (cs-atr.xls): QQQ, 1 April to 13 May 2010, 14 days",
        _columns(
            "High: 48.7000 48.7200 48.9000 48.8700 48.8200 49.0500 49.2000 49.3500 49.9200 "
            "50.1900 50.1200 49.6600 49.8800 50.1900 50.3600 50.5700 50.6500 50.4300 49.6300 "
            "50.3300 50.2900 50.1700 49.3200 48.5000 48.3201 46.8000 47.8000 48.3900 48.6600 "
            "48.7900",
            "Low: 47.7900 48.1400 48.3900 48.3700 48.2400 48.6350 48.9400 48.8600 49.5000 49.8700 "
            "49.2000 48.9000 49.4300 49.7250 49.2600 50.0900 50.3000 49.2100 48.9800 49.6100 "
            "49.2000 49.4300 48.0800 47.6400 41.5500 44.2833 47.3100 47.2000 47.9000 47.7301",
            "Close: 48.1600 48.6100 48.7500 48.6300 48.7400 49.0300 49.0700 49.3200 49.9100 "
            "50.1300 49.5300 49.5000 49.7500 50.0300 50.3100 50.5200 50.4100 49.3400 49.3700 "
            "50.2300 49.2375 49.9300 48.4300 48.1800 46.5700 45.4100 47.7700 47.7200 48.6200 "
            "47.8500",
        ),
        _columns(
            "TR: 0.9100 0.5800 0.5100 0.5000 0.5800 0.4150 0.2600 0.4900 0.6000 0.3200 0.9300 "
            "0.7600 0.4500 0.4650 1.1000 0.4800 0.3500 1.2200 0.6500 0.9600 1.0900 0.9325 1.8500 "
            "0.8600 6.7701 2.5167 2.3900 1.1900 0.9400 1.0599",
            "ATR: 0.5550 0.5939 0.5858 0.5689 0.6155 0.6179 0.6424 0.6743 0.6928 0.7754 0.7815 "
            "1.2092 1.3026 1.3803 1.3667 1.3362 1.3165",
        ),
        lambda given: {
            "TR": _fed(_Supertrend, 1, "_range", given),
            "ATR": _fed(_Supertrend, 14, "_range", given),
        },
    ),
    "channel": Table(
        _SCHOOL + "the stochastic oscillator (cs-soo.xls): 23 February to 6 April 2010, 14 days",
        _columns(
            "High: 127.0090 127.6159 126.5911 127.3472 128.1730 128.4317 127.3671 126.4220 "
            "126.8995 126.8498 125.6460 125.7156 127.1582 127.7154 127.6855 128.2228 128.2725 "
            "128.0934 128.2725 127.7353 128.7700 129.2873 130.0633 129.1182 129.2873 128.4715 "
            "128.0934 128.6506 129.1381 128.6406",
            "Low: 125.3574 126.1633 124.9296 126.0937 126.8199 126.4817 126.0340 124.8301 "
            "126.3921 125.7156 124.5615 124.5715 125.0689 126.8597 126.6309 126.8001 126.7105 "
            "126.8001 126.1335 125.9245 126.9891 127.8148 128.4715 128.0641 127.6059 127.5960 "
            "126.9990 126.8995 127.4865 127.3970",
        ),
        _columns(
            "Highest High (14): 128.4317 128.4317 128.4317 128.4317 128.4317 128.4317 128.2725 "
            "128.7700 129.2873 130.0633 130.0633 130.0633 130.0633 130.0633 130.0633 130.0633 "
            "130.0633",
            "Lowest Low (14): 124.5615 124.5615 124.5615 124.5615 124.5615 124.5615 124.5615 "
            "124.5615 124.5615 124.5615 124.5615 124.5715 125.0689 125.9245 125.9245 125.9245 "
            "125.9245",
        ),
        lambda given: {
            "Highest High (14)": [w.high() for w in _windows(14, given["High"])],
            "Lowest Low (14)": [w.low() for w in _windows(14, given["Low"])],
        },
    ),
}


@cache
def indicators() -> Mapping[str, Table]:
    """The published tables, once the desk's own parts have given every row of every column
    printed, each to the places it is printed to; refused, and not remembered, at the first
    that does not."""
    with localcontext(strategy.ARITHMETIC):
        for name, table in INDICATORS.items():
            columns = table.made(table.given)
            for column, printed in table.printed.items():
                _hold(f"the desk's {name}, its {column}", table, columns[column], printed)
    return INDICATORS


def _hold(whose: str, table: Table, made: Sequence[Decimal], printed: Sequence[Decimal]) -> None:
    said = f"{whose}, is not the published one ({table.source}): it "
    if len(made) != len(printed):
        raise ValueError(f"{said}gives {len(made)} rows where the table prints {len(printed)}")
    for n, (mine, theirs) in enumerate(zip(made, printed, strict=True)):
        if mine.quantize(theirs) != theirs:
            raise ValueError(
                f"{said}gives {mine.quantize(theirs)} at row {n} where the table prints {theirs}"
            )


@cache
def proven(name: str) -> Published:
    """The rule's publication, once the indicators give their published tables and the desk's
    engine and the ladder's cell have both given its known answers on every series; refused,
    and not remembered, when any does not."""
    indicators()
    if name not in PUBLISHED:
        raise ValueError(f"{name}: no published rule on file, so no code can be held to it")
    rule = PUBLISHED[name]
    for case in rule.cases:
        bars = case.bars()
        for whose, made in (
            ("the desk's engine", _desk(name, bars)),
            ("the cell", _cell(name, bars)),
        ):
            if made != case.trades:
                raise ValueError(
                    f"{name}: {whose} is not the published rule ({rule.source}). It trades "
                    f"bars {made} where the rule trades {case.trades}: {case.why}"
                )
    return rule


def _desk(name: str, bars: Sequence[Bar]) -> Trades:
    decided = [d.action for d in strategy.decide({LINES[0].symbol: bars}) if d.strategy == name]
    turns = [n for n, action in enumerate(decided) if action is not Action.HOLD]
    return tuple(zip(turns[::2], [*turns[1::2], None], strict=False))


def _cell(name: str, bars: Sequence[Bar]) -> Trades:
    at = {bar.day: n for n, bar in enumerate(bars)}
    record = cell.run(Cell(name, LINES[0], bars[0].day, bars[-1].day), bars)
    return tuple((at[t.bought], None if t.sold is None else at[t.sold]) for t in record.trades)
