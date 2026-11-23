"""day_money - WHAT THE BOOK IS WORTH, HOW HOT, AND HOW MUCH IT CONTROLS per underlying market,
each read from the saved bars and the ledger at a day's end."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path

from desk import book, venues
from desk.lines import Line
from desk.orders import pennies
from desk.store import Bar


def worth(root: Path, archive: Mapping[Line, Sequence[Bar]], upto: date) -> Decimal:
    """What the book held at a day's end was worth, in pounds: each line at its close then,
    at the rate kept for that very day."""
    lines = {line.symbol: line for line in archive}
    return sum(
        (
            shares * close(archive, lines[s], upto) * book.rate(root, lines[s].currency, upto)
            for s, shares in book.positions(root, upto).items()
        ),
        Decimal(0),
    )


def heat(root: Path, archive: Mapping[Line, Sequence[Bar]], upto: date) -> Decimal | None:
    """The book's heat at a day's end, in pounds: each held line's shares times the larger of
    what falls from its newest buy's price to the stop kept for it, and the worst overnight
    gap down (a close to the next open) in its bars since that buy, at the day's rate. None
    if a held line's stop level was never kept: the heat is then not known."""
    kept, lines = book.levels(root), {line.symbol: line for line in archive}
    buys = {f.symbol: f for f in book.fills(root) if f.quantity > 0 and f.day <= upto}
    heat = Decimal(0)
    for symbol, shares in book.positions(root, upto).items():
        buy, line = buys[symbol], lines[symbol]
        if (stop := kept.get(f"{buy.order_id}-stop")) is None:
            return None
        bars = [bar for bar in archive[line] if buy.day <= bar.day <= upto]
        gaps = (before.close - after.open for before, after in zip(bars, bars[1:], strict=False))
        fall = max(buy.price - stop, *gaps, Decimal(0))
        heat += shares * fall * book.rate(root, line.currency, upto)
    return pennies(heat)


def close(archive: Mapping[Line, Sequence[Bar]], line: Line, upto: date) -> Decimal:
    """The line's close at a day's end: its newest bar's by then. A session of its venue
    since that bar, the line not suspended, is a bar owed: an error, never an older price."""
    bars = [bar for bar in archive.get(line, ()) if bar.day <= upto]
    since = venues.sessions(line.venue, bars[-1].day, upto) if bars else (upto,)
    owed = [on for on in since if not bars or (on > bars[-1].day and on not in line.suspended)]
    if owed:
        raise ValueError(f"{upto}: no close of {line.symbol} for {owed}, so the day has no record")
    return bars[-1].close


def exposure(
    root: Path, archive: Mapping[Line, Sequence[Bar]], rates: Mapping[str, Decimal]
) -> dict[str, Decimal]:
    """THE POUNDS THE BOOK CONTROLS PER UNDERLYING MARKET (risk.underlying_limit): each held
    line's shares at its last close and the day's rate, counted at its leverage."""
    held, total = book.positions(root), dict[str, Decimal]()
    for line, bars in archive.items():
        if line.symbol in held:
            key = line.underlying or line.symbol
            value = held[line.symbol] * bars[-1].close * rates[line.currency] * line.leverage
            total[key] = total.get(key, Decimal(0)) + value
    return total


def fx_split(
    root: Path, archive: Mapping[Line, Sequence[Bar]], day: date
) -> tuple[Decimal, Decimal, Decimal] | None:
    """BIC-04: the closed trades' gross owed to the currency, the rest of it trading, and what
    the open holdings owe the currency. None when nothing traded or a fill's day has no rate."""
    ledger, lines = book.fills(root), tuple(archive)
    kept, money = book.rates_kept(root), {line.symbol: line.currency for line in lines}
    if not ledger or any((f.day, money.get(f.symbol)) not in kept for f in ledger):
        return None
    trips = book.round_trips(root, lines)
    gain = book.currency_gain(root, lines, trips)
    last = {line.symbol: bars[-1].close for line, bars in archive.items()}
    today = all((day, m) in kept for m in set(money.values()))
    held = book.open_currency_gain(root, lines, last, day) if today else Decimal(0)
    return gain, sum((t.gross for t in trips), Decimal(0)) - gain, held


def idle_interest(
    root: Path, archive: Mapping[Line, Sequence[Bar]], day: date, capital: Decimal, annual: Decimal
) -> Decimal | None:
    """BIC-03: what idle cash earned at the yearly rate from the first fill to day. None when
    nothing traded or a fill's day has no rate."""
    ledger, lines = book.fills(root), tuple(archive)
    kept, money = book.rates_kept(root), {line.symbol: line.currency for line in lines}
    if not ledger or any((f.day, money.get(f.symbol)) not in kept for f in ledger):
        return None
    return book.interest(root, lines, capital, annual, min(f.day for f in ledger), day)
