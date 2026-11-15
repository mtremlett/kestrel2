"""simcitycmd: the command lives the saved store in a night, or in the next block of fresh seeds."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from desk import command, simcity, simcitycmd, store

sys.path.insert(0, str(Path(__file__).parents[1] / "scenes"))  #: the scenes' rehearsal data
from rehearsal import CLEAN, SESSIONS  # noqa: E402  the path above comes first

SHORT = {line: [b for b in bars if b.day <= SESSIONS[50]] for line, bars in CLEAN.items()}
RATES = {"GBP": Decimal(1), "USD": Decimal("0.79")}
NOW = datetime(2025, 11, 17, 22, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def saved(monkeypatch: pytest.MonkeyPatch) -> None:
    """The ten weeks of the rehearsal lines stand in for the desk's price store."""
    monkeypatch.setattr(simcitycmd, "LINES", tuple(SHORT))
    monkeypatch.setattr(
        store,
        "read",
        lambda _root, name: next(tuple(b) for x, b in SHORT.items() if x.symbol == name),
    )
    monkeypatch.setattr(command, "rates", lambda _root, _day: RATES)


def test_the_command_lives_the_saved_store_in_a_night_and_its_code_is_zero_only_for_green(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The weekday night is a fifth of the worlds and --full all of them; the night's words
    are the answer, and the record is kept under the desk's folder, red or green."""
    monkeypatch.setattr(simcitycmd, "QUICK", range(1))
    monkeypatch.setattr(simcity, "WORLDS", range(2))
    for argv, worlds in (([], 1), (["--full"], 2)):
        code = simcitycmd.main(argv, {"KESTREL2_DATA": str(tmp_path)}, lambda: NOW)
        printed = capsys.readouterr().out
        assert f"lived {worlds} seeded worlds" in printed and code == int("SIMCITY RED" in printed)
    with (tmp_path / command.ROOT / simcity.NIGHTS).open(encoding="utf-8") as kept:
        assert len(kept.readlines()) == 3
    with pytest.raises(SystemExit):
        simcitycmd.main(["--fast"], {"KESTREL2_DATA": str(tmp_path)}, lambda: NOW)


def test_a_soak_lives_the_next_unused_block_of_fresh_seeds_and_logs_each_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Blocks of two, for speed: the first soak starts at FIRST, the next after the highest."""
    monkeypatch.setattr(simcitycmd, "BLOCK", 2)
    for first in (100, 102):
        simcitycmd.main(["--soak"], {"KESTREL2_DATA": str(tmp_path)}, lambda: NOW)
        printed = capsys.readouterr().out
        assert "lived 2 seeded worlds" in printed and f"Soak: seeds {first}-{first + 1}." in printed
    logged = (tmp_path / simcitycmd.SOAKED).read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["first"] for line in logged] == [100, 102]
