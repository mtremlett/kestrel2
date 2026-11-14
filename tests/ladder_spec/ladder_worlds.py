"""The known-answer worlds of the ladder's spec (`lab/ladder.py`): histories whose answer is
known because it was planted, one world a seed, the same bars every time.

A world is sixteen lines, each a history of its own, eight in London in pounds and eight in
New York in dollars at one rate of exchange, and the market each venue's are set beside.
Four kinds, and the answer each must be given by the one verdict:

    EDGE      a breakout goes on rising: the rule's own edge, planted          PASS
    BELL      a walk with no memory and no rise: nothing to find               FAIL
    DRIFT     a line that climbs of itself, with nothing to time               FAIL
    LOPSIDED  nine trades in ten a small win, one in ten a loss at the         FAIL
              desk's own stop, and the mean of them nothing after costs
    HIDDEN    the same, trading twice a year: under forty trades a line,       FAIL
              so that one line in fifty has not met its loss yet

Every history runs from 2010 to past the ladder's window, a bar each calendar day, so the
ladder's last five whole years are all in it.
"""

from __future__ import annotations

import json
import math
import random
from collections.abc import Iterator, Mapping, Sequence
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from desk.lines import LINES, Line
from desk.store import Bar
from lab import ladder
from lab.cell import Cell

FIRST, DAYS = date(2010, 1, 1), 6200
RULE = "breakout_20_10"
MARKETS = tuple(line for line in LINES if line.symbol in ladder.MARKETS.values())
LONDON = ("SMGB", "IITU", "VHYG", "VUSA", "SGLN", "VUAG", "EQQQ", "IB1T")
NEW_YORK = ("AAPL", "TSLA", "NVDA", "SPCX", "MSTR", "AMD", "MU", "QQQ")
EIGHT = tuple(line for line in LINES if line.symbol in LONDON and line.venue == "LSE")
SIXTEEN = EIGHT + tuple(line for line in LINES if line.symbol in NEW_YORK and line.venue == "US")
EDGE, BELL, DRIFT, LOPSIDED, HIDDEN = "edge", "bell", "drift", "lopsided", "hidden"
#: The planted edge: each day after a close over the twenty before it rises this much more.
PUSH = 0.012
#: The drifting line's rise a day, in and out of the rule's hands alike.
CLIMB = 0.0005
#: The lopsided rule's trades before costs: one in LOSSES falls through the desk's stop, and
#: the rest are small wins of WIN on average, as parts of the price paid, which with the costs
#: come to nothing a trade; the spec's tests hold that true of what the first rung prices.
WIN, LOSSES = 0.0170, 0.1
#: Days of rest between the lopsided rule's trades: DENSE trades nine times a year, SPARSE
#: twice, so a line's whole history is under forty trades and can hide its losses.
DENSE, SPARSE = 24, 150
#: Pounds to the dollar, the same every day: the rate a step of units is told by.
RATE = Decimal("0.8")
POUNDS = {FIRST + timedelta(n): RATE for n in range(DAYS)}

Row = tuple[float, float, float, float]  #: a day's open, high, low and close


def _bars(rows: Sequence[Row]) -> tuple[Bar, ...]:
    made = []
    for n, row in enumerate(rows):
        opened, high, low, close = (Decimal(f"{price:.4f}") for price in row)
        made.append(Bar(FIRST + timedelta(n), opened, high, low, close, 1))
    return tuple(made)


