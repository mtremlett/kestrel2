# Status

**Read this first, then `docs/PLAN.md`, then run `python check.py`.**

Five lanes run side by side (`docs/PLAN.md`). The shared part below is changed only by a
session the operator starts himself; each lane writes only in its own section, so that
parallel pull requests never touch the same lines. A lane's section says where it is, its
next step, what it found and did not fix, and any question it holds for the operator.

## Shared

Last updated: 14 November 2026.

### Where we are

Phase 2 under way. All seven scenes pass: scenes passing 7 of 7.

Two rulings of 13 November are in force (`docs/DECISIONS.md`): sessions merge their own
pull requests when the check is green, and GitHub now refuses any merge whose check has
not passed (driven red on pull request #5); the A-GATE test is written as AG-01 to
AG-06 in `docs/PLAN.md`, with the thirty-day terms fixed in advance.

Every change that lands on main now sends the operator one Telegram line once the check
passes there. Since his request of 13 November it is short: the phase whose step the change
ticked in this plan's checklist, or "housekeeping" when it ticked none, the scenes count,
the week's usage of his plan as the pull request states it on a line "Weekly usage: 21%"
("n/a" when it states none), and the pull request's number, for example "kestrel2 · Phase
2 · step 3 of 6 done · scenes 4/7 · usage 21% (#16)" (`announce.py`, the `announce` job;
`docs/DECISIONS.md`). A missing secret turns the job red; that was driven on main before
the secrets existed. The first line, for #7, reached his phone on 13 November; the first
short one, for #17, on the same day.

Five lanes now run day and night on the operator's PC, by his rulings of 13 November
(`docs/DECISIONS.md`): MONEY (scenes 5 to 7), PAPER (phase 3, begun alongside phase 2),
DATA (the research universe, the parked lines, the store's findings), GRID (the fast grid
engine) and RUNGS (the ladder's rungs). Every lane runs on Fable until 97% of Fable's own
allowance is used or Fable refuses a session, then on Opus until a Fable reset (his ruling
at 20:12 on 13 November, which replaced the earlier 45%). A
runner outside this repository starts each lane's next session when the last one ends,
inside the plan's included usage, stopping at 80% of the week.
GitHub merges a pull request only when its check is green and its branch already holds
everything on main, so two green lanes cannot combine into a red main.

### Open questions for the operator

1. **A second GitHub account** for sessions to work through, so that the guards cannot be
   removed by the account that enforces them. On 13 November he chose to start the lanes
   on his own account now; on 14 November he said leave it for now. Ask again before going
   live.

### Found, not fixed

- **Two of the line limits are prose, not guards.** CLAUDE.md says its 80 lines and
  CANON.md its 200 are held by a guard; no test reads either, and CANON.md is 224 lines.
- **The runner's own lines to his phone wait for his key.** A lane that halts, pauses at
  the weekly cap or needs his decision, and the 07:00 line, are sent by the runner on his
  PC from a file holding the bot key, which he copies beside the runner himself. Until he
  does, they are written to the runner's log only.
- **A Windows Update restart overnight stops the lanes until he logs in.** The runner
  starts at his logon; starting it without one needs his password in Task Scheduler.
  His ruling of 14 November: no password; updates stay paused.
- **The lane guard judges whole files.** A lane may write in any part of a shared
  document; that it keeps to its own section is checked only by the daily audit.
- **A newer ruff on the operator's PC calls the tree badly formatted.** Version 0.15
  formats differently from the pinned 0.8.6, so `python check.py` run with whatever is
  installed shows format red on a clean main. Run it in an environment built from
  `requirements.txt`. The check does not yet say which tool versions it ran with.
- **The scenes rule trusts the error's name.** A scene counts as "not built" when it
  fails with NotImplementedError. A test that raised that error itself would pass as
  unbuilt. No test does; nothing yet checks that none does.
- **Sessions opened in the predecessor's folder carry its permissions.** The session that
  wrote the scenes was started there and could not delete a scratch file. Open sessions
  directly on this folder.
- **The predecessor's price archive is five months stale.** A sample of 120 tickers
  found the newest bar in June 2026 for 85% of them, none current, and some major names
  absent entirely. It is usable as a head start on history, never as current data.
- **The predecessor's scheduled tasks are all disabled.** Eight had refused a session with
  "access denied"; on 13 November he checked every `KESTREL_` task in Task Scheduler as
  administrator and each says disabled (`docs/DECISIONS.md`).
- **The predecessor's paper book is flat.** Read at 14:36 UK on 13 Nov 2026, read-only:
  paper account, no positions and no open orders. Nothing was placed.
- **The unit tests are within a few lines of the product, and lanes collide on it.** The
  guard holds unit tests to no more lines than `desk/` and `lab/` together (about 1,435
  against 1,444 on this branch). The ladder's batch went red by one line once brought up to
  date with main (#28), each lane green alone; the runner's re-check caught it and a line
  was trimmed. Every lane's next test must come with as much product, or a test merged. A
  session the operator starts could record this in `docs/FAILURE_PATTERNS.md`.

## MONEY
Last updated: 14 November 2026 (money-working, money-watch, a lost stop told).
### Where it is
Scenes 7 of 7. Built: the five rules; sizing, cost model, gate; pretend broker; send path, ledger, book; the
day; kill switch; `emergency`; invariants; halts (#148); SimCity (#150, #163): a hundred seeded worlds, 31,000
days, eleven promises, 52 parts; **its night is GREEN** (money-working, #163: a note before each send; after a
death the broker cancels what is left working, a sale too). The crash watch (#172, `desk/watch.py`) is built
and halts nothing yet: nothing calls it. A lost stop is told the same day with stop, shares, level (#191).
### Next step
money-restop's put-back (`desk/broker.py`), then the limits, money-stranger, money-fills. `desk/simcity.py` (399) and
`desk/book.py` (400) are full: split first. A desk not restarted before the next open can end short (pretend broker should lapse orders at close).
### Done for other lanes
- R-PAPER-2: done in #64; R-RUNGS-1: done in #101; R-RUNGS-6, R-RUNGS-12: done in #185
### Requests to PAPER
- [ ] R-MONEY-7 (later): a typed command calling `kill.pull`, sending `Killed.words()` to Telegram.
- [ ] R-MONEY-8 (blocking): the paper day calls `day.trade` and `day.publish`, never `day.run`; the
  adapter refuses an order not dated the session before the broker's today.
- [ ] R-MONEY-9 (later): a stop's fills get the order's id plus "-stop". R-MONEY-10 (later): in conformance set paper
  fills beside `orders.charges` and the 0.05% spread. R-MONEY-11 (later): say when you hold `desk/clearance.py`.
- [ ] R-MONEY-17 (blocking): no paper sale unattended while a stop rests under the same shares, unless tied at
  the broker (money-working landed, #163); record in conformance what paper does.
- [ ] R-MONEY-18 (later): the morning message carries `halt.listed(root, day)`, every day's `halt.said(root, day)`.
  R-MONEY-19 (later): a typed command to call and lift a halt.
- [ ] R-MONEY-20 (later): `test_messenger.py` states each Record's `halted`, `stopped` (say `(), 0`); the evening
  message says when a day does not count. R-MONEY-21 (later): `test_running.py` (line 213) keeps Friday's record
  through `day._row(day.Record(...))`. R-MONEY-22 (later): say if `Broker.place` refusals need a blocker of their own.
- [ ] R-MONEY-23 (later): reword `desk/placing.py` where it says the cancel is the kill switch's alone, and its
  `manifest.toml` line: a desk that died mid-send asks the same cancel through `book._settle`. R-MONEY-24 (later):
  keep the day's check and `recover` before every round; say if you would rather the send path called one recovery.
- [ ] R-MONEY-25 (blocking): the unattended step calls `watch.look(root, fast store, daily bars by line, now, post)`
  every step, every hour, BEFORE its round of orders, and decides if London's morning round waits for the 08:05 bar.
- [ ] R-MONEY-26 (later): a messenger call sending again what was never delivered. R-MONEY-27 (later): the halt-lifting
  command names him (`by=halt.OPERATOR`), with a command for his word against the market.
- [ ] R-MONEY-30 (later): `running.recover` puts back a line held with no stop, when its shares are the book's: stop
  `<newest buy id>-stop` at `book.levels(root)[id]` rounded down to the price step, for the shares held.
  R-MONEY-31 (later): with R-MONEY-18, the day's list message includes its lost-stop entries.
### Requests to DATA
- [ ] R-MONEY-3 (later): a daily rate, pounds per dollar, in the store. [x] R-MONEY-15, R-MONEY-16: done (#163, #150).
- [ ] R-MONEY-12 (later): on the master, the market's lines: the yardstick's twin (VUSA), one in New York hours.
- [ ] R-MONEY-28 (blocking): the keeper writes each line's ended five-minute bars to the fast store every five
  minutes in trading hours, VUAG first, the day's last bar included; and says how late a bar lands (the watch's 20 minutes).
  R-MONEY-29 (later): the keeper or monitor tells him when a whole venue is not heard from.
### Requests to RUNGS
- [ ] R-MONEY-13 (later): the first rung prices each leg with `orders.charges`; a sale is charged as a purchase.
- [ ] R-MONEY-14 (later): AG-04 must not add the records' market column: compound the days or read two closes.
### Found, not fixed
- Costs: spread and slippage assumed; no clock on the day path (R-MONEY-8); `desk/halt.py` still says only the kill switch cancels.
- Watch (#172): no market read after London shuts; `halt.lift` defaults to the operator; a halt cancels no working buy.
- Lost stop (#191): kept level unrounded; `halt.listed` counts it blocked; `book.Reckoning` untyped. SimCity: no nightly run, no halted day or overnight death lived.

## PAPER

Last updated: 14 November 2026 (folds #100, #104, #110, #113, #123, #128, #135, #142, #152, #155).

### Where it is

Built, nothing asking yet: messenger (#142, no bot key), unattended step (#152), daily kill-switch drill (#155); orders refused
unless dated the session before. First real orders 14 Nov (#135), markets shut, all cancelled. No fill seen.

### Next step

paper-conformance in-hours half (needs open markets; drivers must date orders the session before), then paper-supervised
(asks for a step every few minutes; builds the price store's door), main's code, cards.

### Requests to MONEY

- [ ] R-PAPER-4 (later, 2026-11-13 20:05): `book.differences` names an entry at no shares beside another carrying the shares.
- [ ] R-PAPER-5 (later, 2026-11-13 21:10): the ledger keys a fill by whole id; the broker's ".01" to ".02" would double it.
- [ ] R-PAPER-7 (later, 2026-11-13 22:45): one public keeper of dated records (the check borrows `book._write`, `_turn`).
- [ ] R-PAPER-8 (later, 2026-11-13 23:30): the day's run collects fills at day's end too (broker tells today only).
- [ ] R-PAPER-9 (later, 2026-11-13 23:30): word `Broker.stops` as the desk's own stops only, or say others are needed.
- [ ] R-PAPER-10 (later, 2026-11-14 00:30): when `place` raises other than "never received"/refusal, pull the kill switch or tell him at once?
- [ ] R-PAPER-11 (later, 2026-11-14 01:25): `place` can raise "word, fills and account do not agree" after an order has gone; tell him and stop buying?
- [ ] R-PAPER-12 (later, 2026-11-14 01:25): word "a sale takes its shares off that stop" to allow two steps, or say if pretend must.
- [ ] R-PAPER-13 (later, 2026-11-14 02:50): the pretend broker refuses a repeated order id; the real one took it as new. Match, or `place` refuses.
- [ ] R-PAPER-14 (later, 2026-11-14 02:50): no buy on a line with `Line.retail` False (SPY, QQQ); the broker refuses them, 15 s each, daily.
- [ ] R-PAPER-15 (later, 2026-11-14 02:50): a working buy has its stop listed at the real broker; pretend has none. Match, or `Broker.stops` leaves it out.
- [ ] R-PAPER-17 (later, 2026-11-14): `book._write` has one temp file and no lock; two writers were driven to an unreadable record. Kill switch (daily drill, his typed command R-MONEY-7) and `running.csv` borrow it. Own temp name or one writer.
- [ ] R-PAPER-18 (later, 2026-11-14): rule a cut-off for a late buy (desk back at 15:00 sends London's orders); `day.trade` sends sales without buys past it.
- [ ] R-PAPER-19 (later, 2026-11-14): public "sessions owed a record" in `day.py` and "day an order is dated" in `orders.py`.
- [ ] R-PAPER-20 (later, 2026-11-14): `kill.py`: public "a drill made this day is on the record"; word `kill.Failed` for him (a rehearsal; promises named NOT kept).

### Requests to DATA

- [ ] R-PAPER-3 (later, 2026-11-13 18:55): each line's ISIN a fact on `Line`, confirmed from issuer/exchange.
- [ ] R-PAPER-6 (later, 2026-11-13 22:10): `desk/venues.py` gives a venue's wall clock publicly; `gateway` and `running` drop their copies.
- [ ] R-PAPER-16 (later, 2026-11-14 02:50): IDTL in dollars is unlisted at the broker (needs name or ISIN, with R-PAPER-3); SPY, QQQ can leave the lines.
- [ ] R-PAPER-22 (blocking, 2026-11-14 06:50): the day's pounds per dollar, readable before London's open and for any past session (R-MONEY-3's rate); else no dollar line is priced.
- [ ] R-PAPER-23 (blocking, 2026-11-14 06:50): say by what minute after each close the store holds the twenty closes; the day's record fails without them.

### Done for other lanes
- R-DATA-5: done in #53 (first half). Open: what the first London contract note says of stamp duty (conformance).
- R-MONEY-4: done in #75; R-MONEY-5: done in #110; R-MONEY-8: done in #152; R-MONEY-6: done in #113 (drill daily, #155)

### Found, not fixed

- **Nothing asks for a step; the price store's door and his bot key are missing.** Rounds are once a day, orders can go late, an idle Gateway is not told (cards). Unseen at the real Gateway: a fill, a triggered stop, a sale, a part fill.
- **A stop's level is kept only at the broker; a refused order costs 15 s;** a fill on a day the desk never read the broker is in no later answer.
- **Stale words:** `manifest.toml` says placing "is not built", running's line omits the drill; `desk/gateway.py` says "nothing calls it yet".

## DATA

Last updated: 14 November 2026 (folds #84, #85, #87, #89, #96, #97, #175, #180).
### Where it is
The twenty lines (22 on the master until SPY and QQQ leave; VUAG, EQQQ, IDTL in, ISA and retail flags,
yardstick VUAG, #85), one archive client, one store, both calendars to 2027 with hours (#87). Research reads
all 1,065 through `universe.read` (#84; the store still parks 201); the grid does not yet (R-DATA-7). The
fast store `desk/bars.py` (#89) holds five-minute bars, 74,845 real ones saved 13 Nov (#97). Members of the
S&P 500 and Nasdaq 100 since 2010 (#96). The old desk's five-minute bars are a head start (#175,
`lab/headstart.py`): each kept with its source, a fresh bar wins; proven on a copy, NOT yet run on the real
store (waits for R-RUNNER-10, `market.db`). Open boxes stand in working order, keeper first (#180).
### Next step
data-keeper (R-RUNNER-7: the archive's delay, the file kept open, the "price of the moment"); then the head
start on the real store after R-RUNNER-10; its remains: daily bars (calendar before 2010, adjusted against
as-traded, R-RUNGS-5/9), parquet stores (pyarrow, his), 3LGO, research-list bars. Then data-isa-twins
(waits on R-DATA-10/11), data-members, data-research-home.
### Done for other lanes
- R-MONEY-1: done in #47; R-MONEY-2: done in #60; R-PAPER-6: done in #175; R-GRID-4: done in #175
### Requests to GRID
- [x] R-DATA-1: done in #73
- [ ] R-DATA-7 (later, opened 2026-11-13 20:20 UK): a cell reads `universe.read(root, line).bars`, not
  `store.read`, and keeps `History.moves` and `.rescaled`.
- [ ] R-DATA-10 (blocking, opened 2026-11-13 21:45 UK): `test_lab_batch.py`, `test_lab_cell.py` look SPY and
  QQQ up in the master by name; name lines that stay (AAPL, NVDA) so SPY and QQQ can leave.
### Requests to MONEY
- [x] R-DATA-4: each `Line(...)` in its tests states its UK tax.
- [ ] R-DATA-3 (later, opened 2026-11-13 18:15): the day run reads the archive through `archive.gather` and
  hands `store.prepare` its answers whole, so a refused line parks with its reason.
- [ ] R-DATA-6 (later, opened 2026-11-13 19:20 UK): scene 5 reads `CLEAN`; `HISTORY` is the same, and goes.
- [ ] R-DATA-12 (later, opened 2026-11-13 21:45 UK): `day.run` reads "simply holding the market" from
  `lines.YARDSTICK` (VUAG); nothing is bought in the ISA on a line whose `isa` flag is not yes.
- [ ] R-DATA-13 (later, opened 2026-11-14 12:25 UK): `test_watch.py` line 58 names its source,
  `bars.writing(tmp / "bars.db", bars.Source.ARCHIVE)`, so every round must name one.
### Requests to PAPER
- [x] R-DATA-5: each `Line(...)` in its tests states its UK tax.
- [ ] R-DATA-9 (later, opened 2026-11-13 20:20 UK): a read-only question for a line's newest five-minute
  bars at `desk/paper.py`, and whether the paper account gets live or delayed data.
### Requests to RUNGS
- [ ] R-DATA-8 (later, opened 2026-11-13 20:20 UK): a verdict states how many trades were held through a
  day in `History.moves` (about a hundred London bad prints), shown with and without them.
- [ ] R-DATA-11 (blocking, opened 2026-11-13 21:45 UK): `test_lab_rung.py` prices a dollar trade on "SPY"
  from the master; name a US line that stays (AAPL) so SPY can leave.
### Found, not fixed
- **UK tax (NS-05).** Five London products unseen on a contract note; London shares 0.5%, unchecked.
- **Operator:** IB1T (Bitcoin) is not ISA-holdable (crypto notes shut to new ISA purchases from 6 Apr 2026).
- **Research:** today's members only (BT-09); scale changes under the store's belief are UNI-07; WWH, SHC, EDV,
  ROSE read false losses. Member record (#96): one unofficial source; `members.on` raises for FTSE350, ETFS.
- **The store:** nothing fills `Line.real_moves` or `.suspended`; calendar ends 2027; nothing runs `bars.keep`
  nightly until the keeper; 3% of busy reads pass 50 ms; the bars benchmark fails on a saturated disk.

## GRID

Last updated: 14 November 2026 (a hung pass of the week is now ended at 48 hours, #125).
### Where it is

Built and proven: the cell, the batch, the fast grid engine, a key per rung, the auto-tune
(`lab/tune.py`), the pass and the hourly week (`lab/sweep.py`). A pass: 5,325 cells in 2 to 4 min.

### Next step

grid-week: the seven-day run is going (pid in `%KESTREL2_DATA%\grid\week.pid`; moved off C:\tmp at 12:13 on 14 Nov,
unbroken). Nothing to build. On or after 20 Nov 23:45 UK read `sweep.unbroken(Path(KESTREL2_DATA))`: 7 days ticks it.
If it died, restart within the hour, at below-normal priority, from `C:\Users\mtrem\PYTHON\kestrel2_lanes\gridweek`:
`python -B -m lab.sweep %KESTREL2_DATA%\grid\store %KESTREL2_DATA%\grid\cells %KESTREL2_DATA% --days 7`.
grid-declared can start now (it waited only on the shared file).

### Done for other lanes
- R-DATA-1: done in #73
### Requests to MONEY

- [ ] R-GRID-1 (later, opened 2026-11-13 18:15): the five rules at other settings in
  `desk/strategy.py`; the grid runs the published five until then (canon B2).

### Requests to RUNGS

- [ ] R-GRID-2 (later, opened 2026-11-13 20:04 UK): make each cell from a Line in
  `test_lab_rung.py`, `test_lab_luck.py`, and price in `lab/rung.py` with `c.line`. Then GRID drops `Cell.symbol`.
- [ ] R-GRID-3 (later, opened 2026-11-13 21:10 UK): stamp each verdict with `record.key.rung("lab.rung")`
  and each luck correction with `.rung("lab.luck")` in `lab/rung.py`; include the capital setting
  and exchange rate in what a kept verdict is found by. Needed before any verdict is kept.

### Requests to DATA

- [ ] R-GRID-4 (later, opened 2026-11-13 21:35 UK): a public "UK clock time of a moment" in
  `desk/venues.py`, so `lab/tune.py` drops its own summer-time rule.
- [ ] R-GRID-5 (later, opened 2026-11-13 22:20 UK): the research store's home (data-research-home)
  built on this PC (the first pass used a scratch copy); R-DATA-7's second half is still owed.

### Found, not fixed

- **The grid refuses runs of equal closes**; the desk's engine decides them, slower. Not yet counted.
- Grid breaks no series found can show (Supertrend band, Bollinger past 2**53, Wilder window, band margin).
- Cell/batch: key leaves out Python version, paths, capital and exchange rate. Unit-test lines equal product lines.
- Tune: the proof uses one worker; priority and kill-on-exit untested; batch size follows the last batch only.
- Week: a pass over 48 hours is cut and logged failed, so a sweep needing more fails LAD-10 (grid-weekend); a torn `week.jsonl` line needs hand-mending; results grow ~9 MB a day
  (pruning owed, R-GRID-1); an outside pass on the same folder, a PC restart not followed within the hour (nothing restarts it),
  or the copied store `%KESTREL2_DATA%\grid\store` cleared breaks the run (data-research-home fixes the last).
- Log counts tickers as "cells"; refused cells uncounted; busy flag stale if a pass is killed outright or cut at its limit.
  Scratch copies owed removal: `.claude/worktrees/` helpers, `C:\tmp\unebreaks`, `C:\tmp\unedriver`.

## RUNGS

Last updated: 14 November 2026.
### Where it is

Rungs proven on made-up prices only: first (`lab/rung.py`), luck, folds, trials, deflated Sharpe, plateaus,
regimes; built but called by nothing yet: author's result (`reproduce`), promotion, market rung, book
concentration (`bets`, #136), stress (`stress`, #140), indicator tables (`published`, #145, #154: 250 numbers).
The first rung refuses a rule with an author's figure on file until reproduced (#139).
**No winner on real prices is to be believed yet; no real author's or replication's figure is on file.**

### Next step
Open boxes (PLAN): rungs-trustworthy (name market rung; wire bets, stress), rungs-indicators (R-RUNGS-6, 12).
**rungs-reproduce is BLOCKED, hand it out no more** (#143, #149, #169, #186): no book is bought (his ruling, 14 Nov);
a replication stands in for an author's figure, labelled second hand (#169). Best free figures are in DECISIONS;
none on file. Waits on SPY from 1993 (R-RUNGS-5, 9), Double 7's as a rule (R-RUNGS-10), RSI-2 buying under 10
(R-RUNGS-14), the index from 1983 (R-RUNGS-13); then `folds`/`regime`/`stress` pass reproductions on; a person
reopens each page before a figure goes on file. Unit tests stay at the product's size. Ruled 14 Nov: concentration on every report.

### Done for other lanes
- R-DATA-11, R-RUNNER-5, R-RUNNER-3: done in #186 (rungs' tests price dollar trades on AAPL and NVDA; notes out of `lab/reproduce.py`)

### Requests to MONEY
- [ ] R-RUNGS-6 (blocking, 01:20): the indicators of `desk/strategy.py` public and by name (STR-14).
- [ ] R-RUNGS-12 (blocking, 07:55): narrows R-RUNGS-6 to a public RSI and Bollinger lower band; keep `_Window`,
  `_Wilder`, `_Rsi2`, `_Supertrend`, `_gain`, `_loss`, `_range` meanwhile.
- [ ] R-RUNGS-7 (later, 01:50): the day's run reads each candidate's `promotion.standing`, buys nothing for a killed one.
- [ ] R-RUNGS-8 (later, 01:50): `orders.strategy_of` refuses an unreadable id, naming it.
- [ ] R-RUNGS-10 (later, 04:50): Connors' Double 7's as a desk rule (first reproduction's rule).
- [ ] R-RUNGS-11 (later, 04:48): the gap loss limit (STP-10) one named number in `desk/orders.py`.
- [ ] R-RUNGS-14 (later, 14 Nov 10:05): RSI-2 able to buy under 10 as well as 5 (a setting), for the one SPY test with exact dates.

### Requests to GRID
- [ ] R-RUNGS-2 (later, 13 Nov): the declared sweep enters every cell in the register before the batch runs.
- [ ] R-RUNGS-4 (later, 00:35): a kept verdict's key takes in the rates it was priced with.

### Requests to DATA
- [ ] R-RUNGS-3 (blocking, 00:35): a kept daily pounds-per-dollar rate for every research day.
- [ ] R-RUNGS-5 (blocking, 01:20): SPY and US sessions back to January 1993, saying if dividend-adjusted.
- [ ] R-RUNGS-9 (blocking, 04:50): with R-RUNGS-5, SPY from 29 Jan 1993 kept as traded and adjusted, labelled.
- [ ] R-RUNGS-13 (later, 14 Nov 10:05): the S&P 500 index from 1983 to Feb 2013 as a line with daily closes and US sessions.

### Found, not fixed
- **Nothing calls the new rungs yet**; no settings on rules, no regime weather (REG-01); `luck.correct` is a
  door beside the register. **Reproduction:** Bollinger, 50/200 cross, Supertrend have no author's test (ruling owed).
- **Promotion:** fall sees sold shares only; `DEEPEST` belongs to the A-GATE. **Market/stress:** calm-storm
  alternation passes a rider twice as often; "days end at first unjudged trade" lives twice, belongs in `rung.py`.
- **Bets:** a young line (<120 moves) stops it; clusters near 0.5 flip year to year. **Indicators:**
  `published.py` at its 400-line cap; RSI ratio, band line, carried band unheld; no fresh-low table for the channel.
  Scratch owed removal in `C:/tmp`: repro*, promo*, market*, bets*, rungs*, ind*.
