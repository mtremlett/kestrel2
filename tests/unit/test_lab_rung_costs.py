"""The costs rung (rung 2): an edge must live through its costs and through the costs doubled."""

from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from datetime import date
from decimal import Decimal
from math import comb

import pytest

from desk.lines import LINES
from desk.orders import Charges
from desk.store import Bar
from lab import cell, rung, rung_costs
from lab.cell import Cell, Trade
from lab.rung import Answer, Priced

ZERO, PAID = Decimal(0), Decimal(1000)
DAY = date(2010, 1, 4)
BAR = Bar(DAY, PAID, PAID, PAID, PAID, 1)
KEY = cell.key(
    Cell("breakout_20_10", next(x for x in LINES if x.symbol == "VUSA"), DAY, DAY), [BAR]
)


def priced(gross: float, cost: float) -> Priced:
    """A trade that made `gross` and was charged `cost`, each a fraction of the £1,000 it took."""
    one, spent = Trade(DAY, DAY), Decimal(str(cost)) * PAID
    return Priced(
        one,
        1,
        PAID,
        PAID * (1 + Decimal(str(gross))),
        Charges(spent, *[ZERO] * 4),
        (DAY, DAY),
        None,
    )


def cells(mean: float, spread: float, cost: float, n: int, seed: int) -> list[Priced]:
    """n trades whose gross returns are normal about `mean`, each charged `cost`."""
    rng = random.Random(seed)  # noqa: S311 - a repeatable test sample, not a secret
    return [priced(round(rng.gauss(mean, spread), 6), cost) for _ in range(n)]


def judged(trades: Sequence[Priced]) -> rung_costs.Costed:
    return rung_costs.judge(rung.verdict(KEY, tuple(trades)))


def test_the_break_even_is_the_gross_edge_over_the_costs_that_take_it_to_nothing() -> None:
    #: Novy-Marx & Velikov (2016), "A Taxonomy of Anomalies and Their Trading Costs", Review of
    #: Financial Studies 29(1): the break-even cost is the cost at which the net mean is nil.
    #: Gross 1%, 2% and 3% (mean 2%) at 0.5% a trade: nil at four times the cost.
    trades = [priced(g, 0.005) for g in (0.01, 0.02, 0.03)]
    assert rung_costs.breakeven(trades) == Decimal(4)
    assert rung_costs.breakeven([priced(-0.01, 0.005)]) == Decimal(-2), "a gross loss is below nil"
    with pytest.raises(ValueError, match="costs not charged"):  #: LAD-09: no rung is skipped
        rung_costs.breakeven([priced(0.01, 0)])


def battery(judge: Callable[[Sequence[Priced]], rung_costs.Costed]) -> list[Answer]:
    """Three known edges: solid (4x the costs), fragile (1.7x, its t high) and eaten (0.75x)."""
    solid, fragile, eaten = (
        cells(0.016, 0.02, 0.004, 60, 1),
        cells(0.010, 0.005, 0.006, 60, 2),
        cells(0.003, 0.02, 0.004, 60, 3),
    )
    return [judge(t).answer for t in (solid, fragile, eaten)]


def test_a_planted_edge_passes_and_one_that_dies_when_costs_double_does_not() -> None:
    assert battery(judged) == [Answer.PASS, Answer.FAIL, Answer.FAIL]
    fragile = judged(cells(0.010, 0.005, 0.006, 60, 2))
    assert (
        fragile.t is not None
        and fragile.t > 2
        and fragile.breakeven is not None
        and fragile.breakeven < 2
    ), "t alone passes it"
    assert rung.verdict(KEY, tuple(cells(0.010, 0.005, 0.006, 60, 2))).passed


def test_too_few_trades_are_thin_and_none_a_fault_never_a_fail() -> None:
    assert judged(cells(0.003, 0.02, 0.004, 29, 3)).answer is Answer.THIN  #: LAD-03: luck on few
    assert judged([]).answer is Answer.FAULT and judged([]).breakeven is None


def stated_rate_of_noise(mean: float, n: int = 500) -> int:
    """How many of n cells of 60 trades, whose net mean is `mean` above nothing, pass."""
    return sum(
        judged(cells(mean + 0.004, 0.02, 0.004, 60, s)).answer is Answer.PASS for s in range(n)
    )


def test_five_hundred_cells_of_noise_pass_at_about_the_stated_rate_and_no_more() -> None:
    #: LAD-08: net mean nil, the bar 2 standard errors: 2.5% in the t table; a 99.9% binomial bound
    passes = stated_rate_of_noise(0.0)
    cdf = sum(comb(500, k) * 0.025**k * 0.975 ** (500 - k) for k in range(passes + 1))
    assert passes > 0 and cdf < 0.999, f"{passes} of 500 passed: more than luck gives"


def test_the_power_curve_at_three_effect_sizes_rises() -> None:
    small, middle, large = (stated_rate_of_noise(m, 200) for m in (0.0, 0.005, 0.012))
    assert small <= 12 and 40 <= middle <= 160 and large >= 190, (small, middle, large)


def test_a_broken_copy_of_the_rung_is_caught(monkeypatch: pytest.MonkeyPatch) -> None:
    good = battery(judged)
    monkeypatch.setattr(rung_costs, "DOUBLED", ZERO)  #: costs never doubled
    assert battery(judged) != good
    monkeypatch.undo()
    monkeypatch.setattr(rung_costs, "breakeven", lambda _: Decimal(99))  #: costs never counted
    assert battery(judged) != good
    assert good == [Answer.PASS, Answer.FAIL, Answer.FAIL]
