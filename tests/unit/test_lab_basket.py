"""The basket: a rule's lines pooled as one portfolio and judged on the pooled after-cost gains."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from test_lab_rung import FREE

from desk.lines import LINES
from lab import basket, rung, verdict
from lab.cell import Cell, Key, Trade
from lab.rung import Answer, Priced, Verdict

DAY = date(2010, 1, 1)
LINE_NAMES = ("VUSA", "ISF", "SMGB")


def _line_verdict(symbol: str) -> Verdict:
    """12 trades of a line: gains alternating 5% and 1%, so 6 and 6 after the (nil) costs."""
    gains = [Decimal("0.05"), Decimal("0.01")] * 6
    priced = tuple(
        Priced(Trade(DAY, DAY), 1, Decimal(100), 100 * (1 + g), FREE, (DAY, DAY)) for g in gains
    )
    line = next(one for one in LINES if one.symbol == symbol)
    window = Cell("breakout_20_10", line, DAY, DAY + timedelta(days=3652))
    return rung.verdict(Key(window, "code", symbol), priced)


def test_three_thin_lines_make_one_basket_of_36_trades_judged_on_the_pooled_gains(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(verdict, "EASED", True)
    lines = [_line_verdict(s) for s in LINE_NAMES]
    assert {v.answer for v in lines} == {Answer.THIN}  #: none is judged alone: 12 of 30
    row = basket.row(7, "breakout_20_10", lines, 50, Answer.PASS)
    #: by hand: 36 gains, 18 of 0.05 and 18 of 0.01; mean 0.03, each 0.02 from it, so the
    #: sample variance is 36 * 0.0004 / 35, the standard error sqrt(0.0004 / 35), and
    #: t = 0.03 / sqrt(0.0004 / 35) = 0.03 * sqrt(87500) = 8.874: above 2 on 36 trades, PASS
    assert row["trades"] == 36
    assert row["answer"] == "PASS"
    assert row["cell"] == ["breakout_20_10", "BASKET", "all lines pooled"]
    assert row["trials"] == 50
    assert "36 trades judged" in row["rungs"]["first"][1]
    assert "8.87 standard errors" in row["rungs"]["first"][1]
    assert row["unrun"] == verdict.UNRUN  #: a basket's pass is no pass of the whole ladder
    assert not verdict.goes(row)


def test_a_failing_basket_over_one_standard_error_is_incubate_listed_apart_and_never_goes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(verdict, "EASED", True)
    lines = [_line_verdict(s) for s in LINE_NAMES]
    failing = replace(lines[0], answer=Answer.FAIL, t=Decimal("1.5"))
    monkeypatch.setattr(rung, "verdict", lambda key, _: replace(failing, key=key))
    row = basket.row(7, "breakout_20_10", lines, 50, Answer.PASS)
    assert row["answer"] == "INCUBATE" and not verdict.goes(row)
    assert basket.row(7, "breakout_20_10", lines, 50, Answer.FAIL)["answer"] == "FAIL"
    table = verdict.write_table(tmp_path, "T", "Q?", [row], ["breakout_20_10"], 3, (1, 2))
    assert "## INCUBATE: paper only" in table.read_text(encoding="utf-8")
