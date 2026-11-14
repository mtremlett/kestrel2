"""The conformance trades as a command: the run's orders, the run at the pretend broker word
for word, a step that fails, the real stop put above the market, and the command's gates, with
the archive, the Gateway and the paper broker played at their own doors."""

from __future__ import annotations

import csv
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from test_reports import CENT

from desk import archive, book, clearance, command, conformance, listing, paper, placing
from desk.broker import Fault, Fill, Pretend
from desk.lines import LINES, Line
from desk.listing import Listing, Unlisted
from desk.orders import Order, Sale
from desk.store import Bar

MON, FRI = datetime(2026, 11, 16, 8, 5, tzinfo=UTC), date(2026, 11, 13)
ISF, VUAG, SPY = (next(x for x in LINES if x.symbol == s) for s in ("ISF", "VUAG", "SPY"))
FX = {"GBP": Decimal(1), "USD": Decimal("0.8")}
#: Friday's close and shares traded: VUAG traded the most money, 44 million pounds to ISF's 30
LAST = {"ISF": (10, 3_000_000), "VUAG": (110, 400_000), "SPY": (750, 9)}
LISTED: dict[str, Listing | Unlisted] = {
    "3LGO": Listing(LINES[0], "1", "LSEETF", 1, CENT),  # leveraged: never the run's line
    "ISF": Listing(ISF, "2", "LSEETF", 1, CENT),
    "VUAG": Listing(VUAG, "3", "LSEETF", 100, CENT),  # priced in pence at the broker
    "SPY": Listing(SPY, "4", "ARCA", 1, CENT),
}
ID, NO = "20261113-conf{}lse-VUAG", "20261113-conf0lse-SPY"
NONE = "fills: none; held: none; stops: none"
PRETEND = {
    "a rejection": f"{NO}: 0 of 1 shares done ({NO}: rejected by the broker); {NONE}",
    "a market buy at the open, its stop resting": f"{ID.format(1)}: 1 of 1 shares done; fills: "
    f"{ID.format(1)} +1 at 110; held: VUAG 1; stops: VUAG 1",
    "a sale, the stop cancelled": f"{ID.format(2)}: 1 of 1 shares done; fills: "
    f"{ID.format(2)} -1 at 110; held: none; stops: none",
    "a buy of the desk's size, a part fill if given": f"{ID.format(3)}: 18 of 18 shares done; "
    f"fills: {ID.format(3)} +18 at 110; held: VUAG 18; stops: VUAG 18",
    "the stop triggered": f"done; fills: {ID.format(3)}-stop -18 at 99.00; held: none; stops: none",
    "the account left as found": f"nothing to put back; {NONE}",
}


