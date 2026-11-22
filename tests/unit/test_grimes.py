"""Known answers for Grimes's ten setups (desk/grimes.py), each taken from the catalogue's own
definition (kestrel2_research/grimes/catalogue.md, section 3): a hand-built daily series on which
the rule must buy on one known bar, and a near-miss, one condition of the catalogue broken, on
which it must not; MGMT (section 2) on hand-made marks; and the future-blind check (B3)."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from desk.grimes import GRIMES, Chart, Mark, Trade, diverged
from desk.store import Bar
from desk.strategy import Action, _run

Leg = tuple[float | str, ...]  #: (price, bars) walked, or ("bar", open, high, low, close)
SPREAD = Decimal("0.4")  #: each walked bar reaches this far beyond its open and close


def _bars(legs: list[Leg]) -> list[Bar]:
    """Sixty calm bars at 100 (warm-up), then each leg: a walk of closes to a price over so many
    bars, or one bar given whole as ("bar", open, high, low, close)."""
    rows: list[tuple[Decimal, Decimal, Decimal, Decimal]] = []
    close = Decimal(100)
    for n in range(60):
        to = Decimal(100) + Decimal("0.3") * (n % 2)
        rows.append((close, max(close, to) + SPREAD, min(close, to) - SPREAD, to))
        close = to
    for leg in legs:
        if leg[0] == "bar":
            rows.append(tuple(Decimal(str(v)) for v in leg[1:]))  # type: ignore[arg-type]
            close = rows[-1][3]
            continue
        to, steps = Decimal(str(leg[0])), int(str(leg[1]))
        for k in range(1, steps + 1):
            step = rows[-1][3] + (to - rows[-1][3]) / (steps - k + 1)
            rows.append((close, max(close, step) + SPREAD, min(close, step) - SPREAD, step))
            close = step
    return [Bar(date(2020, 1, 1) + timedelta(n), *r, 1) for n, r in enumerate(rows)]


def _trades(name: str, legs: list[Leg]) -> dict[int, Action]:
    """The rule's buys and sales through the desk's one engine, by bar."""
    made = _run(name, GRIMES[name](), "X", _bars(legs))
    return {n: d.action for n, d in enumerate(made) if d.action is not Action.HOLD}


RISE: list[Leg] = [(96, 4), (104, 8), (101, 3), (109, 4), (113, 6)]  #: two legs up: TR, LEG 2

CASES: dict[str, tuple[list[Leg], int, list[Leg]]] = {
    # AG-01: PQ on a 45% pullback, three bars share the high 110.9; the bar to 112 trades through
    # it. Near-miss: PQ holds, but the bounce's highs climb 0.6 a bar: no bars share a high.
    "ag01_pullback_breakout": (
        [*RISE, (108, 5), (110.5, 2), (110.5, 2), (112, 1), (114, 2)],
        94,
        [*RISE, (108, 5), (110.5, 2), (111.1, 1), (111.7, 1), (112.3, 1), (112.9, 1)],
    ),
    # AG-02: a bounce makes the pullback's pivot low 107.6; a bar washes out to 104.6 and closes
    # back over it at 108.3. Near-miss: a deeper wash-out (104.0) closes under it, at 107.4.
    "ag02_washout": (
        [*RISE, (108, 5), (110.5, 2), (110.5, 2), (108.6, 2), ("bar", 108.6, 108.8, 104.6, 108.3)],
        96,
        [*RISE, (108, 5), (110.5, 2), (110.5, 2), (108.6, 2), ("bar", 108.6, 108.8, 104.0, 107.4)],
    ),
    # AG-03: A 113.4, B 107.6, C 111.9, D 106.1 (CD/AB = 1.0); two bars share 107.7; the next
    # trades through. Near-miss: D at 103.1 (CD/AB = 1.5, outside 0.8-1.25).
    "ag03_complex_pullback": (
        [*RISE, (108, 5), (111.5, 3), (106.5, 4), (107.3, 1), (107.3, 1), (109, 1)],
        99,
        [*RISE, (108, 5), (111.5, 3), (103.5, 6), (104.3, 1), (104.3, 1), (106, 1), (108, 3)],
    ),
}


def test_each_coded_setup_has_a_known_answer() -> None:
    assert set(CASES) == set(GRIMES)


@pytest.mark.parametrize("name", sorted(CASES))
def test_the_setup_buys_on_its_known_bar_and_the_near_miss_never_buys(name: str) -> None:
    fires, on, miss = CASES[name]
    assert _trades(name, fires) == {on: Action.BUY}
    assert Action.BUY not in _trades(name, miss).values()


@pytest.mark.parametrize("name", sorted(CASES))
def test_decisions_up_to_a_bar_ignore_every_bar_after_it(name: str) -> None:
    bars = _bars(CASES[name][0])
    whole = [d.action for d in _run(name, GRIMES[name](), "X", bars)]
    for cut in range(len(bars) - 12, len(bars)):
        assert [d.action for d in _run(name, GRIMES[name](), "X", bars[:cut])] == whole[:cut]


def test_after_plus_1r_the_stop_is_at_breakeven_and_the_fall_sells_there() -> None:
    legs = [*CASES["ag01_pullback_breakout"][0][:-1], (118, 5), (121, 3), (111, 6)]
    assert _trades("ag01_pullback_breakout", legs) == {94: Action.BUY, 103: Action.SELL}


def _mark(n: int, low: float, high: float, close: float, opened: float | None = None) -> Mark:
    """A bar's mark with K's middle at 100 and ATRb 1: the upper band at 102.25."""
    o, h, lo, c = (Decimal(str(v)) for v in (opened or close, high, low, close))
    bar = Bar(date(2020, 1, 1) + timedelta(n), o, h, lo, c, 1)
    return Mark(n, bar, Decimal(100), Decimal(1), Decimal(0), 0)


def test_mgmt_time_stop_partials_breakeven_chandelier_and_never_widening() -> None:
    late = Trade(Decimal(98), limit=3)  #: entry 100, risk 2: +1R is 102
    assert [late.step(_mark(n, 99, 101, 100, 100)) for n in range(3)] == [True, True, False]
    run = Trade(Decimal(98), limit=3)
    assert run.step(_mark(0, 99, 102.5, 102, 100))  #: through +1R: a third off, breakeven
    assert run.left == 1 - Decimal("0.33") and run.stop == Decimal("99.9")
    assert run.step(_mark(1, 101, 104.5, 104))  #: through +2R: a third left, the chandelier
    assert run.left == Decimal(1) / 3 and run.stop == Decimal(101)  #: 104 less 3 ATRb
    assert run.step(_mark(2, 101.5, 103, 102)) and run.stop == Decimal(101)  #: never down
    assert all(run.step(_mark(n, 102, 104, 103)) for n in range(3, 9))  #: no time stop now
    assert not run.step(_mark(9, 100.9, 102, 101)) and run.stopped


def test_mgmt_parabolic_stop_follows_each_bar_after_two_free_bars() -> None:
    trade = Trade(Decimal(95), limit=5)  #: entry 103, risk 8
    assert trade.step(_mark(0, 102.5, 104, 103.5, 103))  #: wholly over 102.25: a free bar
    assert trade.stop == Decimal(95)
    assert trade.step(_mark(1, 103.5, 105, 104.5)) and trade.stop == Decimal("103.5")
    assert not trade.step(_mark(2, 103.4, 105, 104))


def test_the_chart_confirms_a_swing_only_on_its_reversal() -> None:
    rise: list[Leg] = [(96, 4), (104, 8), ("bar", 104, 104.2, 102.6, 102.8)]  #: 1.8 off 104.4
    chart = Chart()
    for bar in _bars(rise):
        chart.add(bar)
    assert [p.price for p in chart.pivots][-1:] == [Decimal("95.6")]  #: under 2 ATRb: not yet
    chart.add(_bars([*rise, ("bar", 102.8, 103, 99.8, 100)])[-1])  #: 4.6 off it: confirmed
    assert [p.price for p in chart.pivots][-2:] == [Decimal("95.6"), Decimal("104.4")]


def test_a_long_grind_keeps_every_pivot_on_a_kept_bar_and_div_never_raises() -> None:
    grind: list[Leg] = [(112, 4), (104, 3), (108, 12), (103, 3)]
    grind += [(103 + 0.8 * k, 1) if k % 5 < 2 else (103 + 0.8 * k - 0.7, 1) for k in range(320)]
    chart = Chart()
    for bar in _bars(grind):
        if (mark := chart.add(bar)) is None:
            continue
        assert all(p.n >= chart.marks[0].n for p in chart.pivots)
        for k in range(len(chart.pivots)):
            diverged(chart, k, mark.n)  #: never "min() arg is an empty sequence"
