"""The stress scenarios: a strategy's trades replayed through the flash crashes and the 2020
crash, what a black swan's gap would take from it in a night, and an episode the rule was
never shown able to trade through untested."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal

import pytest
from test_lab_rung import AAPL, POUND, SHAPE, TEN_K, _bars, _walk

from desk import orders
from desk.orders import Leg
from desk.store import Bar
from lab import market, rung, stress
from lab.cell import Cell
from lab.rung import Answer
from lab.stress import Gap, Stressed

MAY, AUGUST, CRASH = (episode.name for episode in stress.EPISODES)
TENTH = Decimal("0.1")


def _flash(late: int = 0) -> tuple[Bar, ...]:
    """A smaller trade in January 2010, so the rule has traded; then SHAPE's around 6 May,
    bar 125: decided on bar 122, bought at bar 123's open of 10.70, stopped at 9.36 within
    bar 125. Or so many days later. Then a quiet week."""
    return _bars([10] * 20 + [10.4, 10.6, 10.6, 9.4, 9.4] + [10] * (77 + late) + SHAPE + [10] * 7)


def _stress(bars: Sequence[Bar], symbol: str = "VUSA", rates: rung.Rates = POUND) -> Stressed:
    window = Cell("breakout_20_10", symbol, bars[0].day, bars[-1].day)
    return stress.judge(window, bars, TEN_K, rates)


def _rates(bars: Sequence[Bar]) -> dict[date, Decimal]:
    """A rate of its own for every day of a week, from 0.3 to 0.9."""
    return {bar.day: Decimal(n % 7 + 3) / 10 for n, bar in enumerate(bars)}


def _marked(found: Stressed, bars: Sequence[Bar], rates: rung.Rates = POUND) -> None:
    """Each episode tested is the market's rung's own marking of its days, summed in pounds."""
    for replay in found.episodes[: -len(found.untested) or None]:
        e, summed = replay.episode, Decimal(0)
        for p in found.verdict.trades:
            days = market.daily([p], bars, found.verdict.key.cell.line, rates)
            summed += sum(p.paid * v for day, v in days.items() if e.first <= day <= e.last)
        assert replay.made is not None and abs(replay.made - summed) < Decimal("1e-18")
        held = [p for p in found.verdict.trades if p.held[0] <= e.last and e.first <= p.held[1]]
        assert list(replay.trades) == held


def test_an_episode_is_replayed_in_pounds_after_costs() -> None:
    assert [(e.name, e.first, e.last) for e in stress.EPISODES] == [
        ("the flash crash of May 2010", date(2010, 5, 6), date(2010, 5, 7)),
        ("the flash crash of August 2015", date(2015, 8, 24), date(2015, 8, 24)),
        ("the 2020 crash", date(2020, 2, 20), date(2020, 3, 23)),
    ]
    bars = _flash()
    found = _stress(bars)
    _, trade = found.verdict.trades
    may = found.episodes[0]
    #: 192 shares worth 2,112 at the close before it; the stop brought 1,797.12, less both
    #: legs' costs of 11.64864: the flash crash took 326.52864 of the trade's loss of 268.92864
    assert (may.episode.name, may.trades, may.made) == (MAY, (trade,), Decimal("-326.52864"))
    assert found.worst == Decimal("0.032652864") and found.verdict.answer is Answer.THIN
    #: a dollar line: each close and each fill at its own day's rate, the dollar's move in it
    _marked(_stress(bars, "AAPL", _rates(bars)), bars, _rates(bars))
    for late in range(-4, 5):  #: bought or sold before it, on its first day, its last, after
        _marked(_stress(_flash(late)), _flash(late))
        assert _stress(_flash(late)).untested == (AUGUST, CRASH)
    for seed in range(2):
        bars = _walk(seed, 0.008)
        found = _stress(bars)
        _marked(found, bars)
        assert found.untested == () and found.verdict.answer is Answer.PASS
        assert any(replay.trades and replay.made for replay in found.episodes), seed
        assert found.gap is not None and found.worst is not None
        costs = [found.gap.lost, *(-replay.made for replay in found.episodes if replay.made)]
        assert found.worst == max(costs) / 10_000 > 0


def test_an_episode_the_rule_was_not_shown_able_to_trade_through_is_untested() -> None:
    bars = _flash()
    assert _stress(bars).untested == (AUGUST, CRASH), "the bars end in May: never nothing lost"
    #: out of the market throughout, having traded before it: tested, and it cost nothing
    aside = _stress(_bars(SHAPE + [10] * 105)).episodes[0]
    assert (aside.trades, aside.made) == ((), Decimal(0))
    #: but a rule that had never bought before it began was not shown able to: a line listed
    #: weeks before, its rule still warming, or one whose first buy is on its first day
    assert _stress(bars[110:]).untested == (MAY, AUGUST, CRASH)
    first = _stress(_bars([10] * 105 + SHAPE))  #: decided on 6 May, the episode's first day
    assert first.untested == (MAY, AUGUST, CRASH) and len(first.verdict.trades) == 1
    #: nor is a trade never judged, still held when the bars end: one decided before it or
    #: within it; but one decided on its last day, 7 May, is bought after it
    for late, untested in ((0, 3), (3, 3), (4, 2)):
        held = _stress(_bars(SHAPE + [10] * (77 + late) + SHAPE[:23] + [11, 11]))
        assert len(held.verdict.trades) == 1 and len(held.untested) == untested, late
    #: nor an episode with a session of its venue the line has no bar for: a fall not seen
    for lost in (125, 126):
        assert _stress(bars[:lost] + bars[lost + 1 :]).untested == (MAY, AUGUST, CRASH)
    none = _stress(_bars(SHAPE[:23] + [11, 11]))
    assert (none.verdict.answer, none.gap, none.worst) == (Answer.FAULT, None, None)
    #: a window that starts after the line's first bar could leave out a trade held into it
    for start in (1, 124):
        cut = Cell("breakout_20_10", "VUSA", bars[start].day, bars[-1].day)
        with pytest.raises(ValueError, match="ask of the whole history"):
            stress.judge(cut, bars, TEN_K, POUND)
    with pytest.raises(ValueError, match="no bars in the window"):
        stress.judge(cut, bars[:100], TEN_K, POUND)


def test_the_gap_is_a_black_swans_fall_in_a_night_times_the_leverage_on_the_worst_night() -> None:
    assert TENTH == stress.FALL
    bars = _flash()
    plain = _stress(bars)
    #: held after a close of 11, its 192 shares worth 2,112: it opens a tenth down at 9.90
    #: and they bring 1,900.80, less a sale that slips as a stop's (3 + 0.9504 + 2.8512)
    took = Decimal("218.0016")
    assert plain.gap == Gap(bars[124].day, Decimal("9.90"), plain.verdict.trades[1], took)
    #: a line of three times opens three tenths down: 63 shares worth 693 open at 7.70 and
    #: bring 485.10, less 3 + 0.72765 + 2.18295, the spread and the slippage thrice as wide
    geared = _stress(bars, "3LGO")
    thrice = geared.verdict.trades[1]
    assert (thrice.shares, thrice.held) == (63, (bars[123].day, bars[126].day))
    assert geared.gap == Gap(bars[124].day, Decimal("7.70"), thrice, Decimal("213.8106"))
    #: every night it was held and no other: its last, before the stop sold it, after a close
    #: of 11.50; and never the night before the buy filled, though that close of 10.40 is higher
    for closes, morning, price, pounds in (
        ([10.4, 11, 11.5, 9.4, 9.4], 23, "10.35", "227.7744"),
        ([10.4, 10.2, 10.2, 9.2, 9.2], 22, "9.18", "202.36512"),
    ):
        one = _stress(_bars([10] * 20 + closes))
        (only,) = one.verdict.trades
        woken = only.held[0] + timedelta(morning - 21)
        assert one.gap == Gap(woken, Decimal(price), only, Decimal(pounds))
    #: the worst night of every trade's every night, no other taking more; on a dollar line
    #: the close at the night's rate, the open and the sale's costs at the morning's
    walk = _walk(1, 0.008)  #: its worst night is in its fiftieth trade of sixty-one
    rates, at = _rates(walk), {bar.day: n for n, bar in enumerate(walk)}
    found = _stress(walk, "AAPL", rates)
    takes = []
    for p in found.verdict.trades:
        for n in range(at[p.held[0]], at[p.held[1]]):
            opened, rate = walk[n].close * (1 - TENTH), rates[walk[n + 1].day]
            sold = orders.charges(AAPL, Leg.STOP, p.shares, opened, rate).total
            takes.append(p.shares * (walk[n].close * rates[walk[n].day] - opened * rate) + sold)
    assert found.gap is not None and found.gap.lost == max(takes) > 0
