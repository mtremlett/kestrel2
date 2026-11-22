"""published_epon - THE EPONYMOUS RULES' PUBLICATIONS (all twenty the ladder judges; Zweig's
is not among them): each rule of `desk/eponymous_*.py` with
its author and work as its module's docstring states them, and its known answers: the series
and trades its own known-answer test holds, worked by hand from the rule's own words. Held
to them by `lab.published.proven`, exactly as the desk's five are; a rule with nothing
written here is refused. They are a book apart from `published.PUBLISHED`, which is the
ladder's first set. Zweig's breadth thrust takes data the store does not hold: it is not here.

THE AUTHOR'S TEST (`TESTED`), written down before any run so reproduction can be held to it:
each rule's market, period and numbers printed, word for word, from the page named, read on
22 November 2026 and never from memory. What was found is said plainly: the author's own test,
a replication of the rule as coded (his ruling, 14 November), a test of a different rule (its
numbers kept, never reproduced), or nothing free, with where it was looked for.
"""

from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from desk.store import Bar
from lab.published_case import FIRST, Case, Published, Trades, known

_D = Decimal
Spec = Sequence[tuple[str, str, str, int]]  #: a bar a day: high, low, close, volume


def _daily(spec: Spec, trades: Trades, why: str) -> Case:
    """Bars from FIRST, a day each, opening on their close."""
    rows = tuple(
        Bar(FIRST + timedelta(n), _D(c), _D(h), _D(lo), _D(c), v)
        for n, (h, lo, c, v) in enumerate(spec)
    )
    return Case(why, (), trades, rows=rows)


