# The rungs lane

The rungs lane's own decisions, each a dated `###` entry saying what was decided, the
options, why, and the evidence; newest last. Only this lane's scribe writes here, so no
other lane's pull request touches these lines. Held to a size a session reads whole
(`BUDGET.json`, `max_lines_per_lane_doc`): when it is full, the scribe folds the oldest
settled entries into one short summary entry; git keeps every word.

## Decisions

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

### 2026-11-14 — the ladder's set 1 as one command (lab.ladder, LAD-09, LAD-03, BT-15, #198)
- *Which strategies.* Options: only rules with an author's figure on file (empty today); every published rule held, each line saying whether an author's result stands behind it. Chosen the second: the set is fixed by the files, not by eye, and an empty file would tell him nothing. Nothing counts towards paper either way.
- *Which lines.* Each rule's declared universe, the twenty-two lines; one answer per rule and line, no pooled answer invented.
- *The window.* Options: all bars held, moving each day (a new trial daily); one fixed window. Chosen fixed, to 13 November 2026; a later end is a new set, on purpose. Judged from each line's first bar: dividing the yearly Sharpe by years the line did not exist came out 1.3 to 5 times too low (the review's blocking finding).
- *Folds: two,* fixed before any result, since the rules trade five to ten times a year; 3 trials a cell, 330 in all.
- *The market beside each venue.* SPY in New York, ISF in London, fixed before any result; the rung also sets each beside its own line held, the harder test.
- *The one verdict.* Options: a new rule over all rungs run; the one in `lab/deflated.py`, with folds and market recorded beside it. Chosen the second: one home for the verdict rule.
- *Dollar rates.* Options: wait for the kept rates (R-RUNGS-3); the desk's interim rule over history (the pound's last close before the day, none older than four days). Chosen the rule, unbent: one day (21 April 2025) has no rate and 32 cells wait. Declined: the day's own close (a peek), a longer limit chosen to cover one day.
- *A parked line is not judged* (six London lines), and *a cell that cannot be judged* is kept with its reason and tried again; only a refusal by name, a missing file or a stale store counts, so a bug stops the run loudly. The command ends 0 when its pass finishes.

### 2026-11-14 — waiting cells and short histories (R-RUNNER-25, #202)
- *History needed before "no trade" means anything.* Options: 200 bars (the longest window); 452 (window plus a year, at 5-10 trades a year); 30 trades' worth. Chosen 452, the middle, recommended. A zero-trade verdict on a shorter line is "waits on history", not FAULT; on a long enough line it is still a FAULT.
- *Retried cells.* Options: rewrite the cell with a new try time (one small line per cell per 30 minutes); a sidecar file. Chosen rewrite: the record stays in one file.

### 2026-11-14 — a cell without its folds has no verdict (R-RUNNER-33, #206)
- Options: (a) no verdict; (b) treat the unrun rung as THIN; (c) leave folds out of the rule for those cells. Chosen (a): the rule is every named rung and no other, and an unrun rung is not evidence; (b) blurs "too few trades" with "not run"; (c) brings back the gap the review found. No real cell is affected today (`reproduce.FIGURES` is empty).
- `Candidate` checks the six named rungs and ignores the row's `unrun` list (regime, plateau, stress), as scoped. Refusing a row that lists unrun rungs is left, recommended when the first real candidate nears.

### 2026-11-14 — rungs-reproduce handed out again while blocked (#195)
- *Build anything while the box waits.* Options: (a) code a real run might want one day; (b) nothing. Chosen (b), as #149: with no figure, rule or prices nothing could call it.
- *Open a pull request at all.* Options: none (the Waits line never reaches the runner); the smallest true record. Chosen the record, one comment line in `lab/reproduce.py`.
- *Which request the Waits line names.* It takes one: R-RUNGS-5 (DATA, blocking) or R-RUNGS-10 (MONEY). Chosen R-RUNGS-5; the box's note in PLAN now holds all five waits.

## 2026-11-14 — pyarrow for the head start, and a source for each old store (R-RUNNER-24)

**His ruling**, standing since 13 November: "please always go with recommended to avoid waiting for me to attend". #196 named why parquet folders and raw Stooq zips had no reader, and asked for option (a), taken as recommended: `pyarrow==26.0.1` to be pinned in `requirements.txt` and imported in `lab/headstart.py` only; `desk/` stays standard library. The pin itself is not in this change: the lane guard refuses `requirements.txt` to the DATA lane (it is in no lane's files), so it waits for a session that may touch it, together with `allowed_third_party` in `manifest.toml`.

**What it replaces.** Four of the five old stores hold parquet. A reader for that format (column encodings, compression, row groups) is code we would otherwise write and maintain; pyarrow is tested code we do not.

