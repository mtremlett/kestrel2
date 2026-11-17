"""The pulled bars let into the database: kept under the broker's source, none from a refusal."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from desk import bars
from desk.history_write import keeper
from desk.lines import LINES
from desk.rollup import Candle
from desk.store import Bar, Refused

LINE = next(line for line in LINES if line.symbol == "VUAG")
PRICE = Decimal("110.5")


def test_a_pulled_answer_lands_under_the_brokers_source_and_a_refusal_adds_nothing(
    tmp_path: Path,
) -> None:
    live, keep = tmp_path / bars.LIVE, keeper(tmp_path / bars.LIVE)
    day = Bar(date(2026, 11, 12), PRICE, PRICE, PRICE, PRICE, 7)
    assert keep(LINE, "1d", Refused("none")) == 0 and not live.exists()
    assert keep(LINE, "1d", (day,)) == 1 and keep(LINE, "1d", (day,)) == 1
    assert bars.daily(live, LINE) == (day,)
    assert bars.sources(live, LINE, bars.DAILY) == {bars.Source.IBKR: 1}
    start = datetime(2026, 11, 12, 9, 30, tzinfo=UTC)
    candle = Candle(start, PRICE, PRICE, PRICE, PRICE, 3, "ibkr")
    assert keep(LINE, "5m", (candle,)) == 1 and keep(LINE, "30m", (candle,)) == 1
    assert bars.five(live, LINE, start, datetime(2026, 11, 13, tzinfo=UTC))[0].volume == 3
    assert bars.timed(live, LINE, "30m", start, datetime(2026, 11, 13, tzinfo=UTC))[0].volume == 3
    with pytest.raises(ValueError, match="mark"):
        keep(LINE, "4h", (candle,))
