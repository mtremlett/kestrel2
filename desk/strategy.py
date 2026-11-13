"""strategy - THE FIVE FROZEN DAILY STRATEGIES. Each computes a decision for every line and
every day in one pass, seeing only bars: never the clock, a vendor or the broker."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from enum import Enum

from desk.store import Bar


class Action(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass(frozen=True)
class Decision:
    strategy: str
    symbol: str
    day: date
    action: Action


def decide(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """A decision from every strategy for every line and every day the bars cover."""
    raise NotImplementedError("strategy.decide: the five frozen strategies are phase 2")
