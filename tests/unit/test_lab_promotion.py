"""Before paper and after it: no candidate without the ladder's pass and a kill condition
written first, and none promoted but on thirty effective paper trades, net positive."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import pytest
from test_lab_rung import FREE

from desk.book import RoundTrip
from desk.broker import Fill
from lab import deflated, promotion
from lab.promotion import Candidate, Kill, Standing
from lab.rung import Answer

RULE, DAY = "breakout_20_10", date(2026, 1, 1)


def _row(rule: str = RULE, answer: str = "PASS", **rungs: str) -> dict[str, Any]:
    """The ladder's line for the rule on VUSA: every named rung passed, but those given."""
    named = dict.fromkeys(deflated.NAMED, "PASS") | rungs
    said = {name: [one, f"{name}'s reason"] for name, one in named.items()}
    return {"cell": [rule, "VUSA", "LSE"], "rungs": said, "answer": answer}


ON_PAPER = Candidate(_row(), DAY, Kill(Decimal(300), 4))
TWO = Candidate(_row(), DAY, Kill(Decimal(300), 2))


def _buy(day: int, line: str = "VUSA", rule: str = RULE, order: int | None = None) -> Fill:
    """Ten shares bought so many days after the declaration, on the order decided that day
    (or, for an order filled over several days, on the day given)."""
    on = DAY + timedelta(day)
    made = f"{DAY + timedelta(day if order is None else order):%Y%m%d}-{rule}-{line}"
    return Fill(f"b{day}{line}", made, line, 10, Decimal(100), on)


def _trip(
    bought: int,
    sold: int,
    profit: str,
    line: str = "VUSA",
    rule: str = RULE,
    order: int | None = None,
) -> RoundTrip:
    """A round trip of the desk's book: ten shares bought and sold on those days."""
    sell = Fill(f"s{sold}{line}", "a-sale", line, -10, Decimal(100), DAY + timedelta(sold))
    return RoundTrip(_buy(bought, line, rule, order), sell, Decimal(profit), FREE, Decimal(profit))


def _run(*profits: str, start: int = 1) -> list[RoundTrip]:
    """One trade after another, each held two days, none held with another."""
    return [_trip(start + 3 * n, start + 3 * n + 1, p) for n, p in enumerate(profits)]


def _stand(
    trips: Sequence[RoundTrip], held: Sequence[Fill] = (), on: Candidate = ON_PAPER
) -> Standing:
    """The standing on a ledger of these round trips' fills, and of buys still held."""
    return promotion.standing(on, [*(trip.buy for trip in trips), *held], trips)


def test_no_candidate_without_the_ladders_pass_and_a_kill_condition_that_can_bite() -> None:
    #: a line claiming a pass its own rungs do not give (a thin worst fold, the market
    #: failed), a line that says less, and one short of a named rung: none is a candidate
    thin, beaten = _row(folds="THIN"), _row(answer="THIN", market="FAIL")
    del (short := _row())["rungs"]["market"]
    for row in (thin, beaten, _row(answer="DOUBT"), _row(folds="OK"), short):
        with pytest.raises(ValueError, match="has not passed the ladder"):
            Candidate(row, DAY, ON_PAPER.kill)
    with pytest.raises(ValueError, match="no strategy of the desk's"):
        Candidate(_row("a_hunch"), DAY, ON_PAPER.kill)
    for fall in ("0", "-1", "NaN", "Infinity", "1500.01"):
        with pytest.raises(ValueError, match="a fall of"):
            Kill(Decimal(fall), 4)
    assert Kill(promotion.DEEPEST, 1).fall == 1500, "the A-GATE's own fall is the loosest"
    with pytest.raises(ValueError, match="losing trades in a row"):
        Kill(Decimal(300), 0)
    #: the condition is written before the first paper buy, sold since or still held
    for early in ([_trip(0, 3, "50")], []):
        with pytest.raises(ValueError, match="bought on .* not after its kill condition"):
            _stand(early, held=[_buy(0, "ISF")])
    assert _stand([], held=[_buy(0, rule="trend_50_200")]).trades == 0, "another rule's buy"
    again = [_trip(3, 4, "50", order=3), _trip(5, 9, "50", order=3)]
    with pytest.raises(ValueError, match="bought again on .* after a sale"):
        _stand(again)
    assert (
        _stand([_trip(3, 5, "50", order=3), again[1]]).trades == 1
    ), "the day it sold is not after"
    with pytest.raises(ValueError, match="more shares sold than the fills given bought"):
        promotion.standing(ON_PAPER, [], _run("50"))