def _months(closes: Sequence[int], first: int | None, why: str, trades: Trades) -> Case:
    """Two bars a month: the 1st at `first`, the 20th at that month's close."""
    rows = tuple(
        Bar(date(2020 + m // 12, m % 12 + 1, day), _D(p), _D(p), _D(p), _D(p), 1)
        for m, close in enumerate(closes)
        for day, p in ((1, close if first is None else first), (20, close))
    )
    return Case(why, (), trades, rows=rows)


_DARVAS = [  #: high, low, close per session
    ("10", "9", "9.5"), ("9.8", "9.2", "9.5"), ("9.7", "9.3", "9.5"), ("9.6", "9.4", "9.5"),
    ("10.2", "9.5", "10.1"), ("10.1", "9.8", "10"), ("10", "9.7", "9.9"), ("10", "9.9", "9.95"),
    ("10.1", "9.8", "10"), ("10.9", "10", "10.8"), ("10.6", "10.3", "10.4"),
    ("10.5", "10.2", "10.3"), ("10.4", "10.1", "10.2"), ("10.3", "9.8", "9.9"),
    ("10", "9.6", "9.7"), ("9.9", "9.7", "9.8"), ("9.8", "9.7", "9.75"), ("9.7", "9.65", "9.7"),
    ("10.6", "9.9", "10.5"),
]  # fmt: skip
_QUIET: Spec = [("101", "100", "100", 1000)] * 50  #: Zanger: fifty quiet sessions
_BREAKS: Spec = [("102", "102", "102", 1000), ("103", "103", "103", 2000)]
_CLIMB: Spec = [("104", "104", "104", 1000), ("105", "105", "105", 1000), ("90", "90", "90", 1000)]
_ENDS = [*range(100, 116), 90, 80, *[80] * 10, 95, 95, 95]  #: Antonacci: the month-end closes
_SOUP = [(99, 100), *[(109, 110)] * 19, (98, 105), (100, 106), (96, 97)]  #: low, close
_RISE = [str(_D(100) + _D("0.2") * n) for n in range(260)]  #: Minervini's year of climbing
_AFTER = [str(_D(_RISE[-1]) + _D(x)) for x in ("2", "2.2", "2.4", "2.6", "2.8")]

EPONYMOUS_PUBLISHED: Mapping[str, Published] = {
    "donchian_channel_breakout": Published(
        "Donchian's four-week rule as Faith gives it, Way of the Turtle (2007): a price over "
        "the highest high of the four weeks before bought, one under their lowest low sold",
        (
            known(
                "20 flat sessions, highs 100.5: 100.5 does not clear them; 102 closes over the "
                "high of 101 (bar 21): buy on 21; 99 closes under the 20-day low: sell on 23",
                ["100"] * 20 + ["100.5", "102", "103", "99", "98"],
                ((21, 23),),
            ),
        ),
    ),
    "donchian_fade_chop": Published(
        "Donchian's four-week channel, faded inside a range, as Faith gives it, Way of the "
        "Turtle (2007)",
        (
            known(
                "20 flat sessions are a range of 99.5 to 100.5: 99 closes under its low, buy "
                "on 20; the channel's midpoint is then 99.5: 99.2 holds, 100 sells on 22",
                ["100"] * 20 + ["99", "99.2", "100"],
                ((20, 22),),
            ),
        ),
    ),
    "bollinger_squeeze": Published(
        "Bollinger on Bollinger Bands (2001), the squeeze: bands at their narrowest in six "
        "months, a close out of them bought, one under the middle band sold",
        (
            known(
                "146 flat days: no width, the narrowest in six months. 110 is over the upper "
                "band of 104.9: buy on 146; 110 holds over the average of 101; 90 is under "
                "the average of 100.5: sell on 148",
                [100] * 146 + [110, 110, 90],
                ((146, 148),),
                reach="0",
            ),
        ),
    ),
    "darvas_box": Published(
        "Darvas, How I Made $2,000,000 in the Stock Market (1960): a close over the box's top "
        "bought, a close under its raised stop sold",
        (
            _daily(
                [(h, lo, c, 1000) for h, lo, c in _DARVAS],
                ((4, 13), (18, None)),
                "box 1 (top 10, bottom 9) stands on 3; 4 closes over it: buy. Boxes stand on 7 "
                "and 12 and raise the stop to 10.0; 13 closes under it: sell. The next box "
                "stands on 17; 18 closes over it: buy",
            ),
        ),
    ),
    "clenow_momentum": Published(
        "Clenow, Stocks on the Move (2015): the momentum model, a close over its 100-day "
        "average with no move of 15% in a day inside 90 days",
        (
            known(
                "100 closes up by 1: the average is full on 99, the close over it: buy. 120 is "
                "under the average, and a 40% move: sell on 100",
                [*range(100, 200), 120, 121],
                ((99, 100),),
                reach="0",
            ),
            known(
                "230 is 15.6% over 199, far above the average, yet the move alone ends the hold",
                [*range(100, 200), 230],
                ((99, 100),),
                reach="0",
            ),
        ),
    ),
    "connors_rsi2": Published(
        "Connors and Alvarez, Short Term Trading Strategies That Work (2008): RSI-2 under 10 "
        "above the 200-day average bought, a close over the 5-day average sold",
        (
            known(
                "200 days up by 1; a fall of 10 makes RSI(2) 9.09, the close over its 200-day "
                "average: buy on 200. 290 is under the 5-day average of 294.6: held. 300 is "
                "over 295.2: sell on 202",
                [*range(100, 300), 289, 290, 300, 301, 302],
                ((200, 202),),
                reach="0",
            ),
        ),
    ),
    "connors_percent_b": Published(
        "Connors and Alvarez, High Probability ETF Trading (2009): %b under 0.2 three days "
        "running above the 200-day average bought, %b over 0.8 sold",
        (
            known(
                "200 days up by 1, then 280, 275, 270: %b is 0.088, -0.061, -0.124, three low "
                "days over the 200-day average: buy on 202. 0.375 and 0.694 hold; 300 gives "
                "0.824, over 0.8: sell on 205",
                [*range(100, 300), 280, 275, 270, 285, 295, 300, 310],
                ((202, 205),),
                reach="0",
            ),
        ),
    ),
    "connors_three_day_high_low": Published(
        "Connors and Alvarez, High Probability ETF Trading (2009): three lower days in an "
        "uptrend bought, a close over the 5-day average sold",
        (
            known(
                "200 days up by 1, then 297, 295, 293: each day's high and low under the day "
                "before's, over the 200-day average: buy on 202. 300 is over the 5-day "
                "average of 296.8: sell on 203",
                [*range(100, 300), 297, 295, 293, 300, 301],
                ((202, 203),),
                reach="1",
            ),
        ),
    ),
    "dan_zanger_breakout": Published(
        "Dan Zanger's base breakout as told in interviews and profiles (secondary): a new "
        "high on volume well over the average bought, a close under the 10-day average sold",
        (
            _daily(
                [*_QUIET, *_BREAKS, *_CLIMB],
                ((51, 54),),
                "day 50 clears the 50-day high on light volume: no buy. 51 clears it on twice "
                "the 50-day volume: buy. 52 and 53 stay over the 10-day average of 101.4. 54 "
                "closes at 90, under 100.4: sell",
            ),
        ),
    ),
    "demark_sequential": Published(
        "DeMark, The New Science of Technical Analysis (1994): the thirteenth countdown bar "
        "of a buy setup bought, the ninth bar of a sell setup sold",
        (
            known(
                "falling by 1 from 300, the buy setup completes on 12 and the thirteenth "
                "countdown bar is 25: buy. Rising by 1 from 276, nine in a row to 36: sell",
                [*range(300, 274, -1), *range(276, 290)],
                ((25, 36),),
                reach="1",
            ),
        ),
    ),
    "faber_tactical": Published(
        "Faber, A Quantitative Approach to Tactical Asset Allocation (2007): long at a "
        "month-end close over its 10-month average, out under it",
        (
            _months(
                [*[100] * 10, 110, 90, 90],
                None,
                "ten flat months: out. Month 11 closes 110 over its average of 101: buy on "
                "month 12's first bar (22). Month 12 closes 90 under 100: sell on 24",
                ((22, 24),),
            ),
        ),
    ),
    "kell_breakout": Published(
        "Kell, base n' break, from his interviews and setups (secondary): a close over a "
        "20-session base and the 10- and 20-day averages bought, under the 10-day sold",
        (
            known(
                "25 days at 100 are the base. 110 is over its high and the averages: buy on "
                "25. 112 and 114 stay over the 10-day average; 100 falls under 104.4: sell "
                "on 28",
                [100] * 25 + [110, 112, 114, 100, 100],
                ((25, 28),),
                reach="0",
            ),
        ),
    ),
    "keltner_channel_trend": Published(
        "Keltner, How to Make Money in Commodities (1960): a close over the upper channel "
        "bought, one under the lower channel sold",
        (
            known(
                "ten days at 100 (range 2): 110 is over the centre 101 + 2: buy on 10. 110 "
                "holds inside or over the band; 90 is under the centre 104 - 2: sell on 15",
                [*[100] * 10, *[110] * 5, 90, 90],
                ((10, 15),),
                reach="1",
            ),
        ),
    ),
    "mansfield_rs_momentum": Published(
        "Weinstein, Secrets for Profiting in Bull and Bear Markets (1988), Mansfield relative "
        "strength: in while the ratio is over its 52-week average",
        (
            known(
                "260 flat days: RS is zero, not above it. 101 lifts the ratio over its average: "
                "buy on 260; 99 puts it under: sell on 261",
                [100] * 260 + [101, 99],
                ((260, 261),),
                reach="0",
            ),
        ),
    ),
    "minervini_breakout": Published(
        "Minervini, Trade Like a Stock Market Wizard (2013): a break of the pivot in the "
        "Trend Template bought, a close under the 50-day average sold",
        (
            known(
                "260 sessions rising 0.2 a day, every average stacked in order, never clearing "
                "the last 15 highs; session 260 jumps 2 over the pivot: buy. 261-264 climb on; "
                "265 closes at 100, far under the 50-day average: sell",
                [*_RISE, *_AFTER, 100],
                ((260, 265),),
            ),
        ),
    ),
    "dual_momentum": Published(
        "Antonacci, Dual Momentum Investing (2014), the absolute leg: hold while the last "
        "month-end close beats the one twelve month-ends before, called on the next month's "
        "first bar",
        (
            _months(
                _ENDS,
                1000,
                "month k decides on ends[k-1] against ends[k-13]: k=13 buys (112 over 100) on "
                "February 2021's first bar (26), k=17 sells (90 under 104) on June's (34), k=29 "
                "buys (95 over 90) on June 2022's (58); the 1000 opens heed nothing",
                ((26, 34), (58, None)),
            ),
        ),
    ),
    "weekly_reversal_jegadeesh": Published(
        "Jegadeesh, Evidence of Predictable Behavior of Security Returns (1990), with the "
        "weekly form of Lehmann (1990): a close under the close five sessions before bought, "
        "sold after five sessions held",
        (
            known(
                "five days at 100, then 99 is a losing week: buy on 5; sold after five held, on "
                "10; 97 is still under 99: buy on 11, sell on 16; the rise after loses nothing",
                [*[100] * 5, *[99] * 5, 98, 97, *range(100, 108)],
                ((5, 10), (11, 16)),
                reach="0",
            ),
        ),
    ),
    "williams_r": Published(
        "Williams, How I Made One Million Dollars Last Year Trading Commodities (1973): %R over "
        "ten days at -90 or lower bought, at -10 or higher sold",
        (
            known(
                "nine days at 100 then 90: the range is 89 to 101, %R -91.7: buy on 9. 100 gives "
                "-8.3: sell on 10",
                [*[100] * 9, 90, 100, 100],
                ((9, 10),),
                reach="1",
            ),
        ),
    ),
    "weinstein_stage": Published(
        "Weinstein, Secrets for Profiting in Bull and Bear Markets (1988), stage analysis: a "
        "close over a rising 30-week (150-day) average bought, one under it sold",
        (
            known(
                "150 flat days fill the average; 110 to 114 lift it. On 154 it is over its value "
                "of a week before and the close is over it: buy. 115 holds; 50 is under it: sell "
                "on 156",
                [*[100] * 150, 110, 111, 112, 113, 114, 115, 50],
                ((154, 156),),
                reach="1",
            ),
        ),
    ),
    "raschke_swing": Published(
        "Raschke and Connors, Street Smarts (1995), Turtle Soup: a new 20-day low set over "
        "four sessions after the old one, closing back over it, bought; a close under the "
        "buying day's low sold",
        (
            _daily(
                [(str(c + 1), str(lo), str(c), 1000) for lo, c in _SOUP],
                ((20, 22),),
                "day 0 sets the 20-day low 99; day 20 undercuts it at 98 and closes back over "
                "it: buy. 21 holds; 22 closes 97, under 98: sell",
            ),
        ),
    ),
}


class Search(enum.Enum):
    """What the search for a rule's published test found. Not `reproduce.Hand`, which names
    whose a figure on file is: these are what was read before any figure is filed."""

    AUTHOR = "the author's own test"
    SECOND = "a replication of the rule as coded"
    OTHER = "a test of a different rule, never reproduced"
    NONE = "no numbers found free"


@dataclass(frozen=True)
class Printed:
    """A rule's published test as its page prints it; with none found, where it was looked for."""

    found: Search
    page: str  #: the address read, or, with nothing found, where it was looked for
    market: str = ""
    period: str = ""
    numbers: str = ""  #: every number, word for word

    def __post_init__(self) -> None:
        if not self.page.strip():
            raise ValueError(f"{self.found.value}: no page read and nowhere looked")
        told = [part.strip() for part in (self.market, self.period, self.numbers)]
        if self.found is Search.NONE and any(told):
            raise ValueError(f"{self.page}: numbers found are not none found")
        if self.found is not Search.NONE and not (self.page.startswith("https://") and all(told)):
            raise ValueError(f"{self.page}: a test with no address, market, period or numbers")

    @property
    def candidate(self) -> bool:
        """Whether reproduction may be held to it: the rule as coded, its numbers printed. It
        waits for `lab/reproduce.py` to take an eponymous rule and the numbers it prints."""
        return self.found in (Search.AUTHOR, Search.SECOND)

    def said(self) -> str:
        """The test in one line, for a results table."""
        if self.found is Search.NONE:
            return f"{self.found.value} (looked: {self.page})"
        return f"{self.found.value}: {self.market}, {self.period}: {self.numbers} ({self.page})"


_QS = "https://quantifiedstrategies.substack.com/p/"
_OXFORD = "https://oxfordstrat.com/"
_NOWHERE = "web search: no rules-based test of this rule published"
TESTED: Mapping[str, Printed] = {
    "donchian_channel_breakout": Printed(
        Search.OTHER,
        _QS + "donchian-breakout-strategy",
        "SPY, EFA, EEM, GLD, TLT, DBC on monthly bars (rules paywalled, not Faith's)",
        "from 2004 (QuantifiedStrategies, 10 August 2026)",
        "No. of trades: 78; Average gain per trade: 4.9%; Win ratio: 51%; CAGR: 7.5%; "
        "Max drawdown: -18%",
    ),
    "donchian_fade_chop": Printed(Search.NONE, _NOWHERE + " (searches find breakouts only)"),
    "bollinger_squeeze": Printed(
        Search.OTHER,
        "https://articles.stockcharts.com/article/articles-arthurhill-2017-03-systemtrader---"
        "testing-a-bollinger-band-squeeze-system-for-stocks-in-the-sp-1500-",
        "S&P 1500 historical members (Arthur Hill: BandWidth under 6%, StochRSI in, RSI out)",
        "1-January-2000 to 1-March-2017, filled at the next open",
        "the Win% is below 50% (47%); average gain is more than twice the average loss",
    ),
    "darvas_box": Printed(Search.NONE, _NOWHERE + " (educational pages only)"),
    "clenow_momentum": Printed(
        Search.OTHER,
        "https://www.quantconnect.com/forum/discussion/16578/"
        "quot-stocks-on-the-move-quot-momentum-strategy-by-cabedovestment/",
        "S&P 500 members ranked by slope times R2: a portfolio, not the desk's one-line rule",
        "2009 until 2024-01-16 (CabedoVestment; the book's own test ran 1994 to 2015)",
        "CAGR of 8.79% with a maximum drawdown of 24.1%; Win rate 59%",
    ),
    "connors_rsi2": Printed(
        Search.OTHER,
        "https://backtest.substack.com/p/the-2-period-rsi-a-simple-system",
        "Nasdaq 100 members, also requiring a close under the 5-day average",
        "December 2006 through late 2025, filled at the next open (Dave Johnson, March 2026)",
        "Annual return: 17.84%; Win rate: 64.33%; Average winner: +2.33%; Average loser: "
        "-3.02%; Max drawdown: 29.15%",
    ),
    "connors_percent_b": Printed(
        Search.NONE, _QS + "larry-connors-b-strategy-bollinger-eb7 (rules and numbers paywalled)"
    ),
    "connors_three_day_high_low": Printed(
        Search.NONE, _QS + "larry-connors-3-day-highlow-method-4f3 (rules and numbers paywalled)"
    ),
    "dan_zanger_breakout": Printed(Search.NONE, _NOWHERE + " (interviews only)"),
    "demark_sequential": Printed(
        Search.NONE, _OXFORD + "indicators/td-sequential-2/ (a futures test, numbers in images)"
    ),
    "faber_tactical": Printed(
        Search.AUTHOR,
        "https://mebfaber.com/wp-content/uploads/2016/05/SSRN-id962461.pdf",
        "S&P 500 total return (Cowles Commission and S&P data before 1971)",
        "1901-2012, filled at the month's last close (the February 2013 update)",
        "invested in the market approximately 70% of the time and making less than one "
        "round-trip trade per year; timing the S&P 500 returned 11.22%; compounded returns "
        "9.32% and 10.18%; drawdown from 83.66% to 42.24%; Taxes, commissions, and slippage "
        "are excluded",
    ),
    "kell_breakout": Printed(Search.NONE, _NOWHERE + " (interviews only)"),
    "keltner_channel_trend": Printed(Search.NONE, _NOWHERE + " (the 1960 rule defined only)"),
    "mansfield_rs_momentum": Printed(Search.NONE, _NOWHERE + " (indicator pages only)"),
    "minervini_breakout": Printed(
        Search.OTHER,
        "https://www.marketinout.com/blog/minervini-trend-template-backtest-markets",
        "the Trend Template alone on S&P 500 members, sold under the 200-day average",
        "from 2000 to 19 October 2026, at the close (MarketInOut, October 2026)",
        "max drawdown: S&P 500 members: 48% against 54% (SPY)",
    ),
    "dual_momentum": Printed(
        Search.NONE,
        "Antonacci, Absolute Momentum (2014): MSCI US, not the S&P 500, its rows unreadable",
    ),
    "weekly_reversal_jegadeesh": Printed(
        Search.OTHER,
        "https://econpapers.repec.org/RePEc:bla:jfinan:v:45:y:1990:i:3:p:881-98",
        "US stocks in decile portfolios on monthly forecasts, not the weekly rule",
        "1934-87 (Jegadeesh's abstract)",
        "The difference between the abnormal returns on the extreme decile portfolios over the "
        "period 1934-87 is 2.49 percent per month",
    ),
    "williams_r": Printed(Search.NONE, _NOWHERE + " at -90 and -10"),
    "weinstein_stage": Printed(Search.NONE, _NOWHERE + " (the method described only)"),
    "raschke_swing": Printed(
        Search.NONE, _OXFORD + "?p=5513 (42 futures 1980-2011, numbers in images only)"
    ),
}
"""Each rule's published test as found on 22 November 2026: Faber's alone is its author's own;
reproduction may be held only to a `candidate`."""
