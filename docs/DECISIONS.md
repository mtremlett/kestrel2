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

---

## 2026-11-13 — the scenes are a ratchet, not a known-failing list

**Decided.** `check.py` judges the scenes this way: each scene passes, or it stops at a
part of the desk that raises NotImplementedError because it is not built yet. Any other
failure is red. The number of passing scenes must equal the one `docs/PLAN.md`
publishes, so a passing scene that regresses is red, and so is a new pass nobody
recorded.

**Why.** The plan says to write the scenes as failing tests, the canon says the check is
always green, and a guard forbids marking any test as expected to fail. Without this
rule, seven honest failing scenes would turn main red until phase 2, and nothing could
merge. With it, a scene can only be "failing" in one way — the desk is not built yet —
and that list of unbuilt parts is kept by name in `docs/STATUS.md`.

**The evidence.** Driven in a throwaway copy against six deliberate violations, each
caught: a scene failing on a wrong answer; the plan publishing 1 of 7 with none passing;
a scene passing that the plan did not record; a scene file that would not load; the
plan's number deleted; a scene crashing in its own setup. The untouched tree is green.

**The cost.** It trusts the error's name: a test raising NotImplementedError itself would
count as unbuilt. Recorded in `docs/STATUS.md`. This change touches a guard
(`check.py`), so it merges only with the operator's approval.

---

## 2026-11-13 — the desk's shape is set by what the scenes call

**Decided.** Seven core modules, each owning one thing, registered in `manifest.toml`:
`lines` (the instrument master), `store` (the one price store and its writer),
`strategy` (the five frozen strategies, a decision for every line and day in one pass),
`orders` (sizing from the one capital number, the order and its stop, the pre-trade
gate), `broker` (the pretend broker with faults), `book` (the ledger under the broker's
ids, and the book built from the broker) and `day` (one day run, published, replayed).

**Why.** Writing the scenes as tests means writing the calls they make. The records are
real; every behaviour raises NotImplementedError until its phase. An order without a
stop cannot be constructed, and a day's costs cannot be recorded with a line missing:
both are made impossible by the types rather than checked afterwards. There is no
separate replay: replaying a day is running it again from the same saved data into a
fresh folder, and scene 7 requires the records to be identical.

**Reviewed.** A reviewer that never saw this reasoning read the scenes against
`docs/SCENES.md`. Its one blocking finding (scene 3's smaller capital could be legal for
a correct sizer) and the weak ones that let a wrong desk pass — the send path not
passing the gate, stops unchecked for size and level, profit not tied to the fill
prices, a replay that could read back its own record — were fixed before commit. What
it found and was not fixed is listed in `docs/STATUS.md`.

---

## 2026-11-13 — the size rule holds unit tests to the product, from the first line

**Decided.** The guard `test_tests_never_outgrow_the_product` compares the lines of
`tests/unit/` with the lines of `desk/` and `lab/`, with no exemption below 200 lines.
The guards and the scenes are no longer counted. The budget key is now
`unit_test_lines_may_not_exceed_product_lines`.

**Why.** Counting every test made the rule red the moment the scenes were written before
their code, as the canon requires: 502 test lines (282 of guards, 220 of scenes) against
303 of desk outline. What grows one test per bug is the unit tests. The guards and the
scenes are fixed in number and change only with his approval.

**By.** The operator. A session proposed it and was refused when it tried to make the
change itself: loosening a guard is his call. Asked in chat on Friday 13 November 2026
whether to count only the everyday tests (option A), his words: "Yes, option A".

**The evidence.** Driven in a throwaway copy: untouched, the guard passes; with 401
lines of unit test against 303 of product, it fails with "unit tests 401 lines > product
303 lines".

---

## 2026-11-13 — sessions merge their own pull requests when the check is green

**Decided.** A session merges its own pull request (`gh pr merge --squash`) when the
`check` job is green on the pull request's last commit. The operator is not asked to
approve merges. A pull request that LOOSENS a guard (`BUDGET.json`, `manifest.toml`,
`tests/guards/`, `check.py`, `.github/`) still waits for his plain-English yes in chat,
asked as a business question with options and a recommendation, never "review this".
Tightening a guard merges like any change.

**His words.** In chat, Friday 13 November 2026, about 12:46 UK time: "operator asks
that they are not required to approve merge requests. can the mentor do this for me? ...
i am not the expert, so how would i know if there was an error. there is no point in
asking me to check this and approve. you must do this via your guardrails and checks.
please confirm."

**Made a guard, not a promise.** GitHub's ruleset `main-guard` required a pull request
and a squash, but not a passing check, so a session could have merged red. Asked once
whether GitHub itself should refuse a merge whose check has not passed, his answer at
about 12:53: "Yes, add it (Recommended)". The ruleset now requires the `check` job
(GitHub Actions) to pass before any merge to main.

**Driven red.** Pull request #5 added an unused import, a deliberate lint failure. The
check failed on GitHub, GitHub reported the pull request BLOCKED, and `gh pr merge
--squash` was refused: "the base branch policy prohibits the merge". It was closed
unmerged. Not tried: whether the owner's account could force it through as an
administrator. Trying it risks merging red, and it is the reason a second, non-admin
account is recommended before unattended work.

---

## 2026-11-13 — the A-GATE test

**Decided.** The requirement, as written in `docs/PLAN.md` phase 5 (AG-01 to AG-06). A
strategy set passes A-GATE only when all of these hold:

| id | condition |
|---|---|
| AG-01 | It passed the ladder first: luck-corrected for every trial it was picked from, after costs, judged on its worst fold, over years of history, not weeks. |
| AG-02 | Sixty consecutive trading days on paper, through the one engine, average at least £100 a day net of every cost (commission, spread, slippage, currency, UK tax), priced under the broker it trades. |
| AG-03 | The paper result sits inside the range the history predicted for a sixty-day stretch. A paper run far below it fails, however it ended. |
| AG-04 | Its net profit over the sixty days is more than the same capital would have made simply holding the market over the same days. |
| AG-05 | The money never falls more than £1,500 below its highest point during the sixty days. |
| AG-06 | Every one of the sixty days reconciled with the broker, no safety rule overridden, no halt bypassed. |

**Why the luck correction sits on the history, not on the sixty days.** Sixty days is
too short to separate skill from luck on its own: proving it from paper days alone needs
a yearly Sharpe above 3, which the canon treats as a red flag. So the history proves the
edge after counting every trial, and the paper days prove the live desk earns what the
history said it would.

**Shortened to thirty days only if all of these hold, fixed now, before any result:**
an average of at least £150 a day net over the thirty days; the money never more than
£750 below its highest point; at least twenty completed trades; the best three days
together under a third of the profit; and AG-01, AG-03, AG-04 and AG-06 as above. Any one
missing and the run continues to sixty days. These numbers are not changed after a
result has been seen.

**His words.** In chat, Friday 13 November 2026, about 12:46 UK time, agreeing the
sixty-day test: "i agree. if we are working will and the P&L can reflect a good
framework and good strategies then we could tune this to 30days, but only if conditions
were excellent." Offered three definitions of "excellent" at about 12:53, he chose
"Strong (Recommended)"; offered three limits for the fall from the highest point, he
chose "£1,500 (Recommended)".

**Replaces.** "Ten consecutive £100 days", close to unreachable for an honest edge.