def test_promoted_only_on_thirty_effective_paper_trades_net_positive() -> None:
    few = _stand(_run(*["50"] * 29))
    assert (few.answer, few.trades, few.effective) == (Answer.THIN, 29, 29)
    assert few.profit == 1450 and _stand([]).answer is Answer.THIN, "not begun is not failed"
    won = _stand(_run(*["50", "-40"] * 15))
    assert (won.answer, won.effective, won.killed) == (Answer.PASS, 30, None)
    #: thirty trades that made nothing, to the penny, are not net positive: kept on paper
    flat = _stand(_run(*["50", "-50"] * 15))
    assert (flat.answer, flat.profit) == (Answer.DOUBT, Decimal(0))
    assert _stand(_run(*["50", "-50"] * 15, "0.01")).answer is Answer.PASS
    assert _stand(_run(*["50", "-50"] * 15, "0.004")).answer is Answer.DOUBT
    #: another rule's trades, however many, are not this candidate's
    others = [_trip(1 + 3 * n, 2 + 3 * n, "50", rule="trend_50_200") for n in range(30)]
    mixed = _stand(_run(*["50"] * 29) + others)
    assert (mixed.answer, mixed.trades, mixed.profit) == (Answer.THIN, 29, Decimal(1450))


def test_trades_held_together_are_one_bet_and_an_order_filled_in_parts_one_trade() -> None:
    #: forty winners on forty lines, all held over the same days: one bet, forty times
    one = _stand([_trip(1, 5, "50", line=f"L{n}") for n in range(40)])
    assert (one.answer, one.trades, one.effective) == (Answer.THIN, 40, 1)
    #: sold on the morning another is bought: that day is shared, so still one bet
    touching = [_trip(1, 4, "50"), _trip(4, 6, "50", line="IUKD"), _trip(7, 8, "50")]
    assert _stand(touching).effective == 2
    #: the most that can be chosen apart, whatever order the book gives them in: a long
    #: trade held over two short ones leaves two bets, not one
    over = [_trip(1, 9, "50", line="IUKD"), _trip(6, 8, "50"), _trip(2, 3, "50", line="ISF")]
    assert [_stand(o).effective for o in (over, over[::-1])] == [2, 2]
    #: an order sold in three parts is three round trips and one trade: its parts lose
    #: together once, never three losers in a row
    split = _stand([_trip(1, 2, "-10")] * 3 + _run("-10", "-10", start=4))
    assert (split.trades, split.profit, split.killed) == (3, Decimal(-50), None)
    #: ten shares bought at once and sold as three and seven: a trade when the seven are sold
    three, seven = (
        replace(trip, buy=replace(trip.buy, quantity=shares))
        for trip, shares in ((_trip(1, 2, "-1"), 3), (_trip(1, 3, "-1"), 7))
    )
    sales = ([three], [three, seven])
    assert [promotion.standing(ON_PAPER, [_buy(1)], s).trades for s in sales] == [0, 1]
    #: bought over two days and sold over two, it was held from the first to the last
    long = [_trip(3, 6, "50", order=3), _trip(5, 9, "50", order=3)]
    assert _stand([*long, _trip(1, 2, "50", line="ISF")]).effective == 2
    assert [_stand([*long, _trip(a, a + 1, "50", line="ISF")]).effective for a in (3, 7)] == [1, 1]
    #: an order with shares still held is no trade yet, though its sales' money is counted
    rest = _buy(1, "ISF")
    part = _stand([_trip(1, 2, "-20", line="ISF"), *_run(*["50"] * 29, start=4)], held=[rest])
    assert (part.answer, part.trades, part.effective) == (Answer.THIN, 29, 29)
    assert part.profit == 1430
    sold = [_trip(1, 2, "-20", line="ISF"), _trip(1, 3, "5", line="ISF")]
    whole = _stand([*sold, *_run(*["50"] * 29, start=4)])
    assert (whole.answer, whole.trades, whole.effective) == (Answer.PASS, 30, 30)


