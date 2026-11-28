"""incident cancelled: SimCity's scenario for one real night (see `git log`, DECISIONS)."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from desk import book, halt
from desk.broker import Fault

if TYPE_CHECKING:
    from desk.simcity import _Life

CANCELLED = "the broker cancels every order of the day with nothing filled"

NAMED = "an order cancelled unfilled is named that day, and the book stays the broker's"


def cancelled(life: _Life, on: date) -> None:
    """The broker cancels, unfilled, the first order it is sent on every line. The desk must name
    each such order on the morning's list (unless another rule's order then fills its line) and
    leave the book the broker's: shares never bought are never in it, so no sale is sent."""
    seen = len(life.pretend.submitted())
    life.pretend._faults.update(  # noqa: SLF001 - the world's own broker, told what to do
        {x.symbol: Fault.REJECT for x in life.market}
    )
    life.live(on)
    life.pretend._faults.clear()  # noqa: SLF001 - what no order met is not left waiting
    told = {b.order_id for b in halt.morning(life.desk, on)[halt.Blocker.BROKER]}
    answers = {i: life.pretend.report(i) for i in life.pretend.submitted()[seen:]}
    bought = {i.rsplit("-", 1)[1] for i, r in answers.items() if r and r.fills}
    resent = {
        i.removesuffix("-r1") for i, r in answers.items() if i.endswith("-r1") and r and r.fills
    }
    refused = {i for i, r in answers.items() if r and not r.fills and not i.endswith("-r1")}
    refused -= told | resent
    named = all(i.rsplit("-", 1)[1] in bought for i in refused)
    level = dict(book.positions(life.desk)) == dict(life.pretend.holdings())
    life.promise(NAMED, named and level)
