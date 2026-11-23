"""The broker's history: a line's daily bars read as the gateway recorded them, only before the
day asked, refused in the broker's words, paced, and never asked in a desk round."""

from __future__ import annotations

import io
import re
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from desk import conformance_tape, history, live, paper
from desk.bars import Five
from desk.history import Busy
from desk.lines import LINES, POUND, Line
from desk.listing import Listing
from desk.rollup import Candle
from desk.store import Bar, Refused

VUAG = next(line for line in LINES if line.symbol == "VUAG")
IDTL = next(line for line in LINES if line.symbol == "IDTL")
AAPL = next(line for line in LINES if line.symbol == "AAPL")
#: As the real paper gateway answered VUAG on 16 November 2026 (six days of daily bars, the
#: last of them 13 November), the dates in its own form; the session of 16 November was open.
TAPE = "17|9001|20261106 01:00:00 MET|20261116 01:00:00 MET|3|20261112|110.7000|111.8400|110.2600|111.7800|36161|110.994|166|20261113|111.1200|111.6600|109.7400|110.2600|53638|110.947|161|20261116|110.5800|110.7600|109.5000|109.9400|32660|110.343|158"  # noqa: E501
NONE = "4|2|9001|200|No security definition has been found for the request"
EMPTY = "17|9001|20261106 01:00:00 MET|20261116 01:00:00 MET|0"
FEEDS = ("4|2|-1|2104|Market data farm connection is OK:eufarm", "9|1|7", "15|1|DU0000001")
DAY, SINCE = date(2026, 11, 16), date(2026, 11, 6)
MONDAY_NOON = datetime(2026, 11, 16, 12, 0, tzinfo=UTC)


def conversation(*answers: str) -> io.BytesIO:
    told = ["176|20261116 17:35:08 Greenwich Mean Time", *FEEDS, *answers]
    return io.BytesIO(b"".join(paper.message(*m.split("|")) for m in told))


def test_the_ask_names_the_line_the_day_before_and_the_trades() -> None:
    fields = history.request(VUAG, DAY, SINCE)[4:].decode().split("\0")[:-1]
    assert fields[:3] == ["20", "9001", "0"] and fields[3:5] == ["VUAG", "STK"]
    assert fields[9:12] == ["SMART", "LSEETF", "GBP"]
    assert fields[15:19] == ["20261116 00:00:00 UTC", "1 day", "10 D", "1"]
    assert fields[19] == "TRADES"
    deep = history.request(IDTL, DAY, date(2020, 1, 1)).decode()
    assert "7 Y" in deep and "USD" in deep
    assert history.request(AAPL, DAY, SINCE).decode().count("SMART") == 1
    for frame, size in history.SIZES.items():
        assert f"\0{size}\0" in history.request(VUAG, DAY, SINCE, frame).decode()
    with pytest.raises(KeyError):
        history.request(VUAG, DAY, SINCE, "3m")
    pair = history.request(POUND, DAY, SINCE)[4:].decode().split(chr(0))[:-1]
    assert pair[3:5] == ["GBP", "CASH"] and pair[9:12] == ["IDEALPRO", "", "USD"]
    assert pair[19] == "MIDPOINT"
    forex = conversation("17|9001|a|b|1|20261112|1.3|1.4|1.2|1.3|-1|1.3|-1")
    paper.start(forex, lambda _: None)
    got = history.ask(forex, lambda _: None, POUND, DAY, SINCE)
    assert not isinstance(got, Refused) and [b.volume for b in got if isinstance(b, Bar)] == [0]


def test_the_bars_are_those_from_since_and_before_the_day_asked() -> None:
    wire = conversation(TAPE)
    paper.start(wire, lambda _: None)
    got = history.ask(wire, lambda _: None, VUAG, DAY, SINCE)
    assert not isinstance(got, Refused)
    assert [bar.day for bar in got if isinstance(bar, Bar)] == [
        date(2026, 11, 12),
        date(2026, 11, 13),
    ]
    prices = [Decimal(p) for p in ("111.12", "111.66", "109.74", "110.26")]
    assert got[1] == Bar(date(2026, 11, 13), prices[0], prices[1], prices[2], prices[3], 53638)


