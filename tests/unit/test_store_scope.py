"""The keeper's judging is scoped to the window the desk decides on (R-RUNNER-327)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from desk import bars, keeper, store, store_scope, venues
from desk.lines import Line

MSTR, DAY = Line("MSTR", "US", "USD", 1), date(2025, 11, 17)


def _history(crash_in: date) -> tuple[store.Bar, ...]:
    """MSTR's March 2000 days (226.75 -> 86.75 on the 20th) and a clean recent year, with a real
    crash on crash_in's session if that is inside the recent year."""
    days = [*venues.sessions("US", date(2000, 3, 1), date(2000, 3, 31))]
    days += venues.sessions("US", date(2022, 1, 3), date(2025, 11, 14))
    out = []
    for n, d in enumerate(days):
        p = Decimal(226 if d < date(2000, 3, 20) else 86) if d.year == 2000 else Decimal(50 + n % 3)
        p = p * Decimal("0.6") if d >= crash_in > date(2001, 1, 1) else p
        out.append(store.Bar(d, p, p + 1, p - 1, p, 900))
    return tuple(out)


def test_a_fault_in_deep_history_is_named_not_parked_and_one_in_the_window_parks(
    tmp_path: Path,
) -> None:
    old = _history(date(2000, 1, 1))
    _, faults, park = store_scope.judge(MSTR, old, DAY)
    assert park is None and any(f.day == date(2000, 3, 20) for f in faults)
    assert all(f.noted for f in faults if f.day < date(2022, 1, 1))
    kept = keeper._kept_in(tmp_path / "hot", {MSTR: old}, DAY, {})
    assert kept[0] == [] and bars.daily(tmp_path / "hot", MSTR)[-1].day == date(2025, 11, 14)
    assert f"{date(2000, 3, 20)} moved" in store.prepare(tmp_path / "s", {MSTR: old}, DAY)[0].reason
    recent = _history(date(2025, 10, 1))
    assert store_scope.judge(MSTR, recent, DAY)[2] is not None
