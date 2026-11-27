"""intraday - the opening range breakout on five-minute bars (Crabel, Day Trading with Short Term
Price Patterns and Opening Range Breakout, 1990), a research rule: it is in no desk mapping and
never trades until it passes the ladder. The range is the session's first six bars (30 minutes);
after them buy a close above its high, sell a close under its low, and be out at the last bar.

It also prices the intraday engine's trades for the ladder's rule (R-RUNNER-354): `priced` takes
a session's decisions, fills each at the NEXT bar's open (a decision on the session's last bar
fills nowhere: the position is forced out at that bar's close), sizes a buy as the first rung
does, and charges both legs by `orders.charges` in pounds; `judged` is rung.decide on
rung.standard_errors. No cost or verdict rule is written here.

SET INTRADAY (R-RUNNER-355): `judge_set` runs both rules on every line the store holds
five-minute bars for (the `held` table of market_live.db), every session it holds, enters every
trial in the register (lab/trials.py) before the first is judged, and writes
`ladder/sets/INTRADAY.md`, PRE-REVIEW until the blind review (R-RUNNER-40) is clean."""

from __future__ import annotations

import hashlib
import inspect
import sqlite3
from collections.abc import Callable, Sequence
from contextlib import closing
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import ClassVar

from desk import bars as store
from desk import intraday, orders, venues
from desk.command import CAPITAL
from desk.intraday import IntradayDecision, IntradayRule, Span
from desk.lines import LINES, Line
from desk.orders import Leg, Settings
from desk.rollup import Candle
from desk.strategy import Action, Decision, _Window, lower_band
from lab import history_bars, ladder, rung, trials, universe, verdict_parts
from lab.cell import Trade
from lab.rung import Answer, Priced, Rates

RANGE_BARS = 6  #: the opening range: the session's first six five-minute bars
BAND_BARS = 20  #: Bollinger's band: the session's last twenty five-minute closes


