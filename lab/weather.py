"""weather - THE MARKET WEATHER (REG-01), first layer: each session's trend state, named from
the closes known at that session's close and never from a later one (canon B3).

A day is `up` when its close is above the mean of the last WINDOW closes, itself included,
`down` when it is at or below it, and `warming` until WINDOW closes have been seen: a label
is never guessed from less. The label of day T reads bars up to T only, so cutting the history
after T changes none of the labels up to T (the future-blind test in
`tests/unit/test_lab_weather.py`). The names are one plain word each, as `lab/regime.py` asks.

The trend is the baseline. Realised volatility, drawdown depth and breadth are built below
but wired into no verdict, each layer only on an out-of-sample win against trend alone, with
the trial count recorded (canon B6).
"""

from __future__ import annotations

import json
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from desk.store import Bar

#: The trend's look-back in sessions: the long average the desk's published rules also use.
WINDOW = 200
UP, DOWN, WARMING = "up", "down", "warming"


def trend(bars: Sequence[Bar]) -> dict[date, str]:
    """Each bar's day under its trend state, oldest bar first, by that day's close and the
    WINDOW closes up to it."""
    days = [bar.day for bar in bars]
    if len(set(days)) != len(days) or days != sorted(days):
        raise ValueError("bars must be one per day, oldest first, to be named in order")
    closes = [bar.close for bar in bars]
    named: dict[date, str] = {}
    total = Decimal(0)
    for n, close in enumerate(closes):
        total += close
        if n >= WINDOW:
            total -= closes[n - WINDOW]
        if n + 1 < WINDOW:
            named[days[n]] = WARMING
        else:
            named[days[n]] = UP if close * WINDOW > total else DOWN
    return named


#: The volatility layer: the look-back for realised volatility, and the history it is ranked in.
VOL_WINDOW, VOL_RANK = 20, 252
CALM, STORMY = "calm", "stormy"


def volatility(bars: Sequence[Bar]) -> dict[date, str]:
    """Each bar's day as `stormy` when the standard deviation of the last VOL_WINDOW daily
    returns is above the median of the VOL_RANK values before it, else `calm`; `warming`
    until that many earlier values exist. Day T reads closes up to T only (canon B3). Built
    but wired into no verdict until it wins out of sample against trend alone (canon B6)."""
    trend(bars)  # the one check that bars are one per day, oldest first
    closes = [bar.close for bar in bars]
    returns = [closes[n] / closes[n - 1] - 1 for n in range(1, len(closes))]
    vols = [
        Decimal(statistics.pstdev(returns[n - VOL_WINDOW : n]))
        for n in range(VOL_WINDOW, len(returns) + 1)
    ]
    named: dict[date, str] = {}
    for n, bar in enumerate(bars):
        i = n - VOL_WINDOW  # this day's volatility is vols[i], from the returns up to it
        if i < VOL_RANK:
            named[bar.day] = WARMING
        else:
            named[bar.day] = STORMY if vols[i] > statistics.median(vols[i - VOL_RANK : i]) else CALM
    return named


#: The drawdown layer: the look-back for the high a close is measured against, and how far
#: below that high is `deep`.
DD_WINDOW, DD_LIMIT = 252, Decimal("0.10")
SHALLOW, DEEP = "shallow", "deep"


def drawdown(bars: Sequence[Bar]) -> dict[date, str]:
    """Each bar's day as `deep` when its close is DD_LIMIT or more below the highest close of
    the last DD_WINDOW (itself included), else `shallow`; `warming` until DD_WINDOW closes
    have been seen. Day T reads closes up to T only (canon B3). Built but wired into no
    verdict until it wins out of sample against trend alone (canon B6)."""
    trend(bars)  # the one check that bars are one per day, oldest first
    closes = [bar.close for bar in bars]
    named: dict[date, str] = {}
    for n, bar in enumerate(bars):
        if n + 1 < DD_WINDOW:
            named[bar.day] = WARMING
        else:
            high = max(closes[n + 1 - DD_WINDOW : n + 1])
            named[bar.day] = DEEP if closes[n] <= high * (1 - DD_LIMIT) else SHALLOW
    return named


#: The layers that won on database long (canon B6), by name; empty until a recorded win, and a
#: layer is added only with its DECISIONS entry and trial count. Only the layers read from a
#: line's own bars may be named; breadth and macro are market-wide and are handed in, never
#: read from the cell's line.
JOINED: tuple[str, ...] = ()
_OWN_LAYERS = {"volatility": (volatility, CALM), "drawdown": (drawdown, SHALLOW)}


def named(bars: Sequence[Bar]) -> dict[date, str]:
    """Each day as `up` only when the trend is up and every JOINED layer reads its good label,
    `warming` when the trend or a joined layer is still warming, else `down`. Day T reads bars
    up to T only (canon B3)."""
    out = trend(bars)
    for layer in JOINED:
        read, good = _OWN_LAYERS[layer]
        for day, label in read(bars).items():
            if out[day] == WARMING or label == WARMING:
                out[day] = WARMING
            elif label != good:
                out[day] = DOWN
    return out