def test_the_kill_condition_written_first_kills_and_nothing_after_revives() -> None:
    #: up 200, then down 300 from that highest point, exactly: killed on the day it got there
    fell = _stand(_run("200", "-100", "90", "-290", *["500"] * 40))
    assert fell.answer is Answer.FAIL and fell.trades == 44 and fell.profit == 19900
    assert fell.killed == f"by {DAY + timedelta(11)} it had fallen 300.00 from its highest point"
    near = _stand(_run("200", "-100", "90", "-289.99", *["500"] * 40))
    assert (near.answer, near.killed) == (Answer.PASS, None), "a penny short of its fall"
    #: a fall is measured from nothing made when it has never been ahead
    assert _stand(_run("-150", "10", "-160")).killed is not None
    #: half an order sold 300 down kills on the money, and the rest sold well does not revive
    half = [_trip(1, 2, "-300", line="ISF")]
    for later, held in ([], [_buy(1, "ISF")]), ([_trip(1, 20, "400", line="ISF")], []):
        dead = _stand([*half, *later], held=held)
        assert dead.answer is Answer.FAIL and dead.killed is not None
        assert str(DAY + timedelta(2)) in dead.killed
    #: four losers in a row kill; three, a flat trade, and three more do not
    row = _stand(_run("-1", "-1", "-1", "-1", "900"))
    assert row.answer is Answer.FAIL
    assert row.killed == f"by {DAY + timedelta(11)} it had lost 4 trades in a row"
    assert _stand(_run(*["-1"] * 3, "0", *["-1"] * 3)).killed is None
    #: the row is read in the order the ledger sold them, within a day too, and a part
    #: sold at a loss is no loser until its order is whole
    first, lost, gained = _trip(1, 2, "-1"), _trip(6, 9, "-1"), _trip(5, 9, "9", line="ISF")
    assert _stand([first, lost, gained], on=TWO).killed is not None
    assert _stand([first, gained, lost], on=TWO).killed is None
    assert _stand([first, lost], held=[_buy(6)], on=TWO).killed is None
    #: an order's parts win or lose as one, and it takes its place when its last part sells
    assert _stand([first, _trip(5, 8, "30"), _trip(5, 9, "-20")], on=TWO).killed is None
    apart = [_trip(5, 9, "-5", line="IUKD"), gained, _trip(5, 9, "-5", line="IUKD")]
    assert _stand([first, *apart], on=TWO).killed is None
    #: a ledger that kept its fills out of the days' order is read in the days' order
    assert _stand([_trip(4, 5, "9"), _trip(7, 8, "-1"), first], on=TWO).killed is None
    late = _stand([_trip(7, 8, "-100"), _trip(1, 2, "100"), _trip(4, 5, "-200")])
    assert late.killed == f"by {DAY + timedelta(8)} it had fallen 300.00 from its highest point"
    #: a day's sales are read together for the fall: neither's loss alone is a fall that day
    day = [_trip(1, 5, "-400"), _trip(2, 5, "450", line="IUKD")]
    assert [_stand(d).killed for d in (day, day[::-1])] == [None, None]
    #: whichever part is met first is the one named
    both = _stand([first, _trip(4, 5, "-299"), _trip(7, 8, "-1")], on=TWO)
    assert both.killed == f"by {DAY + timedelta(5)} it had fallen 300.00 from its highest point"
    rowed = _stand([first, _trip(4, 5, "-1"), _trip(7, 8, "-298")], on=TWO)
    assert rowed.killed == f"by {DAY + timedelta(5)} it had lost 2 trades in a row"
