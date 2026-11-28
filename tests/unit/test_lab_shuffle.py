"""The ladder's shuffle rung: an edge in the order of days beats every shuffle of them."""

from __future__ import annotations

import random
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from test_lab_rung import POUND, TEN_K, _walk

from desk.lines import LINES
from desk.store import Bar
from lab import cell, reproduce, shuffle, tape, trials
from lab.cell import Cell
from lab.reproduce import Figure, Fill, Found, Hand, Measure, Reproduction, Stated

VUSA = next(line for line in LINES if line.symbol == "VUSA")


def _share(*pushes: float, made: tuple[Reproduction, ...] = ()) -> Decimal:
    bars = _walk(1, *pushes, days=3000)
    c = Cell("breakout_20_10", VUSA, bars[0].day, bars[-1].day)
    return shuffle.share(c, bars, TEN_K, POUND, made)


def test_a_planted_edge_is_in_the_order_of_days_and_the_same_trial_is_shuffled_the_same() -> None:
    assert shuffle.SHUFFLES == 100
    assert _share(0.012) == _share(0.012) == Decimal(1) / 101
    assert _share(0.0) > shuffle.SHARE, "a walk with no edge is among the best of its own shuffles"


def test_a_rule_with_an_authors_figure_is_shuffled_with_its_reproduction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    #: the blind re-review (R-RUNNER-188): each shuffle was judged with no reproduction, so a
    #: rule with an author's figure on file was refused at the last rung and never judged
    bars = _walk(1, 0.012, days=3000)
    c = Cell("breakout_20_10", VUSA, bars[0].day, bars[-1].day)
    stated = Stated(Measure.TRADES, Decimal(1), Decimal(0))
    figure = Figure(
        c.strategy, "an author", VUSA, c.start, c.end, Fill.CLOSE, (stated,), Hand.AUTHOR
    )
    made = Reproduction(
        figure, cell.key(c, bars).rung("lab.reproduce"), (Found(stated, Decimal(1)),)
    )
    monkeypatch.setattr(reproduce, "FIGURES", (figure,))
    assert _share(0.012, made=(made,)) == Decimal(1) / 101


