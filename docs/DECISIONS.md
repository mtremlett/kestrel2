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

### 2026-11-13 — the money book's next boxes noted: the kill switch first (#76)

**Decided**, by the lane as the desk's mentor.
- *The kill switch's files.* Options: refuse at the gate in `desk/orders.py`, or on the send
  path in `desk/book.py`. Chosen: the send path, with a new `desk/kill.py` and `desk/broker.py`
  (cancelling). The gate stays a pure rule over the order and the book; whether the switch is
  thrown is a fact on disk, read at the edge where the reconciliation refusal already lives.
- *The costs wait for the kill switch (`after: money-kill`).* Options: side by side, or in turn.
  Chosen: in turn; both change `desk/book.py`, and his ruling puts the kill switch first.
- *The crash watch left un-noted.* Options: note it with no `after` (a session would meet it
  before the five-minute data exists), or wait. Chosen: wait for the data lane's box ids.
- *File lists err wide.* A session may change nothing outside its note, so a missing file strands
  it; a wider note only makes it wait its turn.

### 2026-11-13 — each strategy declares what it is (#92, money-declared)

**Decided**, by the lane as the desk's mentor.
- *Holding period: each of the five declares none.* Options: (a) 5 sessions for RSI-2 and 20 for
  Bollinger, the span of the average each sells on; (b) none for all five; (c) a number measured
  from history. First built (a), but neither published rule has a time exit: RSI-2 outstays 5
  sessions in 13 of 39 golden trades, Bollinger outstays 20 in 29 of 52 (longest 133). Chosen (b):
  a declaration says only what its rule does; (c) is tuning. The time stop (STP-11) must choose
  each limit and build the exit in the same change; the golden days will move, so it needs his
  approval (canon B5).
- *Test universe: every line of the instrument master, by reference.* Options: (a) the master's
  lines; (b) a narrower list per rule; (c) a rule about a line's facts. Chosen (a): a rule judged on
  fewer lines than it trades would trade unjudged; (b) changes what is traded with no evidence;
  (c) makes the research list part of a verdict. By reference, so a new line is declared at once.
- *Data: the numbers of the daily bar a rule reads*, proved (not a named source: the desk has one).
- *The bar is one value, daily;* a second comes with the bars that would feed it.
- *The declaration sits on the rule itself.* Options: (a) on the rule; (b) a second table by name;
  (c) a wrapper. Chosen (a): one home; a rule without one fails the type check.
- *A short sale.* No word for it in declaration, action or decision; the template sells only what
  is held. A hand-made decision to sell is left to the gate (refusing it at its making breaks
  orders tests this box may not edit); the true fix is the order type (recommended box).
- *Ticked though a remainder is named:* a session given the same files could do no more.

### 2026-11-13 — the kill switch and its drill (#95, money-kill)

**Decided**, by the lane as the desk's mentor.
- *The stops stay.* Options: (a) cancel everything, stops included; (b) cancel and sell all held;
  (c) cancel working orders, keep the stops. Chosen (c): removing stops would leave holdings
  unprotected when something is wrong; selling all is a trading decision. The message says what is held.
- *Sales are refused too* (not only buys): all new orders stop, the one promise simple enough to
  trust in an emergency; the stops at the broker still sell.
- *The switch goes on the record before the broker is asked*: the desk is stopped even if the
  broker's line is down.
- *The send path reads the switch itself* (`desk/book.py`), not callers: nothing bypasses it (B1).
  It reads twice, before the broker is asked and at the last moment before the order goes; each
  reading was removed in turn and the tests caught both.
- *An order the broker already has is still recorded while the switch is on*: recording sends
  nothing, and refusing would leave the book wrong.
- *Only the operator releases it*, with a reason; no timer. A pull never fails for want of a
  reason ("no reason given"). A record that cannot be read stops the desk (fail shut).
- *The drill is real, on a scratch desk at the pretend broker* (options: pull the real switch; a
  checklist): it stops no real trading, cannot be ticked without being run, and fails by name.
  "Monthly" is 31 days. The pretend broker gains one fault, an order left working.
- *Branch:* finished on `lane/money-1113-203647-s1` as asked; nothing pushed to `lane/money-1113-212543-s1`.

### 2026-11-13 — the costs whole (money-costs, #101)

**Decided**, by the lane as the desk's mentor, under his ruling "always go with recommended".
- *Spread: 0.05% of a leg's value, assumed.* Options: nothing until measured; one flat assumed rate; a measured figure per line. Chosen the flat rate now, measurement asked for (R-MONEY-10): a result with no spread flatters every strategy (canon B4).
- *Slippage: 0.05% a leg, assumed.* Same options, same choice.
- *A leveraged line pays its leverage times as much.* Options: one rate; times leverage; per line. Chosen times leverage: 3LGO pays 0.15% a leg, 5QQQ 0.25%.
- *A stop's sale slips three times as far* (the spread is not multiplied). Options: as any sale; a multiple; modelled from each day's fall. Chosen three times: a stop sells into a fall.
- *Spread and slippage are taken off the profit, not counted in an order's cost.* Options: inside the fifth of capital; profit only. Chosen profit only: they are the fill being worse than the sizing price, not a bill; it keeps the numbers research has judged.
- *UK tax is part of an order's cost.* Options: profit only; also in the order's cost. Chosen both: it is cash leaving with the purchase.
- *The regulators' fees (SEC, FINRA) go in the commission line.* Options: a sixth line; with commission. Chosen with commission: scene 7 names five lines.
- *The FINRA fee is charged though on holiday to the end of 2026.* Options: nought until January; the published rate. Chosen the rate: a date is a special case; the error is a fraction of a penny, on the safe side.
- *The leg is a typed word* (`orders.Leg`, read in `orders.leg_of`). Options: a sign and a flag; three words. Chosen three words.

**Evidence.** Fourteen months: costs £161.54 → £338.78, profit £967.23 → £791.66. Blind review: no wrong money. 35 breaks, 34 caught, the missed one (UK tax left out of the total) now caught.

### 2026-11-13 — the three emergencies in numbers (money-emergencies, #108)

**Decided**, by the lane as the desk's mentor, under his ruling "always go with recommended". A changed number is one line of code and one of its test.
- *"The market".* Options: the S&P 500 in dollars at New York's close; the yardstick as the desk reads it (pounds, London's close). Chosen the yardstick (VUAG, AG-04); numbers set on VUSA (same index since 2012) and checked on VUAG. New York's numbers on the desk's series would cry black swan on a crash; the code refuses any other market reading.
- *A crash: 4% in a day or 12% below the month's high.* Measured on VUSA: 4%/10% 46 days, 7 episodes; 4%/12% 26 days, 6; 5%/12% 22, 3; 5%/15% 14, March 2020 only. Chosen 4%/12%: the six episodes anyone would name, none missed. It halts buying; sells nothing (his stop already says where to sell).
- *A black swan: 10% in a day or 30% below the month's high.* Options: just beyond the worst closes (8%/25%); round numbers beyond the worst readings within a day (8.7%/26.0%). Chosen the latter: the crash watch reads within the day, so 8% could have sold everything on 9 and 12 March 2020. It means cash, and only the operator lifts it.
- *An emergency: one line down 10% in a day, in its market's terms* (tied to `STOP_FALL`). Options 5%, 7%, 10%, 13%, 15%. Chosen 10%: about ten a year across twenty lines (5% would be about sixty from the US shares alone). The desk buys no more of that line; others carry on. Only the day's fall counts, not the month's.
- *When each ends:* only when a day ends clear of it; a reading within the day raises, never lifts.
- *A bar's close is read, never its low:* the archive's bad lows would each have been a black swan.
- *His other words:* a desk fault is the book not matching (EMG-06) and the kill switch (EMG-02); a volatility spike is a crash; a market halt has no price, so it is unread, never calm.
- *Unread is its own answer* (`Unread`, raised by name). Options: measure with whatever is given; refuse. Chosen refuse.
- *The definitions say what the desk "is to" do*, since nothing acts yet; the type is `Response`, not a second `Action`.

**Evidence.** Four blind reviews (the first found the numbers set on the wrong series); breaks 91 of 92 caught, the last then caught.

### 2026-11-14 — the day's record (money-record, #114 and #124)

**Decided**, by the lane as the desk's mentor, under his ruling "always go with recommended".
- *A day's profit is the book's gain, not only closed trades.* Options: round trips closed that day; change in worth plus dealing less costs. Chosen the second: a falling day is a losing day. They agree when the book is flat.
- *One rounding policy: to the penny, half to even, once, where published.* Everything before is exact.
- *The market's figure: the capital times the yardstick's move over the record's days.* Options: the same capital each day; the capital bought once and held. Chosen each day (like-for-like with the fixed capital). The column must not be added up as buy-and-hold (R-MONEY-14).
- *Each record opens from what the last closed on* (worth and count of fills kept in the record). Options: work it out again from files; keep it. Chosen keep: the first review showed two ways the first loses money in silence.
- *A record is never rewritten;* a late fill is in the next record.
- *A withheld day's money is published with the next plain number* rather than left out of every record.
- *A day is over when its record is made, or the ledger holds a later fill.* Options: ledger alone (as landed in #114); records alone (blind before the first record); either. Chosen either (#124): each sees what the other cannot.
- *A missing record does not hold the next day's orders.* Options: no order until every earlier session has its record; buys held, sales through; nothing held. Chosen nothing held: one late close must not stop rule sales.
- *A records file the desk cannot read stops the morning's orders;* an absent file (a new desk) trades. Chosen stop loudly.
- *A holding is valued at that very day's rate or the day has no record;* records begin at the ledger's first fill; a bar owed is an error unless the line is suspended.
- *Scene 6's last check reads "something was held on some day"*, and both books are compared every day.
- *The ledger writer keeps its private name* (`book._write`) so the paper lane's merged code stays green; asked of PAPER (R-MONEY-11).
- *#114 landed before its last mend's review reported* (#124 closed the finding); nothing but the pretend broker is on this path.

**Evidence.** Fourteen months: 310 days' profits add to £791.66, the 34 round trips'. #114: three blind reviews, 4 blocking findings mended, 27 breaks, 25 caught and the 2 missed then caught. #124: a review found an old day with a made record could be sent again (five buys, £11,602 on £10,000 in its run); closed, eight breaks all caught.

### 2026-11-14 — the rest of the money book noted (money-notes, #130)

- *The crash watch has its own module, `desk/watch.py`, and waits for the halts.* Options: (a) a new module that reads the bars and the emergency thresholds and raises a halt; (b) inside `desk/emergency.py`. Chosen (a): emergency is pure definitions and measurement, the watch runs every five minutes and acts, and "halts all buying" needs the typed halt first. It does not wait for the data lane (the five-minute bar type is in the store); his alert is the paper lane's messenger, the watch gives the words.
- *The golden run (money-golden) holds all the lane's files and runs alone, after the fills, limits and halts.* Options: (a) commit it now; (b) once what a fill costs and what the gate refuses have stopped moving. Chosen (b): each golden change needs his approval (canon B5), so committing early spends his attention on planned changes. Its numbers live in a file the lane owns (a unit test beside the day's).
- *Fills realistic waits for the money invariants,* so the change to what a fill is lands under the property tests.
- *Honest money and the whole story wait for the fills,* which move the profit lines they report. Neither waits for the golden run; if honest money lands after it, its interest moves the golden numbers once, with the explanation B5 asks for.
- *Boxes that share files but do not depend on each other* (small trades, time and gaps, the stranger) carry no `after`: the runner already keeps two sessions off the same files.

