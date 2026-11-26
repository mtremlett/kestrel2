"""stress - THE STRESS SCENARIOS (TST-06): what the worst days the desk can name did to a
strategy, and what a worse night would do, in pounds after every cost.

A rule can pass every rung on a history that was kind to it. Before any money follows it, the
desk asks what it lost when the market broke, in scenarios named here before any result.

THE EPISODES are stretches of the history itself, each named by the American market, the
world's, for every venue. The 2008 crash: from the first session after the S&P 500's closing
high of 9 October 2007 to its closing low of 9 March 2009, the whole fall of the worst market
of modern times (London's own low, 3 March 2009, lies inside it; its high of June 2007 before
it). The 2020 crash: from the first session after the market's high of 19 February to its low
of 23 March. The flash crashes: 6 May 2010, with the morning after, since London had shut
before New York fell; and 24 August 2015. A line whose bars do not reach back through 2008
has not been through it, and is untested there (below). A strategy's cost in an episode is
what the first rung's own priced trades (`lab/rung.py`) made from the close before it to its
last close, in pounds, each close at its own day's rate of exchange: a trade bought within it
is counted from the pounds it took, and one sold within it to the pounds it brought, less
every cost of both its legs, as the market's rung counts them on the day of the sale
(`lab/market.py`). The stop is in it as the broker works it: a day that falls through the
stop and closes back up has sold the shares at the stop. Out of the market throughout, the
rule lost nothing there, and that is said as a result: standing aside in a crash is a thing a
rule does.

UNTESTED IS NOT SURVIVED. An episode the rule was not shown able to trade through whole
shows nothing, and is given as untested (`made` is None), never as nothing lost. It is tested
only where the rule had bought once or more before it began, which is the proof that the
line was listed and the rule warm and trading by then; where the line has a bar for every
session of its venue in it, by the one calendar (`desk/venues.py`), since a fall on a day the
line did not trade, or that the archive does not hold, is a fall not seen; and where the
trades the first rung could judge run to its end (one the rule still holds at the window's
end is not judged, though its stop has sold it, so its days and all after are not counted).
A line listed in 2021 has not been through the 2020 crash, and nor has one listed a month
before it, its rule still warming: nothing here lets either seem to have. And
the window asked of is the line's whole history, from its first bar: a later start would
leave out a trade bought before it and held into an episode, so it is refused.

THE LEAST IT LOST, in a flash crash: the stop is filled as the desk's pretend broker fills
it, at its level or at the open under it, slipping as the one cost model says. On those two
days real stops were filled far lower. No daily bar says how far, so an episode's figure for
them is the least the rule lost, not the most. And a trade bought within an episode and
still held at its end has its buy's costs counted with its sale, after it.

THE GAP is planted, for the history holds too few: the stop sells at the stop only while the
market trades, and a night's fall goes straight through it. The fall is the black swan's own,
the one number the desk has already set beyond every day of its history
(`desk/emergency.py`), and the line opens that far below its last close TIMES ITS LEVERAGE,
read from the instrument master: a line of three times opens three tenths down, one of five
times at half. It is tried on every night each judged trade was held, the shares sold at that
open, as the desk sells everything in a black swan. Its cost is the night's own: what the
shares were worth at the close, less what they brought at the open after the costs of a
sale that slips as a stop's sale does; what the trade had made or lost before that night is
not the gap's. The worst of those nights is what a black swan's night, in its market's
terms, would take from this rule on this line. It is not the most a night can take: one
company's shares have fallen further in a night than the whole market ever has, and those
nights are in the bars only where an episode holds them. On a line not in pounds the close is
at the night's rate and the open at the morning's, so that night's own move of the currency
is in the figure, as it would be in the money.

THE BAR, AND ITS ONE HOME. STRESS_LIMIT is the loss the desk will bear in the worst scenario,
a part of the capital the strategy is given: `Stressed.judged` passes it at or under, fails it
above, naming the scenario, the pounds and the limit. Nothing tested gives THIN, never a pass.
The figure is for the line alone in the book as the first rung prices it. Five holdings hit
together lose as much each. A scenario the rule gained in reads as a cost under nothing.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext

from desk import orders, venues
from desk.emergency import Level
from desk.lines import Line
from desk.orders import Leg, Settings
from desk.store import Bar
from desk.strategy import ARITHMETIC
from lab import cell, rung
from lab.cell import Cell
from lab.rung import Answer, Priced, Rates, Verdict


@dataclass(frozen=True)
class Episode:
    name: str
    first: date  #: its first day and its last, both counted
    last: date


#: Named before any result, oldest first.
EPISODES = (
    Episode("the 2008 crash", date(2007, 10, 10), date(2009, 3, 9)),
    Episode("the flash crash of May 2010", date(2010, 5, 6), date(2010, 5, 7)),
    Episode("the flash crash of August 2015", date(2015, 8, 24), date(2015, 8, 24)),
    Episode("the 2020 crash", date(2020, 2, 20), date(2020, 3, 23)),
)
#: His ruling, Monday 16 November ~09:50 (option a of three; 10% and his own number were the
#: others): "fail a strategy whose worst stress-scenario loss exceeds 20% of the capital it is
#: given (a fifth of the account)".
STRESS_LIMIT = Decimal("0.20")
#: The night's fall of the gap, in the market's terms: a black swan's day.
FALL = Level.BLACK_SWAN.value.day


@dataclass(frozen=True)
class Replay:
    episode: Episode
    trades: tuple[Priced, ...]  #: those held on a day of it
    made: Decimal | None  #: pounds across it after costs, a loss under nothing; None: untested


@dataclass(frozen=True)
class Gap:
    morning: date  #: the worst morning to have woken to it
    open: Decimal  #: the price it opened at, in the line's currency
    trade: Priced  #: the trade held that night
    lost: Decimal  #: pounds the night took: the close's worth, less the sale's after its costs


@dataclass(frozen=True)
class Stressed:
    verdict: Verdict  #: the first rung's on the whole window, whose trades these are
    capital: Decimal  #: the one capital number the trades were sized from
    episodes: tuple[Replay, ...]  #: every one of EPISODES, in its order
    gap: Gap | None  #: None where no judged trade was held a night

    @property
    def untested(self) -> tuple[str, ...]:
        """The episodes it was not shown able to trade through whole: nothing is known there."""
        return tuple(replay.episode.name for replay in self.episodes if replay.made is None)

    def _costs(self) -> list[tuple[str, Decimal]]:
        """Every scenario tested with the pounds it cost, a gain as a cost under nothing."""
        costs = [(r.episode.name, -r.made) for r in self.episodes if r.made is not None]
        if self.gap is not None:
            costs.append((f"a black swan's night, waking {self.gap.morning}", self.gap.lost))
        return costs

    @property
    def worst(self) -> Decimal | None:
        """The most a scenario cost, as a part of the capital, on this line alone in the
        book: under nothing where it gained in every one; None when nothing was tested."""
        costs = self._costs()
        with localcontext(ARITHMETIC):
            return max(pounds for _, pounds in costs) / self.capital if costs else None

    def judged(self) -> tuple[Answer, str]:
        """PASS when the worst scenario cost no more than STRESS_LIMIT of the capital, FAIL
        above it; THIN when no scenario was tested. The reason names scenario, pounds, limit."""
        costs = self._costs()
        if not costs:
            return Answer.THIN, "no scenario was tested: the line was not shown through one"
        name, pounds = max(costs, key=lambda cost: cost[1])
        with localcontext(ARITHMETIC):
            limit = STRESS_LIMIT * self.capital
        answer = Answer.PASS if pounds <= limit else Answer.FAIL
        return answer, f"worst: {name} lost {pounds:,.2f} pounds; the limit is {limit:,.2f}"


def judge(window: Cell, bars: Sequence[Bar], settings: Settings, rates: Rates) -> Stressed:
    """The trades of the line's whole history, priced by the first rung, taken through every
    episode the rule was shown able to trade through and through the gap, each fill and each
    close at its own day's rate."""
    record, read = cell.run(window, bars), cell.shown(window, bars)
    if read[0].day < window.start:
        raise ValueError(
            f"{window}: the line's bars begin on {read[0].day}, and a trade bought before the "
            "window would be left out of an episode it was held into: ask of the whole history"
        )
    verdict = rung.judge(record, bars, settings, rates)
    judged = {priced.trade for priced in verdict.trades}
    #: the days counted end where the first rung's judging does: at a trade it could not judge
    until = min((t.bought for t in record.trades if t not in judged), default=read[-1].day)
    #: and begin once the rule has bought: it was listed, warm and trading before the episode
    since = min((t.bought for t in record.trades), default=date.max)
    have = {bar.day for bar in read}

    def shown(episode: Episode) -> bool:
        sessions = venues.sessions(window.line.venue, episode.first, episode.last)
        return since < episode.first and episode.last <= until and have.issuperset(sessions)

    with localcontext(ARITHMETIC):
        replays = tuple(
            _replay(episode, verdict.trades, read, window.line, rates)
            if shown(episode)
            else Replay(episode, (), None)
            for episode in EPISODES
        )
        gap = _gap(verdict.trades, read, window.line, rates)
    return Stressed(verdict, settings.capital, replays, gap)