def walk(
    seed: int,
    push: float = 0.0,
    climb: float = 0.0,
    sour: tuple[date, date] | None = None,
    days: int = DAYS,
) -> tuple[Bar, ...]:
    """A random walk of one percent a day. With a push, each day after a close over the 20
    before it rises that much more, and the walk is pulled gently back towards 10; with a
    climb, every day rises that much and nothing pulls it back. Between the two sour days
    the push is turned about, twice over: there a breakout is followed by a fall."""
    turned = range(0) if sour is None else range(*((day - FIRST).days for day in sour))
    rng, closes = random.Random(seed), [10.0]  # noqa: S311 - a repeatable test walk, not a secret
    while len(closes) < days:
        up = len(closes) > 20 and closes[-1] > max(closes[-21:-1])
        pull = 0.0 if climb else 0.005 * math.log(closes[-1] / 10)
        pushed = (-2 * push if len(closes) in turned else push) if up else 0
        closes.append(closes[-1] * (1 + rng.gauss(0, 0.01) + pushed + climb - pull))
    befores = [closes[0], *closes[:-1]]
    return _bars(
        [
            ((b + c) / 2, max(b, c) * 1.005, min(b, c) * 0.995, c)
            for b, c in zip(befores, closes, strict=True)
        ]
    )


def _episode(rng: random.Random, base: float, rest: int) -> Iterator[Row]:
    """Flat days, a breakout the rule buys, and its trade: a small win held twelve days and
    sold on a ten-day low, or a fall through the stop the morning after it is bought. The
    wins are of every size from nothing to four times their mean, most of them small."""
    for _ in range(rest + rng.randrange(7)):
        yield (base, base * 1.002, base * 0.998, base)
    paid = base * 1.01
    yield (base, paid * 1.002, base * 0.998, paid)
    if rng.random() < LOSSES:
        yield (paid, paid * 1.002, base * 0.89, base * 0.895)
        return
    out = paid * (1 + WIN * min(rng.expovariate(1), 4) / (1 - math.exp(-4)))
    held = out / 0.99
    yield (paid, max(paid, held) * 1.002, paid * 0.998, held)
    for _ in range(11):
        yield (held, held * 1.002, held * 0.998, held)
    yield (held, held * 1.002, out * 0.998, out)


def lopsided(seed: int, rest: int = DENSE, days: int = DAYS) -> tuple[Bar, ...]:
    """Trade after trade of small wins and a rare loss at the stop, no edge in them."""
    rng, rows = random.Random(seed), [(10.0, 10.02, 9.98, 10.0)]  # noqa: S311 - a test draw
    while len(rows) < days:
        rows.extend(_episode(rng, rows[-1][3], rest))
    return _bars(rows[:days])


def world(
    kind: str, seed: int, sour: tuple[date, date] | None = None
) -> dict[Line, tuple[Bar, ...]]:
    """The seed's world of the kind: its sixteen lines' bars, and the two markets'. A market
    has no memory; it climbs where the lines do. An edge may be soured between two days."""
    if kind not in (EDGE, BELL, DRIFT, LOPSIDED, HIDDEN):
        raise ValueError(f"{kind}: no such world")
    climb = CLIMB if kind == DRIFT else 0.0

    def make(own: int) -> tuple[Bar, ...]:
        if kind in (LOPSIDED, HIDDEN):
            return lopsided(own, SPARSE if kind == HIDDEN else DENSE)
        return walk(own, PUSH if kind == EDGE else 0.0, climb, sour)

    markets = {line: walk(1000 * seed + 100 + n, climb=climb) for n, line in enumerate(MARKETS)}
    return markets | {line: make(1000 * seed + n) for n, line in enumerate(SIXTEEN, 1)}


def judged(
    home: Path, book: Mapping[Line, Sequence[Bar]], lines: Sequence[Line] = SIXTEEN
) -> list[dict[str, Any]]:
    """The ladder's own answers on the book, by its own command's door: the last line it
    kept under the home for each of the rule's cells, in the lines' order."""
    todo = [Cell(RULE, line, ladder.START, ladder.END) for line in lines]
    ladder.run(home, book.__getitem__, POUNDS, todo)
    (kept,) = (f for f in (home / "ladder").glob("set*.jsonl") if ".trials" not in f.name)
    rows = map(json.loads, kept.read_text(encoding="utf-8").splitlines())
    return list({tuple(row["cell"]): row for row in rows}.values())
