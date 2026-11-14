"""The book's concentration: holdings that move together are one bet, and the profit is split
by the cluster of lines that made it."""

from __future__ import annotations

import math
import random
from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from decimal import Decimal

import numpy as np
import pytest
from test_lab_rung import POUND, SPY, _bars

from desk.lines import LINES, Line
from desk.store import Bar
from lab import bets
from lab.rung import Rates

VUAG, EQQQ, QQQ5, SGLN, ISF, QQQ = (
    next(line for line in LINES if line.symbol == s)
    for s in ("VUAG", "EQQQ", "5QQQ", "SGLN", "ISF", "QQQ")
)
D = Decimal


def _moves(seed: int, size: float = 0.01, days: int = 400) -> list[float]:
    rng = random.Random(seed)  # noqa: S311 - a repeatable test walk, not a secret
    return [rng.gauss(0, size) for _ in range(days)]


def _made(*parts: tuple[float, Sequence[float]]) -> tuple[Bar, ...]:
    """A line whose day's move is so much of each series' move that day, one bar a day."""
    closes = [1000.0]
    for moves in zip(*(series for _, series in parts), strict=True):
        closes.append(closes[-1] * (1 + sum(k * m for (k, _), m in zip(parts, moves, strict=True))))
    return _bars(closes)


A, C, E, N = _moves(1), _moves(2), _moves(3), _moves(4, 0.002)
WORLD = {
    VUAG: _made((1, A)),
    QQQ5: _made((3, A), (1, N)),  #: the same market, geared three times
    SGLN: _made((1, C)),
    EQQQ: _made((-1, C), (1, N)),  #: the other side of SGLN's bet
    ISF: _made((1, E)),
}
LAST = WORLD[VUAG][-1].day
HELD = {LAST: {VUAG: D(2000)}}


def _see(
    world: Mapping[Line, Sequence[Bar]],
    gains: Mapping[Line, Decimal] | None = None,
    held: Mapping[date, Mapping[Line, Decimal]] = HELD,
    rates: Rates = POUND,
) -> bets.Concentration:
    """The world's concentration, each line's profit stated: nothing, where none is given."""
    return bets.measure(world, rates, held, dict.fromkeys(world, D(0)) | dict(gains or {}))


def _names(found: bets.Concentration) -> list[tuple[str, ...]]:
    return [tuple(line.symbol for line in cluster.lines) for cluster in found.clusters]


def test_the_number_of_independent_bets_and_the_clusters_worked_by_hand() -> None:
    apart = np.eye(5)
    assert bets.count([200.0] * 5, apart) == 5, "five equal holdings that share nothing"
    assert bets.count([200.0, 200.0, 0, 0, 0], apart) == 2, "what is not held is no bet"
    assert 1 < bets.count([1000.0, 10, 10, 10, 10], apart) < 1.001, "one holding and four crumbs"
    assert bets.count([200.0] * 5, np.ones((5, 5))) == 1, "five holdings of one market"
    assert bets.count([1.0, 1.0], np.array([[1.0, 3], [3, 9]])) == 1, "a market and itself geared"
    assert bets.count([1.0, 1.0], np.array([[1.0, -1], [-1, 1]])) == 1, "a bet and its hedge"
    assert bets.count([1.0, 1.0], np.array([[1.0, 0.5], [0.5, 1]])) == 1.6, "4 over 2.5"
    #: pounds count by how far they move: beside a line three times as wild, the calm one is
    #: nearly no bet at all (100 over 82), and three times the pounds in it make them two
    wild = np.array([[1.0, 0], [0, 9]])
    assert math.isclose(bets.count([1.0, 1.0], wild), 100 / 82)
    assert math.isclose(bets.count([3.0, 1.0], wild), 2)
    for none in ([0.0, 0.0], [-1.0, 2.0], [math.nan, 1.0], [math.inf, 1.0]):
        with pytest.raises(ValueError, match="pounds held"):
            bets.count(none, wild)
    #: a cluster: lines joined by a correlation of a half or more, either way, or by a chain
    three, gains = (VUAG, EQQQ, SGLN), {VUAG: D(10), EQQQ: D(-4), SGLN: D(30)}

    def split(ab: float, bc: float = 0.0) -> list[tuple[tuple[str, ...], Decimal]]:
        co = np.array([[4.0, 6 * ab, 0], [6 * ab, 9, 3 * bc], [0, 3 * bc, 1]])
        made = bets.split(three, co, gains)
        return [(tuple(line.symbol for line in c.lines), c.profit) for c in made]

    assert split(0.5) == [(("SGLN",), D(30)), (("VUAG", "EQQQ"), D(6))], "the largest gain first"
    assert split(-0.5) == split(0.5), "a line and its inverse are one bet"
    assert split(0.49) == [(("SGLN",), D(30)), (("VUAG",), D(10)), (("EQQQ",), D(-4))]
    assert split(0.5, -0.6) == [(("VUAG", "EQQQ", "SGLN"), D(36))], "joined through EQQQ"


