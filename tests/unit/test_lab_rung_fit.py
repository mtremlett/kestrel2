"""The fit rung: a rule cloned from one already running on paper FAILS, one that shares part of
its days is WEAK, an unrelated one passes; and the running rules are the desk's and the zoo's."""

from __future__ import annotations

import random
from collections.abc import Sequence
from decimal import Decimal

import pytest
from test_lab_rung import VUSA, _walk

from desk import intraday
from desk.orders import Charges
from desk.strategy import STRATEGIES
from lab import cell, rung, rung_fit
from lab.cell import Cell, Record, Trade
from lab.rung import Answer, Priced

BARS = _walk(3, 0.0, days=8000)
RECORD = cell.run(Cell("breakout_20_10", VUSA, BARS[0].day, BARS[-1].day), BARS)
SOLD = [t for t in RECORD.trades if t.sold is not None]
Copy = type("Copy", (STRATEGIES["breakout_20_10"],), {})  #: a clone, under another name


def _first(record: Record, trades: Sequence[Trade], mean: float = 0.02) -> rung.Verdict:
    """The first rung's verdict on these of the record's trades, each planted a gain about mean."""
    rng, paid = random.Random(1), Decimal(1000)  # noqa: S311 - a repeatable test sample
    costs = Charges(Decimal(1), *[Decimal(0)] * 4)
    return rung.verdict(
        record.key,
        tuple(
            Priced(
                t,
                1,
                paid,
                paid * (1 + Decimal(f"{rng.gauss(mean, 0.01):.6f}")),
                costs,
                (t.bought, t.sold or t.bought),
                None,
            )
            for t in trades
        ),
    )


def _thirds(kept: int) -> list[Trade]:
    """Of every three of the rule's trades, the first `kept`: its days a part of the clone's."""
    return [t for n, t in enumerate(SOLD) if n % 3 < kept]


@pytest.mark.parametrize(
    ("kept", "answer", "says"),
    [
        (3, Answer.FAIL, "FAIL: moves 1.00 with copy"),
        (2, Answer.DOUBT, "WEAK: moves 0.80"),
        (1, Answer.PASS, "new: moves 0.56"),
    ],
)
def test_a_clone_fails_a_part_of_one_is_weak_and_a_small_part_passes(
    monkeypatch: pytest.MonkeyPatch, kept: int, answer: Answer, says: str
) -> None:
    """Its days a subset of the clone's, the correlation is about the root of the share kept."""
    monkeypatch.setattr(rung_fit, "RUNNING", {"copy": Copy})
    first = _first(RECORD, _thirds(kept))
    assert first.answer is Answer.PASS
    got, why = rung_fit.RUNG.judge(first, BARS, {})
    assert got is answer and why.startswith(says), why


def test_the_rule_itself_running_on_paper_is_passed_over(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rung_fit, "RUNNING", {"same": STRATEGIES["breakout_20_10"]})
    got, why = rung_fit.RUNG.judge(_first(RECORD, SOLD), BARS, {})
    assert got is Answer.PASS and "no rule running on paper" in why, why


def test_a_rule_the_first_rung_did_not_pass_keeps_its_answer() -> None:
    assert rung_fit.RUNG.judge(_first(RECORD, SOLD, -0.02), BARS, {})[0] is Answer.FAIL
    assert rung_fit.RUNG.judge(_first(RECORD, SOLD[:5]), BARS, {})[0] is Answer.THIN
    assert rung_fit.RUNG.judge(rung.verdict(RECORD.key, ()), BARS, {})[0] is Answer.FAULT


def test_the_running_rules_are_the_desks_five_and_the_zoos_daily_rules() -> None:
    assert dict(rung_fit.RUNNING) == {**STRATEGIES, **intraday.ZOO_DAILY}
    assert rung_fit.RUNG in rung.found()[0] and rung_fit.RUNG.name == "fit"
