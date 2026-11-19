"""orders_parts - THE ONE COST MODEL AND THE ONE ROUNDING POLICY, the lower part of desk.orders:
the legs of a trade, every cost of a leg and the broker's schedule that prices it. desk.orders
gives them to its callers."""

from __future__ import annotations

from dataclasses import astuple, dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from enum import Enum

from desk.lines import Line


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


@dataclass(frozen=True)
class _Fee:
    """A venue's commission, in the line's currency: per share plus a share of the value, no
    less than a minimum, and no more than a share of the value where there is a cap. And a
    sale's own cost, its regulators' fees: a share of the value, and an amount for each
    share sold up to the most one sale pays."""

    per_share: Decimal
    of_value: Decimal
    minimum: Decimal
    cap: Decimal | None
    sold_value: Decimal
    sold_share: Decimal
    sold_most: Decimal


#: Interactive Brokers UK, fixed pricing, read from its published schedule on 13 November
#: 2026. Dollars are bought by its automatic conversion: 0.03% on the rate, no commission.
#: With every US sale it passes on the regulators' two fees: the SEC's 20.60 dollars a
#: million sold (since 4 April 2026) and FINRA's 0.0195 cents a share, at most 9.79 dollars
#: (its 2026 rate), each read in the regulator's own notice. A London sale pays nothing more.
BROKER = "Interactive Brokers UK, fixed pricing (schedule read 13 November 2026)"
FEES = {
    "LSE": _Fee(Decimal(0), Decimal("0.0005"), Decimal(3), None, *(Decimal(0),) * 3),
    "US": _Fee(
        Decimal("0.005"),
        Decimal(0),
        Decimal(1),
        Decimal("0.01"),
        Decimal("0.0000206"),
        Decimal("0.000195"),
        Decimal("9.79"),
    ),
}
CONVERSION = Decimal("0.0003")
#: ASSUMED, not measured (docs/DECISIONS.md), until the paper account's own fills are set
#: beside them: each leg loses a twentieth of one per cent of its value to half the spread
#: and as much again to slippage, both times the line's leverage, since a line that moves
#: that many times its market is quoted that much wider. A stop sells into a falling
#: market, so its sale slips STOP_SLIPS times as far.
HALF_SPREAD = SLIPPAGE = Decimal("0.0005")
STOP_SLIPS = 3


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
