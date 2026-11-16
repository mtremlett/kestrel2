"""feasibility - BEFORE A-GATE PAPER: how many rules the ladder has passed, and whether what
they made, after every cost, could reach the A-GATE's pounds a day (NS-04, AG-01).

THE COUNT. A rule is ladder-passed when any of its cells goes forward by the ladder's own
reading (`verdict.goes`): PASS, every rung run passed, none unrun. A rule is counted once,
however many lines it passed on. Three are asked before paper (`NEEDED`).

THE NUMBER. Each passed rule is given with the pounds it made after every cost over a number
of trading days (a measured fact of its tape, never a guess here). Its pounds a day is that
over those days; the number is their sum, each rule once. Rules that earn on the same days
are one bet, so the sum is the most the set can say, and the verdict is read on it: FEASIBLE
only with three passed rules and a sum at the A-GATE's £100 a day (`TARGET`); otherwise it
says which is short. It is a ceiling on what paper can show, never a promise of it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from lab import verdict

NEEDED = 3  #: ladder-passed rules asked before A-GATE paper
TARGET = Decimal(100)  #: the A-GATE's average net pounds a day (AG-01)


@dataclass(frozen=True)
class Earned:
    """One passed rule's record: net pounds after every cost over `days` trading days."""

    rule: str
    pounds: Decimal
    days: int

    def __post_init__(self) -> None:
        """Refuse a record over no days."""
        if self.days <= 0:
            raise ValueError(f"{self.rule}: days must be above nothing, got {self.days}")

    @property
    def per_day(self) -> Decimal:
        """Net pounds a day over its days."""
        return self.pounds / self.days


@dataclass(frozen=True)
class Feasibility:
    """The count of passed rules, the summed pounds a day, and what is short of the ask."""

    passed: tuple[str, ...]  #: the ladder-passed rules, each once, in the order met
    per_day: Decimal  #: the sum of their net pounds a day
    short: tuple[str, ...]  #: what is missing, in words; empty when feasible

    @property
    def feasible(self) -> bool:
        """Nothing is short: the count and the pounds a day both stand."""
        return not self.short


def passed_rules(rows: Sequence[verdict.Row]) -> tuple[str, ...]:
    """The rules with a cell that goes forward, each once, in the order first met."""
    return tuple(dict.fromkeys(row["cell"][0] for row in rows if verdict.goes(row)))


def measure(rows: Sequence[verdict.Row], earned: Sequence[Earned]) -> Feasibility:
    """The count from the ladder's rows and the number from the passed rules' records.

    A record for a rule the ladder has not passed, or two for one rule, is refused: the sum
    would count what the ladder never cleared, or count a rule twice."""
    passed = passed_rules(rows)
    names = [one.rule for one in earned]
    if stray := sorted(set(names) - set(passed)):
        raise ValueError(f"records for rules the ladder has not passed: {', '.join(stray)}")
    if len(set(names)) != len(names):
        raise ValueError(f"two records for one rule among: {', '.join(names)}")
    per_day = sum((one.per_day for one in earned), Decimal(0))
    short: list[str] = []
    if len(passed) < NEEDED:
        short.append(f"{len(passed)} rules passed, {NEEDED} asked")
    if per_day < TARGET:
        short.append(f"{per_day:.2f} pounds a day, {TARGET} asked")
    return Feasibility(passed, per_day, tuple(short))
