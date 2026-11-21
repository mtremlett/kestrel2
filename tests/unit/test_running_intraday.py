"""The step's intraday round (R-RUNNER-202): at each five-minute bar the rule's round is made
once, a restart mid-session sends nothing twice, and with no rule the day is unchanged."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import ClassVar

from test_running import MON, _desk

from desk import book, kill, running, venues
from desk.broker import Pretend
from desk.intraday import Span
from desk.lines import YARDSTICK
from desk.rollup import Candle
from desk.store import Bar


class _Flip:
    """In the market on every other bar, from the first."""

    span: ClassVar[Span] = Span.FIVE_MINUTES

    def step(self, bar: Candle, holding: bool) -> bool:  # noqa: ARG002 - the rule's template
        return bar.start.minute // 5 % 2 == 0


def test_a_step_at_each_bar_makes_its_round_once_and_a_restart_sends_nothing_twice(
    tmp_path: Path,
) -> None:
    desk, today = _desk(tmp_path)[0], MON.date()
    open_ = venues.hours("LSE", today).open
    kill.drill(tmp_path, open_)
    broker = Pretend({YARDSTICK: [Bar(today, *(Decimal(40),) * 4, 1)]}, {})
    broker.open(today)
    live = running.Desk(**{**desk.__dict__, "rules": {"flip": _Flip}})
    sent = []
    for minutes in (0, 5, 5, 10, 10, 15):  # the bar's close; a restart re-runs the same moment
        running._intraday(live, broker, "LSE", open_ + timedelta(minutes=minutes))  # type: ignore[arg-type]
        sent.append(book.positions(tmp_path).get("VUAG", 0))
    assert sent[0] == 0 and sent[1] == sent[2] > 0 and sent[3] == sent[4] == 0 and sent[5] > 0
    assert [f.order_id.split("-")[-1] for f in book.fills(tmp_path) if f.quantity != 0][:3] == [
        "0800B",
        "0805S",
        "0810B",
    ]
    assert len(running.notes(tmp_path)) == 3  # a bar that sent nothing leaves no note
    assert running._pending(tmp_path, open_, None, False) == []  # the look failed: no round
