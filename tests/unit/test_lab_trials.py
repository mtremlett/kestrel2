"""The register of trials: every trial ever tried on a question, kept from batch to batch."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest
from test_lab_luck import DAY, _verdict

from desk import strategy
from desk.lines import LINES
from lab import deflated, luck, trials
from lab.cell import Cell, Key
from lab.rung import Verdict

END = date(2024, 1, 1)
AAPL, NVDA = (next(line for line in LINES if line.symbol == s) for s in ("AAPL", "NVDA"))
FIVE = tuple(Cell(rule, AAPL, DAY, END) for rule in strategy.STRATEGIES)
NAMES = [trials.name(c) for c in FIVE]
ASKED, LONDON = "which daily rule earns on the twenty lines", "does it earn in London too"
DOORS = (lambda r, q, _: trials.count(r, q), trials.enter, lambda r, q, _: trials.correct(r, q, []))


def _on(cell: Cell, seed: int, edge: float) -> Verdict:
    """The luck rung's own made-up trial, as this cell's verdict."""
    return replace(_verdict(seed, edge), key=Key(cell, "code", str(seed)))


WINNER = _on(FIVE[0], 9, 0.008)  #: it stands picked from eight trials, and not from nine


@pytest.fixture
def register(tmp_path: Path) -> Path:
    trials.start(tmp_path / "trials.jsonl")
    trials.ask(tmp_path / "trials.jsonl", ASKED)
    return tmp_path / "trials.jsonl"


def test_the_count_is_kept_from_batch_to_batch(register: Path) -> None:
    assert trials.count(register, ASKED) == 0 and trials.enter(register, ASKED, NAMES[:3]) == 3
    #: a later batch: two tried before, two new. Nothing is counted twice, nothing forgotten
    assert trials.enter(register, ASKED, iter(NAMES[1:])) == 5
    assert trials.enter(register, ASKED, []) == trials.count(register, ASKED) == 5
    #: a candidate that is no cell, tried and dropped, counts as much as any
    assert trials.enter(register, ASKED, ["a hand-drawn rule, dropped"] * 2) == 6
    #: another question keeps its own count, and a trial asked of both counts in each
    trials.ask(register, LONDON)
    assert trials.enter(register, LONDON, NAMES[:1]) == trials.count(register, LONDON) == 1
    #: the same rule on another line, or from another day, or to another, is another trial
    rule = FIVE[0].strategy
    more = [Cell(rule, NVDA, DAY, END), Cell(rule, AAPL, DAY, DAY), Cell(rule, AAPL, END, END)]
    assert trials.enter(register, ASKED, [trials.name(c) for c in more]) == 9
    assert trials.count(register, ASKED) == 9 and trials.count(register, LONDON) == 1
    lines = [json.loads(line) for line in register.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 13 and lines[:2] == [{"register": "trials"}, {"question": ASKED}]
    trial = f"{rule} on AAPL on {AAPL.venue}, 2020-01-01 to 2024-01-01"
    assert lines[2] == {"question": ASKED, "trial": trial}


def test_a_winner_is_corrected_for_every_trial_the_register_holds(register: Path) -> None:
    trials.enter(register, ASKED, NAMES[1:])
    with pytest.raises(ValueError, match=f"never entered.*{FIVE[0].strategy} on AAPL"):
        trials.correct(register, ASKED, [WINNER])
    trials.enter(register, ASKED, [NAMES[0], "dropped one", "dropped two", "dropped three"])
    (eight,) = trials.correct(register, ASKED, [WINNER])
    assert eight.passed and eight.trials == 8 and eight == luck.correct([WINNER], 7)[0]
    #: the register's count is the one every named rung is judged on
    assert deflated.read([eight]) == deflated.judge([WINNER], 7)
    #: a later batch tries one more and brings back the same winner alone: the count goes on
    trials.enter(register, ASKED, ["one more idea"])
    (nine,) = trials.correct(register, ASKED, [WINNER])
    assert not nine.passed and nine.trials == 9 and nine == luck.correct([WINNER], 8)[0]
    #: verdicts brought with it are counted once, as the trials they already are
    both = [_on(FIVE[1], 1, -0.01), WINNER]
    assert trials.correct(register, ASKED, both) == luck.correct(both, 7)
    with pytest.raises(ValueError, match="judged twice"):
        trials.correct(register, ASKED, [WINNER, _on(FIVE[0], 3, 0.008)])
    #: another question's trials are not this one's, and no verdicts is no winners
    trials.ask(register, LONDON)
    trials.enter(register, LONDON, NAMES[:2])
    assert [c.trials for c in trials.correct(register, LONDON, both)] == [2, 2]
    assert trials.correct(register, ASKED, []) == ()


def test_a_question_worded_anew_cannot_begin_the_count_again(register: Path) -> None:
    trials.enter(register, ASKED, NAMES)
    before = register.read_bytes()
    for reworded in (ASKED.capitalize(), ASKED + " ", "never asked"):
        for door in DOORS:
            with pytest.raises(ValueError, match="never asked.*which daily rule"):
                door(register, reworded, ["a trial"])
    for again in (ASKED, "", " ", ASKED + " "):
        with pytest.raises(ValueError, match="asked already"):
            trials.ask(register, again)
    for unnamed in ([""], ["good", " "], "bare"):
        with pytest.raises(ValueError, match="without a name"):
            trials.enter(register, ASKED, unnamed)
    assert register.read_bytes() == before, "a refusal writes nothing"


def test_a_lost_register_is_refused_and_never_quietly_begun_again(tmp_path: Path) -> None:
    lost = tmp_path / "trials.jsonl"
    for door in (*DOORS, lambda r, q, _: trials.ask(r, q)):
        with pytest.raises(FileNotFoundError, match="no register of trials"):
            door(lost, ASKED, ["a trial"])
        #: nor is an emptied file a register, nor one that lost its first line
        lost.write_bytes(b'{"question": "asked"}\n' * (door is not DOORS[0]))
        with pytest.raises(ValueError, match="not a register of trials"):
            door(lost, ASKED, ["a trial"])
        lost.unlink()
    trials.start(lost)
    trials.ask(lost, ASKED)
    trials.enter(lost, ASKED, ["a trial"])
    with pytest.raises(FileExistsError):
        trials.start(lost)
    assert trials.count(lost, ASKED) == 1, "starting over an old register wipes nothing"


def test_a_stop_part_way_loses_no_whole_line_and_damage_is_refused(register: Path) -> None:
    trials.enter(register, ASKED, ["one", "two"])
    whole = register.read_bytes()
    register.write_bytes(whole + b'{"question": "which dai')  #: the power went mid-line
    assert trials.count(register, ASKED) == 2
    assert trials.enter(register, ASKED, ["three"]) == trials.count(register, ASKED) == 3
    three = json.dumps({"question": ASKED, "trial": "three"}).encode()
    assert register.read_bytes() == whole + three + b"\n"
    #: a whole line that is no trial is damage, and is never counted around
    asked = three[: three.index(b", ")]
    damage = [b"not a trial", b"5", b'{"trial": "one"}', b'{"question": "never", "trial": "one"}']
    ends = b', "trial": null}|, "trial": " "}|, "trail": 1}|, "trial": "x", "more": 1}|}'
    for line in (*damage, *(asked + end for end in ends.split(b"|")), b'{"question": " "}'):
        register.write_bytes(whole + line + b"\n")
        with pytest.raises(ValueError, match="line 5: not a trial"):
            trials.count(register, ASKED)
    #: and a writer that finds the register changed under it adds nothing
    register.write_bytes(whole)
    with pytest.raises(RuntimeError, match="another process"):
        trials._append(register, whole[:-1], [{"question": "late"}])  # noqa: SLF001 - the stale read itself
    assert register.read_bytes() == whole