@pytest.fixture(autouse=True)
def _the_desks_own_client_again(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(paper, "CLIENT", paper.CLIENT)  # the command makes it its own: put back


def _fetch(line: Line, before: date) -> tuple[Bar, ...]:
    close, traded = LAST.get(line.symbol, (50, 1))
    return (Bar(FRI, *(Decimal(close),) * 4, traded),) if before > FRI else ()


def _plan(patch: pytest.MonkeyPatch) -> conformance.Plan:
    patch.setattr(archive, "fetch", _fetch)
    return conformance.plan([ISF, VUAG], SPY, MON.date(), FX)


def _market(run: conformance.Plan, *lines: Line, reject: bool = True) -> Pretend:
    """A broker at the paper broker's door: today's market in the lines given, at Friday's
    closes, and tomorrow's, which falls a tenth; SPY refused, or not."""
    bars = {}
    for line in lines:
        at = Decimal(LAST[line.symbol][0])
        fallen = Bar(run.today + timedelta(days=1), at, at, at * Decimal("0.9"), at, 0)
        bars[line] = (Bar(run.today, at, at, at, at, 0), fallen)
    broker = Pretend(bars, {"SPY": Fault.REJECT} if reject and SPY in lines else {})
    broker.open(run.today)
    return broker


def test_the_runs_orders_are_on_the_line_that_traded_most_sized_by_the_desk_dated_the_day_before(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = _plan(monkeypatch)
    assert run.first == Order(ID.format(1), VUAG, 1, Decimal(110), Decimal(1), Decimal(99))
    assert run.sale == Sale(ID.format(2), VUAG, 1)
    # a fifth of the desk's 10,000 pounds: 18 shares at 110 and the broker's 3 pounds
    assert run.second == Order(ID.format(3), VUAG, 18, Decimal(110), Decimal(1), Decimal(99))
    assert run.refusal == Order(NO, SPY, 1, Decimal(750), FX["USD"], Decimal(675))
    with pytest.raises(ValueError, match="no plain line"):
        conformance.plan([], SPY, MON.date(), FX)
    with pytest.raises(ValueError, match="VUAG: the archive has no bar of 2026-11-16"):
        conformance.plan([VUAG], SPY, MON.date() + timedelta(days=1), FX)  # Tuesday: Monday's


def test_the_run_at_the_pretend_broker_word_for_word(monkeypatch: pytest.MonkeyPatch) -> None:
    assert conformance.pretend(_plan(monkeypatch)) == PRETEND


def test_a_step_that_fails_is_named_and_the_account_is_still_put_back(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # the broker does not refuse SPY, and the stop put above the market never sells: the run
    # says so, and its last step sells both lines
    run, said = _plan(monkeypatch), dict[str, str]()
    broker = _market(run, VUAG, SPY, reject=False)

    def stuck(order: Order) -> None:
        raise TimeoutError(f"{order.order_id}-stop: it has not sold")

    side = conformance.Side(tmp_path, broker, lambda: (), stuck)
    assert conformance.live(side, run, said.__setitem__) == ["the stop triggered"]
    assert said["a rejection"].startswith(f"{NO}: 1 of 1 shares done; fills")
    assert (
        said["the stop triggered"] == f"FAILED, TimeoutError: {ID.format(3)}-stop: it has not sold"
    )
    assert said["the account left as found"] == (
        f"20261113-conf9lse-SPY: 1 of 1 shares done; {ID.format(9)}: 18 of 18 shares done; fills: "
        f"20261113-conf9lse-SPY -1 at 750, {ID.format(9)} -18 at 110; held: none; stops: none"
    )
    assert (broker.holdings(), broker.stops(), book.positions(tmp_path)) == ((), (), {})


def test_no_order_goes_while_the_check_names_anything_and_after_a_step_fails_only_the_last_is_tried(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    run, said = _plan(monkeypatch), dict[str, str]()
    broker, last = _market(run, VUAG, SPY), "the account left as found"
    side = conformance.Side(tmp_path, broker, lambda: ("ISF: held by a hand",), lambda _: None)
    assert conformance.live(side, run, said.__setitem__) == ["a rejection", last]
    named = "not sent, the day's check named: ISF: held by a hand"
    assert said["a rejection"] == f"FAILED, Refused: {NO}: {named}"
    assert {said[step] for step in list(said)[1:-1]} == {conformance.UNTRIED}
    assert said[last].startswith("FAILED, ValueError: the account is not as found: the book holds")
    assert "ISF: held by a hand" in said[last] and broker.submitted() == ()


def test_the_real_stop_is_put_above_the_price_paid_and_sold_or_not_the_line_is_left_under_its_own(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    listed, run = LISTED["VUAG"], _plan(monkeypatch)
    assert isinstance(listed, Listing)
    paid = Fill("0001", ID.format(3), "VUAG", 18, Decimal("110.004"), MON.date())
    book._record(tmp_path, [paid])
    held, gone = (
        paper.Account((paper.Holding("DU1", "VUAG", "STK", "GBP", Decimal(18)),), ()),
        paper.Account((), ()),
    )
    reads, settled, waited = iter([held, held, gone, gone]), list[object](), list[float]()
    monkeypatch.setattr(paper, "read", lambda: next(reads))
    monkeypatch.setattr(placing.Paper, "settle", lambda _, *asked: settled.append(asked))
    adapter = placing.Paper(LISTED, tmp_path, lambda: MON)
    fall = conformance._raised(adapter, tmp_path, listed, waited.append)
    fall(run.second)
    # 110.004 and a twentieth, down onto the broker's step, in the broker's pence; once it has
    # sold nothing is held, and the line is left under no stop
    name = f"{ID.format(3)}-stop"
    above: tuple[object, ...] = (
        listed,
        Decimal(18),
        [],
        placing.Stop(Decimal(18), Decimal("11550.00"), name),
    )
    assert (settled, waited) == ([above, (listed, Decimal(0), [], None)], [1])
    monkeypatch.setattr(
        paper, "read", lambda: held
    )  # it never sells: back under the buy's own stop
    with pytest.raises(TimeoutError, match="has not sold in 30 seconds"):
        fall(run.second)
    assert len(waited) == 1 + conformance.WAITS
    assert settled[2:] == [
        above,
        (listed, Decimal(18), [], placing.Stop(Decimal(18), Decimal(9900), name)),
    ]
    reads = iter([held, gone, gone])  # the broker ends the raised stop as it is sent: it sold

    def ended(_: object, *asked: object) -> None:
        settled.append(asked)
        if len(settled) == 5:
            raise placing.Unprotected("the broker ended the stop, Filled")

    monkeypatch.setattr(paper, "read", lambda: next(reads))
    monkeypatch.setattr(placing.Paper, "settle", ended)
    fall(run.second)
    assert settled[4:] == [above, (listed, Decimal(0), [], None)]
    monkeypatch.setattr(paper, "read", lambda: gone)  # the buy bought nothing: nothing is sent
    with pytest.raises(ValueError, match="no share of it is held"):
        fall(run.second)
    assert len(settled) == 6


def _world(patch: pytest.MonkeyPatch, found: tuple[str, ...] = (), sells: bool = True) -> Pretend:
    """The archive, a Gateway that greets, a check that names what is given, and the pretend
    broker at the paper broker's door, its stop selling when the market is made to reach it."""
    broker = _market(_plan(patch), VUAG, SPY)

    def fall(order: Order) -> None:
        if not sells:
            raise TimeoutError(f"{order.order_id}-stop: it has not sold")
        broker.open(MON.date() + timedelta(days=1))

    patch.setattr(command, "rates", lambda _root, _day: FX)
    patch.setattr(paper, "dial", lambda _talk: None)
    patch.setattr(listing, "read", lambda _lines: LISTED)
    patch.setattr(clearance, "check", lambda _root, now: clearance.Check(now, found))
    patch.setattr(placing, "Paper", lambda _listings, _root, _clock: broker)
    patch.setattr(conformance, "_raised", lambda *_: fall)
    return broker


def _run(root: Path, now: datetime, market: str) -> int:
    return conformance.main(["--conformance", market], {"KESTREL2_DATA": str(root)}, lambda: now)


def _never(_talk: object) -> None:
    raise AssertionError("the Gateway was dialled")


def test_the_command_records_each_real_result_beside_the_pretend_brokers_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _world(monkeypatch)
    assert _run(tmp_path, MON, "london") == 0
    record = tmp_path / "conformance" / "trades-london-20261116.csv"
    assert f"6 of 6 steps done on VUAG, each recorded beside the pretend broker's in {record}." in (
        capsys.readouterr().out
    )
    with record.open(newline="", encoding="utf-8") as kept:
        head, *rows = csv.reader(kept)
    assert head == list(conformance.HEAD)
    assert [row[1:] for row in rows[:-1]] == [[step, said, said] for step, said in PRETEND.items()]
    assert rows[-1] == [MON.isoformat(), "the run", "whole", ""]
    assert paper.CLIENT == conformance.CLIENT == 223  # a client of its own, never the desk's 222
    assert book.switch(record.parent)[-1][:2] == (MON, book.Switch.DRILLED)  # the day's own drill
    monkeypatch.setattr(paper, "dial", _never)  # recorded whole: never again, and nothing asked
    assert _run(tmp_path, MON + timedelta(days=1), "london") == 0
    assert _run(tmp_path, MON, "us") == 0  # New York is shut at 08:05
    assert _run(tmp_path, MON.replace(hour=16, minute=30), "london") == 0  # the closing auction
    said = capsys.readouterr().out.splitlines()
    assert f"nothing done, its run is already recorded in {record}." in said[0]
    assert ["New York is shut" in said[1], "London is shut" in said[2]] == [True, True]
    with pytest.raises(SystemExit, match="--conformance london|us"):
        _run(tmp_path, MON, "paris")


def test_nothing_is_sent_unless_the_gateway_is_ready_the_switch_off_and_the_account_quiet(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "conformance"
    broker = _world(monkeypatch, found=("AAPL: the broker holds 5, the desk's book 0",))
    assert _run(tmp_path, MON, "london") == 1
    for desk in (root, tmp_path / "desk"):  # its own kill switch, and the desk's
        book.turn(desk, book.Switch.ON, MON, "his hand")
        assert _run(tmp_path, MON, "london") == 1
        book.turn(desk, book.Switch.OFF, MON, "his hand")
    monkeypatch.setattr(paper, "dial", lambda _talk: (_ for _ in ()).throw(ConnectionRefusedError))
    assert _run(tmp_path, MON, "london") == 1
    quiet, killed, desks, closed = capsys.readouterr().out.splitlines()
    assert (
        "NOT BEGUN, nothing sent: the paper account is not quiet: AAPL: the broker holds 5" in quiet
    )
    assert [
        "NOT BEGUN, nothing sent: the kill switch is on" in said for said in (killed, desks)
    ] == [True] * 2
    assert "NOT BEGUN, nothing sent: " in closed and "its port is closed" in closed
    assert (broker.submitted(), list(root.glob("trades-*"))) == ((), [])


def test_a_run_that_failed_is_code_1_and_recorded_and_tried_again_only_on_a_later_day(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    broker = _world(monkeypatch, sells=False)
    assert _run(tmp_path, MON, "london") == 1
    assert "5 of 6 steps done on VUAG" in (said := capsys.readouterr().out)
    assert "FAILED: the stop triggered. A later day tries again" in said
    root, sent = tmp_path / "conformance", broker.submitted()
    with (root / "trades-london-20261116.csv").open(newline="", encoding="utf-8") as kept:
        assert list(csv.reader(kept))[-1][1:3] == ["the run", "FAILED, at: the stop triggered"]
    assert _run(tmp_path, MON, "london") == 0 and broker.submitted() == sent  # today's is recorded
    assert conformance._recorded(root, "london", MON.date() + timedelta(days=1)) is None
    (root / "trades-london-20261115.csv").write_text("not,a,record\n", encoding="utf-8")
    with pytest.raises(ValueError, match="not a record of the conformance trades"):
        _run(tmp_path, MON, "london")


def test_whatever_stops_a_run_outside_its_steps_the_account_is_still_put_back(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    broker, live = _world(monkeypatch), conformance.live

    def dies(
        side: conformance.Side, run: conformance.Plan, note: Callable[[str, str], None]
    ) -> list[str]:
        if side.broker is not broker:
            return live(side, run, note)  # the pretend broker's run, made first
        conformance._send(side, run.second)
        raise OSError("the record's disk")

    monkeypatch.setattr(conformance, "live", dies)
    with pytest.raises(OSError, match="the record's disk"):
        _run(tmp_path, MON, "london")
    assert (broker.submitted()[-1], broker.holdings()) == (ID.format(9), ())
