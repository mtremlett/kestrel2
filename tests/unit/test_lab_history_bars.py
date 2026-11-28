"""The ladder's bars come from the history database alone: its lines, each line's bars and the
pound are read there with no grid/store folder, and a line it lacks is named."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk import bars
from desk.lines import POUND
from desk.store import Bar
from lab import history_bars, ladder, market, universe

ONE, TWO = universe.UNIVERSE[0], universe.UNIVERSE[1]
DAYS = [ladder.END - timedelta(n) for n in range(10, -3, -1)]  #: two days run past the window


def _series(price: str) -> list[Bar]:
    close = Decimal(price)
    return [Bar(d, close, close, close, close, 0) for d in DAYS]


def test_each_set_reads_lines_bars_and_pound_from_the_history_database_and_names_a_lack(
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError, match=bars.HISTORY):
        history_bars.lines(tmp_path)
    with bars.writing(tmp_path / bars.LIVE) as opened:
        opened.days(ONE, _series("10"))
    assert not (tmp_path / "grid").exists()
    assert history_bars.lines(tmp_path) == (ONE,)
    read = history_bars.reader(tmp_path)
    assert [b.day for b in read(ONE)] == [d for d in DAYS if d <= ladder.END]
    with pytest.raises(LookupError, match=TWO.symbol):
        read(TWO)
    with pytest.raises(LookupError, match=POUND.symbol):
        history_bars.pounds(tmp_path)
    #: a day the archive lacks, filled by the one writer from FRED's DEXUSUK, is the rate read
    held, fed = _series("1.25"), _series("1.6")[5:6]
    for source, given in (bars.Source.ARCHIVE, held[:5] + held[6:]), (bars.Source.FED_NOON, fed):
        with bars.writing(tmp_path / bars.LIVE, source) as opened:
            opened.days(POUND, given)
    rates = history_bars.pounds(tmp_path)
    assert rates[DAYS[6]] == Decimal("0.625") and rates[DAYS[5]] == Decimal("0.8")
    assert rates[ladder.END] == Decimal("0.8") and min(rates) > DAYS[0]
    assert max(rates) == ladder.END and isinstance(next(iter(rates)), date)


def test_every_research_lines_old_holes_are_listed_by_the_preflights_own_rule(
    tmp_path: Path,
) -> None:
    """R-RUNGS-40: a session missing deep in a research line's daily history is listed for the
    greenkeeper, by the same rule the ladder's pre-flight refuses a set on; a whole line is not."""
    with pytest.raises(FileNotFoundError, match=bars.HISTORY):
        history_bars.holes(tmp_path)
    old = [date(2001, 7, d) for d in (23, 24, 25, 26, 27, 30)]
    lost = old[3]
    with bars.writing(tmp_path / bars.LIVE) as opened:
        opened.days(ONE, [Bar(d, *(Decimal(5),) * 4, 0) for d in old if d != lost])
        opened.days(TWO, _series("20"))
    assert history_bars.holes(tmp_path) == {ONE: (lost,)}
    rates = {d: Decimal(1) for d in old}
    named = market.gaps(ONE, bars.daily(history_bars.database(tmp_path), ONE), rates, *old[::5])
    assert named == (f"{ONE.symbol} has no bar on {lost}, a session of {ONE.venue}",)
