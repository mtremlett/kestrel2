"""published_tables - THE INDICATORS, HELD TO TABLES SOMEBODY ELSE PRINTED (STR-14).

A rule is built of a few measurements, and a mistake in one of them is a
mistake in every rule that reads it: the old desk never checked one against a number it had
not worked itself. So the desk's measurements are held to tables printed by somebody else,
StockCharts' ChartSchool, whose spreadsheets give what each is worked from exactly and its
answers row by row (`INDICATORS`), at the tables' own lengths of 10, 20 and 14 days: the
desk's parts are one piece of code at any length. Held by name: the moving average, the
deviation of Bollinger's bands, the breakout's highest high and lowest low, and the RSI
`strategy.rsi` makes of the averages below, and the band line `strategy.lower_band` draws two
deviations under the average. Held as the rule's own lines work them, the rule
shown the table's days and its smoothing read after each: the RSI's gains and losses, and
the true range and its average, from prices alone. No rule is proven while one of them
gives another number. Each table is run twice: with the rule holding nothing, and again
holding from its first smoothed day, so a rule that stops feeding its lines while it holds is
refused (the windows are no rule's lines, and give the same either way). No table has a day
whose own low is its lowest of 14. Supertrend's carried band, which no table here
prints, is left to the known answers of `lab/published.py` and the strategies' contract test.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, localcontext
from functools import cache

from desk import strategy
from desk.store import Bar
from desk.strategy import Rule, _Rsi2, _Supertrend, _Wilder, _Window
from lab.published_case import FIRST

Columns = Mapping[str, tuple[Decimal, ...]]
_SCHOOL = "StockCharts ChartSchool, the spreadsheet of its page on "


@dataclass(frozen=True)
class Table:
    """A table somebody else printed: what the indicator is given, and each column printed of
    it, from the first row that has an answer, to the places written here."""

    source: str
    given: Columns
    printed: Columns
    made: Callable[[Columns, bool], Mapping[str, Sequence[Decimal]]]  #: the desk's, holding or not

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


def _fed(make: type[Rule], size: int, part: str, given: Columns, holding: bool) -> list[Decimal]:
    """What the rule's own lines feed its Wilder's smoothing `part` on the table's days (a
    gain, a loss, a true range), smoothed over `size` days, from the first day it has a value,
    the rule `holding` from then on or never. Over 1 day the smoothing is the number fed
    itself. A table of closes has days of no range."""
    rule, closes = make(), given["Close"]
    smooth = {name: _Wilder(size) for name, was in vars(rule).items() if isinstance(was, _Wilder)}
    vars(rule).update(smooth)
    made = []
    days = zip(given.get("High", closes), given.get("Low", closes), closes, strict=True)
    for n, (high, low, close) in enumerate(days):
        held = holding and smooth[part].value is not None
        rule.step(Bar(FIRST + timedelta(n), close, high, low, close, 1000), held)
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
        lambda given, _held: {"10-day SMA": [w.mean() for w in _windows(10, given["Price"])]},
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
            "Lower Band: 86.1240 86.1411 85.8669 85.8472 85.7037 85.6489 85.5934 85.5600 85.5974 "
            "85.9775 86.2743 86.8204 86.8653 86.9150 87.1168 87.6331 87.8256 87.5622 87.7595 "
            "87.9663 87.9520 87.9639 87.9519",
        ),
        lambda given, _held: {
            "Middle Band": [w.mean() for w in _windows(20, given["Price"])],
            "Standard Deviation": [w.deviation() for w in _windows(20, given["Price"])],
            "Lower Band": [
                strategy.lower_band(w.mean(), w.deviation()) for w in _windows(20, given["Price"])
            ],
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
            "RSI: 70.53 66.32 66.55 69.41 66.36 57.97 62.93 63.26 56.06 62.38 54.71 50.42 39.99 "
            "41.46 41.87 45.46 37.30 33.08 37.77",
        ),
        lambda given, held: {
            "Gain": _fed(_Rsi2, 1, "_gain", given, held),
            "Loss": _fed(_Rsi2, 1, "_loss", given, held),
            "Avg Gain": _fed(_Rsi2, 14, "_gain", given, held),
            "Avg Loss": _fed(_Rsi2, 14, "_loss", given, held),
            "RSI": list(
                map(
                    strategy.rsi,
                    _fed(_Rsi2, 14, "_gain", given, held),
                    _fed(_Rsi2, 14, "_loss", given, held),
                )
            ),
        },
    ),
    "true range": Table(
        _SCHOOL + "the average true range (cs-atr.xls): QQQ, 1 April to 13 May 2010, 14 days",
        _columns(
            "High: 48.7 48.72 48.9 48.87 48.82 49.05 49.2 49.35 49.92 50.19 50.12 49.66 49.88 "
            "50.19 50.36 50.57 50.65 50.43 49.63 50.33 50.29 50.17 49.32 48.5 48.3201 46.8 47.8 "
            "48.39 48.66 48.79",
            "Low: 47.79 48.14 48.39 48.37 48.24 48.635 48.94 48.86 49.5 49.87 49.2 48.9 49.43 "
            "49.725 49.26 50.09 50.3 49.21 48.98 49.61 49.2 49.43 48.08 47.64 41.55 44.2833 47.31 "
            "47.2 47.9 47.7301",
            "Close: 48.16 48.61 48.75 48.63 48.74 49.03 49.07 49.32 49.91 50.13 49.53 49.5 49.75 "
            "50.03 50.31 50.52 50.41 49.34 49.37 50.23 49.2375 49.93 48.43 48.18 46.57 45.41 "
            "47.77 47.72 48.62 47.85",
        ),
        _columns(
            "TR: 0.9100 0.5800 0.5100 0.5000 0.5800 0.4150 0.2600 0.4900 0.6000 0.3200 0.9300 "
            "0.7600 0.4500 0.4650 1.1000 0.4800 0.3500 1.2200 0.6500 0.9600 1.0900 0.9325 1.8500 "
            "0.8600 6.7701 2.5167 2.3900 1.1900 0.9400 1.0599",
            "ATR: 0.5550 0.5939 0.5858 0.5689 0.6155 0.6179 0.6424 0.6743 0.6928 0.7754 0.7815 "
            "1.2092 1.3026 1.3803 1.3667 1.3362 1.3165",
        ),
        lambda given, held: {
            "TR": _fed(_Supertrend, 1, "_range", given, held),
            "ATR": _fed(_Supertrend, 14, "_range", given, held),
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
        lambda given, _held: {
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
            for held, holding in ((False, ""), (True, ", while holding")):
                columns = table.made(table.given, held)
                for column, printed in table.printed.items():
                    whose = f"the desk's {name}, its {column}{holding}"
                    _hold(whose, table, columns[column], printed)
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
