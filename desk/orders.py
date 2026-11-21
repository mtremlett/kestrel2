"""orders - AN ORDER, SIZED FROM THE ONE CAPITAL NUMBER. It cannot exist without its stop,
and the one pre-trade gate reads the same capital number as the sizer. THE ONE COST MODEL:
every cost of a leg, line by line, for whoever prices a buy, a sale or a stop's sale. AND THE
ONE ROUNDING POLICY for what is published of it."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import astuple, dataclass, field, replace
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal
from enum import Enum

from desk.lines import Line
from desk.orders_parts import (
    BROKER as BROKER,
)
from desk.orders_parts import (
    CONVERSION as CONVERSION,
)
from desk.orders_parts import (
    FEES as FEES,
)
from desk.orders_parts import (
    HALF_SPREAD as HALF_SPREAD,
)
from desk.orders_parts import (
    SLIPPAGE as SLIPPAGE,
)
from desk.orders_parts import (
    STOP_SLIPS as STOP_SLIPS,
)
from desk.orders_parts2 import MOVES_DAYS as MOVES_DAYS
from desk.orders_parts2 import MOVES_FROM as MOVES_FROM
from desk.orders_parts2 import Refused as Refused
from desk.orders_parts2 import _apart, _within_limits, _within_underlying, daily_moves
from desk.risk import Standing
from desk.store import Bar
from desk.strategy import Action, Decision

moves = daily_moves  #: the daily returns the correlation gate reads (orders_parts2)

#: His ruling of 13 November 2026 (docs/DECISIONS.md): at most five holdings, each a fifth of
#: the capital counted at what the line controls, and a stop where its market has fallen 10%.
HOLDINGS = 5
STOP_FALL = Decimal("0.10")
#: STP-10, the one home (R-RUNGS-11, docs/DECISIONS.md): the most of the capital one holding may
#: lose when a gap jumps its stop; the stop alone risks STOP_FALL / HOLDINGS of it (2%).
GAP_LOSS = Decimal("0.05")
#: SIZ-10, the one home: no position above this share of its line's average daily traded value
#: over the last LIQUID_DAYS sessions.
LIQUID_SHARE, LIQUID_DAYS = Decimal("0.01"), 20


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


def stop_under(line: Line, price: Decimal) -> Decimal:
    """THE STOP FOR A PRICE: where the line's market has fallen 10% from it. Sizing asks it at
    the signal close; the stop a fill is to rest at is asked at the fill's price, so a gap
    down puts it under the fill, never above it, and a gap up keeps it 10% under its own."""
    if STOP_FALL * line.leverage >= 1:
        raise ValueError(f"{line.symbol}: at {line.leverage} times, a 10% fall empties the line")
    return price * (1 - STOP_FALL * line.leverage)


def size(
    decision: Decision,
    line: Line,
    price: Decimal,
    fx: Decimal,
    settings: Settings,
    held: Mapping[str, int],
    market: Decimal | None = None,
    traded: Decimal | None = None,
) -> Order:
    """The most whole shares whose cost, with the shares of the line already held, fits the
    line's room, and the stop, for a buy; fx is pounds per unit of the line's currency, and
    held is the book (book.positions). Given the live price (market), the stop rests 10% under
    it, never above the signal's, and a buy is refused that the signal's stop would sell at once.
    Given the line's daily pounds (traded_value), the position is
    kept to LIQUID_SHARE of them too."""
    if decision.action is not Action.BUY or decision.symbol != line.symbol:
        raise ValueError(f"{line.symbol}: only a buy for this line is sized, not {decision}")
    order_id = order_id_of(decision)
    stop = stop_under(line, price if market is None else min(price, market))

    def order(quantity: int) -> Order:
        return Order(order_id, line, quantity, price, fx, stop, session=decision.day, market=market)

    if market is not None:
        _above_stop(replace(order(1), stop=stop_under(line, price)))

    room, one = _room(line, settings), order(1)  #: one share proves the price, rate and stop
    if cost(one) > room:
        raise Refused(f"{order_id}: one share costs more than the room of {room} pounds")
    fits, over = 1, int(room / (price * fx)) + 1
    while over - fits > 1:  #: cost grows with the shares, so halve the gap until it closes
        middle = (fits + over) // 2
        fits, over = (middle, over) if cost(order(middle)) <= room else (fits, middle)
    fits = fits if traded is None else min(fits, int(traded * LIQUID_SHARE / (price * fx)))
    already = held.get(line.symbol, 0)
    if fits <= already:
        raise Refused(f"{order_id}: {already} shares held leave no room for more")
    bought = order(fits - already)
    gate(bought, settings, held)
    return bought


def traded_value(line: Line, bars: Sequence[Bar], fx: Decimal) -> Decimal:
    """THE POUNDS A LINE TRADES IN A DAY (SIZ-10): close times volume over its last 20 bars."""
    if len(bars) < LIQUID_DAYS:
        raise Refused(f"{line.symbol}: {len(bars)} bars, under {LIQUID_DAYS} to judge its volume")
    return sum((b.close * b.volume for b in bars[-LIQUID_DAYS:]), Decimal(0)) * fx / LIQUID_DAYS


def gap_loss(order: Order, fill: Decimal) -> Decimal:
    """STP-10: the pounds a stop's sale at `fill` loses against the order's price, charges
    apart. A gap that jumps the stop sells below it, so this is more than the stop's own."""
    return max(Decimal(0), (order.price - fill) * order.quantity * order.fx)


