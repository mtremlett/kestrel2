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

## 2026-11-14 — the docstring ratchet: undocumented public definitions never rise

**Approved** in the after-first-light queue (item 9): undocumented public definitions may fall,
never rise. On main today 71 of the 437 public functions, classes and methods in `desk/` and
`lab/` have no docstring. `tests/guards/test_ratchets.py` counts them at main's commit the
change starts from and in the change itself, and fails if the count rises. No number is kept by
hand, so no lane needs to edit a guard file when it documents something, and the count can only
fall. A public definition is one whose name does not start with `_`, at a module's top level or
inside a public class.

**Driven.** An undocumented public function, async function, class, method of a public class,
and function in a new file each failed, as did removing an existing docstring. A documented new
function, a private undocumented one, a deleted product file, and documenting one while adding
one undocumented each passed.
A blind review found that a definition under a top-level `if`, `try` or `with` went uncounted;
it is counted now, and undocumented ones under an `if`, an `except` and a `match` case each
failed, while one nested inside a function passed. The count is of the total, as approved: a
change that documents one old definition may add one new undocumented one.

## 2026-11-14 — the churn guard: a third fix to one file waits for its mechanism

**His yes**, 14 November about 18:30 ("Yes, Tuesday", gate G-B): a file fixed three or more times
in its last ten changes fails the check until `docs/FAILURE_PATTERNS.md` names the mechanism.
Built now, in a session he did not start for it, because nothing trips it today: no product file
has three fixes in its last ten changes on main (`desk/store.py` and `lab/ladder.py` have two).
`tests/guards/test_churn.py` reads each product file the change touches, counts the changes
titled `fix` among its last ten on main, and counts the change itself as one more when its title
(its pull request's on GitHub, else its commits') starts `fix`. At three, the check fails until
FAILURE_PATTERNS names the file in backquotes. A lane cannot edit FAILURE_PATTERNS, so a lane
that meets it stops and writes the finding in its STATUS section; the runner already halts a lane
earlier, at a second fix, so this is the backstop the runner's halt lacked (pattern 11's debt).
Only `desk/` and `lab/` count: nearly every change edits the shared documents.

**Driven** in a throwaway clone with made-up histories on main. Failed: a third fix to
`desk/store.py`; a feat to a file whose last ten changes hold three fixes; a fix after two in the
last nine; two fix commits on one branch counted as one (three, not four); a pull request titled
`fix` over commits titled `feat`; a file named without backquotes. Passed: a feat after two
fixes; fixes eleven changes back; a title `fixed:`; a pull request titled `feat` over `fix`
commits; a change touching no product file; the file named in backquotes; nothing changed.
A blind review found that GitHub runs the check on a push and on the pull request, and the two
could disagree on one commit (commit subjects against the title that lands). A push run there
now leaves the fix judgement to the pull request's run, and `Fix:` counts as `fix:` does;
driven: a capital `Fix:` and a pull request titled `Fix(kill):` failed, the push run of the same
commit passed, a push run still failed a feat after three fixes, and `fixup!` passed. Known gap:
a pull request's title changed to `fix` after its check ran is not checked again.

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

## 2026-11-14 — failure pattern 13, the cleaner tuned on live lines (R-RUNNER-43)

The store-rules guard, `tests/unit/test_store_rules.py` (#225), is pattern 13's mechanism.
Its drive evidence, from the pull requests that drove it (each plant reverted):
- #225: a new fault site in `desk/store.py` failed the sites test; a new constant failed
  the constants test; `BLIP` 20 to 21 failed the constants test; a reworded "bad print"
  failed that rule's row.
- #227: `EXTRA = 1` added to the store failed
  `test_every_tuning_constant_of_the_store_is_pinned_to_its_value`; a new `Fault(...)`
  branch in `_once` failed `test_every_rule_in_the_store_is_pinned_by_a_row_that_fires_it`.
The pattern's text could not land from the DATA lane (the lane guard refuses
`docs/FAILURE_PATTERNS.md`); a non-lane session added it.

## 2026-11-15 — the ladder's folds are the last five whole years, pooled by rule (R-RUNNER-99)

By his ruling of 15 November ~07:50 ("A", relayed by the main coordinator; canon B5): the
numbers the spec moves are changed, each re-derived by hand. What changed: the ladder's folds
were two thirds of one line's history, judged on thirty trades in each; they are now the last
five whole calendar years (2021 to 2025 for a window ending 13 November 2026), the rule's trades
pooled over all its lines (`folds.pool`, #242), gains taken by the day, and the worst year
judged. One answer, with one reason, stands on every line of a rule. A line that cannot get
its own first rung (no bars, too young, a step of units, a day with no rate) is left out of the
pool, and the lines pooled are part of every cell's key. Years that cannot be had (under five
whole years of history among the lines) are a FAULT on the folds, with the reason, remembered
for the rule. A fold is not a trial. Set EPON now runs a rule's lines together, so only one
rule's bars are held at a time.
Both thresholds stay at "more than 20".

Pinned numbers moved, each by hand:
- Trials: a cell was itself and two folds, 3; it is itself, 1. Two cells: 6 became 2 (and
  `deflated.judge(..., count - 1)` 5 became 1); three cells: 9 became 3; the set EPON test's six
  cells: 18 became 6. `ladder.FOLDS` is 5 (was 2) and names the years, not trials.
- Keys: a cell is kept under its rule's lines' bars too, and under the rates when a line in
  dollars is among them, so a line joining a rule's set judges the rule's other cells again:
  "1 judged now, 2 kept" became "3 judged now" at the dollar line's arrival and at a dearer
  dollar; the noise cell is also judged again when the edge cell's bars arrive (its answer is
  the last row, no longer the edge's).
- Answers: the planted edge on two lines (VUSA edge, ISF noise) stays THIN on its folds, 6 or 7
  trades a year pooled, under thirty (hand-derived by `folds.pool`: 6, 6, 7, 7, 6 for 2021 to
  2025). The trend rule on the same two lines made no trade in 2022, a year with none is a
  FAULT by the spec, and its worst year is the verdict: THIN became FAULT in set EPON's test.
- The known answer, new: sixteen lines each with the edge planted, the five yearly folds
  PASS and the one answer is every line's, where per line the folds were THIN.

Scale, not solved here: pooled over every line of the research store (2,130 at this writing)
a rule's pool holds all its lines' bars and runs about twelve first-rung runs a line. That is the
ruling's design; if it proves too heavy for the PC, the pool's universe is the question to put.

Not done, left in the lane's book: a rule with an author's figure still has its folds unrun
(`NO_FOLDS`); `folds.pool` already takes the reproductions, and wiring them is the next step.

---

## MONEY

This lane's decisions are in `docs/lanes/money.md`; its scribe writes there (from
14 November 2026, 21:04) and moves there any entry that lands below.


## DATA

This lane's decisions are in `docs/lanes/data.md`; its scribe writes there (from
14 November 2026, 21:04) and moves there any entry that lands below.

## PAPER

This lane's decisions are in `docs/lanes/paper.md`; its scribe writes there (from
14 November 2026, 21:04) and moves there any entry that lands below.

## GRID

This lane's decisions are in `docs/lanes/grid.md`; its scribe writes there (from
14 November 2026, 21:04) and moves there any entry that lands below.

## RUNGS

This lane's decisions are in `docs/lanes/rungs.md`; its scribe writes there (from
14 November 2026, 21:04) and moves there any entry that lands below.

### R-RUNNER-107 — the master and the calendars agree (DATA, 15 November 2026)

`tests/unit/test_lines_worlds.py`: every line of `desk.lines` has a rule and a clock in
`desk.venues`, and every SimCity world (read as `simcity.run` deals them, with `_live`
replaced so none is lived) is dated only on trading days of its lines' venues. The test
reads the rehearsal data, which `desk.venues` itself dates, so it is green today; it is
the net for a line or world that drifts. A line on an unknown venue is already refused when
the `Line` is built (`__post_init__`), so the test's break is a venue that loses its
calendar. Each was driven against a planted break, then the break was removed:

