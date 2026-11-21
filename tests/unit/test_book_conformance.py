"""The conformance cost (R-RUNNER-214): trades on the shared paper account are a kind of their
own, so the broker's cash is the book's to the penny and the desk's own dealing is unchanged."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from desk import book
from desk.broker import Fill
from desk.lines import Line

A, DAY = Line("A", "LSE", "GBP", 1), date(2025, 11, 10)


def _keep(root: Path, *fills: Fill) -> None:
    book.record_rates(root, DAY, {"GBP": Decimal(1)})
    book.keep(root / book.LEDGER, [book.COLUMNS, *(tuple(vars(f).values()) for f in fills)])


def test_a_conformance_round_trip_moves_cash_but_not_the_desks_dealing(tmp_path: Path) -> None:
    desk, conformance = tmp_path / "desk", tmp_path / "conformance"
    _keep(desk, Fill("e1", "o-1", "A", 10, Decimal(50), DAY))
    _keep(
        conformance,
        Fill("c1", "c-1", "A", 1, Decimal(40), DAY),
        Fill("c2", "c-2", "A", -1, Decimal(41), DAY),
    )
    cash, costs = book.dealt(desk, (A,), DAY, date.min, 0)
    cost = book.conformance_cost(conformance, (A,))
    assert cash == -500 and costs.total > 0, "the desk's own dealing, without the conformance"
    assert cost == Decimal("-5.0810"), "the shilling gained, less both legs' costs"
    assert 1000 + cash - costs.total + cost == Decimal(
        "491.4190"
    ), "the broker's cash, to the penny"


def test_a_rehearsals_fills_are_found_on_the_account_never_the_desks_trades(tmp_path: Path) -> None:
    mine = Fill("e-1", "20261119-rule-A", "A", 10, Decimal(50), DAY)
    buy = Fill("e-2", "rehearsal-20261119-rule-M", "M", 5, Decimal(100), DAY)
    stop = Fill("e-3", "rehearsal-20261119-rule-M-stop", "M", -5, Decimal(47), DAY)
    book._record(tmp_path, [mine, buy, stop])
    book._record(tmp_path, [buy])  #: a later write keeps the found rows
    assert book.fills(tmp_path) == (mine,) and book.found(tmp_path) == (buy, stop)
    assert book.positions(tmp_path) == {"A": 10}, "a found fill counted as a position"
