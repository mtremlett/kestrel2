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

## 2026-11-13 — the runner restarts without a drain; the doctor takes the recommended option

**Why.** Four drains this evening each idled lanes for up to 45 minutes while the last
sessions finished: the opposite of the pace he asked for.

**How.** Each session now writes its output to a file, not to the runner, and each slot keeps
a record of its session on disk (process, output, work, branch, phase). `restart.cmd` (or
`runner.py restart`) ends the runner once no merge, push or launch is half done, without
touching a session; the next runner holds each recorded slot's claim before any slot takes
work, waits for the session to end, reads its output, and lands its pull request as usual.
A session is known by its program file and its start time, so an update between runners,
or a process number Windows reused, is not mistaken for it. A stop still ends every session.
A drain is needed only for a change to how sessions are launched.

**Driven.** With stand-in sessions in a scratch home, 15 cases: a restart during three
sessions (none killed, all three adopted, finished and landed, none started twice); during
the pull requests' watch; with the sessions ending between runners; after an update between
runners; with a reused process number; between a session's legs (its own session resumed);
and a stop ending adopted sessions. A blind review found eleven faults, all fixed. Live at
21:30: `runner.py restart` took 11 seconds; the new runner adopted five slots (three
sessions still running, two pull requests being watched), started nothing twice, and the
first adopted pull request landed four seconds later.

**His standing ruling**, via #90: "please always go with recommended to avoid waiting for me
to attend". When the doctor finds a halt is a decision for him, it takes the recommended
option, gives it to the lane's next session to act on and record, restarts the lane, and
sends him one line saying what was chosen and why. Going live, credentials and spending
money still wait for him, as does a lane the doctor has already restarted twice that day.
Sessions follow the same ruling for their own questions. Driven: 11 cases. While his ruling
raising the unit-test budget to 1.5 times the product (#90) lands, a pull request red on
that budget alone is not counted toward a halt.

## 2026-11-14 — boxes that wait; requests the runner opens; the desk's jobs; the check's turns

**Why.** At 08:00 three lanes had halted overnight (DATA 21:37, GRID 01:51, RUNGS 07:19), only
5 of 12 sessions ran, and the check took nine minutes. One mechanism behind the halts: a box
blocked outside its lane (seven days of time, a book not bought, another lane's change) was
handed out again and again, because the plan could not say a box waits.

**Built (the runner, outside this repository).**
- *Boxes that wait.* A box's note may say `waits:` a request, a date or `operator` (the guard
  checks the value, #158). The runner also holds waits of its own: a session's `Waits:` line,
  or the doctor's finding after a halt (checked: a real box, a wait it can judge; never over
  a decision that is his or a recurring fix). A waiting box is never handed out; boxes after it
  that do not need it are freed; it is offered again when its request is done or its date
  comes. A wait on a request not yet numbered waits a day for it; `operator` waits are told to
  him and lifted by `runner.py unwait <box>`. Scribes write the held waits into the books.
- *Requests the runner opens.* Each major or blocking finding of the daily audit becomes a
  blocking request in the owning lane's list (R-RUNNER-n), closed for good once done. Request
  lines are now read however their date is written: most of the lanes' requests (R-MONEY-15,
  R-RUNGS-5, R-RUNGS-6) had been invisible to the runner, so blocking requests never reached
  their lanes.
- *The desk's jobs* (no Claude session): `desk.running` every five minutes on weekdays as the
  supervisor's stand-in, only after a passed dry rehearsal; `desk.keeper` every five minutes;
  a pre-flight at 07:15 and a deep run nightly, both in the 08:00 message; on Sunday at 18:00
  the dry rehearsal, then one go/no-go line naming each open blocker with its workaround. Each
  runs once its module has a command on main (requests R-RUNNER-6, -7 to PAPER and DATA).
- *The check's turns* (#161): at most four full checks at once on the PC.

**This morning.** GRID's seven-day box waits until 21 November and frees grid-declared;
RUNGS's indicators wait on R-RUNGS-6 (RSI-2 now from the best free replication, #157);
DATA's ISA swap waits on R-RUNNER-4 and -5 (its #85 asks of GRID and RUNGS, never in STATUS).
The three halts were lifted at 09:18 with each lane's redirect, by a restart that adopted
every running session.