- `CLOCKS["US"]` renamed "XX": "lines on a venue with no calendar in desk.venues (holidays
  and hours): ['AAPL', 'TSLA', 'NVDA', 'SPCX', 'MSTR', 'AMD', 'MU', 'SPY', 'QQQ']".
- `simcity._market` made to date its sixth bar 25 December: "world 0: L01 is dated
  2024-12-25, which is no LSE session" (and every line after it).

## 15 Nov - R-RUNNER-100: the author's figure is handed to the folds

A rule with an author's figure on file used to be given no folds ("the folds rung cannot yet
hand an author's result to its folds"), so its verdict could never be reached. `verdict.judge`
now runs the folds on every cell and `Pool.fold` hands the reproductions to `folds.pool`, which
already took them; a fold is not a trial (trials stay one a cell). His ruling of 15 Nov,
"A" (canon B5): the spec's reading, thresholds staying at "more than 20".

Pinned figure moved, re-derived by hand: `test_a_rule_with_a_figure_on_file_is_judged_only_behind_its_authors_result`
had "folds" unrun and "1 passed ... 1 of them behind an author's result". Its one line (ISF, a
planted edge) now has its folds judged: the worst of 5 yearly folds (2022) holds 2 trades pooled
over 1 line, under the 30 asked, so the folds rung and the verdict are THIN, the row passes not
every rung, and the summary counts 0 behind an author's result. THIN is the honest answer on
2 trades a year; no t, Sharpe, trial count or threshold in any other test was touched.

## 15 Nov — R-RUNNER-103: rare large losses (G2), one more trade at the rule's own stop

His ruling "A" of Sun 15 Nov ~07:50. Small wins and a rare loss at the stop, worth nothing
together, passed the four rungs read from a trial's own trades on 6 of 400 no-edge lines of
under forty trades (a line in fifty has not yet met its loss). Options: (a) plant the loss in
the first rung (chosen, the spec's G2); (b) a bar on skew in the deflated rung (a second rule
for a job the first has); (c) leave it, six false winners in 400. Chosen (a): `rung.planted`
adds to a verdict's gains one more, the least return any judged trade would have made had its
stop sold it, with a stop's costs (`Priced.stopped`). `Verdict.gains` is read by the standard
errors, the luck's chance and the deflated Sharpe's count, skew and kurtosis; `trades` and
every count of the 30 asked are untouched. Both thresholds stay at "more than 20", never 10.

