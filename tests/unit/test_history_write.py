"""The pulled bars let into the database: kept under the broker's source, none from a refusal."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from desk import bars, history
from desk.history_write import held, keeper, main
from desk.lines import LINES
from desk.rollup import Candle
from desk.store import Bar, Refused

LINE = next(line for line in LINES if line.symbol == "VUAG")
PRICE = Decimal("110.5")


def test_a_pulled_answer_lands_under_the_brokers_source_and_a_refusal_adds_nothing(
    tmp_path: Path,
) -> None:
    live, keep = tmp_path / bars.LIVE, keeper(tmp_path / bars.LIVE, {"VUAG": 1})
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


def test_what_the_database_holds_from_the_broker_is_done_and_the_command_stops_in_a_round(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert held(tmp_path / bars.LIVE, [LINE]) == set()
    keeper(tmp_path / bars.LIVE, {"VUAG": 1})(
        LINE, "1d", (Bar(date(2026, 11, 12), PRICE, PRICE, PRICE, PRICE, 7),)
    )
    assert held(tmp_path / bars.LIVE, [LINE]) == {(LINE, "1d")}
    assert (LINE, "1d") not in history.plan([LINE], held(tmp_path / bars.LIVE, [LINE]))
    assert main(tmp_path, datetime(2026, 11, 16, 8, 10, tzinfo=UTC), ["3"]) == 1
    assert "desk round" in capsys.readouterr().err


def test_a_pulled_bar_is_turned_from_the_brokers_unit_into_the_lines_currency(
    tmp_path: Path,
) -> None:
    pence = Bar(date(2026, 11, 12), PRICE, PRICE, PRICE, PRICE, 7)
    keeper(tmp_path / bars.LIVE, {"VUAG": 100})(LINE, "1d", (pence,))
    assert bars.daily(tmp_path / bars.LIVE, LINE)[0].close == Decimal("1.105")
    with pytest.raises(KeyError):
        keeper(tmp_path / bars.LIVE, {})(LINE, "1d", (pence,))
