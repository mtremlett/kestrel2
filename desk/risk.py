"""risk - WHERE THE BOOK STANDS AGAINST ITS LOSS AND ORDER-RATE LIMITS (canon B1). The book's
standing is data in: the pounds lost today and this week, and the new lines entered today. The
limits are numbers in desk.orders.Settings, beside the capital; this module owns none of them.
The pre-trade gate refuses a new entry past either, and the paper desk alerts on a loss limit."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Standing:
    """The book's losses so far, in pounds (0 when it is up), and the new lines it entered today."""

    day_loss: Decimal  #: the last published session's loss
    week_loss: Decimal  #: since the week's open
    new_lines: int

    def __post_init__(self) -> None:
        if min(self.day_loss, self.week_loss) < 0 or self.new_lines < 0:
            raise ValueError(f"a standing of {self}: losses and new lines are never below nothing")


def loss_limit(standing: Standing, capital: Decimal, day: Decimal, week: Decimal) -> str | None:
    """Which loss limit the book has reached (its loss at or past that share of the capital),
    in words, or None while it is under both."""
    for name, lost, share, when in (
        ("day", standing.day_loss, day, "in the last session"),
        ("week", standing.week_loss, week, "this week"),
    ):
        if lost >= capital * share:
            return (
                f"the {name}-loss limit: {lost} pounds lost {when}, the limit "
                f"{share:.0%} of the capital of {capital} ({capital * share} pounds)"
            )
    return None


def underlying_limit(
    exposure: Mapping[str, Decimal], underlying: str, added: Decimal, capital: Decimal, cap: Decimal
) -> str | None:
    """Whether a buy would take one underlying market over its share of the capital, in words,
    or None. exposure is the pounds the book controls per underlying (a 3x line counts three
    times its value); added is the buy's own, at its leverage."""
    total = exposure.get(underlying, Decimal(0)) + added
    if total > capital * cap:
        return (
            f"{total} pounds of {underlying} exposure, over {cap:.0%} of the capital of "
            f"{capital} ({capital * cap} pounds)"
        )
    return None


def _mean(xs: tuple[float, ...]) -> float:
    return sum(xs) / len(xs)


def volatility(returns: tuple[float, ...]) -> Decimal:
    """The standard deviation of a line's daily returns (needs two or more days)."""
    if len(returns) < 2:
        raise ValueError(f"volatility needs two or more daily returns, got {len(returns)}")
    mean = _mean(returns)
    return Decimal(str((sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)) ** 0.5))


def correlation(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    """Pearson correlation of two lines' daily returns over the same days; a flat line has none."""
    if len(a) != len(b) or len(a) < 2:
        raise ValueError(
            f"correlation needs equal runs of two or more days, got {len(a)}, {len(b)}"
        )
    ma, mb = _mean(a), _mean(b)
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b, strict=True))
    spread = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    if spread == 0:
        raise ValueError("a line whose returns never move has no correlation")
    return float(cov / spread)


def correlated_with(
    returns: tuple[float, ...], held: dict[str, tuple[float, ...]], cap: float
) -> str | None:
    """Which held line the candidate moves with above the cap, in words, or None. The cap is a
    correlation between -1 and 1; a candidate correlated past it is not entered beside that line."""
    for symbol, other in held.items():
        rho = correlation(returns, other)
        if rho > cap:
            return f"correlated {rho:.2f} with held {symbol}, above the cap of {cap:.2f}"
    return None


def shares_for_risk(risk: Decimal, price: Decimal, daily_vol: Decimal) -> int:
    """Shares whose one-day typical move (price x volatility) is the pounds of risk allowed:
    a more volatile line gets the smaller size."""
    if risk <= 0 or price <= 0 or daily_vol <= 0:
        raise ValueError(
            f"sizing needs positive risk, price and volatility: {risk}, {price}, {daily_vol}"
        )
    return int(risk / (price * daily_vol))
