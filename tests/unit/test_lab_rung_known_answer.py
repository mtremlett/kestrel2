"""The known-answer kit (the 21 Nov plan, R-RUNNER-496): a goal per rung and one overall, every
rung of the ladder's map holding a row of known answers that passes, read from the map as
`ladder.rungs_built` reads it, never a hand list. The rows are the plan's cases on fixture data
through the real ladder: a paid edge (+0.4% a trade after costs) goes forward on every rung; a
cost churner, one lucky year and noise are refused, each by the rung that should; a line too thin
alone is judged on its basket, not faulted; a look-ahead cheat is refused by the future-blind
check. Kit a and b on the breakout are in `test_lab_ladder_known_answer.py`."""

from __future__ import annotations

import json
import math
import random
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date, timedelta
from decimal import Decimal
from functools import cache
from typing import Any, ClassVar

import pytest
import test_lab_ladder_known_answer as crowds
import test_lab_spec_blind as blind
from test_lab_ladder import SPY, _door
from test_lab_rung import _bars, _walk

from desk.lines import LINES, Line
from desk.store import Bar
from desk.strategy import CLOSES, STRATEGIES, Declared, Rule, Timeframe
from lab import ladder, ladder_map, ladder_sets, rulebook, tape, verdict
from lab.cell import Cell
from lab.published import PUBLISHED
from lab.published_case import FIRST, Published, known
from lab.published_epon import EPONYMOUS_PUBLISHED
from lab.verdict_parts import goes

NAMES = "3LGO 2MU SMGB IITU VHYG 5QQQ ISF VUSA SGLN VUAG EQQQ IB1T AAPL TSLA NVDA AMD".split()
SIXTEEN = [next(line for line in LINES if line.symbol == name) for name in NAMES]
US = SIXTEEN[-4:]  #: the churner's lines, beside SPY
DAYS = 6200  #: 2010 to the end of 2026: the window's last five whole years (2021-25) are folded
LUCKY = 2023  #: case e's one year of profit
DART = 0.1  #: the drift-rider's chance a day of going in, or out
Rows = Sequence[Mapping[str, Any]]
BOOK = frozenset(rulebook.rules())  #: the book as the desk holds it, read before any plant


@dataclass(frozen=True)
class Known:
    """One row of the kit: on every line of the case, the rung (a row key of the ladder's, or
    `answer`, the one rule over them) gives `want`, and its reason says `says`."""

    rung: int  #: its number in the ladder's map; 0 is the one answer, no rung's
    case: str
    key: str
    want: str
    why: str
    says: str = ""


