"""ladder_map - THE RUNG MAP (L2): the plan's eleven rungs, easing 4's twelfth, his 26 Nov
13th and 14th and E13's 15th, each `n name: module, test`, and the count of those the ladder
judges by. It is its own module (R-RUNNER-571) so a new rung adds its row here and never edits
`lab/ladder.py`; it is not named `rung_*`, which `rung.found` reads as a rung's own module.

A row's names differ: `first` holds 1-3, `market` 4 and 6. Each rung's proof is in its own test;
(unbuilt) marks a file not yet there; after the dash, what is owed. BUILT: its module declares a
RUNG, so the ladder judges by it; every other row owes `no RUNG` first (the test holds the two to
agree).
"""

from __future__ import annotations

import importlib

MAP = (
    " 1 sample size, effective trades: lab/rung.py, tests/unit/test_lab_calibration.py"
    " - no RUNG; merged",
    " 2 costs charged: lab/rung_costs.py, tests/unit/test_lab_rung_costs.py",
    " 3 a confidence interval: lab/rung_ci.py, tests/unit/test_lab_rung_ci.py",
    " 4 excess after market risk, by size: lab/market.py, tests/unit/test_lab_rung_beta.py"
    " - no RUNG",
    " 5 two regime windows: lab/rung_regimes.py, tests/unit/test_lab_rung_regimes.py",
    " 6 benchmark excess: lab/market.py, tests/unit/test_lab_market.py"
    " - no RUNG; rung_benchmark merged",
    " 7 deflated Sharpe: lab/deflated.py, tests/unit/test_lab_deflated.py"
    " - no RUNG; rung_dsr merged",
    " 8 purged cross-validation: lab/rung_cpcv.py, tests/unit/test_lab_rung_cpcv.py",
    " 9 placebo, days shuffled: lab/shuffle.py, tests/unit/test_lab_shuffle.py"
    " - no RUNG; blocks dropped",
    "10 walk-forward folds: lab/folds.py, tests/unit/test_lab_folds.py"
    " - no RUNG; the ladder runs `pool`",
    "11 block bootstrap: lab/rung_ci.py, tests/unit/test_lab_rung_bootstrap.py"
    " - wired: holds ci's PASS",
    "12 retail, basket beside market: lab/basket.py, tests/unit/test_lab_basket.py"
    " - no RUNG; merged",
    "13 liquidity and capacity: lab/rung_liquidity.py, tests/unit/test_lab_rung_liquidity.py",
    "14 fit with the book: lab/rung_fit.py, tests/unit/test_lab_rung_fit.py",
    "15 one bar late: lab/rung_late.py, tests/unit/test_lab_rung_late.py",
)


def rows() -> tuple[str, ...]:
    """The map's rows, one a rung, in its order."""
    return MAP


def rungs_built() -> tuple[int, int]:
    """The map's rungs the ladder judges by (their module declares a RUNG), and the map's rungs."""
    mods = {r.split("lab/")[1].split(".py")[0] for r in MAP if ".py (unbuilt)" not in r}
    return sum(hasattr(importlib.import_module(f"lab.{m}"), "RUNG") for m in mods), len(MAP)
