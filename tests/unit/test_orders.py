"""orders: a fifth of the capital to each holding, counted at what the line controls, a stop
where its market has fallen 10%, and Interactive Brokers UK's fixed fees (his ruling of 13
November 2026, docs/DECISIONS.md)."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from desk import orders
from desk.lines import STAMP_DUTY, Line
from desk.strategy import Action, Decision

PLAIN, THREE_X, FIVE_X = (
    Line("P", "LSE", "GBP", 1),
    Line("T", "LSE", "GBP", 3),
    Line("X", "LSE", "GBP", 5),
)
DOLLAR = Line("D", "US", "USD", 1)
TEN_K = orders.Settings(capital=Decimal(10_000))
ON = date(2025, 11, 14)


def _buy(line: Line) -> Decision:
    return Decision("rule", line.symbol, ON, Action.BUY)


def _order(line: Line, quantity: int, price: str, fx: str = "1") -> orders.Order:
    return orders.Order("o", line, quantity, Decimal(price), Decimal(fx), Decimal("0.01"))


def test_a_holding_is_a_fifth_of_the_capital_counted_at_what_the_line_controls() -> None:
    for line, fx, room in (
        (PLAIN, "1", Decimal(2000)),
        (THREE_X, "1", Decimal(2000) / 3),
        (FIVE_X, "1", Decimal(400)),
        (DOLLAR, "0.79", Decimal(2000)),
    ):
        order = orders.size(_buy(line), line, Decimal("7.30"), Decimal(fx), TEN_K, {})
        more = _order(line, order.quantity + 1, "7.30", fx)
        assert orders.cost(order) <= room < orders.cost(more), line
        orders.gate(order, TEN_K, {})
        with pytest.raises(orders.Refused, match="a fifth"):
            orders.gate(more, TEN_K, {})
    exact = orders.size(_buy(PLAIN), PLAIN, Decimal(1), Decimal(1), TEN_K, {})  #: 1997 + 3 fee
    assert orders.cost(exact) == 2000 and exact.quantity == 1997, "a cost of exactly the room fits"
    orders.gate(exact, TEN_K, {})
    held = {"V": 10, "W": 10, "X": 10, "P": 997}  #: four holdings, P's 997 of its 1997 at a pound
    assert orders.size(_buy(PLAIN), PLAIN, Decimal(1), Decimal(1), TEN_K, held).quantity == 1000
    assert orders.size(_buy(PLAIN), PLAIN, Decimal(2), Decimal(1), TEN_K, held).quantity == 1
    for full, why in (({"P": 1997}, "no room"), ({s: 1 for s in "VWXYZ"}, "5 holdings already")):
        with pytest.raises(orders.Refused, match=why):
            orders.size(_buy(PLAIN), PLAIN, Decimal(1), Decimal(1), TEN_K, full)


def test_the_stop_sits_where_the_market_under_the_line_has_fallen_ten_percent() -> None:
    plain = orders.size(_buy(PLAIN), PLAIN, Decimal("50.25"), Decimal(1), TEN_K, {})
    stops = [
        orders.size(_buy(x), x, Decimal("50.25"), Decimal(1), TEN_K, {}).stop
        for x in (THREE_X, FIVE_X)
    ]
    assert [plain.stop, *stops] == [Decimal("45.225"), Decimal("35.175"), Decimal("25.125")]
    with pytest.raises(ValueError, match="empties"):
        orders.size(_buy(PLAIN), replace(PLAIN, leverage=10), Decimal(10), Decimal(1), TEN_K, {})
    assert plain.order_id == "20251114-rule-P", "the same decision must make the same order"


def test_every_cost_of_a_leg_is_charged_line_by_line_from_the_one_model() -> None:
    #: London: 0.05% of the value, at least 3 pounds
    assert orders.cost(_order(PLAIN, 100, "10")) == Decimal(1003)
    assert orders.cost(_order(PLAIN, 1000, "10")) == Decimal(10005)
    #: US: half a cent a share, at least a dollar, at most 1% of the value; then 0.03% on the
    #: rate for every dollar bought, the commission's included
    rate = Decimal("0.8") * Decimal("1.0003")
    assert orders.cost(_order(DOLLAR, 100, "10", "0.8")) == Decimal(1001) * rate
    assert orders.cost(_order(DOLLAR, 1000, "10", "0.8")) == Decimal(10005) * rate
    assert orders.cost(_order(DOLLAR, 10, "5", "0.8")) == Decimal("50.5") * rate
    #: a UK share's purchase pays half of one per cent in tax, and its sale none; every leg
    #: loses a twentieth of one per cent to the spread and as much to slippage, each times the
    #: line's leverage, and a stop's sale slips three times as far
    share, pound = replace(THREE_X, uk_tax=STAMP_DUTY), Decimal(1)
    assert orders.cost(_order(share, 1000, "10")) == Decimal(10055), "the tax is cash it takes"
    quoted = _order(Line("I", "LSE", "USD", 1, STAMP_DUTY), 1000, "10", "0.8")
    assert orders.cost(quoted) == Decimal(10055) * rate, "a tax paid in dollars is converted"
    assert [orders.charges(share, leg, 1000, Decimal(10), pound) for leg in orders.Leg] == [
        _charges("5 15 15 0 50"),
        _charges("5 15 15 0 0"),
        _charges("5 15 45 0 0"),
    ]
    #: a US sale pays its regulators too, 20.60 dollars a million sold and 0.0195 cents a
    #: share, at most 9.79 dollars; the dollars left are converted
    sold = orders.charges(DOLLAR, orders.Leg.SALE, 1000, Decimal(10), Decimal("0.8"))
    assert sold == _charges("4.3208 4 4 2.39870376 0"), "5.401 dollars; 9994.599 converted"
    penny = orders.charges(DOLLAR, orders.Leg.STOP, 100_000, Decimal(1), pound)
    assert penny.commission == Decimal("511.85"), "500, 2.06 and the most of 9.79"
    assert (sold + sold).part(1, 2) == sold and sold.total == Decimal("14.71950376")
    assert [orders.leg_of(name, n) for name, n in (("o-stop", 5), ("o", -5), ("o-stop", -5))] == [
        *orders.Leg
    ], "a fill's leg is read from its shares, and its stop's id"


def _charges(lines: str) -> orders.Charges:
    return orders.Charges(*map(Decimal, lines.split()))


def test_only_a_buy_for_its_own_line_is_sized_and_a_share_must_be_affordable() -> None:
    sell = Decision("rule", PLAIN.symbol, ON, Action.SELL)
    for decision, line in ((sell, PLAIN), (_buy(DOLLAR), PLAIN)):
        with pytest.raises(ValueError, match="buy"):
            orders.size(decision, line, Decimal(10), Decimal(1), TEN_K, {})
    with pytest.raises(orders.Refused, match="one share"):
        orders.size(_buy(PLAIN), PLAIN, Decimal(10), Decimal(1), orders.Settings(Decimal(60)), {})
    for line, fx in ((DOLLAR, "0"), (PLAIN, "0.8")):
        with pytest.raises(ValueError, match="exchange rate"):
            _order(line, 1, "10", fx)
    for leverage in (0, Decimal("2.5"), True):
        with pytest.raises(ValueError, match="leverage"):
            Line("Z", "US", "USD", leverage)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="quoted"):
        Line("Z", "LSE", "gbp", 1)
    for capital in ("Infinity", "0"):
        with pytest.raises(ValueError, match="capital"):
            orders.Settings(Decimal(capital))


def test_a_sale_passes_the_gate_only_for_shares_the_book_holds() -> None:
    sale = orders.Sale("s", PLAIN, 10)
    orders.gate(sale, TEN_K, {"P": 10, "Q": 1, "R": 1, "S": 1, "T": 1})
    for held in ({"P": 9}, {}):
        with pytest.raises(orders.Refused, match="long only"):
            orders.gate(sale, TEN_K, held)
    with pytest.raises(ValueError, match="shares"):
        orders.Sale("s", PLAIN, 0)
    assert orders.strategy_of(orders.order_id_of(_buy(PLAIN))) == "rule"
