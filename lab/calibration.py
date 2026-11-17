"""calibration - EACH RUNG'S PASS RATE ON NOISE, as the deep run's "Calibration:" line (R-MONEY-43).

    python -m lab.calibration [worlds]

A noise world is a rule with no edge: WORLD_TRADES trades whose gains after costs are normal
about nothing (the gross mean is the cost taken), seeded, so a night's line is repeatable.
The first rung and every rung the package declares (`rung.found`) judge each world, and the
line tells how many passed. A rung that passes noise far above its stated rate is broken;
the stated rates and the bands they must fall in are proven by each rung's own tests. The
line is the desk's `desk.simcity` deep run's Calibration, which the desk may not compute."""

from __future__ import annotations

import random
import sys
from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal

from desk.lines import LINES
from desk.orders import Charges
from desk.store import Bar
from lab import cell, rung
from lab.cell import Cell, Trade
from lab.rung import Priced, Verdict

WORLDS, WORLD_TRADES = 500, 120
SPREAD, COST = 0.02, Decimal("0.004")  #: a trade's gain deviation, and the cost each pays
PAID, ZERO, START = Decimal(1000), Decimal(0), date(2010, 1, 4)
BAR = Bar(START, PAID, PAID, PAID, PAID, 1)
VUSA = next(x for x in LINES if x.symbol == "VUSA")
KEY = cell.key(Cell("breakout_20_10", VUSA, START, START), [BAR])


def world(seed: int) -> Verdict:
    """The first rung's verdict on one seeded rule of noise: gains after costs about nothing."""
    rng = random.Random(seed)  # noqa: S311 - a repeatable draw, not a secret
    trades = []
    for n in range(WORLD_TRADES):
        bought = START + timedelta(days=5 * n)
        gross = PAID * (1 + COST + Decimal(str(round(rng.gauss(0, SPREAD), 6))))
        trades.append(
            Priced(
                Trade(bought, bought + timedelta(days=3)),
                1,
                PAID,
                gross,
                Charges(COST * PAID, ZERO, ZERO, ZERO, ZERO),
                (bought, bought + timedelta(days=3)),
            )
        )
    return rung.verdict(KEY, tuple(trades))


def passes(worlds: int) -> dict[str, int]:
    """How many of the worlds each rung passes, the first rung and the declared ones."""
    declared, _ = rung.found()
    count = {"first": 0, **{one.name: 0 for one in declared}}
    for seed in range(worlds):
        first = world(seed)
        count["first"] += first.passed
        for one in declared:
            count[one.name] += one.judge(first)[0] is rung.Answer.PASS
    return count


def words(worlds: int) -> str:
    """The deep run's line: each rung's passes among the worlds, as a share."""
    shares = ", ".join(f"{name} {n / worlds:.1%}" for name, n in passes(worlds).items())
    return f"Calibration: {shares} passed of {worlds} noise worlds of {WORLD_TRADES} trades"


def main(argv: Sequence[str]) -> int:
    """Print the line; the one optional argument is the number of worlds."""
    if len(argv) > 1 or (argv and not argv[0].isdigit()):
        sys.exit("usage: python -m lab.calibration [worlds]")
    sys.stdout.write(words(int(argv[0]) if argv else WORLDS) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
