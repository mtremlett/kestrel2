"""The ladder's known answer for rare large losses (G2, the spec in `lab/ladder.py`): small
wins and a rare loss at the stop, worth nothing together, never pass the first rung's four
rungs on few trades, because a loss at the rule's own stop is counted among them."""

from __future__ import annotations

import math
import random
from datetime import date, timedelta
from decimal import Decimal
from statistics import fmean

from desk.command import CAPITAL
from desk.lines import LINES
from desk.orders import Settings
from desk.store import Bar
from lab import cell, deflated, ladder, rung
from lab.cell import Cell
from lab.rung import Answer

FIRST, DAYS, REST = date(2010, 1, 1), 6200, 150
LOSSES, WIN, SET = 0.1, 0.0170, 110  #: one trade in ten falls through the stop; the first set
LONDON = ("SMGB", "IITU", "VHYG", "VUSA", "SGLN", "VUAG", "EQQQ", "IB1T")
EIGHT = [line for line in LINES if line.symbol in LONDON and line.venue == "LSE"]


def _episode(rng: random.Random, base: float) -> list[tuple[float, float, float, float]]:
    """Flat days, a breakout the rule buys, then a small win sold on a ten-day low, or a fall
    through the stop the morning after it is bought. Rows are open, high, low, close."""
    rows = [(base, base * 1.002, base * 0.998, base)] * (REST + rng.randrange(7))
    paid = base * 1.01
    rows.append((base, paid * 1.002, base * 0.998, paid))
    if rng.random() < LOSSES:
        return [*rows, (paid, paid * 1.002, base * 0.89, base * 0.895)]
    out = paid * (1 + WIN * min(rng.expovariate(1), 4) / (1 - math.exp(-4)))
    held = out / 0.99
    rows.append((paid, max(paid, held) * 1.002, paid * 0.998, held))
    rows += [(held, held * 1.002, held * 0.998, held)] * 11
    return [*rows, (held, held * 1.002, out * 0.998, out)]


def _bars(seed: int) -> tuple[Bar, ...]:
    rng, rows = random.Random(seed), [(10.0, 10.02, 9.98, 10.0)]  # noqa: S311 - a test draw
    while len(rows) < DAYS:
        rows += _episode(rng, rows[-1][3])
    made = []
    for n, (opened, high, low, close) in enumerate(rows[:DAYS]):
        o, h, lo, c = (Decimal(f"{p:.4f}") for p in (opened, high, low, close))
        made.append(Bar(FIRST + timedelta(n), o, h, lo, c, 1))
    return tuple(made)


def test_small_wins_and_a_rare_loss_at_the_stop_never_pass_on_few_trades() -> None:
    room, verdicts = Settings(CAPITAL), []
    for seed in range(400):
        bars = _bars(seed)
        window = Cell("breakout_20_10", EIGHT[seed % 8], bars[0].day, ladder.END)
        verdicts.append(rung.judge(cell.run(window, bars), bars, room, {}))
    #: the world is what it says: under forty trades a line, one in ten a loss at the stop,
    #: and nothing made of them all after the broker's costs
    gains = [float(priced.gain) for verdict in verdicts for priced in verdict.trades]
    assert all(rung.MIN_TRADES <= len(verdict.trades) < 40 for verdict in verdicts)
    assert abs(sum(gain < -0.05 for gain in gains) / len(gains) - LOSSES) < 0.01
    assert abs(fmean(gains)) < 0.001 < 0.1 < -min(gains) < 0.11
    #: a line in fifty hid every loss so far; with the rule's own stop planted none is believed
    own = [deflated.judge([verdict], SET - 1)[0].least for verdict in verdicts]
    assert own.count(Answer.PASS) == 0, "a loss not yet seen was taken for an edge"
