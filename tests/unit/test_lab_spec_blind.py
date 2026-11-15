"""Future-blind, for every rule (canon B3): the decisions up to day T are the same with and
without the bars after T, for every rule of the book and every building block, over random T
on a seeded fixture - and the same test catches a planted rule that peeks one bar ahead."""

from __future__ import annotations

import inspect
import random
from collections.abc import Callable, Sequence
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import pytest

from desk.eponymous_zweig_breadth_thrust import Breadth
from desk.store import Bar
from desk.strategy import Decision, Rule, _run
from lab import rulebook
from lab.blocks import BLOCKS
from lab.spec import Spec, SpecRule

DAYS = 330  #: long enough for the year-long rules (Minervini, Weinstein)
CUTS = 6  #: random T per rule


def _bars() -> tuple[Bar, ...]:
    rng, close, out = random.Random(20201115), Decimal(100), []  # noqa: S311 - seeded, a fixture
    for n in range(DAYS):
        close = max(Decimal(5), close * (1 + Decimal(rng.randint(-300, 320)) / 10000))
        high, low = close * Decimal("1.01"), close * Decimal("0.99")
        out.append(
            Bar(date(2020, 1, 1) + timedelta(n), close, high, low, close, rng.randint(1, 9) * 1000)
        )
    return tuple(out)


Make = Callable[[Sequence[Bar]], Any]  #: a fresh rule, made over the series it will be shown


def _decisions(make: Make, bars: Sequence[Bar]) -> tuple[Decision, ...]:
    return tuple(_run("r", make(bars), "L01", bars))


def _blind(make: Make, bars: Sequence[Bar], seed: int) -> list[date]:
    """The cut days on which the decisions up to the cut changed when later bars went."""
    every, rng, bad = _decisions(make, bars), random.Random(seed), []  # noqa: S311 - seeded, a fixture
    for cut in sorted(rng.sample([b.day for b in bars], CUTS)):
        blind = _decisions(make, [b for b in bars if b.day <= cut])
        if blind != tuple(d for d in every if d.day <= cut):
            bad.append(cut)
    return bad


def _block_rule(name: str) -> Make:
    """A block alone as a rule: in the market on the bars it fires."""
    params = {k: p.low for k, p in BLOCKS[name].params.items()}
    return lambda _: _OneBlock(BLOCKS[name].make(**params))


def _spec_rule(spec: Spec) -> Make:
    """A catalogue spec as a rule."""
    return lambda _: SpecRule(spec)


def _rule(make: type[Rule]) -> Make:
    """A rule of the book; one that takes the market's breadth is given a day-by-day series."""
    if "breadth" not in inspect.signature(make).parameters:
        return lambda _: make()
    rng = random.Random(7)  # noqa: S311 - seeded, a fixture
    breadth = {b.day: Breadth(rng.randint(1, 99), rng.randint(1, 99)) for b in _bars()}
    return lambda _: make(breadth)  # type: ignore[call-arg]


class _OneBlock:
    def __init__(self, block: object) -> None:
        self._block = block

    def step(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the Rule interface
        return bool(self._block.see(bar, holding))  # type: ignore[attr-defined]


class _Peeker:
    """The planted fault: wants to be in the market when TOMORROW's close is higher."""

    def __init__(self, series: Sequence[Bar]) -> None:
        self._next = {a.day: b for a, b in zip(series, series[1:], strict=False)}

    def step(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the Rule interface
        ahead = self._next.get(bar.day)
        return ahead is not None and ahead.close > bar.close


RULES: dict[str, Make] = {
    **{n: _rule(m) for n, m in rulebook.rules().items()},
    **{f"block:{n}": _block_rule(n) for n in BLOCKS},
    **{f"spec:{n}": _spec_rule(s) for n, s in rulebook.specs().items()},
}


@pytest.mark.parametrize("name", sorted(RULES))
def test_every_rule_and_block_decides_the_same_without_the_later_bars(name: str) -> None:
    assert _blind(RULES[name], _bars(), seed=len(name)) == [], f"{name} saw bars after the cut"


def test_a_rule_that_peeks_one_bar_ahead_is_caught() -> None:
    bars = _bars()
    assert _blind(_Peeker, bars, seed=1), "the planted peeker went unseen"
