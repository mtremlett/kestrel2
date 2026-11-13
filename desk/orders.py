"""orders - AN ORDER, SIZED FROM THE ONE CAPITAL NUMBER. It cannot exist without its stop,
and the one pre-trade gate reads the same capital number as the sizer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from desk.lines import Line
from desk.strategy import Decision


@dataclass(frozen=True)
class Settings:
    capital: Decimal  #: pounds the desk may use; nothing else holds this number


@dataclass(frozen=True)
class Order:
    """An order to buy, at the price and rate it was sized at. Its stop is set before it
    exists, below that price, or the order does not exist."""

    order_id: str
    line: Line
    quantity: int
    price: Decimal  #: in the line's currency
    fx: Decimal  #: pounds per unit of the line's currency
    stop: Decimal

    def __post_init__(self) -> None:
        if self.quantity <= 0 or not 0 < self.stop < self.price:
            raise ValueError(f"order {self.order_id}: needs shares, and a stop below its price")


class Refused(Exception):
    """The pre-trade gate refused an order, saying why."""


def size(decision: Decision, line: Line, price: Decimal, fx: Decimal, settings: Settings) -> Order:
    """Whole shares and a stop for a buy; fx is pounds per unit of the line's currency."""
    raise NotImplementedError("orders.size: sizing is phase 2")


def cost(order: Order) -> Decimal:
    """What the order costs in pounds, the currency conversion counted."""
    raise NotImplementedError("orders.cost: the cost model is phase 2")


def gate(order: Order, settings: Settings) -> None:
    """The one pre-trade gate, on the send path: raises Refused, or lets the order through."""
    raise NotImplementedError("orders.gate: the pre-trade gate is phase 2")
