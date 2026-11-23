"""The stop-rule study (R-RUNNER-408): four rival stops sized by risk, judged after costs in and out
of sample, the worst fold given."""

from __future__ import annotations

from decimal import Decimal

from test_lab_rung import POUND, _bars, _walk

from desk.lines import LINES
from desk.orders import Leg, stop_under
from lab import stop_rules as stops
from lab.cell import Cell
from lab.rung import Answer

VUSA = next(line for line in LINES if line.symbol == "VUSA")
#: 21 flat bars give an ATR of 0.1 (each bar's range is a fifth beyond 10 times 0.01 either side)
FLAT = _bars([10.0] * 22)


def test_rivals_stop_where_registered_chandelier_climbs_and_the_worst_fold_is_given() -> None:
    spread = stops.atr(FLAT[:21])
    assert spread == Decimal("0.1") and stops.TRIALS == 4
    fill = Decimal(10)
    assert stops.stop_at("fixed", VUSA, fill, spread) == stop_under(VUSA, fill)
    assert [fill - stops.stop_at(r, VUSA, fill, spread) for r in ("atr2", "atr3")] == [
        Decimal("0.2"),
        Decimal("0.3"),
    ]
    rise = _bars([10, 10, 12, 12, 11.6, 11.6])  #: up to 12, then back 0.4 under it
    held, out = rise[:5], rise[5]
    leg, price, _, share = stops.exit_of("chandelier3", VUSA, held, out, Decimal("0.1"))
    assert (leg, price) == (Leg.STOP, Decimal("11.7")) and share == Decimal("0.03")  # lifted
    leg, price, _, _ = stops.exit_of("atr3", VUSA, held, out, Decimal("0.1"))
    assert (leg, price) == (Leg.SALE, out.open), "a fixed ATR stop stays put at 9.7"
    bars = _walk(7, 0.012, days=1500)
    walked = stops.judge(Cell("breakout_20_10", VUSA, bars[0].day, bars[-1].day), bars, POUND, 3)
    assert set(walked) == set(stops.RULES) and all(len(w.folds) == 3 for w in walked.values())
    assert all(w.worst.outside.answer in set(Answer) for w in walked.values())
