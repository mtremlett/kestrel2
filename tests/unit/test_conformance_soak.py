"""The conformance soak: a round of one share, many a day, each its own line."""

from __future__ import annotations

import csv
from datetime import timedelta
from pathlib import Path

import pytest
from test_conformance import FX, HOME, ISF, MON, SPY, STAMP, VUAG, _plan, _run_soak, _world

from desk import conformance, conformance_tape


def test_two_rounds_of_a_day_send_distinct_ids_and_both_are_recorded_and_a_desk_round_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _world(monkeypatch)
    assert _run_soak(tmp_path, MON, "london") == 0
    _run_soak(tmp_path, MON + timedelta(hours=1), "london")
    first, second = sorted((tmp_path / "conformance").glob("trades-london-*.csv"))
    ids = [path.read_text(encoding="utf-8") for path in (first, second)]
    assert "conf1lse1005" in ids[0] and "conf1lse1105" in ids[1]
    assert "conf1lse1105" not in ids[0] and "conf1lse1005" not in ids[1]
    assert _run_soak(tmp_path, MON.replace(hour=8, minute=10), "london") == 0
    assert "a desk round runs 08:00-08:30" in capsys.readouterr().out.splitlines()[-1]
    with (tmp_path / "conformance" / conformance_tape.LEDGER).open(encoding="utf-8") as kept:
        rows = list(csv.reader(kept))
    assert [row[0] for row in rows[1:]][:2] == [
        MON.isoformat(),
        (MON + timedelta(hours=1)).isoformat(),
    ]
    assert len(rows) == 4 and tuple(rows[0]) == conformance_tape.HEAD
    assert rows[1][2].endswith(f"Its line drawn by seed {int(MON.timestamp())}.")


def test_a_seed_draws_the_same_line_again_and_its_draws_reach_every_plain_line(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = _plan(monkeypatch)  #: no seed: the line that traded the most money, VUAG
    drawn = {
        s: conformance.plan([ISF, VUAG], SPY, MON.date(), FX, STAMP, HOME, seed=s)
        for s in range(12)
    }
    assert {plan.second.line for plan in drawn.values()} == {ISF, VUAG}
    assert drawn[7] == conformance.plan([VUAG, ISF], SPY, MON.date(), FX, STAMP, HOME, seed=7)
    assert run.second.line == VUAG