**Driven.** In scratch homes: waits 36 cases, jobs 26, the turns 8 (four breaks and real
processes), the guard 29; the earlier drives re-run on the new code. A blind review found one
blocking and five major faults in the waits (live since 09:18), all fixed and driven, and
loaded with the jobs by a second restart.
Measured: CPU 100% on all 8 logical processors with six checks at once.

---

# The lanes' own decisions

Each lane's decisions are in its own file, `docs/lanes/<lane>.md` (from 14 November 2026),
so that parallel pull requests never touch the same lines. Each entry is a dated `###`
heading, and says what was decided, the options, why, and the evidence. The entries below
are the operator's sessions' decisions about the lanes.

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

## 2026-11-14 — five answers: concentration shown first, no book yet, one account, updates paused

**His rulings**, in his own chat, from options with a recommendation each:
1. **Concentration is shown, not yet a condition.** "Show it first": the book's number of
   independent bets and its profit by correlated cluster go on every report; the A-GATE
   sets no mark on them until a few reports show what normal looks like. The option
   declined: a pass-or-fail mark now, chosen without evidence.
2. **No Connors book for now.** "Work around this for now." The first reproduction is
   Connors' Double 7's on SPY, whose figure is already read from its publication and
   written down (#141); RSI-2's reproduction waits until its figure is on file. The book
   ("Short Term Trading Strategies That Work", Connors and Alvarez, 2008) carries both;
   seen 14 November at about $23 to £48 used, no new price confirmed.
3. **No second GitHub account yet.** "No - leave for now." Sessions stay on his account;
   the question stays open, to be asked again before going live.
4. **The runner's Telegram key** he copies beside the runner himself, as ruled on
   13 November; he was given the steps.
5. **Windows updates stay paused.** "I agree": no password goes into Task Scheduler; a
   restart still stops the lanes until he logs in.

---

## 2026-11-14 — phase 3 begins: phase 2's scenes all pass

**Found.** At 08:00 on Saturday 14 November, scenes passed 7 of 7: phase 2's goal, the money
path in simulation, is met. The desk had 5,421 of phase 2's 7,000 lines and was growing about
320 lines an hour across twelve sessions, so the ceiling would have turned every money, paper
and data change red within about five hours. The paper lane has worked in phase 3 since his
ruling of 13 November.

**Decided.** `BUDGET.json` names `3-money-paper`, whose ceilings (9,000 lines of desk code in
55 files) were agreed before phase 0 began. Its lab ceiling is set to 7,000, not the 1,500
written then: he raised the lab to 7,000 on 13 November for the ladder lanes that now run
alongside, and moving the phase must not take that back. Nothing else changes. This loosens
a ceiling and moves the phase, both his to decide. He has ruled that a question put to him
takes its recommended option without waiting (13 November, about 21:05), but a session's
permission check asks for his direct yes on these, so he was asked. His words, Saturday 14
November about 08:15 UK, offered "Yes, phase 3" (recommended) or "Not yet": "Yes, phase 3".
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

## 2026-11-14 — no books bought; the old stores as a head start; the ladder in published sets

**His words, about 08:30 UK on 14 November.** "why do i need to buy a book. right now i
cannot afford it, so instead, research on the internet and find a best fit answer. when
ladder is working we can try variants to then test which is the favoured ones." And: the
fast and second stores "were already built in the kestrel repo. maybe you can copy the
contents?" And: "will you test in sets and then publish findings results as you iterate ...
what is the graduation process into paper trading?"

**Decided by the mentor, as his rulings allow.** No book is bought (that would be spending,
his alone, and he has said no). Where an author's table is not free, the best published
replication found on the internet stands in, labelled secondary, with its source written
down, and reproduction must land inside the range the sources give. This replaces "RSI-2
waits for the book" of this morning. The old desk's Stooq and IBKR stores and its matrices
are read in now as a head start, every bar re-checked on entry and the fresh bar winning
where they differ; their stored indicators are only a cross-check, never copied, since an
indicator kept in two places is the second-home failure. The ladder runs in sets, each
published as it finishes, and a strategy graduates to paper only through all eleven rungs
and the luck test, named in the plan before its first paper day.

---

## 2026-11-14 — Monday holds; one pre-flight and one deep night run; old data kept

**His words, about 09:20 UK.** "If something misses Monday, FIRST-LIGHT starts on Tuesday
instead....this is not acceptable. we must itentify blockers and work together to find
solutions. this is the elite desk way." He asked for daemons and monitors per lane, daily
known-answer tests "as if these are pre-flight checks", synthetic trades, simulations,
lifecycle and funnel tests, audits, smoke, integrity, canary and wiring scans. And whether to
delete the original stores after import.

**Decided by the mentor, as his rulings allow.**
- FIRST-LIGHT's first day is Monday 16 November, 08:00. It starts on every clean line,
  and later lines join without restarting the count. Each blocker has a workaround that keeps
  every safety rule (in `docs/PLAN.md`), and a dry rehearsal on Sunday at 18:00 ends in a
  go/no-go line to him.
- His test list becomes two runs, not many processes: one pre-flight each trading morning and
  one deep run each night (fuller at weekends), each writing one record into the morning
  line. The old desk had sixty scheduled tasks; one process with many checks keeps the
  checking without the sprawl. A "funnel" count was dropped on 13 November (FIL-05) because
  one gate has one step; a refusal's reason serves it.
- The old stores are consolidated into the one store on C: and verified; the originals are
  then deleted with his explicit yes, asked at that time. Never E:, which is his backup drive
  (his words: "E: drive is my automated backups drive. please do not use this"). `C:\mtt_cache` was kept back while his mark_the_trend programs
  might read it; asked, he answered "Retired", so it is treated like the other stores.
- The GPU is not used for now. The old desk measured no gain on it (its mentor's hand-over
  of 18 October: "GPU/in-memory: no gain"), it would add a library and a second engine needing
  its own parity test, and numpy on the CPU has not yet been shown to fall short. If a full
  pass over the research universe overruns a weekend, a benchmark decides.

---

## 2026-11-14 — self-contained now, a cloud server later

**His words, about 10:00 UK.** "as we build kestrel2, there should be no link to other
folders or repo. when kestrel2 is live we can remove all other older folders ... if we are
using another folder area, then please copy the contents to have zero dependencies. the
future idea is that all of this desk is packaged and migrated to a cloud server and cloud
database to avoid the single point of failure which is my current desktop pc."

**Decided.** The desk depends only on its own folders: the repository, its runner, its data
folder and its notes. The old desks are a quarry. Their code is ported under test, and their
stores are copied in through the one store's checks, never read in place at run time. Paths
come from one setting, and the database is named `market.db`, without the project's name,
behind the one store, so that a server database can replace it. A guard will hold this. Moving
to a cloud server is a phase 7 step, drilled before real money, and the Windows-only parts of
the runner sit behind one door so they can be swapped.

---

## 2026-11-14 — one merge train, and the check on GitHub split into parallel steps

**Why.** At 11:05 eleven pull requests sat behind main. main merges only a change that is up
to date, so each landing put every other one behind; the runner then re-ran the full check on
this PC for each (about 9 minutes, ten at once), and those checks timed out. Nine changes
landed between 08:00 and 11:00, against about six an hour before.

**Decided.** The runner keeps one merge train: the oldest armed pull request that is not red,
not in conflict and not being pushed to, brought up to date (main merged in, no local check),
landed by auto-merge on GitHub's own check, then the next. On GitHub the check's steps run side
by side, `python check.py --only <step>`, the unit tests in three shares, and the job named
`check`, the one main requires, is green only when every step passed. A run superseded by a
newer push to the same branch gives way, except on main. Nothing is loosened: every step of
the full check still runs on every change.

**The guard, driven.** `tests/guards/test_workflow.py` holds the workflow to `check.py`. Eight
planted breaks were each caught: a step dropped, a unit share dropped, `if: always()` dropped,
the success test weakened, `fail-fast` dropped, `needs: step` dropped, a share that loses one
file, and every share given the same files.

---

## 2026-11-14 — two databases, 1-minute hot data, and the reset kept for Monday

**His rulings, about 11:45 UK, each chosen from options.**
- **Tokens to Monday 08:00**: "Monday-critical first (Recommended)". Until FIRST-LIGHT's first
  morning only MONEY, PAPER and DATA run sessions, all at medium effort, at most six at once.
  GRID's and RUNGS' backtests keep running as plain code. The evidence: the paper and money
  lanes at high effort took about 63% of the spend, at $14 to $17 a landed change at list price.
- **Hot data**: "1-minute", over the 5-minute recommended. It is kept for the twenty lines and a
  watchlist of up to 100 within his IBKR line allowance.
- **Backups**: his automated backup covers `C:\Users\mtrem\PYTHON`. The desk writes one
  consistent snapshot each night for it to carry, and never writes to E: itself.
- **No dashboard page**: "No, Telegram is enough".

**Decided with them.** The desk keeps two databases, both owned by the one store: `market.db`,
long-term, and `market_hot.db`, live. Every useful store found on C: is consolidated into
`market.db`, so the old areas can be removed later, each only on his yes. Keeping these two
apart lets the minute-by-minute writes never contend with long reads of history, while the
one store stays their only writer.

---

## 2026-11-14 — data for 4,000+ tickers: tiers, SQLite now, a bounded ingest

**His ask, about 11:30 UK.** "ultimately we want to trade 4000+ tickers across hundreds of
strategies. can we rename the databases market_history and history_live? ensure both
databases ... can cope. ... will there be a queue growing problem? ... think of multiple
options, verify them, score them and then recommend them."

**Researched.** An independent study, with every key claim checked at its source, is kept in
the notes folder (`data_stack_2026-11-14.md`). IBKR cannot stream 4,000 tickers. Each needs a
market-data line; an account starts with 100, and boosters top out near 1,100 at $300 a
month. Small-bar history is capped at 60 requests per 10 minutes. The load itself is small:
about 1.8 million 1-minute rows a day at 4,000 tickers, one transaction a minute. Scored
options: for live data, tiers score 23 of 30 against 18 for IBKR alone; for storage, SQLite
in WAL mode scores 27, Parquet with DuckDB for sealed history 27, DuckDB alone 25, QuestDB
24, TimescaleDB 23 and ClickHouse 20.

**Decided, the recommended options.**
- The databases are `market_history.db` and `market_live.db` (his names).
- Data comes in three tiers: live from IBKR for held, signalled and watched names; a US vendor
  feed bought only after the A-GATE and only if a strategy needs it; and daily bars for all.
- SQLite stays (standard library, one writer).
- Months of intraday history are sealed into compressed files once a benchmark shows the need.
- The ingest is bounded by construction, not by watching.
- Nothing new is bought now. The vendor feed (about $99 a month), IBKR boosters ($30 a month
  per 100 names) and a London second source (about £30 a month) are spending, asked of him
  when a strategy needs them.

---

## 2026-11-14 — no new data spend: IBKR's real capacity, a free collector, weather recorded first

**His words, about 12:40 UK.** "derive a finite number of tickers (minus 10%) that can be
easily refreshed within these limits ... i do not want to pay for more data, not until this
desk can pay for itself." And: research the free tiers of the keys he already has, for
triangulation and for news and market regime, as the first mark_the_trend did. "does the
elite desk agree?"

**Researched**, sources cited, in the notes folder (`free_data_2026-11-14.md`). IBKR's own
historical-limits page says the hard 60-per-10-minutes rule is for bars of 30 seconds or less.
For 1 minute and longer it is "lifted" to a soft throttle, with no published number. The old
desk built eight regime feeds and a sentiment daemon. None was ever shown to predict out of
sample. Its regime map discarded about 74% of its winning cells, and its regime history was
overwritten in place.

**Decided by the mentor, as his rulings allow.**
- Within IBKR's free capacity, with 10% kept spare: 90 tickers live, a measured ramp for
  polled ones, and daily bars for all.
- A daily free collector starts now, so that history the free tiers drop is kept.
- Weather follows "record first, prove second, act last": realised-volatility sizing first,
  everything else recorded until it passes REG-07.
- News serves event awareness only.
- Nothing is bought. Databento's free credit needs a card, so it is his decision, not taken.
- The data-service keys move into the desk's own secrets file, outside the repository. His
  Trading 212 keys and his email passwords are never copied.

---

## 2026-11-14 — the whole check runs on GitHub; a session runs the fast check

**His ruling**, in the coordinator's chat, to options put with a recommendation: "yes...option A".
Measured first, from all 121 sessions that landed a change since 13 November 18:00: the whole
`python check.py` run on the PC took 46.5% of all session minutes. That is a median of 8.9
minutes a run, often several runs a session, with up to four checks at once on one PC. GitHub runs
the same check in parallel parts in about 2.3 minutes, and refuses any merge that is not green. A
session now runs `python check.py --fast` and the tests of what it changed, then pushes. The whole
check on GitHub is the gate. It runs the whole check on the PC only to chase a red. Nothing merges
red, as before. Expected: a typical session from about 22 minutes to about 12.

## 2026-11-14 — the desk's ceiling raised to 10,500 lines, so FIRST-LIGHT never waits on it

**His ruling**, in the coordinator's chat, to the question asked as a guard loosening. First
"Yes, standby only", for a raise from 9,000 to 10,500 lines if the ceiling ever refused a
FIRST-LIGHT change. Then, an hour later: "if i cannot attend at the time then i auto-approve
it now. please confirm. do not stop or stall on account of desk code lines. we can
iteratively refactor at a later date if need be." An unattended session may not raise a
guard on a relayed yes, so the session he spoke to makes the raise now, while it is attended.
In `BUDGET.json`, `product_lines` goes from 9,000 to 10,500 for phases `3-money-paper` and
`4-ladder`. Phase 4 changes too, so the move to phase 4 cannot shrink the room. Nothing else
in the budget changes. desk/ was 6,751 lines at the time. Until Monday 08:00 the runner still
lets only FIRST-LIGHT boxes grow desk/. After FIRST-LIGHT, a deletion box aims to bring desk/
back under 9,000.

**Driven.** With the ceiling at 10,500, a desk/ of exactly 10,500 lines passed, and one more
line failed it.

## 2026-11-14 — CLAUDE.md and CANON.md held to their limits by a guard

**Approved** in the after-first-light queue (item 5): a guard reading CLAUDE.md at most 80 lines
and CANON.md at most 200, the canon trimmed by merging rules, not deleting them. The canon said
"Limit: 200 lines, held by a guard" and stood at 225 with no guard: the promise in prose had
already been broken. `BUDGET.json` now holds both caps, so loosening one is announced as a guard
change; `test_the_rulebooks_stay_short` reads them. The canon went to 190 lines by merging rules
said twice (A1's stop rule into A8, A5's repeats of A3, A4 and A9 into one line, A9's
work-around rule into A1.3; A5's ban on proof scripts and second objectives left to A3 and A9,
which already say it) and dropping blank lines and separators. No rule was removed; a blind
review found "never declare done without the check's output" dropped, and it is back in A6.

**Driven.** A canon of 201 lines failed and one of exactly 200 passed; a CLAUDE.md of 81 lines
failed; a budget that forgot CLAUDE.md's cap failed; a cap of 150 under the canon
failed. Each named the file and its count.


## 2026-11-14 — each lane's decisions in its own file

**Approved** in the after-first-light queue (items 3 and 4): one file per lane, `docs/lanes/<lane>.md`;
13 of 14 clashes in 175 pull requests were the shared documents. Each lane's part of this file
(2,152 lines in all) moved verbatim to its own file; a check counted every line before and
after and found none lost. Only that lane may change its file (`tests/guards/test_lanes.py`), the
document set admits one per lane the manifest knows, and each is held to 800 lines
(`max_lines_per_lane_doc` in `BUDGET.json`; the largest is DATA's at 596), the size limit #46
proposed, rebuilt per lane. A stub under each lane's heading here keeps the runner's scribe
working until its prompt and claim name the lane's file. The lanes' STATUS sections stay in
`docs/STATUS.md` for now, because the runner reads each lane's requests from there.

**Driven** in a throwaway clone. Failed: a lane file of 801 lines; a lane file for a lane the
manifest lacks; a budget without the cap; the money lane changing the data lane's file; the
money lane changing its own file outside its claim; a lane branch the manifest does not know.
Passed: a lane file of exactly 800; the money lane changing its own file with claim `*` or a
claim naming it; the money lane still writing `docs/DECISIONS.md`, as the scribe does today.

---

## MONEY

This lane's decisions are in `docs/lanes/money.md`. Until the runner's scribe
writes there, a new entry may land below; the next scribe moves it.

## DATA

This lane's decisions are in `docs/lanes/data.md`. Until the runner's scribe
writes there, a new entry may land below; the next scribe moves it.

## PAPER

This lane's decisions are in `docs/lanes/paper.md`. Until the runner's scribe
writes there, a new entry may land below; the next scribe moves it.

## GRID

This lane's decisions are in `docs/lanes/grid.md`. Until the runner's scribe
writes there, a new entry may land below; the next scribe moves it.

## RUNGS

This lane's decisions are in `docs/lanes/rungs.md`. Until the runner's scribe
writes there, a new entry may land below; the next scribe moves it.