KIT = (
    Known(0, "churner", "answer", "FAIL", "d: the cost churner is refused"),
    Known(0, "lucky", "answer", "FAIL", "e: one lucky year is refused"),
    Known(0, "thin", "answer", "THIN", "f: a line too thin alone is THIN, never a fault"),
    Known(1, "thin", "first", "THIN", "f: too few trades to pass or to fail", "30 trades"),
    Known(2, "churner", "costs", "FAIL", "d: a gross edge a tenth of its costs", "0.1 times"),
    Known(10, "lucky", "folds", "FAIL", "e: its worst year is not its lucky one", "2022"),
    Known(10, "thin", "folds", "PASS", "f: judged on the basket", "over 16 lines"),
    Known(0, "paid", "answer", "PASS", "a: the paid edge goes forward on every rung run"),
    Known(1, "paid", "first", "PASS", "1,100 trades of a planted edge are heard"),
    Known(1, "noise", "first", "FAIL", "b: noise after costs earns nothing"),
    Known(2, "paid", "costs", "PASS", "the edge holds to over twice its costs"),
    Known(3, "paid", "ci", "PASS", "the interval of the mean gain lies above nothing"),
    Known(3, "churner", "ci", "FAIL", "the interval lies below nothing"),
    Known(4, "paid", "market", "PASS", "it earns beyond its market's moves", "SPY's moves"),
    Known(4, "churner", "market", "FAIL", "it loses beyond its market's moves", "SPY's moves"),
    Known(5, "paid", "regimes", "PASS", "it earns in both regime windows"),
    Known(5, "churner", "regimes", "FAIL", "it loses in both", "first window FAIL"),
    Known(6, "paid", "market", "PASS", "beyond its own line's moves", "its own line's"),
    Known(6, "noise", "market", "FAIL", "noise earns nothing beyond them", "its own line's"),
    Known(7, "paid", "deflated", "PASS", "its Sharpe survives the trials it was one of"),
    Known(7, "churner", "deflated", "FAIL", "a Sharpe of nothing", "0.00"),
    Known(8, "paid", "cpcv", "PASS", "chosen in-sample and kept out of it"),
    Known(8, "noise", "cpcv", "FAIL", "noise is not chosen where it is not kept"),
    Known(9, "paid", "shuffle", "PASS", "the days in order earn more than shuffled", "shuffles"),
    Known(10, "paid", "folds", "PASS", "every one of the five years earns"),
    Known(11, "paid", "ci", "PASS", "the ci's PASS is held to the block bootstrap's"),
    Known(12, "paid basket", "retail", "PASS", "the basket beats holding its market"),
    Known(12, "noise basket", "retail", "FAIL", "a basket of noise does not"),
    Known(9, "drift", "shuffle", "FAIL", "random entries on a rising line", "share among them"),
    Known(6, "drift", "market", "FAIL", "they earn only their own line's rise", "its own line's"),
    Known(13, "clone", "liquidity", "PASS", "a deep line takes under 1% of its day", "capacity"),
    Known(
        13,
        "one-share paid",
        "liquidity",
        "FAIL",
        "one share a day cannot take its trades",
        "volume on",
    ),
    Known(14, "clone", "fit", "FAIL", "a clone of the desk's breakout adds no new return", "FAIL:"),
    Known(14, "paid", "fit", "PASS", "the churner moves with none of the desk's five", "new:"),
    Known(15, "paid", "late", "FAIL", "paid only on the next open, gone a bar late", "a bar late"),
    Known(
        15, "crowd", "late", "PASS", "a crowd's spells last: still paid a bar late", "a bar late"
    ),
)


