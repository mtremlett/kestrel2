"""orders - AN ORDER, SIZED FROM THE ONE CAPITAL NUMBER. It cannot exist without its stop,
and the one pre-trade gate reads the same capital number as the sizer. THE ONE COST MODEL:
every cost of a leg, line by line, for whoever prices a buy, a sale or a stop's sale. AND THE
ONE ROUNDING POLICY for what is published of it."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from decimal import Decimal

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
from desk.orders_parts2 import (
    Charges as Charges,
)
from desk.orders_parts2 import (
    Leg as Leg,
)
from desk.orders_parts2 import (
    Order as Order,
)
from desk.orders_parts2 import (
    Refused as Refused,
)
from desk.orders_parts2 import (
    Sale as Sale,
)
from desk.orders_parts2 import (
    Settings as Settings,
)
from desk.orders_parts2 import (
    pennies as pennies,
)
from desk.risk import Standing, correlated_with, loss_limit, underlying_limit
from desk.store import Bar
from desk.strategy import Action, Decision

#: His ruling of 13 November 2026 (docs/DECISIONS.md): at most five holdings, each a fifth of
#: the capital counted at what the line controls, and a stop where its market has fallen 10%.
HOLDINGS = 5
STOP_FALL = Decimal("0.10")
#: STP-10, the one home (R-RUNGS-11, docs/DECISIONS.md): the most of the capital one holding may
#: lose when a gap jumps its stop; the stop alone risks STOP_FALL / HOLDINGS of it (2%).
GAP_LOSS = Decimal("0.05")


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
) -> Order:
    """The most whole shares whose cost, with the shares of the line already held, fits the
    line's room, and the stop, for a buy; fx is pounds per unit of the line's currency, and
    held is the book (book.positions)."""
    if decision.action is not Action.BUY or decision.symbol != line.symbol:
        raise ValueError(f"{line.symbol}: only a buy for this line is sized, not {decision}")
    order_id = order_id_of(decision)
    stop = stop_under(line, price)

    def order(quantity: int) -> Order:
        return Order(order_id, line, quantity, price, fx, stop, session=decision.day)

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


def _within_limits(
    order: Order, settings: Settings, held: Mapping[str, int], standing: Standing
) -> None:
    """Refuses a buy past a loss limit, or a new line past the day's count, naming the limit."""
    reached = loss_limit(standing, settings.capital, settings.day_loss, settings.week_loss)
    if reached is not None:
        raise Refused(f"{order.order_id}: no buy past {reached}")
    if order.line.symbol not in held and standing.new_lines >= settings.new_lines:
        raise Refused(
            f"{order.order_id}: {standing.new_lines} new lines entered today, the limit is "
            f"{settings.new_lines} a day"
        )


def _within_underlying(order: Order, settings: Settings, exposure: Mapping[str, Decimal]) -> None:
    """Refuses a buy that takes its underlying market past the cap, counted at its leverage."""
    line = order.line
    added = order.quantity * order.price * order.fx * line.leverage
    key = line.underlying or line.symbol
    over = underlying_limit(exposure, key, added, settings.capital, settings.underlying)
    if over is not None:
        raise Refused(f"{order.order_id}: {over}")


def _apart(
    order: Order,
    settings: Settings,
    held: Mapping[str, int],
    moves: Mapping[str, tuple[float, ...]],
) -> None:
    """Refuses a buy that moves with a line already held above the correlation cap."""
    symbol = order.line.symbol
    if symbol not in moves:
        return
    others = {s: moves[s] for s in held if s != symbol and s in moves}
    together = correlated_with(moves[symbol], others, float(settings.correlation))
    if together is not None:
        raise Refused(f"{order.order_id}: {symbol} is {together}")


MOVES_DAYS, MOVES_FROM = 60, 20  #: the daily returns kept for the correlation gate, and the fewest


def moves(
    held: set[str], archive: Mapping[Line, Sequence[Bar]], symbol: str
) -> dict[str, tuple[float, ...]]:
    """THE DAILY RETURNS OF A LINE AND OF THE LINES HELD (risk.correlated_with), by symbol, over
    the last sessions all of them have a bar for. All are left out when the days they share are
    under MOVES_FROM (nothing to judge by); a line whose price never moved is left out alone."""
    closes = {
        line.symbol: {bar.day: bar.close for bar in bars}
        for line, bars in archive.items()
        if line.symbol == symbol or line.symbol in held
    }
    if symbol not in closes:
        return {}
    shared = sorted(set.intersection(*(set(c) for c in closes.values())))[-MOVES_DAYS - 1 :]
    if len(shared) <= MOVES_FROM:
        return {}
    rows = {
        s: tuple(float(c[b] / c[a] - 1) for a, b in zip(shared, shared[1:], strict=False))
        for s, c in closes.items()
    }
    return {s: r for s, r in rows.items() if len(set(r)) > 1}
