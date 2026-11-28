"""weather - THE MARKET WEATHER RECORDED BEFORE IT ACTS (REG-01, REG-07): each line's realised
volatility, one reading a day, kept in a file beside the data and read by nothing that trades.

A day's reading is the standard deviation of the last VOL_DAYS daily returns up to that day's
close (the one `risk.volatility`), so it never reads a later bar (canon B3): cutting the bars
after T changes no reading up to T. Fewer than VOL_DAYS returns give no reading, never a guess.
Recording adds only days not yet written, so a second call changes nothing. Sizing by it waits
for its own pass of the ladder; this module only records."""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path

from desk.risk import volatility
from desk.store import Bar

#: Daily returns in one reading: about a trading month.
VOL_DAYS = 20


def realised_volatility(bars: Sequence[Bar]) -> dict[date, Decimal]:
    """Each day's volatility from the VOL_DAYS returns ending on it; one bar a day."""
    days = [bar.day for bar in bars]
    if len(set(days)) != len(days) or days != sorted(days):
        raise ValueError("bars must be one per day, oldest first, to be read in order")
    closes = [float(bar.close) for bar in bars]
    moves = [closes[n] / closes[n - 1] - 1 for n in range(1, len(closes))]
    return {
        days[n + 1]: volatility(tuple(moves[n + 1 - VOL_DAYS : n + 1]))
        for n in range(VOL_DAYS - 1, len(moves))
    }


def record(folder: Path, symbol: str, bars: Sequence[Bar]) -> int:
    """Append the days of `symbol` not yet in its file `folder/<symbol>.jsonl`; the count added."""
    path = folder / f"{symbol}.jsonl"
    held: set[str] = set()
    if path.exists():
        with path.open() as lines:
            held = {json.loads(line)["day"] for line in lines}
    fresh = [
        {"day": day.isoformat(), "volatility": str(vol)}
        for day, vol in realised_volatility(bars).items()
        if day.isoformat() not in held
    ]
    folder.mkdir(parents=True, exist_ok=True)
    with path.open("a") as out:
        out.writelines(json.dumps(row) + "\n" for row in fresh)
    return len(fresh)