class Cheat:
    """Case c: in the market whenever TOMORROW's close is higher than today's."""

    def __init__(self, series: Sequence[Bar]) -> None:
        self._tomorrow = {a.day: b.close for a, b in zip(series, series[1:], strict=False)}

    def step(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the Rule interface
        return self._tomorrow.get(bar.day, bar.close) > bar.close


class Churner:
    """In the market every other bar: case d on a line with a tiny gross edge, case a on one
    that pays it on each held day."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, CLOSES)

    def step(self, bar: Bar, holding: bool) -> bool:  # noqa: ARG002 - the Rule interface
        return not holding


class Dart:
    """The drift-rider: in or out at random, a chance of a tenth a day, by the day's own seed.
    On a rising line it earns, and only what holding the line earns: no edge of its own."""

    declared: ClassVar[Declared] = Declared(Timeframe.DAILY, None, LINES, CLOSES)

    def step(self, bar: Bar, holding: bool) -> bool:
        return holding != _flip(bar.day)


def _flip(day: date) -> bool:
    return random.Random(day.toordinal()).random() < DART  # noqa: S311 - a repeatable coin


def _darts(days: int) -> tuple[tuple[int, int | None], ...]:
    """The drift-rider's known trades on `days` bars from the cases' first day, worked from
    its coin alone, never by running it."""
    out: list[tuple[int, int | None]] = []
    bought: int | None = None
    for n in (n for n in range(days) if _flip(FIRST + timedelta(n))):
        if bought is None:
            bought = n
        else:
            out.append((bought, n))
            bought = None
    return (*out, *([(bought, None)] if bought is not None else []))


def _rising(seed: int) -> tuple[Bar, ...]:
    """A line flat, then rising 0.1% a day under 1% of noise through the 2,400 days judged, 100
    to about 1,100: a holder at random is paid the rise, at a price the desk's room can buy."""
    rng, closes = random.Random(seed), [100.0]  # noqa: S311 - a repeatable test walk
    while len(closes) < DAYS:
        rise = 1.001 if len(closes) >= DAYS - 2400 else 1.0
        closes.append(closes[-1] * (rise + rng.gauss(0, 0.01)))
    return _bars(closes)[-2400:]


def _drift(seed: int) -> tuple[Bar, ...]:
    """A line rising 0.03% a day under a little noise: a tiny gross edge for any holder."""
    rng, closes = random.Random(seed), [100.0]  # noqa: S311 - a repeatable test walk
    while len(closes) < DAYS:
        closes.append(closes[-1] * (1.0003 + rng.gauss(0, 0.002)))
    return _bars(closes)[-2400:]


def _paid(seed: int) -> tuple[Bar, ...]:
    """Case a's line: from each odd bar's open to the next it gains 0.75%, from each even bar's
    it gives it back, under 5.5% of noise a day, pulled back towards 100. The churner, bought at
    bar 0's close (bar 1's open) and out a bar later, is paid the gain on every trade."""
    rng, opens = random.Random(seed), [100.0]  # noqa: S311 - a repeatable test walk
    while len(opens) < 4801:
        tilt = 0.0075 if len(opens) % 2 == 0 else -0.0075  #: opens[k] to opens[k + 1]
        pull = 0.05 * math.log(opens[-1] / 100)
        opens.append(opens[-1] * (1 + tilt + rng.gauss(0, 0.055) - pull))
    out = []
    for k in range(4800):
        o, c = Decimal(f"{opens[k]:.2f}"), Decimal(f"{opens[k + 1]:.2f}")
        high, low = max(o, c) * Decimal("1.005"), min(o, c) * Decimal("0.995")
        out.append(Bar(date(2013, 12, 1) + timedelta(k), o, high, low, c, 1))
    return tuple(out)


#: The desk's breakout copied under another name, not a subclass (which is its family, a
#: variant): a rule that only repeats one the book already trades.
Clone = type(
    "Clone",
    (),
    {
        k: v
        for k, v in vars(STRATEGIES["breakout_20_10"]).items()
        if k not in ("__dict__", "__weakref__", "__module__", "__qualname__")
    },
)


def _deep_as(bars: Sequence[Bar]) -> tuple[Bar, ...]:
    """The bars of a line trading a million shares a day, deep enough for any trade of the desk."""
    return tuple(replace(bar, volume=1_000_000) for bar in bars)


def _deep() -> Mapping[Line, Sequence[Bar]]:
    """The breakout's planted edge on the four US lines, each trading a million shares a day."""
    return {line: _deep_as(_walk(n, 0.012, 0.012, days=3100)) for n, line in enumerate(US, 1)}


def _lucky() -> Mapping[Line, Sequence[Bar]]:
    """A breakout that loses a little every year but one, and earns its whole profit there."""
    pushes = [0.03 if year == LUCKY else -0.003 for year in range(2010, 2027)]
    return {line: _walk(n, *pushes, days=365)[-2400:] for n, line in enumerate(SIXTEEN, 1)}


def _thin() -> Mapping[Line, Sequence[Bar]]:
    """The breakout's edge on sixteen lines, AMD holding only its last 2,000 days of it."""
    walks: dict[Line, Sequence[Bar]] = {
        line: _walk(n, 0.012, 0.012, days=DAYS // 2)[-2400:] for n, line in enumerate(SIXTEEN)
    }
    return walks | {US[-1]: walks[US[-1]][-2000:]}


def _noise() -> Mapping[Line, Sequence[Bar]]:
    """The breakout on sixteen walks with nothing planted."""
    return {line: _walk(n, 0, 0, days=DAYS // 2)[-2400:] for n, line in enumerate(SIXTEEN, 1)}


CASES: dict[str, tuple[str, Callable[[], Mapping[Line, Sequence[Bar]]]]] = {
    "paid": ("churner", lambda: {line: _deep_as(_paid(n)) for n, line in enumerate(US, 1)}),
    "churner": ("churner", lambda: {line: _drift(n) for n, line in enumerate(US, 1)}),
    "lucky": ("breakout_20_10", _lucky),
    "thin": ("breakout_20_10", _thin),
    "noise": ("breakout_20_10", _noise),
    "drift": ("dart", lambda: {line: _rising(n) for n, line in enumerate(US, 1)}),
    "clone": ("clone", _deep),
    "one-share paid": ("churner", lambda: {line: _paid(n) for n, line in enumerate(US, 1)}),
    "crowd": (
        "crowd",
        lambda: {line: crowds._crowds(n, crowds.RISE) for n, line in enumerate(US, 1)},
    ),
}


def plant(patch: pytest.MonkeyPatch) -> None:
    """The kit's planted rules in the book, each with its own known answers, so the ladder's
    door lets them in: the churner, the drift-rider, the clone and the crowd."""
    book: dict[str, type[Rule]] = {
        **rulebook.rules(),
        "churner": Churner,
        "dart": Dart,
        "clone": Clone,
    }
    patch.setattr(rulebook, "rules", lambda folder=None: book)  # noqa: ARG005
    churns = known("in on bars 0, 2 and 4", [10] * 5, ((0, 1), (2, 3), (4, None)))
    patch.setitem(EPONYMOUS_PUBLISHED, "churner", Published("the kit's churner", (churns,)))
    darts = known("its coin's days", [10] * 60, _darts(60))
    patch.setitem(EPONYMOUS_PUBLISHED, "dart", Published("the kit's drift-rider", (darts,)))
    real = tape.code_of_rule  #: the test module is not under the code's root: keyed by name
    patch.setitem(EPONYMOUS_PUBLISHED, "clone", PUBLISHED["breakout_20_10"])
    named = {"churner": "planted", "clone": "planted", "dart": "dart"}
    patch.setattr(tape, "code_of_rule", lambda s: named.get(s) or real(s))
    crowds._plant(patch)  #: the crowd (`test_lab_ladder_known_answer.py`), the edge that lasts


@pytest.fixture(scope="module")
def judged(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Callable[[str], Rows]]:
    """Each case's rows from the real ladder, run once for the module: a basket case is its
    set's basket row, read with the retail rung (EASED); the churner is planted in the book
    with its own known answers, so the ladder's door lets it in."""
    with pytest.MonkeyPatch.context() as patch:
        plant(patch)

        @cache
        def rows(case: str) -> Rows:
            name, basket = case.removesuffix(" basket"), case.endswith(" basket")
            rule, make = CASES[name]
            walks = make()
            spy = _walk(99, 0, 0, days=DAYS // 2)
            door, pounds = _door(dict(walks) | {SPY: spy}), {bar.day: Decimal("0.8") for bar in spy}
            todo = [Cell(rule, line, ladder.START, ladder.END) for line in walks]
            patch.setattr(verdict, "EASED", basket or name == "drift")  #: as EPON runs it
            if basket:  #: the US lines, beside SPY: a proxied London line's US days are not ISF's
                walks = {line: bars for line, bars in walks.items() if line in US}
                todo = [Cell(rule, line, ladder.START, ladder.END) for line in walks]
                return ladder_sets.baskets(door, pounds, todo, [rule], ladder.FIRST)
            home = tmp_path_factory.mktemp(name)
            ladder.run(home, door, pounds, todo)
            lines = (home / "ladder" / "set1.jsonl").read_text().splitlines()
            got = [json.loads(line) for line in lines]
            return got[-1:] if name == "thin" else got  #: case f is AMD's row alone

        yield rows


def _failed(row: Known, rows: Rows) -> str:
    """Why the row's known answer is not given, or nothing when it is on every line."""
    if not rows or any("rungs" not in r for r in rows):
        return f"no judged row: {[r.get('error') or r.get('refused') for r in rows][:2]}"
    for r in rows:
        said = ["", ""] if row.key == "answer" else r["rungs"].get(row.key, ["absent", ""])
        got = r["answer"] if row.key == "answer" else said[0]
        if got != row.want or row.says not in said[1]:
            return f"{r['cell'][1]}: {row.key} {got}, not {row.want}: {said[1][:120]}"
    return ""


def _map() -> dict[int, str]:
    """The ladder's map of rungs, number to name, read from `lab/ladder_map.py` as `rungs_built`
    reads it (pattern 18: the registry, never a list kept here)."""
    rows = [line.strip() for line in ladder_map.rows()]
    return {int(r.split()[0]): r.split(":")[0] for r in rows}


def test_every_rung_of_the_map_has_a_known_answer_row_that_passes(
    judged: Callable[[str], Rows],
) -> None:
    """THE GOAL, per rung and overall: every rung the map registers holds a row of the kit, and
    every row passes; the failure lists each rung that lacks one or fails one."""
    rungs, owed = _map(), []
    assert len(rungs) == ladder.rungs_built()[1], "the map read is not the ladder's"
    for number, name in sorted(rungs.items()):
        mine = [row for row in KIT if row.rung == number]
        wrong = [f"{row.case}: {why}" for row in mine if (why := _failed(row, judged(row.case)))]
        if not mine or wrong:
            owed.append(f"{name}: " + ("no known-answer row" if not mine else "; ".join(wrong)))
    assert not owed, "rungs still owed a passing known answer:\n" + "\n".join(owed)


@pytest.mark.parametrize("row", [row for row in KIT if row.rung == 0], ids=lambda r: r.case)
def test_each_case_gives_its_one_answer(judged: Callable[[str], Rows], row: Known) -> None:
    """The one answer over the rungs, case by case: the overall goal's half of the table."""
    assert not (why := _failed(row, judged(row.case))), why


def test_c_a_look_ahead_cheat_is_refused_by_the_future_blind_check() -> None:
    """The check every rule of the book passes (`test_lab_spec_blind.py`) refuses the cheat,
    and every rule the ladder can be handed is one it checks."""
    assert blind._blind(Cheat, blind._bars(), seed=3), "the cheat went unseen"
    assert set(blind.RULES) >= BOOK


def test_the_churners_edge_is_real_and_the_lucky_year_is_the_whole_profit(
    judged: Callable[[str], Rows],
) -> None:
    """Case d's gross edge is above nothing, only small; case e's whole history earns."""
    assert all("the edge holds to 0.1 times" in r["rungs"]["costs"][1] for r in judged("churner"))
    lucky = judged("lucky")
    assert all("above nothing" in r["rungs"]["first"][1] for r in lucky), "the whole is profit"
    assert all(f"folds, {LUCKY}:" not in r["rungs"]["folds"][1] for r in lucky)


def test_the_paid_edge_goes_forward_on_every_line_and_no_settings_block_it(
    judged: Callable[[str], Rows],
) -> None:
    """L17's gate: with plateau and reproduce judged, no rung is unrun on the planted edge, and
    a rule with no settings is NOT APPLICABLE for plateau, never blocked by it. On a line deep
    enough to take its trades its one rung short of going forward is the one-bar-late rung (E13),
    as it is paid only on the next open; on a line of one share a day liquidity (#2230) holds it
    too. The crowd goes forward (`test_lab_ladder_known_answer.py`)."""
    deep, thin = judged("paid"), judged("one-share paid")
    held = [
        {k for k, (a, _) in row["rungs"].items() if a != "PASS" and k not in verdict.GRADED}
        for row in [*deep, *thin]
    ]  #: a graded rung's mark is the scorecard's, never a hold
    assert all(row["unrun"] == {} and row["answer"] == "PASS" for row in [*deep, *thin])
    assert deep and thin and not any(goes(row) for row in [*deep, *thin])
    assert held == [{"late"}] * len(deep) + [{"liquidity", "late"}] * len(thin), held
    assert all(row["rungs"]["plateau"][1].startswith("NOT APPLICABLE") for row in [*deep, *thin])
