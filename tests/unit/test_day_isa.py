"""day: the book is the ISA's, so a line shut out of one is never bought."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from desk import book, day
from desk.broker import Pretend
from desk.halt import Blocker
from desk.lines import Line
from desk.orders import Settings
from desk.store import Bar
from desk.strategy import Action, Decision

ON = date(2025, 1, 8)
CASES = [(True, None), (False, "shut out of an ISA"), (None, None)]


@pytest.mark.parametrize(("isa", "said"), CASES)
def test_a_line_shut_out_of_an_isa_is_not_bought(
    tmp_path: Path, isa: bool | None, said: str | None
) -> None:
    line = replace(Line("B", "LSE", "GBP", 1), isa=isa)
    broker = Pretend({line: (Bar(ON, 10, 10, 10, 10, 1),)}, {})
    broker.open(ON)
    want = Decision("bollinger", "B", ON, Action.BUY)
    sent = day._buy(
        tmp_path, broker, want, line, (Decimal(10), Decimal(1)), Settings(Decimal(1000)), ON
    )
    if said is None:
        assert sent.blocker is None and book.positions(tmp_path) == {"B": sent.filled}
    else:
        assert sent.blocker is Blocker.GATE and said in str(sent.reason)
        assert book.positions(tmp_path) == {}
