"""The ladder's Monte Carlo rung: synthetic trades with known answers."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from test_lab_sweep import BOEING, DAY, START, _keep

from desk import bars
from desk.bars import Source
from desk.lines import POUND
from desk.store import Bar
from lab import cell, ladder, montecarlo, universe

D = Decimal


def test_a_lone_loss_has_its_own_drawdown_and_return_in_every_path() -> None:
    got = montecarlo.resample([D("-0.1")], seed=1, paths=20)
    assert got.paths == 20
    assert got.drawdown == montecarlo.Spread(D("0.1"), D("0.1"), D("0.1"))
    assert got.returns == montecarlo.Spread(D("-0.1"), D("-0.1"), D("-0.1"))


def test_wins_alone_never_draw_down_and_compound() -> None:
    got = montecarlo.resample([D("0.1")] * 3, seed=1, paths=5)
    assert got.drawdown.high == 0
    assert got.returns.median == D("1.1") ** 3 - 1


def test_a_seed_repeats_and_another_seed_differs() -> None:
    coin = [D("0.02"), D("-0.02")] * 15
    assert montecarlo.resample(coin, seed=7) == montecarlo.resample(coin, seed=7)
    assert montecarlo.resample(coin, seed=7) != montecarlo.resample(coin, seed=8)


def test_a_fair_coin_is_centred_on_nothing_with_a_spread_both_sides_and_ordered_cuts() -> None:
    got = montecarlo.resample([D("0.02"), D("-0.02")] * 15, seed=3)
    assert got.paths == montecarlo.PATHS
    assert got.returns.low < 0 < got.returns.high
    assert abs(got.returns.median) < D("0.05")
    assert 0 < got.drawdown.low <= got.drawdown.median <= got.drawdown.high


@pytest.mark.parametrize(("trades", "paths"), [([], 10), ([D("0.1")], 0), ([D("-1")], 10)])
def test_input_that_cannot_be_resampled_is_refused(trades: list[Decimal], paths: int) -> None:
    with pytest.raises(ValueError, match="montecarlo"):
        montecarlo.resample(trades, seed=1, paths=paths)


def _home(tmp_path: Path, key: str = "k1") -> Path:
    """A data folder with one ladder cell that traded, and one grid cell held."""
    cell = ["rsi2_pullback", "3IN", "LSE", "2010-01-01", "2026-11-13"]
    ladder = {"cell": cell, "key": key, "from": "2011-01-03", "trades": 2}
    held = {"cell": cell, "code": "c", "data": "d", "trades": [["2011-01-13", "2011-01-27"]]}
    (tmp_path / "grid" / "store" / "LSE").mkdir(parents=True)
    (tmp_path / "grid" / "store" / "LSE" / "3IN.csv").write_text("")
    (tmp_path / "ladder").mkdir()
    (tmp_path / "ladder" / "set1.jsonl").write_text(json.dumps(ladder) + "\n")
    (tmp_path / "grid" / "held" / "LSE").mkdir(parents=True)
    (tmp_path / "grid" / "held" / "LSE" / "3IN.jsonl").write_text(json.dumps(held) + "\n")
    return tmp_path


def test_the_command_resamples_each_cell_once_and_again_only_a_changed_one(tmp_path: Path) -> None:
    home = _home(tmp_path)

    def gains(_job: montecarlo.Job) -> list[D]:
        return [D("0.02"), D("-0.01"), D("0.03")]

    assert montecarlo.run(home, gains) == "2 resampled now, 0 kept from before"
    kept = (home / "montecarlo" / "results.jsonl").read_text().splitlines()
    assert [json.loads(row)["id"][0] for row in kept] == ["ladder", "grid"]
    assert montecarlo.run(home, gains) == "0 resampled now, 2 kept from before"
    changed = home / "ladder" / "set1.jsonl"
    changed.write_text(changed.read_text().replace("k1", "k2"))
    assert montecarlo.run(home, gains) == "1 resampled now, 1 kept from before"
    assert montecarlo.run(home, nothing) == "0 resampled now, 2 kept from before"


def nothing(_job: montecarlo.Job) -> list[D]:
    return []


def test_a_cell_that_cannot_be_priced_is_told_and_tried_again(tmp_path: Path) -> None:
    home = _home(tmp_path)
    assert montecarlo.run(home, nothing) == (
        "0 resampled now, 0 kept from before, 2 could not be resampled"
    )


def test_a_cell_the_sizing_refuses_is_recorded_with_its_reason_and_the_rest_go_on(
    tmp_path: Path,
) -> None:
    home = _home(tmp_path)

    def gains(job: montecarlo.Job) -> list[D] | str:
        if job.source == "ladder":
            return "one share costs more than the room of 2000 pounds"
        return [D("0.02"), D("-0.01")]

    assert montecarlo.run(home, gains) == (
        "1 resampled now, 0 kept from before, 1 refused by the desk's sizing"
    )
    rows = [json.loads(r) for r in (home / "montecarlo" / "results.jsonl").read_text().splitlines()]
    assert "one share costs more" in rows[0]["refused"]
    assert rows[1]["trades"] == 2
    assert montecarlo.run(home, gains) == "0 resampled now, 2 kept from before"


def test_a_run_without_a_data_folder_stops_and_says_why() -> None:
    with pytest.raises(SystemExit, match="KESTREL2_DATA names no data folder"):
        montecarlo.main({})


def test_a_cut_short_last_line_is_left_out_and_a_kept_row_is_never_parsed(tmp_path: Path) -> None:
    home = _home(tmp_path)
    assert montecarlo.run(home, lambda _job: [D("0.02"), D("-0.01")]) == (
        "2 resampled now, 0 kept from before"
    )
    results = home / "montecarlo" / "results.jsonl"
    results.write_bytes(results.read_bytes() + b'{"id": ["gr')
    held = home / "grid" / "held" / "LSE" / "3IN.jsonl"
    held.write_text(held.read_text().replace("2011-01-13", "not a date"))  # parsing would raise
    assert montecarlo.run(home, nothing) == "0 resampled now, 2 kept from before"
    assert results.read_bytes().endswith(b"}\n")


def test_a_held_error_row_is_passed_over_counted_and_the_good_rows_measured(tmp_path: Path) -> None:
    home = _home(tmp_path)
    error = {"cell": ["rsi2_pullback", "3IN.faults", "LSE", "2010-01-01", "2026-11-13"]}
    with (home / "grid" / "held" / "LSE" / "3IN.jsonl").open("a") as held:
        held.write(json.dumps(error | {"code": "c", "error": "no bars"}) + "\n")
    assert montecarlo.run(home, lambda _job: [D("0.02")]) == (
        "2 resampled now, 0 kept from before, 1 grid error row passed over"
    )


def test_a_grid_cell_is_priced_from_the_database_never_a_bar_held_only_in_a_csv(
    tmp_path: Path,
) -> None:
    path, one = tmp_path / bars.LIVE, Decimal("1.3")
    _keep(tmp_path / "grid" / "store", BOEING, path=path)  # the CSV holds one bar more
    with bars.writing(path, Source.ARCHIVE) as opened:
        days = [START - timedelta(n) for n in range(-200, 30)]
        opened.daily(POUND, [Bar(d, one, one, one, one, 0) for d in days])
    todo = cell.Cell("breakout_20_10", BOEING, START, DAY)
    made = cell.run(todo, universe.read(path, BOEING).bars)
    job = montecarlo.Job("grid", todo, made.key.code + made.key.data, made.trades)
    priced = montecarlo.priced(tmp_path)
    assert priced(job) == priced(replace(job, trades=None)), "its trades were made on these bars"
    with pytest.raises(ladder.FAILED, match="NONE on US"):  # counted as one failure, never a stop
        priced(replace(job, cell=replace(todo, line=replace(BOEING, symbol="NONE"))))
