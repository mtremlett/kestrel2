"""The free price archive: what it says is read exactly, once, on entry, or refused; its
five-minute bars too, which it forgets after sixty days (DAT-11)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from http.client import IncompleteRead
from urllib.error import URLError

import pytest

from desk import archive
from desk.bars import Five
from desk.lines import Line
from desk.store import Bar, Refused

US, UK = Line("AAA", "US", "USD", 1), Line("BBB", "LSE", "GBP", 1)
Row = tuple[str, str | None, str, str, str, int]
ROWS: tuple[Row, ...] = (
    ("2025-11-13T14:30", "187.4300079345703", "189.1", "186.5", "188.25", 51_000),
    ("2025-11-14T14:30", "188.0", "190.75", "187.5", "190.5", 48_000),
)


PRICES = ("open", "high", "low", "close")
MARK = datetime(2025, 11, 14, 14, 30, tzinfo=UTC)  #: when the second of ROWS starts


def _five(start: datetime, row: Row) -> Five:
    open_, high, low, close = (Decimal(str(price)) for price in row[1:5])
    return Five(start, open_, high, low, close, row[5])


FIVES = (_five(MARK - timedelta(1), ROWS[0]), _five(MARK, ROWS[1]))


def _stamp(moment: str) -> int:
    return int(datetime.fromisoformat(moment).replace(tzinfo=UTC).timestamp())


def _payload(
    rows: tuple[Row, ...] = ROWS,
    currency: str = "USD",
    symbol: str = "AAA",
    span: str = "1d",
    traded: str = "2025-11-14T21:00:01",
) -> bytes:
    """The archive's own shape, with every number written as the text it sends: the bars, their
    span, the line's last trade, and the close of the session of 14 November 2025."""
    stamps = [_stamp(r[0]) for r in rows]
    quote = ", ".join(
        f'"{key}": [{", ".join("null" if r[n] is None else str(r[n]) for r in rows)}]'
        for n, key in enumerate(("open", "high", "low", "close", "volume"), 1)
    )
    close = f'"currentTradingPeriod": {{"regular": {{"end": {_stamp("2025-11-14T21:00")}}}}}'
    said = f'"dataGranularity": "{span}", "regularMarketTime": {_stamp(traded)}, {close}'
    meta = f'"meta": {{"symbol": "{symbol}", "currency": "{currency}", {said}}}'
    result = f'{meta}, "timestamp": {stamps}'
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
        _payload(span="5m"),
    ],
    ids=["currency", "pence for a dollar line", "another line", "part of a share", "none", "5m"],
)
def test_an_answer_about_anything_else_is_refused_naming_the_line(payload: bytes) -> None:
    with pytest.raises(ValueError, match="AAA"):
        archive.parse(US, payload)


def test_the_archive_is_asked_for_nothing_on_or_after_the_day() -> None:
    address = archive.address(UK, date(2025, 11, 17))
    assert "/BBB.L?" in address
    assert f"period2={int(datetime(2025, 11, 17, tzinfo=UTC).timestamp())}&" in address


def test_a_london_line_priced_in_pounds_is_read_as_given_on_its_summer_session() -> None:
    rows: tuple[Row, ...] = (("2025-06-13T07:00", "1.5", "1.75", "1.25", "1.5", 900),)
    assert archive.parse(UK, _payload(rows, "GBP", "BBB.L")) == (
        Bar(
            date(2025, 6, 13), Decimal("1.5"), Decimal("1.75"), Decimal("1.25"), Decimal("1.5"), 900
        ),
    )


def test_a_price_that_is_not_a_number_enters_as_one_the_store_refuses() -> None:
    rows: tuple[Row, ...] = (("2025-11-13T14:30", "NaN", "Infinity", "1", "1", 9),)
    bar = archive.parse(US, _payload(rows))[0]
    assert not bar.open.is_finite() and not bar.high.is_finite()


def test_a_line_the_archive_refuses_is_refused_alone_and_the_others_carry_on() -> None:
    other, cut, late = (Line(s, "US", "USD", 1) for s in ("CCC", "DDD", "EEE"))
    gone = {US: URLError("HTTP Error 404"), cut: IncompleteRead(b"{"), late: TimeoutError()}

    def ask(line: Line, _: date) -> tuple[Bar, ...]:
        if line in gone:
            raise gone[line]
        return archive.parse(line, _payload(symbol=line.symbol))

    assert archive.gather((US, UK, other, cut, late), date(2025, 11, 17), ask) == {
        US: Refused("URLError: <urlopen error HTTP Error 404>"),
        UK: Refused("ValueError: BBB: the archive answered about BBB"),
        other: archive.parse(other, _payload(symbol="CCC")),
        cut: Refused("IncompleteRead: IncompleteRead(1 bytes read)"),
        late: Refused("TimeoutError: "),
    }
    with pytest.raises(KeyError, match="chart"):  # a shape the desk does not know: stop all
        archive.gather((US,), date(2025, 11, 17), lambda line, _: archive.parse(line, b"{}"))


def test_five_minute_bars_are_read_exactly_once_each_has_ended() -> None:
    """The archive's answer in a session: a five minutes with no trade, the bar still forming,
    and last the price of the moment, dated at the last trade."""
    forming: Row = ("2025-11-14T14:40", "190.5", "191", "190", "190.75", 7)
    rows = (*ROWS, ("2025-11-14T14:35", None, "1", "1", "1", 0), forming)
    quote: Row = ("2025-11-14T14:42:10", "9", "9", "9", "9", 0)
    during = _payload((*rows, quote), span="5m", traded="2025-11-14T14:42:10")
    ended = (*FIVES, _five(MARK + timedelta(minutes=10), forming))
    for seconds, read in ((899, FIVES), (900, ended), (86_400, ended)):
        assert archive.parse_five(US, during, MARK + timedelta(seconds=seconds)) == read
    with pytest.raises(ValueError, match="not a five-minute mark"):  # dated at no last trade
        archive.parse_five(US, _payload((*rows, quote), span="5m"), MARK + timedelta(1))
    after = _payload((*ROWS, ("2025-11-14T21:00", "9", "9", "9", "9", 0)), span="5m")
    assert archive.parse_five(US, after, MARK + timedelta(1)) == FIVES  # the price at the close
    pence = archive.parse_five(UK, _payload(currency="GBp", symbol="BBB.L", span="5m"), MARK)
    assert pence == (replace(FIVES[0], **{k: getattr(FIVES[0], k) / 100 for k in PRICES}),)
    with pytest.raises(ValueError, match="AAA: the archive answered in bars of 1d, not 5m"):
        archive.parse_five(US, _payload(), MARK)


def test_five_minute_bars_are_asked_for_as_far_back_as_the_archive_keeps_them() -> None:
    address = archive.address_five(UK, MARK)
    first, end = (int((MARK - timedelta(days)).timestamp()) for days in (59, 0))
    assert address.endswith(f"/BBB.L?period1={first}&period2={end}&interval=5m")
    with pytest.raises(TypeError, match="offset-naive"):
        archive.address_five(UK, MARK.replace(tzinfo=None))
