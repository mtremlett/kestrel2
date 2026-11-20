"""The stop-rule rung's contract: the ATR, each rival's first stop, a stop hit and gapped
through, the chandelier's raise, and a winner only when its worst fold passes."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from desk.store import Bar
from lab.rung_stops import ATR_BARS, TRIALS, Stop, atr, gain, walk, winner

D = Decimal


def _bar(i: int, o: int, h: int, low: int, c: int) -> Bar:
    return Bar(date(2026, 1, 1) + timedelta(days=i), D(o), D(h), D(low), D(c), 1000)


FLAT = [_bar(i, 100, 101, 99, 100) for i in range(ATR_BARS + 1)]  # true range 2 every day


def test_atr_and_first_stops() -> None:
    assert atr(FLAT) == 2
    with pytest.raises(ValueError, match="needs 21"):
        atr(FLAT[:5])
    held = [_bar(0, 100, 100, 100, 100), _bar(1, 100, 120, 100, 110)]
    # up 10 at exit, stop widths 10 (fixed), 4 (ATR2), 6 (ATR3 and chandelier): R = 10 / width
    assert [gain(s, FLAT, held, D(0)) for s in Stop] == [1, D("2.5"), D(10) / 6, D(10) / 6]


def test_stop_hit_gap_and_chandelier() -> None:
    gap = [_bar(0, 100, 100, 100, 100), _bar(1, 80, 90, 78, 85)]
    assert gain(Stop.FIXED, FLAT, gap, D(0)) == -2  # gapped to 80, stop at 90: sold at the open
    run = [_bar(0, 100, 100, 100, 100), _bar(1, 100, 130, 100, 130), _bar(2, 125, 126, 120, 121)]
    assert gain(Stop.ATR3, FLAT, run, D(0)) == D(21) / 6  # no raise: held to the close
    assert gain(Stop.CHANDELIER, FLAT, run, D(0)) == D(24) / 6  # raised to 124: sold at the open


def test_worst_fold_judges_and_no_winner_stays_with_today() -> None:
    good = [D(1) + D(i % 5) / 10 for i in range(30)]
    bad = [D(-1) - D(i % 5) / 10 for i in range(30)]
    assert walk([good, good]).passed and not walk([good, bad]).passed
    assert TRIALS == 4
    assert winner({Stop.FIXED: [good, bad], Stop.ATR2: [bad, bad]}, 0.1) is None
