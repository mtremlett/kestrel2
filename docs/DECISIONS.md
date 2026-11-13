# Decisions

Dated, with what was decided, why, and the evidence. Every change to a golden number and
every new dependency appears here. A decision contradicted by the tree is a defect.

---

## 2026-11-13 — start again, in a new repository

**Decided.** Build the desk afresh here rather than repair the predecessor in place.

**Why.** Measured on the predecessor the same day: 438,466 lines of product code in 460
files; 400,000 lines of test across 2,054 files, 1,218 of them named after the session
that wrote them; 2,221 tests set aside as known failures; 27,983 commits in thirty days
of which 14,387 were automatic checkpoints; 1,367 work cards created in six weeks against
10 of 64 requirements proven. Its daily trading run could reach 352,000 lines of code.

Its own clean core had already been tried in place: capped at 2,000 lines in September,
it was still 2,331 lines two months later — the cap held. It leaked in exactly one place,
when the code that ran it each day was put outside the capped folder on 29 October, and
that file was changed 54 times afterwards. **A hard limit worked; the failure was that
there was an outside.** Hence a repository where there is no outside.

**By.** The operator, in conversation, reversing his ruling of 8 November that nothing
would be rebuilt elsewhere.

---

## 2026-11-13 — the repository is public

**Decided.** Public, not private.

**Why.** The guards are only real if they are enforced somewhere a session cannot reach,
and GitHub's branch rules are not available on a free private repository. This was tested,
not assumed: creating the rule on the private repository returned "Upgrade to GitHub Pro
or make this repository public". The operator chose not to pay.

**The cost.** Anyone can read the code, strategy logic included. No price data, position,
account record or credential ever enters the repository, and a guard checks that on every
change.

---

## 2026-11-13 — twelve guards, each proven by breaking it

**Decided.** No guard counts until a deliberate violation has been shown to trip it.

**The evidence.** Twelve mistakes made on purpose. Eleven were caught. The one that was
missed was the guard against reaching live money: it excused any file containing the word
"never" anywhere, and the core package says it in ordinary prose, so the guard had been
passing green while doing nothing. A second guard had the same shape — a file containing
the words of its own escape hatch excused itself entirely.

Both were rewritten to judge one line at a time, and the words they search for are now
assembled from pieces so that a guard never flags its own source. Re-run: twelve of
twelve caught, the tree restored, the check green.

**Why it is recorded.** It is the reason A7 exists in the canon. Nothing in the reasoning
found this; driving it against a real mistake found it in ninety seconds.

---

## 2026-11-13 — the declared environment has one home

**Decided.** `requirements.txt` is the only list of dependencies. Three to begin with:
ruff, mypy, pytest.

**Why.** They were briefly written down twice, in `requirements.txt` and in a
`pyproject.toml` extra, which is two homes for one fact. GitHub's check installs the one
list and does not build the project, because nothing imports it as an installed package.

---

## 2026-11-13 — the seven scenes are approved

**Decided.** The seven scenes in `docs/SCENES.md` are the scoreboard. They change only
with the operator's approval.

**His words.** In chat, Friday 13 November 2026, about 11:55 UK time, answering that the
seven scenes were waiting on his approval: "i approve all."

**What follows.** The next step in the plan is to write them as failing tests.
