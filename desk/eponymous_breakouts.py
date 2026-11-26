"""eponymous_breakouts - rules named for their authors, ported one at a time under the one
template (`desk/strategy.py`), long only. The paper desk does not trade these: they are
here to be judged on the ladder. Each rule's docstring writes down its author, source,
the author's instrument and period, and the figure he published.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import ARITHMETIC, RANGES, Decision, Declared, Rule, Timeframe, _run


@dataclass(frozen=True)
class _Box:
    top: Decimal
    bottom: Decimal


class _Formation:
    """A box in the making. Its top is a high that the next 3 sessions do not exceed; its
    bottom is the lowest low from the top's session on that the next 3 sessions do not
    undercut. The rule starts it again on a higher high before the top is confirmed."""

    def __init__(self, bar: Bar) -> None:
        self.top, self.low, self.low_age = bar.high, bar.low, 0

    def add(self, bar: Bar) -> _Box | None:
        """The box, once both its top and its bottom stand; None while it is forming.
        Shown only bars whose high does not pass the top."""
        if bar.low < self.low:
            self.low, self.low_age = bar.low, 0
        else:
            self.low_age += 1
        # the low is from the top's session on, so 3 sessions without a lower low also
        # confirm the top
        return _Box(self.top, self.low) if self.low_age >= 3 else None


class _Darvas:
    """Nicolas Darvas's box (How I Made $2,000,000 in the Stock Market, 1960). Author's
    instrument and period: American-listed shares he traded from his hotel rooms from 1957
    to 1959 (his dates are loosely given).
    Published figure: a profit of about $2,000,000, his own account of it, never
    audited (no secondary source is used here). The rule: a stock trading in a box, its
    top and bottom each confirmed by 3 sessions, is bought when it breaks out through the
    top, with a stop at the box's bottom; each higher box that forms raises the stop to
    its own bottom, and the stop never falls. On daily closes, as the template reads
    them: buy a close over the top; sell a close under the stop. A high over the top that closes
    inside the box, or a box left by a close under its bottom unheld, begins a new box.
    No holding period: his sale is the stop alone, and a rising stock is held while it rises.
    Simplification: he boxed only stocks making new highs; this rule boxes at any level."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, RANGES)

    def __init__(self) -> None:
        self._form: _Formation | None = None
        self._box: _Box | None = None
        self._stop: Decimal | None = None

    def _restart(self, bar: Bar) -> None:
        self._form, self._box = _Formation(bar), None

    def _raise_stop(self, bottom: Decimal) -> None:
        self._stop = bottom if self._stop is None else max(self._stop, bottom)

    def _forming(self, bar: Bar, holding: bool) -> None:
        if self._form is None or bar.high > self._form.top:
            self._restart(bar)
            return
        self._box = self._form.add(bar)
        if self._box is not None and holding:
            self._raise_stop(self._box.bottom)

    def step(self, bar: Bar, holding: bool) -> bool:
        if not holding:
            self._stop = None
        elif self._stop is not None and bar.close < self._stop:
            self._restart(bar)
            return False
        if self._box is None:
            self._forming(bar, holding)
        elif bar.close > self._box.top:
            self._raise_stop(self._box.bottom)
            self._restart(bar)
            return True
        elif bar.high > self._box.top or (not holding and bar.close < self._box.bottom):
            self._restart(bar)
        return holding


#: The rules of this module, by name; none is one of the paper desk's five.
RULES: Mapping[str, type[Rule]] = {"darvas_box": _Darvas}


def decide(bars: Mapping[str, Sequence[Bar]]) -> tuple[Decision, ...]:
    """A decision from every rule here for every line and every day the bars cover."""
    with localcontext(ARITHMETIC):
        return tuple(
            decision
            for symbol, series in bars.items()
            for name, make in RULES.items()
            for decision in _run(name, make(), symbol, series)
        )


EPONYMOUS: Mapping[str, type[Rule]] = {"darvas_box": _Darvas}
