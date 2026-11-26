"""The ladder's verdict on the fixture book, pinned (EASED on, since ease-switch-on)."""

from __future__ import annotations

from pathlib import Path

from test_lab_ladder import EDGE, ISF, NOISE, VUSA, _door, _rows, _set

from lab import ladder

GOLDEN = [
    (
        "THIN",
        {
            "ci": (
                "PASS",
                "the mean gain lies in 0.0742 to 0.1703 after costs; needs above nothing",
            ),
            "costs": ("PASS", "the edge holds to 25.6 times the costs; needs 2"),
            "cpcv": (
                "PASS",
                "58 trades in 6 stretches, 3 purged at the cuts; of 15 splits with 2 held out, "
                "chosen in-sample in 15, lost out-of-sample in 0 of those, a probability of "
                "overfitting of 0.00; chosen in all and lost in none asked",
            ),
            "deflated": ("PASS", "a deflated Sharpe of 1.00; 0.9 passes and under 0.5 fails"),
            "first": (
                "PASS",
                "61 trades judged, their mean gain after every cost (Interactive Brokers UK, "
                "fixed pricing (schedule read 13 November 2026)) 5.09 standard errors above "
                "nothing; 30 trades and 2 asked",
            ),
            "folds": (
                "WEAK",
                "the worst of 5 yearly folds, 2022: 6 trades pooled over 2 lines, their mean day "
                "-0.57 standard errors from nothing; on the history before it, 8.59",
            ),
            "luck": (
                "PASS",
                "its chance of 1.8e-06, times 2 trials of the breakout_20_10 family, is 3.6e-06; "
                "0.05 or under asked",
            ),
            "market": (
                "PASS",
                "over 6160 days, 13.13 standard errors beyond -0.01 of ISF's moves and 15.68 "
                "beyond 0.42 of its own line's; 2 asked of both",
            ),
            "regime": ("WEAK", "up days THIN on 20 trades, down days PASS on 39; both must pass"),
            "regimes": (
                "PASS",
                "first window PASS, second PASS, cut at 2018-06-08; both must pass",
            ),
            "shuffle": (
                "PASS",
                "100 shuffles of its days, its share among them 0.010; 0.05 or under passes",
            ),
            "stress": (
                "PASS",
                "worst: a black swan's night, waking 2016-07-08 lost 345.99 pounds; the limit is "
                "2,000.00; untested: the 2008 crash",
            ),
            "yearly": ("PASS", "a yearly Sharpe of 1.24; over 2.0 is doubted"),
        },
    ),
    (
        "FAIL",
        {
            "ci": (
                "DOUBT",
                "the mean gain lies in -0.0097 to 0.0088 after costs; needs above nothing",
            ),
            "costs": ("FAIL", "the edge holds to 1.2 times the costs; needs 2"),
            "cpcv": (
                "FAIL",
                "91 trades in 6 stretches, 5 purged at the cuts; of 15 splits with 2 held out, "
                "chosen in-sample in 9, lost out-of-sample in 7 of those, a probability of "
                "overfitting of 0.78; chosen in all and lost in none asked",
            ),
            "first": (
                "FAIL",
                "96 trades judged, their mean gain after every cost (Interactive Brokers UK, "
                "fixed pricing (schedule read 13 November 2026)) -0.10 standard errors above "
                "nothing; 30 trades and 2 asked",
            ),
            "regimes": (
                "FAIL",
                "first window FAIL, second FAIL, cut at 2018-06-08; both must pass",
            ),
        },
    ),
]


def test_the_ladder_answers_on_the_fixture_book_are_pinned(tmp_path: Path) -> None:
    ladder.run(tmp_path, _door({VUSA: EDGE, ISF: NOISE}), {}, _set(VUSA, ISF))
    got = [
        (row["answer"], {k: tuple(v) for k, v in row["rungs"].items()}) for row in _rows(tmp_path)
    ]
    assert got == GOLDEN


def test_one_line_through_the_eased_ladder_end_to_end_is_graded_on_every_rung(
    tmp_path: Path,
) -> None:
    """A tiny fixture (one cell, its market beside), EASED on: the row is graded, not unrun."""
    ladder.run(tmp_path, _door({VUSA: EDGE, ISF: NOISE}), {}, _set(VUSA))
    (row,) = _rows(tmp_path)
    assert {"first", "folds", "market", "stress"} <= set(row["rungs"])
