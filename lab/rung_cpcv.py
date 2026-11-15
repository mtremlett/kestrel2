"""rung_cpcv - THE LADDER'S EIGHTH RUNG: combinatorial purged cross-validation, and the
probability that a rule was overfitted to the history it was chosen on (R-RUNNER-119).

A rule that earned over its whole history may have earned it all in one lucky stretch. The
first rung (`lab/rung.py`) cannot tell, for the total is the same; walking forward
(`lab/folds.py`) asks it of the years in the one order they came. This rung asks it of every
way the history divides.

SIX STRETCHES, EVERY TWO HELD OUT IN TURN. The days from the first judged trade's buy to the
last one's sale are cut into STRETCHES equal stretches. Each way of holding HELD_OUT of them
out is a split, fifteen in all. The other four are in-sample, all a chooser is shown: the rule
is CHOSEN there when its trades' mean gain after costs is above nothing. The two held out are
out-of-sample, where the rule earns or LOSES by the same measure.

PURGED. A trade held across a cut stands on both sides of it, and one bought in the embargo
after a cut (a hundredth of the days, Lopez de Prado's own figure) was decided on what the
stretch before it showed. Both are in no stretch, in every split, so nothing the in-sample
side saw is judged out-of-sample.

THE PROBABILITY OF OVERFITTING is, of the splits the rule was chosen in, the share it then
lost out-of-sample: about a half for noise, nothing for an edge that is there throughout.

THE RUNG PASSES a rule chosen in every split and losing in none: any two stretches of its
history earn together, so one poor stretch fails nothing and gains that are one stretch's do.
ITS STATED RATE (RATE) is 1 in 32 of rules with no edge, and is exact. It passes only when the
two worst stretches sum above nothing; where each stretch's sum is as likely either side of
nothing, whatever its size, and independent of the rest, that is all six above (1 in 64) or
one below and the smallest of the six (1 in 64).

FAILING FAIRLY (LAD-06). No judged trade is a FAULT in the test. Under `rung.MIN_TRADES` left
in the stretches, or a stretch with none, is THIN: the rung could not have passed it.

READS THE TAPE, KEYED BY IT. It is handed the first rung's verdict on a tape (`lab/tape.py`),
the tape's trades priced, and runs no simulation. Its result's key is the tape's own (the
rule's code, the engine's, the bars, the window) and this module's code with all it reaches,
the cost model among it. The rates it was priced at are the caller's to key.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import combinations

from desk.strategy import ARITHMETIC
from lab import rung, tape
from lab.rung import Answer, Priced, Verdict

ME = "lab.rung_cpcv"  #: this module as the cell knows it
STRETCHES, HELD_OUT = 6, 2
EMBARGO = 100  #: the days after a cut that are no stretch's: one in this many of the history's
RATE = Fraction(2, 2**STRETCHES)  #: the share of rules with no edge it passes, two held out


@dataclass(frozen=True)
class Split:
    """One way of holding stretches out: the rule's mean gain on each side of it."""

    out: tuple[int, ...]  #: the stretches held out, the oldest stretch 0
    inside: Decimal  #: in-sample: the mean gain of the trades of the other stretches
    outside: Decimal  #: out-of-sample: the mean gain of the trades of those held out

    @property
    def chosen(self) -> bool:
        """Whether a chooser shown the in-sample side alone would have taken the rule."""
        return self.inside > 0

    @property
    def lost(self) -> bool:
        """Chosen in-sample, and no gain out-of-sample."""
        return self.chosen and self.outside <= 0


@dataclass(frozen=True)
class Crossed:
    """A tape crossed: every split, and the rung's one answer on them."""

    key: str  #: what made it: the tape, and this module's code
    trades: int  #: the judged trades in the stretches
    purged: int  #: the judged trades in no stretch
    splits: tuple[Split, ...]  #: every split; none where the answer is THIN or FAULT
    answer: Answer  #: PASS, FAIL, THIN or FAULT: this rung never answers DOUBT

    @property
    def chosen(self) -> int:
        """The splits the rule was chosen in."""
        return sum(split.chosen for split in self.splits)

    @property
    def lost(self) -> int:
        """The splits it was chosen in and then lost in, out-of-sample."""
        return sum(split.lost for split in self.splits)

    @property
    def overfit(self) -> Fraction | None:
        """The probability of overfitting; none where the rule was never chosen."""
        return Fraction(self.lost, self.chosen) if self.chosen else None

    @property
    def passed(self) -> bool:
        """Whether the rung passes the rule."""
        return self.answer is Answer.PASS

    @property
    def reason(self) -> str:
        """The answer's reason, in the words of a results table."""
        cut = f"{self.trades} trades in {STRETCHES} stretches, {self.purged} purged at the cuts"
        if not self.splits:
            return f"{cut}; {rung.MIN_TRADES} trades asked, and a trade in every stretch"
        odds = "never chosen" if self.overfit is None else f"{float(self.overfit):.2f}"
        return (
            f"{cut}; of {len(self.splits)} splits with {HELD_OUT} held out, chosen in-sample in "
            f"{self.chosen}, lost out-of-sample in {self.lost} of those, a probability of "
            f"overfitting of {odds}; chosen in all and lost in none asked"
        )


def cross(verdict: Verdict) -> Crossed:
    """The first rung's verdict on a tape, crossed: every split's two means, and the answer."""
    stretches = _stretches(verdict.trades)
    kept = sum(map(len, stretches))
    splits: tuple[Split, ...] = ()
    if not verdict.trades:
        answer = Answer.FAULT
    elif kept < rung.MIN_TRADES or not all(stretches):
        answer = Answer.THIN
    else:
        with localcontext(ARITHMETIC):
            splits = tuple(
                Split(
                    out,
                    _mean([g for n, s in enumerate(stretches) if n not in out for g in s]),
                    _mean([g for n in out for g in stretches[n]]),
                )
                for out in combinations(range(STRETCHES), HELD_OUT)
            )
        held = all(split.chosen and not split.lost for split in splits)
        answer = Answer.PASS if held else Answer.FAIL
    return Crossed(key(verdict), kept, len(verdict.trades) - kept, splits, answer)


def key(verdict: Verdict) -> str:
    """What made a result: the tape's key, its engine's code joined by this rung's and all
    this rung reaches."""
    made = verdict.key.rung(ME)
    text = f"{tape.rule_code(made.cell.strategy)}\n{made.code}\n{made.data}\n{made.cell}"
    return hashlib.sha256(text.encode()).hexdigest()


def _stretches(priced: Sequence[Priced]) -> list[list[Decimal]]:
    """Each stretch's gains, the oldest stretch first; a purged trade's gain is in none."""
    stretches: list[list[Decimal]] = [[] for _ in range(STRETCHES)]
    if not priced:
        return stretches
    first = min(p.held[0] for p in priced)
    days = (max(p.held[1] for p in priced) - first).days
    cuts = [first + timedelta(days * n // STRETCHES) for n in range(1, STRETCHES)]
    for p in priced:
        bought, sold = (sum(cut <= day for cut in cuts) for day in p.held)
        embargo = bought > 0 and p.held[0] < cuts[bought - 1] + timedelta(days // EMBARGO)
        if bought == sold and not embargo:
            stretches[bought].append(p.gain)
    return stretches


def _mean(gains: Sequence[Decimal]) -> Decimal:
    return sum(gains, Decimal(0)) / len(gains)