def followed(
    labels: Mapping[date, str], bars: Sequence[Bar], folds: int = 1
) -> list[dict[str, Decimal]]:
    """What followed each label (canon B6): per fold, the mean next-session return after a day
    of each label. The sessions are cut into `folds` contiguous slices, oldest first, so the
    worst fold can be reported beside the whole. A `warming` day has no label to score. The
    label of day T is paired with the return from T's close to the next close, never earlier."""
    trend(bars)  # the one check that bars are one per day, oldest first
    pairs = [
        (labels[a.day], b.close / a.close - 1)
        for a, b in zip(bars, bars[1:], strict=False)
        if labels[a.day] != WARMING
    ]
    out = []
    for k in range(folds):
        slice_ = pairs[k * len(pairs) // folds : (k + 1) * len(pairs) // folds]
        by_name: dict[str, list[Decimal]] = {}
        for name, ret in slice_:
            by_name.setdefault(name, []).append(ret)
        out.append({name: Decimal(sum(rets)) / len(rets) for name, rets in by_name.items()})
    return out


def edges(
    labels: Mapping[date, str], bars: Sequence[Bar], good: str, folds: int = 1
) -> list[Decimal]:
    """The layer's edge per fold (canon B6): the mean next-session return after days labelled
    `good` less the mean after every other labelled day. A layer joins the regime rung only
    if its worst fold beats trend alone's worst fold. A fold with no `good` day, or with only
    `good` days, has no edge to state and is refused, never read as zero."""
    out = []
    for k, fold in enumerate(followed(labels, bars, folds)):
        if good not in fold or len(fold) < 2:
            raise ValueError(f"fold {k} of {folds} has no {good!r} day or no other day to compare")
        rest = [ret for name, ret in fold.items() if name != good]
        out.append(fold[good] - Decimal(sum(rest)) / len(rest))
    return out


BROAD, NARROW = "broad", "narrow"


def breadth(lines: Mapping[str, Sequence[Bar]]) -> dict[date, str]:
    """Each day across the research universe as `broad` when more than half of the lines that
    have a trend state that day are `up`, else `narrow`; `warming` when no line has one yet.
    A day's label reads each line's closes up to that day only (canon B3). Built but wired
    into no verdict until it wins out of sample against trend alone (canon B6)."""
    states = [trend(bars) for bars in lines.values()]
    named: dict[date, str] = {}
    for day in sorted({day for state in states for day in state}):
        today = [state[day] for state in states if state.get(day, WARMING) != WARMING]
        if not today:
            named[day] = WARMING
        else:
            named[day] = BROAD if 2 * today.count(UP) > len(today) else NARROW
    return named


@dataclass(frozen=True)
class Contest:
    """A layer's worst-fold edge against trend alone's, and how many layers were tried."""

    layer: Decimal
    trend: Decimal
    trials: int

    @property
    def wins(self) -> bool:
        """The layer joins only if its worst fold beats trend alone's worst fold (canon B6)."""
        return self.layer > self.trend


def against_trend(
    labels: Mapping[date, str], good: str, bars: Sequence[Bar], folds: int, trials: int
) -> Contest:
    """The win-against-trend test: the layer's worst fold edge beside trend alone's, over the
    same bars and folds, with the count of layers tried so the luck can be judged."""
    return Contest(
        min(edges(labels, bars, good, folds)), min(edges(trend(bars), bars, UP, folds)), trials
    )


@dataclass(frozen=True)
class Entry:
    """One layer's contest, or why it could not be scored (never read as zero)."""

    layer: str
    contest: Contest | None
    why: str = ""


def contest(
    market: Sequence[Bar], lines: Mapping[str, Sequence[Bar]], folds: int = 5
) -> list[Entry]:
    """Run the win-against-trend test over `market` for each built layer with its good label
    (volatility calm, drawdown shallow, breadth broad over `lines`); the trials are the layers
    tried. A fold a layer cannot score is said so in `why`."""
    layers = [
        ("volatility", volatility(market), CALM),
        ("drawdown", drawdown(market), SHALLOW),
        ("breadth", breadth(lines), BROAD),
    ]
    out = []
    for name, labels, good in layers:
        try:
            out.append(Entry(name, against_trend(labels, good, market, folds, len(layers))))
        except ValueError as refusal:
            out.append(Entry(name, None, str(refusal)))
    return out


def write(folder: Path, contests: Sequence[Entry]) -> None:
    """Write weather.md and weather.json into `folder`: each layer's worst fold beside trend's,
    whether it joins, and the trials. PRE-REVIEW until a reviewer has read the numbers."""
    rows = []
    for e in contests:
        c = e.contest
        rows.append(
            {
                "layer": e.layer,
                "worst_fold": None if c is None else str(c.layer),
                "trend_worst_fold": None if c is None else str(c.trend),
                "joins": None if c is None else c.wins,
                "trials": None if c is None else c.trials,
                "unscored": e.why,
            }
        )
    lines = ["# Weather layers against trend (PRE-REVIEW)", ""]
    lines += ["| layer | worst fold | trend worst fold | joins | trials |", "|---|---|---|---|---|"]
    for r in rows:
        if r["joins"] is None:
            lines.append(f"| {r['layer']} | cannot score: {r['unscored']} | | no | |")
        else:
            verdict = "yes" if r["joins"] else "no"
            lines.append(
                f"| {r['layer']} | {r['worst_fold']} | {r['trend_worst_fold']} | {verdict} "
                f"| {r['trials']} |"
            )
    (folder / "weather.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    payload = {"status": "PRE-REVIEW", "layers": rows}
    (folder / "weather.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
