"""scalping - rules on one-minute bars (VwapReversion below), research: in no desk mapping
and never trade until it passes the ladder. The idea is Pradeep Bonde's "momentum burst"
(Stockbee, 2010s, taught on daily bars: a few days' sharp move on range that carries on a few
more); here it is worked on the one-minute bars of a session, an adaptation that is ours. Buy
when the close has risen over the last LOOKBACK bars by more than BURST times their average
range; sell after HOLD_BARS bars held or a close under the entry bar's low; be out at the
session's last bar. A new session empties the window.

SET SCALP (R-RUNNER-358): `judge_set` runs both rules on every line the store holds one-minute
bars for, every session it holds, enters every trial in the register first, and writes
`ladder/sets/SCALP.md` (PRE-REVIEW) with each line's round-trip cost and the edge it needs."""

from __future__ import annotations

import hashlib
import inspect
import sqlite3
from collections.abc import Callable, Sequence
from contextlib import closing
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import ClassVar

from desk import bars as store
from desk import intraday, orders, venues
from desk.command import CAPITAL
from desk.intraday import IntradayRule, Span
from desk.lines import LINES, Line
from desk.orders import Leg, Settings
from desk.rollup import Candle
from desk.strategy import Action, Decision
from lab import history_bars, ladder, rung, trials, universe, verdict_parts
from lab.intraday import judged, priced
from lab.rung import Priced, Rates

LOOKBACK = 3  #: bars the rise is measured over
BURST = Decimal(2)  #: how many average ranges the rise must exceed
HOLD_BARS = 10  #: bars a position is kept, the entry bar not counted
BELOW_VWAP = Decimal("0.01")  #: how far under the VWAP, as a fraction of it, a close is bought


def _session(venue: str, bar: Candle) -> venues.Hours:
    """The venue's session the bar falls in; a bar outside any is an error."""
    found = venues.open_at(venue, bar.start)
    if found is None:
        raise ValueError(f"{bar.start}: outside {venue}'s session")
    return found


