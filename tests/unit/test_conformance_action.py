"""The two sides of a conformance step must name the same action: a stop IBKR cancelled and the
desk sold by hand is not a stop fill, and the pretend side is priced at the real stop's fill."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from test_conformance import ID, MON, PRETEND, _plan, _run, _world

from desk import conformance, ended

TAPE = (  # step 5 of the 16 November US tape: the real fill and IBKR's reason
    f"done; fills: {ID.format(3)}-stop -16 at 159.13; held: none; stops: none",
    f"{ID.format(3)}-stop: Cancelled by Trader",
)


def test_a_stop_sold_by_hand_is_no_stop_fill_and_the_pretend_side_is_priced_at_the_real_fill(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real, said = TAPE
    assert ended.action(real, said) == "stop cancelled, sold at market"
    assert ended.action(real, "") == ended.action(PRETEND["the stop triggered"], "")
    assert ended.action(PRETEND["a refusal"], "") == "no fill"
    run = _plan(monkeypatch)  # priced from the real fill: above the stop's level it sells at once
    assert conformance.pretend(run, Decimal("159.13"))["the stop triggered"] == (
        f"done; fills: {ID.format(3)}-stop -18 at 159.13; held: none; stops: none"
    )


def test_a_run_whose_stop_was_cancelled_by_hand_is_refused_loudly_though_its_fill_looks_the_same(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _world(monkeypatch)
    ended = {f"{ID.format(3)}-stop": "Cancelled by Trader"}
    monkeypatch.setattr(conformance, "reasons", lambda _door: ended)
    assert _run(tmp_path, MON, "london") == 1
    assert "the stop triggered (THE TWO SIDES DID DIFFERENT THINGS)" in capsys.readouterr().out


def test_a_stop_that_rests_unsold_at_the_real_broker_rests_at_the_pretend_one_and_the_run_passes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _world(monkeypatch)  # London, 16 November 13:57: the stop put above the market was not sold
    name = f"{ID.format(3)}-stop"
    monkeypatch.setattr(
        conformance, "_raised", lambda *_: lambda _: conformance.STILL.format(name, 30)
    )
    assert _run(tmp_path, MON, "london") == 0
