"""pnl - THE HOURLY PROFIT AND LOSS, in a few lines for his phone. One pure function: the
book and the bars in, words out. The day's profit is what the desk gained since the last
close, after every cost (the one cost model, desk/orders.py): what it held then moved from
that close to the newest bar, and each of today's fills from its price to that bar. Pounds
at the day's rate, exact, rounded once to the penny where it is told (B4). Beside it, what
the capital would have gained simply holding the market (the yardstick), and each holding's
move. A line with no bar yet today is told so, never as calm."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path

from desk import bars, book, halt, venues
from desk.broker import Fill
from desk.lines import YARDSTICK, Line
from desk.orders import charges, leg_of, pennies
from desk.store import Bar

BAR = timedelta(minutes=5)


class Mood(Enum):
    """The desk's state, as the message tells it."""

    TRADING = "✅ trading"
    HALTED = "⏸️ halted"
    KILLED = "🛑 killed"


def _sign(amount: Decimal) -> str:
    return "+" if amount > 0 else "-" if amount < 0 else ""


def _icon(amount: Decimal | None) -> str:
    return "⚪" if not amount else "🟢" if amount > 0 else "🔴"


def _move(close: Decimal, now: Decimal | None) -> Decimal | None:
    """A price's move since the close, exact, as a fraction; None with no bar today."""
    return None if now is None else now / close - 1


def _percent(move: Decimal | None) -> str:
    if move is None:
        return "no bar yet"
    percent = pennies(move * 100)
    return f"{_sign(percent)}{abs(percent)}%"


def _pounds(amount: Decimal) -> str:
    return f"{_sign(amount)}£{abs(amount):,.2f}"


def report(
    now: datetime,
    lines: Sequence[Line],
    before: Mapping[str, int],
    fills: Sequence[Fill],
    closes: Mapping[str, Decimal],
    last: Mapping[str, Decimal],
    rates: Mapping[str, Decimal],
    capital: Decimal,
    mood: Mood,
) -> str:
    """The message: what was held at the last close (before), today's fills, each line's last
    close and newest bar price (last, absent when it has none today), the day's pounds per
    unit of currency, the capital, and the desk's state."""
    known = {line.symbol: line for line in lines}
    fx = {s: Decimal(1) if known[s].currency == "GBP" else rates[known[s].currency] for s in closes}
    price = {symbol: last.get(symbol, close) for symbol, close in closes.items()}
    held, gain = dict(before), Decimal(0)
    for symbol, shares in before.items():
        gain += shares * (price[symbol] - closes[symbol]) * fx[symbol]
    for fill in fills:
        symbol, leg = fill.symbol, leg_of(fill.order_id, fill.quantity)
        cost = charges(known[symbol], leg, abs(fill.quantity), fill.price, fx[symbol]).total
        gain += fill.quantity * (price[symbol] - fill.price) * fx[symbol] - cost
        held[symbol] = held.get(symbol, 0) + fill.quantity
    day = pennies(gain)
    moves = {symbol: _move(close, last.get(symbol)) for symbol, close in closes.items()}
    rows = [
        f"{_icon(moves[symbol])} {symbol} {shares} sh {_percent(moves[symbol])}"
        for symbol, shares in sorted(held.items())
        if shares
    ]
    move = moves[YARDSTICK.symbol]
    worth = f"{_pounds(pennies(capital * move))} ({_percent(move)})" if move else _percent(move)
    return "\n".join(
        [
            f"📊 Desk {venues.uk_time(now):%H:%M} UK",
            f"{_icon(day)} Day {_pounds(day)} after costs",
            *rows,
            f"{_icon(move)} Holding the market: {worth}",
            mood.value,
        ]
    )


def told(
    root: Path,
    hot: Path,
    daily: Mapping[Line, Sequence[Bar]],
    rates: Mapping[str, Decimal],
    capital: Decimal,
    now: datetime,
) -> str:
    """The message for a moment in UTC, from the ledger at root, the fast store of
    five-minute bars at hot and each line's daily bars (a line with none before today is not
    asked about unless held). A bar is read once it has ended."""
    today, mood = now.date(), Mood.TRADING
    before = book.positions(root, today - timedelta(days=1))
    fills = [fill for fill in book.fills(root) if fill.day == today]
    needed = {*before, *(fill.symbol for fill in fills), YARDSTICK.symbol}
    closes, last = {}, {}
    for line, history in daily.items():
        if line.symbol not in needed:
            continue
        closes[line.symbol] = [bar for bar in history if bar.day < today][-1].close
        try:
            ended = bars.five(hot, line, datetime.combine(today, time(), UTC), now)
        except LookupError:  #: the store never held a bar of the line: it has none today
            continue
        if news := [bar for bar in ended if bar.start + BAR <= now]:
            last[line.symbol] = news[-1].close
    if halt.in_force(root):
        mood = Mood.HALTED
    if book.killed(root):
        mood = Mood.KILLED
    return report(now, list(daily), before, fills, closes, last, rates, capital, mood)
