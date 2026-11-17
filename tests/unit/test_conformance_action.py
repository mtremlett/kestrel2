"""The two sides of a conformance step must name the same action, judged on fills (not the
broker's status words), and the pretend side is priced at the real stop's fill."""

from __future__ import annotations

from pathlib import Path

import pytest
from test_conformance import ID, MON, PRETEND, _run, _world

from desk import conformance, ended

TAPE = (  # step 5 of the 16 November US tape: the real fill and IBKR's reason
    f"done; fills: {ID.format(3)}-stop -16 at 159.13; held: none; stops: none",
    f"{ID.format(3)}-stop: Cancelled by Trader",
)


def test_the_pretend_side_is_priced_at_the_real_stop_fill_and_a_sale_by_hand_differs() -> None:
    real, _ = TAPE
    assert ended.action(real, "") == ended.action(PRETEND["the stop triggered"], "")
    assert ended.action(PRETEND["a refusal"], "") == "no fill"
    by_hand = real.replace("-stop -16", " -16")  # not under the stop name
    assert ended.action(by_hand, "") != ended.action(PRETEND["the stop triggered"], "")


def test_a_stop_filled_though_the_runs_own_swap_cancelled_the_old_one_passes_with_the_words_kept(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _world(monkeypatch)  # 17 November 15:05 US: -16 at the stop, "Cancelled by Trader" beside it
    swapped = {f"{ID.format(3)}-stop": "Cancelled by Trader"}
    monkeypatch.setattr(conformance, "reasons", lambda _door: swapped)
    assert _run(tmp_path, MON, "london") == 0
    assert "Cancelled by Trader" in next(tmp_path.rglob("trades-*.csv")).read_text()


def test_a_stop_that_rests_unsold_at_the_real_broker_rests_at_the_pretend_one_and_the_run_passes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _world(monkeypatch)  # London, 16 November 13:57: the stop put above the market was not sold
    name = f"{ID.format(3)}-stop"
    monkeypatch.setattr(
        conformance, "_raised", lambda *_: lambda _: conformance.STILL.format(name, 30)
    )
    assert _run(tmp_path, MON, "london") == 0