def gapped(order: Order, fill: Decimal, settings: Settings) -> bool:
    """Whether a stop's sale at `fill` lost more than GAP_LOSS of the capital: such a gap is
    held against the limit, and the desk is to stand down (STP-10, SIZ-09: sizing at a fifth
    of the capital over the leverage keeps a market gap of up to 25% inside it)."""
    return gap_loss(order, fill) > GAP_LOSS * settings.capital


def order_id_of(decision: Decision) -> str:
    """The id of the order a decision makes: its day, its strategy and its line."""
    return f"{decision.day:%Y%m%d}-{decision.strategy}-{decision.symbol}"


def strategy_of(order_id: str) -> str:
    """The strategy whose decision made the order, or the stop it left."""
    parts = order_id.split("-")
    if len(parts) < 3 or not all(parts[:3]):
        raise ValueError(f"order id {order_id!r} is not day-strategy-line; no strategy can be read")
    return parts[1]


def cost(order: Order) -> Decimal:
    """The pounds the order takes at its price: its value, the broker's commission, the UK
    tax, and on a line not in pounds the conversion of them all. The spread and the slippage
    are what its fill loses against that price: they are counted in its profit, not here."""
    paid = charges(order.line, Leg.BUY, order.quantity, order.price, order.fx)
    value = order.quantity * order.price * order.fx
    return value + paid.commission + paid.currency + paid.uk_taxes


def gate(
    order: Order | Sale,
    settings: Settings,
    held: Mapping[str, int],
    standing: Standing | None = None,
    exposure: Mapping[str, Decimal] | None = None,
    moves: Mapping[str, tuple[float, ...]] | None = None,
) -> None:
    """The one pre-trade gate, on the send path: raises Refused, or lets the order through.
    held is the book (book.positions): a sale needs the shares in it, for the desk is long
    only; a new line needs one of the five holdings free, and a line's shares, held and
    ordered, are counted together at the order's price and rate. Given the book's standing
    (risk.Standing), a buy is refused once a loss limit is reached, and a new line once the
    day's new lines are used up; None checks neither (the send path does not yet give it). Given
    the pounds the book controls per underlying (exposure), a buy is refused that would take
    its underlying market over its share of the capital; None checks nothing. Given the daily
    returns of the order's line and of the lines held, over the same days (moves, by symbol), a
    buy is refused that moves with a held line above the settings' correlation; None checks
    nothing, as does a line with no returns."""
    symbol = order.line.symbol
    if isinstance(order, Sale):
        if order.quantity > held.get(symbol, 0):
            raise Refused(
                f"{order.order_id}: sells {order.quantity} of {symbol}, the book holds "
                f"{held.get(symbol, 0)}: the desk is long only"
            )
        return
    _above_stop(order)
    if standing is not None:
        _within_limits(order, settings, held, standing)
    if exposure is not None:
        _within_underlying(order, settings, exposure)
    if moves is not None:
        _apart(order, settings, held, moves)
    if symbol not in held and len(held) >= HOLDINGS:
        raise Refused(f"{order.order_id}: {len(held)} holdings already, at most {HOLDINGS}")
    whole = replace(order, quantity=order.quantity + held.get(symbol, 0))
    if cost(whole) > _room(order.line, settings):
        raise Refused(
            f"{order.order_id}: {cost(whole)} pounds for {whole.quantity} shares, counted "
            f"{order.line.leverage} times for what it controls, is over a fifth of the "
            f"capital of {settings.capital}"
        )


def _above_stop(order: Order) -> None:
    """Refuses a buy whose live price is at or under its stop: it would be sold at once."""
    if order.market is not None and order.market <= order.stop:
        raise Refused(
            f"{order.order_id}: the emergency rule: {order.line.symbol} trades at {order.market}, "
            f"at or under the stop of {order.stop}; bought, it would be sold at once"
        )


def _room(line: Line, settings: Settings) -> Decimal:
    """Pounds one holding in the line may cost: a fifth of the capital, counted at what the
    line controls."""
    return settings.capital / HOLDINGS / line.leverage
