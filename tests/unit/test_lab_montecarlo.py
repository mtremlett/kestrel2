"""The ladder's Monte Carlo rung: synthetic trades with known answers."""

from __future__ import annotations

from decimal import Decimal

import pytest

from lab import montecarlo

D = Decimal


def test_a_lone_loss_has_its_own_drawdown_and_return_in_every_path() -> None:
    got = montecarlo.resample([D("-0.1")], seed=1, paths=20)
    assert got.paths == 20
    assert got.drawdown == montecarlo.Spread(D("0.1"), D("0.1"), D("0.1"))
    assert got.returns == montecarlo.Spread(D("-0.1"), D("-0.1"), D("-0.1"))


def test_wins_alone_never_draw_down_and_compound() -> None:
    got = montecarlo.resample([D("0.1")] * 3, seed=1, paths=5)
    assert got.drawdown.high == 0
    assert got.returns.median == D("1.1") ** 3 - 1


def test_a_seed_repeats_and_another_seed_differs() -> None:
    coin = [D("0.02"), D("-0.02")] * 15
    assert montecarlo.resample(coin, seed=7) == montecarlo.resample(coin, seed=7)
    assert montecarlo.resample(coin, seed=7) != montecarlo.resample(coin, seed=8)


def test_a_fair_coin_is_centred_on_nothing_with_a_spread_both_sides_and_ordered_cuts() -> None:
    got = montecarlo.resample([D("0.02"), D("-0.02")] * 15, seed=3)
    assert got.paths == montecarlo.PATHS
    assert got.returns.low < 0 < got.returns.high
    assert abs(got.returns.median) < D("0.05")
    assert 0 < got.drawdown.low <= got.drawdown.median <= got.drawdown.high


@pytest.mark.parametrize(("trades", "paths"), [([], 10), ([D("0.1")], 0), ([D("-1")], 10)])
def test_input_that_cannot_be_resampled_is_refused(trades: list[Decimal], paths: int) -> None:
    with pytest.raises(ValueError, match="montecarlo"):
        montecarlo.resample(trades, seed=1, paths=paths)