**Options.** (a) pin pyarrow, lab only (chosen); (b) write a parquet reader (refused, large and ours to maintain); (c) leave four stores unread (refused, the head start's whole point is those bars).

**Sources.** `Source` in `desk/bars.py` gains `STOOQ_RAW`, `IBKR_STORE`, `STOOQ_STORE` and `TREND_STOOQ`, so that each old store's bars are kept under its own name. All are non-fresh: they only fill.

**Remains.** The pin and the manifest's `allowed_third_party`, then the readers.

**14 November, later.** The four `Source` names are on main (#203). The pin was tried again under a claim naming `requirements.txt`: `tests/guards/test_lanes.py` still refuses the file to the DATA lane whatever the claim says, so it needs `requirements.txt` added to a lane's files in `manifest.toml` `[lanes]` (a guard loosening: recommended, taken, DATA's list), in a session whose claim holds `manifest.toml`.

**His approval, 14 November ~20:05**, in chat, answering "pyarrow: it lets the old-store readers open the old stores' files, which gives the ladder years of extra history ... My recommendation is yes": "Yes, allow pyarrow". Pinned as `pyarrow==22.0.0`, the version already installed on the desk's PC (so the jobs need no install), and added to `lab`'s `allowed_third_party` only. `desk/` stays standard library; the wall guard still refuses it there. Made by the coordinator in a non-lane change, because no lane may touch `requirements.txt` or `manifest.toml`'s third-party lists; the lanes table is unchanged.

### 2026-11-14 — the old stores as a head start, as a command (data-headstart, #190)
- Where the register is found. Options: a new environment variable; an argument; the notes folder next to the data folder. Chosen: next to the data folder (`KESTREL2_DATA/../kestrel2_notes/data_register.md`), so every path still comes from the one setting (OPS-15).
- Which database. Options: `bars.db`; `market.db`, as R-RUNNER-11 names it. Chosen: `market.db`. Bringing the two files together belongs to data-two-stores.
- How a store is read. Options: by its name in the register; by its form (a `.db` file, or a folder of a line's matrices). Chosen: by form, so a renamed folder is still read; any other form is counted as "no reader yet", never skipped silently.
- The archive's five-minute bars go in first. Without them an empty market.db held nothing to prove an old bar's clock and the trial let in no bar; with them it let in 245,593.
- A store that cannot be read. Options: exit 1; exit 0 and name it in the counts. Chosen: exit 0 and name it; exit 1 is kept for a real failure.

### 2026-11-14 — the store's keeper (data-keeper, archive half, #188)
- Where the daily bars are kept. Options: (a) the existing price store (a file per line, cleaned by `store.prepare`) in `KESTREL2_DATA/daily`, with a record of the day covered; (b) inside the SQLite store. Chosen (a): the store the desk and scenes already trade on; the database's move is R-RUNNER-11's.
- When a refresh is due. Options: once each morning; morning and again after each venue's close. Chosen both: the day's record needs the day's closes that evening (R-PAPER-23), and the archive restates a close overnight.
- How long after a close. 30 minutes (`keeper.SETTLED`): the archive shows London about a quarter-hour late and an official close prints minutes after the bell. To be measured on real closes.
- A line the archive will not answer for. Options: always empty it; always keep what is held. Chosen by the day: a day already held keeps its bars, a new day parks the line with no bars, so an archive away at 06:00 does not blind a desk that was whole at 21:35.
- What is a miss: a venue with no line answered, or no clean line. One refused line among answered ones is parked alone and is no miss.
- A faulted line is asked again for six calls (half an hour), then left until the next refresh, unless its whole venue is blind: then at every call.
- A weekend call. Options: do nothing on any non-trading day; fetch what the store does not yet hold. Chosen the second: a whole store is left alone at once, and Sunday's rehearsal and a missed Friday evening are readied without a special command.
- The broker's bars as the fallback are not in this change (300-line step limit; the question must be proven on the Gateway). Until then a line without fresh bars is parked and not traded, and an archive wholly away ends the command with 1 so he is told after two rounds.
- The databases' names are not changed here (`bars.db` stays until R-RUNNER-11).

### 2026-11-14 — the store audited each morning (R-RUNNER-18, #199)
- Faults are grouped "by kind" by stripping dates, times and numbers from the store's own fault text, so no second set of rules exists. Options: a fixed list of kinds (a second rule set); this. Chosen: this.

### 2026-11-14 — the nightly backup (R-RUNNER-13, #204)
- Which databases. The plan names market_history.db and market_live.db but today's store is market.db. Options: wait for the rename; copy whichever of the three exist. Chosen the latter (fails loudly if none), so the 01:30 job works now and after the split.
- Keep 7 nights ("the last few").
- A same-night rerun is refused rather than overwritten, so a good snapshot is never replaced.

### 2026-11-14 — 3LGO's daily history (R-RUNNER-21, #209)
- Where to keep the history. Options: write the line's CSV directly (lost at the next keeper refresh, which rebuilds from the archive); change the keeper (outside the claim); shelve beside the store (`daily/<venue>/history/`) and join in `store.prepare`. Chosen: the last; the archive wins on any day it gives.
- The missing 12 November. Options: record the line as suspended (false); leave the gap (parks the line for 60 sessions); build it from the archive's five-minute bars of that day. Chosen: the last.
- Cross-check source. The archive holds nothing of 3LGO before 13 November, so the database's July daily closes are the only independent proof; gate: at least half the overlapping closes agree (7 of 9 did). Units: pence assumed for a pound line, refuted by the store's jump check if wrong.
- No blind review was run in this unattended session.
