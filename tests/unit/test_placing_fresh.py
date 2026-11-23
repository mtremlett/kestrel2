"""placing: an order's freshness is read from its own session, never from its id."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from test_paper import _gateway
from test_placing import AT, BUY_IT, DATED, _paper, _ready

from desk.orders import Refused


def test_a_stale_order_is_refused_and_a_fresh_one_clears_whatever_its_id_says(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _ready(tmp_path)
    _gateway(monkeypatch, [])
    stale = replace(BUY_IT, order_id=f"{AT:%Y%m%d}-rsi2-IITU", session=AT.date())  # id looks fresh
    with pytest.raises(Refused, match="the one it is dated"):
        _paper(root)._cleared(stale)
    fresh = replace(BUY_IT, order_id="20200101-rsi2-IITU", session=DATED)  # id looks ancient
    assert _paper(root)._cleared(fresh)[0].line.symbol == "IITU"
