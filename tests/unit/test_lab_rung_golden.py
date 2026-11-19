"""The ladder's verdict on the fixture book, pinned: a restructuring shows it changed nothing."""

from __future__ import annotations

from pathlib import Path

from test_lab_ladder import EDGE, ISF, NOISE, VUSA, _door, _rows, _set

from lab import ladder

GOLDEN = [
    (
        "THIN",
        {
            "first": (
                "PASS",
                "61 trades judged, their mean gain after every cost (Interactive Brokers UK, "
                "fixed pricing (schedule read 13 November 2026)) 5.09 standard errors above "
                "nothing; 30 trades and 2 asked",
            ),
            "luck": (
                "PASS",
                "its chance of 1.8e-06, times 2 trials, is 3.6e-06; 0.05 or under asked",
            ),
            "deflated": ("PASS", "a deflated Sharpe of 1.00; 0.9 passes and under 0.5 fails"),
            "yearly": ("PASS", "a yearly Sharpe of 1.24; over 2.0 is doubted"),
            "folds": (
                "THIN",
                "the worst of 5 yearly folds, 2022: 6 trades pooled over 2 lines, their mean day "
                "-0.57 standard errors from nothing; on the history before it, 8.59",
            ),
            "market": (
                "PASS",
                "over 6160 days, 13.13 standard errors beyond -0.01 of ISF's moves and 15.68 "
                "beyond 0.42 of its own line's; 2 asked of both",
            ),
            "regime": ("THIN", "up days THIN on 20 trades, down days PASS on 39; both must pass"),
            "stress": (
                "PASS",
                "worst: a black swan's night, waking 2016-07-08 lost 345.99 pounds; the limit is "
                "2,000.00",
            ),
            "shuffle": (
                "THIN",
                "not run: its 100 shuffles are kept for a trial that passed every rung before "
                "it, and folds answered THIN",
            ),
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
        },
    ),
    (
        "FAIL",
        {
            "first": (
                "FAIL",
                "96 trades judged, their mean gain after every cost (Interactive Brokers UK, "
                "fixed pricing (schedule read 13 November 2026)) -0.10 standard errors above "
                "nothing; 30 trades and 2 asked",
            ),
            "luck": ("FAIL", "its chance of 0.54, times 2 trials, is 1; 0.05 or under asked"),
            "deflated": ("FAIL", "a deflated Sharpe of 0.27; 0.9 passes and under 0.5 fails"),
            "yearly": ("PASS", "a yearly Sharpe of -0.02; over 2.0 is doubted"),
            "folds": (
                "THIN",
                "the worst of 5 yearly folds, 2022: 6 trades pooled over 2 lines, their mean day "
                "-0.57 standard errors from nothing; on the history before it, 8.59",
            ),
            "market": (
                "FAIL",
                "over 6151 days, -0.32 standard errors beyond 0.42 of ISF's moves and -0.32 "
                "beyond 0.42 of its own line's; 2 asked of both",
            ),
            "regime": ("FAIL", "up days FAIL on 55 trades, down days FAIL on 39; both must pass"),
            "stress": (
                "PASS",
                "worst: a black swan's night, waking 2016-02-17 lost 253.63 pounds; the limit is "
                "2,000.00",
            ),
            "shuffle": (
                "FAIL",
                "not run: its 100 shuffles are kept for a trial that passed every rung before "
                "it, and first answered FAIL",
            ),
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
        },
    ),
]


def test_the_ladder_answers_on_the_fixture_book_are_pinned(tmp_path: Path) -> None:
    ladder.run(tmp_path, _door({VUSA: EDGE, ISF: NOISE}), {}, _set(VUSA, ISF))
    got = [
        (row["answer"], {k: tuple(v) for k, v in row["rungs"].items()}) for row in _rows(tmp_path)
    ]
    assert got == GOLDEN
