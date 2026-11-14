"""The ladder's resampled drawdowns: parts of the capital, drawn from the trial's name."""

from __future__ import annotations

import pytest
from test_lab_folds import _verdict

from desk.command import CAPITAL
from lab import drawdown


def test_the_deepest_fall_of_draws_of_the_trades_is_kept_as_a_part_of_the_capital() -> None:
    mixed = _verdict(*["-1000", "400", "700"] * 4).trades
    fall = drawdown.judge(mixed, "a trial")
    assert fall == drawdown.judge(mixed, "a trial") != drawdown.judge(mixed, "another")
    assert 1000 / float(CAPITAL) <= fall["median"] <= fall["p95"] <= 12000 / float(CAPITAL)
    assert drawdown.judge(_verdict("5", "7").trades, "wins") == {"median": 0.0, "p95": 0.0}
    with pytest.raises(ValueError, match="no judged trade"):
        drawdown.judge((), "none")
