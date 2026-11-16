"""simcitycmd: the command lives the saved store in a night, or in the next block of fresh seeds."""

from __future__ import annotations

import json
import sys
from contextlib import suppress
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from desk import command, keeper, simcity, simcitycmd, venues
from desk.broker import Crash, Fault, Pretend
from desk.lines import Line
from desk.orders import Order
from desk.store import Bar

sys.path.insert(0, str(Path(__file__).parents[1] / "scenes"))  #: the scenes' rehearsal data
from rehearsal import CLEAN, SESSIONS  # noqa: E402  the path above comes first

SHORT = {line: [b for b in bars if b.day <= SESSIONS[50]] for line, bars in CLEAN.items()}
RATES = {"GBP": Decimal(1), "USD": Decimal("0.79")}
NOW = datetime(2025, 11, 17, 22, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def saved(monkeypatch: pytest.MonkeyPatch) -> None:
    """The ten weeks of the rehearsal lines stand in for the desk's price store."""
    monkeypatch.setattr(simcitycmd, "LINES", tuple(SHORT))
    monkeypatch.setattr(simcitycmd, "YARDSTICK", next(iter(SHORT)))
    monkeypatch.setattr(
        keeper,
        "saved",
        lambda _home, _day, lines: ({x: tuple(SHORT[x]) for x in lines}, frozenset()),
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
        assert f"lived {worlds} seeded worlds" in printed
        deep = [x for x in ("Stress:", "Calibration:", "Lifecycle:") if x in printed]
        assert deep == ([] if not argv else ["Stress:", "Calibration:", "Lifecycle:"])
        assert code == int("SIMCITY RED" in printed or "BROKEN" in printed.split("Stress:")[-1])
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


def test_the_worlds_are_built_from_the_keepers_store_and_not_the_old_desk_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A day only the keeper's daily store holds (desk/store is empty) reaches the worlds."""
    monkeypatch.undo()
    line, lived = Line("VUAG", "LSE", "GBP", 1), []

    def run(_root: Path, held: dict[Line, tuple[Bar, ...]], *_rest: object) -> simcity.Night:
        lived.append(held)
        raise RuntimeError("the worlds were given what the keeper holds")

    days = venues.sessions("LSE", date(2025, 8, 4), date(2025, 11, 17))
    prices = [Decimal(100 + n % 5) for n in range(len(days))]
    bars = tuple(
        Bar(d, p, p + 1, p - 1, p, 1000 + n)
        for n, (d, p) in enumerate(zip(days, prices, strict=True))
    )
    keeper.keep(tmp_path, NOW, (line,), lambda _line, _day: bars, lambda _l, _n: (), lambda: 0.0)
    monkeypatch.setattr(simcitycmd, "LINES", (line,))
    monkeypatch.setattr(command, "rates", lambda _root, _day: RATES)
    monkeypatch.setattr(simcity, "run", run)
    with pytest.raises(RuntimeError, match="keeper holds"):
        simcitycmd.main([], {"KESTREL2_DATA": str(tmp_path)}, lambda: NOW)
    assert lived[0][line][-1].day == date(2025, 11, 14)


def test_a_planted_stuck_order_is_counted_in_the_lifecycle_by_where_it_ended() -> None:
    """Each order ends in one place: filled, part-filled, refused, or left working (stuck)."""
    line, on = next(iter(SHORT)), SESSIONS[1]
    price = SHORT[line][1].open
    for fault, ends in (
        (Fault.STRAND, "stuck"),
        (Fault.PARTIAL, "part"),
        (Fault.REJECT, "refused"),
        (None, "filled"),
    ):
        broker = Pretend(SHORT, {} if fault is None else {line.symbol: fault})
        broker.open(on)
        with suppress(Crash):
            broker.place(Order("A", line, 4, price, Decimal(1), price / 2))
        got = simcitycmd.lifecycle(broker)
        assert got == simcitycmd.Lifecycle(**{k: int(k == ends) for k in vars(got)})
    assert "1 filled" in got.words() and "0 stuck" in got.words()
