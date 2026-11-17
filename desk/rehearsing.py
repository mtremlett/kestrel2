"""rehearsing - THE REHEARSAL'S BROKER DOOR (desk/command.py): the paper door that marks every
order the rehearsal sends as its own and shows the rehearsal's desk only what it sent."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from desk import placing
from desk.broker import Fill, Report
from desk.orders import Order, Sale


class Rehearsing(placing.Paper):
    """THE REHEARSAL'S BROKER DOOR: the paper door (placing.Paper) that sends every order under
    an id marked as this run's own, the mark put after the id's date, and gives the desk back
    only what it sent in this run, by the ids the desk gave: an order, fill or stop of the
    account's under the very id the rehearsal decides is another's and never its book."""

    mark = ""  #: this run's stamp, set while the rehearsal runs

    def _in(self, ref: str) -> str:
        return ref[:8] + self.mark + ref[8:]

    def _own(self, ref: str) -> bool:
        return ref[8 : 8 + len(self.mark)] == self.mark

    def _out(self, ref: str) -> str:
        return self._in(ref)[:8] + ref[8 + len(self.mark) :] if self._own(ref) else ref

    def place(self, order: Order | Sale) -> Report:
        """Send the order marked; the answer is given under the desk's own id."""
        return self._back(super().place(replace(order, order_id=self._in(order.order_id))))

    def report(self, order_id: str) -> Report | None:
        """What the broker did with the marked order: none of the account's under that id."""
        told = super().report(self._in(order_id))
        return told and self._back(told)

    def _back(self, report: Report) -> Report:
        return replace(report, order_id=self._out(report.order_id), fills=self._ours(report.fills))

    def _ours(self, fills: Sequence[Fill]) -> tuple[Fill, ...]:
        mine = (f for f in fills if self._own(f.order_id))
        return tuple(replace(f, order_id=self._out(f.order_id)) for f in mine)

    def fills(self) -> tuple[Fill, ...]:
        """The fills of the rehearsal's own orders alone."""
        return self._ours(super().fills())

    def cancel(self) -> tuple[str, ...]:
        """Cancel the orders this run sent that are still working; the account's are left."""
        working = {o.number: o.ref for o in self._orders().unsettled if placing._working(o)}
        mine = {number: ref for number, ref in working.items() if self._own(ref)}
        said = self._cancelled(mine) if mine else {}
        return tuple(self._out(ref) for number, ref in mine.items() if said[number] in placing.GONE)
