"""The liquidity rung: a rule whose trades, at the desk's own sizing, take more than the desk's
share of a day's volume FAILS; one on a deep line passes, with its capacity in pounds."""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal

from desk.command import CAPITAL
from desk.lines import LINES
from desk.orders import LIQUIDITY, Charges
from desk.store import Bar
from lab import cell, rung, rung_liquidity
from lab.cell import Cell, Trade
from lab.rung import Answer, Priced

DAY, SHARES, PAID = date(2010, 1, 4), 100, Decimal(1000)
VUSA = next(x for x in LINES if x.symbol == "VUSA")
KEY = cell.key(Cell("breakout_20_10", VUSA, DAY, DAY), [Bar(DAY, PAID, PAID, PAID, PAID, 1)])
TRADES = 40


def _priced(n: int, gain: float) -> Priced:
    """The n-th trade: decided on day 3n, filled on the next two days, 100 shares."""
    bought = DAY + timedelta(3 * n)
    held = (bought + timedelta(1), bought + timedelta(2))
    received = PAID * (1 + Decimal(str(gain)))
    costs = Charges(Decimal(1), *[Decimal(0)] * 4)
    return Priced(Trade(bought, bought + timedelta(1)), SHARES, PAID, received, costs, held, None)


def _first(mean: float = 0.02) -> rung.Verdict:
    """The first rung's verdict on TRADES trades whose gains spread about `mean`."""
    rng = random.Random(7)  # noqa: S311 - a repeatable test sample, not a secret
    trades = tuple(_priced(n, round(rng.gauss(mean, 0.01), 6)) for n in range(TRADES))
    return rung.verdict(KEY, trades)


def _bars(volume: int, thin: dict[date, int] | None = None) -> tuple[Bar, ...]:
    """A bar a day over every trade's days, each of `volume` shares but those named thin."""
    days = [DAY + timedelta(n) for n in range(3 * TRADES + 3)]
    one = Decimal(10)
    return tuple(Bar(d, one, one, one, one, (thin or {}).get(d, volume)) for d in days)


def test_a_deep_line_passes_and_names_its_capacity_in_pounds() -> None:
    first = _first()
    assert first.answer is Answer.PASS
    answer, why = rung_liquidity.RUNG.judge(first, _bars(1_000_000), {})
    assert answer is Answer.PASS, why
    depth = rung_liquidity.judge(first, _bars(1_000_000))
    assert depth.worst == Decimal(SHARES) / 1_000_000
    assert depth.capacity == Decimal(1_000_000)  #: 100 shares of a million: 1% at 100 times the pot
    assert Decimal(10_000) == CAPITAL and "about 1,000,000 pounds" in why
    #: the volume read is named by the line whose bars were judged: a proxy's, where one stands in
    assert "of VUSA's volume" in why


def test_a_thin_line_fails_where_its_trades_take_more_than_the_desks_share_of_the_day() -> None:
    first = _first()
    over = int(SHARES / LIQUIDITY) - 1  #: 100 shares a little over 1% of the day's volume
    answer, why = rung_liquidity.RUNG.judge(first, _bars(over), {})
    assert answer is Answer.FAIL and "of VUSA's volume" in why, why
    at = int(SHARES / LIQUIDITY)  #: exactly 1%: not more than the share, so it passes
    assert rung_liquidity.RUNG.judge(first, _bars(at), {})[0] is Answer.PASS


def test_one_thin_day_or_a_day_of_no_volume_fails_the_whole_rule() -> None:
    first = _first()
    sold = first.trades[5].held[1]
    for volume in (2_000, 0):
        answer, why = rung_liquidity.RUNG.judge(first, _bars(1_000_000, {sold: volume}), {})
        assert answer is Answer.FAIL and str(sold) in why, why


def test_a_rule_the_first_rung_did_not_pass_keeps_its_answer() -> None:
    """Only a PASS is lowered: a fail, a thin sample and no trades are the first rung's own."""
    failed = _first(-0.02)
    assert failed.answer is Answer.FAIL
    assert rung_liquidity.RUNG.judge(failed, _bars(1), {})[0] is Answer.FAIL
    thin = rung.verdict(KEY, _first().trades[:5])
    assert rung_liquidity.RUNG.judge(thin, _bars(1), {})[0] is Answer.THIN
    assert rung_liquidity.RUNG.judge(rung.verdict(KEY, ()), (), {})[0] is Answer.FAULT


def test_the_rung_is_declared_to_the_ladder_by_name() -> None:
    assert rung_liquidity.RUNG in rung.found()[0]
    assert rung_liquidity.RUNG.name == "liquidity"