### 2026-11-14 — the money invariants (money-invariants, TST-04, #132)

- *Seeded with the standard library's random numbers, not a property-testing library.* Options: (a) `hypothesis` (a new dependency: his approval, and `requirements.txt` is outside the claim); (b) worlds from `random.Random(seed)`, as the lab's tests do. Chosen (b): no dependency, the same world for the same seed everywhere, a failing seed is its own reproduction.
- *"Equity is cash plus market value" is tested through the day's published record.* Options: (a) at the book alone, valuing holdings in the test: the first blind review proved the value cancels and the check cannot fail; (b) drive `day.publish` in every world and set its worth and profit against the broker's holdings at the test's own closes and rates; (c) leave it to a box that owns the day's tests. Chosen (b): the record is the only place the desk states its equity. The file is named for the book because the claim names it so.
- *The late-fill path is kept beside the record.* The record brings the ledger up to date first, so it never meets a late fill against the pretend broker; the test also counts each day's dealing on the ledger as it stood (`book.dealt`) and holds each fill counted once.
- *Costs shared between round trips are compared to 1e-27 of a pound, everything else exactly.* Sharing a split fill's costs by division is the one inexact step; the largest difference measured was 2.1e-27.
- *The guard proved (canon A7): 37 deliberate breaks, 36 caught,* two by no other money-path test (a sale closing the newest buy; a part-sold buy sent to the back of the queue). Not caught: a book-and-broker comparison that finds nothing, which breaks no invariant where the two always agree; the reconciliation tests catch it. Two blind reviews found three blocking issues, all mended: the market-value term cancelled, a cancelled order that later filled was invisible, a first send reaching the broker twice went unseen.
- Found, not fixed (product files outside the claim): no fault can reach a sale; the pretend broker never fills in two executions; an order's state is read from words, not typed.
- All of this is paper. His standing ruling of 13 November: "please always go with recommended to avoid waiting for me to attend".

### 2026-11-14 — SimCity, small (money-simcity, #134)

Decided by the MONEY lane as the desk's mentor, no one watching.

