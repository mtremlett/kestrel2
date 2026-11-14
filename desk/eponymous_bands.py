"""eponymous_bands - the eponymous strategies that trade a channel of highs and lows, each a
rule under the one template (`desk.strategy`'s interface, imported and not changed). The paper
desk does not trade them: the ladder judges them.

DONCHIAN CHANNEL BREAKOUT.
  Author:      Richard Donchian, "the four-week rule" (1960s, Commodities Futures Fund).
  Source:      his own newsletter and fund notes are not on hand; the rule is read from Curtis
               Faith, Way of the Turtle (2007), SECONDARY, which gives it as the four-week
               breakout: buy a price over the highest high of the four weeks before, and close
               the position on a price under the lowest low of the four weeks before.
  Instrument:  commodity futures, by his fund; period 1960s to 1970s.
  Published figure: none found in a primary source; none is claimed here.
  Where sources differ: Faith's Turtle system 1 is the same breakout with a 10-day exit
               (`strategy.breakout_20_10`); the four-week rule exits on the 4-week low, 20 sessions.
  Reading here: four weeks is 20 sessions; long only (the original also sold short, which the
               template has no word for); on the close, as the template's other breakouts are.

DONCHIAN FADE IN CHOP.
  Author:      Richard Donchian, the four-week channel, read the other way: in a range the channel
               edge is where price turns back, so the edge is faded and not followed.
  Source:      SECONDARY, a practitioner reading of the channel in a range, found in no primary
               text of Donchian's; its source is to be found (R-RUNNER-64 remains), and the
               channel width that makes a range is this desk's reading (10% of the midpoint).
  Instrument:  commodity futures by his fund; here the desk's daily lines. Period: 1960s on.
  Published figure: none found; none is claimed here.
  Where sources differ: the range test is not in Donchian's rule at all; the exit at the
               midpoint (and not the far edge) is the cautious reading.
  Reading here: long only; buy a close at or under the lowest low of the 20 sessions before,
               when that channel is a range (high less low at most a tenth of its midpoint);
               sell a close at or over the channel's midpoint. On the close.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import ClassVar

from desk.lines import LINES
from desk.store import Bar
from desk.strategy import RANGES, Declared, Rule, Timeframe, _Window

#: Four weeks of five sessions.
WEEKS_4 = 20


class DonchianChannelBreakout:
    """Buy a close over the highest high of the 20 sessions before; sell a close under the
    lowest low of the 20 sessions before. Nothing is bought until 20 sessions are seen."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, RANGES)

    def __init__(self) -> None:
        self._highs, self._lows = _Window(WEEKS_4), _Window(WEEKS_4)

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        if holding:
            wants = bar.close >= self._lows.low()
        else:
            wants = self._highs.full and bar.close > self._highs.high()
        self._highs.add(bar.high)
        self._lows.add(bar.low)
        return wants


#: A channel is a range when its width is at most this share of its midpoint.
RANGE_WIDTH = Decimal("0.10")


class DonchianFadeChop:
    """In a 20-session range, buy a close at or under the channel's low, and sell a close at or
    over its midpoint. Nothing is bought until 20 sessions are seen."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, RANGES)

    def __init__(self) -> None:
        self._highs, self._lows = _Window(WEEKS_4), _Window(WEEKS_4)

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        wants = False
        if self._highs.full:
            high, low = self._highs.high(), self._lows.low()
            middle = (high + low) / 2
            if holding:
                wants = bar.close < middle
            else:
                wants = high - low <= RANGE_WIDTH * middle and bar.close <= low
        self._highs.add(bar.high)
        self._lows.add(bar.low)
        return wants


#: The eponymous rules by name, apart from the five and the wiring strategy.
EPONYMOUS: Mapping[str, type[Rule]] = {
    "donchian_channel_breakout": DonchianChannelBreakout,
    "donchian_fade_chop": DonchianFadeChop,
}