class OpeningRangeBreakout:
    """Crabel's opening range breakout on five-minute bars, a new session resetting the range."""

    span: ClassVar[Span] = Span.FIVE_MINUTES

    def __init__(self, venue: str = "LSE") -> None:
        self.venue = venue
        self.opened: datetime | None = None
        self.seen = 0
        self.high = self.low = Decimal(0)

    def step(self, bar: Candle, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        found = venues.open_at(self.venue, bar.start)
        if found is None:
            raise ValueError(f"{bar.start}: outside {self.venue}'s session")
        if found.open != self.opened:
            self.opened, self.seen, self.high, self.low = found.open, 0, bar.high, bar.low
        if self.seen < RANGE_BARS:
            self.seen += 1
            self.high, self.low = max(self.high, bar.high), min(self.low, bar.low)
            return False
        if bar.start + timedelta(minutes=self.span.value) >= found.close:
            return False
        return bar.close >= self.low if holding else bar.close > self.high


class IntradayMeanReversion:
    """Bollinger's bands (Bollinger on Bollinger Bands, 2001) on five-minute bars, 20 bars and 2
    deviations counted within the session: buy a close under the lower band, sell a close over
    the middle, be out at the last bar. Each session refills the band, holding nothing till full."""

    span: ClassVar[Span] = Span.FIVE_MINUTES

    def __init__(self, venue: str = "LSE") -> None:
        self.venue = venue
        self.opened: datetime | None = None
        self.closes = _Window(BAND_BARS)

    def step(self, bar: Candle, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        found = venues.open_at(self.venue, bar.start)
        if found is None:
            raise ValueError(f"{bar.start}: outside {self.venue}'s session")
        if found.open != self.opened:
            self.opened, self.closes = found.open, _Window(BAND_BARS)
        self.closes.add(bar.close)
        if not self.closes.full or bar.start + timedelta(minutes=self.span.value) >= found.close:
            return False
        mean = self.closes.mean()
        if holding:
            return bar.close <= mean
        return bar.close < lower_band(mean, self.closes.deviation())


def _leg(
    line: Line, rates: Rates, shares: int, leg: Leg, price: Decimal, at: Candle
) -> tuple[Decimal, orders.Charges]:
    """A leg's value and every cost, in pounds at the day's rate."""
    fx = rung.rate(line, rates, at.start.date())
    return shares * price * fx, orders.charges(line, leg, shares, price, fx)


def priced(
    line: Line,
    decisions: Sequence[IntradayDecision],
    bars: Sequence[Candle],
    rates: Rates,
    settings: Settings,
) -> tuple[Priced, ...]:
    """One session's trades, priced: a buy fills at the next bar's open, sized at the deciding
    bar's close; a sale likewise, or at the last bar's close when nothing comes after it."""
    if len(decisions) != len(bars):
        raise ValueError(f"{line.symbol}: {len(decisions)} decisions for {len(bars)} bars")
    made: list[Priced] = []
    buying: tuple[Candle, orders.Order] | None = None
    for n, (decision, bar) in enumerate(zip(decisions, bars, strict=True)):
        later = bars[n + 1] if n + 1 < len(bars) else None
        if decision.action is Action.BUY and later is not None and buying is None:
            fx = rung.rate(line, rates, later.start.date())
            day = Decision(decision.strategy, line.symbol, later.start.date(), Action.BUY)
            buying = (later, orders.size(day, line, bar.close, fx, settings, {}))
        last = later is None
        if buying is not None and (decision.action is Action.SELL or last):
            out, price = (bar, bar.close) if later is None else (later, later.open)
            (into, order) = buying
            paid, bought = _leg(line, rates, order.quantity, Leg.BUY, into.open, into)
            got, sold = _leg(line, rates, order.quantity, Leg.SALE, price, out)
            held = (into.start.date(), out.start.date())
            made.append(Priced(Trade(*held), order.quantity, paid, got, bought + sold, held, None))
            buying = None
    return tuple(made)


def judged(trades: Sequence[Priced]) -> Answer:
    """The first rung's one rule on the trades' gains: THIN under MIN_TRADES; no spread refused."""
    return rung.decide(len(trades), rung.standard_errors([p.gain for p in trades]))


TAG = "INTRADAY"
QUESTION = (
    "set INTRADAY: does an intraday rule earn on a line the store holds five-minute bars for?"
)
HELD = "SELECT venue, symbol FROM held WHERE span = ?"
FAR = datetime(2100, 1, 1, tzinfo=UTC)
RULES: dict[str, Callable[[str], IntradayRule]] = {
    "opening_range_breakout": OpeningRangeBreakout,
    "intraday_mean_reversion": IntradayMeanReversion,
}


def lines(home: Path) -> tuple[Line, ...]:
    """The lines the store holds five-minute bars for, the desk's own first, then the research
    list's, as `history_bars.lines` reads the daily ones."""
    file = history_bars.database(home)
    if not file.is_file():
        raise FileNotFoundError(f"{file}: no live database to take the intraday set's lines from")
    with closing(sqlite3.connect(file)) as held:
        kept = set(held.execute(HELD, (store.FIVE,)).fetchall())
    both = dict.fromkeys((*LINES, *universe.UNIVERSE))
    return tuple(line for line in both if (line.venue, line.symbol) in kept)


def trial(rule: str, line: Line) -> str:
    """A trial's name: the rule, the line and venue, and the hash of the rule's code, so a rule
    that is changed is new trials, never a free second look."""
    code = hashlib.sha256(inspect.getsource(RULES[rule]).encode()).hexdigest()[:12]
    return f"{rule} {line.symbol} {line.venue} five-minute {code}"


def _register(home: Path, todo: Sequence[str]) -> Path:
    """The set's register, begun on its first run, with every trial of this run entered."""
    register = home / ladder.FOLDER / f"{TAG}.trials.jsonl"
    if not register.exists():
        register.parent.mkdir(parents=True, exist_ok=True)
        trials.start(register)
        trials.ask(register, QUESTION)
    trials.enter(register, QUESTION, todo)
    return register


def _line_trades(
    path: Path, rule: str, line: Line, rates: Rates, settings: Settings
) -> tuple[Priced, ...]:
    """Every session the store holds for the line, the rule run on each and its trades priced."""
    held = store.five(path, line, store.EPOCH, FAR)
    made: list[Priced] = []
    for day in sorted({b.start.date() for b in held}):
        session = intraday.session(path, line, Span.FIVE_MINUTES, day)
        got = intraday.run(rule, RULES[rule](line.venue), line.venue, line.symbol, session)
        made += priced(line, [*got], session, rates, settings)
    return tuple(made)


def judge_set(home: Path, rates: Rates) -> str:
    """Set INTRADAY: both rules on each line, the trials entered first, the table written and
    `SET INTRADAY: <n> rules, <passed> passed, table <path>` said. A line the store cannot
    serve whole is a row that says why, never a guess."""
    held = lines(home)
    todo = [(rule, line) for rule in RULES for line in held]
    register = _register(home, [trial(rule, line) for rule, line in todo])
    path, settings, rows = history_bars.database(home), Settings(CAPITAL), []
    for rule, line in todo:
        try:
            trades = _line_trades(path, rule, line, rates, settings)
            answer = judged(trades)
            rows.append((rule, line, f"{len(trades)} trades", answer.name))
        except (ValueError, LookupError) as refusal:
            rows.append((rule, line, "refused", str(refusal).replace("|", "/")))
    table = home / ladder.FOLDER / "sets" / f"{TAG}.md"
    table.parent.mkdir(parents=True, exist_ok=True)
    built = ladder.rungs_built()
    out = [
        f"# SET {TAG} - {verdict_parts.STATUS}",
        "",
        f"rungs built: {built[0]} of {built[1]}",
        "",
    ]
    out += [QUESTION]
    out += [f"Each is judged against {trials.count(register, QUESTION)} trials.", ""]
    out += ["| rule | line | trades | answer |", "|---|---|---|---|"]
    out += [f"| {r} | {ln.symbol} ({ln.venue}) | {t} | {a} |" for r, ln, t, a in rows]
    table.write_text(chr(10).join(out) + chr(10), encoding="utf-8")
    passed = sum(a == "PASS" for *_, a in rows)
    return f"SET {TAG}: {len(RULES)} rules, {passed} passed, table {table}"