- *What a "part of the money path" is.* Options: a hand-kept list; every function; everything the six modules offer by name plus the broker's five faults. Chosen: the last. A hand list rots; private helpers are their callers' business. A rule's own arithmetic is not a part; "rules that never held a line" is reported beside the census.
- *Measured, not claimed.* Options: scenarios declare their cover; the profiler records what ran. Chosen: the profiler (about 17 seconds a night).
- *Which modules.* Six: strategy, orders, broker, book, day, kill. Not `emergency.py` until the crash watch is built.
- *One life, not several.* A fault on every line; each thing done to the desk waits for a plain day. Several lives cost about a minute each.
- *"One command" is a function,* run by the check on every change; a command-line entry would reach into `tests/`. The nightly run on his PC is the runner's.
- *The night's test sits with the unit tests,* so the scenes stay his seven.
- *Land RED and pin it.* Options: leave the limit of five untried; try it, say RED, pin the test to that one broken promise; mend the send path here (outside the box's files). Chosen: the second. The pin fails if any other promise breaks, or the moment the fault is mended.
- *A red night is kept; a night that cannot be lived is an error.* Nothing written when data is missing or the time is not UTC.
- *No exact money figures pinned,* so another lane's rightful change cannot turn this test red beyond its claim.
- Evidence: two blind reviews, each with a blocking finding mended; 27 deliberate breaks, 24 caught, 1 closed by a test, 1 dead name removed, 1 rightly green.
- Found, not fixed: six lines held when a working order fills late (box money-working); a cancelled stop never put back (money-restop).
- All of this is paper. His standing ruling of 13 November: "please always go with recommended to avoid waiting for me to attend".

### 2026-11-14 — a hundred seeded worlds (money-worlds, #150)
- What a world is. Options: (a) made-up random markets; (b) the saved data as it stands, only faults seeded; (c) the saved lines on their own days, each line's months dealt again by the world's number. Chosen (c): calendars, gaps and each day's shape stay real, and a real archive needs no new code.
- Each line's months in an order of its own (b), not one order for the world (a): the rehearsal lines all follow one shape, so (a) would put every line's buy on one morning. The cost: days when everything falls together are not rehearsed.
- Every world seeded; the saved data as it stands is no longer lived whole by SimCity (a special case for one input; the scenes live it).
- Faults drawn at the broker's door for each order, one in four (not one per line per life): a sale can now meet one.
- Things done to the desk take turns in an order each world deals, on one fit morning in eight (not a fixed order, nor a free draw that left one world in eight without one of the three).
- A stop cancelled by hand is put back the next morning seven times in eight. Never put back froze the desks 30% to 67% of days; always put back never tries the long freeze. 14% of days withheld.
- A world in which the desk refuses to go on is a RED night naming world, day and words (its ValueErrors only), not a dead night. This changes #134's ruling in one case: data the desk cannot price is now a RED record.
- The check lives world 0 of the fourteen months; the hundred are the nightly command's (a hundred would take two hours).
- The fourteen-month test allows the known six-lines fault and does not ask for it (SIX_HELD): three worlds in four break it, so any rightful change by another session would turn their check red. The limit is proved another way; a green night is held to green. The box that mends it removes the allowance.
- Prices are rounded to the penny by the desk's one rounding; simcity.csv gained "worlds" (none existed); tests grew 146 lines against 99, the guard has room.
- Ticks: money-worlds. Evidence: 53 deliberate breaks, 52 caught, one rightly not a promise.

### 2026-11-14 — halts (money-halts, #148)
- Where enforced. Options: (a) in the day's trading; (b) at the send path, the one door. Chosen (b): "no halt bypassed" (A-GATE); read again at the last moment, as the kill switch is.
- A halt stops buys only (his emergencies ruling, #108). It never expires (FIL-08: the old desk's halts were set and forgotten); only lift, with a reason, ends it.
- A halt cancels nothing at the broker; the kill switch does. Options: (a) cancel every working order (would cancel a rule's sale too); (b) a buys-only cancel (right, needs broker files); (c) state the limit now. Chosen (c) now, (b) with the crash watch.
- No well-made halt is refused (a safety act is not refused over a clock); a halt is known by its moment and reason, the same twice is kept once, lifting names the very halt.
- A halt marks every UTC day from called to lifted, both included, whatever the hour: errs toward not counting. A halted day keeps its profit figure (the money is real) and does not count.
- The verdict also reads what the send path did (a mis-dated lift could let a day count with six buys refused); the kill switch counts against the day too; a day whose orders were never sent does not count.
- The morning's list holds everything day.trade answered that did not fill whole, sales included, and the lines with no bar for the session before, named apart (a stale morning reading "0 blocked" is the old silent stop).
- Refusals at the paper account's door are filed under "the broker, or the desk's door to it".
- desk/halt.py borrows the price store's file writer (the send path reads halts, so the halt sits below the book); one public writer owed (R-PAPER-7, R-MONEY-11).
- Record.counts is stored when the record is made (SimCity's census would turn red for a new public function).
- Records built without the two new facts, and a row of ten columns kept by hand (#152), read as nothing known sent and cannot count. Options: (a) strict reader, close this change until PAPER mends; (b) read such rows as the record's own not-known state; (c) convert old-name files (none exist). Chosen (b) as a bridge, asked of PAPER (R-MONEY-20, 21); the reader's allowance and the defaults go together.
- records.csv changes shape with no conversion (no day's record exists outside a test). Who called a halt, who may lift it and a halt on one line are not recorded yet (crash watch).
- Ticks: money-halts. Evidence: 128 deliberate breaks, 125 caught, 3 closed.

### 2026-11-14 — a dead desk's working orders cancelled, not counted (money-working, #163)
- What to do with an order a dead desk left working. Options: (a) as the box worded it: every broker gains a question and the limit counts the answer; (b) the desk notes each order as it goes, and after a death has the broker cancel whatever is working before it sends; (c) land nothing and ask the paper lane first. Chosen (b): (a) cannot be green from this box's files (the paper adapter is the paper lane's, and added questions change conversations its tests hold byte for byte); (c) leaves the limit broken and R-MONEY-15 open for rounds. (b) asks nothing new of any broker and is the 13 November broker ruling (what is not filled is cancelled). Cost: that trade is given up for the day; its rule asks again tomorrow. After a crash the desk prefers flat and certain.
- The box is ticked though its second clause (a broker says which orders are working) is not built as worded: nothing is left working to list.
- Which endings leave the note. Options: (a) only a death; (b) every ending but the broker's last answer or its door's word that nothing went. Chosen (b): not knowing is treated as a death.
- The cancel comes at the start of every send (not only before a new order), so the leftover order's answer never reads "working" a moment before it is cancelled. While the kill switch is on the note waits: the pull has cancelled, and a refusal made with the switch on asks the broker nothing.
- SimCity's eleventh promise: no order is left working at a day's end. The check's one lived world moved from 0 to 1, the first that came to six lines, so the test fails without the mend. The sending-twice test was tightened, not loosened (a working order's answer changes to cancelled, no fill added).
- Evidence: hundred worlds GREEN (31,000 days, 1,195 deaths, 583 orders left working); 24 deliberate breaks, 20 caught at once, 4 survivors closed. Ticks: money-working.

### 2026-11-14 — the crash watch (money-watch, #172)
- His lift of a watch's halt. Options: (a) it stands until the market ends a day clear; (b) for that day only; (c) no memory: while the market still raises the halt, the watch calls it again and tells him. Built (a), narrowed three times; four reviews each found it buying into a fall or halting against his word. Chosen (c): errs toward the halt; he has no lift command yet. His recorded word against the market is owed.
- Any bar of the session raises a halt, not only the newest: a look can be missed or bars land together. A day's end is read at its last five-minute bar once the auction is over; if missing it lifts nothing and he is told once.
- A crash and a black swan are two halts, each on its own; the black swan's is his alone to lift. The watch lifts its own crash halt as of the day's end.
- Twenty minutes unheard means unread (options 10, 15, 20: three missed rounds and a fourth late); change once the keeper's delay is measured. A thin line is read at its last trade while its venue is heard.
- Blind (market unreadable) calls no halt: a stopped feed is far commoner than a crash, and a halted day does not count; he is told once an hour. One line's emergency parks nothing yet (the send path asks only for whole-desk halts; one ticker must not stop all trading).
- The watch runs inside the desk's step, so the halts' record keeps one writer. A halt called with no caller named is the operator's own (outside tests call it so).
- Evidence: five blind reviews (four failed, eleven findings closed); 82 of 89 breaks caught; twelve real sessions, 628 looks, no crash. Ticks: money-watch.

### 2026-11-14 — notes for the runner (money-notes, #176)
- The unnoted standing rule (a box adding a public function needs SimCity's files). Options: (a) leave it unnoted, so the runner treats it as whole-lane work; (b) note it as waiting on the operator, untrue; (c) put its files into each box it speaks of and give it a note placing it last. Chosen (c): true, and it frees the runner. It is now money-census, ticked when every other box is.
- SimCity's file has one line of room. Options: a box of its own to split it, or let the first box needing room split it. Chosen the second.

### 2026-11-14 — the RSI and the lower band made public (R-RUNGS-6, R-RUNGS-12, #185)
- Options: (a) two plain functions of numbers the rules already work, read by the rules; (b) whole public indicator classes; (c) public aliases of the private classes. Chosen (a): names exactly the two lines RUNGS could not reach, one code path, every private name RUNGS uses still works. (b) is the cleaner end state once RUNGS stops reaching the private parts. The band's width stays the fixed 2 deviations.
- Proof the rules read the names: the test puts another number at each name and sees the pinned trade vanish.

### 2026-11-14 — a lost stop is told the same day (money-restop, first step, #191)
- When the desk looks. Options: (a) a new read of the broker each morning; (b) the day record's existing reading at the day's end; (c) only when an order is refused. Chosen (b): (a) changes the paper conversation its tests pin; (c) says nothing on a quiet day. Cost: on the pretend desk a stop lost overnight is told at that day's end.
- The level is kept by the desk as each buy goes out (not recomputed, not read from a broker that lost it).
- Only lines the broker holds exactly as the book does, with fewer shares under a stop, are told: telling him to rest a stop for shares not held could sell short.
- Under the book's blocker ("the book is not the broker's"), the list's id the stop's own; a blocker of its own needs `desk/halt.py`. Evidence: 8 breaks caught; SimCity promises it.

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

### 2026-11-13 — the parked fifth's box closed on the rule as it stands (data-parked-fifth, #84)

- **Tick the box, or hold it for the misjudgements.** Options: (a) hold it open until WWH, SHC and the three windfalls are settled from a second source: none exists, so the box would block the research home behind it for good; (b) tune the rule until they come out right: every signal tried (range, a round ratio, a gap in sessions) also catches real crashes (PCG 0.476, ALNY 0.515), and raising 2.5 to catch WWH (2.51) leaves FANG's real crash (2.76) a whisker away, on a number chosen looking at this one list; (c) tick it. Chosen (c): every known error is a false loss or an unread stretch, which makes a strategy look worse, never better, and each is named in the history.
- **A crash wholly won back overnight stays cut at the way back.** Options: (a) read through a one-day excursion that returns (on the one real case, ROSE, that reads three false moves instead of one, the day "returned to" being a stale quote); (b) leave it. Chosen (b).
- **A move made within a day stays named on two days.** Naming it once would be truer for a count, but tests outside the box hold the behaviour and the rungs' request counts trades held through a named day, not days. Left as is.
- **Tests not landed over the size guard.** Options: (a) ask him to loosen the guard, for two hair's-breadth cases; (b) grow the product to make room, which is forbidden in spirit; (c) run them from outside the repository and record the output. Chosen (c): 14 deliberate breaks, 12 caught by the existing tests.

### 2026-11-13 — the ISA twins, the flags and the yardstick (data-isa-twins, first step, #85)

- **Red on the tests-no-bigger-than-the-product guard.** Options: (a) tighten the claimed tests keeping every assertion; (b) add product lines; (c) ask for the guard to be loosened; (d) close the pull request. Chosen (a): (b) grows code to get round a guard, (c) is not needed, (d) throws away finished work.
- **SPY and QQQ cannot leave in this change.** Options: (a) add nothing until other lanes' tests change; (b) add the twins and flags, remove GLD, keep SPY and QQQ flagged as not holdable and ask GRID and RUNGS to stop naming them; (c) edit the other lanes' tests (refused by the claim). Chosen (b); the master holds 22 lines for a while, held by a test that names the two as leaving.
- **IDTL is priced in dollars.** The archive and the exchange quote it in dollars; the pound-priced IDTG is a different, currency-hedged product. Chosen: IDTL as he ruled, in dollars, so a purchase carries the currency cost like a US line.
- **The yardstick is one line, VUAG.** Options: VUAG; VUSA (same index, pays out its dividends); one yardstick per venue. Chosen VUAG: one capital number in pounds, one yardstick in pounds, and its dividends stay in its price, so holding it is the whole of what the market earned (AG-04).
- **What the flags say.** Options: one flag "ISA-ready"; two facts. Chosen two: IB1T shows why (retail yes, ISA no, crypto notes shut to new purchases in an ISA from 6 April 2026).
- **A line nobody has recorded.** Options: default no; default unrecorded; no default. Chosen unrecorded (None): no would call a thousand research tickers unholdable, falsely; no default would break files outside the claim.
- **The constructor's suspension check was reshaped** (same behaviour, same test) to stay inside the lint's complexity limit rather than touch the limit.

### 2026-11-13 — trading hours in the one calendar (data-hours, #87)

- **Summer time by rule, in the calendar.** Options: (a) Python's time-zone database (this PC lacks it; needs `tzdata`, a file outside the claim); (b) each country's rule in the one calendar. Chosen (b): `desk/` stays standard library only, both sides of every change tested.
- **A venue is open from its open to its closing auction, both ends included.** Options: continuous trading only; to the auction. Chosen the second: a five-minute bar is whole only at its end, so the keeper's round at 16:30 and 16:35 London (16:00 New York) collects the day's last bar and the official close.
- **A shut day asked for its hours is refused; a shut moment asked "is it open" answers nothing.** The first is the caller's mistake; the second is the keeper's ordinary question.
- **London's half-days by rule** (last session before Christmas Day, last of the year), not by 24 and 31 December: on a weekend London closes the Friday before. New York has no such carry.
- **Closing auctions as each exchange publishes:** New York's at the bell, London's five minutes after continuous trading ends.

### 2026-11-13 — the one fast store (data-fast-store, #89)

- **One table for both spans, a line keyed by venue and symbol.** Options: a table per line; one table keyed by venue, symbol, span and start. Chosen the second: one model, and thirteen symbols are two companies by venue.
- **Prices as exact text.** Options: floating point; whole ticks (needs every tick size); the decimal's own text. Chosen the text (canon B4), the history benchmark met with room.
- **A daily history is replaced whole; five-minute bars gather.** The archive restates the past for splits and a dropped bad day must go; five-minute bars are forgotten by the archive after sixty days, so nothing is cleared and a bar given again replaces that one bar.
- **A second writer waits up to five seconds, then is refused.** First built as refuse-at-once; review showed the only writer refused when readers merely opened and closed the file. Chosen SQLite's own bounded wait, not a retry in the desk's code.
- **Each round forced to disk (FULL).** NORMAL is faster but a power cut can lose rounds; the benchmark is met eighty times over with FULL.
- **A refused line leaves its round whole** (one bad ticker must not stop all trading); a round SQLite itself drops lands nothing.
- **A store or line never written is an error, not an empty answer** (failure pattern 10).
- **The fastest of five runs is the benchmark's measure,** because one run fails by chance on a busy machine; the numbers live in the test.
- **Evidence (A7):** 107 deliberate breaks over three versions; survivors listed in the pull request, each unobservable in a unit test. Two blind reviews: seven blocking points, all mended.

### 2026-11-13 — the survivors' lists (data-members, first part, #96)

- **Where past members come from.** Options: (a) a paid history of index members (spending is the operator's); (b) the index owners' notices change by change (hundreds of documents); (c) Wikipedia's dated change tables, checked by walking today's list back through them. Chosen (c): free, the walk reaches exactly 500 and 100 in 2010; unofficial, and the module says so. If survivorship ever decides a promotion, a paid history is the question for him then.
- **Where the record lives.** A file outside the repository, or the module's text. Chosen the text (about 100 lines, versioned with the code), with a golden fingerprint so no change or date is altered unnoticed.
- **How a past member is named.** A ticker is not a company (Q was Qwest, is Qnity). Options: match by ticker; carry every ticker change as an event; name each company by its last ticker on the list, and a leaver whose ticker a later member carried with its year of leaving (Q.2011, CB.2016, JCI.2016, ...). Chosen the last: no stranger's bars read as a leaver's, one mechanism.
- **Hand corrections to the source,** each because the walk back contradicted today's list: ticker changes written as a leaver and a joiner made one company (Facebook to META and twenty more); GOOG for GOOGL in April 2014; two mergers followed by the surviving company (ACE took CB, Tyco took JCI; which company's prices the archive keeps under CB and JCI before the mergers is unconfirmed); four early-2010 S&P changes added from news of the day (NRG, Berkshire, Discovery, ONEOK); second share classes of Comcast, Discovery and Liberty written as joining (22 December 2014, inferred, not sourced).
- **Days outside the record** (before 1 January 2010, after 13 November 2026) are refused, never guessed.
- **The year-by-year counts and the record's fingerprint are golden numbers;** they change only by a deliberate, explained edit.

### 2026-11-13 — five-minute bars saved for good (data-five-minute, #97)

- **Where "everything older" lives.** Options: one file with the week read from on top of the older bars; a second archive file that older bars move into. Chosen one file: 5.2 million bars still read a week in 5 ms, and moving bars between two files is the one place a bar could be lost.
- **How much is asked each evening.** The day's bars only, or all 59 days the archive keeps. Chosen all 59: 22 requests either way, a missed evening heals itself, a corrected bar is picked up.
- **A bar the archive restates takes its place if it passes the checks,** so the evening's answer can correct a bar saved while it was forming; a restatement in a wrong unit never gets in.
- **Checks not carried over from daily bars:** a missing bar and a repeated price are no fault (thin lines trade in few spans; 345 of 3LGO's bars were flat); a line late or missing its newest bar is the keeper's to judge.
- **A big move is kept and listed, not dropped,** as the daily store does: the crash watch needs those bars.
- **A wrong unit is judged against the middle price** of the bars held for those days (of the answer itself the first time). Simpler than neighbour rules and not dragged along by a run of bad bars; on the very first save an answer more than half wrong would be judged the wrong way round, and every such bar is listed.
- **The archive's "price of the moment" and a forming bar are not bars yet;** the client leaves them out so a fault list means something.
- **The store's file is `KESTREL2_DATA/bars.db`,** chosen now so the first night's bars are saved where the keeper will look.
- **`archive.gather` no longer has a default question;** every caller already named one.
- **Identical repeats of one bar are kept once without a fault,** or they would repeat for 59 evenings.

### 2026-11-14 — the old desk's five-minute bars as a head start (data-headstart, first step, #175)

- **Which objective first.** Options: (a) the keeper (R-RUNNER-7), as the protocol says; (b) the head start, as the runner's first instruction said. Chose (b): the later, more specific word, resting on his ruling "always go with recommended". The keeper is next.
- **Five-minute before daily.** The archive forgets five-minute bars after sixty days, so the old desk's are the only copy; daily bars can be fetched again any day.
- **What vouches for an old bar.** Options: (a) the old desk's cleaning; (b) the store's checks alone; (c) also that the bar lies inside its day's fresh daily bar (within the 3% the store allows). Chose (c): (b) cannot see a whole history in a wrong unit where nothing fresh is held.
- **London pence.** Options: (a) refuse them (loses seven months of six lines); (b) read a bar as pence only when it fits the day's fresh range as pence and not as pounds; (c) try any factor. Chose (b): the readings are a hundredfold apart; no other factor is tried, so bars a hundred times too small are refused.
- **A line's old bars need proof of their clock.** Options: (a) the daily range alone; (b) also bars already held for some of the same moments, at least half agreeing. Chose (b): the matrices were on Warsaw's clock (1 of 2,184 SPY bars agreed as stamped, 2,170 two hours earlier); aligned sources agreed on 65% to 99.4%, misaligned under 1%. Not tuned further.
- **"Differs"** means any of the four prices further apart than 0.01%; volumes are not compared (vendors count different venues). Bars already held are recorded as the archive's.
- **The parquet stores are not read.** They need a parquet reader, a new dependency (his to approve). Options: (a) add one to `lab/`; (b) convert once outside the repository; (c) leave them. Chose (c): the matrices carry Stooq's bars, IBKR's folder holds 24 tickers.
- **The real store is not changed until this lands and `market.db` exists** (R-RUNNER-10): the store gains a column, so older code could not write to it; the command is one line and safe to repeat.
- **A round that names no source.** Options: (a) ask MONEY to name the archive in its test and wait; (b) a round is the archive's unless an old store is named. Chose (b); the head start names its source every time. R-DATA-13 lets the default go later.
- **data-isa-twins waits** until GRID and RUNGS stop naming SPY and QQQ in their tests (the runner's ruling taken on his standing one); the old stores' consolidation comes first (R-RUNNER-10), nothing to E:, no original deleted.
- **Evidence (A7):** 36 deliberate breaks on scratch copies, 35 caught; the one missed (the order the two old stores are read in) caught since. Blind review: one blocking fault (a read-only open leaves two side files), fixed and tested. `manifest.toml` gains one line registering `lab/headstart.py`; nothing loosened.

### 2026-11-14 — the data lane's open boxes in working order (#180)

- **The keeper before the ISA twins.** Options: (a) twins first, as the book's wording says; (b) the keeper first. Chose (b): the twins wait on other lanes, the keeper is the runner's blocking request and his "paramount" ruling.
- **The head start second:** his ask says "now", and five-minute bars older than sixty days exist nowhere else.
- **The single-line findings (2MU, 5QQQ, SGLN, 3LGO) and the three store findings are chained one after another:** they change the same two files (`desk/lines.py`, `desk/store.py`), so only one could run at a time anyway.
- **data-consolidated carries no "waits: operator".** Options: (a) hold the whole box for his yes; (b) hand it out and let its session stop at the deletion. Chose (b): only deleting the originals is his.
- **data-tiers names a new module, `desk/tiers.py`:** which tier a name is in is one concept and needs one home; the building session may find a better name.
- **Nine boxes left un-noted** rather than guessed at: a note naming the wrong files makes a session fail its check.

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

### 2026-11-14 — a buy goes with its stop; the line settled after any order (paper-adapter, paper-stops, #123)

Decided by the PAPER lane as the desk's mentor, no one watching.

- *How a buy and its stop go together.* Options: (a) send the stop after the buy fills: a second or two with no stop, and a
  dead desk leaves shares unprotected; (b) attach the stop to the buy so the broker holds both, then settle; (c) rest the
  stop first: impossible without risking a short sale. Chosen: (b); if the stop's half is refused the buy never reaches the market.
- *Which shares the stop is for, and on what evidence.* Options: (a) the desk's own sum, checked against the account;
  (b) the account's shares alone; (c) size from the account, and act only when the account moved by exactly the order's
  fills and "filled" is borne out by fills. Chosen: (c), after the blind review showed five ways the sum is silently wrong.
  When the three disagree nothing is changed and an error is raised.
- *A sale: take shares off the stop before or after.* Chosen: after, by what happened; one mechanism for buys and sales.
  For a moment the stop is for more shares than held (recorded, not fixed).
- *Replace a stop, never change it in place* (changing a stop attached to a buy is unproven); new first, then cancel the old,
  so a line is never under none. A line whose stops are unsettled is refused, buy and sale alike. A stop already right is
  kept whatever its name; a stop the broker is not holding counts as none.
- *The broker's notice 202 (order cancelled) is news, not a fault, in every reading.* This changes one line of #110's test:
  cancelling a buy makes the broker cancel its stop and say so. The comparison of book with broker still names any line left bare.
- *A stop with no price at the broker* stops the buy with an error before anything is dialled. The stop rests until
  cancelled (GTC), plainest kind. A stop that ends some other way while being cancelled is an error unless the shares are as read.
- *Both boxes ticked.* No test order was sent to the real Gateway: one wrong field could make a real order on a shared account.
- The tests' pretend Gateway moved into the door's test file (no test changed): the placing tests were at the 400-line cap.
- Evidence: tests seen failing first; blind review, one blocking finding fixed; 60 + 25 + 31 deliberate breaks, 2 that cannot differ.

### 2026-11-14 — the paper book's next boxes ordered for the runner (#128)

Decided by the PAPER lane as the desk's mentor, no one watching.

- *Messages and the unattended day ahead of conformance.* Options: conformance next; boxes needing no market first. Chosen:
  the latter: it is a weekend, and conformance holds every file so would stall the lane until Monday. The code already
  refuses any order without a drilled kill switch and clean check.
- *Supervision after conformance:* its box needs seven days without an operator action and would hold the first paper trades.
- *Conformance keeps `files: *`:* nobody has seen where real results are recorded; a missed file would stop the session.
- New modules named before they exist: `desk/messenger.py`, `desk/running.py`, `desk/supervisor.py`. paper-running also holds
  `desk/placing.py` for R-MONEY-8 and waits for paper-messages so there is one messenger.

### 2026-11-14 — the desk's one voice (#142)

Decided by the PAPER lane as the desk's mentor, no one watching.

- *Alarm on silence:* the desk alarming itself (a dead desk cannot); only a human rule; a watch outside the desk reading the delivery record. Chosen the watch, with the human rule beside it.
- *Hours:* morning 08:00 (05:40 was in his night), owed by 08:30; evening 21:05, owed by 21:30 (21:00 sat on New York's bell on 465 of 502 sessions). Nothing sent from 22:00; only the alarm goes at any hour.
- *The record is SQLite,* not a CSV: two writers by design, and two processes drove the CSV unreadable within six writes.
- *Asked on the record before the door; told twice rather than never.* A lost Telegram answer means a resend.
- *Over-long messages* are cut at the door and kept whole on the record. *The key* comes from `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`; giving it to the desk is his alone.
- *The morning message claims only what it asked* (Gateway, the day's check, kill switch and drill). The merge line and runner alerts stay outside until paper-cards.
- Evidence: two blind reviews, three blocking findings fixed; 518 deliberate breaks, 473 caught as driven, gaps closed and driven again.

### 2026-11-14 — the unattended desk (#152)

Decided by the PAPER lane as the desk's mentor, no one watching.

- *A step, not a loop:* a restart then needs no special path; what is done is known from the desk's records (and `running.csv`).
- *Recovery runs whenever the check names something* (not at start, not every step). The stop kept is the newest whose buy really bought, for the shares held, only where they are the book's; read before the dead desk's orders are cancelled. It waits while the kill switch is on or undrilled.
- *The check comes before a record too* (blocking finding). *A round is made once a day,* all answers told to him; an unclean check keeps it owed. Orders go whenever clear, however late (cut-off asked of MONEY).
- *A line with no bar of the session before is left out and named,* not the whole round refused.
- *Record hour:* five minutes after the last closing auction. *His hours:* nothing before 08:00 or from 22:00; a Gateway failure goes at any hour, once per day.
- *The adapter itself refuses an order not dated the session before* (R-MONEY-8), by the venue's calendar.
- Evidence: tests seen failing first; two blind reviews (2 blocking fixed); 78 deliberate breaks, 78 caught; dried read-only at the real Gateway.

### 2026-11-14 — the daily kill-switch drill (#155)

Decided by the PAPER lane as the desk's mentor, no one watching.

- *When:* only when the last drill is over 31 days old; once each day before that day's first work; at each process start. Chosen daily: a step has no start, and a month-old drill says nothing of today's code. The 31-day refusal stays in the adapter as the floor.
- *Where:* after the ledger, before the check (the check may put right with orders). *A failed drill stops everything but the ledger* and the step fails; told once in his words, wrapped from the money lane's error.
- *Any day the desk works,* on the UTC day. No message for a drill that passed.
- Evidence: tests seen failing first; one blind review, nothing blocking; 31 deliberate breaks, all caught; dried at the real paper Gateway with the switch on.

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

### 2026-11-13 — a key per rung (grid-key, #88)

**Decided.** Each rung (a module of `lab/` that builds on the cell) has a code version of its own, covering every file it reaches; the first rung reaches the cost model (`desk/orders.py`), so a change of costs moves every verdict's key and leaves the trades' keys alone.
- *One key or a key per rung?* (a) fold the cost model and every rung's code into the cell's one key; (b) a key per rung. Chosen (b): under (a) a one-line commission change re-runs every trade search, hours of work, though the days a rule bought and sold cannot depend on costs. Under (b) a change re-runs exactly what it touches.
- *The cost model's version.* A number someone must raise, or the code's own text. Chosen the text: a number kept by hand is a rule in prose.
- *Chained, not swapped.* The rung's key hashes the record's code with the rung's, so trades made by older code never pass for this code's under a verdict's key.
- *When read.* First asked, or at load. Chosen at load, every rung at once: the first showed a cost model edited after the process loaded the old one.
- *What is a rung.* A `lab/` module reaching the cell through its imports; any other name is refused, no list kept by hand.

**Evidence.** Test seen failing first; 27 deliberate breaks, 27 caught; a blind review's one blocking finding fixed. Open: nothing stamps a verdict with the key yet (R-GRID-3).

### 2026-11-13 — the auto-tune: finish the kept work (grid-tune, #94)

**Decided.**
- *Which branch.* The kept branch, or a fresh one. Chosen the kept branch, as the restore instruction says, keeping the earlier three commits.
- *Finish or delete.* Chosen finish: complete, green with main, review found no blocker.
- *The review's minor findings.* Fix now or carry to grid-pass. Chosen carry: none is wrong behaviour today and the change sat at 296 of 300 lines allowed.
- *UK clock.* `tune.spare` works out summer time itself because the calendar keeps its rule private. Keep and ask DATA for a public one (R-GRID-4), or wait. Chosen keep: proven on both sides of both hours.

**Evidence.** 18 deliberate breaks, 18 caught; proven with the real Windows ceiling (a gigabyte cell under 400 MB was refused and the rest finished); blind review found nothing blocking.

### 2026-11-13 — the grid's first pass (grid-pass, #102)

**Decided.**
- *What "every setting" means.* (a) whatever the desk's engine can make (`strategy.STRATEGIES`, five today); (b) settings invented in the grid. Chosen (a): the grid is trusted only where it matches the desk's engine (canon B2); settings are MONEY's (R-GRID-1).
- *The unit handed to a worker.* A cell with a shared journal, or a ticker with a journal each. Chosen the ticker: prices read once instead of five times and two workers never write one journal.
- *Which tickers.* Only the 864 clean ones, or all 1,065 through research's own reading. Chosen all 1,065: DATA built that reading for it (R-DATA-7), and a parked ticker can still be studied.
- *Window.* The whole history, one window per cell; folds are RUNGS'.
- *The research store.* A scratch folder rebuilt from cached answers, or a permanent home now. Chosen scratch: the home is DATA's box (R-GRID-5) and kept cells do not depend on it.
- *A ticker listed twice is refused*, not quietly counted once: a repeat is a mistake in the list.

**Evidence.** The pass run for real: 5,325 cells run and kept in 200 s, none failed; a second pass ran none, in 45 s. 14 deliberate breaks, all caught after the test was strengthened; a blind review's one blocking finding fixed.

### 2026-11-14 — the grid's week: who starts it, how it runs, what breaks it (grid-week, #111)

**Decided.** By the GRID lane as the desk's mentor, no one watching.
- *Who starts the seven-day run.* This session, now, detached, from a pinned copy of the code, or a command left for the operator. Chosen now: the box cannot close for seven days, so each hour unstarted is an hour later; paper research only, below-normal priority under the memory ceiling, one process to end. His ruling: always go with recommended.
- *Ticks: none.* Tick when the service runs, or when the log shows seven days. Chosen the log: "runs seven days" is a measurement nobody has seen. Recommended to the scribe: let grid-declared start now, as it waited on the shared file, not the week.
- *Each pass in a fresh process*, not one long-lived process: five lanes change code day and night, and a crash or leak should cost one pass, not the week.
- *A pass every hour*, not back to back or daily: prices change daily and code a few times a day; hourly picks changes up and leaves the PC to the lanes.
- *What breaks "without stopping".* A failed pass, a pass holding no cell, a gap over an hour. Chosen to break on a failed pass: a service alive and producing nothing is not the grid running. One dead ticker does not break it.
- *The window ends today*, so each midnight every cell is new; the cost is growth of results (Found, not fixed).
- *A failed cell is written once*, only where the outcome differs from its last line; a cell's last line is its outcome now.
- *No time limit on a pass*: any number is a guess; a hung pass writes no line, so the log shows the stop.

**Evidence.** 36 deliberate breaks over two rounds: 30 caught at first, 4 after strengthening, 1 changes nothing, 1 left uncaught (named). Two blind reviews; two blocking defects fixed. Real run: 5,325 cells in 3 min 58 s; a short week of four passes read 17 min 50 s.

### 2026-11-14 — what "seven days" is measured to (grid-week, #118)

**Decided.** By the GRID lane as the desk's mentor, no one watching.
- *The measure.* (a) loosen it, counting to the last pass's start plus an hour; (b) have someone start one more pass by hand on 20 November; (c) the week runs until a pass has ended its whole length after the first began. Chosen (c): the measure is honest; a proof needing a person at the right hour is no proof for a desk no one watches.
- *Restart the running week now.* Chosen now, between two passes: the gap was ten minutes, inside the hour allowed, so the count carried on. His ruling: always go with recommended.
- *The earlier short passes count*, from 22:45 UTC on 13 November, as the rule reads; either reading passes seven days, the run going to 21 November 00:44 UTC.
- *Ticks: none*, as in #111.

**Evidence.** A clean week read 6 days 23 hours before the fix (seen failing first), exactly seven after. 10 deliberate breaks: 9 caught, the tenth after one line strengthened. One blocking review finding fixed.

### 2026-11-14 — a limit on a pass of the week (grid-week, #125)

**Decided.** By the GRID lane as the desk's mentor, no one watching.
- *A limit, and its length.* #111 chose none. Options: (a) none; (b) a few hours; (c) 48 hours. Chosen (c): the desk already requires a full sweep to fit a weekend (LAD-10), so a longer pass has failed that whatever the week does; a hung pass was the one failure the week could not survive alone. A short limit refused for #111's reason. Cost: a hang costs up to two days.
- *The running week stays on its pinned code.* Options: (a) restart it between passes as #118 did; (b) leave it. Chosen (b): a hang breaks the count either way, so the change cannot save this run; a restart risks a clean count.
- *The busy flag stays the pass's own.* Options: (a) the week writes "not busy" after ending a pass; (b) the next pass writes its own. Chosen (b): a second writer could end the week on a refused write and could say "not busy" over another pass.
- *A hung pass is a failed pass in the log*, so it breaks the unbroken time (#111's rule).
- *Ticks: none*, as #111 and #118.

**Evidence.** A real pass ended at a 20 s limit (error at 20.0 s, no worker left, lock free); the next pass ran whole (5,325 cells, 115 kept). 11 deliberate breaks, 9 caught; uncaught: the limit multiplied, and the count read from a successful pass's file (the real pass is the evidence). Blind review: nothing blocking; pipes replaced by files so a leftover worker cannot hold the week.

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

### 2026-11-13 — the paper account check asks the desk's one comparison (R-MONEY-4, #75)

**Decided**, by the lane as the desk's mentor (no one watching), when moving `paper.differences`
onto `book.differences`. The door keeps what is its alone: paper accounts only, a holding's
name, and the orders resting at the broker.

- *The name a holding is compared under.* Options: its symbol, kind and currency in one phrase;
  or the broker's own number for the line. Chosen: the phrase, so the same symbol in another
  currency or as another kind of product is never the book's line. The broker's number needs
  the listings read in the same check, a second conversation that is the adapter's to arrange.
- *Stricter in two cases, on purpose.* Two entries each exactly the book's shares, and an entry
  that matches beside another with shares, are both named now. Options: keep the door's own rule
  to stay as lenient as before; or take the one rule whole. Chosen: the one rule whole. A line
  with shares in two entries is never the book's one line, and a check that sends orders only
  when clean should err towards naming.
- *The sentence.* Options: leave "the broker holds 25, the desk's book 25", which reads as no
  difference; add a line about the entries; or say it in each sentence. Chosen: each sentence
  about a name given more than once says "holds 25 in one of 2 entries", counting every entry,
  empty ones too.
- *One word each.* A book's "BRK B" beside a broker's "BRK" of kind "B STK" came back clean
  when a name was one phrase. Options: hand the rule the three parts apart (the money lane's);
  or make such a holding impossible. Chosen: a holding cannot be made unless its kind and
  currency are each one word of letters and digits and its shares a finite number. No real kind
  or currency is refused (23 kinds and 26 currencies tried, from memory, not the broker's manual).
- *The unfinished run's document lines.* Options: keep its edits on the branch (the claim guard
  would refuse them); or state them in the pull request. Chosen: the pull request; the scribe
  writes the documents. Its shortening of an older decision entry was dropped.
- *Two breaks left surviving.* A kind or currency of letters only instead of letters and digits,
  and the book's shares made positive: neither can change a result for any kind, currency or book
  that exists. Options: add cases; or leave them. Chosen: leave them.

**Evidence.** The whole check green three times. The real account read at 19:51 UK, read-only:
seventeen lines at no shares, no order resting, nothing named. A blind review compared old and
new rules on 1,651,663 accounts: no false clean, no difference lost, every sentence true; the old
rule's 496 false cleans are the only new sentences. Thirty deliberate breaks in a copy outside
the repository with Python's cache off: twenty-eight caught, the two above left.

### 2026-11-13 — the fills and orders the paper broker reports (paper-reports, #86)

**Decided**, by the lane as the desk's mentor (no one watching), for `desk/reports.py`, read-only:
only questions are sent, nothing is placed.

- *Whose is whose.* Options: the desk's client id alone; the order's reference alone; both.
  Chosen: both. Another program could copy a reference, and the desk's own client with no
  reference of the desk's is something the desk cannot explain; either is kept apart and named
  by the daily check, never taken as the desk's.
- *A fill's day.* The gateway tells each fill's time on a clock it names (London "MET", New York
  "US/Eastern"; 14 and 7 real fills seen). Options: turn every time into UTC; or keep it as told
  with its clock's name, taking only the session's day and the order within a line. Chosen: as
  told. Turning the gateway's clock names into UTC needs a table of time zones the desk does not
  carry. A desk fill on any clock but its venue's stops the reading. This departs from the canon's
  "UTC inside" for this one value; to revisit if a time of day is ever needed.
- *Twice, or corrected.* Options: stop for any fill on the account given twice; or only the
  desk's own. Chosen: the desk's own. Others' fills are theirs to explain; the desk's own go to
  its ledger, where a fill counted twice is a wrong position.
- *What counts as a resting stop.* Options: any stop to sell the broker lists as open; or only
  one it says it is holding ("PreSubmitted" or "Submitted"), for the shares left. Chosen: the
  second. The broker lists refused and part-done orders as open too.
- *An order with no state told.* Options: read it with no state; or stop. Chosen: stop, naming
  the broker's id for it. An order is built once, with its state, when the reading is whole
  (options: leave it, every path failed safe; or build once). Chosen: once, so a missing fact
  cannot be mistaken for a value.
- *An order told twice is left listed twice.* Options: keep one per broker's id; stop the
  reading; or leave it. Chosen: leave it until a real order has been seen. A new order may briefly
  carry no id of the broker's, so keeping one per id could hide a real order, the dangerous
  direction; listed twice is a false alarm on the safe side.
- *The tests tightened, none dropped.* The rule that unit tests never outgrow the product turned
  the check red (244 test lines for 228 of product, two lines of room). Options: ask the operator
  to loosen it (his alone, not needed); drop cases (never); or write the same cases in fewer
  lines. Chosen: fewer lines (222 for 228); every case kept.

**Evidence.** The whole check green four times. The real gateway at 20:40 and 21:05 UK (port
4002, client 222), read-only: 21 fills, none the desk's; no order open; twenty of twenty lines
listed; nothing named against the empty book. A blind review: nothing blocking; it checked field
places against the published client (from memory, about nine in ten sure) and that nothing sent
can place or cancel an order; its two test gaps closed. Deliberate breaks outside the repository,
cache off: twenty-nine on the restored work and twenty on the final code, all caught, plus one
that cannot change a result. Not witnessed: the unfinished run's tests failing first.

### 2026-11-13 — the folds rung (rungs-folds, #79)

**Decided**, by the lane as the desk's mentor. Options and choices:
- *What "in-sample" means for a frozen rule with no settings.* (a) plain consecutive folds;
  (b) walk-forward, each fold beside all the history before it. Chose (b): it is what a
  chooser would have known the day the fold began, and it shows an edge decaying.
- *What the verdict is judged on.* (a) worst fold among all parts; (b) worst out-of-sample
  fold, in-sample shown beside it. Chose (b): in-sample is where a choice is made, never proof.
- *The bar per fold.* (a) a looser bar; (b) the first rung whole. Chose (b): one rule, one
  home. A thin fold reads as a fail until "failing fairly" makes it "not enough evidence".
- *Trades across a boundary.* (a) to the fold it was bought in; (b) to neither. Chose (b):
  otherwise an in-sample result would lean on out-of-sample prices.
- *Luck trials.* The out-of-sample verdicts only: they are what a winner is picked on.
- *Number of folds* is the caller's; fewer bars than parts is refused.

### 2026-11-13 — the register of trials (rungs-trials, #91)

**Decided**, by the lane as the desk's mentor.
- *What makes two trials the same.* (a) the cell alone; (b) the cell with code and data
  versions; (c) a made-up name. Chose (a), other candidates entered under a telling name:
  with the code version every unrelated commit would double the count; with the data version
  a mended bar would. Cost: a rule changed under its old name is not seen (written in STATUS).
- *When a trial is counted.* (a) when its verdict arrives; (b) before it is run. Chose (b): a
  failed cell or dropped candidate leaves no verdict, and the count must not rely on memory.
- *One count or one per question.* Chose per question, each opened on purpose once, other
  wordings refused: one count would charge a London question for New York trials; free
  rewording is the restart the box forbids.
- *A missing register.* (a) begin empty; (b) refuse, with a separate door to start one
  on purpose. Chose (b): a wrong path must fail loudly, not count from nothing.
- The same trial entered twice counts once; a verdict not in the register, or a trial judged
  twice in one set, is refused; the trial's name is the register's own wording, apart from
  how a cell prints, so a printing change cannot rename counted trials.

### 2026-11-13 — the luck test fixed before any result (rungs-deflated, #98)

**Decided**, by the lane as the desk's mentor.
- *What the Sharpe is measured on.* (a) daily account values; (b) the trades. Chose (b): the
  first rung's own gains, so the rungs cannot disagree about evidence.
- *The spread setting luck's bar.* (a) the spread of the batch's Sharpes (the paper's own);
  (b) one over the trades less one, what no edge gives. Built (a) first; review showed the
  same winner failing beside noise (0.43) and passing beside its twin (0.9998). Chose (b):
  the bar depends on two counts only, so no result can move it.
- *The bands.* 0.90 and 0.50, the book's own: pass, fail, and doubt between (two bands, three
  answers).
- *The daily Sharpe above 2.* Worked as a yearly Sharpe from the trades (a verdict holds no
  daily accounts). A flag gives doubt, not a note (nobody reads it) and not a fail (the cause
  is usually a fault in the test).
- *The one rule.* (a) the worst of the named rungs; (b) a score. Chose (a), refusing any set
  of answers that is not exactly the named rungs; later rungs join by being named in the list.
- The luck rung stays beside the deflated Sharpe. A trial under two trades fails.
- Guards driven: 6 contract tests seen failing first; 47 deliberate breaks, 43 caught.

### 2026-11-13 — the Gateway's own week known before any order (paper-gateway, #100)

Decided by the PAPER lane as the desk's mentor, no one watching, under his ruling "always go with recommended".

- *The daily restart.* Options: any silence is an alarm (he is woken at 03:00 nightly); quiet retries inside every
  reading; or know the restart's time. Chosen: know it. The Gateway's logs hold sixteen restarts, all at 03:00 UK, all back
  within seconds. 02:55 to 03:15 is "restarting" whatever it would answer, and it is not dialled.
- *Which silence is his.* Options: all failures his; only a closed port; split by what came back. Chosen: split. Nothing
  came back (port closed, 15 seconds silent) is his login, told at any hour on his ruling that a Gateway login goes at once;
  something came back but not "ready" is unwell and not his; anything else is raised as a fault.
- *True only when ready.* `known(now)` is true only for a ready Gateway, so no way of asking can send into one that is not.
- *The weekly reminder.* Options: Saturday evening (spent by the weekend reset); the reset itself (he is asleep); Monday
  (too late); Sunday 08:00 UK. Chosen: Sunday 08:00, every Sunday, answered or not, since the desk cannot see his login.
- *The UK clock.* Options: add a time-zone dependency (his call); a second rule; the calendar's own dates. Chosen: the
  calendar's, at the cost of three repeated lines (R-PAPER-6 removes them).
- *Ticked though nothing sends the lines yet.* Sending is the messenger's, asking the adapter's; both owed under Remains.
- Evidence: contract test seen failing first; two blind reviews, seven blocking findings fixed; 183 deliberate breaks, four gaps left and named.

### 2026-11-13 — the day's check and the refusal (paper-check, #104)

Decided by the PAPER lane as the desk's mentor, no one watching.

- *Where the refusal lives.* Options: a question the adapter asks at the last moment; a lock inside the door reading every
  message; a wrapper round any broker. Chosen: the question (`clearance.require`), as the kill switch's drill is ruled.
- *A record, not a held pass.* Chosen: a dated record in the desk's folder (`checks.csv`), surviving restarts.
- *"Begun" first, then the result.* A check that dies half way leaves a row that refuses orders, with no error handling.
- *The newest check decides*, not any clean one that day. The day is the UTC date (both sessions fall inside one).
- *Whose stop.* Only the desk's own stop under its own order id protects; anyone else's is named and the line unprotected.
- *Holdings stay with the door, orders go to the check*, because a lane may not reword the manifest's description.
- Recorded, not changed: no maximum age inside a day; the zero-share stop; a future-dated row sticks. Evidence: 54 breaks, 49 caught at once, two gaps closed.

### 2026-11-13 — the paper account answers five of six questions (paper-adapter first step, R-MONEY-5, #110)

Decided by the PAPER lane as the desk's mentor, no one watching.

- *How much in one change.* Options: the whole adapter; the five answers with placing raising. Chosen: the five (209 product
  lines, under the 300 cap); placing cannot be safe without its stop.
- *What "did the broker receive it" reads.* Options: open orders and fills; those plus the day's ended orders. Chosen: both
  plus ended, read in the order open, ended, fills, so nothing slips between readings and nothing is sent twice.
- *Filled completely* only when listed once, ended, filled whole, and the desk's fills agree; else the broker's words.
- *A refused cancel.* Options: raise; take as "already over"; read the account again. Chosen: read again (a fill just before
  the cancel is the likeliest case; "over" could hide a working order). A stop to sell is never cancelled.
- *The ended list names no program*: the reference alone decides, which can only make the desk send less.
- *Stops given* are the desk's own. *The published client* (ib_insync 0.9.86) was read as a reference only, never imported.
- *Tests against product:* 223 test lines for 209 product; shared messages and loops, no case dropped. Evidence: 65 breaks, 62 caught at once.

### 2026-11-14 — a sale can be placed; a buy waits for its stop; the drill held by code (paper-adapter second step, paper-drill, R-MONEY-6, #113)

Decided by the PAPER lane as the desk's mentor, no one watching.

- *How much in one change.* Options: both sides with the stop later (a buy could sit unprotected); everything at once (over
  300 lines, too much unproven); the sale whole and a buy refused in code. Chosen: the third.
- *A sale on a line under the desk's own stop* is refused: it would leave a stop for shares not held and could sell short.
- *The drill now, not in its own box.* The review's blocking point: this change is where the adapter can send, and his
  ruling is no order before a drill. So paper-drill and R-MONEY-6 are done here: a drill within 31 days, else refused.
- *The broker's last word.* Read until the order is over or the Gateway is silent 15 seconds, then cancel what did not fill.
- *Answer read afresh* from the broker, one home for "what did it do". *Not ready* is "never received"; no drill, no check, an
  unlisted line are refusals. *An error after sending*: raise and leave it; the broker is asked before any resend.
- *No trial order* went to the real Gateway: one wrong field could place a real order on an account shared with the old desk.
- *Unasked news passed over in every reading*, reversing one line of #86's tests, since fees and states arrive after an order.
- Evidence: 64 breaks, 62 caught at once, two gaps closed; the 115 order fields checked twice independently, no difference.

### 2026-11-14 — plateaus over peaks (rungs-plateau, #107)

**Decided**, by the lane as the desk's mentor.
- *What counts as beside a setting.* Options: sides only; sides and corners. Chosen: sides and corners (eight neighbours for two parameters), the stricter, since a failing corner is a failing rule one step away.
- *The grid's edge.* Options: passing ground; unknown. Chosen: unknown, so a setting on the edge has depth 1 and is never promoted: the best on a slope still rising is not a plateau.
- *Failures left off the surface.* Options: read the grid from the results; declare the grid first. Chosen: declared first; a missing setting counts as never tried and ends a plateau (the first blind review's finding).
- *The least plateau.* Options: depth 2 (the setting and all beside it); deeper. Chosen: depth 2, the smallest shape that is not a peak; the deepest is chosen first anyway.
- *Ties.* Options: best own score; best worst neighbouring score. Chosen: best worst neighbour, so the choice never chases one high score; then grid order, so arrival order changes nothing.
- *The least step between values, a tenth of the lower.* Options: none; a limit. Chosen: a limit, compared exactly; values a hair apart are one rule tried twice and would make a plateau of a peak.
- *Settings held to the grid's own number types.* Options: accept anything equal to a grid value; refuse floats and bools. Chosen: refuse.
- *Which branch carried the pull request.* Chosen: the restored branch, keeping its history without a force-push.

**Evidence.** Two blind reviews; depth matched a naive definition on 5,980 random surfaces; 22 of 24 deliberate mutations caught (one equivalent, one now pinned). Nothing calls the module yet: the five rules carry no settings.

### 2026-11-14 — periods and regimes (rungs-regimes, #109)

**Decided**, by the lane as the desk's mentor.
- *What the weather is.* Options: this module invents a regime label; the caller gives each day's regime by name. Chosen: the caller; the label is the "Market weather" box's (REG-01), one owner per concept.
- *Which regime a trade belongs to.* Options: the day decided on; the day filled; the day sold. Chosen: the day decided on, all the desk could know when it sent the order, and the day the paper tag reads.
- *How a regime is replayed.* Options: a separate run per unbroken stretch; the whole window run once and its priced trades shared out by regime. Chosen: the latter; the rule stays warmed, every trade is in exactly one regime, nothing is priced twice. Periods reuse the folds' cutting (the lane's ruling of 13 November).
- *"Never failed for working in only one".* Options: pass only if it earns in most regimes; not failed if it earned on the whole window or in one regime or more. Chosen: the latter, the box's own words; each look is a trial for the luck rung.
- *A strategy that passed only on all weather together.* Options: call it proven in each regime it traded in; it has no home and every paper trade is tagged. Chosen: no home; the tag is a fact, not a refusal, so over-tagging costs nothing and under-tagging hides a risk.
- *Periods earn no home.* A past period cannot come again; they are shown side by side, never picked from.
- *Refused as faults:* a day with no regime; a regime name not one plain word; a window all one regime; under two periods or more periods than bars.

**Evidence.** Four contract tests; 68 deliberate breaks over two rounds, one harmless survivor; a blind review's two blocking faults fixed.

### 2026-11-14 — failing fairly (rungs-fair, #112)

**Decided**, by the lane as the desk's mentor.
- *Several answers read together.* Options: a fail always first; a fault in the test first, then a fail on enough trades, then not enough evidence, then doubt, then pass. Chosen: the latter; a faulty test says nothing, and a real fail on enough trades outranks what too few could not settle.
- *A window whose only trade is still held, or sold on its last day.* Options: not enough evidence; a fault in the test. Chosen: fault; the window was too short to judge even one trade.
- *Known answers written in `lab/published.py` and in the strategies' contract test.* Options: one home; two. Chosen: two; the contract test is the independent pin, so editing the published answers alone cannot make wrong code pass.
- *"Effective trades"* today is trades judged whole on one line; pooling across lines waits until pooling is built.

**Evidence.** Deliberate violations driven in tests: a rule buying a day early, a grid selling a day late, a rule with no publication; each refused. Not built (minor): plateau and regime rungs read only pass or not.

### 2026-11-14 — the first rung's costs whole (rungs-costs, #115)

**Decided**, by the lane as the desk's mentor.
- *What a trade's return is measured on.* Options: the pounds out at the buy with its commission and conversion in, as before; the pounds the shares' value took at the buy's fill, every cost of both legs off the profit. Chosen: the latter, as the desk's own book states a round trip, so rung and book agree to the penny. This replaces the 13 November wording "on the pounds paid".
- *Which day's rate sizes an order.* Options: the decision day; the sending morning. Chosen: the sending morning, as the desk's day does (the blind review caught the first draft).
- *A pound line and the rates.* Options: demand a rate of 1; read none. Chosen: none.
- *A missing day's rate.* Options: carry the last forward; refuse. Chosen: refuse; carrying forward is a default that masks missing data (canon A2).
- *A sale on a morning that opens at or under the stop.* Options: an ordinary sale; the stop's sale. Chosen: the stop's, which slips three times as far.
- *Re-pinned test numbers*, under his ruling of 13 November "always go with recommended": with fuller costs three pins on made-up prices moved (the bracket seeds are now 1 and 16; one pin reads "above 2.8"). Not a golden number, not a loosened guard.

**Evidence.** Rung and the desk's book agree on the same fills; eight deliberate breaks, all caught; two blind-review findings fixed.

### 2026-11-14 — the author's own result (rungs-reproduce, #120)

**Decided**, by the lane as the desk's mentor.
- *Costs in a reproduction.* Options: the desk's costs; count as the author counted, before costs. Chosen: the author's way; the question is whether the code is the author's, and the desk's costs could never match a figure. What a rule earns stays the first rung's to say.
- *How near is "the same".* Options: one tolerance; one written beside each printed number before any run. Chosen: the second; a nearness picked after a run is picked to pass.
- *A figure not read from its source.* Options: enter second-hand numbers marked unverified; enter nothing. Chosen: nothing; a number nobody checked proves nothing.
- *A hole in the bars.* Options: carry on; refuse, warm-up included. Chosen: refuse; a 200-day average over a hole is another average.
- *No trade in the author's period.* Options: "not reproduced"; refusal. Chosen: refusal; a share of winners among no trades is no number.
- *Which box.* The indicator box was not taken because it needs the money lane's file.

**Evidence.** Sixteen deliberate breaks, all caught; a blind review's two blocking findings fixed.

### 2026-11-14 — before paper and after it (rungs-promotion, #127)

**Decided**, by the lane as the desk's mentor.
- *Which box.* Options: reproduction, indicators, the later requests, "before paper". Chosen: "before paper", the first waiting on nobody.
- *A kill condition.* Options: free words; numbers. Chosen: numbers, a fall in pounds from the highest paper profit and a run of lost trades, both required; words can be argued with afterwards.
- *The loosest kill.* Options: any fall; none deeper than the A-GATE's £1,500 (AG-05). Chosen: the cap. Open: several candidates may each declare £1,500; a share per candidate belongs with phase 5's side-by-side box.
- *Kill numbers for the five rules now.* Options: declare today; none until a rule passes. Chosen: none; a number with no history is a guess.
- *Effective trades.* Options: every round trip; every order; the most trades no two held on one day. Chosen: the last, the lowest honest count.
- *An order sold in parts.* Options: a trade from its first sale; only once whole, its money counted meanwhile. Chosen: the second; else history is rewritten.
- *A day's sales and the fall.* Options: sale by sale; the day together. Chosen: together; fill order within a day is the broker's accident.
- *"A penny ahead".* Chosen: by the one rounding policy.
- *Losses still held.* Options: withhold promotion while anything is held; judge sold trades only. Chosen: sold only (a rule nearly always holds something); the stop bounds the rest.
- *Words.* Chosen: the ladder's own (fail, not enough evidence, doubt, pass).

**Evidence.** Two blind reviews; 82 deliberate breaks over three rounds; bet count checked against brute force on 3,000 random sets.

### 2026-11-14 — the market's rung (rungs-market, BIC-01, #131)

**Decided**, by the lane as the desk's mentor.
- *Which box.* Options: reproduction, indicators, three-strategies, this. Chosen: this, first half (BIC-01) only.
- *What the risk is measured on.* Options: each trade beside the market over its days; every day of the window. Chosen: every day; under the first a rule in for rises and out for falls scores nothing, its skill being the days it stood aside.
- *Beta or a leverage-matched benchmark.* Options: assume stated leverage; measure the share carried. Chosen: measure; a five-times line held a fifth of the days carries the market's risk.
- *The market only or the line as well.* Options: the market; the line; both. Chosen: both, after the blind review showed a rider of a self-climbing line passing; the lesser excess is judged.
- *The bar.* Options: any positive excess; two standard errors; a new figure. Chosen: the first rung's two standard errors; no new knob.
- *Which line is the market.* Options: fix VUAG; the caller names it, on the line's own venue. Chosen: the second; closes hours apart understate risk. Owed: write down each line's market once the rung is wired in.
- *A trade the first rung could not judge.* Options: count its days as nothing; leave them out. Chosen: leave out (LAD-06).
- *Costs within a trade's days.* Options: split between legs; all on the selling day. Chosen: the selling day, so days sum to the first rung's gain.
- *When it answers.* Options: its own answer; repeat a first-rung fail. Chosen: its own; the verdict rule takes the least.

**Evidence.** 45 deliberate breaks, 42 caught, 3 that no single line can produce; a blind review's two blocking findings fixed.

### 2026-11-14 — the nine open boxes noted (rungs-notes, #129)

**Decided**, by the lane as the desk's mentor.
- *The order.* Options: the book's order; ready boxes first. Chosen: ready first; a session handed a blocked box is spent on nothing.
- *The eleven-rungs box.* Options: a fixed set of files so others run beside it; all the lane's files, alone. Chosen: alone; a guessed list would stop it half-way. A later session may split it.
- *Beta before the eleven rungs.* Options: folded in; its own box first. Chosen: its own, one home for "the market risk taken".
- *Leveraged and eponymous boxes* hold all the lane's files; new rules live in `desk/strategy.py`, so each will need a request to MONEY.

### 2026-11-14 — the first real paper orders, with the markets shut (paper-conformance, dry half, #135)

Decided by the PAPER lane as the desk's mentor, no one watching.

- *Send real orders with the markets shut?* Options: wait for market hours; send one share with its stop while no market can
  fill it and cancel at once; also force rare answers. Chosen: the second. Drill, clean check and Gateway ready first.
- *One dry order on every line.* It learns each line's stop step and unit and which lines the account may trade; found SPY, QQQ refused.
- *A conformance desk of its own* (`KESTREL2_DATA/conformance`), so no conformance fill counts towards FIRST-LIGHT. The driver is scaffolding outside the repository.
- *An order the broker tells twice is one order.* Options: mend in each reader or once in the door; known by the broker's id or by everything read of it.
  Chosen: once, by the broker's lasting id, last telling standing; an order under no real id is refused loudly. Known-by-content would read two stops if shares changed, and could cancel a line's only stop.
- *Tests against product:* 4 product lines, 48 test lines, spent from the guard's room to make the lane's pretend match the real.
- *The 15 seconds a refusal costs are left*: stopping at "Inactive" would lose the reason. *Kill switch pulled whole on the real account*, released at once.
- *Ticks none:* fills, a triggered stop, a sale and a part fill cannot exist with markets shut.
- Evidence: 13 deliberate breaks, all caught; 609 recorded conversations replayed through the code; a blind review's three looks, the last clean.
### 2026-11-14 — the book's concentration (rungs-beta, BIC-02, #136)
- Which box: reproduction (waits on DATA), indicators (waits on MONEY), or the market-risk box's second half. Chosen the last: waits on nobody, and the eleven-rungs box waits on it.
- What "moves together" is measured on: (a) each holding's own daily profit; (b) the lines' price moves. Chosen (b): a line is held on few days, so profits overlap too little to measure, while prices give a full year.
- Moves over one day, two days or a week. Chosen two days: London closes 16:30, New York 21:00, so a US day reaches a London line the day after (the same company's two listings read 0.79 day against day, 0.88 over two days). A week leaves too few moves.
- History: only the days judged (too few; chance joins lines), everything kept (lines that parted still join), or the latest year. Chosen the latest 250 moves, 120 the fewest. Fixed before any result.
- The line between together and apart: 0.3, 0.5 or 0.7. Chosen a half, either sign (a line and its inverse are one bet): clear of chance on a year, low enough that a share and its market are one bet.
- Clusters only where every pair links, or joined through chains. Chosen chains: errs towards more concentrated, the safe direction.
- Independent bets: count clusters held, or the effective number weighing pounds and movement. Chosen the second: counting clusters calls 4,000 pounds in one market and 10 in another two bets.
- A pass mark: set one now, or measure and show only. Chosen show only: a new A-GATE condition is the operator's. Recommended when asked: show both numbers on every report, set a mark after seeing a few.
- A line's profit not stated, or a day held outside the year read: suppose/answer anyway, or refuse. Chosen refuse (blind review): both give a wrong split or weighing, silently.
- Ticks: none, as #131 and #127, or rungs-beta. Chosen rungs-beta: both halves are built and proven; leaving it open would hand the same work to another session.

### 2026-11-14 — which rules wait for the author's result (rungs-reproduce, second step, #139)
- Every rule waits for a reproduction, or a rule waits for every figure on file for it. Chosen the second: three of five rules (Bollinger, 50/200 cross, Supertrend) have no author's test, and the first would stop the whole lane on one data request. The verdict carries the fact, so promotion can demand it later.
- Wait by a new "waiting" answer, or by a loud refusal as for code that is not the published rule. Chosen refusal.
- What counts: any "the same", or only one of the figure on file, over its market and period, by the code as it now is. Chosen the second.
- Does the rung re-run the reproduction: no, it takes the answer of `reproduce`, since `folds` and `regime` have no author's bars to pass. Said plainly in the module. Not ticked: the figure and first real run remain.

### 2026-11-14 — the first printed result (rungs-reproduce, a step, #141)
- Which result first: (a) wait for RSI-2's figure, which needs the book bought (spend is the operator's); (b) the publisher's free chapter, Double 7's on SPY from 29 January 1993 (153 trades, 80.4%, 0.85%, 122.36 points); (c) web write-ups. Chosen (b); (c) refused as second hand.
- Figure fixed before any run: end 31 December 2007 (not printed for SPY; taken from the chapter's other tables); filled at the close. Same means: within 5 trades, 1.5 points of per cent correct, 0.05 average gain, 10 points. Wide because the end date is uncertain by months; not to be moved after a run.
- Prices as traded or dividend-adjusted: the 122.36 points look like unadjusted prices (inference). Chosen: ask DATA for both, let the points say.
- Enter it in FIGURES now, or when the rule and bars exist. Chosen the second: a figure on file stops every verdict on its rule, and this rule is not coded.
- Buying the book is the operator's. Recommended: yes, one copy; it holds RSI-2 and several more of the twenty-one rules' figures.

### 2026-11-14 — stress scenarios judge nothing (rungs-stress, TST-06, #140)
- Pass or fail a strategy: fail above a loss bar set here, or measure only. Chosen measure only: the loss the desk will bear from a gap is MONEY's to set once (STP-10); a bar here would be a second home for one rule.
- Which fall is the gap: an invented figure, the worst day of the history (7.2%/8.7%), or the black swan's 10% already ruled. Chosen the black swan's, read from `desk/emergency.py`, times the line's leverage.
- The gap's cost: the trade's whole loss, or the night's own take. Chosen the night's own (the first review showed the other picks the lowest close, not the worst night). Limit: the market's fall, not a single share's.
- When an episode is "tested": the dates cover it, or the rule is shown able to trade through it. Chosen the stricter: bought before it began, a bar for every session, judged trades to its end. A wrongly "untested" costs evidence; a wrongly "lost nothing" costs money.
- Episodes fixed in code before any result: 2020 crash from the session after 19 February's high to 23 March; May 2010 as two days (London's morning after counts); August 2015 one day. Flash-crash stops fill at their level, so the figure is the least lost.

### 2026-11-14 — indicators held to tables printed by others (rungs-indicators, first step, STR-14, #145)
- Take the box though it waits on MONEY, or return it. Chosen take: the parts where classic mistakes live (sample deviation, exponential average for Wilder's) are reachable today.
- Reach `_Window` and `_Wilder` directly, wait for public names, or test through strategies only (only frozen settings 2 to 200 days visible, no published table). Chosen direct: one piece of code at any length. The cost is a coupling to MONEY's private names, asked about as R-RUNGS-6.
- Publication: Wilder's and Bollinger's books (not obtainable this session) or StockCharts' spreadsheets (read cell by cell). Chosen StockCharts; the books' tables stay worth adding if the operator has them.
- Nearness fixed before the first run: average exact to six places, deviation and smoothed value to four. Nothing needed loosening.
- Wilder's smoothing fed the spreadsheet's own Gain, Loss and true-range columns, not a re-typed split (that would test a second copy).
- A gate in `proven` before any verdict, not only a test: under a millisecond once per run.
- Ticks: none; "each indicator" is not true while the RSI and true range as wholes are out of reach.

### 2026-11-14 — RSI-2's figure and the book (rungs-reproduce, blocked, #143, #149)
- Read RSI-2's figure from a copy of the book on a stranger's site: (a) yes, free and now; (b) no, wait for a bought copy. Chosen (b): not the publisher's, cannot be shown unaltered, and taking it is not the desk's to decide unattended. Write-ups refused again (second hand; they disagree on which rule the book's table tests).
- Connors' own free "RSI 25" figure on SPY (1993-2008: 85 trades, 88.24% correct, 1.50% average gain; 2009-2017: 62 trades, 96.77%, 1.32%): write it into the code, or note it only. Chosen note only: the rule is on nobody's list and the desk holds one position on a line, so a figure in code would be a promise nothing can keep.
- Run RSI-2 on real SPY before its figure is known: only as a dry run, no author's number beside it, over years the book does not cover. Nearness is still fixed with the figure, before any run against it.
- Build anything while the box waits (a reader of the store, a runner of every figure): chosen nothing; code for a need nobody has yet is growth the canon forbids. A two-line record of the finding was kept so the next session reads it first.
- Buying the book is the operator's (spend), so the recommended option is not taken for him. Recommended: yes, one copy of Connors and Alvarez, Short Term Trading Strategies That Work (2008).
- Ticks: none; the box is marked blocked so the runner stops handing it out.

### 2026-11-14 — indicators through the rules' own lines (rungs-indicators, second step, STR-14, #154)
- Wait for MONEY to name the indicators (R-RUNGS-6), copy the rules' lines here, or show the rule itself the published days and read what its lines fed to its smoothing. Chosen the third: a copy proves nothing about what trades; waiting leaves the true range's gap term unheld. Cost: deeper coupling to private names, asked about as R-RUNGS-12.
- A rule at 2 or 10 days against a 14-day table: its smoothing parts are swapped for ones of the table's length; a smoothing of length 1 returns what it was fed, which reads the raw Gain, Loss and TR columns.
- The RSI's table is now given closes, so Gain and Loss become printed columns to be matched; the numbers on file were re-read and found identical first.
- Channel table: the stochastic oscillator's spreadsheet (the only ChartSchool one printing highest high and lowest low). Its weakness (no day whose own low is the 14-day low) is stated, not hidden.
- Nearness fixed before the first run: Gain, Loss, TR, highest high, lowest low exact to four places; averages to four. Nothing loosened.
- The surviving break (a lowest low leaving today out): leave unsaid, invent a series (refused), or say so and ask for a second table. Chosen say so.
- Two commits in one pull request (re-laying tables under the 400-line cap, then the feature). Chosen over two pull requests.
- Evidence (A7): 27 deliberate breaks, 26 caught; blind review compared 19 columns to the spreadsheets' cells and drove 21 mutations, nothing blocking.
- Ticks: none; "each indicator" is not true while the RSI's ratio is held by no printed number.

### 2026-11-14 — a replication stands in for the book's figure (rungs-reproduce, a step, #169)
- What stands in for the book's RSI-2 table: (a) wait for the book (his spend; he has said no); (b) a best-fit number put together from pages that each test something else; (c) write down the nearest published tests exactly as printed, each of its own rule, market and period, and put none on file until the desk can run that very test. Chosen (c). His words: "cannot afford it, so instead, research on the internet and find a best fit answer." A number nobody printed is not a figure.
- This replaces #141's refusal of web write-ups as second hand, made the same morning before his ruling.
- Second hand as a label on the figure, or a separate list: chosen one list, each figure saying whose it is. The first rung waits for both alike; a second list would be a second home for one rule.
- A range as its own kind of number, or a middle and a distance: chosen the second (`Stated.between`), one way of saying "the same", already tested at its edges.
- Swanson's "cumulative RSI(2) below 5": read as Connors' cumulative RSI, or as the plain 2-day RSI. Chosen the plain one: he tests thresholds from 1 to 30 and a sum of two days' could not sit under 5 a hundred and twenty-nine times. An inference, labelled so; the tolerance is wide for it.
- How near, fixed before any run: Swanson 8 trades and 3 points (his dates are not printed); Empirica 3 trades, 2 points, 0.06 of mean gain (exact dates, costs not said to be in or out).
- Enter either figure in FIGURES now: no. A figure on file stops every verdict on its rule, and neither can be run yet.
- Ticks: none; the first real run and the passing-on through folds and regimes are not done.

### 2026-11-14 — the ruling acted on, the rungs' tests off SPY and QQQ (rungs-reproduce, requests, #186)
- The ruling, taken for the operator by his standing ruling of 13 November: rungs-indicators waits on R-RUNGS-6; RSI-2 no longer waits for the book. His words of 14 November (#157): "why do i need to buy a book. right now i cannot afford it, so instead, research on the internet and find a best fit answer." Both reproductions are to be made from the best free published figures, labelled second hand; one needing prices from 1993 waits on R-RUNGS-5.
- Run a reproduction today on the prices the desk has (2010 on)? (a) set the 1993-on figures beside a run over 2010-2026: refused, numbers of other years could only match by accident; (b) make a 2010-on figure by subtracting one printed span from another: refused, a number nobody printed; (c) wait for SPY from 1993. Chosen (c).
- A third RSI-2 page, read and refused as a figure: Backtrex, "Does the RSI(2) strategy work on the S&P 500?" (run 2 October 2026), 3 October 2016 to 1 October 2026, 73 trades, 71.2% winners. Its period is inside the desk's prices, but it trades long and short, also sells under the 200-day average, carries a stop, and is on a contract for difference. Another rule on another market.
- Where the research notes go: STATUS or DECISIONS. Chosen DECISIONS (how near is the same is a decision fixed before a run, and this record is never cut down); STATUS keeps one line on what the box waits on.
- The figures written down, none on file, nearness fixed before any run:
  1. Double 7's, the authors' own. Connors and Alvarez (2008), chapter 10 as its publisher gives it away: a close at a seven-day low bought while SPY is above its 200-day average, sold at a close at a seven-day high; SPY from 29 January 1993, end taken as the end of 2007: 153 trades, 80.4% gaining, mean gain 0.85%, 122.36 points. The same is within 5 trades, 1.5 points of share gaining, 0.05 of mean gain and 10 points. Waits for R-RUNGS-10 and SPY from 1993 as traded (R-RUNGS-5, 9).
  2. Double 7's, second hand. StrategyQuant, "Larry Connors' Double 7 Strategy: Tested on SPY and 8 Other Markets" (Souckova, 16 September 2026): same rule, long only, daily SPY, filled at the close, no cost, January 1993 to September 2026: 333 trades. No share gaining or mean gain printed; profit factor, Sharpe and dollars are not numbers the desk counts. Dates taken as 29 January 1993 to 15 September 2026; the same is within 10 trades (days not printed; dividend adjustment unsaid). Waits as the first.
  3. RSI-2, second hand, on the index. Swanson, "Connors 2-Period RSI Update For 2013" (EasyLanguage Mastery, 26 August 2013): rule as coded, at the close, S&P 500 index "from 1983": 129 trades, 82% profitable. Period taken as first session of 1983 to last of February 2013; "cumulative" read as plain 2-day RSI under 5. Within 8 trades and 3 points. Its dollars and misprinted SPY column are not used. Waits for the index from 1983 (R-RUNGS-13).
  4. RSI-2, second hand, on SPY. Empirica Lab, note EL-R-2026-302 (11 October 2026): SPY dividend-adjusted, at the close, 29 January 1993 to 30 September 2026, bought under 10 and not under 5: 265 trades, 204 gaining, mean gain 0.63% (0.02% charged a side; whether the mean is after it is not said); before 2009: 116 trades, 81%, 0.79%. Within 3 trades, 2 points and 0.06. Waits for RSI-2 buying under 10 (R-RUNGS-14) and SPY from 1993.
- The best free figure per rule: RSI-2, Empirica's (4), the only one on SPY with exact dates; Swanson's (3) is of the rule exactly as coded but needs the index. Double 7's: the authors' own (1), with StrategyQuant's (2) as the second-hand check.
- Three requests and the ruling in one pull request: all on one box's files, each in its own commit.
- Pages read through a web reader on the day, not opened by a person; a person or a later session opens each once more before its figure goes on file.
- Ticks: R-DATA-11, R-RUNNER-5, R-RUNNER-3 (requests to this lane, done).