def test_a_cell_ending_before_later_bars_draws_none_of_their_days(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """T2, future-blind (canon B3): a day after the cell's end, planted as a hundredfold rise, is
    never shuffled into the cell's window; only the days the cell is shown are drawn."""
    walk = _walk(1, 0.0, days=3000)
    end = walk[1999].day
    later = walk[2500]
    big = Bar(later.day, later.open * 100, later.high * 100, later.low * 100, later.close * 100, 1)
    bars = (*walk[:2500], big, *walk[2501:])
    c = Cell("breakout_20_10", VUSA, bars[0].day, end)
    seen: list[Sequence[Bar]] = []
    real = shuffle._t

    def spied(c: Cell, b: Sequence[Bar], *rest: Any) -> Decimal | None:
        seen.append(b)
        return real(c, b, *rest)

    monkeypatch.setattr(shuffle, "_t", spied)
    shuffle.share(c, bars, TEN_K, POUND, ())
    top = max(bar.close for bar in bars if bar.day <= end)
    for history in seen[1:]:
        assert max(bar.close for bar in history if bar.day <= end) < top * 20, "a later day drawn"


def _full(c: Cell, bars: Sequence[Bar]) -> int:
    """The shuffles as good as the trial, itself among them, over all SHUFFLES: the rung as it
    was before it stopped early, written again here as the reference."""
    own = shuffle._t(c, bars, TEN_K, POUND, ())
    assert own is not None
    rng, shown = random.Random(trials.name(c)), cell.shown(c, bars)  # noqa: S311
    moves, as_good = shuffle._moves(shown), 1
    for _ in range(shuffle.SHUFFLES):
        rng.shuffle(moves)
        got = shuffle._t(c, shuffle._history(shown, moves), TEN_K, POUND, ())
        as_good += got is not None and got >= own
    return as_good


@pytest.mark.parametrize(("seed", "push"), [(1, 0.012), (1, 0.0)])
def test_a_shuffle_stopped_once_it_cannot_pass_answers_as_the_full_one(
    seed: int, push: float, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S3: at six of 101 as good the trial cannot pass (five or fewer passes), so the rung stops
    there; the answer is the full run's, and a failing share is said as 'at least 6 of 101'."""
    bars = _walk(seed, push, days=3000)
    c = Cell("breakout_20_10", VUSA, bars[0].day, bars[-1].day)
    full = _full(c, bars)
    runs, real = [0], shuffle._t

    def counted(*args: Any) -> Decimal | None:
        runs[0] += 1
        return real(*args)

    monkeypatch.setattr(shuffle, "_t", counted)
    got = shuffle.share(c, bars, TEN_K, POUND, ())
    passes = Decimal(full) / (shuffle.SHUFFLES + 1) <= shuffle.SHARE
    assert (got <= shuffle.SHARE) == passes
    if passes:
        assert got == Decimal(full) / (shuffle.SHUFFLES + 1) and runs[0] == shuffle.SHUFFLES + 1
        assert shuffle.said(got) == f"{got:.3f}"
    else:
        assert got == Decimal(6) / (shuffle.SHUFFLES + 1) and runs[0] < shuffle.SHUFFLES + 1
        assert shuffle.said(got) == "at least 6 of 101"


@pytest.mark.parametrize(
    ("better", "runs", "share"), [(4, 101, "0.050"), (5, 7, "at least 6 of 101")]
)
def test_five_as_good_passes_the_sixth_fails_and_stops_there(
    better: int, runs: int, share: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S3 at its edge: four shuffles as good (ties among them) and the trial makes five of 101,
    which passes after all 100; a fifth makes six and the rung stops there. A shuffle with no
    standard errors (None) is never counted."""
    ties = [Decimal(1 + n % 2) for n in range(better)]  #: as good: equal, then better, by turns
    told = iter([Decimal(1), None, *ties, *[Decimal(0)] * 100])
    asked = [0]

    def scripted(*_: Any) -> Decimal | None:
        asked[0] += 1
        return next(told)

    monkeypatch.setattr(shuffle, "_t", scripted)
    bars = _walk(1, 0.0, days=300)
    got = shuffle.share(
        Cell("breakout_20_10", VUSA, bars[0].day, bars[-1].day), bars, TEN_K, POUND, ()
    )
    assert shuffle.said(got) == share and asked[0] == runs


def test_a_trial_of_under_two_trades_is_said_as_run_no_shuffles() -> None:
    assert shuffle.said(Decimal(1)) == "1 (under two trades: no shuffle run)"


def test_a_cells_shuffles_are_one_tape_read_back_with_no_simulation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S5: a cell's resampled histories are kept as one tape beside its own, not a file each,
    and a shuffle judged again under the same tapes simulates nothing; the share is the one
    given with no tapes at all."""
    bars = _walk(1, 0.012, days=3000)
    c = Cell("breakout_20_10", VUSA, bars[0].day, bars[-1].day)
    bare = shuffle.share(c, bars, TEN_K, POUND, ())
    runs, engine = [0], cell.run

    def counted(*args: Any) -> cell.Record:
        runs[0] += 1
        return engine(*args)

    monkeypatch.setattr(cell, "run", counted)
    with tape.on(tmp_path):
        first = shuffle.share(c, bars, TEN_K, POUND, ())
        cold = runs[0]
        again = shuffle.share(c, bars, TEN_K, POUND, ())
    assert bare == first == again == Decimal(1) / 101
    assert cold == shuffle.SHUFFLES + 1 and runs[0] == cold, "the second shuffle simulated"
    assert len(list(tmp_path.glob("*.tape"))) == 1 and len(list(tmp_path.glob("*.shuffles"))) == 1


def test_a_kept_shuffle_is_never_served_for_another_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S5: each kept entry answers only the history that made it; shuffled in another order
    (here a new seed) under the same tapes, every entry is run again and the share is the one
    that order gives with no tapes at all."""
    bars = _walk(1, 0.012, days=3000)
    c = Cell("breakout_20_10", VUSA, bars[0].day, bars[-1].day)
    with tape.on(tmp_path):
        kept = shuffle.share(c, bars, TEN_K, POUND, ())
    monkeypatch.setattr(trials, "name", lambda c: f"another order for {c}")
    other = shuffle.share(c, bars, TEN_K, POUND, ())
    runs, engine = [0], cell.run

    def counted(*args: Any) -> cell.Record:
        runs[0] += 1
        return engine(*args)

    monkeypatch.setattr(cell, "run", counted)
    with tape.on(tmp_path):
        assert shuffle.share(c, bars, TEN_K, POUND, ()) == other
    assert runs[0] == shuffle.SHUFFLES and kept == Decimal(1) / 101  #: all but the trial's own


def test_a_shuffle_broken_off_keeps_the_resamples_it_finished(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S5: a pass stopped mid-shuffle keeps what it ran, so the next runs only the rest."""
    bars = _walk(1, 0.012, days=3000)
    c = Cell("breakout_20_10", VUSA, bars[0].day, bars[-1].day)
    real, asked = shuffle._t, [0]

    def broken(*args: Any) -> Decimal | None:
        asked[0] += 1
        if asked[0] > 51:  #: the trial and fifty shuffles done
            raise KeyboardInterrupt
        return real(*args)

    with tape.on(tmp_path):
        monkeypatch.setattr(shuffle, "_t", broken)
        with pytest.raises(KeyboardInterrupt):
            shuffle.share(c, bars, TEN_K, POUND, ())
        monkeypatch.setattr(shuffle, "_t", real)
        runs, engine = [0], tape._ON[-1][1]

        def counted(*args: Any) -> cell.Record:
            runs[0] += 1
            return engine(*args)

        tape._ON[-1] = (tmp_path, counted)  #: the engine the tapes keep, counted; popped at the end
        assert shuffle.share(c, bars, TEN_K, POUND, ()) == Decimal(1) / 101
    assert runs[0] == shuffle.SHUFFLES - 50
