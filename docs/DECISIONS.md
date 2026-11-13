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
