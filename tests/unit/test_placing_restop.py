"""placing: a resting stop moved at the paper broker, through the same fake gateway."""

from __future__ import annotations

from decimal import Decimal

import pytest
from test_paper import _account, _gateway, _order
from test_placing import (
    ACCOUNT,
    AT_STOP,
    BARE,
    CANCEL_7,
    ENDED_7,
    HELD,
    ID,
    RESTS,
    _msg,
    _paper,
)


def test_a_resting_stop_is_moved_with_the_new_one_sent_before_the_old_is_cancelled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old = _account([HELD], *_order("7", "SELL STP 3600.0", f"{ID}-stop", "PreSubmitted"))
    sent = _gateway(monkeypatch, old, RESTS, [ENDED_7])
    _paper().restop("IITU", Decimal("33"))
    lower = _msg(AT_STOP | {20: "3300.00", 1: "41"})
    assert sent == [ACCOUNT, lower, CANCEL_7]  #: one stop rests, the new one sent first
    sent = _gateway(monkeypatch, old)
    _paper().restop("IITU", Decimal("36.007"))
    assert sent == [ACCOUNT]  #: the same level sends nothing
    sent = _gateway(monkeypatch, BARE)
    with pytest.raises(ValueError, match="0 stops"):
        _paper().restop("IITU", Decimal("33"))
