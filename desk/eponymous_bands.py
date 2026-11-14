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

DONCHIAN FADE IN A CHOP.
  Author:      Richard Donchian (the channel of the highest high and lowest low of N periods).
  Source:      SECONDARY, read 14 Nov 2026: the fade of a channel inside a range is not in
               his writings; it is the common reading of his channel in trading texts (the
               bands as the edges of a range, the middle as the mean). Primary source not
               found; the old desk's `EPONYMOUS_STRATEGIES` could not be read in this run.
  Instrument:  his fund traded commodity futures; the fade carries no instrument of its own.
  Published figure: none found; none is claimed here.
  Where sources differ: the exit is the channel's middle here; some texts exit at the
               opposite band. No source fixes the period for the fade; the breakout's 20 is used.
  Reading here: long only; buy a close under the lowest low of the 20 sessions before (the
               floor of the range); sell a close at or over the middle of that channel, the
               mean of its highest high and lowest low. "Chop" is not detected: the template
               has no regime word, so the rule is the fade alone.
"""

from __future__ import annotations

from collections.abc import Mapping
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


class DonchianFadeChop:
    """Buy a close under the lowest low of the 20 sessions before; sell a close at or over
    the middle of that channel. Nothing is bought until 20 sessions are seen."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, RANGES)

    def __init__(self) -> None:
        self._highs, self._lows = _Window(WEEKS_4), _Window(WEEKS_4)

    def step(self, bar: Bar, holding: bool) -> bool:
        """Shown the next bar after its close: whether to be in the market from here."""
        if holding:
            wants = bar.close < (self._highs.high() + self._lows.low()) / 2
        else:
            wants = self._lows.full and bar.close < self._lows.low()
        self._highs.add(bar.high)
        self._lows.add(bar.low)
        return wants


#: The eponymous rules by name, apart from the five and the wiring strategy.
EPONYMOUS: Mapping[str, type[Rule]] = {
    "donchian_channel_breakout": DonchianChannelBreakout,
    "donchian_fade_chop": DonchianFadeChop,
}
