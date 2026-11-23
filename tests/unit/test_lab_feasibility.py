"""Contract of lab/feasibility.py: the count of passed rules and the pounds-a-day number."""

from decimal import Decimal

import pytest

from lab import feasibility
from lab.feasibility import Earned


def row(rule: str, line: str = "VUKE", passed: bool = True) -> dict[str, object]:
    return {
        "cell": [rule, line],
        "answer": "PASS" if passed else "FAIL",
        "every": passed,
        "unrun": {},
    }


def test_three_rules_at_the_target_are_feasible() -> None:
    rows = [row("a"), row("a", "SPY"), row("b"), row("c"), row("d", passed=False)]
    earned = [Earned(r, Decimal(3000), 30) for r in "abc"]
    result = feasibility.measure(rows, earned)
    assert result.passed == ("a", "b", "c")
    assert result.per_day == Decimal(300)
    assert result.feasible


def test_each_shortfall_is_named() -> None:
    result = feasibility.measure([row("a")], [Earned("a", Decimal(500), 10)])
    assert not result.feasible
    assert result.short == ("1 rules passed, 3 asked", "50.00 pounds a day, 100 asked")


def test_a_rule_with_a_rung_unrun_is_not_passed() -> None:
    open_rung = row("a") | {"unrun": {"regimes": "no weather"}}
    assert feasibility.passed_rules([open_rung]) == ()


def test_records_must_match_passed_rules_once_each() -> None:
    with pytest.raises(ValueError, match="not passed: z"):
        feasibility.measure([row("a")], [Earned("z", Decimal(1), 1)])
    with pytest.raises(ValueError, match="two records"):
        feasibility.measure([row("a")], [Earned("a", Decimal(1), 1)] * 2)
    with pytest.raises(ValueError, match="days"):
        Earned("a", Decimal(1), 0)