Known answer: `tests/unit/test_lab_ladder_spec.py` (from #211's branch, shrunk to one world),
seen failing first with 6 of 400 passing, now 0.

Pinned figures moved, each re-derived by running the first rung on the same seeds:
- `test_a_planted_edge_passes_and_a_planted_non_edge_does_not`: the bar-straddling pair was
  seeds 1 and 16 at t 1.99 and 2.02; with the loss planted they read 1.76 and 1.72, so the
  pair is seeds 12 (1.979, fails) and 40 (2.021, passes), the same claim (the bar sits between
  them). Seed 0 cut at 29 trades read t above 2.8, now 2.52, so the pin is above 2.5; at 30
  trades it still passes (2.35) and at 29 is still THIN.
- No pinned figure in test_lab_luck, test_lab_deflated or test_lab_trials moved: their trades
  are built by hand without a stop, so `Priced.stopped` is left unset and plants nothing. The
  default is a cost of keeping to the claim (test_lab_folds and test_lab_plateau build
  `Priced` too and are another lane's files); the ask to make it required is under Remains.

## 15 Nov - the lab's ceiling rises by 400 lines, by his yes

In `BUDGET.json`, `lab_lines` goes from 7,000 to 7,400 for phases `3-money-paper` and
`4-ladder`. The desk's ceiling is unchanged at 10,500.

Why: the lab held 6,976 of its 7,000 lines on main. Moving the twenty eponymous rules into
the spec book as data rows (R-RUNNER-125, spec-epon) needs about 400 lines of blocks in
`lab/blocks.py`. Two rules landed as spec rows with parity proven; the other seventeen could
not fit. Once all twenty are rows, retire-epon (R-RUNNER-127) deletes about 1,600 desk lines
of the old eponymous modules.

His ruling, Sun 15 Nov 2026 ~13:20, in chat with the coordinator. He was offered three
options: move 400 lines of ceiling from the desk to the lab (recommended), raise the lab by
400 alone, or wait for Tuesday's consolidation. He chose "Raise research by 400".

## 15 Nov - the lab's ceiling rises from 7,400 to 8,000 lines, by his yes

In `BUDGET.json`, `lab_lines` goes from 7,400 to 8,000 for phases `3-money-paper` and
`4-ladder`. The desk's ceiling is unchanged at 10,500. The lab is research code; the trading
path is untouched.

Why: main's lab held 7,391 of 7,400 lines. Five ladder pull requests (#342 rung-regimes, #350
rung-bootstrap, #351 rung-cpcv, #352 spec-epon slice 3, #354 rung-placebo) were green on every
check except `test_the_tree_is_inside_this_phases_ceiling`, needing about 595 lines together.
The 13:20 rise to 7,400 was sized for spec-epon alone and did not count the rungs already
building; that was the coordinator's error. To stop a repeat, the runner holds a card on the
ceiling before a session starts, instead of after it has built.

His ruling, Sun 15 Nov 2026 ~16:00, in chat with the coordinator, chosen from three options
(raise to 8,000; keep 7,400 and cut first, which slips the ladder to Tuesday; hold the ladder
to Tuesday): "Raise to 8,000". Clean-up cards (the rung registry, consolidation) are expected
to shrink the lab again.

## 15 Nov - the lab's ceiling rises from 8,000 to 12,000 lines, by his ruling

In `BUDGET.json`, `lab_lines` goes from 8,000 to 12,000 for phases `3-money-paper` and
`4-ladder`. The desk's ceiling is unchanged at 10,500. The lab is research code; the trading
path is untouched.

Why: main's lab held 7,690 lines with about 417 more riding the train, so 8,000 was full
before the rest of LADDER READY's chain (rung-dsr, rung-folds, rung-trials-cluster,
ladder-catalogue, spec-variants, ladder-gate, grid-chain, spec-epon's last slices,
rung-registry, pool-unit; about 900-1,200 lines by their estimates) could land.

His ruling, Sun 15 Nov 2026 ~16:30, in chat with the coordinator, offered 9,500 with or
without a matching desk cut, or a hold to Tuesday: "for research, set to 12000 and we can
iteratively refactor later". The refactor is owed: the rung registry, consolidation and the
fan-in guard's split cards are expected to shrink the lab, and retire-epon deletes 1,593 desk
lines.

## R-RUNNER-180 - the paper Gateway's wait, measured (Sun 15 Nov 2026, PAPER lane)

`paper.SECONDS` goes from 15 to 30, one constant for the knock and every conversation
(`desk/paper.py`, its reason beside it). Measured read-only on port 4002 only (the knock, and
the account read), with the Gateway already logged in and up:

| case | knock | account read |
|---|---|---|
| warm, PC at its usual load (36 Python processes), 3 knocks | 0.004-0.013 s | 0.10 s |
| under load: 24 busy processes (3 per core), 15 rounds | max 0.136 s | max 0.178 s |

No call failed or came near the limit. A truly cold Gateway (just restarted) could not be
timed without restarting his Gateway, which is his alone; the three step TimeoutErrors seen
(each beside SimCity or a build) were therefore not reproduced at 15 s. Options: (a) keep 15,
measured at under 1% of it; (b) 30, matching the Telegram door's 30 (`messenger.SECONDS`), a
hundredfold on the worst measure; (c) 60 or more. Chosen (b): it gives a stalled PC double the
time, and a dead Gateway is still called silent after 30 s, far inside one five-minute step,
with no retry and no sleep. Test: `test_a_slow_first_answer_is_waited_for_and_a_silent_one_is_called_silent`
(a stand-in answering at 20 s passes; one silent past 31 s is his).

## R-RUNNER-156 - the loss and order-rate limits of the pre-trade gate (Mon 16 Nov 2026, MONEY lane)

`orders.Settings` holds, beside the capital, the day-loss limit (2%), the week-loss limit (5%) and
the new lines a day (4); the colleague's range for new lines was 3-5, 4 is its middle. The gate
(`orders.gate`, given a `risk.Standing`) refuses a buy once a loss reaches a limit (naming it) and a
new line once four are entered that day. On paper `halt.drawdown` alerts and records "would have
halted" in `would_have_halted.csv`, beside `halts.csv`, and never halts. Options for the record: (a)
a row in `halts.csv`, which would read as a halt in force and stop the buying, or change the file's
columns under the existing record; (b) a file beside it. Chosen (b). Evidence the tests catch it:
the new-line test failed with the limit's `>=` made `>` (both `test_risk.py` tests red).

## 16 Nov - the desk's ceilings rise to 15,000 lines and 80 files, by his rulings

In `BUDGET.json`, `product_lines` goes from 10,500 to 15,000 and `product_files` from 55 to
80, for phases `3-money-paper` and `4-ladder`. The lab's ceiling (12,000) and every per-file
and per-function cap are unchanged.

Why: main's desk held about 9,700 counted lines with about 620 more riding the train, so the
READY gate was refusing cards for want of room (hourly-pnl, heat-report-a, kill-go-flat,
paper-bars-question), and desk/ stood at 55 of 55 files, so any card adding a desk module
(desk/pnl.py, the intraday engine and step) would meet the file ceiling next. At the day's
pace the line ceiling was a day away.

His rulings, Mon 16 Nov 2026, in chat with runner ops, each answering a question put with
options (A raise, B keep the ceiling and delete to make room) and a recommendation:
- about 12:30, on the line ceiling (recommended: 11,500): "A - raise to 15,000".
- about 13:15, on the file ceiling (recommended: 80): "Raise file limit to 80".

The refactor stays owed: rungs-merge-duplicates (R-RUNNER-191) and retire-epon (R-RUNNER-127)
are expected to shrink the tree, and the size ratchet still holds the new ceilings.

## R-RUNNER-225 - the ladder's easings, pre-registered and frozen (Mon 16 Nov 2026, RUNGS lane)

Why: his question of 18:5x ("can we trust the ladder test? ... I am a single retail trader"). SET EPON
judged 21,320 cells and passed 0: each cell was charged all 63,920 trials the register ever held,
each rule was judged line by line (30 trades needed on one line), and the first failed rung stopped
the line. Zero of twenty is as much a finding about the ladder as about the rules. His rulings, Mon
~19:15 "Yes, all four" and ~19:20 "YES TO ALL ... I trust your recommendations ... Do it with tests"
(approved: 1-6 and 8; later: 7 and 9; rejected: 10). The coordinator's conditions: pre-registered and
frozen before the re-run, per-family trials printed on each verdict, incubation paper only. Review and
scores: `kestrel2_notes/ladder-easing-16nov.md`. This entry changes no code; the golden verdict in
`tests/unit/test_lab_verdict.py` is unchanged by it.

THE PRE-REGISTRATION (fixed exactly; the easing numbers are those of the review):

1. **Trials per family.** A cell's luck and deflation count every variant of its rule's family ever
   run - the rule and its whole parameter grid, abandoned sets included - and not the whole register
   (63,920 today). The count is printed on each verdict beside the cell.
2. **The basket.** A rule is judged on all its lines pooled as one portfolio at the desk's sizing.
   Each line is still reported on its own, but the pooled basket is what is judged.
3. **Incubation.** A rule whose basket's after-cost mean is at least one standard error above nothing
   and whose stress stays within 20% is INCUBATE, never PASS: paper only, one fixed small size, its
   own book line, promoted only on its live paper record and his yes.
4. **The retail rung.** The basket beats simply holding its market on risk: its after-cost Sharpe is
   at least the market's, OR it keeps at least 80% of the market's return with at most 60% of its
   worst fall.
5. **The full history** in `market_history.db` (under way: tf-rollup, ibkr-history-pull,
   consolidate-stores) is what the rules are judged on.
6. **The scorecard.** The hard fails are only a negative after-cost mean, a failed reproduction, or
   stress over 20%. Every other rung is graded and reported, and none stops the line.
8. **Costs against real fills.** The cost model is checked against real paper fills (q2-costs,
   R-RUNNER-145); an overstated cost under-judges every rule.

Kept, unchanged: costs always in (every verdict names the broker whose schedule priced it), the worst
fold reported and judged on, reproduction, the planted stop trade, and his yes before any rule trades.
Later, by their own conditions: (7) a one-sided test, after (1) is measured; (9) weather, after
R-RUNNER-205. Rejected: (10) fewer trades a line - noise without the benefit of pooling.

THE FREEZE. This whole set - the easings above and the switch that turns them on - is FROZEN from this
entry until the re-run of EPON. A change to it after seeing results is itself a counted trial, and is
recorded here with its count. The re-run's verdicts are read against this entry and no other.

Options considered for the register-wide trial count: (a) keep 63,920 for every cell - a bar that rises
forever as research grows; (b) count per family, abandoned variants included (chosen, as the review
scored it 9.5 and the coordinator required the abandoned sets be counted); (c) count only the variants
of the set at hand, which would let a family hide its failed grids. Chosen (b).

## The underlying cap: 40% of the capital (R-RUNNER-158, step 1)

`Settings.underlying` (0.40) is the one home of the cap; `risk.underlying_limit` judges it and the
pre-trade gate refuses a buy that would take one underlying market past it, counting a leveraged
line at its exposure (3x counts three times its value). Source: the coordinator's card of Sun 15 Nov
from the colleague-desk extraction, "Card items 1 to 6 for after Monday". Options: (a) cap in the
gate only; (b) cap in Settings beside the other limits (chosen: one config, one owner).
The gate takes the book's exposure per underlying as data, like the standing; the send path does
not yet give it (None checks nothing), so wiring it in is the remaining step. A line with no
recorded underlying counts as its own market.

## 16 Nov - main-guard allows rebase merges beside squash, for the merge train's batches, by his ruling

The ruleset `main-guard` (GitHub, id 27193932) changes in one parameter: the pull-request
rule's `allowed_merge_methods` goes from `["squash"]` to `["squash", "rebase"]`. The required
`check` job, the up-to-date rule (`strict_required_status_checks_policy: true`), the bans on
deletion and force-push, and the empty bypass list are unchanged. Applied by the coordinator
at 21:12 UK and read back from the API.

Why: the merge train merged one pull request at a time, about 8 to 15 an hour, and that was
the ceiling on building all day (one to three of twelve sessions at work). The runner's
batching (fix-plan F4, his answer "B", no move to an organization) builds one branch from
several pull requests that touch different files, with ONE COMMIT PER PULL REQUEST (its title,
its number, its Ticks line, its co-authors), and merges it with `--rebase`, so the check runs
once on main plus every member, and main still has one commit per change, each revertable on
its own (canon A6, A8). A squash would have put several changes in one commit. Only the
runner's batch step asks for `--rebase`; every other merge it sends is `--squash`, which a
drive in the runner proves.

What this loosens, said plainly: a pull request may now be merged with its own commits kept.
A lane's pull request with work-in-progress commits could put them on main if merged that
way. Guard against it: the runner arms lane pull requests with `--squash` only, and a batch
branch is built by the runner from squashed members.

His ruling, Mon 16 Nov 2026, in chat with the coordinator, answering the question put with
options ((a) allow rebase for the batches only, recommended; (b) keep squash only, a batch
becomes one commit; (c) no batching): "i trust your recommendations." The batching is
switched on (state\train-batch.on) only after the evening's rehearsal is GO.

## 17 Nov - the desk's file ceiling rises from 80 to 95, by his ruling

In `BUDGET.json`, `product_files` goes from 80 to 95 for phases `3-money-paper` and `4-ladder`.
`product_lines` stays at 15,000, and every per-file and per-function cap is unchanged.

Why: twelve desk files had reached the 400-line cap (book, conformance, placing, strategy,
day, bars, running, keeper, command, messenger, simcity, store), and the READY gate creates a
split card for each, but every split needs one new module and desk/ stood at 80 of 80 files.
One freed file unblocks one split, and folding enough small modules to free twelve would be
churn for no gain. Each split is pure restructuring: the file's tests unchanged and no
behaviour changed.

His ruling, Tue 17 Nov 2026, in chat with runner ops at about 14:20, answering the question
put by the coordinator with options ((a) raise to 95, recommended; (b) fold small modules to
make room; (c) leave the twelve waiting): "Option (a)".

## 19 Nov - the desk's file ceiling rises from 95 to 100, repaid by retire-epon

In `BUDGET.json`, `product_files` goes from 95 to 100 for phases `3-money-paper` and `4-ladder`.
`product_lines` stays at 15,000, and every per-file and per-function cap is unchanged.

Why: desk/ stands at 92 of 95 files. Three desk files at or near the 400-line cap block
trading-path work until they split (desk/keeper.py, desk/command.py at 400, desk/day.py at
390: split-desk-keeper, split-desk-command, then z3-own-ids, stop-at-fill, intraday-engine
and intraday-step), and each split, like each new-module card, needs one file.

REPAYMENT: retire-epon (R-RUNNER-127) deletes 19 desk files once catalogue-epon-rows
(R-RUNNER-219) gives every eponymous rule its catalogue row (6 of 20 on 19 Nov). Its pull
request sets `product_files` back to 95 or lower in both phases. R-RUNNER-219 is ranked so
that the repayment lands this week.

His ruling, Thu 19 Nov 2026, in chat with runner ops at about 19:10, answering the question
put with options ((a) raise by 5, repaid by retire-epon, recommended; (b) not yet), the
coordinator backing (a): "Yes, raise by 5".

## 2026-11-20: phase 3's product-line ceiling 15,000 -> 18,000 (the operator's ruling)

The desk stood at 14,895 of 15,000 product lines on Fri 20 Nov at about 16:00, so every card
that grows the desk (the broker fault matrix's behaviour groups, the order's own date, the
resend of a desk-cancelled order) would stall until it deleted lines elsewhere. Asked with
options ((a) 16,500 once, recommended; (b) 18,000; (c) keep 15,000), he chose (b): "Raise to
18,000", Fri 20 Nov 2026 about 15:55, in chat with the coordinator.

Conditions kept with it: every growing card names itself in its pull request, and growth,
bloat, sprawl and doom loops are reviewed in the 21:00 report. The ceiling still ratchets:
this file is the only place it moves, and only on his word.

## 2026-11-21: stop-rule rung pre-registered (R-RUNNER-408, `lab/rung_stops.py`)

Written before the rung was run. His word, Fri 20 Nov about 18:2x via the coordinator: "ok, go with
the ATR stop test". Research only: no live stop changes until a winner passes the ladder.

- **Rivals (4):** today's fixed stop (10% under the market's fall, 30% on a 3x line); ATR(20) stop
  at k = 2; ATR(20) stop at k = 3 (both set at the fill, from the ATR at the signal close); a
  chandelier trail (ATR(20), k = 3: the stop rises to the highest close less 3 ATRs, never falls).
