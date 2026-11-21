"""fast_sequential - the fast engine's firing of the TD Sequential blocks
(`lab.block_sequential`), bar by bar over the line's whole prices: those compare exactly, so
nothing here can be close."""

from __future__ import annotations

import numpy as np

from lab.block_sequential import BACK, COUNTDOWN, LAG, SETUP
from lab.fast_bands import Params
from lab.grid import Bools, Prices


def _runs(close: list[float], over: bool) -> list[int]:
    """After each bar, the closes in a row over (or under) the close `BACK` bars before."""
    out, run = [], 0
    for n, price in enumerate(close):
        before = close[n - BACK]
        run = run + 1 if n >= BACK and (price > before if over else price < before) else 0
        out.append(run)
    return out


def sell_setup(p: Prices, params: Params) -> Bools:  # noqa: ARG001 - no settings
    """Whether the close is the ninth in a row over the close four bars back."""
    return np.array([run == SETUP for run in _runs(p.close.tolist(), True)], dtype=np.bool_)


def buy_countdown(p: Prices, params: Params) -> Bools:  # noqa: ARG001 - no settings
    """Whether the bar is the thirteenth of a buy countdown."""
    close, low = p.close.tolist(), p.low.tolist()
    up, down = _runs(close, True), _runs(close, False)
    out, count = [], None
    for n, (rise, fall) in enumerate(zip(up, down, strict=True)):
        if rise == SETUP:
            count = None
        elif fall == SETUP:
            count = 0
        elif count is not None and n >= LAG and close[n] <= low[n - LAG]:
            count += 1
        out.append(count == COUNTDOWN)
        count = None if count == COUNTDOWN else count
    return np.array(out, dtype=np.bool_)