def test_the_books_bets_and_its_profit_by_cluster_measured_on_its_lines_prices() -> None:
    held = {
        LAST - timedelta(1): {VUAG: D(2000), SGLN: D(2000), ISF: D(2000)},  #: three, three
        LAST: {VUAG: D(3000), QQQ5: D(1000)},  #: two holdings, one market
        #: two that share nothing, one three times as wild: about 100 over 82 again
        LAST - timedelta(2): {QQQ5: D(2000), SGLN: D(2000)},
    }
    gains = {VUAG: D(100), QQQ5: D(500), SGLN: D(-50), EQQQ: D(20), ISF: D(130)}
    found = _see(WORLD, gains, held)
    assert found.moves == 250, "the latest year of two-day moves, and no older"
    assert _names(found) == [("VUAG", "5QQQ"), ("ISF",), ("SGLN", "EQQQ")]
    assert [cluster.profit for cluster in found.clusters] == [D(600), D(130), D(-30)]
    assert found.top == D(600) / D(700), "six sevenths of the profit was one market's"
    #: the mean of the three days (2.94, 1.00 and 1.27), and the fewest beside it
    assert 1 <= found.fewest < 1.01 and 1.7 < found.bets < 1.78
    assert _see(WORLD, {VUAG: D(600), ISF: D(-500)}).top == 6, "the others lost five sixths"
    for none in ({}, {VUAG: D(5), ISF: D(-9)}):
        assert _see(WORLD, none).top is None, "no gain to share out"
    #: only the latest year is read: lines that moved as one until then are two bets now
    old, since = _moves(5, days=345), (_moves(8, days=255), _moves(9, days=255))
    parted = {line: _made((1, old + own)) for line, own in zip((VUAG, ISF), since, strict=True)}
    assert _names(_see(parted)) == [("VUAG",), ("ISF",)]
    #: New York closes hours after London, so most of a day's move reaches London's line a
    #: day late: over two days they are plainly one market. In pounds, each day at its rate
    late = _made((0.3, A), (0.7, [0.0, *A[:-1]]))
    rates = {bar.day: D("0.8") for bar in late}
    assert _names(_see({VUAG: WORLD[VUAG], SPY: late}, rates=rates)) == [("VUAG", "SPY")]
    #: two dollar lines that barely move share the dollar's own moves: one bet, in pounds
    swung = dict(zip(rates, (bar.close / 1000 for bar in WORLD[SGLN]), strict=True))
    calm = (_made((1, _moves(seed, 0.001))) for seed in (6, 7))
    dollars, book = (
        dict(zip((SPY, QQQ), calm, strict=True)) | {ISF: WORLD[ISF]},
        {LAST: {ISF: D(9)}},
    )
    assert _names(_see(dollars, held=book, rates=swung)) == [("SPY", "QQQ"), ("ISF",)]
    with pytest.raises(ValueError, match=f"SPY: no rate of pounds per USD to price {LAST}"):
        _see(dollars, held=book, rates=swung | {LAST: D(0)})
    #: a day one venue was shut is set aside for every line, and the year is still a year; a
    #: book is read on such a day too, the last of them included
    gaps = tuple(bar for n, bar in enumerate(WORLD[QQQ5]) if n % 7)
    shut = _see(WORLD | {QQQ5: gaps, ISF: WORLD[ISF][:-1]})
    assert shut.moves == 250 and _names(shut)[0] == ("VUAG", "5QQQ")


def test_what_cannot_be_measured_is_refused() -> None:
    assert _see({line: bars[-122:] for line, bars in WORLD.items()}).moves == 120
    with pytest.raises(ValueError, match="119 two-day moves .* fewer than 120"):
        _see({line: bars[-121:] for line, bars in WORLD.items()})
    with pytest.raises(ValueError, match="no lines"):
        _see({}, held={})
    for gains, book, odd in (({SPY: D(5)}, HELD, "SPY"), ({}, {LAST: {QQQ: D(5)}}, "QQQ")):
        with pytest.raises(ValueError, match=f"{odd}.*: held with no bars given, or of bars and"):
            _see(WORLD, gains, book)
    with pytest.raises(ValueError, match="'5QQQ', 'EQQQ', 'ISF', 'SGLN'.* profit only the one"):
        bets.measure(WORLD, POUND, HELD, {VUAG: D(5)})  #: a line's profit is said, never supposed
    with pytest.raises(ValueError, match="held nothing"):
        _see(WORLD, held={})
    with pytest.raises(ValueError, match="pounds held"):
        _see(WORLD, held={LAST: {}})
    #: each day held is weighed by the year's moves, so it lies in the year read
    first = WORLD[VUAG][-252].day
    assert _see(WORLD, held={first: HELD[LAST]}).bets == 1
    for out in (first - timedelta(1), LAST + timedelta(1)):
        with pytest.raises(
            ValueError, match=f"held on {out}, outside the year .* {first} to {LAST}"
        ):
            _see(WORLD, held={LAST: HELD[LAST], out: HELD[LAST]})
    with pytest.raises(ValueError, match="SGLN never moved"):
        _see(WORLD | {SGLN: _bars([10] * 401)})
