"""The collector: with fake vendors, one run writes a price cross-check, a macro series, an
earnings date and a timestamped headline into the one store; keys come from its environment
only and are never printed, and a source without a key is skipped, saying which."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from desk import bars, collector

NOW = datetime(2026, 11, 16, 22, 15, tzinfo=UTC)  #: a Monday evening: the day asked is Friday
HIDDEN = "hidden123"
ANSWERS = {
    "api.massive.com": {"results": [{"T": "AAPL", "c": 190.5}, {"T": "ZZZZ", "c": 1}]},
    "api.tiingo.com": [{"date": "2026-11-13T00:00:00.000Z", "close": 190.4}],
    "api.stlouisfed.org": {"observations": [{"date": "2026-11-13", "value": "4.1"}]},
    "finnhub.io/api/v1/calendar": {"earningsCalendar": [{"date": "2026-11-19", "symbol": "NVDA"}]},
    "finnhub.io/api/v1/news": [{"datetime": 1763280000, "headline": "Markets rally"}],
    "api.marketaux.com": {"data": [{"published_at": "2026-11-16T09:30:00.000000Z", "title": "M"}]},
    "gnews.io": {"articles": [{"publishedAt": "2026-11-16T08:00:00Z", "title": "G"}]},
}


def _ask(address: str) -> bytes:
    assert HIDDEN in address
    return json.dumps(next(a for host, a in ANSWERS.items() if host in address)).encode()


def _held(root: Path) -> dict[tuple[str, str], list[tuple[str, str]]]:
    with sqlite3.connect(root / bars.HISTORY) as store:
        rows = store.execute("SELECT kind, subject, at, value FROM fact").fetchall()
        raw = store.execute("SELECT count(*) FROM raw").fetchone()[0]
    assert raw > 0
    held: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for kind, subject, at, value in rows:
        held.setdefault((kind, subject), []).append((at, value))
    return held


def test_one_run_writes_the_four_kinds_and_never_prints_a_key(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    env = {name + "_API_KEY": HIDDEN for name in collector.NAMES}
    assert collector.run(tmp_path, env, NOW, _ask) == 0
    assert collector.run(tmp_path, env, NOW, _ask) == 0  # again: nothing is written twice
    held = _held(tmp_path)
    assert held[("price", "AAPL")] == [("2026-11-13", "190.5"), ("2026-11-13", "190.4")]
    assert ("price", "ZZZZ") not in held  # a ticker the desk holds no line for
    assert held[("macro", "DGS10")] == [("2026-11-13", "4.1")]
    assert held[("earnings", "NVDA")] == [("2026-11-19", "")]
    assert ("2025-11-16T08:00:00+00:00", "Markets rally") in held[("news", "finnhub")]
    assert ("2026-11-16T09:30:00+00:00", "M") in held[("news", "marketaux")]
    out = capsys.readouterr()
    assert HIDDEN not in out.out + out.err


def test_a_source_without_a_key_is_skipped_by_name_and_no_key_at_all_is_a_miss(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert collector.run(tmp_path, {"FRED_API_KEY": HIDDEN}, NOW, _ask) == 0
    err = capsys.readouterr().err
    assert "no GNEWS_API_KEY: gnews skipped" in err
    assert ("macro", "DGS10") in _held(tmp_path)
    assert collector.run(tmp_path, {}, NOW, _ask) == 1


def test_a_vendor_that_fails_is_told_and_the_others_still_land(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    def ask(address: str) -> bytes:
        if "gnews" in address:
            raise OSError(address)
        return _ask(address)

    env = {name + "_API_KEY": HIDDEN for name in collector.NAMES}
    assert collector.run(tmp_path, env, NOW, ask) == 1
    err = capsys.readouterr().err
    assert "gnews: OSError" in err
    assert HIDDEN not in err  # a fault's words may hold the address, and so the key
    assert ("macro", "DGS10") in _held(tmp_path)
