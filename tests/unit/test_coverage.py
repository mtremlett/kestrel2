"""The coverage contract: sessions against twice the longest lookback, parked lines score nothing,
the desk's score is the mean and the parked share is capped."""

from __future__ import annotations

from decimal import Decimal

from desk import coverage


def test_enough_history_is_twice_the_longest_lookback_and_parked_scores_nothing() -> None:
    held = {"AAA": coverage.NEED, "BBB": coverage.NEED - 1, "CCC": coverage.A_GATE * 2, "DDD": 900}
    got = {c.symbol: c for c in coverage.measure(held, {"DDD"})}
    assert [got[s].enough for s in held] == [True, False, True, False]
    assert got["CCC"].score == 1 and got["DDD"].score == 0
    assert got["AAA"].score == Decimal(coverage.NEED) / coverage.A_GATE


def test_desk_score_is_the_mean_and_the_parked_cap_binds() -> None:
    held = {f"L{n}": coverage.A_GATE for n in range(10)}
    lines = coverage.measure(held, {"L0"})
    assert coverage.desk_score(lines) == Decimal("0.9")
    assert coverage.desk_score(()) == 0
    assert coverage.parked_within_cap(held, {"L0"})
    assert not coverage.parked_within_cap(held, {"L0", "L1"})


def test_the_lookback_is_the_longest_setting_the_grid_may_try() -> None:
    assert coverage.LOOKBACK == 250 and coverage.NEED == 500
