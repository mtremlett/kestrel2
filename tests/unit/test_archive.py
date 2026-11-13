"""The free price archive: what it says is read exactly, once, on entry, or refused."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from desk import archive
from desk.lines import Line
from desk.store import Bar

US, UK = Line("AAA", "US", "USD"), Line("BBB", "LSE", "GBP")
Row = tuple[str, str | None, str, str, str, int]
ROWS: tuple[Row, ...] = (
    ("2025-11-13T14:30", "187.4300079345703", "189.1", "186.5", "188.25", 51_000),
    ("2025-11-14T14:30", "188.0", "190.75", "187.5", "190.5", 48_000),
)


def _payload(rows: tuple[Row, ...] = ROWS, currency: str = "USD", symbol: str = "AAA") -> bytes:
    """The archive's own shape, with every number written as the text it sends."""
    stamps = [int(datetime.fromisoformat(r[0]).replace(tzinfo=UTC).timestamp()) for r in rows]
    quote = ", ".join(
        f'"{key}": [{", ".join("null" if r[n] is None else str(r[n]) for r in rows)}]'
        for n, key in enumerate(("open", "high", "low", "close", "volume"), 1)
    )
    result = f'"meta": {{"symbol": "{symbol}", "currency": "{currency}"}}, "timestamp": {stamps}'
    indicators = f'"indicators": {{"quote": [{{{quote}}}]}}'
    return f'{{"chart": {{"error": null, "result": [{{{result}, {indicators}}}]}}}}'.encode()


def test_bars_are_read_exactly_and_dated_by_their_session() -> None:
    assert archive.parse(US, _payload()) == (
        Bar(
            date(2025, 11, 13),
            Decimal("187.4300079345703"),
            Decimal("189.1"),
            Decimal("186.5"),
            Decimal("188.25"),
            51_000,
        ),
        Bar(
            date(2025, 11, 14),
            Decimal("188.0"),
            Decimal("190.75"),
            Decimal("187.5"),
            Decimal("190.5"),
            48_000,
        ),
    )


def test_a_line_priced_in_pence_enters_in_pounds() -> None:
    bars = archive.parse(UK, _payload(currency="GBp", symbol="BBB.L"))
    assert bars[1].close == Decimal("1.905") and bars[0].open == Decimal("1.874300079345703")


def test_a_day_the_archive_gives_without_a_full_bar_has_no_bar() -> None:
    rows = (("2025-11-12T14:30", None, "189.1", "186.5", "188.25", 0), *ROWS)
    assert [b.day for b in archive.parse(US, _payload(rows))] == [
        date(2025, 11, 13),
        date(2025, 11, 14),
    ]


def test_a_line_the_archive_holds_no_history_for_has_no_bars() -> None:
    assert archive.parse(US, _payload(rows=())) == ()


@pytest.mark.parametrize(
    "payload",
    [
        _payload(currency="EUR"),
        _payload(currency="GBp"),
        _payload(symbol="AAA.L"),
        _payload((("2025-11-13T14:30", "1", "1", "1", "1", "1.5"),)),  # type: ignore[arg-type]
        b'{"chart": {"result": null, "error": {"code": "Not Found"}}}',
    ],
    ids=["another currency", "pence for a dollar line", "another line", "part of a share", "none"],
)
def test_an_answer_about_anything_else_is_refused_naming_the_line(payload: bytes) -> None:
    with pytest.raises(ValueError, match="AAA"):
        archive.parse(US, payload)


def test_the_archive_is_asked_for_nothing_on_or_after_the_day() -> None:
    address = archive.address(UK, date(2025, 11, 17))
    assert "/BBB.L?" in address
    assert f"period2={int(datetime(2025, 11, 17, tzinfo=UTC).timestamp())}&" in address
