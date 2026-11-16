"""risk - WHERE THE BOOK STANDS AGAINST ITS LOSS AND ORDER-RATE LIMITS (canon B1). The book's
standing is data in: the pounds lost today and this week, and the new lines entered today. The
limits are numbers in desk.orders.Settings, beside the capital; this module owns none of them.
The pre-trade gate refuses a new entry past either, and the paper desk alerts on a loss limit."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Standing:
    """The book's losses so far, in pounds (0 when it is up), and the new lines it entered today."""

    day_loss: Decimal  #: since the day's open
    week_loss: Decimal  #: since the week's open
    new_lines: int

    def __post_init__(self) -> None:
        if min(self.day_loss, self.week_loss) < 0 or self.new_lines < 0:
            raise ValueError(f"a standing of {self}: losses and new lines are never below nothing")


def loss_limit(standing: Standing, capital: Decimal, day: Decimal, week: Decimal) -> str | None:
    """Which loss limit the book has reached (its loss at or past that share of the capital),
    in words, or None while it is under both."""
    for name, lost, share in (("day", standing.day_loss, day), ("week", standing.week_loss, week)):
        if lost >= capital * share:
            return (
                f"the {name}-loss limit: {lost} pounds lost this {name}, the limit "
                f"{share:.0%} of the capital of {capital} ({capital * share} pounds)"
            )
    return None
