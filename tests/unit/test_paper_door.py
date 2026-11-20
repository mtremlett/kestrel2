"""paper: a Door is who a conversation with the gateway is, built by each caller and passed
down, so two doors in one process never see each other's orders (R-RUNNER-258)."""

from __future__ import annotations

import re
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from test_reports import LISTED, OURS

from desk import book, paper, placing
from desk.broker import Disconnected
from desk.listing import Listing
from desk.orders import Sale

#: the paper lane's modules but paper itself, which alone still reads them for the data lane
PAPER_LANE = (
    "placing placing_parts conformance conformance_parts reports ended listing gateway "
    "clearance running command"
).split()


def test_two_doors_in_one_process_each_see_only_their_own_orders_and_stops_in_either_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    desk, run = paper.Door(paper.DESK), paper.Door(223, paper.Apart(frozenset()))
    theirs = replace(OURS, broker_id="8", client="223", contract="212969319", symbol="IITU")
    theirs = replace(theirs, ref="conf1-stop", left=Decimal(3))
    account = paper.Account((), (OURS, theirs))
    monkeypatch.setattr(paper, "dial", lambda _talk: account)
    at, own = datetime(2026, 11, 16, 8, 5, tzinfo=UTC), {222: OURS, 223: theirs}
    for order in ((desk, run, desk), (run, desk, run)):  # a run then a restop, and the reverse
        for door in order:
            broker = placing.Paper(LISTED, Path("unread"), lambda: at, door)
            listed = LISTED[own[door.client].symbol]
            assert isinstance(listed, Listing)
            held, stops = placing.on(paper.read(door), listed, door)
            assert stops == [own[door.client]] and held == 0
            assert broker.stops() == ((own[door.client].symbol, own[door.client].left),)


def test_no_paper_lane_module_reads_the_modules_client_or_apart() -> None:
    reads = re.compile(r"paper\.(CLIENT|APART)\b|from desk\.paper import .*\b(CLIENT|APART)\b")
    for name in PAPER_LANE:
        text = (Path(__file__).parents[2] / "desk" / f"{name}.py").read_text(encoding="utf-8")
        assert not reads.search(text), f"desk/{name}.py reads paper.CLIENT or paper.APART"


def test_link_news_after_an_order_is_unknown_not_a_fault_and_the_kill_switch_stays_off(
    tmp_path: Path,
) -> None:
    class Lost:
        def place(self, _order: object) -> None:
            paper.other(["4", "2", "-1", "2157", "Sec-def data farm connection is broken", ""])

    with pytest.raises(Disconnected, match="2157"):
        book._place(tmp_path, Lost(), Sale("a-1", LISTED["IITU"], 1), None)  # type: ignore[arg-type]
    assert book.killed(tmp_path) is None and (tmp_path / book.GOING).exists()
