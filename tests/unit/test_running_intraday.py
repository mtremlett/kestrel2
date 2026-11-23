"""The step's intraday round (R-RUNNER-202): at each five-minute bar the rule's round is made
once, a restart mid-session sends nothing twice, and with no rule the day is unchanged."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import ClassVar

import pytest
from test_running import MON, _desk

from desk import book, command, handpark, intraday, kill, running, venues
from desk.broker import Pretend
from desk.intraday import Span
from desk.lines import YARDSTICK
from desk.orders import is_zoo
from desk.rollup import Candle
from desk.store import Bar
from desk.strategy import Action


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


def test_the_zoo_is_off_by_default_and_trades_one_share_labelled_only_behind_its_switch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (desk, post), today = _desk(tmp_path), MON.date()
    assert not desk.zoo and not command._desk(tmp_path, desk.post, tmp_path).zoo  # OFF by default
    (tmp_path / running.ZOO_ON).touch()
    assert command._desk(tmp_path, desk.post, tmp_path).zoo  # the one paper switch turns it on
    open_ = venues.hours("LSE", today).open
    kill.drill(tmp_path, open_)
    broker = Pretend({YARDSTICK: [Bar(today, *(Decimal(40),) * 4, 1)]}, {})
    broker.open(today)
    assert len(intraday.ZOO_RULES) == 7 and all(is_zoo(f"d-{n}-L") for n in intraday.ZOO_RULES)
    monkeypatch.setattr(intraday, "ZOO_RULES", {"zoo_flip": _Flip})
    running._intraday(desk, broker, "LSE", open_ + timedelta(minutes=5))  # type: ignore[arg-type]
    assert book.positions(tmp_path).get("VUAG", 0) == 0  # switch off: the zoo sends nothing
    zoo, parked = replace(desk, zoo=True), tmp_path / handpark.FILE
    parked.write_text("symbol,who,why\nVUAG,him,a test\n", encoding="utf-8")
    running._intraday(zoo, broker, "LSE", open_ + timedelta(minutes=5))  # type: ignore[arg-type]
    assert "parked by hand" in running.notes(tmp_path)[-1].words  # the daily buy's refusals
    parked.unlink()
    running._intraday(zoo, broker, "LSE", open_ + timedelta(minutes=5))  # type: ignore[arg-type]
    assert book.positions(tmp_path)["VUAG"] == 1  # tiny: one share, through the one gate
    assert [f.order_id for f in book.fills(tmp_path)][0].split("-")[1] == "zoo_flip"
    assert running.MACHINERY in running.notes(tmp_path)[-1].words
    later = open_ + timedelta(minutes=6)  # his waking hours: each note of the day is told...
    running._say(zoo, later, running.UNASKED)
    assert not any("zoo_flip" in str(call) for call in post.call_args_list)  # ...not the zoo's
    assert "1 of 2 orders filled" in running.zoo_hour(tmp_path, later)  # it is the hour's line


@pytest.mark.parametrize(
    ("line", "held", "words"),
    [
        (replace(YARDSTICK, isa=False), {}, "ISA"),
        (replace(YARDSTICK, retail=False), {}, "retail"),
        (YARDSTICK, {"VUAG": 3}, "held already"),
    ],
)
def test_an_intraday_buy_gets_the_daily_buys_refusals(
    tmp_path: Path, line: object, held: dict[str, int], words: str
) -> None:
    desk, at = _desk(tmp_path)[0], venues.hours("LSE", MON.date()).open
    buy = intraday.IntradayDecision("flip", "VUAG", at, Action.BUY)
    said = running._order(desk, desk.room, buy, line, "id", Decimal(40), held)  # type: ignore[arg-type]
    assert isinstance(said, str) and "not sent" in said and words in said