class MomentumBurst:
    """Bonde's momentum burst on one-minute bars, a new session resetting the window."""

    span: ClassVar[Span] = Span.ONE_MINUTE

    def __init__(self, venue: str = "LSE") -> None:
        self.venue = venue
        self.opened: datetime | None = None
        self.window: list[Candle] = []
        self.held = 0
        self.stop = Decimal(0)  #: the entry bar's low

    def step(self, bar: Candle, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        found = _session(self.venue, bar)
        if found.open != self.opened:
            self.opened, self.window = found.open, []
        self.window = [*self.window, bar][-(LOOKBACK + 1) :]
        if bar.start + timedelta(minutes=self.span.value) >= found.close:
            return False
        if holding:
            self.held += 1
            return self.held < HOLD_BARS and bar.close >= self.stop
        if len(self.window) <= LOOKBACK or not self._burst():
            return False
        self.held, self.stop = 0, bar.low
        return True

    def _burst(self) -> bool:
        """Whether the close rose over the window by more than BURST average ranges."""
        recent = self.window[1:]
        average = sum((b.high - b.low for b in recent), Decimal(0)) / LOOKBACK
        return self.window[-1].close - self.window[0].close > BURST * average


class VwapReversion:
    """A one-minute mean reversion to the session's VWAP, a new session resetting it. VWAP, the
    volume-weighted average price, is the institutional benchmark of Berkowitz, Logue and Noser
    ("The Total Cost of Transactions on the NYSE", Journal of Finance, 1988); trading a close
    back to it from BELOW_VWAP under is the common practitioner's use, the rule here ours.
    Buy a close that far under the VWAP, sell at or over it, be out at the session's last bar;
    a bar of no volume adds nothing to the VWAP."""

    span: ClassVar[Span] = Span.ONE_MINUTE

    def __init__(self, venue: str = "LSE") -> None:
        self.venue = venue
        self.opened: datetime | None = None
        self.worth = Decimal(0)  #: typical price times volume, summed over the session
        self.volume = 0

    @property
    def vwap(self) -> Decimal | None:
        """The VWAP of the bars seen this session, None until one has traded."""
        return self.worth / self.volume if self.volume else None

    def step(self, bar: Candle, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        found = _session(self.venue, bar)
        if found.open != self.opened:
            self.opened, self.worth, self.volume = found.open, Decimal(0), 0
        self.worth += (bar.high + bar.low + bar.close) / 3 * bar.volume
        self.volume += bar.volume
        vwap = self.vwap
        if vwap is None or bar.start + timedelta(minutes=self.span.value) >= found.close:
            return False
        return bar.close < vwap if holding else bar.close < vwap * (1 - BELOW_VWAP)


def round_trip_cost(
    line: Line, price: Decimal, day: date, rates: Rates, settings: Settings
) -> Decimal:
    """What a round trip costs on the line at the size the rung sizes, as a fraction of the
    price paid: both legs by `orders.charges` (commission, fees, half the spread, slippage,
    conversion, UK tax), the buy and the sale both at `price`."""
    fx = rung.rate(line, rates, day)
    buy = Decision("cost", line.symbol, day, Action.BUY)
    shares = orders.size(buy, line, price, fx, settings, {}).quantity
    both = orders.charges(line, Leg.BUY, shares, price, fx) + orders.charges(
        line, Leg.SALE, shares, price, fx
    )
    return both.total / (shares * price * fx)


def edge_needed(cost: Decimal, trades: Sequence[Priced]) -> Decimal | None:
    """The gain per trade, before costs, the first rung needs to pass the trades seen: the
    round trip's cost plus T_PASS standard errors of their gains; None under two trades."""
    found = rung.mean_and_error([p.gain for p in trades])
    return None if found is None else cost + rung.T_PASS * found[1]


def trades_of(
    rule: IntradayRule, line: Line, bars: Sequence[Candle], rates: Rates, settings: Settings
) -> tuple[Priced, ...]:
    """The rule run on one session's bars, its trades priced through `lab.intraday.priced`."""
    got = intraday.run(type(rule).__name__, rule, line.venue, line.symbol, bars)
    return priced(line, [*got], bars, rates, settings)


TAG = "SCALP"
QUESTION = "set SCALP: does a scalping rule earn on a line the store holds one-minute bars for?"
HELD = "SELECT venue, symbol FROM held WHERE span = ?"
FAR = datetime(2100, 1, 1, tzinfo=UTC)
RULES: dict[str, Callable[[str], IntradayRule]] = {
    "momentum_burst": MomentumBurst,
    "vwap_reversion": VwapReversion,
}


def lines(home: Path) -> tuple[Line, ...]:
    """The lines the store holds one-minute bars for, the desk's own first, then the research
    list's."""
    file = history_bars.database(home)
    if not file.is_file():
        raise FileNotFoundError(f"{file}: no live database to take the scalping set's lines from")
    with closing(sqlite3.connect(file)) as held:
        kept = set(held.execute(HELD, ("1m",)).fetchall())
    both = dict.fromkeys((*LINES, *universe.UNIVERSE))
    return tuple(line for line in both if (line.venue, line.symbol) in kept)


def trial(rule: str, line: Line) -> str:
    """A trial's name: the rule, the line and venue, and the hash of the rule's code, so a rule
    that is changed is new trials, never a free second look."""
    code = hashlib.sha256(inspect.getsource(RULES[rule]).encode()).hexdigest()[:12]
    return f"{rule} {line.symbol} {line.venue} one-minute {code}"


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
    held = store.timed(path, line, "1m", store.EPOCH, FAR)
    made: list[Priced] = []
    for day in sorted({b.start.date() for b in held}):
        session = intraday.session(path, line, Span.ONE_MINUTE, day)
        made += trades_of(RULES[rule](line.venue), line, session, rates, settings)
    return tuple(made)


def _costs(
    line: Line, trades: Sequence[Priced], rates: Rates, settings: Settings
) -> tuple[str, str]:
    """The round trip's cost at the first trade's price and the edge needed, as percentages;
    a dash where there is no trade or fewer than two."""
    if not trades:
        return "-", "-"
    first = trades[0]
    price = first.paid / first.shares / rung.rate(line, rates, first.held[0])
    cost = round_trip_cost(line, price, first.held[0], rates, settings)
    edge = edge_needed(cost, trades)
    return f"{cost:.4%}", "-" if edge is None else f"{edge:.4%}"


def judge_set(home: Path, rates: Rates) -> str:
    """Set SCALP: both rules on each line, the trials entered first, the table written and
    `SET SCALP: <n> rules, <passed> passed, table <path>` said. A line with too few trades is
    THIN, never a fail; one the store cannot serve whole is a row that says why."""
    held = lines(home)
    todo = [(rule, line) for rule in RULES for line in held]
    register = _register(home, [trial(rule, line) for rule, line in todo])
    path, settings, rows = history_bars.database(home), Settings(CAPITAL), []
    for rule, line in todo:
        try:
            trades = _line_trades(path, rule, line, rates, settings)
            cost, edge = _costs(line, trades, rates, settings)
            rows.append((rule, line, f"{len(trades)} trades", judged(trades).name, cost, edge))
        except (ValueError, LookupError) as refusal:
            rows.append((rule, line, "refused", str(refusal).replace("|", "/"), "-", "-"))
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
    out += ["| rule | line | trades | answer | round-trip cost | edge needed |"]
    out += ["|---|---|---|---|---|---|"]
    out += [
        f"| {r} | {ln.symbol} ({ln.venue}) | {t} | {a} | {c} | {e} |" for r, ln, t, a, c, e in rows
    ]
    table.write_text(chr(10).join(out) + chr(10), encoding="utf-8")
    passed = sum(row[3] == "PASS" for row in rows)
    return f"SET {TAG}: {len(RULES)} rules, {passed} passed, table {table}"
