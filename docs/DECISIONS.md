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

---

## 2026-11-13 — one Telegram line for each change that lands on main

**Decided.** The operator's request, in chat on 13 November: when a change lands on main,
GitHub sends him one plain-English Telegram line, for example "kestrel2: price store
merged (#6). Scenes passing 1 of 7. Next: daily bars for the twenty lines." One line per
merge, which is one per session's deliverable; nothing on a timer.

**How.** A job, `announce`, in the one workflow (`.github/workflows/check.yml`). It runs
only on main, and only after the check has passed there. `announce.py`, beside
`check.py`, takes the title and number of the pull request whose merge made the commit
from GitHub, and the scenes count and the current objective from `docs/PLAN.md`. The
scenes count is read with the same pattern the check uses to hold that number true, so
the line can never report a number the check has not measured.

**It refuses rather than guesses.** A missing or blank secret
(`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, set by the operator on GitHub and nowhere else)
turns the job red before anything is sent; it never skips. So does a plan that no longer
states its objective or its scenes count, a commit on main that no pull request made, and
Telegram not confirming delivery. The message number Telegram returns is written on the
run's page as the delivery record.

**The key never reaches a log.** The repository is public. The key's shape is checked on
entry, so a bad paste is refused by name without being shown, and an error from Telegram
names the host it came from, never the address, which holds the key.

**Proven.** Eleven deliberate breaks were each caught by `tests/unit/test_announce.py`:
a blank secret taken as set; a missing secret skipped; the secrets never read; the wrong
pull request announced; a plan without its objective, and one without its count, sent
anyway; Telegram's refusal ignored; the error printing the address with the key; a
half-valid key let through; no time limit on a call; the delivery record losing
Telegram's message number. A blind review found nothing blocking; three of its minor
points were taken (the sending tests, the key's shape, a truer error when GitHub has not
yet linked a commit to its pull request).

**No new dependency.** The standard library only (`urllib`, `json`), on GitHub's own
Python. Nothing is added to `requirements.txt`.

**What it is not.** This is a notice about the repository, not the desk's messenger. The
desk's morning and evening messages, with their delivery record and an alarm on silence,
are phase 3, behind one adapter in `desk/`. When that is built, this line either goes
through it or is the one exception, decided then and recorded here.

**The cost.** The line comes only when the check on main passes. If main were ever red
after a merge, no line comes, and GitHub's own failure notice is the alarm.

---

## 2026-11-13 — the twenty lines: ten in London, ten in the US

**Decided.** The twenty frozen lines are ten on the London venue and ten in the US,
all London lines priced in pounds and all US lines in dollars:

| London | US |
|---|---|
| 3LGO WisdomTree Gold 3x daily | AAPL Apple |
| 2MU Leverage Shares 2x Micron | TSLA Tesla |
| SMGB VanEck Semiconductor | NVDA Nvidia |
| IITU iShares S&P 500 Information Technology | SPCX SpaceX |
| VHYG Vanguard All-World High Dividend | MSTR Strategy |
| 5QQQ Leverage Shares 5x Nasdaq 100 | AMD Advanced Micro Devices |
| IB1T iShares Bitcoin | SPY S&P 500 |
| ISF iShares Core FTSE 100 | QQQ Nasdaq 100 |
| VUSA Vanguard S&P 500, in pounds | MU Micron |
| SGLN iShares Physical Gold | GLD Gold |

**How each was checked.** Every ticker was looked up in the free archive on 13 November
2026. Two he named did not exist there: "aalp" and "1b1t.l". Asked whether he meant AAPL
and IB1T, he answered "Yes, AAPL and IB1T (Recommended)". SPCX is SpaceX, listed on 12
June 2026. 3LGO has no history in the free archive, though the same product in dollars,
3GOL, has fourteen years; offered 3GOL, 3LGO or plain gold, he chose "Keep 3LGO in
pounds", so it holds no history to test on until the archive gathers some. The last seven
were proposed with a recommendation each: for London he chose "ISF, VUSA, SGLN
(Recommended)", for the US "SPY, QQQ, MU, GLD (Recommended)" - a yardstick for "simply
holding the market" on each venue (AG-04) and the plain version of each leveraged line.

**Leverage, told to him before anything trades it.** 3LGO is three times gold's daily
move, 2MU twice Micron's, 5QQQ five times the Nasdaq's. They reset daily, so a 20% day
empties a 5x line and a choppy market bleeds them even when the index ends flat. Phase 2
asks him how they are sized.

**His words.** In chat, Friday 13 November 2026, about 13:24 UK time: "10 uk and 10 us.
uk includes 3lgo.l, 2mu.l, smgb.l, iitu.l, vhyg.l, 5qqq.l , 1b1t.l . us includes: aalp,
tsla, nvda, spcx, mstr, amd."

---

## 2026-11-13 — London's auction prices, and old bad days

**Found.** With the twenty lines fetched, all ten US lines came in clean and complete
from 2010. All ten London lines were parked: on up to a quarter of their days the free
archive's open or close sat outside that day's high and low, mostly by under 2%, at worst
20% (2MU). London records its opening and closing auctions apart from the day's trading,
which is the likely cause. And because a line is judged on its whole history, which never
changes, one bad day years ago (ISF has a bar on 29 April 2011, when London was shut)
parked a line for good.

**Decided, first.** An open or close no more than 3% outside the day's range is taken as
the official price, and the range is stretched to hold it; further out, the bar is still
refused. A stop is then judged as if the price reached that open or close, which errs
toward a stop being hit. The rule applies on both venues; the US lines have no such day.
Asked how to treat those days, with three options, he chose "Trust the close, small gaps
(Recommended)". Driven: with no stretch, a close 2.9% out parks its line; with 5%, an
open 4% out enters. Both are caught.

**Decided, second.** A bad day older than the last sixty trading days is removed and
listed in the line's record, and no longer parks it; anything wrong in the last sixty
sessions still does. A step in the price that the archive did not adjust parks the line
however old it is, because it makes every bar before it wrong. Asked, he chose "Drop old
bad days, hold back on recent ones (Recommended)". A run of up to twenty days a hundredfold out of
line with the days either side (pence among pounds) is bad days, not a step; any other fall
and recovery is kept and parks, since a leveraged line can lose 40% and win it back.
Driven: a window of 3000 sessions, a window of 3, a step not counted as lasting, a run
limit of 1, and a 40% fall taken as a unit were each caught.

---

## 2026-11-13 — leveraged lines sized by what they control; phase 2 begins

**Decided, first.** When the desk sizes an order in a leveraged line, the money counts
times its leverage against every limit: £1,000 in 5QQQ (5x) counts as £5,000, in 3LGO
(3x) as £3,000, in 2MU (2x) as £2,000. Each line then puts the same real risk on the book,
and its stop sits correspondingly closer. Built with sizing in phase 2; the leverage of
each line becomes a fact in the instrument master, never read from its name.

**Decided, second.** Phase 1's data is done (sixteen of twenty lines clean, four parked
with named reasons) and the desk moves to phase 2: strategies, sizing and the pretend
broker, in simulation only. `BUDGET.json` names `2-money-sim`, whose ceilings - 7,000 lines
of desk code in 45 files, 1,500 of lab - were agreed before phase 0 began. This raises a
guard's ceiling, and his answer below is the plain yes it needs. The four parked lines are
brought back along the way.

**His words.** In chat, Friday 13 November 2026, about 14:00 UK time. Offered three ways
to size the leveraged lines, he chose "Size by what they control (Recommended)". Offered
phase 2 now or one more data session first, he chose "Move to phase 2 now (Recommended)".

---

## 2026-11-13 — the five frozen strategies: five textbook rules

**Decided.** The desk's five daily strategies are five published rules at their authors'
settings, long only, untuned (`desk/strategy.py`):

| name | the rule |
|---|---|
| `rsi2_pullback` | Connors (2008): buy when the close is above its 200-day average and the 2-day RSI is under 5; sell on a close above the 5-day average |
| `bollinger_pullback` | Bollinger, 20 days and 2 deviations: buy a close under the lower band; sell a close over the 20-day average |
| `breakout_20_10` | The Turtles' system 1 (Faith, 2007), on the close: buy a close over the highest high of the 20 days before; sell a close under the lowest low of the 10 days before |
| `trend_50_200` | Buy the day the 50-day average crosses above the 200-day; sell the day it no longer is |
| `supertrend_10_3` | Seban's Supertrend, 10 days and 3 average true ranges, as the common reference script carries its bands: buy a close over yesterday's upper band, sell one under yesterday's lower |

**Why.** At this stage they prove the machine, not an edge; whether any earns money is the
ladder's question (phase 4) before any money depends on it. Published settings leave
nothing tuned, so nothing was picked from trials, and each can later be checked against
its author's own published results.

**The template.** A rule is shown one bar at a time after its close and says whether it
wants to be in the market; it is never handed the series, so it cannot read a later bar.
The template turns each change of mind into a buy or a sell and every other day into a
hold. Each starts out of the market.

**The evidence.** Each rule buys and sells on the day worked out by hand in its contract
test, ties included: a close exactly on the Supertrend's band holds, and a pullback
exactly on the 200-day average does not buy. A second implementation, written by a
separate agent from the rules above without seeing the desk's code, found identical trade
days for all five on sixty 1,200-day walks, whose prices sit on a 25p tick and whose
open, high and low fall unevenly about the close, and on the hand-made series. Seven
series' days are pinned in `tests/unit/test_strategy.py`: walk 1, plus each walk or
short jumpy series that was the first to show a wrong rule the others let through.

Forty-five deliberate breaks were driven, each from a copy of the tree whose own tests
first passed: every window one day long or short, every "over" turned into "at or over",
the wrong deviation, band width, smoothing or its seed, true range, band carry or price
the bands sit on, too few digits, the caller's arithmetic leaking in, the 50/200 buying a
cross it never saw, selling what it did not hold, and the template peeking one bar ahead.
Forty-four are caught. The one that passes, an RSI "at or under 5" for "under 5", cannot
differ: in this arithmetic the RSI never comes out at exactly 5.

**Reviewed.** A blind reviewer found no look-ahead and no rule off its definition, but
showed wrong rules passing the first tests: the test walk's bars were symmetric about an
open equal to the close, so a window a day off, the close read for the middle of the
range, or a tie broken the wrong way could not show. The walk was rebuilt, the second
implementation re-run, and the series that catch each one pinned. One run of the breaks
was first read as all caught when its starting tests were themselves failing; the breaks
are now run only from a passing start. The reviewer's minor points were taken: the
Supertrend script is named, an impossible state raises instead of quietly holding, and
the rules run under one stated arithmetic whatever the caller has set. What it found for
later scenes is in `docs/STATUS.md`.

**His words.** In chat, Friday 13 November 2026, offered five textbook rules, the old
desk's four plus one, or his own five, he chose "Five textbook rules (Recommended)".

---

## 2026-11-13 — the scenes' rehearsal data is to be lengthened

**Found.** On the scenes' six weeks of made-up prices, none of the five rules ever buys:
they need 20 to 200 days of history first, then a breakout or a sharp dip, and the
rehearsal prices only drift gently. Scene 5 needs a complete buy and sell, so it cannot
pass on that data.

**Decided.** The rehearsal data becomes about fourteen months of made-up prices with a
steady rise, a sharp dip and a breakout, still tiny, fixed and identical on every
machine, so that all five rules can buy and sell. Every scene still passes or fails for
the same reasons it does today. It is done before scene 5 is attempted.

**His words.** In chat, Friday 13 November 2026, offered longer rehearsal data, one dip
in the six weeks, or deciding later, he chose "Longer rehearsal data (Recommended)".

---

## 2026-11-13 — auto-merge: a green pull request lands with no one present

**Decided.** GitHub's "allow auto-merge" is on for this repository. A session arms it when
it opens its pull request (`gh pr merge --squash --auto`), and GitHub merges the pull
request the moment the required `check` passes on its last commit. Nobody has to be
present for the merge.

**Why.** Until now a session had to stay until GitHub finished the check and then merge
by hand, and when it could not wait, the merge waited for him. His words, in chat on
Friday 13 November 2026, after #12 waited on him: "can we switch this on so you do not
need me to attend?"

**What does not change.** The ruleset `main-guard` still requires the `check` job, squash
merges only, and has no one who may bypass it; auto-merge waits on exactly that rule. A
pull request that loosens a guard is still not armed until his plain-English yes. The job
that names a touched guard on a pull request only warns; it never blocked a merge, by
hand or now.

**Driven red.** Pull request #13 added an unused import, a deliberate lint failure, and
had auto-merge armed. Both runs of `check` failed; GitHub held it BLOCKED and did not
merge it. It was closed unmerged and its branch deleted.

**The cost.** An armed pull request stays armed: anything a session pushes to that branch
afterwards merges too once it is green. Sessions push to their branch only what they mean
to land.

---

## 2026-11-13 — a fifth to each holding, and a stop where its market has fallen 10%

**Decided.** The desk sizes a buy from the one capital number (`orders.Settings.capital`):
at most five holdings, each costing at most a fifth of the capital, a leveraged line
counted at what it controls. Of £10,000, a plain line may take £2,000, 3LGO £666.67, 2MU
£1,000 and 5QQQ £400. The stop is set when the order is made, where the market under the
line has fallen 10%: 10% below the price on a plain line, 20% on 2MU, 30% on 3LGO, 50% on
5QQQ. So the most any one stop loses is about 2% of the capital, on every line alike. The
sizer takes the most whole shares whose full cost fits, and the pre-trade gate refuses an
order that costs more; both read the same number (`_room` in `desk/orders.py`).

This settles what the ruling above, "leveraged lines sized by what they control", left
open: its "stop correspondingly closer" holds in money, not in price. The stop sits at the
same fall of the market, so on a leveraged line's own price it is further away.

Leverage is now a fact written against every line in the instrument master, never read
from a name and never defaulted: a line cannot be made without it.

**The costs.** An order's cost is priced under Interactive Brokers UK's fixed pricing, read
from its published schedule on 13 November 2026 (`orders.BROKER`): London 0.05% of the
value, at least £3; US half a cent a share, at least a dollar, at most 1% of the value;
dollars bought by its automatic conversion, 0.03% on the rate, commission included. UK
stamp duty is not in an order's cost: the ten London lines are exchange-traded funds and
products, which normally pay none. That is to be confirmed line by line before the day's
record counts UK tax.

**The evidence.** The order tests were seen failing first. Thirty deliberate breaks
were driven from a passing copy: the leverage of one line, the five holdings, the 10%, the
stop's leverage, the room's leverage, the gate reading the whole capital, a cost exactly
equal to the room refused, one share fewer, each fee and its minimum and cap, the
conversion and what it is charged on, a pound line at a rate other than 1. The first run
missed three (a leverage of nought, a cost exactly equal to the room, a rate of nought) and
the second missed one (an exact fit of more than one share); each became a test. The
re-review's checks on entry added four more (a currency, a whole leverage, a capital that is
positive and finite). All thirty are now caught.

**Reviewed.** A blind reviewer found two blocking problems. A pound line accepted any
exchange rate, so an order worth £10,000 could cost "£100" and pass the gate: a pound line
now requires a rate of exactly 1. And "at most five holdings" is checked nowhere, because
the gate cannot see the book: it is recorded in `docs/STATUS.md`, to be built with the
book. Its minor findings were taken (conversion on the commission too, bad inputs refused
on entry, leverage required, the missing tests), or recorded. A second blind reviewer read
the repairs and found nothing blocking; its three minor findings, inputs that slipped past
a check on entry (a currency other than pounds or dollars, a leverage of 2.5, an infinite
capital), are each now refused and tested.

**His words.** In chat, Friday 13 November 2026, about 15:05 UK time. Offered a fifth each
with a 10% stop in the market's terms, a tenth each, the same 10% on every line's own
price, or a stop set from each line's own swings, he chose "Fifth each, 10% stop
(Recommended)".

---

## 2026-11-13 — the Telegram line is short: the phase and its step

**Asked.** The operator, in chat on 13 November: "for the telegram messages, can you make
each much shorter and to the point? just phase or sub-phases?" The line had grown to three
sentences: the pull request's title, the scenes count, and the next objective spelled out.

**Decided by the session**, as the desk's mentor (his standing ruling: sessions settle
intended behaviour themselves and record it). One line, under sixty characters, in three
forms:

    kestrel2 · Phase 2 · step 3 of 6 done · scenes 4/7 (#16)
    kestrel2 · Phase 2 complete · scenes 7/7 (#20)
    kestrel2 · housekeeping · scenes 4/7 (#17)

"Step 3 of 6 done" is the phase's ticked boxes out of all its boxes in `docs/PLAN.md`.
"Housekeeping" marks a change that ticked no step: a document, a chore, a repair. Steps
ticked in two phases by one change name both. The scenes count and the pull request's
number stay, so he can still ask about one change by its number.

**How it knows.** The line compares the plan's phase checklists just before the merge
(main's previous commit, fetched from GitHub) with just after it, and names the phases
whose ticked count rose. It reads the checklists, never the "Current objective" sentence,
so the plan can give each lane its own objective without changing the line. Only a box at
the start of a line under a `## Phase N` heading is a step; a box indented under a step is
part of it. A plan that loses its phase checklists or its scenes count turns the job red
rather than sending half a line, as before.

**Kept.** A missing secret still fails loudly, the bot key is still checked on entry and
never printed, and the delivery record is unchanged. The "🔔 ACTION:" he sees in front of
each line is not sent by the desk: `announce.py` sends the line alone, so that prefix
comes from his own Telegram client or a forwarder.

**Proven.** Eleven deliberate breaks were each caught by `tests/unit/test_announce.py`: a
ticked step read as housekeeping; an unchanged phase announced; a finished phase not
called complete; a phase's boxes running into the next heading; an indented box counted
as a step (missed on the first run; the tests now hold it); the plan compared with itself
instead of the previous one; the housekeeping mark dropped; a plan with no phases sent
anyway; the number dropped; the scenes count or the step count read from the old plan.

**Reviewed.** A blind reviewer found one thing to fix: two tests expected the step in
the live plan to be in phase 0, so ticking phase 0's last box, a documents change, would
have turned the check red. They now hold any phase. Its minor point was taken too: when
GitHub sends the previous plan in any form but base64 (it sends no content over 1 MB),
the job now stops naming that cause, not a plan with no phases. Its other points are
accepted as the design: a line naming two phases runs past sixty characters, and a box
un-ticked, or a phase renamed, reads as "housekeeping".

---

## 2026-11-13 — the week's usage on every Telegram line

**His choice.** In chat on 13 November, offered ways to see how much of his plan's weekly
allowance the desk's sessions use, he chose "Usage on each line, plus stop alerts
(Recommended)". This entry is the first half. The stop alerts are sent by the lane runner
from his PC, not by this line.

**How.** GitHub cannot see his plan's usage, so the figure travels in the pull request.
Each lane run writes one line in its pull request's description, exactly
`Weekly usage: 21%`. `announce.py` reads it from the merged pull request's description,
which comes back from the call to GitHub it already makes, and adds it to the line:

    kestrel2 · Phase 2 · step 3 of 6 done · scenes 4/7 · usage 21% (#16)

**Never a guess, never a red job.** A pull request made by hand has no such line, and its
Telegram line says `usage n/a`. So does a line that is not exactly of that form: words
before or after the figure, no percent sign, a fraction, digits in another script, or a
figure over 100. The figure is read only from a line of its own, so a sentence that
mentions weekly usage is not taken for it. Two such lines also give `n/a`: an example
quoted beside the real one, or a stale figure left in, could say different things, and
picking one would be a guess. A missing figure never stops the job; everything that stopped
it before still does.

**A snapshot.** The figure is the usage when the pull request was written, not when it
landed. A lane run merges within minutes, so the two are close; a hand-made pull request
has no figure at all.

**Longer than sixty characters.** The usage figure adds about twelve characters. The
length check on the live plan's line now allows 72. That is a change of requirement, his
choice of usage on each line, not a test loosened to pass.

**Proven.** Fourteen deliberate breaks were each caught by `tests/unit/test_announce.py`:
a figure over 100 let through; 100% refused; the figure found partway along a line; no
percent sign needed; words after the figure accepted; a Windows line ending refusing the
figure; only the description's first line read; a missing figure shown as 0%; 0% shown
as n/a; the usage left off; an empty description failing the job; the first of two lines
taken; digits in any script accepted; the figure taken from another pull request. The
earlier eleven breaks are still caught. The tests stay within the product's size: one
test was folded into another, and a duplicate case dropped, to fit.

**Reviewed.** A blind reviewer found nothing blocking. Its one medium finding was taken: a
description holding both an example line and the real one used to give the first figure,
and now gives `n/a`. So were two minor ones: digits only from 0 to 9, and a test for
spaces after the figure. Its point that a line naming two phases and the usage runs to
about ninety characters is accepted; such a merge is rare.

## 2026-11-13 — three lanes, each a chain of sessions, day and night on his PC

**Decided.** The desk is built by three lanes at once: MONEY (scenes 4 to 7), DATA (the
rehearsal data, the parked lines, the store's open findings) and LADDER (phase 4). Each
lane is a chain of Claude Code sessions, each starting as soon as the one before it ends,
each in its own fresh copy of main. A runner on his PC starts them, outside this
repository (canon A3: tooling lives outside the tree), launched by a Windows scheduled task
when he logs on. Each lane owns its files and its own sections of the shared documents
(`docs/PLAN.md`), so their pull requests never touch the same lines.

**His words**, in chat on Friday 13 November 2026: "i need each session chained onto the
next, to run 24x7, whilst watching token use". Asked where, he chose "On this PC"; how many
lanes, "Three lanes (Recommended)"; which account, "Start on my account now" (the second
GitHub account stays an open question); what sessions may do unasked, "Bypass all
checks"; and what they may spend, "Plan limits, never extra (Recommended)".

**What this means.** No session buys usage beyond what his plan includes: when the plan's
limit is reached, every lane waits until it resets and then carries on. A lane stops, and
leaves a note in the runner's report, after two sessions in a row that land nothing or end
red (canon A8). Sessions never dial the live port, never touch the predecessor's folders
or its scheduled tasks, and everything they do is paper.

**The cost.** Three lanes draw on one plan, so each moves at about a third of the pace one
lane would when the plan's limit binds. Parallel work can be green apart and red together;
the next decision closes that.

## 2026-11-13 — nobody is watching a lane, so it decides for itself

**Decided.** A lane session that meets a question of intended behaviour decides it itself,
as the desk's mentor, from the north star, the scenes and his past rulings. It writes the
options, its choice and the reasons in its lane's part of this file, and carries on. It
still stops for what is his alone: going live, credentials, spend, permissions, moving the
phase, and loosening a guard. Then it writes the question, with options and a
recommendation, in its STATUS section, and lands what it has.

**His words**, in chat on 13 November 2026: "i am not the expert. you know the north star
and goals and requirements, so, as the elite desk mentor, you can make the decisions.
remember this is all paper trading and not real money".

**The cost.** A decision he would have made differently can stand for a while. Each one
is in this file with its options, so he can overturn any of them in a sentence.

## 2026-11-13 — a branch must hold everything on main before it merges

**Decided.** The ruleset `main-guard` now requires a pull request's branch to be up to date
with main before it merges ("require branches to be up to date", GitHub's strict status
checks), on top of the green `check` it already required. A tightening, so it merged like
any change.

**Why.** Three lanes now open pull requests side by side. Two can each be green on their
own and red together: one lengthens the rehearsal data while another writes a scene that
assumes the old length, or both add unit tests that together pass the product's size.
Before this, GitHub would merge both and main would go red with no Telegram line to say so
(the line waits for a green check on main). Now the second waits until it holds the first,
and its check runs again on the combination. The runner brings a lane's branch up to date
with main, re-runs the check on the PC, and pushes, so GitHub checks it again before
auto-merge can land it.

**Driven red.** Pull request #16 was built on main as it stood before #15, with a harmless
one-line change. Its `check` passed and GitHub marked it BEHIND. `gh pr merge 16 --squash`
was refused: "the head branch is not up to date with the base branch". Armed for
auto-merge, it stayed BEHIND and did not merge. It was closed unmerged and its branch
deleted. The ruleset still lists no one who may bypass it.

**The cost.** Each lane's merge can make the other lanes' open pull requests wait for one
more check run, about two minutes each.

## 2026-11-13 — the lanes stop at 80% of the plan's week

**His ruling**, chosen from options in chat on 13 November: "Yes, pause at 80%". The other
20% of each week is his own.

**How.** Before every run, the runner reads the plan's weekly usage. The figures come from
the plan itself: a one-word session on the smallest model, which reports the plan's
windows the way every session does. A reading counts only if it is under twenty minutes
old and taken since the window last reset. At 80% or more of any weekly window, no run
starts: every lane waits until that window resets, the pause is written in the usage log,
and he gets one Telegram line. The account refuses extra usage ("overage rejected" in the
plan's own report), and no API key reaches a session.

**Driven.** A stand-in session reported 85% of the week with a reset a minute away. The lane
paused, logged the cap and the pause, and sent the line. After the reset it read the
plan again, found 20%, and ran its session.

## 2026-11-13 — the lanes' models: quality first, then measure

**His ruling**, from options: "Quality first, then measure (Recommended)". Every lane run
is Claude Opus 5.5, at high effort on MONEY and medium on DATA and LADDER. Inside a run,
chores (rebasing, document lines, driving the deliberate breaks) go to helpers on Claude
Sonnet 5.5; blind reviews stay on Opus. The usage log keeps each run's model, effort and
tokens, and the runner's report gives tokens per landed pull request per lane, so after
three nights the choice can be compared and changed.

## 2026-11-13 — the runner's own Telegram lines, and the week's usage

**His ruling**, from options: "Usage on each line, plus stop alerts (Recommended)". Each
lane run's pull request carries `Weekly usage: N%` on a line of its own, the highest weekly
window. The session writes it, and the runner writes it again from the plan's figure when
the run ends. The runner sends its own line when a lane pauses at the cap, stops after two
failed runs, stops for any watch below, finishes its book, or stops for a decision that
is his alone. It reads the bot key and chat id from a file beside the runner on his PC,
which he copies there himself. The key never appears in a log or on a command line, and
sessions are walled off from that folder.

## 2026-11-13 — no nesting

**His ruling**, from options. A lane run never starts another session or another runner;
helpers inside a run are fine. That means three lanes, one process per lane at a time, and
nothing more. The runner holds a lock per lane and refuses a second process for a lane
that a live process holds. It refuses a second runner. Sessions are denied the commands
that start Claude or the runner.

**Driven.** A lane held by a live process was refused, a lock left by a dead process was
taken over, and the lock was released at the end.

## 2026-11-13 — mechanical guards against doom loops, sprawl and bloat

**Asked** by the operator before the lanes run unattended. Rules in a session's prompt are
not enough. Five guards, each driven against a deliberate violation (canon A7):

1. **A lane changes only its own files, enforced by the check.** A branch named
   `lane/<lane>-...` (the runner names them) may change only its lane's modules (under its
   heading in `manifest.toml`), their unit tests, the files the manifest's new `[lanes]`
   table gives it, and the shared documents. It may also add lines registering its own
   modules. Anything else fails `tests/guards/test_lanes.py`: another lane's code, a
   guard, CLAUDE.md, the workflow, or the ownership table itself. Seventeen cases were driven
   in a copy whose main held the guard, and each behaved as intended. The first drive found
   a defect: git's header lines were read as edits, so a lane registering its own module was
   refused. That is fixed. On GitHub, pull request #25 (branch `lane/data-probe`) added one
   comment line to `desk/orders.py`, the money lane's file. The check failed on both its
   push and its pull request: "the data lane may not change ['desk/orders.py']". It was
   closed unmerged.
2. **No change grows the product by more than 300 lines.** Any branch adding more than 300
   net lines to `desk/` and `lab/` together fails the same file's second test. Driven: 300
   passes, 301 fails, on a lane branch and on any other. The phase ceilings stand.
3. **No progress: halt.** A lane whose last three landed pull requests ticked no box in its
   book (for MONEY: and did not raise the scenes count) is halted, with a line to him.
   Driven: two such landings left it running, the third halted it; a ticked box, or for
   MONEY a scene passing, reset the count.
4. **A recurring fix: halt** (canon A2). A landed `fix` that touches a code file another
   `fix` of the same lane touched within its last ten landings halts the lane and names the
   file, so a session he starts records it in `docs/FAILURE_PATTERNS.md` with its guard.
   Driven: a second fix to the store halted the lane and named the file. These did not
   halt it: two fixes touching only documents, a fix after a feature, a fix more than ten
   landings later, and another lane's fix.
5. **A line at 07:00.** Every morning at 07:00 UK he gets one line: scenes passing, desk,
   lab and test lines, the share of fixes in the last 24 hours, the week's usage, and each
   lane's state. If he hears nothing at 07:00, something is wrong: the alarm on silence.
   Built from the live repository on 13 November, it read: "morning · scenes 4/7 · desk
   1,096 lines · lab 166 · tests 1,809 · fixes 2 of 21 in 24h · usage 13% · ...".

Guards 1 and 2 tighten the check, so they merge like any change. Guards 3 to 5 are in the
runner, outside this repository. A lane that finishes its book is halted too, with a line
asking for its next book.

**Gap, recorded.** Guard 1 judges a lane by whole files. It does not check that a lane writes
only in its own section of a shared document; the daily audit looks for that.

**Learned the hard way.** The runner's first stop for these guards ended its own process
and left one session running orphaned (it was ended, and nothing of it was pushed). The
runner now has "drain", which lets each lane finish the session it is in and then stops,
separate from "stop", which ends everything at once. Driven: a drain during a running
session let it finish and record its run. Its copy was tidied and the runner ended, with
no orphan left.

## 2026-11-13 — an independent audit every morning

**His ruling**, from options: "Yes, daily audit". At 05:30 UK the runner starts one fresh
session on Claude Opus 5.5 at medium effort, in a fresh copy of main. It may only read: it
has no tools to edit or write, and only git's and GitHub's reading commands. It reads
every change that landed in the last 24 hours against the canon, the lanes' ownership,
the failure patterns and the size rules. It reports each finding with its file, line,
severity and lane. The report is kept in the runner's logs and summarised after the 07:00
line as "audit: N findings (B blocking)". A blocking finding halts the lane it names until
a session he starts looks at it. It counts against the 80% cap, and is skipped and logged at it.

**Driven.** A copy of main was given one commit, as if from the data lane, with three
planted faults: a store test weakened to a bare truth check, the money lane's file edited,
and his 10% stop changed to 25%. The audit found all three, as blocking. It also found the
commit had skipped the lane's end-of-session record. It halted the data lane (in a scratch
copy of the runner's state) and wrote the line for him. It took 45 seconds; its tokens at
list price came to about $0.30, which the plan pays. Its real share of the week shows in
the usage log from its first morning.

## 2026-11-13 — five lanes, and phase 3 begins alongside phase 2

**His ruling**, chosen from options in chat at about 17:15 UK on 13 November: "Five lanes,
phase 3 now (Recommended)". He decides the phase, so phase 3's work starts now, alongside
phase 2. `BUDGET.json` keeps its phase; only the lab's ceiling moves (below).

- **MONEY** finishes scenes 5 to 7.
- **PAPER** (new) builds phase 3: the real paper-broker adapter behind the same interface
  as `broker.Pretend`, stops resting at the broker, recovery from a restart, then the
  morning and evening messages. Paper port 4002 only. The guard on 4001 stays, and
  sessions are now also refused any shell command that names 4001.
- **DATA** widens to the research universe (below), besides its book.
- **GRID** (from the ladder) builds the fast grid engine. Its parity test against the
  desk's engine on the golden data comes first (canon B2): it matches, or it is removed.
- **RUNGS** (from the ladder) builds the rungs: a planted edge caught and a non-edge
  rejected, luck correction counting every trial, in-sample and out-of-sample folds with
  the worst fold reported, and plateaus over peaks (canon B6).

No two lanes share a file. `manifest.toml` gives each lane its own heading over its
modules, and `tests/guards/test_lanes.py` refuses a lane's branch that changes another's.
The ladder's existing modules (`lab/cell.py`, `lab/batch.py`) go to GRID; RUNGS starts
with none. A branch naming a lane the manifest does not know fails the check, so the old
ladder's branch name cannot slip through unguarded. As the desk's mentor, the session set
PAPER's effort to high, like MONEY's: it is the code that speaks to a real broker. GRID,
RUNGS and DATA run at medium.

**Driven.** Fifteen cases, in a copy whose main held the change. These were refused: rungs
editing grid's module and its test, grid registering under rungs' heading, paper editing
money's broker, money editing the lab, and the old ladder's branch. Rungs and paper each
registering and writing their own module passed.

## 2026-11-13 — numpy, for the lab only

**His ruling**, from options: "Allow numpy, research only (Recommended)". `numpy==2.1.3` is
pinned in `requirements.txt`, and is the one third-party package `lab/` may import
(`manifest.toml`). `desk/` stays standard library, and the wall guard enforces it.

**What it replaces.** The grid runs every strategy's rule over about 1,500 lines, sixteen
years of daily bars and many parameter settings. In plain Python that is loops over every
bar of every cell: rolling windows, cumulative sums, crossings, drawdowns, written and
kept by us, and slower than a night allows. numpy does the same arithmetic on whole arrays,
in tested code we do not maintain. The grid must match the desk's own engine on the golden
data, or be removed (canon B2).

**Driven.** Within the same fifteen: the lab importing numpy passed; the desk importing
numpy and the lab importing pandas were each refused by the wall.

## 2026-11-13 — the lab's ceiling raised to 7,000 lines

**His ruling**, to the question asked as a guard loosening: "Yes, to 7,000 now
(Recommended)". In `BUDGET.json`, phase `2-money-sim`'s `lab_lines` goes from 1,500 to
7,000: the phase 4 figure agreed before phase 0. Nothing else in the budget changes. The
change travels alone, in its own pull request with his words in its description. A session
may not arm a guard's loosening on a yes relayed through another session, so he merges
that pull request himself. Until he does, the lab's ceiling stays at 1,500.

**Driven.** With the ceiling at 7,000, a lab of exactly 7,000 lines passed, and one more
line failed it.

## 2026-11-13 — the research universe: about 1,500 tickers first

**His ruling**, from options: "About 1,500 first (Recommended)". The S&P 500, the Nasdaq
100, the FTSE 350 and about 200 of the most-traded ETFs, daily since 2010, from the free
archive, through the one store's checks. This is a research list, kept apart from the
twenty trading lines in the instrument master: nothing on it is traded. The full 5,000
and more comes after the grid's first pass works. It is DATA's lane objective now,
because the grid needs it.

## 2026-11-13 — the ladder lanes run on Fable's allowance

**His ruling**, from options: "Use them for the lanes (Recommended)". GRID and RUNGS run on
Claude Fable 5.2, which has its own allowance, up to half of the weekly limit. A Fable
reset gives back what Fable used of the weekly limit. He has two Fable resets (to 9 March
2027) and one weekly reset (to 10 December), and clicks them himself.

**How.** The runner reads Fable's window from the same rate-limit report the sessions
give for the week; the plan calls it `seven_day_overage_included`, and it appears only
in Fable sessions (seen 13 November: 2% while the week stood at 15%). The 80% pause stays on the all-models week alone. A session refused on
Fable's allowance pauses only the two Fable lanes. At 90% of Fable's allowance he gets one
line: "a Fable reset would help now". When every lane waits at 80% and the week's reset
is more than twelve hours away, he gets one line: "the weekly reset would help now".

**Driven.** Eighteen cases with the plan's report played back:
- With Fable at 95% and the week at 40%, no lane waited and the Fable line went out once.
- With the week at 82% and twelve hours or more to go, every lane waited, the reset line
  went out once, and the pause was logged.
- With the week at 85% and three hours to go, they waited without the reset line.
- A Fable refusal paused only the Fable lanes.

## 2026-11-13 — the old desk's tasks are all disabled

**His check**, as administrator in Task Scheduler on 13 November: '"Right-click any
KESTREL_ task".....all say "disabled"'. The eight a session could not disable earlier are
disabled too. The PAPER lane may use the shared paper account on that basis; the daily
read-only check of its positions and open orders stays, as the proof each day.

## 2026-11-13 — auto-tune, so the grid can never take the PC down

**His words**: "we need to use auto-tune to make sure we do not run out of cpu or memory.
in the first repo we ran a program called backtest with an argument of '123456'. this
sometimes ran out of memory and crashed the pc." It belongs to GRID, built before the
first big pass. A hard memory ceiling held by Windows itself, not only watched (a Job
Object on the worker processes, about 60% of the 64 GB). Workers sized to free cores: two
of the eight threads left free while markets are open (UK 08:00 to 21:00 on trading days)
for the paper desk and the lanes, one overnight and at weekends. Batches sized from
measured memory per cell, bars read per ticker, never the whole universe at once. Backing
off (fewer workers, smaller batches) under about 25% free memory or above about 85% CPU
sustained, and stepping back up with room. Peak memory and CPU logged for each pass. It is
proven when a deliberately memory-hungry cell is killed by the ceiling, the PC stays
responsive, and the batch carries on. The predecessor's backtest tool is a quarry only.

## 2026-11-13 — SimCity, small, after scene 7

**His question**: when will SimCity work? The old desk's SimCity ran hundreds of whole
trading lives over saved bars with the market shut, with a census so every part of the
desk had a scenario. It goes in MONEY's book right after scene 7, kept small: one command
runs the whole desk's day over all fourteen months of rehearsal data against the pretend
broker with its faults, every night, and writes one record; a census names every part of
the money path and turns red when one has no scenario.

## 2026-11-13 — conformance trades, UK and US, in phase 3

**His question**: which phase runs them? PAPER's, as phase 3's proof that the pretend broker
behaves like the real one. On paper only, on one London and one US line, in each market's
hours: a market buy at the open; the resting stop placed, triggered, and cancelled on a
sale; a partial fill if the paper broker gives one; a rejection. Each real result is
recorded beside the pretend broker's, and the pretend broker is fixed where they differ.
A small matrix, not the old desk's 48 cells.

## 2026-11-13 — Fable first, then Opus; and when to press a reset

**His rulings**, refining the two above on models and Fable. Every lane runs on Claude Fable
5.2 while Fable's allowance is under about 45%, then on Claude Opus 5.5 (high effort on
MONEY and PAPER, medium on the others) until a Fable reset refills it. Fable's use can be
given back by his two Fable resets; Opus's cannot. A session refused on Fable's allowance
carries on on Opus. The usage log keeps tokens per landed change per model, so the two can
be compared on quality and cost.

He presses the resets himself; the runner tells him when, by these rules:
- "Press the Fable reset now" when Fable's allowance is at 45% or more and the week's reset
  is more than 36 hours away;
- "Press the weekly reset now" when every lane waits at the 80% pause and the week's reset
  is more than 36 hours away;
- within 36 hours of the week's reset, never: the lanes wait;
- once, a week before 10 December, a reminder that the weekly reset expires unused.

After any reset the runner reads the new usage and the new reset time from the plan, and
never assumes the reset stays on Thursday. While the lanes wait at the cap, it reads the
plan again every quarter of an hour, so a reset he presses lets them carry on at once.
(The 45% figures above were read on the wrong scale: see the next entry.)

## 2026-11-13 — Fable's figure is a share of Fable's own allowance: switch at 97%

**The evidence.** From 17:37 to 20:08 every lane ran on Fable. The Fable window the plan
reports (`seven_day_overage_included`) rose from 20% to 33%, 13 points, while the
all-models week rose from 25% to 33%, 8 points. Were Fable's figure a share of the week,
the week would have risen at least as much. So it is a share of Fable's own allowance
(about half the week), and 100% means Fable is full. Switching to Opus at 45% would have
thrown away more than half of the allowance his Fable resets give back.

**His ruling**, in his own chat at 20:12 UK: "Please use all fable tokens and then flip to
opus overnight. I can then reset fable in the morning around 8am". So:
- the lanes stay on Fable until 97% of Fable's own allowance, or until Fable refuses a
  session, then run on Opus;
- no request to press the Fable reset before bed or overnight: at 21:45 the runner only
  logs its forecast;
- "press the Fable reset now" is sent by day only (08:00 to 22:00) at 95% or more, with the
  week's reset more than 36 hours away; so a Fable that filled overnight is asked for at
  08:00. The Fable figure is read every 15 minutes, so the lanes return to Fable as soon as
  the reset shows;
- the weekly 80% pause reads only the all-models window, and stands as ruled, at all
  hours. Asked at 20:16 whether to run up to 95% of the week overnight instead, he answered
  "Keep 80": an option he considered and declined. He accepts that the lanes may pause at
  80% overnight until he presses the Fable reset at about 08:00.

**Driven** in a scratch home: the lanes on Fable at 33% and 96%, on Opus at 97%, and on
Fable when no figure is known; at 14:00, 94% asks nothing and 95% asks once; at 23:00 and
03:00, 99% asks nothing; at 08:00, 99% asks once; at 21:45, Fable at 60% rising four points
an hour and at 96% bring no request, only the forecast in the log.

## 2026-11-13 — the paper account is the old desk's

**His ruling**, from options: "The same paper account (Recommended)". The new desk connects
through port 4002 only, with its own client id. Before the PAPER lane sends its first
order, it must prove nothing else trades that account. Every day it checks the account's
positions and open orders, read-only, against the desk's own book, and flags a mismatch
(scene 6). The old desk's scheduled tasks were disabled, and he is checking the eight that
could not be seen without administrator rights. This is the first box of PAPER's book.

## 2026-11-13 — four gaps closed before the lanes run unattended

**Asked** by the session that set the lanes up, after a pre-mortem of five lanes running
overnight. Each gap is closed in the runner (outside this repository) or in a lane's book,
and each was driven.

1. **The Claude CLI is pinned.** An update overnight could change its flags under the lanes,
   as one version's refusal of Fable did on 13 November. The lanes run one version's own file
   (2.1.323), and their sessions have the auto-updater turned off. The version changes only
   when he runs the runner's update command. That updates the CLI, gives the new version
   one small Fable session, and pins it only if it passes. Driven: the current version
   passed and was pinned. A broken "new version" failed its trial in plain words, and the
   lanes kept the old one.
2. **Cross-lane requests are mechanical.** A lane that needs another lane's file changed
   writes a numbered request in its own STATUS section. The owner records it done or
   declined in its own (the rule is in `docs/PLAN.md`). The runner puts each lane's open
   requests at the top of its next session; a blocking one is the session's objective
   before its own book. The 07:00 line counts them, and one open over a day is sent to the
   operator once. Driven: open, ticked, done and declined requests told apart; a request
   wrapped over two lines read whole; each lane shown only what is asked of it; one line
   per request over a day, not repeated.
3. **IB Gateway is watched, read-only.** Every five minutes the runner knocks on port 4002.
   Every six hours it opens the API's handshake as its own client (917), reads the account
   and leaves. It sends nothing else and never an order. On 13 November the Gateway answered
   on 4002 only (4001 closed), every installation is set to paper, and the account it named
   is a paper one (its id starts DU). Fifteen minutes without an answer (longer than its
   daily restart) sends him one line saying a login may be his to do; its return sends
   another. Driven, with a dead port standing in for a logged-out Gateway: nothing at first,
   one line after fifteen minutes, no repeat, one line on its return. How the desk itself
   handles the daily restart and the weekly re-login is the first box of PAPER's book.
4. **The free archive is not hammered.** DATA's book now asks for slow, resumable fetching
   with backoff and cached raw answers, kept outside every worktree. While the archive
   refuses, the fetcher writes when that began to a file the runner reads; after six hours
   he gets one line, and the lane does other work rather than burn sessions retrying.
   Driven: two hours of refusal sent nothing; seven hours sent one line, once.

**Left with him.** A Windows Update restart overnight leaves the lanes stopped until he logs
in, because the runner starts at his logon. Starting it without a logon would need his
password stored in Task Scheduler, which is his to decide. He is pausing updates instead.

## 2026-11-13 — twelve sessions at once, held apart by claims

**Asked** by the operator at 18:25: "Up to 12 at once (Recommended)". Built by a session
started for it by the one that set the lanes up; the runner is outside this repository.

**How.** MONEY and DATA run three sessions each, PAPER, GRID and RUNGS two each. The runner,
not the session, picks the work: the first box of a lane's book whose note names its files,
whose `after` boxes are done, and whose files no running session holds. Those files are the
session's claim. A box with no note runs alone in its lane. The rule is in `docs/PLAN.md`
("The five lanes"); the claim is enforced in `tests/guards/test_lanes.py`, which reads it
from the pull request on GitHub (or from KESTREL_CLAIM on the PC) and refuses a lane's pull
request without one. The runner also refuses to land a pull request whose `Claim:` line is
not the claim it gave, and reads the worst of the two "check" runs (the push's and the pull
request's), since only the pull request's can read the claim.

**The shared documents.** Twelve sessions writing STATUS, SCOREBOARD and DECISIONS at once
would collide. So a session writes `Ticks:`, its status, decisions and requests in its pull
request, and a small scribe session per lane (Sonnet, about every two hours) folds them in.
A ticked box counts as done the moment its pull request lands, so the next box waits for no
scribe. The scribe also keeps each STATUS section under 50 lines, which the document guard
in #46 needs.

**The machine.** No session starts while under 25% of memory is free, while twelve run, or
while more than eight run and the grid's auto-tune says a pass is busy; one start a minute.

**Driven (canon A7).** The guard: 26 cases in a scratch clone, each failing for its stated
reason, among them a change outside the claim, STATUS without claiming it, a pull request
with no claim or two, a claim in a bullet, duplicate ids, an `after` naming nothing or
waiting on itself through others, a note without files or id; and passing for a claim kept, a glob, `*`, a scribe's four documents,
a push run with no claim to read, and a note shown in prose. The runner, with a stand-in for
sessions in a scratch home: 61 cases, among them two boxes on one file never side by side,
a box waiting for its `after`, a carry's files held while its slot is idle, a blocking
request draining its lane first, the memory floor and the grid's cap holding starts, a wider
claim disarmed, a red pull-request run not hidden by a green push run, and twelve slots
working a book through with a peak of nine sessions and no two claims ever overlapping. The
older drives were re-run on the new code; the only misses were words changed on purpose.
On GitHub, once the guard was on main (#69, #70, closed unmerged): a money-lane pull
request claiming `desk/day.py` and changing `desk/orders.py` failed its pull-request check
on exactly that, and GitHub showed it BLOCKED although its push run was green; the same
claim changing only `desk/day.py` was green and CLEAN. A first attempt from the guard's own
branch was refused by the older lane guard, rightly, as a lane editing a guard.

**Reviewed blind.** An independent reviewer found one blocking fault and six major ones, all
fixed and driven: after a restart two slots could carry one pull request; two landings at
once could lose a tick; GitHub not answering could free a claim whose pull request was open;
two globs covering one file did not clash; a session arming its own merge could land before
the runner read its Claim line (the runner now arms it, only after); two slots could swap
pull request descriptions; a lane with nothing it may start sat idle untold.

**Found on the way.** Taking over a lock left by a dead runner held the log's lock and then
waited for it: every lane would have hung after a hard stop. Fixed (a re-entrant lock) and
driven.

## 2026-11-13 — his hours, the before-bed reset, and the keeper's rounds

**His words**, relayed 13 November evening: "operator will typically sleep from 10pm to 8am.
operator will have smartphone and can approve things when requested."

1. **His hours.** From 22:00 to 08:00 UK a change's Telegram line is not sent; GitHub's job
   records it instead (`announce.py`). The runner's own news lines (the runner back, an
   outage over, a drain, a request waiting a day) wait too. At 08:00 one message carries
   the morning line, the audit's line, every change that landed overnight and the held
   lines. The audit moves from 05:30 to 07:30 and the morning line from 07:00 to 08:00, so
   both arrive when he wakes. Anything that needs him goes at once, at any hour: a reset to
   press, a Gateway login, a decision, a lane halted, a crash, the keeper missing rounds.
2. **The before-bed reset.** At 21:45 the runner forecasts the night from the last three
   hours' rate. If the lanes would reach the 80% pause before 08:00, it asks for the weekly
   reset before he sleeps, when the week is at 25% or more, its reset is more than 36 hours
   away, and the weekly reset is unused and unexpired; once a night. So a night is not lost
   to a pause nobody could answer. Fable is never asked for before bed: his ruling at 20:12
   is to use all of Fable, run on Opus overnight, and reset Fable at about 08:00.
3. **The five-minute keeper.** Once DATA's `desk/keeper.py` is on main, the runner runs
   `python -m desk.keeper` from a copy of main every five minutes, 08:00 to 21:00 UK on
   weekdays (London opens at 08:00, New York closes at 21:00). The keeper reads the
   calendars itself and exits at once when no venue is open, so holidays need no second
   calendar in the runner. Plain code, no Claude session, no tokens. Two missed rounds in
   a row reach him at any hour. DATA's sessions are told this contract.

**Driven** in a scratch home, 25 cases: news held at night and sent by day, what needs him
sent at once at 23:10, the 08:00 message carrying the night and clearing what was held, the
night's idle hours 22:00 to 08:00; the forecast asking for each reset when the pace crosses
the line before 08:00 and not when it is too small to matter, too slow, within 36 hours of
the week's reset, already used, or with no readings, and once a night; the keeper not run
outside its hours, at a weekend or before it exists, a round done, failed or hung, two
misses told at once even at night, and its return held for the morning.

---

# The lanes' own decisions

Each lane appends its decisions to its own part below, never to another's, so that
parallel pull requests do not touch the same lines. Each entry is a dated `###` heading
under its lane, and says what was decided, the options, why, and the evidence.

## 2026-11-13 — every requirement of his spec has a home; 31 dropped, 11 added, 3 lines swapped

**Found.** His spec, `DESK_REQUIREMENTS_V2` (226 rows, ratified 31 October 2026 and
reconciled then against his 947-line tenets list), was never traced row by row into this
desk. The scenes and the plan cited 31 of its ids. An independent trace on 13 November read
every row against main: 65 delivered or standing, 71 half delivered, 50 with nothing
planned, 9 replaced by his rulings of 13 November, and 31 not worth building. The holes
that mattered first: no plan item built the kill switch the canon promises (B1), though
phase 3 sends paper orders; nothing counted dividends; the research list held only today's
index members; and too few trades failed a strategy instead of saying "not enough
evidence". The trace is kept outside the repository, in the notes folder beside it.

**Decided, first: every gap into the books, the kill switch first.** Each half-delivered or
missing row is now a step in a lane's book or a phase in `docs/PLAN.md`, its ids beside it.
The kill switch and its drill head the money lane's new steps, and the paper lane sends no
order until it is drilled. The 65 standing rows are listed under "The requirements" in the
plan. A guard, `tests/guards/test_requirements.py`, holds all 237 ids (the 226 and the 11
below) and fails the check when any id has no home: a step, the standing list, or this
entry. His words: "All gaps into the lanes, kill switch first (Recommended)".

**Decided, second: 31 rows dropped, each for its reason.** His words: "Drop them, each with
its reason (Recommended)". Any one can come back by his ruling.

| id | dropped because |
|---|---|
| NS-09 | goals.json and a rendered status file per row: the scene ratchet and this guard replace it |
| NS-13 | the ALPHAHAWK rename is a ceremony; the desk is kestrel2 |
| GOV-03 | five states per row: replaced by a passing scene, or NotImplementedError listed in STATUS |
| GOV-11 | the old names it retires never existed here |
| GOV-12 | DEV and PROD rule tags: every guard is always on, and GitHub enforces them |
| MIG-08 | PROD rules switched on at go-live: there is no DEV and PROD split |
| DAT-06 | a weekly bottleneck review: optimise only on a benchmark (canon A4) |
| DAT-09 | a hot store and an archive: one store, rebuilt from the archive, one writer |
| DQ-04 | an independent data checker: data is checked once, at the boundary, by the one writer |
| DQ-13 | a stored indicator database: indicators are recomputed from bars; a copy is a second home |
| UNI-03 | weekly review of curation rules: there is no curation filter |
| STR-11 | losers parked, never deleted: git is the archive, and the ladder's verdict record serves |
| STR-15 | straddles, gappers and pairs: intraday and pairs are a future release |
| LAD-14 | a progress dashboard with heatmaps: resume and the runner's halts cover stalls |
| LAD-15 | GPU sweeps: numpy on eight threads suffices for daily bars |
| REG-06 | satellite and sentiment feeds: no evidence they pay, and each is an adapter to keep |
| REG-10 | explain "Alpha Lab": no such module |
| REG-11 | a regime four times a day: a daily desk has nothing that would read it |
| FIL-02 | guardrails justified by replay: there are no filters, only his rulings |
| FIL-05 | a daily funnel with chokepoints: one gate and five rules; the refusal reason says it |
| STP-04 | TP1, TP2 and TP3 on every position: the rules carry their own exits |
| EMG-05 | a small tail hedge as research: no case for it before the edge exists |
| MSG-01 | HTML, forty characters a line, emoji: presentation, not behaviour |
| MSG-07 | bold and monospace blocks: presentation |
| MSG-05 | findings filed as rows: STATUS "found, not fixed" serves |
| MSG-10 | bug and strategy messages filed as rows: as MSG-05 |
| MSG-06 | a weekend card: no decision depends on it |
| MSG-12 | sentiment, news and forecast cards: no decision depends on them |
| OPS-06 | clock drift: daily bars and next-open orders do not care about a second |
| TST-15 | a coverage percentage: the deliberate breaks prove more |

**Replaced by his rulings of 13 November (9):** NS-02 and MIG-09 by the A-GATE terms (AG-01
to AG-06); GOV-08 by Fable first, then Opus, and the 80% pause; UNI-08 by the twenty lines
he chose; STR-10, TRD-14 and SIZ-07 by a fifth of one capital number each, a leveraged line
counted at what it controls; STP-01's method by the stop where the market has fallen 10%
(set at entry, as it asked); TST-18 by the scenes rule, which has no list of known reds.

**Decided, third: eleven best-in-class additions the spec never asked for.** His words:
"Add all 11 at their gates (Recommended)". Each sits in the plan at its gate.

| id | the requirement | gate |
|---|---|---|
| BIC-01 | the edge judged against the market risk it took (beta, or a leverage-matched benchmark) | AG |
| BIC-02 | concentration: the book's number of independent bets, A-GATE profit split by correlated cluster | AG |
| BIC-03 | idle cash earns interest in the profit, and every Sharpe uses the risk-free rate | AG |
| BIC-04 | currency gains and losses on dollar holdings reported apart from trading profit | AG |
| BIC-05 | a fall from the book's highest point: alerted on paper, new entries stopped live | AG, LIVE |
| BIC-06 | an earnings and events calendar, point-in-time, for rules and stops | P100 |
| BIC-07 | the ISA's yearly limit and real pot size; paper re-scored at the size live can reach | LIVE |
| BIC-08 | records kept for their statutory years, reconciled each year to the broker's statements | LIVE |
| BIC-09 | if he does not acknowledge for a set number of days, no new positions; a named second person can sell everything | LIVE |
| BIC-10 | each strategy's capacity: the size at which costs erase its edge | P1000 |
| BIC-11 | leveraged products watched for closure, compulsory redemption and ISA eligibility | AG |

**Decided, fourth: three lines swapped now, for lines an ISA can hold.** SPY, QQQ and GLD are
US-registered funds a UK retail ISA cannot normally buy. Asked whether to keep them for
paper or swap now, he chose "Swap them now". Asked for each replacement: SPY becomes VUAG,
Vanguard's S&P 500 in pounds ("VUAG"); QQQ becomes EQQQ, Invesco's Nasdaq 100 in London
("EQQQ (Recommended)"); GLD becomes IDTL, iShares' US Treasuries of 20 years and more,
in London, which takes the twenty off a third gold line ("A different market: IDTL
(Recommended)"). The twenty become thirteen on the London venue and seven in the US. The
swap heads the data lane's book, with an ISA and retail-buyable flag on every line and the
hold-the-market yardstick re-pointed.

**Merging.** He asked, the same evening, that merges never wait for his click: "i asked for
auto merge to be turned on permanently. you need to do this yourself." Every change is
armed to merge itself when its check is green. A change that loosens a guard still needs his
plain yes, as CLAUDE.md says; the session he gives it to, in its own chat, arms it. A yes
relayed from another session is refused by the sessions' own permission check, so a lane
that needs one asks him through its Telegram alert, and he answers the session he is
talking to. Pull requests #36 and #37 were armed that way at about 17:30 UK.

**Driven.** From a passing copy, each break alone: the kill switch's id removed from both
of its steps, a dropped id put back on a step, a dropped row's id lost, an id taken off the
standing list, an id the spec does not have, an addition's id removed, and the roster short
by one. All seven were caught. Removing the kill switch's id from one step only passes, as
it should: the paper lane's step still homes it.

**His words, together.** In chat, Friday 13 November 2026, about 17:45 to 17:55 UK time,
each chosen from options with a recommendation.

---

## 2026-11-13 — the weekend sprint: resets spent now, twelve sessions, and the A-GATE clock

**Why.** At 18:20 UK he judged the target dates far too long and asked for ten times the
pace. Building phases 2 to 4 is where the tokens go; once built, the desk trades paper as
plain code and costs almost none. And the A-GATE's dates are set by the calendar, not by
building, so only its terms could bring them forward.

**Decided, first: the free resets are spent this week.** Every lane runs on Fable while
Fable has room, then on Opus. The runner's Telegram line tells him when a Fable reset (two,
expiring 9 March 2027) and then the weekly reset (one, expiring 10 December) would help;
never within 36 hours of the weekly reset. The 80% pause stands. His words: "Spend them
now (Recommended)".

**Decided, second: up to twelve sessions at once.** Each lane runs two or three sessions
side by side on book items whose files do not overlap; a session claims its item and files
first, the runner starts nothing that overlaps a running claim, and the check fails a
change outside its claim. Items that must go in order stay in order. His words: "Up to 12
at once (Recommended)".

**Decided, third: the A-GATE clock (AG-02 to AG-06 amended, AG-01 kept).** A candidate's
paper days now count from the first clean FIRST-LIGHT day, or from the day it passed the
ladder if that is later; they no longer wait for FIRST-LIGHT's ten days to finish. Up to
ten candidates run side by side on the one paper account, each with its own capital number
and its own book, each named in `docs/PLAN.md` before its first paper day. Every one counts
as a trial in the luck test, and one dropped part-way still counts, so trying several
raises the bar rather than lowering it. His words: "Both (Recommended)", offered against
"Only the side-by-side candidates" and "Neither".

**The cost.** The resets give about two and a half weeks of allowance this week and none
in reserve until the weekly allowance renews. Twelve sessions mean more changes landing
on main at once; the check, the claims and the lane guards hold them apart. The FIRST-LIGHT
days now carry a candidate's money as well as the machine's proof, so a FIRST-LIGHT day
that is not clean is also a lost A-GATE day.

**His words, together.** In chat, Friday 13 November 2026, about 18:25 UK time, each
chosen from options with a recommendation.

---

## 2026-11-13 — deep and five-minute data, kept hot; trustworthy rungs; the eponymous strategies first

**His asks, about 18:35 UK.** A database of many years for backtesting, like the old Stooq
data; a hot store of a week of five-minute bars; a monitor that keeps all data fresh; the
eleven rungs made trustworthy, "the biggest issue in the previous repo"; and the eponymous
strategies through the ladder first.

**Decided by the mentor, as his rulings allow.** Daily history is carried back to 2000
where the archive has it. A five-minute store starts now, for the twenty lines: the free
archive keeps only about sixty days of five-minute bars, so every week not collected is lost
for good; the last week is kept hot and nothing is thrown away. The store's keeper runs on
every trading day after the US close and before the London open, with an alert for a stale
line or a missed run. The rungs lane makes each of the eleven rungs pass its own known-answer
test before any verdict counts: a planted edge passes, pure noise passes at about the stated
rate, a power curve, a broken rung caught, and every defect the old desk's rung audit of 20
October found kept as a failing case. The twenty-one eponymous strategies go through first,
each with its published figure written down so that reproduction can run.

**The old desk's "Yeager" speed-up** was computing an indicator once over a whole series
instead of again for every bar. The grid lane's numpy engine is that method, held to the
desk's engine by a parity test (canon B2); its old desk equivalent had parity tests that
were red on main.

---

## 2026-11-13 — hot every five minutes, a crash watch, and one fast store

**His words, about 18:55 UK:** "please confirm that it runs during the trading data every
5mins? we need hot data every 5mins. this is paramount. if a crash event happens then we need
5min price and indicator data to immediately flag a crash situation". And: "the data quality
monitor needs to make sure ticker price and all indicator data is always hot ... we need a
high performance way to reading and writing to a database." And: "any tickers with suspect
data issues are checked, but, then parked ... one ticker with bad data should not stop all
trading."

**Decided by the mentor, as his rulings allow.** During each venue's trading hours the
keeper takes every clean line's newest five-minute bar every five minutes, checks it on
entry, and updates every indicator the rules and the crash watch read. A late, missing or
out-of-line bar parks only its line, at once; the rest carry on, and a line that comes clean
returns by itself. A crash watch on those bars halts all buying the moment a fall crosses
the emergency thresholds, and alerts him at any hour. Hot and deep data share one store,
SQLite in WAL mode (standard library, one writer, many readers), held to benchmarks set in
advance. DAT-04, dropped earlier this evening for want of a benchmark, is restored: he has
now set the need, and the benchmarks are its test.

**The source.** He already pays for IBKR's market data and uses the free archive as a
second source (his words: "i already pay for ibkr market data and use yf.download as a second
source"). So the hot bars come first from the broker, read-only through the paper port, and
the free archive checks them. No new spending. The paper account must see his live data, not
the delayed kind; the data lane proves that first, read-only.

---

## 2026-11-13 — tests up to 1.5 times the product; the recommended option, always

**Found.** With ten sessions adding tests side by side, the rule "unit tests may not exceed
the product's lines" sat at exactly its limit (2,861 lines each), and at 20:57 a data-lane
change went red by eight lines once it held main. The work next in line - the kill switch,
the money invariants, the eleven rungs - properly needs more test than code.

**Decided, first.** Unit tests may reach 1.5 times the product's lines (`BUDGET.json`,
`unit_test_lines_per_product_line`). The guard still stops test-per-bug piles; 1.5 is a
ceiling, not a target. A loosening; his words below are its yes. Driven: tests at 1.2 times the
product fail at 1.0 and pass at 1.5, and tests grown past 1.5 times fail.

**Decided, second: the recommended option is taken without waiting.** A question put to him
with options and a recommendation no longer waits for his answer: the session takes the
recommended option, records it here, and tells him on Telegram. That includes loosening a
guard, moving the phase and permissions. He alone still decides going live, entering
credentials and spending money; no real money moves until he signs for going live. A
session whose own permission check will not arm a loosening on this standing ruling leaves
it armed-ready and named in its STATUS section, for the next session he talks to.

**His words.** Friday 13 November 2026, about 21:05 UK, offered "1.5" (recommended) or "keep
1": "1.5 . please always go with recommended to avoid waiting for me to attend."

---

## MONEY

### 2026-11-13 — how the pretend broker behaves

**Decided**, by the lane as the desk's mentor (no one watching), for scene 4 and after:

1. **A buy fills at the opening price of the day the market is open**, for the whole order.
   The desk decides after a day's close and its order meets the next open. Options were the
   open, the close, or the price the order was sized at. The open is what a market order sent
   overnight gets. The close would be a price the desk had not seen when it sent the order.
   The sized price would make every gap free.
2. **A stop is tested on the day of its buy too**, against that day's whole range. Testing
   it only from the next day would let a buy whose market fell through the stop the same
   afternoon escape the loss. That is an optimistic fill, and the desk's measurements must
   err the other way. A day that opens below a stop sells at the open, not at the stop.
3. **One stop per line.** A second buy of a line held adds its shares to the line's one
   stop, at the newest order's level. The book is to give each line one fifth (his ruling
   on sizing), so a line is one holding, with one protection. The other option, a stop per
   order, could leave two levels on one holding.
4. **A fault hits a symbol's first order that meets a market.** An order sent before the
   open, or on a day its line does not trade, is refused with that reason and leaves the
   fault waiting (the blind review's finding: a fault used up on such an order never
   happened at all). A partial fill gets half, rounded down, and the rest is cancelled. A
   dropped connection means the order never reached the broker. A crash means the broker
   has it, and has filled it, but the desk has no answer.
5. **The desk asks before it sends again**, as with Interactive Brokers: the broker answers
   `report(order_id)` with what it did, or nothing if it never received the id. A repeated
   id is refused with a reason, never filled twice, and still counted as received, so
   scene 4 sees a desk that sends twice.
6. **A position planted by hand has no fill and no stop.** The broker reports it among its
   positions only, as a real account shows a hand trade made elsewhere; scene 6 must find it.

**Evidence.** `tests/unit/test_broker.py` failed first on the unbuilt broker. Thirty
deliberate breaks of `desk/broker.py` were each caught. Among them: the order's own id
used as the execution id, no stop left after a fill, a partial fill filling in full or in
silence, a fault outliving its first order, a disconnected order counted as received, a
crash losing the broker's record, a duplicate filling again, a gapped stop selling at its
level, no stop test on the day of the buy, a fill at the close, and a fault spent on no
market.

### 2026-11-13 — the send path: ask first, gate second, a fill written once

**Decided**, by the lane as the desk's mentor (no one watching), for scene 4:

1. **The desk asks the broker before anything else.** If the broker already has the order's
   id, the desk records what it did and sends nothing. Only an order the broker never
   received goes through the pre-trade gate and is sent. The other option, the gate first,
   would judge an order the broker already holds a second time: after a restart with a
   changed capital it could be refused, and its fills, real at the broker, never written.
   Every order the broker receives still passed the gate on the way.
2. **A dropped connection is a stated answer, not a crash.** The order never arrived, so the
   desk says so in the order's reason and the same id may be sent again; the broker answers
   for it then. A crash after the broker has the order is the desk dying: it stops, and the
   next ask records what the broker did.
3. **The ledger is one file of fills, keyed by the broker's execution id**, written whole and
   swapped in, as the price store is, so a desk that dies mid-write keeps the old one. A
   fill already written is never written again, so asking about an order twice is harmless.
4. **The ledger learns only what the send path is told.** A stop the broker sells overnight is
   not in any order's answer; the book built from the broker (the next step) and the day run
   must collect it, or the ledger and the broker's fills part company.

**Evidence.** `tests/unit/test_book.py` failed first on the unbuilt send path; scene 4 now
passes. Eleven deliberate breaks of `desk/book.py` were each caught: never asking the
broker first, gating an order the broker already had (the blind review's one gap), skipping the gate, letting a dropped connection escape, not recording, recording a
fill twice, overwriting the ledger, counting the order's shares as filled, dropping a
reason, a silent disconnection, and a price read back rounded.

### 2026-11-13 — the book: the ledger's fills, read by the gate

**Decided**, by the lane as the desk's mentor (no one watching), for the gate and scene 5:

1. **The book is the ledger's fills added up, line by line.** Never the orders meant, and
   never the broker's own positions: the book is what the desk itself knows, so scene 6 can
   compare the two. A position bought by hand at the broker is not in the book; finding it
   is reconciliation's job, not the gate's.
2. **The send path brings the ledger up to date before the gate looks.** It writes every
   fill the broker made that the ledger lacks (`book.collect`), so a stop sold overnight,
   which is in no order's answer, frees its holding before the next buy is judged. The
   other option, leaving that to the day run, would let a caller that forgot judge a buy
   against a book that still holds the stopped line.
3. **A line's shares, held and ordered, are counted together at the order's price and
   rate** against its one fifth. Options were the price paid, or today's price. Today's is
   what the line is worth now, which is the risk the fifth limits; the price paid would
   also need each fill's exchange rate, which the ledger does not keep. So a line that has
   risen leaves less room for a second buy, and one that has fallen leaves more.
4. **A sixth line is refused; a second buy of a held line is not a new holding.** The
   sizer gives a second buy what is left of the fifth and passes it through the same gate,
   so the rule lives in one place.
5. **A ledger that sells more of a line than it bought is refused loudly**: the desk is long
   only, so such a ledger is broken, and the book says which line.

**Evidence.** `tests/unit/test_book.py` and `tests/unit/test_orders.py` failed first on the
unbuilt book and the one-holding gate. Fifteen deliberate breaks were each caught: no
collect before the gate, an empty book given to the gate, collect writing nothing, the
book counting buys only, a line sold out still counted, the long-only check removed, sales
counted as buys, the five-holding check removed or off by one, a held line counted as a new
holding, held shares ignored or counted twice, the sizer not subtracting what is held, the
sizer skipping the gate, and a full line sized to no shares. A blind review found nothing
blocking: its fix (a stop sold on its buy's own day reached the book only on the next send)
and its test gap (a crashed order's fill must count as a holding) are taken, the second
driven by removing the first collect.

### 2026-11-13 — the day run: whose position, which day, which rate

**Decided**, by the lane as the desk's mentor (no one watching), for scene 5 and after:

1. **A rule's position is the book's, not its own idea.** Options were (a) each rule
   counting its own buys and sells as done, the book only refusing what it cannot do, or
   (b) each rule told, on the day it decides, whether the book holds the line for it. (a)
   leaves a rule whose buy was refused, or whose stop sold, believing it holds: it will not
   buy again while its condition lasts and later says sell to a flat book. Chosen (b)
   (`strategy.today`). The rules' indicators do not depend on what they hold, so the same
   history gives the same bands either way.
2. **A line is one holding, owned by the strategy whose buy opened it** (the strategy in its
   latest buy's order id). Only that strategy's sell sells it, and it sells the whole of
   what the book holds. While a line is held, the other four rules' signals on it are not
   acted on. Of several rules buying one flat line the same day, the first in the
   operator's list of five buys it. The other option, a position per rule within the
   line's fifth, needs a stop per rule, which the broker's one stop a line (decided above)
   does not give.
3. **Sales first, then buys, each sized from the book after the send before it.** A sixth
   line is refused by the gate and kept among the day's answers with its reason, never
   dropped. A line sold that morning, by its rule or by its stop, is not bought again the
   same day: its stop was judged against the whole day before the new order, and could
   sell it twice on one bar.
4. **Only decisions dated the line's venue's session before the day are acted on**, and
   only on a day its venue trades. A line whose bars stop earlier is left alone that day.
5. **The day run is given the day's pounds per unit of each currency, and keeps it**
   (`rates.csv` beside the ledger). Each fill is now dated by the broker, so a round trip
   prices each leg at its own day's kept rate. Options were a rate in the fill (the broker
   does not report one), one rate for the whole run (wrong for a trip that spans a move in
   the pound), or looking it up again later (not the rate of the day). The scenes give 0.79
   every day; a daily rate in the store is asked of the data lane.
6. **A round trip pairs each sale with the buys it closes, oldest first**; a fill split
   between trips shares its commission and conversion by its shares. Spread, slippage and
   UK tax are not yet charged: they belong to the day record (scene 7), where the spread
   and slippage of both legs, the stop's sale included, must be added.
7. **Scene 5 runs on the rehearsal's whole fourteen months** now, since no rule trades in
   the six weeks the other scenes still see. When the data lane moves the scenes onto the
   whole history, scene 5 reads the same data as the others.
8. **Scene 2 counts each line against its own venue's calendar** over the scenes' days:
   five decisions for every session the line's venue traded. Counting each line's own
   bars, the first form tried, could not fail (the blind review's finding).

**Evidence.** The new tests in `test_day`, `test_book`, `test_broker`, `test_orders` and
`test_strategy` failed first on the unbuilt code; scene 5 failed on the six weeks and passes
on the fourteen months. Twenty-five deliberate breaks were driven. Twenty-two were caught at
once: the open's stops not collected, buys sized from a stale book, a line sold that morning
bought again, a stale decision acted on, the book's holding not given to the rules, a sale
leaving its stop or taking all of it, a sale at the close, the gate letting one share too
many be sold, conversion on a pound line or on the wrong amount, a split fill's charges not
shared or its rest forgotten, the wrong day's rate, a sale counted as negative shares, a
fill's day moved, a missing rate not refused, a kept rate repriced, a zero rate, and a line
missing a day in scene 2. One, a pound rate other than 1, was missed because its test met
the "already kept" refusal first; the test now uses a fresh day and catches it. Two were
missed because the code did nothing (an owner check `strategy.today` already makes, and a
filter whose result was overwritten); both are removed.

### 2026-11-13 — reconciliation: before every order, shares and stops; and scenes 6 and 7 together

**Decided**, by the lane as the desk's mentor (no one watching):

1. **The book is checked against the broker's on the send path, before every order**
   (`book.reconcile`, called by `book.send`). Options were (a) once, in the day run after
   the open; (b) on the send path, the one door every order already passes. Chosen (b): a
   hand trade made in the middle of a morning is seen before the next order, and any later
   caller of the send path (the paper lane's) is held by it without being told to. It stays
   out of `orders.gate`, which is pure and is also the rungs lane's; the refusal is the
   same `Refused` the gate raises.
2. **A line differs when its shares differ, or when the stop resting at the broker is not
   for exactly the shares the book holds.** Every share the desk holds has its stop at the
   broker; a holding whose stop was cancelled is the most dangerous quiet state there is,
   so it is named like a wrong position. Shares alone, the scene's own words, would miss it.
3. **While any line differs the desk buys nothing; it sells a line only if that line's
   shares agree.** Options were (a) send nothing at all; (b) stop buying only; (c) stop
   buying, and never sell a line whose shares differ. (a) would hold a rule's sale of a
   sound line for as long as a person takes to look. (b) would sell the book's ten shares
   of a line of which the broker holds four, and leave the desk short. Chosen (c), with the
   blind review's point taken: a line whose shares agree but whose stop is gone may be
   sold, since that is the protective act. Nothing is remembered from day to day: the two
   books are compared afresh each time, and buying starts again once they agree.
4. **The day does not stop.** A refusal on the send path becomes that order's answer, with
   its reason naming the lines, kept with the day's others. The desk dying, or any other
   error, still stops the day.
5. **An order the broker already has is recorded, never refused**, whatever the books say:
   the broker is asked first, as before.
6. **Scenes 6 and 7 pass together.** The plan had reconciliation turn scene 6 by itself. It
   cannot: scene 6 asks that a reconciled day carry a profit, scene 7 reads the same
   record, and a profit is not published without every cost (canon B4). Spread, slippage
   and a sale's own cost are not in the cost model, and UK tax needs a fact on each line
   that the data lane owns. Options were (a) give scene 6 a record with the missing costs
   at nought; (b) take "a reconciled day has a number" out of scene 6; (c) land
   reconciliation under its own contract tests and turn both scenes when the record is
   real. (a) is a made-up number and (b) weakens a scene to count it. Chosen (c). The
   scenes stay at 5 of 7 for this step; the lane's book says what remains.
7. **Scene 6's days.** No rule holds a position at the end of the rehearsal data, on its
   six weeks or its fourteen months, so "the broker holds something" cannot be read after
   the last day. When the record lands, scene 6 will run the fourteen months and set the
   book against the broker's on every day, which asks more of the desk, not less.
8. **The kill switch is the lane's next objective, ahead of the costs.** His ruling of the
   same day, which reached this branch as it was finishing, puts the kill switch first and
   holds the paper lane's orders until it is drilled. Options were the costs next, as the
   scenes' order suggests, or the kill switch next. Chosen the kill switch: it is his word,
   another lane waits on it, and scenes 6 and 7 wait on the data lane's tax fact in any
   case, so the scenes lose nothing by it.

**Evidence.** Two contract tests seen failing first (`book.reconcile` did not exist; the day
sent five buys with a hand-bought line at the broker). Over the fourteen months, with and
without every line's first order rejected, the desk made the same 68 fills and 34 round
trips as before the change: in ordinary running the two books never differ. Thirty-one
deliberate breaks were driven first; twenty-six were caught and five missed, each a gap in
the tests: a line only the book holds, the names in no order, an order the broker already
has refused while the books differ, any error at all kept as an answer, and a cancelled
stop that also emptied the position. Tests were added for each. Thirteen more were then
driven, those five and eight against the review's fix; twelve were caught at once and the
thirteenth (a sale allowed when the broker holds more than the book) after its test was
tightened. The blind review, which ran 400 random runs of its own (20,907 orders, every
fault) without one false mismatch, found nothing blocking; what it left is in
`docs/STATUS.md`.

### 2026-11-13 — one rule for "is the book the broker's?", for every broker

**Decided**, by the lane as the desk's mentor (no one watching), on the paper lane's request
R-PAPER-1: the comparison of the desk's book with a broker's holdings has one home,
`book.differences`, and reconciliation (`book.reconcile`, `book.send`) is rebuilt on it.

1. **What it is handed: the book, and the broker's entries, each a name and its shares.**
   Options were (a) the pretend broker's own answer, one number a line, which a real
   account's rows would have to be added together to fit, the very fault the paper lane's
   blind review found; (b) a typed holding carrying the real broker's own words (its kind
   of product, its currency), which puts one broker's language in the core and means
   nothing at the pretend one; (c) plain entries, each named by the door that read them in
   the same words it names the book's lines in. Chosen (c): the paper door names an entry
   by its symbol, kind and currency, the pretend broker by its symbol, and the rule itself
   knows no broker.
2. **Entry by entry, never added up.** Taken whole from the paper lane's rule: each entry
   must itself be the book's shares; a line the book holds and the broker does not list is
   named at no shares; a line listed at no shares is no holding.
3. **A line with shares in two entries is never the book's.** The paper door's rule passed
   two entries that were each the book's shares, which is what two accounts each holding
   the line would look like: twice the book, read as clean. Options were to carry the rule
   over exactly as it stood, or to close this while it was being given its one home.
   Chosen: close it. The book holds a line once. Zero entries do not count as a second
   place, so every case the paper door's tests hold today comes out as before.
4. **The resting stops go through the same rule.** "The stop is for exactly the shares
   held" is the same comparison with the stops as the entries, so reconciliation asks one
   rule twice and has none of its own. When the paper door is taught the desk's own stops,
   it can hand them to the same rule.
5. **What comes back: one typed difference for each entry that is not the book's**, with
   the name, the broker's shares and the book's. Reconciliation keeps the names, as scene 6
   reads them; the paper door can word its sentences from the same record.
6. **The paper door's own comparison stays until the paper lane moves it** (its file, asked
   as R-MONEY-4). Until then the rule is written twice; after it, once.
7. **The other blocking request (R-PAPER-2, any broker behind the send path) is the next
   session's**, not folded into this one: one objective a session. It should have a broker
   give its holdings and stops as entries, so a real account's rows reach this rule whole.

**Evidence.** The contract test was seen failing first (`book.differences` did not exist).
Run from outside the repository, the old book and the new traded the rehearsal's fourteen
months to the same 68 fills, 34 round trips and every order's answer, with and without each
line's first order rejected. A blind review found nothing blocking. It set the rule against
its own separate statement of it on 210,525 accounts of up to three entries (whole, short,
fractional and zero shares): no disagreement passed as clean and no agreement was named. It
ran the old reconciliation and the new side by side over 8,000 random runs at the pretend
broker with every fault, hand trades and cancelled stops: no difference in any answer,
ledger or refusal. And it rebuilt the paper door on the rule in a copy: all forty of the
door's tests passed unchanged, and of 83,793 accounts none became less safe (23 false
cleans, all "two entries each the book's", became named). Sixty-seven deliberate breaks were
driven in copies outside the repository, with Python's cache off: forty-three by the lane
(thirty-nine caught at once, two gaps closed, two that cannot differ) and twenty-four by
the review (eight survived: six gaps, one of them found by the lane too, each closed and
caught; two that cannot differ at the pretend broker). The seven gaps were a one-share
line, a zero entry beside two that cancel, the lines named out of order, a stop for fewer
shares than held, entries given as a stream that can be read once, a matching entry beside
a wrong one, and a line listed only at no shares. What the review left is in
`docs/STATUS.md`.

### 2026-11-13 — any broker behind the send path: five questions, entries, each asked once

**Decided**, by the lane as the desk's mentor (no one watching), on the paper lane's request
R-PAPER-2: the send path, the ledger and the day run know a broker by five questions
(`broker.Broker`) and no longer by the pretend broker's name.

1. **A stated interface, not a parent class.** Options were (a) the paper adapter inherits
   from the pretend broker, and with it a simulation's insides; (b) a parent class both must
   inherit; (c) a typed statement of the questions, which any class that answers them
   satisfies, the type check proving it wherever one is handed over. Chosen (c). It sits in
   `desk/broker.py` beside the answers a broker gives (`Fill`, `Report`, `Disconnected`), so
   an adapter imports one module. The manifest's line for that file still says only "the
   pretend broker": a lane may not reword it, so a session he starts should.
2. **Five questions, the ones the send path and the day run ask:** what did you do with
   this order id; take this order; your fills; your holdings; your resting stops. Opening a
   day, planting a position, cancelling a stop by hand and the stops' levels are the
   simulation's own instruments and stay off it. Cancelling orders will be the sixth, added
   with the kill switch that needs it, not before.
3. **Holdings and stops are entries, a name and its shares each, as the broker gives them.**
   The pretend broker gave one number a line, a shape a real account's rows would have to be
   added together to fit. It now gives entries too (`holdings`, `stops`), and its old answer
   (`positions`) is gone, not kept beside: one job, one path. Its stops with their levels
   (`resting_stops`) stay for the simulation's tests, which prove the level.
4. **A line's symbol names that line and nothing else.** The door that reads an account
   names each entry; anything that is not the line itself (another kind of product, another
   currency) goes under a name of its own. Such an entry is named as a difference and stops
   all buying. Options for the line's own sale were to refuse it too, or to allow it while
   the line's own entry agrees. Chosen: allow it, as a line that has lost its stop may be
   sold: the shares are known to be there, and a sale only lowers risk.
5. **Each question asked once for an order, the stops before the holdings.** The send path
   asked for the holdings twice, once to name what differs and once to judge the order's own
   line. It now asks once for the fills, the stops and the holdings, and judges both from
   those answers (`book._compare`). They are three moments at a real broker, and the order
   matters (the blind review's blocking finding): with the holdings read first, a stop that
   sold between the two readings looked like "shares there, stop gone", a line that may be
   sold, and its sale went out for shares already sold. Read stops first and the same moment
   shows the shares gone, and the sale is refused. A stop that sells after the last reading
   no order of questions can catch: that is the broker's to refuse.
6. **`place` gives an order's last answer.** The send path and the gate count fills only, so
   an order left working at the broker is in none of the five answers, and six buys could
   each pass a gate that sees an empty book. Options were to add working orders to the
   interface now, or to state that an adapter must not leave one working. Chosen: state it
   (what is not filled is cancelled), and let working orders arrive with cancelling, in the
   kill switch's step. The interface also states what the send path leans on: one stop a
   line, for all the shares held; fills in the order made, under ids that never change; an
   answer whole or an error.
7. **Left open, in `docs/STATUS.md`:** a resting order that is not a sell stop is unseen, a
   stop's level is never compared, and a connection lost while reading is not a stated answer.

**Evidence.** Tests seen failing first: the type check refused any broker but the pretend
one (seven errors), the new contract test failed on "one order, two readings", and the
review's race test failed with the sale not refused. Run from outside the repository, main
and this branch traded the fourteen months to the same ledger and the same answers, with and
without every first order rejected (68 fills, 34 round trips), before the repair and after.
The blind review rebuilt the old send path and ran it beside the new over 4,000 random
sequences (179,764 steps: buys, sales, every fault, hand trades, cancelled stops) and 600
random mornings of the day run: no answer, refusal, ledger or holding differed. Its one
blocking finding is point 5, fixed and tested; its lesser ones are taken (the interface's
wording, three test gaps) or recorded. Eighty-five deliberate breaks were driven in copies
outside the repository, Python's cache off: thirty-nine by the lane (one gap: a broker's
rows collapsed into one a name), thirty-one by the review (five survived), fifteen on the
repaired code (one gap: two stops collapsed). Six gaps are closed and each is now caught; the
one left narrows a type of the interface's, which can refuse a broker, never admit one.

## DATA

### 2026-11-13 — the fourteen months are built; the scenes move onto them in two steps

**Found.** On their own calendars, a London line and a US line do not trade the same days
over fourteen months (Easter Monday, Thanksgiving, the 4th of July and eight more), so
there is no longer one list of days that every line shares. Scene 2 counts its decisions
as five rules times nineteen lines times one list of days; at full length that count is
wrong by design, and scene 2 goes red (driven: 28,925 decisions against 29,545 expected),
though not one decision is missing. Scenes 1 and 3 pass at full length. Scene 2 is the
money lane's file, which this lane may not edit.

**Options.** (a) Give every line the same days, holidays ignored: the store rightly refuses
a bar on a closed day, so the clean lines would park and scene 1 would break. (b) Choose
windows so the two venues happen to have equal counts: a trick to fit one assertion.
(c) Edit scene 2's count from this lane: against the lanes' ownership rule. (d) Build the
fourteen months now, let the scenes keep seeing its last six weeks (which hold no holiday
on either venue), and move them onto the whole of it with a one-line change once scene 2
counts each line's own days.

**Chosen.** (d). The data is in one place, its last six weeks in use; nothing is duplicated; main stays
green; the move is one constant (`SCENES_FROM` in `tests/scenes/rehearsal.py`).

**Evidence**, from a script run outside the repository on the whole fourteen months:
London lines trade 307 sessions and US lines 303, on each venue's own calendar; the store
keeps every clean line whole with no fault, and parks only the spoilt line, for its three
faults (now placed among its last sixty sessions). Each of the five rules buys and sells
on every one of the nineteen clean lines: RSI-2 19 round trips, Bollinger 38, the 20/10
breakout 38, the 50/200 cross 19, Supertrend 57. Deliberate breaks: a London line laid on
US days is refused for 25 August 2025 (a UK bank holiday) and parked for the missing 1
September; a plain weekday calendar faults Christmas, Boxing Day and New Year in London,
and Labor Day and Thanksgiving in the US. The first shape tried, a two-day dip, gave RSI-2
a trade on only 11 lines; a three-day dip gives it all nineteen.

**The cost.** Until the move, the scenes still run on six weeks in which no rule trades.
Scene 2's future-blind loop over all 311 days will take about twenty seconds where it now
takes one; the money lane may cut on fewer days.

### 2026-11-13 — which archive failures park one line, and which stop the fetch

**The question.** When the free archive fails for one line, should the whole morning's fetch stop, or only that line park?

**Options.** (a) Stop everything on any failure: one flaky line would keep all twenty from trading. (b) Park a line on any error at all: a fault in the desk's own code would be hidden as a parked line. (c) Park a line for a failure of the network or of the archive's answer - a dropped connection, a half-delivered answer, a timeout, a missing page, an answer that is not the line asked about or not in its currency - and stop everything for anything else, such as an answer of a shape the desk does not know, which would hit every line alike.

**Chosen.** (c). It is what the north star needs: the clean lines still trade on a morning one line fails, and a fault of the desk is never mistaken for the archive's. The reason is kept with the error's name (a timeout carries no message of its own). A refused line keeps no bars in the store, so nothing from an earlier day can be read as today's.

**Evidence.** Tests seen failing first. Six deliberate breaks, each caught: no handling at all; the answer's refusals not handled; every error handled; old bars left in place; the refusal dated too long ago to park; its reason dropped. A blind review found that a half-delivered answer (`IncompleteRead`) still stopped everything; it was made a failing test and fixed.

### 2026-11-13 — what a frozen feed is, and what the store does with one

**The question.** The archive can go on sending yesterday's bar as if it were today's. How many days of one repeated price make a frozen feed, which bars count, and what becomes of them?

**Options.** (a) Any single day of one price and no volume: thin London lines have such days often (2MU has 441 days with no volume since 2010), so this would park real lines. (b) A run of three: 2MU really has runs of three. (c) A run of five sessions, a trading week, each bar repeating the one before it (its volume too, or with none) or flat at its close with nothing traded; a flat day that traded stays a market. Its bars dropped as untrue and listed, the fault dated by the run's last day, so a run reaching the last sixty sessions parks the line, as any recent fault does.

**Chosen.** (c). It is what the north star needs: the desk never decides on a price the market did not make, and no line that trades is parked for being quiet. A week with no trade at all is also reason enough not to trade a line. Dropping, not keeping, the bars: kept, they would hand the strategies a calm week that never happened. Whether the archive or the market went quiet, the line waits until a real price arrives.

**Evidence.** The twenty lines from the archive on 13 November: the longest real run is three sessions (2MU, December 2022); after the rule the same four lines park, for their old reasons, and no clean line has a frozen fault. Tests seen failing first. Nine deliberate breaks, each caught: the run made four and six; a traded repeat counted; a flat traded day counted; each kind of repeat removed; a whole repeat with volume let through; the rule switched off; the bars kept. A tenth, dating the fault by the run's first day, cannot change an outcome: the dropped days are also missing sessions, which park the line on their own. A blind review found nothing blocking; its point that a whole repeat, volume too, is a frozen feed was taken; its other points are in `docs/STATUS.md`.

### 2026-11-13 — a suspension is recorded on the line, as a real move is

**The question.** The archive leaves out a day a line did not trade because it was
suspended. The store cannot tell that from a day the archive lost, and parks the line for
sixty sessions. What should a missing session do?

**Options.** (a) Leave it: any missing recent session parks, with no way back out but
waiting sixty sessions. (b) Let a short hole in the middle pass, parking only when the
newest session is missing: a day the archive lost would then be traded through unnoticed,
a default that masks missing data. (c) Record a confirmed suspension on the line in the
instrument master, as a real move is (`Line.suspended`): the store expects no bar that day,
so its absence parks nothing; an unrecorded gap still parks, its reason naming the way out;
a bar the archive gives on a recorded day is refused, for the record and the archive
disagree; a day the venue did not trade cannot be recorded.

**Chosen.** (c). It is what the north star needs: the desk never trades on a history with
an unexplained hole, and a line suspended for a day comes back as soon as the fact is
recorded, not three months later. Facts about a line come from the instrument master. None
of the twenty has a suspension recorded today; none is parked for a gap.

**Evidence.** Tests seen failing first. Four deliberate breaks, each caught: the record
ignored; a bar on a recorded day let in; the reason naming no way out; any day allowed in
the record.

### 2026-11-13 — a one-day crash is kept; only a hundredfold bar is a wrong unit

**The question.** A single day out of line with the days either side was dropped as "a wrong
unit", at any size. On the real archive that dropped 5QQQ's crash of 7 April 2025: a five-times
line down 40% at its low, half of it won back the next day. Which single days may the store
throw away?

**Options.** (a) Leave it: a real crash vanishes from the history, so every test of a rule on
that history looks safer than the market was. (b) Keep an old one and list it, park only a
recent one: a bad print would then stay in the history unparked, as a crash that never was.
(c) Drop a day only when a price sits a hundredfold out of its neighbour (pence among pounds,
the one fault price alone proves), the rule a run of days already followed; keep any other
move and record it as a lasting fault, which parks however old until each close is recorded
on the line (`Line.real_moves`), as a step in the price already did.

**Chosen.** (c). It is what the north star needs: the desk neither forgets a loss the market
really dealt nor trades on a history holding a move nobody has confirmed. One rule now
decides for a single day and for a run. The cost: a bad print of another size, say a tenth,
parks its line until someone looks; no line is parked by it today.

**Evidence.** The twenty lines from the archive on 13 November: before, 5QQQ's 7 April 2025
was dropped as a wrong unit; after, it is kept, its fall and its recovery listed as moves to
record; the same four lines park, and no clean line has a new fault. Tests seen failing first:
a 60% one-day fall, at the first bar, an old one, a recent one and the newest, each kept and
parking, and each back out once its closes are recorded. Seven deliberate breaks, each
caught: the size test removed, made always true, always false, made to read the close alone,
its margin widened, its margin made a single jump, the wrong neighbour measured. A blind
review found nothing blocking; its one finding of the same kind - a crash straight after
days in the wrong unit was dropped with them - was made a failing test and fixed: a run in
the wrong unit now ends at the first day back in the right one. Its other points are in
`docs/STATUS.md`.

### 2026-11-13 — the research list: what is on it, where it lives, and what a refusal does

**The questions.** His ruling named four lists and "about 1,500" tickers, kept apart from
the twenty trading lines, nothing on it traded. Building it raised six questions of intended
behaviour.

**1. How many.** The four lists, as published on 13 November, hold 503, 101, 350 and 200
names, and overlap (86 of the Nasdaq 100 are in the S&P 500). Options: (a) the lists
as ruled, each ticker once: 1,065; (b) pad to 1,500 with names from no list he chose.
**Chosen (a):** the lists are the ruling and the number was an estimate of them. The full
universe of 5,000 and more is already the plan's next size.

**2. Where it lives.** Options: (a) in the instrument master beside the twenty, marked "not
traded": one wrong flag and the desk trades a research ticker; (b) a module in `desk/`;
(c) a module in `lab/`, which `desk/` may never import (the wall guard). **Chosen (c):**
"nothing on it is traded" is then held by the wall, not by a flag. Ten of its tickers are
also trading lines; for those the list hands out the master's own line, so a fact recorded
there (a real move, a suspension) has one home, and a disagreement between the two refuses
to load.

**3. One store folder for each venue.** Thirteen symbols are two companies (BA is Boeing in
New York and BAE Systems in London), and the store names a file by its symbol. Options:
(a) rename one of each pair; (b) change the store's file names, the money lane's reader with
them; (c) keep each venue's tickers in its own folder, the store unchanged. **Chosen (c).**
A parked ticker is returned by its line, which carries its venue, never by symbol alone.

**4. Which funds.** No free, published list of US funds by value traded was found. Options:
(a) a list from memory; (b) a field of 330 well-known funds drawn up by the session, each
fetched from the archive and ranked by its median value traded a day over the sixty sessions
to 12 November, the top 200 taken. **Chosen (b):** the cut is measured, and repeatable. The
200th trades about 87 million dollars a day. Left out of the field: funds that move against
their market (a line's leverage is one or more), funds whose multiple has changed (their
history is on two scales), single-share funds and volatility trackers. Ten funds built to
make two or three times their market's move are in, each with its multiple.

**5. Shares London does not quote in pounds.** The archive refused eight FTSE 350 members
as "not GBP". Five are quoted in dollars and are recorded so, and come back clean. Three
(BCG, MTLN, PEY) are quoted in euros; a line is in pounds or dollars. Options: (a) record
them in pounds, knowingly false, and let them park every day; (b) teach every line euros,
which reaches the money lane's sizing and conversion; (c) leave the three off and say so.
**Chosen (c)**, until research needs them.

**6. A ticker the archive refuses for a day.** The blind review's finding: a throttled or
timed-out answer empties that ticker's file, sixteen years of bars, until the next run.
Options: (a) leave the old bars in place for a refused ticker: yesterday's data would then
read as today's, the fault the desk's store was built to refuse, and the research store
would follow a second rule; (b) stop the whole run at the first refusal: one bad ticker
would cost the other thousand; (c) one rule for every store: a ticker refused today holds
no bars today and is parked with the reason, and the next run, ten minutes, restores it.
**Chosen (c).** A cell on an emptied ticker fails loudly and is retried; nothing stale is
ever studied. It is now a test.

**Evidence.** Membership read from the published pages of the four lists (the S&P 500, the
Nasdaq 100 as of 22 October, the FTSE 100 after 1 October and the FTSE 250 after 20 October
2026). `universe.keep` driven on the real archive for 13 November by a script outside the
repository: every one of the 1,065 answered; 4,097,609 bars; 249 tickers begin after January
2010; 864 clean (625 of 718 US, 239 of 347 London) and 201 parked, each for a one-day move
beyond the store's belief that its line does not record: 406 moves, 31 tickers on the flash
crash of 6 May 2010, 46 in March 2020, 10 on the day after the Brexit vote. Tests seen
failing first. Thirty-one deliberate breaks: twenty-eight caught at once (every venue in one
folder, the parked dropped, a refused ticker's old bars left in place, a list left out, a
multiple changed or lost, a ticker added or removed, and more); two caught once their tests
were added (the master looked up by symbol alone; the two allowed to disagree on currency);
the last, two tickers swapped in order, changes nothing. A blind review found two things
blocking: a parked ticker did not say which venue it was on (fixed: parked by line), and
question 6 (decided, and tested). Its other points are fixed (wording, a silent default for
a missing multiple, the master silently winning a disagreement, eight London currencies) or
listed in `docs/STATUS.md`.

### 2026-11-13 — a line's UK tax: two rates, a fact on the line, and how far each is confirmed

**The questions.** The money lane asked (R-MONEY-1) for what a purchase pays in UK
transaction tax as a fact on each line, the ten London lines confirmed, and one London line
of the rehearsal data that pays it. This entry replaces the sentence above, under the costs,
that the tax "is to be confirmed line by line". Five questions of intended behaviour.

**1. What the fact is.** Options: (a) a kind on the line (share, fund, product) from which
the cost model works out the tax; (b) the rate itself on the line, taken from one table of
rates in the instrument master. **Chosen (b).** The tax does not follow the kind: a share
of a company registered abroad can pay none. The cost model needs a number, and a kind
would be a second fact to keep true. The table has two rates, nil and a UK share's half of
one per cent (`lines.NO_TAX`, `lines.STAMP_DUTY`); a line can state only one of them, and
only a London line can pay, so a wrong figure or a taxed US line cannot be made. A sale pays
none.

**2. A line made without it.** Leverage cannot be left out of a line. Options: (a) the
same for the tax: about thirty lines built in the money and paper lanes' tests would stop
working, in files this lane may not edit, and main would be red; (b) nil when not stated,
for good; (c) nil when not stated for now, every real list stating it, and the other lanes
asked to state it in their tests so the default can go. **Chosen (c)** (R-DATA-4,
R-DATA-5). Until then a UK share built by hand from four facts pays nothing, which is the
risk; no list the desk or research reads is built that way.

**3. The ten London lines: nil, and how far confirmed.** As the session knows them:

| line | what it is | why nil | confirmed |
|---|---|---|---|
| SMGB | VanEck Semiconductor fund, Irish | exchange-traded funds are exempt | yes |
| IITU | iShares S&P 500 technology fund, Irish | the same | yes |
| VHYG | Vanguard world high-dividend fund, Irish | the same | yes |
| ISF | iShares FTSE 100 fund, Irish | the same | yes |
| VUSA | Vanguard S&P 500 fund, Irish | the same | yes |
| 3LGO | WisdomTree three-times gold product, debt of an Irish issuer | not a UK company's security | as the law reads |
| 2MU | Leverage Shares two-times Micron product, debt of an Irish issuer | the same | as the law reads |
| 5QQQ | Leverage Shares five-times Nasdaq product, debt of an Irish issuer | the same | as the law reads |
| IB1T | iShares Bitcoin product, debt of a Swiss issuer | the same | as the law reads |
| SGLN | iShares physical gold product, debt of an Irish issuer | the same | as the law reads |

The funds: the Stamp Duty and Stamp Duty Reserve Tax (Exchange Traded Funds) (Exemption)
Regulations 2014 (SI 2014/911), read in the tax office's manual (STSM101065) on 13 November
2026; interactive investor's and Freetrade's pages say the same. The products are not funds,
so those regulations do not name them. Stamp duty reserve tax falls on a UK company's
securities, or ones kept on a UK register, and these are debt of companies outside the UK;
brokers charge none. But no official page or issuer's document saying so of these five was
reached: the prospectuses could not be fetched, and the brokers' cost pages for IB1T do not
mention the tax. Options: (a) nil, recorded as not officially confirmed; (b) half a per
cent until confirmed, most likely false, and it would make the leveraged lines look worse
than they are; (c) stop and ask the operator. **Chosen (a):** it is the best reading, a
mistake costs half a per cent of a purchase on paper only, and it is settled by any real
contract note or by the order preview at his own broker. If one pays, one word on its line
changes.

**4. The research list's London shares.** Options: (a) leave them at nil: 347 UK shares
would be studied free of a tax nearly all of them pay; (b) charge each a UK share's stamp
duty, knowing a minority registered abroad pay none and three or so registered in Ireland
pay 1%; (c) check all 347 this session. **Chosen (b):** it is right for most, errs toward
too much cost for most of the rest, and the exceptions the blind review named from memory
are listed in `docs/STATUS.md` to be checked name by name. Ireland's 1% is a third rate, to
be added to the table when a line needs it.

**5. Which rehearsal line pays.** L01, a London line the rules buy: three times over the
fourteen months (2 October 2024, 22 April and 16 June 2025), £29.66 of stamp duty in all at
the fills' prices. In the six weeks the scenes see today nothing is bought, so the tax is
charged there only once the scenes move (R-MONEY-2).

**Not in the fact:** rounding (the tax office collects to the penny; the day record's one
rounding policy), and the takeover panel's flat levy on a trade over £10,000 in a UK
company's shares, which no trade of £2,000 reaches.

**Evidence.** Tests seen failing first: a line accepted any tax, the research list's London
shares paid nil, and a disagreement with the master on tax went unseen. A script outside the
repository ran the day's trading over the fourteen months before and after: the same buys,
and stamp duty of nil, then £29.66. Seventeen deliberate breaks, driven by a helper with
the Python cache off: fifteen caught (a rate changed, the default changed, each refusal
removed, the twenty lines or the research list given the wrong rate, the disagreement check
blinded); one changes nothing (the twenty lines built without stating the tax, which is the
default of question 2); one no test can see yet (the rehearsal line's tax removed: nothing
reads it until the money lane builds the day's record, and scene 7 will then need it). A
blind review found two things blocking, both wording that claimed more than was proven:
"each confirmed" before this entry existed and beyond what was found for the five products,
and the research list's shares stated as plain fact. Both are reworded and recorded here
and in `docs/STATUS.md`; its other points are taken (a London share quoted in dollars
tested, the default recorded and asked away) or listed there.

### 2026-11-13 — the scenes on the whole fourteen months (R-MONEY-2), and the status cut

The money lane asked (R-MONEY-2, blocking) for the scenes to see all fourteen months of the
rehearsal data: scene 2 already counts each line against its own venue's calendar, and
scene 7 needs days on which the rules trade; none trades in the last six weeks.

**1. Widen the window, or remove it.** Options: (a) set the window's start back to the
first day, one constant, leaving a filter that filters nothing; (b) remove the window, so
the rehearsal data is one thing under one name. **Chosen (b):** less code, and no second
view of the data to drift. `HISTORY`, scene 5's name for the whole of it, stays for now as
a second name for `CLEAN`, because the scenes' file is the money lane's; asked away as
R-DATA-6.

**2. The cost in time.** Scene 2 deletes the later bars at every one of 311 days, not 33:
it takes about 24 seconds, and the scenes step about 47, from 23. Options: (a) accept it;
(b) keep scene 2 alone on a short window. **Chosen (a):** the check stays under two
minutes, and a short window is exactly what hid holidays and trading days from the scenes.
Scenes 6 and 7 will add the day run over the same months, about 24 seconds each (the money
lane's note that the day run decides each line's whole history again every day).

**3. The scenes' days** (`SESSIONS`) are now every day either venue trades, 311 of them:
some are one venue's holiday (Thanksgiving, the UK's bank holidays). Scene 5 already runs
the day's trading over exactly those days and passes; scenes 6 and 7 will meet them too.

**4. The status cut.** By the operator's rule against document bloat the data lane's
section of `docs/STATUS.md` went from 286 lines to 50, in a commit of its own: what is done
was removed (git keeps it, and the book in `docs/PLAN.md` holds each open step), and each
open finding, request and requirement id kept in a line or two.

**Evidence.** Scenes 1 to 5 pass on the fourteen months; 6 and 7 stop, as before, at the
day's record, which is not built. Two deliberate breaks, the Python cache off: every line
laid on London's calendar (scenes 1 and 2 fail), and the data cut back to six weeks (scene 5
fails). No test fails yet if the rehearsal's taxed line (L01) lost its stamp duty: scene 7
will be that test.

**The blind review** found nothing blocking: no scene proves less than before (the spoilt
line's three faults still fall in its last sixty sessions; scene 2 now truly counts two
calendars, eight days only London trades and four only the US), and the second name does no
harm. It ran the day's trading itself with no faults: L01 is bought three times and US
lines are bought, so scene 7's tax and currency costs can be charged, and no fill lands on
a day only one venue trades. Two things it left for the money lane's day record, neither
new: every rule is out of the market by the data's end, so scene 6 as written cannot find a
holding (the money lane's own note of 13 November); and the scenes' first day, 2 September
2024, is the US Labor Day, so the US lines have no bar until the day after.

### 2026-11-13 — research reads the parked fifth by a rule of its own (#80)

**How research reads a ticker the store parks for an unconfirmed move.** Options: (a) leave the
parked fifth out: research loses its most violent names, the ones a leveraged trend strategy lives
on, and every result flatters; (b) read them as they are: a series that jumps a hundredfold (CLDN) or
to a tenth is priced as a gain or loss nobody had; (c) confirm all 406 moves from a second source:
there is none yet; (d) break the history at every unconfirmed move: the crashes of March 2020 and
6 May 2010 vanish and every strategy looks safer than the market was; (e) a rule from the bars alone
that sorts a change of scale from a market's move, each doubt resolved against the strategy. Chosen
(e). It lives in `lab/`, which the desk cannot import, so the store keeps its one rule and still
parks all 201.

**The rule, and which way each doubt falls.** Only a move made wholly between two sessions can be a
change of scale; a move within the day, or a spike that came back, cannot. Of the 33 such, a rise is
never believed unconfirmed (disbelieving a windfall costs a study nothing; counting a false one
flatters it). A fall is disbelieved only on ordinary trading, under 2.5 times the median value traded
of the twenty sessions before: all fifteen such look like changes of scale, none confirmed; the
lightest real fall came on 2.8 times (FANG, 9 March 2020). A fall with no volume to judge by is
believed. The margin is thin and was chosen looking at this list. The one error that flatters a
strategy, a real overnight crash on quiet trading read as a change of scale, is shown by none here.
The desk only buys; a study of short sales would need the opposite rule for a rise.

**What research reads of a ticker with a change of scale.** Options: (a) nothing; (b) only what
follows the last one (ROR would keep 85 of 4,260 bars); (c) the longest run on one scale; (d) every
run as a history of its own, which would make a ticker several lines for the grid. Chosen (c): 11,150
bars unread against 28,702 by (b). The store's bars are not rescaled.

**A bad print within a day is read, not mended.** Options: (a) clip a low or high far outside the
day's open and close: it mends data after the one writer, and a real flash crash looks the same;
(b) read it and name the day. Chosen (b).

**Evidence.** Tests seen failing first; the rule driven over the real list from cached answers by a
script outside the repository; 39 deliberate breaks with Python's cache off, 38 caught at once and the
last (which of two equal runs is read) once its test was added. A blind review's two blocking points
were wording the code did not keep, both corrected. The box stays unticked: the grid does not read
through the rule yet (R-DATA-7), and WWH, SHC, ECHO, MRNA and ROR stand misjudged.

### 2026-11-13 — the data lane's next boxes: the order, the keeper's road, the store's name (#66)

**Which box is first.** Options: (a) the lane objective's parked fifth first; (b) the box that says
"First, by his ruling" (VUAG, EQQQ and IDTL for SPY, QQQ and GLD) first. Chosen (b) with (a) beside
it: his ruling names it first, and their files do not overlap. For that, the parked fifth's tests go
in `tests/unit/test_lab_universe_parked.py` and do not touch `desk/store.py`.

**The keeper's road.** Options: (a) one big keeper box holding all the lane's files, alone;
(b) separate boxes with separate files. Chosen (b): the fast store, then trading hours and half-days,
then five-minute bars into the fast store, then the keeper. Two of the four run side by side, and
the paramount keeper is served sooner than by a lane held to one session.

**Half-days before the keeper.** A keeper that did not know a venue's hours and early closes would
park every line as "late" on a half-day, and could not know when no venue is open (exit 0 at once).

**Five-minute bars ahead of the archive's manners in the order, not in dependence.** Both change
`desk/archive.py`, so they cannot run together; the five-minute box is listed first because his
ruling makes it paramount. "Polite fetching" (DAT-08) waits for "The archive spared".

**The fast store's name.** `desk/bars.py`, not "hot": it becomes the one store for hot and deep data
alike, under the one writer, not a second store beside the first (canon A4). How `desk/store.py`'s
files move onto it is a later step.

**No `after` naming another lane's box.** No other lane's ids were on main and the guard refuses an
`after` naming no box; the one cross-lane dependence is an un-noted box and a request (R-DATA-9).

## LADDER (until 13 November; since then GRID and RUNGS)

### 2026-11-13 — the ladder's unit of work: days only, the whole history, keyed by what it read

**Decided.** The ladder's unit of work is a cell: one of the five strategies, one line of
the twenty, and a window of days (`lab/cell.py`). Its record holds the trades the desk's own
`strategy.decide` makes there, as days only: the day bought and the day sold, or none while
still held at the window's end. It is keyed by a code version and a data version.

**The choices, and why.**
- *What the record holds.* Options: days only; days with prices and a profit before costs;
  a profit after costs. Chosen: days only. The canon reports no result without its costs,
  and pricing a trade honestly needs the fill convention, the sizing and the exchange rate
  of each day, which are a rung of their own. Days are facts every later rung agrees on.
- *Where the rule starts.* Options: at the window's first day; at the line's first bar.
  Chosen: the line's first bar, with nothing after the window's end shown. A rule needs up
  to 200 days to warm up, and the money lane found that a decision depends on where the
  history starts; starting where the desk starts keeps the ladder's decisions the desk's.
- *Which trades are the window's.* A trade belongs to the window it was bought in, so
  windows laid side by side count each trade once.
- *The code version.* Options: the git commit; a hand-kept list of files; every file of the
  repository that `lab/cell.py` reaches through its imports. Chosen: the files reached,
  read once as the process loads them, Windows line endings ignored. A commit moves with
  any document, and a hand-kept list goes stale the day someone forgets it; following the
  imports cannot forget a file the result depends on.
- *The data version.* Every bar the rule was shown, so a bar changed years before the
  window moves the key, and one after the window does not.

**Evidence.** Nine contract tests, seen failing first. Seventeen deliberate breaks of
the module were driven against them; fifteen were caught at once. Two showed the test
itself was blind (Windows writes its own line endings, so the "same code on Windows" check
compared like with like; and the package files were never proven counted, which hid that
`lab/__init__.py` was not hashed at all): both fixed, and each break then caught. Two more
survived because the code was not needed (a filter on package names, and hashing file
names); that code was deleted, not tested. A blind review found nothing blocking; its
test gaps (a high or low changed alone; the pairing of each buy with its own sell) and
bars out of order being accepted were fixed, each break driven and caught.

### 2026-11-13 — the ladder's batch: a journal on disk, failures retried, one code per run

**Decided.** A batch runs a list of cells in turn (`lab/batch.py`) and appends each
outcome to a journal file, one line per cell, forced to disk before the next cell starts.
A cell that raises is recorded with its error and the batch carries on. On a restart the
journal's records made by the same code are kept and those cells are not run again.

**The choices, and why.**
- *Where progress lives.* Options: a journal of finished cells; one file per cell; a
  database. Chosen: one append-only journal of JSON lines. One file is the simplest thing a
  stop cannot corrupt: a line cut short by a stop is the one cell that never finished, and
  it is cut off and run again.
- *Is a failed cell done?* Options: done, so the next run repeats the failure; not done, so
  it is tried again. Chosen: tried again. The blind review showed why: what failed a cell
  may be a missing day of data since filled, or a reader outside the code the key covers,
  and a failure kept as done would hide the mend for ever. A cell that truly cannot run
  costs one failure line per start.
- *Which code's results count.* Only records made by the code this process runs. A batch
  refuses to start when the code on disk is no longer what it loaded, as its records would
  claim code it is not running: each batch runs in a fresh process.
- *What a restart trusts.* For now a kept record is trusted without re-reading its bars;
  checking the data version is the ladder's next item.

**Evidence.** Four contract tests, seen failing first (the module did not exist). Sixteen
deliberate breaks driven; fifteen caught. The one left is the forcing of each line to
disk, which only a killed process would show. A blind review found nothing blocking; its
two findings (failed cells never retried; cutting a torn line by emptying and rewriting
the whole journal, which a second stop could lose) were fixed, and each fix driven red.

### 2026-11-13 — the ladder keeps a result by what made it: its code and every bar it read

**Decided.** A batch keeps a result by its key, the code version and the data version, and
runs a cell again only when one of them has changed (`lab/batch.py`). Each run reads every
cell's bars again to find its key; a journal record with that key is the cell's result.

**The choices, and why.**
- *How a batch learns the bars changed.* Options: trust a kept record until told otherwise;
  a fingerprint per line kept by the store; read the cell's bars and hash them each run.
  Chosen: read and hash each run. The store keeps no version of its own yet, and a record
  from bars since corrected must never be kept; reading a line is cheap beside running the
  rules on it. A benchmark may later ask for the store's own fingerprint.
- *Which bars count.* Only those the rule is shown, up to the window's end, as in the key a
  cell already carries: a bar corrected after a window ends leaves that window alone.
- *Old records.* Records under other code or other bars stay in the journal, never matched;
  the journal is append-only, and growing it is cheaper than rewriting it.

**Evidence.** A contract test seen failing first (a corrected bar left the old result
kept). Nineteen deliberate breaks driven; thirteen caught at first, and the blind review
found the same gap: no test could tell a kept result from one worked out again. A count of
the rule's real runs was added; the five breaks it should catch were driven again and all
caught. Two remain, both in the unit of work's own fingerprint and owed to its contract
test: a change of volume alone, and two bars on one day (`docs/STATUS.md`).

### 2026-11-13 — the ladder's first rung: thirty trades, two standard errors, after costs

**Decided.** A strategy passes the first rung on a line (`lab/rung.py`) when it made at least
thirty judged trades and the average of their returns after costs is at least two standard
errors above nothing. Each trade is sized by the desk's own sizer at the close it was
decided on, bought at the next open through the desk's own pretend broker with its stop
resting there, and sold by that stop or at the open after the rule's sell. Both legs are
priced by the desk's one cost model, and every verdict names the broker whose schedule
priced it.

**The choices, and why.**
- *What is judged.* Options: total profit; the profit per day; the return of each trade.
  Chosen: each trade's return after costs, on the pounds paid. Trades are separate bets,
  so their spread measures how much of the average is luck; days inside one trade are not.
- *The bar.* Options: any profit after costs; two standard errors; a stricter bar now.
  Chosen: two standard errors and thirty trades, the textbook bar. Many cells tried at
  once will throw up chance winners at this bar (about one in forty), which is why AG-01
  asks for a luck correction for every trial: that is a rung of its own, in the book.
- *The fills.* Options: the rule's own days only; the desk's fills and stop. Chosen: the
  desk's. The blind review showed that leaving out the stop the desk always sets would
  judge trades the desk never makes. The stop is the pretend broker's own, never a copy.
- *A sale's cost.* The desk's cost model prices only a buy. Options: wait for the money
  lane; write a sale's fee in the ladder; charge a sale what a buy of the same shares costs
  beyond its value. Chosen: the last, through the one model; on dollars it charges a little
  more than the truth, never less. A sale's own cost is asked of the money lane.
- *Trades not judged.* One still held at the window's end, or sold on its last day, has
  no sale price inside the window, and the rung reads nothing after it.

**Evidence.** Five contract tests. On a hand-made trade every number is worked by hand, in
pounds and in dollars, and the stop sells it. A planted edge passes on eight random
histories (forty tried, all passed) and no edge fails on eight (forty tried, none passed,
the highest 0.51 standard errors); an edge the £3 least commission eats at a £500 capital
fails, though it stood over three standard errors before costs; and fixtures sit either
side of each bar (1.98 fails, 2.14 passes; 29 trades fail, 30 pass). Thirty-five deliberate
breaks were driven over two rounds; the first left six alive, showing the tests too loose,
and the fixtures were rebuilt. Every break is now caught but two that cannot differ ("over
2" for "2 or over", and the arithmetic setting). The blind review's two blocking findings
(the stop left out, the statistic left loose) are fixed; the rest is in `docs/STATUS.md`.
The tests were written after the module, not seen failing first; the breaks stand in.

## PAPER

### 2026-11-13 — the paper account is read, never written, and only if it is a paper one

**Decided**, by the lane as the desk's mentor (no one watching), for the first box of its
book: the desk's one door to the paper broker (`desk/paper.py`) reads the account's
holdings and resting orders and names every difference from the desk's book. It sends the
gateway four things and no others: a greeting, a start, and two questions.

**The choices, and why.**
- *How to speak to the gateway.* Options: the broker's own Python client or a popular
  wrapper (each a new dependency, and `desk/` may import the standard library alone); or
  the gateway's own language over a plain connection. Chosen: the plain connection. This
  step needs two questions and four kinds of answer, about a hundred lines.
- *Which version of that language.* The gateway changes the shape of its messages from
  version to version. Options: accept a range and carry a reader for each; take the newest
  (it has since moved to another encoding); offer one version and refuse any other answer.
  Chosen: one, version 176, which the gateway on his PC accepts and a widely used published
  client reads. A gateway that will not speak it stops the check with that reason.
- *The desk's client id.* Options: 0 (the gateway's master id, which can take over orders
  placed by hand: never); a small number the old desk may still use; one fixed number of the
  desk's own. Chosen: 222. If anything else ever holds it, the gateway refuses the desk
  with a stated reason; the desk does not hunt for a free one.
- *Only a paper account.* The broker starts a paper account's code with a D and no other
  account's. The door refuses any other code: in the gateway's list of accounts, before a
  single question is asked, and on every holding and every order. So a gateway logged in
  to a real account by mistake cannot be read as "quiet", let alone traded. A second lock
  beside the port.
- *What "quiet" means today.* A holding is matched to the book by its symbol, its kind (a
  share or fund) and its currency, so the same name in another currency, or as another kind
  of product, is a difference. A line the broker lists at no shares is no holding. Each
  entry the broker gives must itself be the book's shares: the first version added a line's
  entries together, and the blind review showed that a holding changed while it was being
  read, or 25 bought in one place and 25 sold short in another, would then pass as the
  book. Every order resting at the broker is a difference, whoever placed it, the desk's
  own client included: the desk rests none on paper yet. When the desk's own stops rest
  there (the next box), the check must be taught to know them, and only them.
- *What the check gives back.* The differences, in words (`paper.differences`,
  `paper.mismatches`); none means quiet. It was first called "quiet", which a caller could
  read backwards and trade exactly when the account was not; the review caught the name.
- *The gateway's news.* It sends notices that its price feeds are up or down, which this
  door does not use: those nine codes are passed over. Any other notice or error (the
  client id taken, the link to the broker lost) stops the reading, as does a kind of message
  the desk does not know. A reading that stops is never a clean one.
- *The plan's first box, split in two.* The check exists and has run clean once; nothing
  yet runs it each day or makes the desk wait for it. That half belongs to the adapter,
  which must refuse to send until the day's check is clean, so it stays an open box.

**Evidence.** From the real gateway on his PC, read-only, 13 November at about 17:45 UK,
through the door's own code: it greeted in version 176, named one account, a paper one,
and listed seventeen lines the old desk once held, each at no shares, and no order
resting; against the desk's empty book the check named nothing. With the desk's client id
already connected, a second connection was refused by the gateway ("326: the client id is
already in use") and the desk stopped on it. The tests' messages are the gateway's own
from that reading, with the account's code changed; only the open order is taken from the
published client, since none rested to copy. The contract test was seen failing first (no
module), and again for each of the review's fixes. A blind review checked every message
number and field position against the published client and found them right; its one
blocking finding (entries added together) is fixed and tested, and its nine lesser points
are taken or recorded in `docs/STATUS.md`. Sixty-five deliberate breaks were driven in a copy
outside the repository: fifty-nine were caught at once, and six showed a gap in the tests,
each now closed and caught (the symbol read from the wrong field, asking before the
gateway is ready or has named its accounts, another port, the two lists ending in the
other order, and reading the connection as text). One lesson for every lane's breaks: a
break written less than a second after the last, to a file of the same size, can run the
old code from Python's cache and report the wrong result; the breaks were run again with
the cache off before these numbers were written.

### 2026-11-13 — each line as the broker lists it: asked each time, pence and pounds, and a line it does not list

**Decided**, by the lane as the desk's mentor (no one watching), for the next box of its
book: the desk asks the paper broker how it lists each of the twenty lines
(`desk/listing.py`) and gets back, for each, the broker's own number for the line, the
exchange it lists it on, whether it prices it in pence or in pounds, and its price steps.
Two questions are sent through the one door, neither of which can place an order.

**The choices, and why.**
- *Where the broker's facts about a line live.* Options: on the line in the instrument
  master (the money lane's review of sizing had suggested the master carry the price step);
  in a table in the paper module; or asked of the broker each time. Chosen: asked each
  time, nothing written down. A price step is not one number: the broker gives a rule of
  bands (IITU moves in tenths of a penny under £5 and whole pence above £25), the rule
  differs from line to line, and the broker and the exchange change it. A copy would be a
  second home that goes stale in silence; the question also proves, each time, that the
  broker still lists the line. The instrument master keeps the desk's facts, the broker
  its own.
- *How the desk knows the broker's line is its own.* The desk asks by the line's name, as a
  share or fund, in its currency. The answer must come back exactly once, under that name,
  kind and currency, on an exchange of the line's venue. The broker's names for those
  exchanges are written in the module, each one seen from the gateway on one of the twenty
  (London's funds list; Nasdaq and Arca; none of the twenty lists in New York): a line
  listed anywhere else is unlisted until its exchange is added on purpose.
- *A line the broker does not list.* Options: stop the whole reading; or name that line
  with the reason and carry on. Chosen: carry on, as the data lane ruled for a line the
  archive refuses. A leveraged product can be closed by its issuer; nineteen sound lines
  should not stop for it. The line comes back as "unlisted" with the broker's own words or
  what differed, a different kind of record from a listing, so the adapter cannot build an
  order for it by mistake. An answer the desk cannot read (a message of another shape, an
  answer to another question, any error but "no such line") still stops the whole reading:
  a reading that stops is never a clean one.
- *Pence and pounds.* The broker prices six of the ten London lines in pence (3LGO, 2MU,
  IITU, 5QQQ, ISF, SGLN) and four in pounds (SMGB, VHYG, IB1T, VUSA), while it calls the
  currency of all ten pounds; the desk's prices are all pounds. The broker's rule of steps
  speaks in pounds. So a desk price is first put down onto its step in pounds, then
  multiplied into the broker's unit (`Listing.floor`): £37.556 on IITU becomes 3755. This
  was not taken from the broker's documents but tested on its own prices (below).
- *Which steps.* A line has a rule for each place the broker can send its order. The desk
  reads the rule of the broker's own router, where its orders will go, the route the
  question itself is asked on.
- *Down, never to the nearest.* A stop is put down onto the step, so it stays below the
  price it was set from (an order whose stop is not below its price cannot exist). The
  cost is a stop up to one step lower than the 10% rule's exact figure. A price with no
  step at or below it is refused, and so is one that is not a finite number.
- *A listing the desk cannot trust is no listing.* The record cannot be made at all
  unless it has a real number for the line, a unit the line's currency is priced in (a
  hundredth for pounds alone: pence; never for dollars, and never a tenth), and steps
  that are steps: finite, above nothing, starting from a price of nothing, each band above
  the last and starting on its own step. The reading stops on anything else. So the wrong
  unit, the fault that would put a stop a hundred times out, cannot be carried in a
  listing.
- *The gateway's notice that it cannot look lines up.* The account check passed over nine
  notices about the gateway's price feeds. One of them (2157) says the service that
  answers questions about lines is down; the blind review showed that passing it over
  could let an outage be read as "the broker lists nothing", every line unlisted. It now
  stops any reading, the account's too: one rule, and a gateway in that state is not one
  to trust on anything. The other eight are still passed over.

**Evidence.** From the real gateway on his PC, read-only, 13 November at about 18:35 UK,
through the module's own code, and again after each repair: twenty of twenty lines listed,
each exactly once under the desk's name and currency; all ten London lines on London's
funds list, eight US lines on Nasdaq, SPY and GLD on Arca; six London lines priced in
pence, four in pounds; twelve different rules of steps among them. A name the broker does
not know was asked on purpose and answered "No security definition has been found", the
answer the desk reads as unlisted; a name asked without its currency came back twice
(Boeing in New York and its Canadian receipt), the case the desk names as listed twice.

*Pence or pounds was proved on prices, not taken from a manual.* The open, high, low and
close of each line's last thirty sessions were read from the broker (a question about past
prices, read-only, asked from outside the repository): 2,392 prices. Put through
`Listing.floor`, every price of nineteen lines came back unchanged: it already sat on the
step, in the unit, that the desk had worked out. Then the finer test, since a rule read a
hundred times too fine would pass the first: in each band of each line's rule the prices
were found to move in exactly the listing's step and no finer one, in twenty bands of
twenty-one (whole pence on IITU, 3LGO and SGLN; a tenth of a penny on 5QQQ; a fifth on ISF;
a quarter of a penny on VUSA; a cent on every US line). The twenty-first is 2MU above £500,
where the broker's rule says £5 and the market moved in £1; below £500 it moves in the
rule's £2 exactly. That one is recorded in `docs/STATUS.md`; 2MU is parked.

The contract test was seen failing first (no module), and again for each repair. A blind
review, which checked every field the desk reads against the gateway's twenty real answers
and the published client, found two blocking faults: the look-up notice passed over, and
infinite or not-a-number prices and steps let through. Both are fixed and tested, with its
lesser points on the rule's number, the unit and the broker's number for the line. Its
second reading approved the repair and found the rules being read before the line was known
to be the desk's; that is fixed and tested too. What it left is in `docs/STATUS.md`.

Deliberate breaks, driven in copies outside the repository with Python's cache off: 113
over three rounds, 101 caught at once. Five showed a gap in the tests, each closed and
caught when driven again (a cut-short "no such line" notice, a London line priced in
pounds, an infinite band edge, and a listing one field short or one over whose rules still
read). Five different breaks survive, seven runs in all. Four cannot change a result: a
band taken to begin just above its edge, which differs only on a rule whose edge is off the
step below it, and none of the twelve real rules is; a pairing check behind a length check
that already forces it; and two that pick the last of exactly one. The fifth adds New York
to the US exchanges, which no test forbids: adding an exchange is a deliberate edit.

### 2026-11-13 — the paper lane's book ordered: read-only first, placing last, one new module per box

Options and choices (from #68):
1. Kill-switch refusal: first in the book, or after the adapter whose send it guards. Chosen:
   after. The refusal is a line in the adapter's send and reads the money lane's drill record,
   which is not built. Nothing is loosened: paper-conformance, the first real paper order, waits
   for paper-drill.
2. Should paper-drill and paper-conformance name the money lane's kill switch in `after`? Chosen:
   only this lane's ids for now, as the money lane has not noted its book and the check refuses an
   `after` naming no box. The wait is held by the box text, the four boxes in front, and the lane
   objective. Owed: add the id to paper-drill's `after` once it exists.
3. Order: reports, daily check, adapter, stops, drill refusal, then a real order, following "built
   from what it reads towards what it sends".
4. New modules (`reports`, `gateway`, `clearance`, `placing`) or all in `desk/paper.py`. Chosen:
   their own: paper.py is 216 of 400 lines, and separate files let paper-gateway run beside the
   chain. A session finding one unnecessary need not create it.
5. paper-conformance holds every file (`files: *`): it runs on the real account in market hours
   and may fix any module where the broker differs, so it runs alone.

## GRID

### 2026-11-13 — the fast grid engine: it holds what the desk holds, or it refuses

**Decided.** The grid engine (`lab/grid.py`) works out, for one strategy on one line, whether
it is in the market after every bar, on whole arrays at once. It is a second implementation
of the five rules, so it stays only while a parity test shows it holds what the desk's own
engine holds after every bar (canon B2). Where it cannot be sure it raises `TooClose` and
gives no answer: the desk's own engine must decide that cell.

**The choices, and why.**
- *The arithmetic.* The desk works in exact decimals at 28 digits; numpy works in floating
  point, which is fast and rounds at about 16. Options: trust floating point and accept a
  rare different answer; do the grid in decimals too (no faster than the desk); floating
  point that knows when it cannot be sure. Chosen: the last. Prices become whole numbers of
  the line's last decimal place; while a rule's sums of them stay under 2**53 they are
  exact and a tie is a true tie, called as the desk calls it. Everything else (prices as
  long as the archive's seventeen digits, Wilder's smoothing) is trusted only when the two
  sides differ by more than one part in a thousand million of the prices they were worked
  out from, ten thousand times further than rounding can move them. Closer than that is
  refused, never guessed. Prices too long for the desk's own 28 digits to add exactly are
  refused whole. On prices like the archive's nothing was refused; on made-up prices on a
  coarse tick, a close exactly on a Supertrend band is.
- *A refusal is not a failure.* The desk's engine is the truth and the grid is its
  shortcut. When the unit of work is moved onto the grid, a refused cell is run by the
  desk's engine, the one other path, and its record is the same record.
- *What it answers.* Options: the desk's `Decision` for every bar; the position after each
  bar as an array. Chosen: the array. Making one object per bar costs more than the rules
  do, and a cell needs only the days a position opens and closes.
- *The settings.* The five rules at their published settings only. The desk's rules take
  no settings, so parity at any other setting cannot be shown yet; a grid over settings
  waits for the desk's rules to take theirs (asked of the money lane in `docs/STATUS.md`).
- *The golden data.* The series in the money lane's `tests/unit/test_strategy.py` on which
  a second implementation written apart agreed with the desk (five walks of 1,200 days and
  two short jumpy series), read from that file, never copied; each also cut short either
  side of every rule's warm-up. Beside them, three walks of 1,500 days at prices as long
  as the archive's, since the golden series sit on a 25p tick and real prices do not.

**Evidence.** The parity test was seen failing first (no engine), and each later fix's test
was seen failing on the engine before the fix. On the golden series the grid answers 477 of
490 askings (seven series, five rules, fourteen lengths) and refuses 13, every one a close
exactly on a Supertrend band; the test holds that count. Measured from outside the
repository on 4,000 days of one line: the desk's engine about 100 ms for the five rules,
the grid about 6 to 8 ms, after 17 ms once per line to read the prices in.

Two blind reviews, each comparing the grid with the desk on thousands of random series of
its own making. The first found one wrong answer: an RSI on days that move a
thousand-millionth of the price, where the day's change is mostly rounding (53 of 1,201
placements wrong). The second, of the repaired engine, found two more: a Supertrend band
when a close sits far outside its day's range, and exact ties called among prices of 26
digits and more, which the desk's own 28 digits cannot add exactly. None arises on prices
like the archive's, but the rule is never a different answer, so each was made a failing
test and fixed at its cause: a comparison's margin is now measured against the prices it
was worked out from, and prices too long for the desk are refused. The second review's
whole comparison was then run again on the repaired engine: twelve kinds of series, 120 of
each, every rule, no difference from the desk and no error; its three searches that had
found wrong answers found none. There was no third blind review.

Deliberate breaks: 64 in the first round, 42 caught. The 22 left showed that a bar on which
a rule would enter and would not stay never arose in any test, that five safeguards
(a tie on each Supertrend band, the RSI's tie, the edge of exact arithmetic, the margin
itself) were held by none, and one piece of code that could never run, since removed.
Tests were added and those breaks driven again: all caught. What still survives, each
recorded in `docs/STATUS.md`: breaks that cannot differ (a tie's direction where ties are
already refused), a more cautious margin, and a few no series found can show.

### 2026-11-13 — the unit of work on the grid: one record, whichever engine answered

**Decided.** A cell's trades (`lab/cell.py`) now come from the grid engine's answer, and from
the desk's own engine whenever the grid refuses (`TooClose`). The record is the same record
either way, and the same as before the change.

**The choices, and why.**
- *Does the record say which engine answered?* Options: mark each record "grid" or "desk";
  say nothing. Chosen: nothing. The grid is kept only while it holds what the desk holds, so
  the answer does not depend on who gave it, and two records with one key must be one
  result. A count of refusals belongs to a pass's log, when a pass exists.
- *What goes to the desk's engine.* Only a refusal. Any other error from the grid is a
  fault and fails the cell loudly (the batch records it and carries on); the desk's engine
  never hides it. A test holds this.
- *The code version.* The grid's file is reached through the cell's imports, so a change to
  the grid changes every key and every result is run again. numpy's own version is not in
  the key; it is pinned in `requirements.txt`.
- *Trades from positions.* The grid answers "in or out after each bar", so a trade is now
  the day the position turns in and the day it turns out, on both paths; the desk's
  decisions are first read into the same in-or-out list.

**Evidence.** The test was seen failing first (the cell never asked the grid). It runs each
of the five rules on three golden series: on the long walk the desk's engine is never
asked; on each of the two jumpy series it is asked exactly once, for the Supertrend cell
the grid refuses; every trade day is the golden one. A blind review rebuilt the old code
from the diff and compared 88,815 cells (5,921 series, five rules, three windows each, each
once as it runs and once with the grid made to refuse): no difference and no error;
nothing blocking. Its test gap (any error, not only a refusal, could have been sent to the
desk's engine unseen) is closed and was seen failing; the rest is in `docs/STATUS.md`.
Twenty deliberate breaks of the new code: nineteen caught, the twentieth being that same
gap, caught since. Measured from outside the repository on 4,000 days: a cell about 25 ms
for any of the five rules, where the desk's engine alone took 90 to 100 ms; 17 ms of the
25 is reading the line's prices in, paid again by each cell.

### 2026-11-13 — a cell names its line and venue (R-DATA-1)

**Decided.** A cell holds the whole `Line`, not symbol plus venue. Options: the Line; two
strings. Chosen the Line: the data lane asked for it, the first rung needs the line's facts
(currency, leverage, UK tax) to price a trade, and they then have one home.
- A cell does not check its line against the research list. Options: check membership; trust
  the typed Line. Chosen the latter: checking would put the list inside every result's code
  version, so adding one ticker would re-run every kept cell; a line with no stored prices
  already fails its own cell loudly and the rest carry on.
- A symbol alone is still accepted, meaning one of the twenty. Options: break the rungs
  lane's tests, which this lane may not edit; hold the change until they move, which they
  cannot do first; accept both for now and ask them to move (R-GRID-2). Chosen the last; the
  door is named as temporary in the code.
- The journal names a cell by strategy, symbol, venue and window; a kept record is found by
  those plus the code and data versions. The line's other facts are not written: the days a
  rule bought and sold do not depend on them.

**Evidence.** Four deliberate breaks, each caught and undone: every line read from the US
folder; the journal leaving the venue out; a kept record never found; a cell given a line
quietly taking the trading line of the same symbol. Blind review, nothing blocking.

### 2026-11-13 — the grid lane's open boxes ordered for the runner (#71)

**Decided.**
- The cell's key (BT-04) comes before the first pass. Options: keep the book's order (pass
  first, key later); move the key up. Chosen: up. A change to the key re-runs every kept cell,
  so changing it after a pass over the research universe would throw that pass away.
- Auto-tune lives in `lab/tune.py`, not inside `lab/batch.py`. Options: grow the batch
  service; a new module around it. Chosen the module: auto-tune and the venue box then share
  no file, two sessions can build them at once, and the batch keeps its one job.
- The pass lives in `lab/sweep.py`: it owns which cells make a pass and the busy flag the
  runner reads (`autotune.json`).
- grid-weekend claims every file of the lane (`*`): making a sweep fast enough can touch the
  engine, the cell and the batch alike, and it is last, so running alone costs nothing.

## RUNGS

### 2026-11-13 — the luck rung: a chance multiplied by every trial, one 5% test across the set

**Decided**, by the lane as the desk's mentor (no one watching). A verdict passes the luck
rung (`lab/luck.py`) when it passed the first rung and its chance of being luck, multiplied
by the number of trials it was picked from, is at most 5%. The chance is that of an average
so many standard errors up, or further, from trades with no edge (Student's t on the trades
themselves). Each corrected verdict carries the count.

**The choices, and why.**
- *The correction.* Options: multiply the chance by the count (Bonferroni); the same in
  steps, a little kinder to the second and third winner (Holm); a deflated Sharpe; shuffling
  the histories to see what luck alone gives. Chosen: the plain multiplication. It holds
  however the trials lean on one another (five rules on one line share its history), needs
  nothing but the trades, and is one sentence he can check. Holm passes almost nothing more
  when winners are few among thousands. The deflated Sharpe has its own box in the book
  (LAD-03) and will sit beside this, not replace the count.
- *The line.* 5% across the whole set, the plan's own number (LAD-08): of twenty sets with
  no edge anywhere, about one still hands over a winner.
- *What counts as a trial.* Options: the verdicts that passed the first rung; every verdict;
  every trial tried. Chosen: every trial tried: losers, those with too few trades, and those
  that left no verdict at all (a cell that failed, a candidate dropped), which the caller
  must state as a number; there is no default, and a number under nothing is refused.
- *A trial the first rung failed* never passes here, however small its chance: thirty trades
  remain the least.
- *A verdict with under two trades* has no chance to speak of: it counts as certain luck.
- *The chance itself.* No library the lab may use gives Student's tail, so it is worked here
  as one smooth sum (about ten lines), and held to the textbook table's own rows.
- *What it does not cover* (the blind review's blocking finding, taken): the 5% is true only
  if each trial's own chance is true, which needs trades that are separate bets with gains
  spread roughly like a bell. Many small wins and a rare large loss on few trades read as
  far less chance than they are. The module now says so; the cure is in the book's later
  boxes, and no winner on real prices is believed before it (`docs/STATUS.md`).
- *The first rung's pass rule as one function* (`rung.verdict`), in a commit of its own,
  nothing changed: the first rung calls it, and the luck rung's tests build their trials by
  it, so no test carries a second copy of the rule.

**Evidence.** Four contract tests, seen failing first (no module). The chance agrees with
the published table to a part in a million, and with a second method written apart (outside
the repository) to under one part in a million over degrees of freedom from 1 to 5,000; the
blind review's own second method agreed to a few parts in a hundred million. Of forty sets
of forty no-edge trials, twenty-six gave the first rung a winner and one gave the luck rung
one; a real edge added to each passed in all forty. Forty-two deliberate breaks were driven
in a copy outside the repository with Python's cache off: all caught but four, none able to
change a real result: "under 5%" for "5% or under", an odd number of steps in the sum (a
difference far below any line), and the first rung's two known ones ("over 2" for "2 or
over", the arithmetic setting).

### 2026-11-13 — the rungs book's next boxes: one new module each, failing fairly last

**Decided**, by the lane as the desk's mentor (#65).
- *Where the boxes live.* Options: each in a new module (`lab/folds.py`, `trials.py`,
  `deflated.py`, `plateau.py`, `regime.py`); or grow `lab/rung.py` and `lab/luck.py`.
  Chosen: new modules. Each is one concept with one owner (canon A4), and boxes sharing no
  file can be built side by side; growing the two files would force them into single file.
- *Failing fairly runs alone, last.* It turns the first rung's pass-or-fail into three
  answers (pass, fail, not enough evidence), which every other rung reads; done beside them
  it would break whichever landed second. Doing it first would hold the folds behind it.
- *Regimes waits for the folds*: it replays the same history cut by period and should reuse
  the folds' cutting, not write a second.
- *"Its costs whole"* sits below the noted boxes without a note: it cannot start until the
  money lane's costs land, and that box has no id yet.
