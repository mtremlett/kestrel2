"""R-RUNNER-569: a conformance run begins by settling what its own earlier runs left at the
broker: a resting stop of an earlier day is cancelled and recorded, the desk's order beside it is
untouched, and one the broker will not end stops the run before anything is sent."""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_conformance import MON, PRETEND, _run, _world

from desk import book, conformance, conformance_parts, paper

OLD = "20261124-conf3lse1013-SMGB-stop"


def _rest(client: str, number: str, ref: str) -> paper.Resting:
    return paper.Resting(
        "1", number, client, "DU1", "SMGB", "SELL", Decimal(5), "STP", "9", ref, "PreSubmitted",
        Decimal(5), Decimal(100),
    )  # fmt: skip


def _broker(patch: pytest.MonkeyPatch, word: str) -> None:
    """The paper broker holds a conformance stop and a desk order, and answers every cancel the
    run asks with `word` for the stop (7) alone: the desk's order (9) has no word."""
    mine, desk = _rest("223", "7", OLD), _rest("222", "9", "d")
    patch.setattr(paper, "whole", lambda _door: paper.Account((), (mine, desk)))
    patch.setattr(conformance_parts, "paper", SimpleNamespace(dial=lambda _talk: {"7": word}))


def test_an_earlier_runs_resting_stop_is_cancelled_and_recorded_before_the_run_sends(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _world(monkeypatch)
    _broker(monkeypatch, "Cancelled")
    assert _run(tmp_path, MON, "london") == 0
    record = tmp_path / "conformance" / "trades-london-20261116-1005.csv"
    with record.open(newline="", encoding="utf-8") as kept:
        rows = list(csv.reader(kept))[1:]
    assert [row[1] for row in rows[:-1]] == [conformance.LEFT_OVER, *PRETEND]
    assert OLD in rows[0][2]


def test_an_order_the_broker_will_not_end_is_named_and_nothing_is_sent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _world(monkeypatch)
    _broker(monkeypatch, "Rejected")
    assert _run(tmp_path, MON, "london") == 1
    assert f"{OLD} (Rejected)" in capsys.readouterr().out
    assert not book.fills(tmp_path / "conformance")
