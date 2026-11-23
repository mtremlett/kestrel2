"""block_base - what every building block shares: the kinds of place a block fits, the block's
one interface, and how the registry (`lab.blocks`) holds one with its parameters' ranges."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from desk.store import Bar


class Kind(Enum):
    """Where in a rule a block sits."""

    ENTRY = "entry"
    EXIT = "exit"
    STOP = "stop"
    FILTER = "filter"
    SIZE = "size"  #: how many shares a buy takes; a spec may name one, never must


class Block:
    """Shown each bar with whether the position is held; says whether it fires."""

    def see(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar: whether the block fires."""
        raise NotImplementedError

    def shares(self, risk: Decimal) -> int:
        """A SIZE block: shares to buy at the last close for this much risk."""
        raise NotImplementedError(f"{type(self).__name__} is no sizing block")


@dataclass(frozen=True)
class Param:
    """One parameter a block takes: its type and the closed range it must lie in."""

    kind: type[int] | type[Decimal]
    low: int
    high: int


@dataclass(frozen=True)
class Spot:
    """A block as the registry holds it: the kind of place it fits, its class, its parameters
    in the order its constructor takes them."""

    kind: Kind
    make: Callable[..., Block]
    params: Mapping[str, Param]
