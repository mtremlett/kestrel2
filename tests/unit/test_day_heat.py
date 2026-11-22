"""day heat: the book's heat on a day's record is the pounds lost if every stop were hit, each
line at its stop or, if worse, at its worst recorded overnight gap; unknown without a stop."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from desk import book, day_money, venues
from desk.broker import Fill
from desk.lines import Line
from desk.store import Bar

DAYS = venues.sessions("LSE", date(2025, 1, 6), date(2025, 1, 10))[:4]
BUY = DAYS[0]


def _bars(opens: list[int], closes: list[int]) -> tuple[Bar, ...]:
    return tuple(
        Bar(d, Decimal(o), Decimal(9), Decimal(1), Decimal(c), 1_000_000)
        for d, o, c in zip(DAYS, opens, closes, strict=True)
    )


def test_the_heat_is_each_lines_loss_at_its_stop_or_its_worst_gap_if_worse(tmp_path: Path) -> None:
    calm, gapped = Line("CALM", "LSE", "GBP", 1), Line("GAP", "LSE", "GBP", 1)
    archive = {calm: _bars([10] * 4, [10] * 4), gapped: _bars([10, 10, 6, 10], [10, 10, 10, 10])}
    book._record(tmp_path, [Fill("1", "a", "CALM", 10, Decimal(10), BUY)])
    book._record(tmp_path, [Fill("2", "b", "GAP", 5, Decimal(10), BUY)])
    book._write(tmp_path / book.STOPS, [book.LEVELS, ("a-stop", 9), ("b-stop", 9)])
    book.record_rates(tmp_path, DAYS[3], {"GBP": Decimal(1)})
    #: CALM: 10 shares to its stop, 1 each = 10; GAP: 5 shares to a gap of 4, past its stop's 1
    assert day_money.heat(tmp_path, archive, DAYS[3]) == Decimal("30.00")
    book._write(tmp_path / book.STOPS, [book.LEVELS, ("a-stop", 9)])
    assert day_money.heat(tmp_path, archive, DAYS[3]) is None, "a stop never kept: heat unknown"
