"""rung_beta - THE LADDER'S BETA RUNG: is the strategy's excess over the market risk it took
clear of nothing by its whole interval?

Each day is a pair: what the strategy made, and what its benchmark did (`lab/market.py` builds the
pairs). The least-squares line of the first on the second (Wasserman, All of Statistics, 13.3;
Weisberg, Applied Linear Regression, 2.3) gives the beta the strategy carried and, as its height,
the EXCESS. The rung answers on the excess in its standard errors, never on its sign: at least
T_PASS above nothing PASS, at least that below FAIL, between DOUBT (LAD-08). Under MIN_TRADES days
it is THIN, never a fail; no day at all is a FAULT in the test (LAD-06, LAD-09); days with no
spread, or a benchmark that never moved, are refused loudly. The fit and the bar are the first
rung's own (`lab/market.fit`, `lab/rung`), read from there and not copied.
"""

from __future__ import annotations

from collections.abc import Sequence

from lab.market import fit
from lab.rung import MIN_TRADES, Answer, band


def judge(own: Sequence[float], market: Sequence[float]) -> Answer:
    """The rung's answer on the strategy's days and the benchmark's, paired and oldest first."""
    if not own:
        return Answer.FAULT
    if len(own) < MIN_TRADES:
        return Answer.THIN
    return band(fit(own, market).t)
