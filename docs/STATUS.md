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
Last updated: 20 November 2026 (#1102, #1108, #1117, #1119 folded).
### Where it is
Scenes 7 of 7. Built: the five rules (each takes its settings, #240) and `ema_9_21`; sizing, cost model, gate; pretend broker; send path, ledger, book (a corrected fill is one fill, #288; a repeated order id is new, #297; a disconnect mid-send keeps the going note so the next send cancels the desk's working order first, #1008; a disagreeing place halts buying, cancels working buys through `halt.stop` and tells him, #290, #1031); the day (no buy on a no-ISA or non-retail line, #278, #516; none for a killed strategy, #519; heat on each record, #472); kill switch, halts, crash watch (nothing calls it), SimCity (each phase under a 2-hour limit that names the stuck line, #936; the real hang's cause is unread, a card to make the stress replay's slicing incremental if the next stall names it; `--soak` fresh seeds #332; round trips and keeper store #370, #375; deep run ends in stress and lifecycle lines, calibration NOT RUN #474). Gate: day and week loss, new lines, Standing and underlying exposure on the send path, drawdown alert told (#467, #632, #661), underlying cap 40% (#564), `GAP_LOSS` 5% (#506); correlation cap 0.90 on the send path (#698); volatility sizing is in `desk/risk.py`, not wired into `orders.size`. `orders.stop_under` is the one stop level (#573); the cost model is in `orders_parts.py` (#881). SimCity has the stale-store scenario (venue bars a session short; the door must refuse, #955), the parked-yardstick scenario (VUAG's bar missing for a session: the day is refused naming it; the long test world is seed 1 since the unheld scenario, #1000), a bar-less line in the gap is a named FAULT that turns the night red (#945), the cancelled-unfilled scenario (#884), the market unheard for an hour (blind told once per hour, #924), the live keeper's unheld one-minute bars (each line named stale, not a LookupError, #1000) and halted and outside-ISA scenarios (#895, not yet in `simcity.py` EVENTS; repeated order ids still taken as new by the pretend broker). `strategy.SWEEPS` and `VARIANTS` list each rule's settings to try, nothing new trades (#904). `desk/intraday.py`: engine core, backtest and step in parity, `today` over an empty rule registry (#557, #649); `session(path, line, span, day)` reads a venue session's store bars as Candles (source "store", #916, R-RUNNER-199 done). Strangers sold, unreached signals listed (#683). Stops move to 10% under the fill in `day.run` (#611). `day_parts.py` (#653), `day_money.py` (#661): splits. `python -m lab.slippage` (#466). `book_parts.py` (#576), `strategy_parts.py` (#586), `simcity_census.py` (#590), `simcity_parts.py` (#796, simcity.py 334 lines): splits. SimCity lives shares beside the book under a stop (`simcity_incidents.beside`, #834). A strategy declaring a holding period is sold out of after it (`strategy._run`, STP-11, #845; the five declare none). Next in money-time-gaps: choose each hold limit (golden days move, needs his approval), call `gapped` at the stop fill and stand down, age from the book's fill date. Twenty-four eponymous rules (R-RUNNER-60 to 80, 88), the paper desk trades none. `desk/simcity_faults.py` (#1035): the broker fault matrix as data, 305 cells, 2 built (2110 and 2157 after accept; `Fault.LINK` on the pretend broker), `summary()` counts built vs not; an unbuilt cell raises NotImplementedError. SimCity has `unbarred` (`simcity_incidents.py`, #1052, R-RUNNER-318): no bar for the session before the day, the conformance plan refuses naming line and session (`_last` raises), green, red if an older close is used; the refusal is kept (R-MONEY-56 would leave the line out instead). `desk/handpark.py` (#1117): `parked.csv` (symbol, who, why) in the desk's data folder; `day._buy` sends no order for a listed line (blocker GATE); R-RUNNER-401 auto-park would write rows into it. `book_parts.keep` writes through a uniquely named temp file per writer (#1119). Conformance cost is a kind in the book (#534); `book.conformance_cost(root, lines)` is public with a SimCity promise (#763), PAPER to call it from `desk/conformance.py` (R-PAPER-29).
### Next step
money-restop waits on R-MONEY-18, R-MONEY-31 (the lost-stop list in `desk/messenger.py` is PAPER's, R-RUNNER-291); the Pretend put-back, `put_stop_back`, is on main (#758). R-MONEY-54 not done (#1046): needs PAPER's `desk/running.py` and `desk/goflat.py` (R-MONEY-57); plan in docs/PLAN.md. R-RUNNER-392 remains 303 cells, one row at a time; hooking `summary()` into the SimCity night needs desk/simcity*.py. Next for MONEY: **R-MONEY-40** `desk/sent.py` written before `broker.place`, withdrawn only on Disconnected/Refused, atomic, with the SimCity "no order reached the broker twice" violation (claim also `tests/unit/test_simcity.py`, `manifest.toml`; design in #297); volatility sizing into `orders.size` waits on the weather box (his 16 Nov "record first, act last"; R-RUNNER-147); R-RUNNER-220 live wiring waits on R-MONEY-49; intraday into the day's step waits on PAPER's intraday-step (R-RUNNER-199). R-RUNNER-127 held (15 of 21 rules not yet spec rows; coordinator's branch). Callers still use `book._write`, an alias of `book.keep` (R-PAPER-7). A desk not restarted before the next open can end short.
### Done for other lanes
- R-PAPER-2: done in #64; R-RUNGS-1: done in #101; R-RUNGS-6, R-RUNGS-12: done in #185; R-PAPER-9: done in #282; R-PAPER-10: done in #285; R-RUNNER-44: done in #224; R-RUNNER-48: done in #231; R-RUNNER-84: done in #257; R-RUNNER-88: done in #280
- R-RUNNER-60: done in #247; R-RUNNER-61: done in #256; R-RUNNER-62: done in #261; R-RUNNER-63: done in #246; R-RUNNER-64: done in #258; R-RUNNER-65: done in #272; R-RUNNER-66: done in #262; R-RUNNER-67: done in #273; R-RUNNER-68: done in #251; R-RUNNER-69: done in #266; R-RUNNER-70: done in #269; R-RUNNER-71: done in #265; R-RUNNER-72: done in #250; R-RUNNER-73: done in #264; R-RUNNER-74: done in #267; R-RUNNER-75: done in #271; R-RUNNER-76: done in #248; R-RUNNER-77: done in #276; R-RUNNER-78: done in #274; R-RUNNER-79: done in #277; R-RUNNER-80: done in #275
- R-PAPER-5: done in #288; R-PAPER-11: done in #290; R-PAPER-12: done in #289; R-PAPER-15: done in #291; R-PAPER-14: done in #516; R-GRID-1: done in #240 (part 1 of the sweep, #904); R-RUNNER-338: done in #880; R-RUNNER-345: done in #881; R-RUNNER-323: done in #884; R-DATA-6, R-DATA-12: done in #522 (refuse on a recorded no; an unrecorded flag waits on R-MONEY-44)
- R-RUNNER-129: done in #332; R-RUNNER-176: done in #370; R-RUNNER-181: done in #375; R-RUNNER-156: done in #467, #661; R-RUNNER-265: done in #653; R-RUNNER-159: done in #472; R-RUNNER-145: done in #466; R-RUNNER-214: done in #534; R-RUNNER-233: done in #576; R-RUNNER-238: done in #586; R-RUNGS-8: done in #479; R-RUNNER-292: done in #758; R-RUNGS-11: done in #506; R-RUNGS-14: done in #508; R-PAPER-29: done in #763 (ledger half), #824; R-DATA-53: done in #824; R-RUNNER-287: done in #796; R-RUNNER-247: done in #834; R-RUNNER-248: done in #924; R-RUNNER-377: done in #945; R-RUNNER-314: done in #955; R-RUNNER-315: done in #972; R-RUNNER-389: done in #1008; R-RUNNER-316: done in #1000; R-RUNNER-392: done in #1035 (part 1, matrix and two cells); R-RUNNER-318: done in #1052; R-RUNNER-397: done in #1117; R-PAPER-17: done in #1119
### Requests to PAPER
- [ ] R-MONEY-53 (later, opened 2026-11-17 UK): the morning message in `desk/messenger.py` carries the day's lost-stop list (stop, shares, level) beside `halt.listed`, so a stop lost by hand reaches him the same day (R-MONEY-18, R-MONEY-31).
- [ ] R-MONEY-49 (blocking, opened 2026-11-17 00:00 UK): call `restop.move(desk.root, broker, lines)` after `day.trade` in `desk/running.py` `_round` and extend `tests/unit/test_running.py`'s scripted gateway; finishes R-RUNNER-220 on paper (#611).
- [ ] R-MONEY-50 (later, opened 2026-11-17): `Pretend.place` for a Sale leaves a resting stop at its shares when the stop does not cover them (`desk/broker.py`), so SimCity's stranger drill can use lines the desk holds (#683).
- [ ] R-MONEY-7 (later): a typed command calling `kill.pull`, sending `Killed.words()` to Telegram. R-MONEY-8 (blocking): paper day calls `day.trade`/`day.publish`, never `day.run`; done in #152.
- [ ] R-MONEY-9 (later): a stop's fills get the order's id plus "-stop". R-MONEY-10 (later): in conformance set paper fills beside `orders.charges` and the 0.05% spread. R-MONEY-11 (later): say when you hold `desk/clearance.py`.
- [ ] R-MONEY-17 (blocking): no paper sale unattended while a stop rests under the same shares, unless tied at the broker (#163); record in conformance what paper does.
- [ ] R-MONEY-18 (later): the morning message carries `halt.listed(root, day)`, every day's `halt.said(root, day)`. R-MONEY-19 (later): a typed command to call and lift a halt. [x] R-MONEY-30: paper put-back done in #657 (`running.recover`); a Pretend door remains (R-MONEY-51). R-MONEY-31 (later): with R-MONEY-18, the day's list message includes its lost-stop entries.
- [ ] R-MONEY-20 (later): `test_messenger.py` states each Record's `halted`, `stopped` (say `(), 0`); the evening message says when a day does not count. R-MONEY-21 (later): `test_running.py` (line 213) keeps Friday's record through `day._row(day.Record(...))`. R-MONEY-22 (later): say if `Broker.place` refusals need a blocker of their own.
- [ ] R-MONEY-23 (later): reword `desk/placing.py` (lines 269-272 too, "no cancel either", stale since #285) and its `manifest.toml` line: a desk that died mid-send asks the same cancel through `book._settle`. R-MONEY-24 (later): keep the day's check and `recover` before every round; say if you would rather the send path called one recovery.
- [ ] R-MONEY-25 (blocking): the unattended step calls `watch.look(root, fast store, daily bars by line, now, post)` every step, every hour, BEFORE its round of orders, and decides if London's morning round waits for the 08:05 bar.
- [ ] R-MONEY-26 (later): a messenger call sending again what was never delivered. R-MONEY-27 (later): the halt-lifting command names him (`by=halt.OPERATOR`), with a command for his word against the market.
- [ ] R-MONEY-55 (blocking, opened 2026-11-20 12:00 UK): in `desk/goflat.py` replace `halt.call` with `halt.stop(root, broker, now, why, BY)`; step already holds the broker. [ ] R-MONEY-56 (blocking, opened 2026-11-20 11:00 UK): `desk/conformance_parts.py` `_last`/`plan` raises for the whole run when one line has no bar of the session before (17 Nov SMGB); leave that line out and plan from the rest, so the plan survives one bar-less line (#1052 kept the refusal; his option b). [ ] R-MONEY-57 (blocking, opened 2026-11-20 13:00 UK): claim `desk/running.py` and `desk/goflat.py` with R-MONEY-54 so `watch.look` gets a broker door (`running._paper`) and goflat calls `halt.stop` (with R-MONEY-55). [ ] R-MONEY-58 (blocking, opened 2026-11-20 19:00 UK): finish R-PAPER-35 (session field on main, #1102): `session=` on the Sales in `desk/conformance_parts.py` and `desk/goflat.py`, then `placing.Paper._cleared` compares `list(last)` to `[order.session, now.date()]`. [ ] R-MONEY-59 (later, opened 2026-11-20 20:00 UK): `desk/watch.py` PARK text says the desk cannot park one line; it can now (`desk/handpark.py`, #1117), update the wording.
- [ ] R-MONEY-32 (later): `desk/command.py` rates use `book.rate(root, "USD", day)`, falling back to the archive on ValueError; or move onto `carry.pounds_per_dollar` (#224).
- [ ] R-MONEY-36 (blocking, opened 15 November 2026): catch `book.Alarm` in the day's send path (`desk/day.py` or `desk/messenger.py`) and message him its words once. R-MONEY-38 (later): `reports.fills` collapses a fill and its correction in one reading (keeps the highest version) instead of raising; the ledger now does (#288).
- [ ] R-MONEY-47 (later): `desk/running.py` passes `killed=` to `day.trade` from `lab.promotion` standings, read outside desk/ (R-RUNGS-7, #519). R-MONEY-39 (later): the same file passes `tell=messenger.send` to `day.trade` so a disagreeing place reaches his phone (#290).
### Requests to MONEY
- [ ] R-RUNGS-29 (blocking, 19 Nov 23:30): let `tests/guards/test_lanes.py` take a lane's owned modules from the merge-base manifest and allow removing a module's own manifest line, so R-RUNNER-191 (b) can delete lab/rung_folds.py (a guard change; recommended, outside RUNGS's claim).
- [ ] R-MONEY-54 (blocking, opened 2026-11-19 20:10 UK): wire `desk/watch.py`, `desk/goflat.py`, `desk/book.py` to `halt.stop` so a real halt cancels working buys (send path done #1031; `desk/goflat.py` is R-MONEY-55, `desk/watch.py` looks before the broker exists in `running._work`, so it needs a broker passed in or a cancel after the look; #871).
### Requests to DATA
- [ ] R-DATA-60 (blocking, 2026-11-20, #950): add `Source.ROLLUP_5M = 'rollup:5m'` to desk/bars_schema.py (widen the card's claim to it) so R-RUNNER-217 step 2 can be built.
- [ ] R-MONEY-3 (later): a daily rate, pounds per dollar, in the store. [x] R-MONEY-15, R-MONEY-16: done (#163, #150). R-MONEY-12 (later): on the master, the market's lines: the yardstick's twin (VUSA), one in New York hours.
- [x] R-MONEY-28 (done in #536, #740, #769; re-verified 20 Nov): the keeper writes each line's ended five-minute bars to the fast store every five minutes in trading hours, VUAG first, the day's last bar included; and says how late a bar lands (the watch's 20 minutes). R-MONEY-29 (later): the keeper or monitor tells him when a whole venue is not heard from.
- [ ] R-MONEY-35 (later, opened 14 November 2026): a daily advances/declines series for the US market, so Zweig's breadth thrust (#275) can run on real days. R-MONEY-48 (later): delete `HISTORY = CLEAN` in `tests/scenes/rehearsal.py`; nothing reads it (#522).
### Requests to GRID
- [ ] R-MONEY-41 (later): the engine takes settings (`strategy.decide(bars, settings)`); the grid sweeps them once its cell matches the engine at those settings (#240). R-MONEY-44 (blocking): `tests/scenes/rehearsal.py` Lines need `isa=True`, then `day._buy` refuses any line not recorded yes (#278).
### Requests to RUNGS
- [ ] R-MONEY-33 (later): ladder, cells and fast grid also run `strategy.WIRING` names (a grid twin for `ema_9_21`) and the `EPONYMOUS` rules (R-RUNNER-87); promotion keeps refusing the first.
- [ ] R-MONEY-34 (blocking): `lab/rung.py` and `lab/ladder.py` use `desk.carry.pounds_per_dollar` (R-RUNNER-45); F1: 32 US cells fail on 2025-04-21.
- [ ] R-MONEY-13 (later): the first rung prices each leg with `orders.charges`; a sale is charged as a purchase. R-MONEY-14 (later): AG-04 must not add the records' market column.
- [ ] R-MONEY-37 (later): R-RUNGS-10 needs one session claiming `desk/eponymous_connors_double_7.py`, `lab/published_epon.py` and its test together (box money-connors7 waits: operator).
- [ ] R-MONEY-43 (later): a lab/ command printing "Calibration: ..." (each rung's pass rate on the night's noise worlds) for the deep run to append; SimCity prints "NOT RUN" until then (#474).
- [ ] R-MONEY-45 (blocking): the other 15 eponymous rules become catalogue rows so R-RUNNER-127 can delete the files; R-MONEY-46 (later): RUNNER hands spec-epon those 15 (#465, #468).
### Found, not fixed
- Costs: spread and slippage assumed; no clock on the day path (R-MONEY-8); `desk/halt.py` still says only the kill switch cancels. Kill switch time in `book.send` is the wall clock (#285).
- Watch (#172, blind after 15 min without a bar #880; why VUAG's 17 Nov 09:25 bar was refused is undiagnosed): no market read after London shuts; `halt.lift` defaults to the operator; `halt.stop` cancels working buys (#871) and the send path calls it (#1031); goflat does too (#1066, R-MONEY-55); watch does not (R-MONEY-54). Lost stop (#191): kept level unrounded; `book.Reckoning` untyped.
- SimCity: the deep run on the real store is unconfirmed after #231; no halted day or overnight death lived. TD Sequential's countdown cancel is untested (#274). Eponymous rules: published figures unchecked, several without a blind review.
- `day.py` counts the ledger by length: a correction after a day's record is not re-priced. SimCity soak names the first red world per promise, not all. `test_lab_headstart` fails on a PC without tzdata (unrelated). `GAP_LOSS` is measured (`orders.gapped`, #845) but acted on nowhere yet (money-time-gaps).

## PAPER

Last updated: 20 November 2026 (folds #215 to #1026, #1024, #1066, #1097).

### Where it is

Built: supervisor pulls main at the safe point (#752), contract request carries exchange, currency, ISIN (#706), pound from IBKR first (#716), `paper.CLIENT`/`APART`/`current` gone (#733), messenger (hourly P&L, kill/halt line, email door not yet wired), step, drill, supervisor (step registered, `tell`), conformance (ids, gate refusal, tape with the soak folded in, #766, Door), go flat, streak, records_kept, t212 (read-only), stop moved to the fill each round, recover puts back a lost stop (R-MONEY-30). Conformance Mon 16 Nov: every difference fixed; the stop step is judged on fills and holdings (#779, needs the next live US run to confirm 6 of 6); evening message names each lost stop (#805) and a stop's fill with its money (#874), the morning one the stops lost and still to be put back (#885); `paper.READ_ONLY` pins the bars question to port 4002 (#793). Held lines a round cannot judge are told with reason and stop (#843); a buy the desk withdraws is told so (#854); a market order waits 120 s (`paper.FILL_SECONDS`, #860) and its sent/accepted/fill/cancel times are kept in `order_times.csv` (#862); the rehearsal books no fill on a line the account held when it began (#909: `reports.ours` takes the symbol; no check yet that an order is one the desk did not send, which would need `desk/command.py`). Conformance's action names each order once with its total shares, fills summed; prices are not judged, a differing kind or total still fails (#1026; the stop step's fixture now has the real -18). Gateway link news 1100, 2110, 2157 is `Disconnected` (a buy sent just before it is received-unknown, its note kept, kill switch not turned on; #1024). Unseen: a part fill; a true stop trigger; t212 shapes never met the real service; `paper.newest` (R-DATA-9) never met the Gateway.

### Next step

R-RUNNER-348 (`Paper._cleared` reads the date from `order_id[:8]`) waits on R-PAPER-35: add a date to Order and Sale, then read it, tests first. R-PAPER-28, -29. Drop the unused `ended` branch of `action(said, ended)` in `desk/ended.py` (needs a claim). Conformance sizing (R-RUNNER-281): `desk/conformance.py:242` must pass `root` to `plan(...)` as `home`, then the archive branch goes (needs a claim naming it). Live check that the gateway answers IDTL (R-RUNNER-278). paper-supervised, paper-cards, paper-extras, paper-backups wait: operator. Coordinator deletes `desk/conformance_soak.py` and its manifest row (non-lane PR, R-RUNNER-285).

### Requests to MONEY

- [ ] R-PAPER-35 (blocking, opened 20 Nov): a session-date field on Order and Sale in `desk/orders.py`, set at every constructor (day, goflat, conformance_parts, simcity, kill), so `Paper._cleared` stops reading `order_id[:8]` (R-RUNNER-348).
- [ ] R-PAPER-4, -7, -8, -13, -18, -19, -20 (later, 13-14 Nov): `book.differences` names an entry at no shares beside one with them; one public keeper of dated records (half done, #301); the day's run collects fills at day's end; the pretend broker refuses a repeated order id like the real one; a cut-off for a late buy; public "sessions owed a record" in `day.py`, "day an order is dated" in `orders.py`; `kill.py` public "drill made this day", word `kill.Failed` for him.
- [ ] R-PAPER-17 (later, 14 Nov): `book._write` has one temp file and no lock; two writers gave an unreadable record (kill switch, `running.csv`). Own temp name or one writer.
- [ ] R-PAPER-26 (later, opened 15 Nov): `watch.look` returns what it read even if a message is undelivered, so a down phone door holds no round.
- [ ] R-PAPER-27 (later, opened 15 Nov): move `messenger.EVENING` (21:05) after the day's record (about 21:40 UK) so it tells the day just recorded.
- [ ] R-PAPER-29 (blocking, opened 16 Nov): ledger kind 'conformance cost' in `desk/book.py` (client 223 commission and spread through the one ledger; trading P&L reported without it); PAPER then feeds it from `desk/conformance.py`.
- [ ] R-PAPER-30 (later, opened 16 Nov): R-MONEY-10: real VUAG buy filled 0.09 below the pretend close, sale 0.14 below; size the 0.05% spread (Monday's files, #686).

### Requests to DATA

- [ ] R-PAPER-3 (later): each line's ISIN a fact on `Line`. R-PAPER-16 (later): IDTL in dollars unlisted at the broker (needs R-PAPER-3); SPY, QQQ can leave the lines. R-PAPER-23 (done in #294; re-verified 20 Nov): say by what minute after each close the store holds the twenty closes.
- [x] R-PAPER-33 (done in #770; re-verified 20 Nov): `history.request` builds a stock contract only; let it ask a forex pair (GBP.USD, IDEALPRO, MIDPOINT) so `command.POUND` is answered by IBKR; until then every rate is named as the archive's (#716).

### Own, to PAPER

- [ ] R-PAPER-25 (later, opened 15 Nov): tie a buy's stop and later sales in one OCA group at the broker once the group fields are proved on the Gateway; then cancel-first (#296) can go.
- [ ] R-PAPER-34 (later, opened 19 Nov): set `paper.FILL_SECONDS` from the measured `order_times.csv` (broker's first accepted time and fill time), once some mornings are kept; why IBKR gave no fill in 30 s (auction?) is uninvestigated.
- [ ] R-PAPER-28 (blocking, opened 16 Nov): wire `messenger.with_mail` and `messenger.summary` into `desk/running.py`, and the runner hands it SMTP_*; else the email fallback (#484) is never used.

### Done for other lanes
- R-RUNNER-26: #215; R-RUNNER-42: #223; R-RUNNER-91: #295; R-MONEY-17: #296; R-MONEY-25: #300; R-DATA-14: #302; R-RUNNER-177: #369; R-RUNNER-180: #373; R-MONEY-36: #385; R-RUNNER-191: #433; R-RUNNER-196: #437; R-RUNNER-197: #444; R-RUNNER-190: #462; R-RUNNER-113: #461 (half); R-RUNNER-207: #471; R-RUNNER-209: #476
- R-RUNNER-16: #484 (door only); R-RUNNER-93: #393; R-RUNNER-210: #492; R-RUNNER-17: #495; R-RUNNER-212: #512; R-DATA-9: #509 and #793; R-RUNNER-161: #502; R-RUNNER-162: #558; R-RUNNER-92: #565; R-RUNNER-223: #572; R-RUNNER-234: #577; R-RUNNER-250: #584; R-RUNNER-251: #599; R-RUNNER-235: #601; R-RUNNER-256: #623; R-RUNNER-255: #645; R-RUNNER-258: #651 (step 1 of 3); R-MONEY-30: #657; R-RUNNER-268: #690; R-RUNNER-278: #706; R-RUNNER-282: #716; R-RUNNER-257: #733; R-MONEY-49 and R-MONEY-36: #741 (already on main); R-DATA-52: #798; R-MONEY-49: #798 (declined, already on main); R-RUNNER-286: #782; R-RUNNER-291: #805; R-RUNNER-308: #779; R-RUNNER-312: #843; R-RUNNER-339: #860; R-RUNNER-342: #862; R-RUNNER-330: #874; R-MONEY-53: #885; R-MONEY-49: #888 and #893 (already on main); R-MONEY-36: #890 (already on main); R-RUNNER-380: #909; R-RUNNER-390: #1024
- R-PAPER-32: #733; R-PAPER-5, -9 to -12, -14, -15, -22, -24 (done, see #288, #282, #285, #290, #289, #516, #291, #215/#393, #302); R-PAPER-6: #175
- R-MONEY-55: done in #1066

### Found, not fixed

- **Unseen at the real Gateway:** a part fill, a true stop trigger; the 08:05 London opening buy cancelled once by the desk's own 30 s wait (#437; now 120 s, #860). While the kill switch is on, go flat sells nothing (R-RUNNER-162).
- **Supervisor:** Windows does not yet start it or `tell`; no kill drill on the real step; seven days not counted; the Gateway's 03:00 restart may show as bad receipts (`messenger.watch` has no caller).
- **Other:** `tape.moved` in `desk/conformance_tape.py` is unused; `desk/messenger.py` is at 349 lines after the split (#782) but `desk/` has 92 of 10,500 lines left; a note over 24 h old is no longer re-sent; the rehearsal docstring says "no market trading" (stale); the pound's IBKR request asks for a share contract, so the archive fills in (R-PAPER-33); `keeper.saved` is stale for every venue if one is not refreshed.

## DATA
### Where it is (17 November 2026, folds #217-#770)
Twenty traded lines (SPY, QQQ reference series, #455, #544); one archive client, spared (#637-#732), its six-hour `alert`
(#671); calendars 1993-2030; daily asks back to 2000 (`archive.SINCE`, #691); two databases (#442, #510), broker first
(#521); the pound from 1993 (#614). Keeper: `--live`, five-minute rounds, `--roll`, receipts, `parked_live` (#530-#701);
keeper and history-pull bars keep the line's currency (#719, #725); backfill; old stores in (#238-#566). Six London lines
clean (#222-#702); an untraded bar gives way to a traded one (#721). Keeper asks IBKR first for every line, a disagreement over 2% recorded not parked (#751); gaps bridged from
five-minute bars (#747); a shelf a hundredth of the archive's put right in the store (#753); history pull asks only 1m-30m
and 1d (#739). 1h, 4h, 1wk rolled locally as rollup:<from> (#760); keeper takes the five-minute round first under half its time (#759); 1m bars parsed as Timed (#757); the pound asked as GBP.USD forex (#770); shelf unit rule on a 95% majority of shared days (#768, IB1T; 3LGO and 2MU unseen, to be checked on the next real round). `desk/store.py` split, its neighbour judging in `desk/store_parts.py` (#764); `lab/universe.py` split, reading rule in `lab/universe_parts.py` (#784); a rolled bar disagreeing with a held one is a stderr FAULT (#780); `python -m desk.quality` daily audit-backfill-reaudit (#797); `desk/coverage.py` scores coverage per line, wired into the quality monitor, which prints "coverage 0.xx" and goes red past 10% of lines parked (#795, #1037, DQ-01; per-lookback from the grid's SWEEPS, #1059; open: second-source part) the quality monitor also rolls up 1h, 4h, weekly and reds a clash with a pulled bar (#811; a line with no 30m bars is skipped). Unfinished: R-RUNNER-216 and -217 (gaps per timeframe against the venue calendar, market_live.db, the runner job), -215, R-RUNNER-350 to -352 (database timeframes, shelf CSV, monitor rollup). Deep history: the store keeps bars from 2000, five real moves recorded (#841, R-DATA-54); the first keeper round must fill 2000-2009 and any park be read. Keeper receipts name each newest bar's source and arrival (#820); it withdraws dropped days (#855, R-RUNNER-311); the writer joins by day, deletes no held day, one price form, corrections on real change only (#801, #861); IBKR asked for every line within ceil(lines/ROOM) calls (#859); no park for a fault older than 400 sessions (#863); a store lock wait is named (#856). Quality monitor: thin sessions on all short timeframes, the finer span that could rebuild one, five-minute against daily volume (#825, #836, #842, #853). Paper Gateway five-minute bars proved live, 7 US lines (#844, #903); data-broker-bars and data-ingest verified done (#915). Bars and faults written whole before either swap (#832). Quality audit counts a closed session of today, so the job is no longer false-red after keeper-roll (#935, R-RUNNER-382); `backfill.fill` takes one ordered (source, ask) list (#930). `Source.ROLLUP_5M` is on main (R-DATA-60, #978); R-RUNNER-217 step 2 (the rollup ask) now needs a card claiming tests/unit/test_quality.py; data-two-stores' remainder (other timeframes' audit, market_live.db, local Stooq and rollup, runner job) lies outside its claim and waits: operator (#934, #938, #947). No free daily advancing/declining series exists (#917): the Zweig row stays out (R-RUNNER-346, R-MONEY-35; waits: operator). Blocking requests R-PAPER-23, -33, R-MONEY-28, -48, R-RUNGS-16 verified on main (#921-#992, R-PAPER-23 again #1038-#1044, R-MONEY-48 #1062); no blocking request is open. Next: the first real `--live` run.
### Done for other lanes
- R-RUNNER-28 #222, -41 #219, -24 #238, -37 #254, -90 #286, -97 #305, -104 #314, -107 #315, -116 #349, -175 #367, -182 #374, -179 #376, -185 #381, -15 #460, -94 #303, -96 #475, -149 #453, -194 #518,
  -11 #514, -211 #530, -178 #532, -189 #541, -157 #528, -221 #548, -218 #547, -224 #574, -236 #591, -254 #612, -12 #629, -264 #656, -266 #666, -263 #660, -270 #701, -269 #715, R-RUNNER-10 #908 (ibkr_store stamps on the venue's clock), -349 #901 (whole headstart pass; -350, -351, -352 remain), -381 #905 (desk/bars.py split to 349 lines), -382 #935, -279 #719, -274 and -275
  #721, -277 #727, -284 #744, -276 #751, -272 #753; R-RUNNER-290 #757; R-PAPER-33 #770; R-RUNNER-288 #764, -289 #784; R-MONEY-48 #783; R-PAPER-23 #294, -22 #505, -16 and -3 #543; R-GRID-4 #338; R-MONEY-28 #536, #740, #769; R-RUNGS-3, -5, -15 #537, -9 #544, -16 #630, #747
- R-RUNNER-387 #996, R-RUNNER-311 #855, -313 #859, -327 #863, -329 #856, -341 #861
- R-PAPER-23: done in #294; R-PAPER-33: #770; R-RUNGS-16: #630, #747; R-MONEY-28: #536, #740, #769; R-MONEY-48: #783 (all re-verified on main 20 Nov; R-PAPER-23 again #1038-#1044, R-MONEY-48 #1062). PAPER's line 161 still lists R-PAPER-23 open in a run-on (pattern 22): PAPER's scribe to strike it.
- Mine, done by others: R-DATA-1 (#73), -4, -5, -6 (#522), -9, -15 (#517, #530), -17, -25, -26, -27, -28, -31, -35 (#652); R-DATA-49 (#814); own R-DATA-19 to -23, -36, -40, -41 done, -24 superseded by the database
### Requests to DATA
- [ ] R-DATA-55 (later, #832): widen data-written-together's claim to desk/store.py, tests/unit/test_lab_universe.py and lab/universe.py so bars and faults live in one file.
- [ ] R-DATA-56 (later, #842): a card claiming desk/bars.py and desk/quality.py to add rollup:<from> sources for short spans and write them where the monitor says "rollable".
- [ ] R-DATA-57 (later, #825, #836): R-RUNNER-217 left: audit market_live.db; yf.download and local Stooq in the backfill order (desk/backfill.py); an adjustment-basis-per-bar fault (#870: the monitor now names a daily series mixed across bases, judged from each bar's source, no column; open: restating it onto IBKR's basis, 1m-30m gaps from IBKR/yf/Stooq, a separate market_live.db audit).
- [x] R-DATA-58: declined (#872): the live store holds every backup day; the 20 differing days (20 Oct-16 Nov, nine US lines) are fresh pulls, old values kept in `correction`. Lifting state/job-keeper.hold is the runner's call.
- [ ] R-DATA-59 (later, #872, waits: operator): decide the daily volume basis for those nine lines (fresh pull about half the old import) by comparing the sum of five-minute volumes to each, then record it in the store.
### Requests to GRID
- [ ] R-DATA-7: a cell reads `universe.read(root, line).bars`, keeps `History.moves`, `.rescaled`. R-DATA-10 (blocking): `test_lab_batch.py`, `test_lab_cell.py` name SPY and QQQ; name lines that stay.
### Requests to MONEY
- [ ] R-DATA-3: the day run reads the archive through `archive.gather`. R-DATA-12: `day.run` takes "simply holding the market" from `lines.YARDSTICK`; no ISA buy where isa is not yes. R-DATA-13:
  `test_watch.py`, `test_pnl.py` name the store "bars.db"; use `keeper.HOT`. R-DATA-30: `lab/slippage.py` reads `bars.daily(home / keeper.HOT, line)`, not CSVs.
- [ ] R-DATA-33: `command.rates` calls `keeper.pound(home, day)`; POUND, DOLLARS from `desk.lines`. R-DATA-45, -47: refuse a buy on a line in `keeper.parked_live(home / keeper.HOT, LINES, now)`; say
  why. R-DATA-46: `conformance.py` picks its refused line from `lines.REFERENCE`, so SPY can leave LINES. R-DATA-48: a per-bar source in the daily store (`store.judge` returns it, `Round.daily` writes
  it); #844: carry a bar's own source label (IBKR or archive) to the store's row so the keeper stops inferring it per round.
- [ ] R-DATA-51 (later, #753): the lane owning `desk/lines.py` sets IB1T to USD (dollar-quoted on the LSE); then the store may read the unit from it.
### Requests to PAPER
- [ ] R-DATA-14 (blocking): wire `keeper.saved(home, day)` and the crash watch's `home / keeper.HOT`; the day's record only once `keeper.target(venue, now)` is past, or the door refuses 25 minutes
  every evening.
- [ ] R-DATA-37: look IDTL up by `Line.isin`. R-DATA-42: `test_conformance_action.py` restores `paper.CLIENT`, `paper.APART`. R-DATA-44: `command.py` drops its own POUND and DOLLARS. R-DATA-50 (later,
  #747): IDTL has no security definition at the broker, so the live round refuses it; needs its ISIN/contract.
### Requests to RUNGS
- [ ] R-DATA-8: a verdict counts trades held through a day in `History.moves`, with and without. R-DATA-11 (blocking): `test_lab_rung.py` prices a dollar trade on "SPY"; name a US line that stays.
- [ ] R-DATA-29, -38, -34, -43: the ladder reads SPY and its sets from `market_history.db`, rates from `keeper.pound`, POUND and DOLLARS from `desk.lines`. R-DATA-39: re-run the 35 waiting cells.
### Requests to RUNNER
- [ ] R-DATA-16 (blocking): `test_check.py::test_at_most_n_full_checks_run_at_once` flaky on Windows. R-DATA-18: keeper to 21:40 UK with logs; schedule the head start, `lab.universe nightly`, audit,
  snapshot, `desk.history_write`, `desk.backfill`; the hourly report calls `desk.archive.alert`, sends its line. R-DATA-32: READY counts desk/ room.
### Found, not fixed
- **UK tax (NS-05).** Five London products unseen on a contract note; London shares 0.5%, unchecked. **Research:** today's members only (BT-09); scale changes under the store's belief are UNI-07.
- **Keeper/collector:** desk/collector.py:199 and desk/keeper_live.py:130 do not yet name a lock wait (#856); IDTL has no security definition at the broker (#844). **Operator:** IB1T not ISA-holdable; data-members, data-isa-twins wait on him. **Store/keeper:** `history.run` checks the desk round once, not per page, its bars not yet re-aligned to the session,
  5QQQ's 2021-22 lost; `backfill.in_currency` alias awaits `test_backfill.py`; `keeper.py` 400 lines; `quality` runner job needs its card ticked; a broker-filled bar is labelled "archive"; archive limits unmeasured
  (#685); `history.lacks` unused (#751); IDTL parks on a missing 16 Nov unless its five-minute bars are held; disagreements not in a stored fault file.
## GRID

Last updated: 17 November 2026 (one bars reader #449; batch.stored reads as research does #618; R-DATA-10 confirmed #626).
### Where it is

Built and proven: the cell (a Line only), batch, fast grid engine and fast spec-row engine (`lab/fast.py`, ~30 times
the desk's), a key per rung that ignores the modules that run it, auto-tune, the pass and hourly week, `--held`, the rule
book with the catalogue's specs, the transfer study (`lab/transfer.py`; a refused line answers REFUSED). The default
pass runs each strategy on its declared universe (22 lines); all-on-all is `--transfer`, never a verdict. A pass reports
its seconds: cold transfer 5,330 cells in 17 min, declared about 8 min, far inside the 48 h weekend (LAD-10 done).

### Next step
grid-week (waits: 2026-11-21): the seven-day run is going (pid in `%KESTREL2_DATA%\grid\week.pid`). Nothing to build.
On or after 20 Nov 23:45 UK read `sweep.unbroken(Path(KESTREL2_DATA))`: 7 days ticks it. If it died, restart within the
hour, below-normal priority, from `C:\Users\mtrem\PYTHON\kestrel2_lanes\gridweek`:
`python -B -m lab.sweep %KESTREL2_DATA%\grid\store %KESTREL2_DATA%\grid\cells %KESTREL2_DATA% --days 7`.
Every other box is ticked. Open: R-DATA-7 (`batch.stored` now reads through `universe.read`, #618; remains: a cell keeping
`History.moves` and `.rescaled` in its record, which changes the cell's record and key), R-RUNGS-2 (declared sweep enters every cell in the register), R-RUNGS-4.

### Done for other lanes
- R-DATA-1: done in #73; R-DATA-10: #391; R-RUNNER-4: #171; R-RUNNER-8: #391; R-RUNNER-19: #197; R-RUNNER-82: #263
- R-RUNNER-89: #281; R-RUNNER-128: #360; R-RUNNER-140: #330; R-RUNNER-164: #397; R-RUNNER-167: #359; R-RUNNER-170: #372; R-RUNNER-112: #449
### Requests to MONEY
- [ ] R-GRID-1 (later, 2026-11-13 18:15): the five rules at other settings in `desk/strategy.py`, each with a grid and
  a name per setting in `transfer.families()`; the grid runs the published five until then.
### Requests to RUNGS
- [ ] R-GRID-2 (later, 2026-11-13 20:04 UK): make each cell from a Line in `test_lab_rung.py`, `test_lab_luck.py`,
  and price in `lab/rung.py` with `c.line`. Then GRID drops `Cell.symbol`.
- [ ] R-GRID-3 (later, 2026-11-13 21:10 UK): stamp each verdict with `record.key.rung("lab.rung")`, each luck
  correction with `.rung("lab.luck")`; include capital and exchange rate in what a kept verdict is found by.
- [ ] R-GRID-6 (blocking, 2026-11-14 10:30 UK): the rungs' tests (`test_lab_rung/trials/bets/regime/reproduce.py`) name
  SPY and QQQ; name lines that stay (AAPL, NVDA) so DATA can take them out of the twenty.
- [ ] R-GRID-7 (later, 2026-11-16 12:00 UK): `lab/cell.py` `rungs()` stats per candidate per module; cache `_file`
  so the import takes seconds, not minutes, on the PC.
### Requests to DATA
- [ ] R-GRID-5 (later, 2026-11-13 22:20 UK): the research store's home (data-research-home) built on this PC.

### Found, not fixed
- **60 of 110 cells failed in the cold declared pass** (#403); cause unread (journals): look first.
- `lab/cell.py` import takes 1-3 min on a loaded PC (R-GRID-7). The grid refuses runs of equal closes (desk engine decides).
- Grid breaks no series found can show (Supertrend band, Bollinger past 2**53, Wilder window, band margin).
- Cell key leaves out Python version, paths, capital and exchange rate. `lab/fast.py` not yet wired into the sweep.
- Rung key still holds batch, folds, published*, shuffle, desk/*; narrowing needs a per-rung declaration in `lab/ladder.py`.
- Week: a pass over 48 h is cut and logged failed; a torn `week.jsonl` line needs hand-mending; results grow ~9 MB a day
  (pruning owed, R-GRID-1); an outside pass, a PC restart, or the copied store cleared breaks the run.
- Flaky `tests/unit/test_bars.py` once under load (#171). Busy flag stale if a pass is killed outright.
  Scratch owed removal: `.claude/worktrees/` helpers, `C:\tmp\unebreaks`, `C:\tmp\unedriver`.

## RUNGS

Last updated: 20 November 2026.
### Where it is
Eleven rungs built, each proven alone (#342-#365, #412). The ladder judges by the first rung, luck, deflated Sharpe, folds (five whole years pooled by
rule, #313), market, stress (20% of capital, #457), regime on the weather (#622) and the shuffle last; costs, ci and cpcv are declared (#438-#445): "rungs built: 3 of 12" (the retail rung, #927, is map row 12, wired into a basket row behind EASED).
Machinery: a cell's key carries its own rule's code (#912); a golden ladder verdict pins the fixture (#919); pooled folds fold each line on its own window, whole years only (#858); one compressed tape per (rule, line) (#378, #555); a pool by fold year sized by free memory (#368, #451); sets read market_history.db only (#562), trade list members only (#569);
EPON (20 rules proven, #308), LEV (#423); the spec book holds rules as rows with a fast engine that also walks position-dependent blocks (darvas_box #799, demark_sequential #790, raschke_swing #773). Easings pre-registered (#567) and switched on with `verdict.EASED` (True, #993): family
trials (#596), basket (#664), scorecard (#589), INCUBATE (#695); the golden verdict re-pinned to the eased answers (#993). Calibration: `python -m lab.calibration` (#693). Weather layers 2, realised volatility (`weather.volatility`, #737), and 3, drawdown depth (`weather.drawdown`, 10% under the 252-session high, #776), and 4, breadth (`weather.breadth`, more than half the lines up, #831), are wired into no verdict; `weather.followed` scores a layer per fold by the next-session return (#813). `weather.edges` gives a layer's edge per fold (#866) and `weather.against_trend` its worst fold beside trend's (#875); a layer joins the regime rung only if it wins (`weather.contest`, #907, scores calm, shallow, broad layers with 3 trials; open, R-RUNNER-205: run it on the real store as a plain-code job, wire winners, then macro). `python -m lab.ladder` says FAULT per rung and exits 1 when over half the cells FAULTed (#892); the set's table is swapped in whole (#868). Blind reviews: #402, #419; judge walk test (#593).
**No winner on real prices is to be believed: SET EPON judged 21,320 cells, none goes forward; every table is PRE-REVIEW. A loss gapping through the stop is unplanted (#402, #409 declined): a no-edge gap rule can pass rung 1 up to 18.8%, the later rungs cut it to 0-2.2%.**

### Next step
Open: rungs-trustworthy remainder (wire the other eight rungs, R-RUNNER-191, which need trials, spread and market bars handed over by the ladder; the Sharpe a trade now has one home, #746; the three-band rule of t has one home, `rung.band` (#772), a mean and its standard error one home, `rung.mean_and_error` (#789), the fold's second judge is gone (#803; Fold/Walked still sit in rung_folds.py, moving them needs a claim with manifest.toml and test_lab_folds.py); next: rung_regimes and rung_bootstrap own bands could read rung.decide/band, float mean/spread in market.py (rung_benchmark.interval done, #827; one home for a mean and its interval, `rung.interval`, #838; rung_dsr's wrapper gone, #848; rung_ci keeps its own bounds, #815); clustered trials (#379) into the verdict; ease-switch-on done: EASED = True, golden verdicts re-pinned, #993), rungs-each-rung, rungs-gate, rungs-spec; spec book: 20 of 21 rules are rows (Mansfield #873); owed: zweig_breadth_thrust (waits R-MONEY-35, no breadth series in any store) (R-MONEY-45, R-RUNNER-219). The table's holding column is built (R-RUNGS-23, #775); other rungs' wiring remains. Ruled: concentration on every report; unit tests stay at the product's size.
**Waiting (hand out no more):** rungs-reproduce (R-RUNGS-5, 9, 10, 13, 14; R-RUNGS-13 BLOCKED ON DATA: no store holds the S&P 500 index from 1983; SPY daily from 1993-01-29 in mark_the_trend.db serves, R-RUNNER-37);
rungs-promotion (R-RUNGS-7; kill numbers need a ladder-passed candidate); rungs-leveraged (inverse lines wait R-RUNGS-21, 22; LEV long half built); rungs-feasibility (needs three ladder-passed rules, from rungs-eponymous); rungs-blocks (sizing blocks, operator); rungs-indicators (operator).
R-RUNGS-29 (guard, outside RUNGS's claim; Option 1 taken, #951, #949, #952) blocks moving Fold/Walked and deleting lab/rung_folds.py.
`Candidate` should also refuse a row listing unrun rungs (recommended: when the first real candidate nears).
### Done for other lanes
- R-RUNGS-31: done in #986 (the pooled run passes the family count; re-verified 20 Nov)
- R-DATA-11, R-RUNNER-5, R-RUNNER-3: done in #186; R-RUNNER-25: #202; R-RUNNER-33: #206; R-MONEY-34: #239; R-GRID-6: #427; R-GRID-2: #504, #846, #922, #980 (verified); R-RUNGS-18: #846; R-RUNNER-331: #858; R-MONEY-13: #600; R-MONEY-43: #693
- R-RUNNER-47: done in #235; -45: #239; -49: #244; -52: #241; -83: #252; -85: #253; -86: #279; -95: #304; -101: #307; -98: #308; -102: #309; -106: #310; -108: #311; -109: #312; -99: #313; -114: #316; -110: #318; -100: #319; -103: #322; -124: #327
- R-RUNNER-117: done in #331; -130: #333; -152: #340; -133: #343; -131: #344; -134: #347; -123: #346; -122: #342; -121: #350; -119: #351; -120: #354; -136: #361; -154: #362; -139: #364; -155: #363; -135: #365; -168: #366; -166: #368; -173: #371; -137: #379; -169: #378; -126: #382; -165: #384
- R-RUNNER-183: done in #405; -187: #409 (declined); -174: #410; -188: #419; -40: #402; -186: #425; -192: #427; -203: #451; -204: #457; -171: #560; -213: #555; -222: #562; -146: #569; -225: #567; -230: #589; -237: #603; -193: #593; -226: #596; -239: #635; -260: #658; -227: #664; -267: #680; R-RUNGS-23: #775; R-RUNNER-340: #868; -332: #892; -205: #907 (part 1); -138: #912; -191: #919 (part a); -384: #942; R-RUNGS-30: #942; R-RUNNER-385: #984; -386: #986
### Requests to MONEY
- [x] R-RUNGS-6, 8, 11, 12 met on main (public indicators #185, `strategy_of` refuses, `GAP_LOSS`); [x] R-RUNGS-3, 15 met by the carry rule and the kept table (#239, #307)
- [ ] R-RUNGS-7 (later, 01:50): the day's run reads each candidate's `promotion.standing`, buys nothing for a killed one.
- [ ] R-RUNGS-10 (later, 04:50): Connors' Double 7's as a desk rule. [ ] R-RUNGS-14 (later, 14 Nov): RSI-2 able to buy under 10 as well as 5 (a setting).
- [ ] R-RUNGS-21 (later, 16 Nov 12:00): let a Line state an inverse fund (leverage -1 to -3), sized and stopped by its magnitude.
- [ ] R-RUNGS-26 (later, 17 Nov): replace the deep run's "Calibration: NOT RUN" with the output of `python -m lab.calibration` (run by the runner, not imported by desk/).
### Requests to GRID
- [ ] R-RUNGS-2 (later, 13 Nov): the declared sweep enters every cell in the register before the batch runs. [ ] R-RUNGS-4 (later): a kept verdict's key takes in the rates it was priced with.
- [ ] R-RUNGS-19 (later, 16 Nov 15:00): `Cell.symbol` still read in lab/cell.py:65, lab/ladder_sets.py and tests/unit/test_lab_tune.py:210; RUNGS's files are clear: drop it.
- [ ] R-RUNGS-25 (later, 17 Nov 05:00): capital and the rate table's version into `lab.cell.Key` (R-GRID-3, last part).
- [ ] R-RUNGS-28 (later, 17 Nov 18:00): `lab/transfer.py:170` calls `ladder.rates(home=data)` (the data folder, where the pound's kept closes live), so they are not asked of the archive each run; its test's stub takes `home`. Meets R-RUNGS-17. RUNGS's own edit was refused by the lane-ownership guard (#852): GRID's file.
### Requests to DATA
- [ ] R-RUNGS-5 (blocking): SPY and US sessions back to January 1993, saying if dividend-adjusted. [ ] R-RUNGS-9 (blocking): SPY from 29 Jan 1993 kept as traded and adjusted, labelled.
- [ ] R-RUNGS-13 (later, 14 Nov): the S&P 500 index from 1983 to Feb 2013, daily closes, US sessions (BLOCKED ON DATA).
- [x] R-RUNGS-16 (done in #630, #747; re-verified 20 Nov): six London lines parked for price steps (2MU, 5QQQ, SGLN, VUAG, EQQQ, IDTL), 3LGO one bar.
- [ ] R-RUNGS-20 (later, 16 Nov 01:45): 24 London lines refused for a day whose open and close both step by the pound's rate; HVPE (2015-09-09), NBPE (2017-05-02), VOF (2016-03-30) changed quote currency and want mending; the rest (AJB, BMY, CMCX, HAS, RMV, BPT, CWR, FOUR) look like real gaps and want naming in the line master.
- [ ] R-RUNGS-22 (later, 16 Nov 12:00): inverse ETFs (SQQQ, SPXU, SH, SDS) in the research list and store, once R-RUNGS-21 allows.
### Requests to RUNGS
- [ ] R-RUNGS-17 (later): lab/transfer.py:170 calls `ladder.rates(home=root)` (GRID's file; see R-RUNGS-28). [x] R-RUNGS-18: `Priced.stopped` is required (#846); montecarlo reading `verdict.gains` declined (it plants a made-up stop-sold gain).
- [x] R-RUNGS-30: `ladder_sets.baskets()` passes the market to `basket.row` (#942); mixed-venue baskets are judged against the first line's venue.
- [x] R-RUNGS-23 (16 Nov 12:00): the table's holding column, `lab.holding.beside` per cell (#775).
- [x] R-RUNGS-27 (17 Nov): `verdict.basket_answer` wired into `basket.row`, INCUBATE listed apart (#742); EASED stays off until card ease-switch-on.
- [x] R-RUNGS-31: `lab/ladder_pool.py` passes the family count to `ladder._one`, so a pooled run works with EASED on (#986).
### Found, not fixed
- **Ladder:** one run at a time; no settings on rules; `ladder.stored` unused since #562; `Cell` key omits capital. **Reproduction:** Bollinger, 50/200 cross, Supertrend have no author's test (ruling owed).
- **Judge:** the planted loss covers a stop, not a gap (above); `test_lab_headstart.py` fails on a PC with old-desk stooq stores. **Promotion:** fall sees sold shares only; `DEEPEST` belongs to the A-GATE. **Stress:** calm-storm alternation passes a rider twice as often.
- **Bets:** a young line (<120 moves) stops it. **Indicators:** `published.py` at its 400-line cap. **Clustered trials:** the days of a set must equal the window (#379). Scratch owed removal in `C:/tmp`: repro*, promo*, market*, bets*, rungs*, ind*, rr188*.
