"""The day's check, and no order without it: the desk's own resting stops told from anyone
else's orders, every difference from the desk's book named, each check kept on a dated
record, and an order refused unless today's newest check came back clean."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from test_paper import AAPL_STOP
from test_reports import AAPL, IITU, LISTED, OURS

from desk import book, clearance, listing, paper
from desk.clearance import Check
from desk.lines import LINES
from desk.orders import Refused
from desk.paper import Account, Holding

TEN = Holding("DU0000001", "AAPL", "STK", "USD", Decimal(10))
QUIET, BARE = Account((), ()), Account((TEN,), ())
NOW = datetime(2026, 11, 16, 7, 5, tzinfo=UTC)
HEAD, AT = "at,result,found\n", NOW.isoformat()
HOLDS = "AAPL STK USD: the broker holds {}, the desk's book {}"
STOP = "AAPL: the desk's own stop resting at the broker is for {}, the desk's book {}"
ORDER = "AAPL: an order resting at the broker to {} 10 ({}, the broker's id {}, client {}), {}"
THEIRS = ORDER.format("SELL", "STP, PreSubmitted", "1234567", 31, "not the desk's own")
IDLE = "the desk's own, and no stop the broker is holding"
TWO = "10 in one of 2 entries"
WORKS = ORDER.format("BUY", "MKT, Submitted", 8, 222, IDLE)
BUYING = replace(OURS, broker_id="8", action="BUY", kind="MKT", state="Submitted")


def test_a_line_held_under_the_desks_own_stop_for_exactly_its_shares_is_no_difference() -> None:
    assert clearance.differences(Account((TEN,), (OURS,)), LISTED, {"AAPL": 10}, (AAPL, IITU)) == ()
    assert clearance.differences(QUIET, LISTED, {}, (AAPL, IITU)) == ()
    with pytest.raises(ValueError, match="999"):  # the desk's own, on no line of the desk's
        clearance.differences(Account((), (replace(OURS, contract="999"),)), LISTED, {}, (AAPL,))


@pytest.mark.parametrize(
    ("orders", "held", "named"),
    [
        ((), 10, (STOP.format(0, 10),)),  # held, and under no stop
        ((replace(OURS, state="Submitted", left=Decimal(4)),), 10, (STOP.format(4, 10),)),
        # two stops are never the book's one line, though each is for the book's shares
        ((OURS, replace(OURS, broker_id="8")), 10, (STOP.format(TWO, 10), STOP.format(TWO, 10))),
        ((OURS,), 0, (HOLDS.format(10, 0), STOP.format(10, 0))),  # a stop for shares the book lacks
        # anyone else's stop protects nothing of the desk's, and is named as theirs
        ((AAPL_STOP,), 10, (STOP.format(0, 10), THEIRS)),
        ((OURS, AAPL_STOP), 10, (THEIRS,)),
        # the desk's own, but refused or still to fill: no protection, and named
        (
            (replace(OURS, state="Inactive", left=Decimal(0)),),
            10,
            (STOP.format(0, 10), ORDER.format("SELL", "STP, Inactive", "1234567", 222, IDLE)),
        ),
        ((AAPL_STOP, BUYING, OURS), 10, (WORKS, THEIRS)),
    ],
)
def test_every_stop_and_order_that_is_not_the_books_is_named_holdings_first(
    orders: tuple[paper.Resting, ...], held: int, named: tuple[str, ...]
) -> None:
    book_ = {"AAPL": held} if held else {}
    assert clearance.differences(Account((TEN,), orders), LISTED, book_, (AAPL, IITU)) == named


def _check(patch: pytest.MonkeyPatch, root: Path, at: datetime, account: Account) -> Check:
    """The day's check at a moment: the door lists the desk's lines, then gives the account,
    the newest thing read."""
    answers = iter((LISTED, account))
    patch.setattr(listing, "read", lambda lines: next(answers) if lines is LINES else {})
    patch.setattr(paper, "read", lambda: next(answers))
    return clearance.check(root, at)


def test_no_order_until_todays_newest_check_came_back_clean(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    hours = [NOW + timedelta(hours=n) for n in range(5)]
    with pytest.raises(Refused, match="o-1: not sent, .*not been checked today"):
        clearance.require(tmp_path, NOW, "o-1")
    assert _check(monkeypatch, tmp_path, NOW, QUIET) == Check(NOW, ())
    clearance.require(tmp_path, NOW, "o-1")
    clearance.require(tmp_path, NOW.replace(hour=23, minute=59), "o-1")  # all of that day
    for other in (NOW + timedelta(days=1), NOW.replace(hour=0, minute=0) - timedelta(minutes=1)):
        with pytest.raises(Refused, match="not been checked today"):  # no other day's
            clearance.require(tmp_path, other, "o-1")
    # a later check that names anything takes the day's clearance away
    found = _check(monkeypatch, tmp_path, hours[1], BARE)
    assert found == Check(hours[1], (HOLDS.format(10, 0),))
    with pytest.raises(Refused, match="o-2: not sent, .*08:05 UTC.*the broker holds 10"):
        clearance.require(tmp_path, hours[2], "o-2")
    # and so does one whose reading stopped: it has not come back, and is never a clean one
    monkeypatch.setattr(listing, "read", lambda _: LISTED)
    monkeypatch.setattr(paper, "read", lambda: paper.only("U7654321"))
    with pytest.raises(paper.NotPaper):
        clearance.check(tmp_path, hours[2])
    with pytest.raises(Refused, match="o-3: not sent, .*09:05 UTC.*not come back"):
        clearance.require(tmp_path, hours[3], "o-3")
    assert clearance.checks(tmp_path) == (Check(NOW, ()), found, Check(hours[2], None))
    with pytest.raises(ValueError, match="before"):  # a clock gone back is no newer check
        _check(monkeypatch, tmp_path, hours[1], QUIET)
    _check(monkeypatch, tmp_path, hours[3], QUIET)
    clearance.require(tmp_path, hours[4], "o-3")
    assert len(clearance.checks(tmp_path)) == 4, "every check is kept, none written over"


def test_the_check_reads_the_desks_own_ledger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rows = (",".join(book.COLUMNS), "X1,20261113-rsi2-AAPL,AAPL,10,171.5,2026-11-13")
    (tmp_path / book.LEDGER).write_text("\n".join(rows), encoding="utf-8")
    assert _check(monkeypatch, tmp_path, NOW, Account((TEN,), (OURS,))).found == ()
    later = NOW + timedelta(hours=1)
    gone = (HOLDS.format(0, 10), STOP.format(0, 10))
    assert _check(monkeypatch, tmp_path, later, QUIET).found == gone


@pytest.mark.parametrize(
    "record",
    [
        "",
        "at,result\n",
        HEAD + "\n",
        HEAD + AT + "\n",
        HEAD + AT + ",quiet\n",
        HEAD + AT + ",clean,AAPL: something found\n",  # clean, yet it names something
        HEAD + AT + ",differs\n",  # differs, and names nothing
        HEAD + AT + ",begun,\n",
        HEAD + AT + ",clean\n" + AT + ",Clean\n",
        HEAD + "2026-11-16T07:05:00,clean\n",  # a moment on no clock
        HEAD + "2026-11-16T08:05:00+01:00,clean\n",
        HEAD + "2026-11-16 07:05:00+00:00,clean\n",  # not as the desk writes a moment
    ],
)
def test_a_record_that_cannot_be_read_whole_is_an_error_never_a_clean_day(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, record: str
) -> None:
    (tmp_path / clearance.CHECKS).write_text(record, encoding="utf-8")
    with pytest.raises(ValueError, match="checks.csv"):
        clearance.require(tmp_path, NOW, "o-1")
    with pytest.raises(ValueError, match="checks.csv"):  # and no check is written over it
        _check(monkeypatch, tmp_path, NOW, QUIET)
    assert (tmp_path / clearance.CHECKS).read_text(encoding="utf-8") == record


def test_a_moment_not_in_utc_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for moment in (NOW.replace(tzinfo=None), NOW.astimezone(timezone(timedelta(hours=1)))):
        with pytest.raises(ValueError, match="UTC"):
            clearance.require(tmp_path, moment, "o-1")
        with pytest.raises(ValueError, match="UTC"):
            _check(monkeypatch, tmp_path, moment, QUIET)
    assert clearance.checks(tmp_path) == ()