def _replay(
    episode: Episode, trades: Sequence[Priced], read: Sequence[Bar], line: Line, rates: Rates
) -> Replay:
    """What the trades held on a day of the episode made from the close before it to its last."""
    days = [bar.day for bar in read]
    before, last = bisect_left(days, episode.first) - 1, bisect_right(days, episode.last) - 1
    held = tuple(p for p in trades if p.held[0] <= episode.last and episode.first <= p.held[1])
    made = Decimal(0)
    for p in held:
        began = p.paid if episode.first <= p.held[0] else _worth(p, read[before], line, rates)
        if p.held[1] <= episode.last:
            made += p.received - p.costs.total - began
        else:
            made += _worth(p, read[last], line, rates) - began
    return Replay(episode, held, made)


def _worth(priced: Priced, bar: Bar, line: Line, rates: Rates) -> Decimal:
    """Pounds the trade's shares were worth at the bar's close, at that day's rate."""
    return priced.shares * bar.close * rung.rate(line, rates, bar.day)


def _gap(trades: Sequence[Priced], read: Sequence[Bar], line: Line, rates: Rates) -> Gap | None:
    """The gap tried on every night a trade was held; the one that took most."""
    at = {bar.day: n for n, bar in enumerate(read)}
    worst: Gap | None = None
    for p in trades:
        first, last = at[p.held[0]], at[p.held[1]]
        for night, morning in zip(read[first:last], read[first + 1 : last + 1], strict=True):
            opened = night.close * (1 - FALL * line.leverage)
            rate = rung.rate(line, rates, morning.day)
            sold = orders.charges(line, Leg.STOP, p.shares, opened, rate)
            lost = _worth(p, night, line, rates) + sold.total - p.shares * opened * rate
            if worst is None or lost > worst.lost:
                worst = Gap(morning.day, opened, p, lost)
    return worst
