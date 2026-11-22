"""Known answers for Grimes's ten setups (desk/grimes.py), each taken from the catalogue's own
definition (kestrel2_research/grimes/catalogue.md, section 3): a hand-built daily series on which
the rule must buy on one known bar, and a near-miss, one condition of the catalogue broken, on
which it must not; MGMT (section 2) on hand-made marks; and the future-blind check (B3)."""

from datetime import date, timedelta
from decimal import Decimal

from desk.grimes import Chart, diverged
from desk.store import Bar

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