def test_a_line_the_broker_will_not_give_is_refused_in_its_words() -> None:
    wire = conversation(NONE)
    paper.start(wire, lambda _: None)
    got = history.ask(wire, lambda _: None, VUAG, DAY, SINCE)
    assert got == Refused("the broker's 200: No security definition has been found for the request")


def test_a_count_that_does_not_fit_the_bars_is_refused_loudly() -> None:
    wire = conversation(TAPE.replace("|3|", "|4|"))
    paper.start(wire, lambda _: None)
    with pytest.raises(ValueError, match="shape the desk does not read"):
        history.ask(wire, lambda _: None, VUAG, DAY, SINCE)


def test_each_line_is_asked_as_its_own_client_paced_apart(monkeypatch: pytest.MonkeyPatch) -> None:
    waits: list[float] = []
    wire = conversation(TAPE, NONE)
    monkeypatch.setattr(paper, "dial", lambda talk: talk(wire, lambda _: None))
    got = history.gather((VUAG, IDTL), DAY, SINCE, MONDAY_NOON, waits.append)
    assert waits == [history.PACING] and history.CLIENT == 225
    assert isinstance(got[IDTL], Refused) and got[VUAG] != got[IDTL]


def test_nothing_is_asked_in_a_desk_round(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(conformance_tape, "ROUNDS", ((time(9, 0), time(9, 30)),))
    moment = datetime(2026, 11, 16, 9, 10, tzinfo=UTC)
    with pytest.raises(Busy, match="09:00-09:30"):
        history.gather((VUAG,), DAY, SINCE, moment)
    assert history.quiet(datetime(2026, 11, 16, 8, 10, tzinfo=UTC))
    monkeypatch.undo()
    monkeypatch.setattr(paper, "dial", lambda _: pytest.fail("dialled in a desk round"))
    for hour, minute in ((8, 0), (8, 29), (14, 30), (14, 59)):
        with pytest.raises(Busy):
            history.gather((VUAG,), DAY, SINCE, datetime(2026, 11, 16, hour, minute, tzinfo=UTC))
    assert history.quiet(datetime(2026, 11, 16, 8, 30, tzinfo=UTC))


def test_a_pull_fills_the_gaps_only_paced_and_resumes_after_a_stop() -> None:
    done: set[history.Ask] = {(VUAG, "1d")}
    waits: list[float] = []
    asked: list[history.Ask] = []

    def fetch(line: Line, frame: str) -> Refused:
        asked.append((line, frame))
        return Refused("none")

    def keep(line: Line, frame: str, _: object) -> None:
        done.add((line, frame))

    everything = len(history.PULLED) * 2
    first = history.plan((VUAG, IDTL), done)
    assert not {f for _, f in first} & {"1h", "4h", "1wk"}  # rolled up locally, not asked
    assert len(first) == everything - 1 and (VUAG, "1d") not in first
    assert history.pull(first, fetch, keep, waits.append, limit=4) == 4
    assert waits == [history.PACING] * 3 and len(done) == 5
    rest = history.plan((VUAG, IDTL), done)
    assert history.pull(rest, fetch, keep, waits.append) == everything - 5
    assert len(set(asked)) == len(asked) == everything - 1 and not history.plan((VUAG, IDTL), done)


def test_a_run_asks_each_timeframe_over_one_conversation_and_not_in_a_round(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    kept: dict[history.Ask, object] = {}
    sent: list[bytes] = []
    wire = conversation(TAPE, EMPTY, NONE)
    monkeypatch.setattr(paper, "dial", lambda talk: talk(wire, sent.append))
    asks = [(VUAG, "1d"), (VUAG, "1wk")]
    keep = lambda line, frame, got: kept.update({(line, frame): got})  # noqa: E731
    assert history.run(asks, keep, DAY, MONDAY_NOON, lambda _: None) == 2
    assert (
        history.REACH.keys() == history.SIZES.keys() and "\0" + "365 D" + "\0" in sent[-1].decode()
    )
    first_page = kept[(VUAG, "1d")]
    assert isinstance(first_page, tuple) and len(first_page) == 2  # the second page was empty
    assert isinstance(kept[(VUAG, "1wk")], Refused) and "\0" + "1 week" + "\0" in sent[-1].decode()
    stamp = int(datetime(2026, 11, 12, 9, 30, tzinfo=UTC).timestamp())
    timed = conversation(TAPE.replace("20261112", str(stamp)))
    paper.start(timed, lambda _: None)
    got = history.ask(timed, sent.append, VUAG, DAY, SINCE, "5m")
    first = datetime(2026, 11, 12, 9, 30, tzinfo=UTC)
    prices = [Decimal(p) for p in ("110.70", "111.84", "110.26", "111.78")]
    assert isinstance(got, tuple) and got[0] == Candle(
        first, prices[0], prices[1], prices[2], prices[3], 36161, "ibkr"
    )
    assert "\0" + "5 mins" + "\0" in sent[-1].decode() and b"TRADES\0" + b"2\0" in sent[-1]
    odd = conversation(TAPE.replace("20261112", "20261112 09:30:00"))
    paper.start(odd, lambda _: None)
    with pytest.raises(ValueError, match="no epoch seconds"):
        history.ask(odd, sent.append, VUAG, DAY, SINCE, "5m")
    with pytest.raises(Busy):
        history.run(asks, keep, DAY, datetime(2026, 11, 16, 8, 0, tzinfo=UTC))


def test_a_pull_and_a_live_round_in_one_process_each_start_as_their_own_client(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    sent: list[bytes] = []
    five = Five(MONDAY_NOON, *(Decimal(1),) * 4, 1)
    pence = Listing(VUAG, "1", "LSE", 1, ((Decimal(0), Decimal("0.5")),))

    def newest(_l: Line, _c: str, _r: str, _n: int, door: paper.Door) -> tuple[Five, ...]:
        paper.start(conversation(), sent.append, door)
        return (five,)

    monkeypatch.setattr(paper, "dial", lambda talk: talk(conversation(TAPE), sent.append))
    ask = live.ibkr(tmp_path, lambda _: None, newest, lambda *_: {"VUAG": pence})
    for first in (history, live):  # both orders
        sent.clear()
        for one in (first, live if first is history else history):
            if one is history:
                history.gather((VUAG,), DAY, SINCE, MONDAY_NOON, lambda _: None)
            else:
                ask(VUAG, MONDAY_NOON + timedelta(minutes=5))
        ids = [m[4:].decode().split("\0")[2] for m in sent if m[4:6] == b"71"]
        assert ids == [str(first.CLIENT), str(live.CLIENT if first is history else history.CLIENT)]
    modules = [
        (Path(__file__).parents[2] / "desk" / f"{n}.py").read_text("utf-8")
        for n in ("history", "live")
    ]
    assert not any(re.search(r"paper\.(CLIENT|APART)\s*=", text) for text in modules)


def test_a_walk_back_pages_before_each_page_until_one_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: list[bytes] = []
    waits: list[float] = []
    wire = conversation(TAPE, TAPE.replace("202611", "202501"), EMPTY)
    monkeypatch.setattr(paper, "dial", lambda talk: talk(wire, sent.append))
    kept: list[object] = []
    keep = lambda _l, _f, got: kept.append(got)  # noqa: E731
    assert history.run([(VUAG, "1d")], keep, DAY, MONDAY_NOON, waits.append) == 1
    ends = [re.search(r"\d{8} 00:00:00 UTC", m.decode()) for m in sent if b"UTC" in m]
    assert [e.group()[:8] if e else "" for e in ends] == ["20261116", "20251116", "20241116"]
    assert waits == [history.PACING] * 2 and len(kept[0]) == 5  # type: ignore[arg-type]
