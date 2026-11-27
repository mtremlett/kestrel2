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
after a cut (a hundredth of the days, Lopez de Prado's own figure; none on a history under
a hundred days) follows too closely on the stretch before. Both are in no stretch, in every
split, so no trade stands on both sides of one.

THE PROBABILITY OF OVERFITTING is this rung's own figure for one rule, not Bailey's across a
roster: of the splits the rule was chosen in, the share it then lost out-of-sample. Pooled
over many rules of noise it is a half, though one tape's own swings from nothing to one; for
an edge that is there throughout it is nothing.

THE RUNG PASSES a rule chosen in every split and losing in none: any two stretches of its
history earn together. A poor stretch fails it only when it loses as much as the next worst
earns, or more; gains that are all one stretch's always do. Earning on every two held out is being
chosen on every four (two pairs), so the answer is decided out-of-sample: the choosing is in
the probability reported, not in the pass.

ITS STATED RATE (RATE) is 1 in 32, and exact for gains with no edge that are symmetric about
nothing. It passes only when the two worst stretches sum above nothing; where each
stretch's sum is as likely above as below, whatever its size, and independent of the rest,
that is all six above (1 in 64) or one below and the smallest of the six (1 in 64).
IT IS NOT THE RATE OF LOPSIDED GAINS, AND ALONE THIS RUNG PUTS NO CEILING ON THEM. A rule with
no edge that makes many small wins and a few large losses passes more often, wherever a
stretch holds no large loss or wins enough to outweigh one, and the rarer the loss the more.
Measured: at nine wins to each loss nine times the size, 3 in 32 at six trades a stretch (the
tests record it), under 1 at ten and 3 again at twelve; at ninety-nine to one, 23 in 32 at six
and 18 at ten. The mirror shape passes a third as often at six a stretch and a little over the
rate at ten; gains that each carry on half of the last, about 1.2 in 32 on sixty trades.
No sample holds the loss that has not come yet: that loss is the first rung's to plant (G2),
and with it planted at the size of the rare loss the two rungs together passed under 1 in 32
on every shape measured. No rule passes the ladder by this rung alone.

FAILING FAIRLY (LAD-06). No judged trade is a FAULT in the test. Under `rung.MIN_TRADES` left
in the stretches, or a stretch with none, is THIN: the rung could not have passed it.

READS THE TAPE, KEYED BY IT. It is handed the first rung's verdict on a tape (`lab/tape.py`),
the tape's trades priced, and runs no simulation. Its result's key is the tape's record's,
made this rung's by this module's code and all it reaches, the cost model among it
(`Key.rung`). The rates and the capital it was priced at are the caller's to key.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import combinations

from desk.strategy import ARITHMETIC
from lab import rung
from lab.cell import Key
from lab.rung import Answer, Priced, Rung, Verdict

STRETCHES, HELD_OUT = 6, 2  #: RATE is this pair's alone: change either and derive it again
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

    key: Key  #: the tape's key, made this rung's by its code
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


def judge(verdict: Verdict) -> Crossed:
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
    return Crossed(verdict.key.rung(__name__), kept, len(verdict.trades) - kept, splits, answer)


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


def _judged(first: Verdict) -> tuple[Answer, str]:
    """The cross-validation rung as the ladder reads it: its answer, and its reason in words."""
    crossed = judge(first)
    return crossed.answer, crossed.reason


RUNG = Rung("cpcv", "chosen in-sample in every split and lost out-of-sample in none", _judged)
