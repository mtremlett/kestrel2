"""orders_parts2 - the order's types: the settings, the order and the sale, the refusal, the legs
of a trade, the charges of a leg, and the one rounding policy. desk.orders gives them to its
callers."""

from __future__ import annotations

from dataclasses import astuple, dataclass, field
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal
from enum import Enum

from desk.lines import Line


@dataclass(frozen=True)
class Settings:
    capital: Decimal  #: pounds the desk may use; nothing else holds this number
    #: The loss and order-rate limits (R-RUNNER-156, docs/DECISIONS.md): a share of the capital
    #: lost in a day or in a week, and the new lines entered in a day, each past which the gate
    #: refuses a new entry.
    day_loss: Decimal = Decimal("0.02")
    week_loss: Decimal = Decimal("0.05")
    new_lines: int = 4
    #: R-RUNNER-158 (docs/DECISIONS.md): the most of the capital one underlying market may
    #: control, a leveraged line counted at its exposure; past it the gate refuses a buy.
    underlying: Decimal = Decimal("0.40")
    #: The most two held lines' daily returns may move together (Pearson, -1 to 1): a buy
    #: correlated past it with a line held is refused (canon B1, docs/DECISIONS.md); above 1 it
    #: never refuses.
    correlation: Decimal = Decimal("0.90")

    def __post_init__(self) -> None:
        if not self.capital.is_finite() or self.capital <= 0:
            raise ValueError(f"a capital of {self.capital} pounds")
        if self.correlation <= 0:
            raise ValueError(f"a correlation cap of {self.correlation}")
        if not (0 < self.day_loss <= self.week_loss <= 1) or self.new_lines < 1:
            raise ValueError(f"limits of {self.day_loss}, {self.week_loss} and {self.new_lines}")


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
    #: The session the order is dated (R-PAPER-35); None until every constructor sets it.
    session: date | None = field(default=None, kw_only=True, compare=False)
    #: The live price when the order is sent (R-RUNNER-407); None where none was read.
    market: Decimal | None = field(default=None, kw_only=True, compare=False)

    def __post_init__(self) -> None:
        if self.quantity <= 0 or not 0 < self.stop < self.price:
            raise ValueError(f"order {self.order_id}: needs shares, and a stop below its price")
        if self.fx <= 0 or (self.line.currency == "GBP" and self.fx != 1):
            raise ValueError(
                f"order {self.order_id}: {self.line.currency} at an exchange rate of {self.fx}"
            )


@dataclass(frozen=True)
class Sale:
    """An order to sell shares of a line the book holds, at the market."""

    order_id: str
    line: Line
    quantity: int
    session: date | None = field(default=None, compare=False)  #: as Order.session

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError(f"sale {self.order_id}: needs shares to sell")


class Refused(Exception):
    """The desk refused an order before sending it, saying why: the pre-trade gate, or the
    send path while the book is not the broker's."""


class Leg(Enum):
    """One side of a trade, as the cost model prices it."""

    BUY = "bought"
    SALE = "sold at the market"
    STOP = "sold by the stop resting at the broker"


@dataclass(frozen=True)
class Charges:
    """Every cost of a leg, or of legs added together, in pounds: none can be left out."""

    commission: Decimal  #: the broker's, and the regulators' fees it passes on with a US sale
    spread: Decimal  #: half of it, lost at each leg against the price the market showed
    slippage: Decimal  #: what the fill loses beyond the spread; more when a stop sells
    currency: Decimal  #: the conversion of the money moved, on a line not in pounds
    uk_taxes: Decimal  #: on a purchase, the part of its value the line states (Line.uk_tax)

    @property
    def total(self) -> Decimal:
        return sum(astuple(self), Decimal(0))

    def __add__(self, other: Charges) -> Charges:
        return Charges(*(a + b for a, b in zip(astuple(self), astuple(other), strict=True)))

    def part(self, shares: int, of: int) -> Charges:
        """The share of a fill's costs that some of its shares carry."""
        return Charges(*(a * shares / of for a in astuple(self)))

    def published(self) -> Charges:
        """Each line as it is published: rounded once, by the one policy (pennies)."""
        return Charges(*map(pennies, astuple(self)))


def pennies(amount: Decimal) -> Decimal:
    """THE ONE ROUNDING POLICY. Money is carried exact and rounded once, where it is
    published: to the penny, a half going to the even penny so that many days lean no way."""
    return amount.quantize(Decimal("0.01"), ROUND_HALF_EVEN)