- **Sizing:** shares = risk budget / stop distance, capped at the desk's room; the budget is what
  today's stop risks (10% times the line's leverage), so the fixed rule is sized as it is today.
- **Judging:** the EPON ladder's trades, after the desk's one cost model, in-sample and
  out-of-sample side by side (`lab/folds.py` cuts); the worst fold's answer is the one judged on,
  by the first rung's bar (30 trades, t >= 2). The same trades judge every rival.
- **Trials:** 4 rules (`rung_stops.TRIALS`) per line and fold, named for the luck correction. A
  rival is promoted only if it beats the fixed rule on its worst fold, from the centre of a plateau.

## 2026-11-20: the ladder's golden verdict, re-pinned under R-225, and the eased tests restored (R-RUNNER-396, RUNGS lane)

B5: `tests/unit/test_lab_rung_golden.py` was re-pinned by 5ebe658 (#993) under R-RUNNER-225's
easings. In plain English: with the easings on, a line is graded on every rung (a weak rung is
WEAK, no longer a fail), is charged only its rule's own family of trials, and a hard fail on
the first rung stops that line there; so the fixture's two lines now read THIN and FAIL where
the old table read otherwise. His 16 Nov "YES TO ALL" is the approval.
Two loosenings that change followed are undone here: the registry test again asserts that
every line not stopped by a hard fail is judged on first, market and folds, and the blanket
autouse switch-off in the ladder, retail and tape tests is gone: a test pins the easing off
only by name, with its reason beside it.

## 2026-11-21: whole-file reads may fall and never rise (failure pattern 26), his ask in chat

His words, Sat 21 Nov ~10:40: "can we mechanically never forget this? do not just write this
down, please build it and then verify." EPON's 1.2 GB results file, read and parsed whole on
every start, held 12.8 GB and judged nothing for nine hours. A new ratchet in
`tests/guards/test_ratchets.py` counts `read_bytes()`, `read_text()`, `readlines()` and a bare
`read()` in `desk/` and `lab/` against main: 37 today, and the count may only fall. A read of
a file that cannot grow is not counted when its own line says why (`# bounded: <why>`, words
required). Driven (A7) by appending one line to `desk/command.py` and running the ratchet:
`Path("big.jsonl").read_text()` FAILED (37 -> 38); `open("big.jsonl").read()` FAILED;
`read_text()  # bounded:` with no reason FAILED; `read_text()  # bounded: one-line marker
file` passed; a line-at-a-time loop over the file passed. After a blind review it counts
calls, not lines, and a mark on any line of a call that spans lines counts; driven again on
main at 39: a new `p.read_text()` in `desk/__init__.py` FAILED (39 -> 40); the same call
split over two lines with the mark on its second passed. A tightening: it adds a guard and
loosens none.

## 21 Nov - a file may hold 800 lines, not 400, by his own words

His words, to the coordinator in chat, Sat 21 Nov ~09:10, verbatim: "whilst we are in
development then relax these rules to allow natural file growth. but please monitor doom
loops." The coordinator recorded them (kestrel2_notes after-first-light.md, "Sat 21 Nov
09:3x HIS WORDS") and ruled them his plain-English yes to loosen one guard:
`max_lines_per_file` in `BUDGET.json` rises from 400 to 800 (order S). Unchanged: functions
stay under 50 lines, and the desk and lab package ceilings stay as they are.

Why: sessions were splitting files only to stay under 400 (simcity, store, orders), each
split a pull request that moved lines without adding behaviour. The package ceilings still
bound growth; the doom-loop watch is the stall monitor and the recurring-fix rule (A2).

Guard proven (A7): an 801-line file under `desk/` made `test_no_file_is_a_monolith` fail
("over 800 lines"); an 800-line file passed; both removed.

## 21 Nov - the lab may hold 20,000 lines, not 12,000, by his own words

His words, to the coordinator in chat, Sat 21 Nov ~11:2x (clock-checked 11:32), verbatim:
"raise the Experimental-code area ceiling to 20,000. we can iteratively refactor in the
future." The coordinator recorded them (kestrel2_notes HANDOVER-coordinator.md, "HIS WORDS
11:2x") and ordered this change (order A). `lab_lines` in `BUDGET.json` rises from 12,000
to 20,000 in phases 3 and 4, as his 15 Nov ruling raised both to 12,000. Unchanged: the
desk ceilings, the file and function limits.

Why: research cards stood still "waiting for room" with lab/ at 11,951 of 12,000 and more
riding; building had fallen to 0 of 12. The cleanup he named is a later refactor, not a
precondition.

Guard proven (A7): lab/ padded to 20,001 lines made `test_the_tree_is_inside_this_phases_ceiling`
fail ("ceiling 20000"); at 20,000 it passed; the padding removed.

## 21 Nov - a '*' session's own check holds it to the files it named in .claim

A session holding '*' (a serial run, or a box noted `files: *`) now names its files in
`.claim` at its worktree's top before any edit, and the runner holds only those, so the
rest of its lane can run beside it (runner item 7, coordinator 40, Sat 19:5x). Until now its
local check still read '*' and allowed any file of the lane. `tests/guards/test_lanes.py`
now reads `.claim` when the claim it is given holds '*', so the session's check and the
runner's hold read one claim. This narrows what a session may change: a tightening. A pull
request's own Claim line on GitHub is read as before.

Guard proven (A7): in a scratch clone, on a `lane/money-...` branch changing
`desk/orders.py` with `KESTREL_CLAIM='*'`: no `.claim` passed; `.claim` naming
`desk/day.py` made `test_a_lane_changes_only_what_it_claimed` fail; `.claim` naming
`desk/orders.py` passed. On main's guard all three passed (the hole).

## 22 Nov - the rulebooks rewritten so seats, cards and memory are rules with checks, and the failure patterns capped

His order in chat (Sun 22 Nov ~12:00): an independent (Fable) review of CLAUDE.md, CANON.md and the
notes' LESSONS.md, then best-in-class versions that stop doom loops, bloat and sprawl and keep work as
code, not prose. The review found the canon governed lanes only while every recent failure was in the
seats; four progress numbers (scenes, cards, boxes, commits); CLAUDE.md's false "a guard is owed";
self-approved loosening of guards against his hard lines; and FAILURE_PATTERNS.md imported into every
session with no cap. Changes: CANON.md gains Part C (seats, cards and memory: every rule names its check
or is marked OWED), A6 Ready holds a card to ten minutes with its exact files and failing test, A8 decides
by rule and absorbs A9; CLAUDE.md names one outcome number (plan boxes ticked on main per 24 h), the seats,
the 70% handover, IBKR first for prices, and makes loosening a guard his alone, default no. No rule was
dropped to make room: each was merged or moved (A7's story is failure pattern 1).

The failure patterns are capped at today's 221 lines, down-only (a tightening). Guard proven (A7):
with the cap at 220, `test_the_rulebooks_stay_short` failed; at 221 it passed.

## 22 Nov - the zoo trades on paper as a MACHINERY TEST while the ladder runs, by his own words

His ruling in chat (Sun 22 Nov 14:1x): "CANON B6 is correct, but, when the ladder testing is taking so
long then we need to revise this ruling... run these strategies to test the desk whilst we wait for the
ladder to finish." The ladder will not finish before about Wed to Thu. Options: (a) wait for the ladder,
which leaves the desk's intraday path untested on paper for days; (b) let the collated rules trade at the
desk's normal size, which would read as evidence and risk the desk's book; (c) DECIDED: a machinery test,
inside the existing safety design. CANON B6 gains the one line (merged with its promotion line, 198 lines).

What (c) is, and the check that fails on each breach (`tests/unit/test_running_intraday.py`,
`test_the_zoo_is_off_by_default_and_trades_one_share_labelled_only_behind_its_switch`):
- OFF by default: `Desk.zoo` is False, and `command._desk` turns it on only when the file `zoo-on-paper`
  (`running.ZOO_ON`) is in the desk's root. The rehearsal's root is its own folder, so it never trades it.
- PAPER only: the step's one broker is the paper Gateway's (`running._paper`); nothing new dials anything.
- TINY: each zoo buy is one share; the one gate (`day._send`: loss, rate, exposure, kill switch) is unchanged.
- ITS OWN ORDER IDS: `<day>-zoo_<rule>-<line>-<HHMM><B|S>`; `strategy_of` reads `zoo_<rule>`, so its
  fills stand apart in the ledger and a zoo rule sells only what it bought. A buy of a line held already
  (by any rule), parked by hand, or no ISA can hold sends nothing, through the daily buy's own
  refusals now in one home (`day.refusal`, R-RUNNER-436), so a zoo sale never sells the desk's shares.
- LABELLED: every zoo order's line in the record says "MACHINERY TEST, NOT EVIDENCE OF AN EDGE".
- NOT ON HIS PHONE AT EACH BAR (coordinator 78): zoo notes are kept as `zoo <venue> <HHMM>`, never sent
  one by one; his hourly message carries one line of the zoo's last hour (`running.zoo_hour`).
- ITS OWN ALLOWANCE (coordinator 78): zoo orders meet the gate with `running.ZOO_ROOM` (£1,000: 2% a day,
  5% a week, 10 new lines a day) and the zoo's own standing; the desk's standing (`day.standing`, also
  the drawdown halt) leaves out the zoo's lines and its round trips' pounds, so the zoo never spends the
  desk's four new lines or its loss limits (`test_day_standing.py`, driven red both ways). The gate also
  counts a buy's holdings and room by side (`book.side`), so the zoo's holdings never fill the desk's five;
  a sale meets the whole book, so go flat (the second kill level) still sells every zoo share.
BLIND REVIEW (A6 step 6, a fresh reviewer given only the diff and this claim): BLOCKING, the zoo and the
desk shared the gate's five holdings; fixed by `book.side` (test seen red without it). Also fixed: two zoo
rules stacking a line in one bar (the book is read afresh for each rule), zoo orders sized with the zoo's
allowance, the day's rates kept first in the intraday round. Accepted as approximate, with one share each
worth pence: the zoo's pounds are taken from the day its round trip closes (a zoo line held overnight shifts
a day's split), and the hourly line counts a refusal's own '; ' as an order. The reviewer's re-check of the
fixes found one more BLOCKING issue (go flat could not sell zoo shares through `book.side`); fixed, test seen red.
- NEVER A-GATE, NEVER PROMOTED: zoo names are never in `STRATEGIES` or `intraday.RULES`
  (`test_intraday_zoo.py`), and promotion reads only its candidates' own fills (`lab/promotion.py`).
Scope for Mon 23 Nov: the zoo's seven day-trading rules (5- and 15-minute bars) on the zoo's lines. Owed:
the zoo's thirteen daily rules (they need the daily round, `desk/day.py`), and the Grimes AG catalogue
(no AG rule exists as code yet). Guard proven (A7): with `zoo` defaulting to True the test failed at its
first assert; with the one-share cap removed it failed (23 shares bought, not 1).

## 22 Nov - Grimes's ten setups join the zoo as a paper MACHINERY TEST (his "both now")

His words in chat (Sun 22 Nov 15:3x, via the coordinator): "both now": build the ten AG strategies now, beside
the ladder, to trade on paper as a test of the desk; the ladder stays the only gate for edge and money (CANON
B6, his 22 Nov ruling on zoo machinery above, PR #1682). Decided, with options:
- WHERE: desk/ may never import lab/, so rules the desk runs live in desk/; an `eponymous_*` file would put them
  in the ladder's rule book and its published-figure checks, so they get their own `desk/grimes.py`; desk/ held
  100 of 100 files, so `desk/simcity_parts2.py` was folded into `simcity_parts.py` first (#1691, a pure move).
- WHAT: the catalogue (kestrel2_research/grimes/catalogue.md v3, review 9.8) at its defaults, long only, on the
  daily bar (the intraday round shows a rule one session, under the 60-bar warm-up the blocks need), one share.
  Left to the ladder: sweeps, sizing by risk, shorts through inverse ETFs, the weekly (HTF) contexts, the MGMT
  study. A resting order becomes a bar trading through its level, filled at the next open (the engine's fill).
- HOW IT TRADES: as daily zoo machines `zoo_ag01_...` to `zoo_ag10_...` in `desk/intraday.py` ZOO, so the zoo's
  switch, its own allowance, its one-share cap and its MACHINERY TEST label apply; they trade only when the
  zoo's daily round (zoo-daily) reads ZOO's daily machines, behind the `zoo-on-paper` file. Never in STRATEGIES,
  never A-GATE (`test_intraday_zoo.py`).
Guard proven (A7): the tests were written after the code, so each was driven red by a planted mutation of the
condition it names, 13 of 13 caught: AG-01 shared high not needed, AG-02 close back over the boundary dropped,
AG-03 CD/AB band widened, AG-04 reaction limit 50% to 80%, AG-05 spring's close inside dropped, AG-06 context
always true, AG-07 retrace 62% to 80%, AG-08 pierce of K by any bar, AG-09 weak thrust under 2x mean, AG-10 top
third to two thirds, MGMT breakeven dropped, MGMT parabolic stop dropped, SW confirming at a third of z. The drive
first found three near-misses blocked by a second condition (AG-01, AG-02, AG-08) and a swing test passing on a
tie; each was rebuilt until the named condition alone decided it.

## 22 Nov - a lane may fold away its own module (R-RUNGS-29), by his own words

**His words** (chat seat 44, Sun 22 Nov ~18:1x), asked whether lanes may remove their own
modules' lines from the manifest so the ladder's eight owed rungs can be wired and merged:
"Yes / I trust your recommendations / Do what is required to speed up". Loosening a guard
is his alone (CLAUDE.md); this is that yes.

**What changed.** `tests/guards/test_lanes.py`: a lane branch may now also *remove* the
manifest line of a module it owned on main (the merge-base manifest), and change that
module's files and tests while folding it away. Nothing else moves: removing or adding
another lane's line, editing any non-module line, and touching another lane's files are
refused as before. Before, `rungs-each-rung` waited on this since 19 Nov (R-RUNGS-29:
five of the eight owed rungs fold into another module), and MONEY rightly declined it
(#1417): a guard no lane owns.

**Driven (A7)**, on scratch clones whose main held the guard, each scenario on a
`lane/rungs-...` branch, `test_a_lane_changes_only_its_own_files`:

| scenario | old guard | new guard |
|---|---|---|
| fold own: remove `lab/rung_ci.py`'s line, delete it and its tests | FAIL | pass |
| remove MONEY's `desk/orders.py` line | FAIL | FAIL |
| add a planted `desk/zzz.py` line under MONEY's heading | FAIL | FAIL |
| edit a non-module line (MONEY's heading) | FAIL | FAIL |
| delete MONEY's `desk/orders.py` | FAIL | FAIL |

## 22 Nov - the zoo's thirteen daily rules join the morning round, and the zoo yields every line to the desk

His order (Sun 22 Nov 15:3x, "both now") under the same 14:1x ruling and conditions as above. Options for
where the daily zoo trades: (a) a second daily engine beside `day.trade`, which B2 forbids; (b) the zoo's
rules added to `strategy.STRATEGIES`, which would make them A-GATE candidates and change the desk's goldens;
(c) DECIDED: one more step at the end of the same morning round (`day._zoo`), after the desk's own orders,
on the same bars, the same send path and gate, behind the same switch (`Desk.zoo`, the file `zoo-on-paper`).
Options for the book: a separate book file cannot work (the paper account holds one position per line, and
the stop follows the line's newest buy, `restop`), so ONE OWNER PER LINE stands, and the desk comes first:
- THE ZOO YIELDS (`day._yields`): a line one of the desk's rules buys today that a zoo rule (daily or
  intraday) holds is sold out of the zoo first, under the zoo rule's id; the desk's "sold this morning"
  reads only the desk's own sales, so its buy goes as if the zoo were not there.
- THE GATE SEES ONE SIDE (`book.side`): a zoo order's gate counts the zoo's lines alone, a desk order's
  the desk's, so zoo lines fill none of the desk's five holdings, room or correlation cap. Not split: the
  pounds per underlying (`day_money.exposure`) still count the zoo's single shares (a few pounds against
  a 40% cap), recorded rather than built.
- ONE SHARE, ITS OWN ALLOWANCE: a daily zoo buy is one share on `orders.ZOO_ROOM` (moved from running.py,
  one home) and the zoo's own standing; refused as the desk's own (`day.refusal`, sold this morning).
- NEWS HOURLY: the morning round's zoo answers are kept as a `zoo <venue>` note, labelled MACHINERY TEST,
  NOT EVIDENCE OF AN EDGE, told only in his hourly line (`running.zoo_hour`), never in the round's message.
- Goldens unchanged: with no zoo fills every new path is a no-op (`_yields` sends nothing, `_side` is the
  whole book), and SimCity and replays never set the switch.
Check: `tests/unit/test_day_standing.py::test_the_daily_zoo_buys_one_share_a_rule_only_when_on_and_yields_the_desks_lines`.
Guard proven (A7): it failed first (no `intraday.ZOO_DAILY`); then with the gate given the whole book
("1 holdings already, at most 1"), with no yield (1 share, not more), and with the desk's "sold this
morning" reading the zoo's sales too (no VUAG bought).
Blind review (CANON A6.6) found one blocking fault, fixed: the zoo's sales were dated today, and the
paper door refuses an order not dated the session before (`placing.py`; the pretend broker never checks,
failure pattern 15), so no zoo sale would ever have filled. Now dated as the desk's own; the test records
every placed order's session and failed (dated Wednesday) before the fix.

## 22 Nov - the one-price-door guard, the last condition on the price-one-door hold

His ruling (~10:00, "paramount"): every price is read from market_history.db or market_live.db.
The hold on the ladder and grid jobs (runner ops 69) asked for all five doors AND
`tests/guards/test_one_price_door.py`; the five doors are on main (#1672, #1674, #1683, #1697,
money-door-slippage), but no card ever built the guard, so the hold could never lift (pattern 20).
The guard: outside seven writers named in the manifest as letting outside prices in, no line in
desk/ or lab/ asks the archive or reads a price file. Driven (A7) on a scratch worktree: green on
main; red naming `lab/ladder.py:354` for a planted `archive.fetch`, and `desk/day.py:525` for a
planted `read_csv`; green again with both removed.

## 22 Nov - a wait names a real request (guard), and four waits that could never lift

`tests/guards/test_waits.py`: every request an open box waits on is a request line in STATUS.
Driven (A7): red on main naming R-MONEY-31, R-RUNGS-14, R-RUNGS-7, R-RUNGS-9; green after.
R-RUNGS-9 (#544, #889) and R-RUNGS-14 (#508) were done but never lines: now `- [x]`, which
frees rungs-reproduce of them. R-RUNGS-7 is written as the open MONEY request it is.
money-restop waited on R-MONEY-31, never a line: its text ("the day's list message includes its
lost-stop entries") is the open R-MONEY-53, so the wait names that.

## 22 Nov - every desk rule is reached by the rulebook or the zoo (guard, G27)

Coordinator 96 (G27): desk/grimes.py landed (#1693, #1694) and nothing in desk/ or lab/ reaches
it, so its rules can never trade, even as the machinery test he ordered (zoo plus AG on paper).
`tests/guards/test_zoo_reach.py`: a desk module importing the rule declaration is named
eponymous_* (lab/rulebook.py globs those) or is imported by desk/intraday.py, the zoo's path.
Driven (A7) on a scratch worktree: red on main 10004db0 naming desk/grimes.py; green with #1696's
desk/intraday.py (the ten AG setups join the zoo). Rejected: "imported by any module" (the
rungs and eponymous rules are found by glob and would all read as orphans). It lands after #1696.

## 23 Nov - every open request has its own box (guard), and 30 run-on lines split
Runner ops 113, coordinator 107/110's H1: the runner reads one request per `- [ ]` line in STATUS, so a
request written inside another's line was never offered or was read as met (data-survivorship's re-offer
loop, R-DATA-68, 01:36). `tests/guards/test_lanes.py::test_every_open_request_has_its_own_box` refuses any
`R-X-n (later` or `(blocking` not at the head of its own checkbox line. Driven: RED on main's STATUS
(a63c9bf2 era, 26 run-on requests, R-MONEY-8 first), GREEN after this change splits all 30 run-on lines
mechanically, each request on its own line with its own words. A split request keeps its line's box
unless its own words say it is done (`[x]` before it, `(done ...`, `done in #n`, `Met by #n`): 15 such.
Tightening only; nothing is loosened.

## 23 Nov - one cap at one place over the whole round; the golden run moves (R-RUNNER-456)
Coordinator 140's ruling 13:1x(b), after two NO-GOs (#2036, #2055: a carried order had no intent and
no chain): the cap acts at ONE place, `day._send`, the one door every order of the round passes after
`book.intend` and before `book.chain`. It reads the round's answers so far; once `paper.MAX_ORDERS` (7,
paper's step time) asked the broker, the order is answered `Blocker.CARRIED`, chained and on the
morning's list. Order: stranger sales, desk sales, zoo yields, desk buys, then the zoo. Options: the
cap at each call site (rejected twice: no chain, four copies) or in the send door (taken). N2 decided:
an answer takes a slot only if the broker was asked (filled, or the broker's own BROKER answer); one
the gate, a halt, the kill switch, the book or a held line stopped takes none (test plants 16 killed
buys and the zoo still gets all 7). Golden run (canon B5, the desk approves goldens, his 22 Nov):
Mon 11 Aug 2025 decides 17 orders on Friday's bars; 7 go, 9 desk buys are carried (L07, L09, L11, L12,
L13, L16, L17, L20, VUAG), 1 is held. Carried buys are not re-sent (R-RUNNER-456 leaves the re-send
open), so the desk buys L12, L15, L16 on 13 Aug instead of L07, L09 on the 11th; two of them stop out
on 14-15 Aug. Fills (64), trips (32) and days (310) stand; costs move from 353.78 to 351.96 and
profit from 61.86 to -154.51. Before, the round sent every order whatever the step's time, which the 900 s step cannot hold
at 120 s a fill (failure pattern 24).

## 23 Nov - six operator waits that were not his hard lines, decided by the desk
Coordinator 140's ORDER 13:2x, carried out by runner ops 144. His 22 Nov ruling: "nothing parks on him but
hard lines" (live, credentials, spend, deleting data, loosening a guard). Six PLAN boxes carried
`waits: operator` with none of those behind them; four only needed runner ops to widen a claim.
Options: leave them parked (lanes idle for want of a card), or decide each by rule. Decided by rule:
data-members builds from the free page revisions and names every source with no free feed UNMEASURED (no
paid data before profit); rungs-each-rung widens to lab/rung.py and its calibration test (sample into rung
1); rungs-plateau-wired already names its four files and is held by its after: link alone; rungs-blocks
widens to lab/spec.py, its test and the manifest; rungs-fast-engine and rungs-eponymous are held by their
after: links alone, and real money stays his. data-disk-rolloff keeps its wait: deleting data is his.
Check: `tests/guards/test_lanes.py` still reads every remaining wait; the runner's READY gate holds each box
behind its after: link.

## 23 Nov - four RUNGS waits lifted; the known-answer kit before the fast engine
Coordinator 158's ruling 19:3x, carried out by runner ops 159. His words: 22 Nov "nothing parks on him but hard
lines", and 23 Nov 19:2x "allow the ladder to run 24x7". Options: keep `waits: operator` on four RUNGS boxes
(the ladder chain idles behind them) or let each be held by its after: links alone. Decided by rule: the waits
leave rungs-plateau-wired, rungs-eponymous, rungs-indicators (ticked) and rungs-fast-engine, none of them a hard
line; real money stays his. A new box, rungs-known-answer-kit, follows the blind review, and the fast engine
waits on it (a parity test first, canon B2). data-disk-rolloff keeps its wait: deleting data is his, and his
yes of 23 Nov 19:3x named five folders once, not a standing rule.
Check: `tests/guards/test_lanes.py` reads every wait and after: link; the runner's READY gate holds each box
behind its after: links.

## 24 Nov - the block bootstrap is wired into the ci rung (R-RUNNER-503, RUNGS lane)

`Rung.judge` now takes the first rung's verdict, the bars and the day's rates; the ci rung's
answer is its interval's, held to the block bootstrap (`rung_ci.bootstrap`): an interval PASS
whose redrawn runs of days made nothing or lost more than 2.5% of the time is DOUBT. Options for
that case: FAIL (the bootstrap gates, as its module says), DOUBT, or leave it a PASS. Decided
DOUBT, by canon LAD-08: FAIL is for an interval wholly below nothing; a PASS the days' runs do
not bear out is a doubt about the rule, never proof of a loss. Too few days to draw (THIN) leaves
the PASS standing (LAD-06). Golden verdicts moved: none (the ladder's golden and the registry
tests pass unchanged); calibration worlds now carry daily bars, as the bootstrap reads them.

## 26 Nov - the desk's ceiling raised from 18,000 to 30,000 lines (his ruling)

**His words.** In chat, Thursday 26 November 2026, about 13:45 UK, offered 20,000 (recommended),
22,000 or 18,000 kept, he chose "Raise to 22,000".

**His words, about 14:00 the same day.** "if we need to add more code to build the desk then this is ok. go to a limit that is sensible. what we need to be careful about is doon loops, bloat and sprawl. if we can monitor those things closely then line limits can grow as they are needed to ... if we need 50,000 lines to build the desk then this is fine as long as we know there is no doon loops, bloat and sprawl."

**Decided.** `BUDGET.json`'s phase 3 `product_lines` goes from 18,000 to 30,000, sized for the
money features and the five lane books; it rises again, by his words above, when the desk needs
it and the doom-loop (`tests/guards/test_churn.py`), bloat and sprawl checks are green. The guard
stays and still fails one line past the new ceiling; files stay under 800 lines each.

**Why.** The desk stood at 18,000 of 18,000, so every money feature had first to delete as
much as it added; his rulings of the same hour (risk-based sizing, trend and market filters,
TP1/TP2/TP3 take-profits: R-RUNNER-543 to 545) and the money fixes need room to land.

## 26 Nov - doom loops, bloat and sprawl held by code, not prose (his ruling)

**His words.** In chat, Thursday 26 November 2026, about 14:10 UK: "we have updated the claude.md
file and other md files to watch for doom loops, bloat and sprawl. it is clear that this is just
prose. i want you to add code wherever is needed to control doom loops, bloat and sprawl. this is
a must."

**What already held each.** Doom loops: `tests/guards/test_churn.py` and the runner's halt on a
second `fix` to the same file. Sprawl: the file and function size guards, the manifest's register
and wall, the versioned-copy and document-set guards. Bloat: the undocumented and whole-file-read
ratchets and the 300-line change cap.

**Added** (three ratchets in `tests/guards/test_ratchets.py`, each may fall and never rise against
main): duplicate function bodies in `desk/` and `lab/` (5 on main), top-level definitions that
nothing in `desk/`, `lab/`, `tests/` or `check.py` uses (0 on main), and constant names assigned
in two or more modules, every extra home counted (168 on main: failure pattern 8, whose debt this
closes; `CAPITAL` in `desk/command.py` and `lab/stop_rules.py` among them).

**Driven (A7).** On a copy of main whose ratchets passed, `desk/halt.py` was given a copy of
`desk/strategy.py`'s `_run`, an unused `planted_dead_function` and `CAPITAL = 3`: duplicates rose
5 to 6, unused 0 to 2, both failing; the two-homes test, first written to count names, did NOT
fail (CAPITAL already had two homes), so it was rewritten to count every extra home and driven
again: 168 to 169, failing. With the plants removed all pass.

## 26 Nov - the manifest split into one file per lane (guard restructured, stricter)

**His words** (Thu 26 Nov 17:5x, to chat seat 215): "check if you still agree that this fix is
the best one and them implement now. no more prose. build it." and "yes to all. now implement and
build and wire." The fix is the one recommended on 15 Nov (`kestrel2_notes/after-first-light.md`
:222 and :232): "manifest -> one fragment per lane", "split by lane, joined at read time by the one
loader, never rejoined on disk". Why now: on 26 Nov the runner's cards name `manifest.toml` 56
times, and one file is held by one lane at a time, so every card that registers a module waited
behind every other lane's (the governor's 'claims N').

**Shape.** `manifest.toml` keeps `[packages.*]`, `[lanes]` and the two package markers;
`manifest/<lane>.toml` holds each lane's `[modules]`, exactly the lines once under its heading
(174 modules: data 36, money 49, paper 25, grid 8, rungs 54; checked equal before and after).
One loader, `manifest()` in `tests/guards/test_guards.py`, merges them for every reader
(`test_guards.py`, `test_lanes.py`); `check.py`, `test_one_price_door.py` and `test_ratchets.py`
only name the manifest in prose, so they needed no change.

**Every rule as strict or stricter.** A module's lane is the file it sits in, not a comment
heading. The loader fails on a module listed twice, a file in `manifest/` not named for a lane, a
lane without its file, a fragment holding anything but `[modules]`, and a lane module in
`manifest.toml` (all new refusals). A lane branch may change only its own fragment, and there only
module lines (as before); `manifest.toml` itself, once open to a lane's module lines, is now
refused to every lane branch, and the claim test excuses only the lane's own fragment where it
excused all of `manifest.toml`. The guard-change warning on GitHub names `manifest/` too.

**Driven (A7)**, on a clone whose main was this change, each plant alone on a `lane/money-` branch:
1. `desk/book.py` also listed in `manifest/paper.toml`: "manifest/paper.toml lists ['desk/book.py'],
   listed already: one home each".
2. the money branch edits `manifest/paper.toml`: "the money lane may not change
   ['manifest/paper.toml']".
3. the money branch edits `manifest.toml`: "the money lane may not change ['manifest.toml']".
4. `desk/zzdrive.py` with no line: "not in the manifest: ['desk/zzdrive.py']".
5. a comment added to `manifest/money.toml`: "may only register or fold away modules: ['+# a note']".
6. `manifest/zoo.toml`: "manifest/ holds [... 'zoo.toml']; exactly one file per lane".
7. a lane module in `manifest.toml`: "manifest.toml lists lane modules ['desk/zzdrive.py']".
Control: the money branch registering `desk/zzdrive.py` in `manifest/money.toml` passes both tests.
Open pull requests that edit `manifest.toml` (#2107) rebase onto their lane's fragment; the
runner's card claims are renamed by runner ops after this lands.

## 26 Nov - plateau is judged on every cell (L17, RUNGS)

**Why.** Nothing could go forward: `verdict_parts.goes` asks that no rung be unrun, and plateau was
always unrun, as the ladder hands `verdict.judge` no surface (`lab/ladder.py`, claimed by RUNGS-s4).
Chat seat 215's order (26 Nov): the verdict builds the plateau itself, the one home of the answer.

**Options.** (a) the ladder builds the surface (its file is claimed; two homes for one rung);
(b) `verdict.judge` builds it when handed none (chosen). Its parameter goes dead: dropping it is a
RUNGS follow-up once RUNGS-s4 frees `lab/ladder.py`.

**What it does.** A rule with no ranges is FIXED: NOT APPLICABLE, a PASS (decision a). A ranged
rule's own setting that failed its first rung is 0 deep whatever its neighbours, so it FAILs with
no variant run. Only a cell whose own setting passed has its row's variants (3 to 27) run on its
own line, window and bars. Found on the way: `published.proven` refused every variant (no
publication under a variant's name), so a variant could never be judged. A variant is its row's
code at other settings, so it is held to its row's publication; a variant of a row with none is
still refused (`test_a_variant_is_held_to_its_rows_publication_and_refused_without_one`). A basket
keeps its own unrun line, so its pass is still no pass of the whole ladder.

**The golden moves (B5).** `test_lab_rung_golden.py`'s edge row gains a plateau rung, PASS as NOT
APPLICABLE (the breakout has no settings); no answer and no other rung changes. The noise row
stops at its hard fail before plateau, so it is unchanged.

**Cost, measured** on a 2,400-bar walk: 0.4 s a variant, about 3.6 s for a passing cell (9
variants on average). EPON's ~21,000 cells: at most ~21 CPU hours were every cell to pass, under
four hours on the pool's six workers; in practice only passing cells pay, a small share.

## 26 Nov - reproduce, with no author's figure, is judged on determinism (RUNGS)

**Ruled by chat seat 215** (26 Nov, 18:5x). A rule with no author's figure on file stayed UNRUN
for ever (`verdict.NO_FIGURE`), and `goes()` lets nothing forward with a rung unrun. No figure
is on file (`reproduce.FIGURES` is empty), so no rule could ever go forward.

**Options.** (a) keep it UNRUN until figures are read: requiring a figure that does not exist
forbids every unpublished rule for ever and tests nothing of the rule; (b) excuse it: a rung
that cannot fail; (c) judge it by determinism as PLUMB LINE v2 defines reproduce, "identical
verdict on a re-run with the same seed and data" (chosen). The determinism test can fail, so it
is a real rung (A7).

**What it does.** With no figure, the cell and its first rung are run again on the same bars
and code; PASS only on the identical verdict (every priced trade, the t and the answer), and a
FAIL is a hard fail that stops the line. Its reason names the form: "no author's figure: judged
on determinism". A rule with a figure keeps the author's-figure test, whose reason begins
"reproduced:". The shuffle is not run twice: it is seeded by the trial's name. Cost: one more
first-rung run a cell, about 0.4 s.

**Driven (A7).** A planted coin (the cell drops its last trade on every other run) FAILs the
rung; the breakout on a walk PASSes
(`test_a_rule_with_no_figure_is_judged_on_determinism_and_a_planted_coin_fails_it`).

**The golden moves (B5).** `test_lab_rung_golden.py`'s edge row gains a reproduce rung, PASS on
determinism; no answer and no other rung changes. Its noise row stops at its hard fail first.

**Blind review (26 Nov, Fable, CANON A6 step 6): one blocking finding, fixed.** Determinism stood in
for every rule with no figure, Faber's too, whose author's test binds (`published_epon.TESTED`,
`candidate`): his printed figure would never have been asked, and `promotion.Candidate` would have
let him onto paper unreproduced. Now determinism judges only a rule no author's test binds; one
that binds keeps reproduce UNRUN (`NO_FIGURE`) until its figure is on file and reproduced. Seen red
first: `test_a_rule_whose_authors_test_binds_waits_for_its_figure_never_for_determinism`.

## 26 Nov - the rest of the answer key (PLUMB LINE v2 step 2, RUNGS)

Seat 215's order, the rest of the key, every rung real (no rung's own result stubbed):
- **The drift-rider** (`Dart`, in or out with a chance of a tenth a day by the day's own seed) on four
  US lines rising 0.1% a day, run EASED as EPON runs: the real shuffle FAILs it on every line
  (shares 0.23 to 0.91) and the market rung FAILs it beyond its own line's moves; on NVDA its first
  rung PASSes (2.45), so the key shows the first rung fooled and the later rungs catching it.
- **Noise: 160 cells in the unit check, 1,008 once outside it.** There is no nightly tier and a
  unit shard holds about five minutes; 1,000 cells take 15 to 18 minutes. Chosen: 10 sets of 16
  (about 3 minutes), passing at most 2% (3 cells). Honestly sized: at a true false pass of 2% the
  160 show over 3 about a third of the time, at 5% nine times in ten, so it catches a ladder that
  lets noise through, not the 2% edge itself. The 1,008 (63 sets of 16, seeds 1000 on) were run
  once on 26 Nov through the same ladder with plateau and reproduce wired: 0 went forward, every one
  FAIL, 952 s.
- **Planted edges at a true t of 1, 2, 3 and 4** (the churner on the kit's paid line, its tilt set
  from the mean and spread measured at no tilt): stated first-rung pass rates 0.16, 0.50, 0.84, 0.98
  (a normal above 2 - t), found 0.20, 0.65, 0.95, 1.00 on 20 lines each, within 0.25 and rising; the
  first rung is the rung a true t governs, so the rates are stated for it.
- **A delisted line** (AMD cut at 2023-06-30 among 16): judged, FAIL, never an error; the 2025 fold
  pooled over the 15 lines still trading. Found: its regimes rung FAULTs (STATUS, found not fixed).
- **L17's gate met:** the kit's paid edge goes forward on every line.

**Driven (A7)**, each against a planted fault from a plugin outside the tree: the shuffle replaced
by a constant pass (main's fake proof) turns the drift-rider's shuffle row red; a ladder that
passes everything turns the noise test red (9 of 160 went forward); a first rung passing any t
above nothing turns the planted-edge rates red. The paid-edge test was red on the plateau branch
alone, reproduce still UNRUN.

**Shard weights.** `check.py` SECONDS gains the two key files (220 s, 205 s, measured on the PC), so
the sharder does not weigh them by size as near nothing. A weight loosens nothing.
