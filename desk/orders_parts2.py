"""orders_parts2 - THE ONE COST MODEL AND THE ONE ROUNDING POLICY, the middle part of
desk.orders: the legs of a trade, every cost of a leg, and the penny. desk.orders gives them
to its callers."""

from __future__ import annotations

from dataclasses import astuple, dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from enum import Enum

from desk.lines import Line
from desk.orders_parts import CONVERSION, FEES, HALF_SPREAD, SLIPPAGE, STOP_SLIPS


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


def leg_of(order_id: str, shares: int) -> Leg:
    """The leg a fill is, from the shares it added to the book and the id it carries: a
    stop's sale carries the id of the order that left the stop, with "-stop"."""
    if shares > 0:
        return Leg.BUY
    return Leg.STOP if order_id.endswith("-stop") else Leg.SALE


def charges(line: Line, leg: Leg, shares: int, price: Decimal, fx: Decimal) -> Charges:
    """THE ONE COST MODEL: every cost of one leg of shares at a price, in pounds at fx. The
    broker's commission, with the regulators' fees on a sale; the spread and the slippage
    assumed; the conversion of the money moved, on a line not in pounds; and the UK tax the
    line states, on a purchase."""
    if shares <= 0:
        raise ValueError(f"{line.symbol}: {shares} shares {leg.value}; the leg says which side")
    value, fee = shares * price, FEES[line.venue]
    commission = max(fee.minimum, fee.per_share * shares + fee.of_value * value)
    if fee.cap is not None:
        commission = min(commission, fee.cap * value)
    if leg is not Leg.BUY:
        commission += fee.sold_value * value + min(fee.sold_share * shares, fee.sold_most)
    tax = line.uk_tax * value if leg is Leg.BUY else Decimal(0)
    moved = value + commission + tax if leg is Leg.BUY else value - commission
    slips = SLIPPAGE * (STOP_SLIPS if leg is Leg.STOP else 1)
    return Charges(
        commission * fx,
        HALF_SPREAD * line.leverage * value * fx,
        slips * line.leverage * value * fx,
        Decimal(0) if line.currency == "GBP" else moved * fx * CONVERSION,
        tax * fx,
    )
