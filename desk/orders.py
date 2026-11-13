"""orders - AN ORDER, SIZED FROM THE ONE CAPITAL NUMBER. It cannot exist without its stop,
and the one pre-trade gate reads the same capital number as the sizer. THE ONE COST MODEL:
every cost of a leg, line by line, for the gate, the round trip and research alike."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import astuple, dataclass, replace
from decimal import Decimal
from enum import Enum

from desk.lines import Line
from desk.strategy import Action, Decision

#: His ruling of 13 November 2026 (docs/DECISIONS.md): at most five holdings, each a fifth of
#: the capital counted at what the line controls, and a stop where its market has fallen 10%.
HOLDINGS = 5
STOP_FALL = Decimal("0.10")


@dataclass(frozen=True)
class Settings:
    capital: Decimal  #: pounds the desk may use; nothing else holds this number

    def __post_init__(self) -> None:
        if not self.capital.is_finite() or self.capital <= 0:
            raise ValueError(f"a capital of {self.capital} pounds")


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


def size(
    decision: Decision,
    line: Line,
    price: Decimal,
    fx: Decimal,
    settings: Settings,
    held: Mapping[str, int],
) -> Order:
    """The most whole shares whose cost, with the shares of the line already held, fits the
    line's room, and the stop, for a buy; fx is pounds per unit of the line's currency, and
    held is the book (book.positions)."""
    if decision.action is not Action.BUY or decision.symbol != line.symbol:
        raise ValueError(f"{line.symbol}: only a buy for this line is sized, not {decision}")
    if STOP_FALL * line.leverage >= 1:
        raise ValueError(f"{line.symbol}: at {line.leverage} times, a 10% fall empties the line")
    order_id = order_id_of(decision)
    stop = price * (1 - STOP_FALL * line.leverage)

    def order(quantity: int) -> Order:
        return Order(order_id, line, quantity, price, fx, stop)

    room, one = _room(line, settings), order(1)  #: one share proves the price, rate and stop
    if cost(one) > room:
        raise Refused(f"{order_id}: one share costs more than the room of {room} pounds")
    fits, over = 1, int(room / (price * fx)) + 1
    while over - fits > 1:  #: cost grows with the shares, so halve the gap until it closes
        middle = (fits + over) // 2
        fits, over = (middle, over) if cost(order(middle)) <= room else (fits, middle)
    already = held.get(line.symbol, 0)
    if fits <= already:
        raise Refused(f"{order_id}: {already} shares held leave no room for more")
    bought = order(fits - already)
    gate(bought, settings, held)
    return bought


def order_id_of(decision: Decision) -> str:
    """The id of the order a decision makes: its day, its strategy and its line."""
    return f"{decision.day:%Y%m%d}-{decision.strategy}-{decision.symbol}"


def strategy_of(order_id: str) -> str:
    """The strategy whose decision made the order, or the stop it left."""
    return order_id.split("-")[1]


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


def cost(order: Order) -> Decimal:
    """The pounds the order takes at its price: its value, the broker's commission, the UK
    tax, and on a line not in pounds the conversion of them all. The spread and the slippage
    are what its fill loses against that price: they are counted in its profit, not here."""
    paid = charges(order.line, Leg.BUY, order.quantity, order.price, order.fx)
    value = order.quantity * order.price * order.fx
    return value + paid.commission + paid.currency + paid.uk_taxes


def gate(order: Order | Sale, settings: Settings, held: Mapping[str, int]) -> None:
    """The one pre-trade gate, on the send path: raises Refused, or lets the order through.
    held is the book (book.positions): a sale needs the shares in it, for the desk is long
    only; a new line needs one of the five holdings free, and a line's shares, held and
    ordered, are counted together at the order's price and rate."""
    symbol = order.line.symbol
    if isinstance(order, Sale):
        if order.quantity > held.get(symbol, 0):
            raise Refused(
                f"{order.order_id}: sells {order.quantity} of {symbol}, the book holds "
                f"{held.get(symbol, 0)}: the desk is long only"
            )
        return
    if symbol not in held and len(held) >= HOLDINGS:
        raise Refused(f"{order.order_id}: {len(held)} holdings already, at most {HOLDINGS}")
    whole = replace(order, quantity=order.quantity + held.get(symbol, 0))
    if cost(whole) > _room(order.line, settings):
        raise Refused(
            f"{order.order_id}: {cost(whole)} pounds for {whole.quantity} shares, counted "
            f"{order.line.leverage} times for what it controls, is over a fifth of the "
            f"capital of {settings.capital}"
        )


def _room(line: Line, settings: Settings) -> Decimal:
    """Pounds one holding in the line may cost: a fifth of the capital, counted at what the
    line controls."""
    return settings.capital / HOLDINGS / line.leverage
