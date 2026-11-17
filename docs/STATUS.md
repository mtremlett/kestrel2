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
Last updated: 17 November 2026 (49 pull requests folded: gate limits, SimCity soak and deep run, intraday core, book and strategy splits, many RUNGS re-checks).
### Where it is
Scenes 7 of 7. Built: the five rules (each takes its settings, #240) and `ema_9_21`; sizing, cost model, gate; pretend broker; send path, ledger, book (a corrected fill is one fill, #288; a repeated order id is new, #297; a disagreeing place halts buying and tells him, #290); the day (no buy on a no-ISA or non-retail line, #278, #516; none for a killed strategy, #519; heat on each record, #472); kill switch, halts, crash watch (nothing calls it), SimCity (`--soak` fresh seeds #332; round trips and keeper store #370, #375; deep run ends in stress and lifecycle lines, calibration NOT RUN #474). Gate: day and week loss and new lines (#467), underlying cap 40% (#564), `GAP_LOSS` 5% (#506); in `desk/risk.py` correlation and volatility sizing, not in the gate (#478). `orders.stop_under` is the one stop level (#573). `desk/intraday.py`: engine core, backtest and step in parity, no rule trades (#557). `python -m lab.slippage` (#466). `book_parts.py` (#576), `strategy_parts.py` (#586), `simcity_census.py` (#590): splits. Twenty-four eponymous rules (R-RUNNER-60 to 80, 88), the paper desk trades none. Conformance cost is a kind in the book (#534), uncalled.
### Next step
money-restop waits on R-MONEY-30 (box waits). Then: **R-MONEY-42** pass the book's Standing and per-underlying exposure into `gate` in `book.send` and send `halt.drawdown`'s alert (R-RUNNER-156, -158; nothing is enforced on the live path until then); **R-MONEY-40** second half of R-PAPER-13: `desk/sent.py` written before `broker.place`, withdrawn only on Disconnected/Refused, atomic, with the SimCity "no order reached the broker twice" violation (claim also `tests/unit/test_simcity.py`, `manifest.toml`; design in #297); wire `_conformance_cost` and `desk/risk.py`'s correlation cap/sizing into the gate (R-RUNNER-214, -147); R-RUNNER-220 after the restop door; intraday into `strategy.today` and the day's step (R-RUNNER-199). R-RUNNER-127 held (15 of 21 rules not yet spec rows; coordinator's branch). Callers still use `book._write`, an alias of `book.keep` (R-PAPER-7). A desk not restarted before the next open can end short.
### Done for other lanes
- R-PAPER-2: done in #64; R-RUNGS-1: done in #101; R-RUNGS-6, R-RUNGS-12: done in #185; R-PAPER-9: done in #282; R-PAPER-10: done in #285
- R-RUNNER-44: done in #224; R-RUNNER-48: done in #231; R-RUNNER-84: done in #257; R-RUNNER-88: done in #280
- R-RUNNER-60: done in #247; R-RUNNER-61: done in #256; R-RUNNER-62: done in #261; R-RUNNER-63: done in #246; R-RUNNER-64: done in #258; R-RUNNER-65: done in #272; R-RUNNER-66: done in #262; R-RUNNER-67: done in #273; R-RUNNER-68: done in #251; R-RUNNER-69: done in #266; R-RUNNER-70: done in #269; R-RUNNER-71: done in #265; R-RUNNER-72: done in #250; R-RUNNER-73: done in #264; R-RUNNER-74: done in #267; R-RUNNER-75: done in #271; R-RUNNER-76: done in #248; R-RUNNER-77: done in #276; R-RUNNER-78: done in #274; R-RUNNER-79: done in #277; R-RUNNER-80: done in #275
- R-PAPER-5: done in #288; R-PAPER-11: done in #290; R-PAPER-12: done in #289; R-PAPER-15: done in #291; R-PAPER-14: done in #516; R-GRID-1: done in #240; R-DATA-6, R-DATA-12: done in #522 (refuse on a recorded no; an unrecorded flag waits on R-MONEY-44)
- R-RUNNER-129: done in #332; R-RUNNER-176: done in #370; R-RUNNER-181: done in #375; R-RUNNER-156: done in #467 (not yet on the send path); R-RUNNER-159: done in #472; R-RUNNER-145: done in #466; R-RUNNER-214: done in #534; R-RUNNER-233: done in #576; R-RUNNER-238: done in #586; R-RUNGS-8: done in #479; R-RUNGS-11: done in #506; R-RUNGS-14: done in #508
### Requests to PAPER
- [ ] R-MONEY-7 (later): a typed command calling `kill.pull`, sending `Killed.words()` to Telegram.
- [x] R-MONEY-8 (blocking): the paper day calls `day.trade` and `day.publish`, never `day.run`; the adapter refuses an order not dated the session before the broker's today. Done in #152.
- [ ] R-MONEY-9 (later): a stop's fills get the order's id plus "-stop". R-MONEY-10 (later): in conformance set paper fills beside `orders.charges` and the 0.05% spread. R-MONEY-11 (later): say when you hold `desk/clearance.py`.
- [ ] R-MONEY-17 (blocking): no paper sale unattended while a stop rests under the same shares, unless tied at the broker (#163); record in conformance what paper does.
- [ ] R-MONEY-18 (later): the morning message carries `halt.listed(root, day)`, every day's `halt.said(root, day)`. R-MONEY-19 (later): a typed command to call and lift a halt.
- [ ] R-MONEY-20 (later): `test_messenger.py` states each Record's `halted`, `stopped` (say `(), 0`); the evening message says when a day does not count. R-MONEY-21 (later): `test_running.py` (line 213) keeps Friday's record through `day._row(day.Record(...))`. R-MONEY-22 (later): say if `Broker.place` refusals need a blocker of their own.
- [ ] R-MONEY-23 (later): reword `desk/placing.py` (lines 269-272 too, "no cancel either", stale since #285) and its `manifest.toml` line: a desk that died mid-send asks the same cancel through `book._settle`. R-MONEY-24 (later): keep the day's check and `recover` before every round; say if you would rather the send path called one recovery.
- [ ] R-MONEY-25 (blocking): the unattended step calls `watch.look(root, fast store, daily bars by line, now, post)` every step, every hour, BEFORE its round of orders, and decides if London's morning round waits for the 08:05 bar.
- [ ] R-MONEY-26 (later): a messenger call sending again what was never delivered. R-MONEY-27 (later): the halt-lifting command names him (`by=halt.OPERATOR`), with a command for his word against the market.
- [ ] R-MONEY-30 (blocking; money-restop and R-RUNNER-220 wait on it, #573, #617): a `Broker.restop(line, level)` door on Paper (via `placing.moved`, which refuses a line with no stop) and Pretend, through the gate, and `running.recover` puts back a line held with no stop, when its shares are the book's: stop `<newest buy id>-stop` at `book.levels(root)[id]` rounded down to the price step. R-MONEY-31 (later): with R-MONEY-18, the day's list message includes its lost-stop entries.
- [ ] R-MONEY-32 (later): `desk/command.py` rates use `book.rate(root, "USD", day)`, falling back to the archive on ValueError; or move onto `carry.pounds_per_dollar` (#224).
- [ ] R-MONEY-36 (blocking, opened 15 November 2026): catch `book.Alarm` in the day's send path (`desk/day.py` or `desk/messenger.py`) and message him its words once.
- [ ] R-MONEY-38 (later): `reports.fills` collapses a fill and its correction in one reading (keeps the highest version) instead of raising; the ledger now does (#288).
- [ ] R-MONEY-47 (later): `desk/running.py` passes `killed=` to `day.trade` from `lab.promotion` standings, read outside desk/ (R-RUNGS-7, #519). R-MONEY-39 (later): the same file passes `tell=messenger.send` to `day.trade` so a disagreeing place reaches his phone (#290).
### Requests to DATA
- [ ] R-MONEY-3 (later): a daily rate, pounds per dollar, in the store. [x] R-MONEY-15, R-MONEY-16: done (#163, #150). R-MONEY-12 (later): on the master, the market's lines: the yardstick's twin (VUSA), one in New York hours.
- [ ] R-MONEY-28 (blocking): the keeper writes each line's ended five-minute bars to the fast store every five minutes in trading hours, VUAG first, the day's last bar included; and says how late a bar lands (the watch's 20 minutes). R-MONEY-29 (later): the keeper or monitor tells him when a whole venue is not heard from.
- [ ] R-MONEY-35 (later, opened 14 November 2026): a daily advances/declines series for the US market, so Zweig's breadth thrust (#275) can run on real days.
- [ ] R-MONEY-48 (later): delete `HISTORY = CLEAN` in `tests/scenes/rehearsal.py`; nothing reads it (#522).
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
- Watch (#172): no market read after London shuts; `halt.lift` defaults to the operator; a halt cancels no working buy. Lost stop (#191): kept level unrounded; `book.Reckoning` untyped.
- SimCity: the deep run on the real store is unconfirmed after #231; no halted day or overnight death lived. TD Sequential's countdown cancel is untested (#274). Eponymous rules: published figures unchecked, several without a blind review.
- `day.py` counts the ledger by length: a correction after a day's record is not re-priced. SimCity soak names the first red world per promise, not all. `test_lab_headstart` fails on a PC without tzdata (unrelated). `GAP_LOSS` is enforced nowhere (money-time-gaps).

## PAPER

Last updated: 14 November 2026 (folds #100, #104, #110, #113, #123, #128, #135, #142, #152, #155, #168, #182, #183, #189, #210).

### Where it is

Built: messenger (#142), step (#152), drill (#155), supervisor, register empty (#168), no order while another is open (#182),
`desk.running` step/--preflight/--rehearse (#189), `desk.paper --conformance london|us` (#210). No fill seen; his Telegram key unset.

### Next step

Mon 16 Nov: conformance runs 08:05 and 14:35 first, then the desk's day (account empty, never beside a step); compare the files; then supervised.

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
- [ ] R-PAPER-24 (later, 2026-11-14 13:40): a daily store of the archive's answers kept raw, which `desk/command.py` reads instead of rebuilding the store at each asking; and the pound's rate from it (R-PAPER-22).

### Done for other lanes
- R-DATA-5: done in #53 (first half). Open: what the first London contract note says of stamp duty (conformance).
- R-RUNNER-1, R-RUNNER-9, R-MONEY-15: done in #182; R-RUNNER-6: done in #189; R-RUNNER-22: done in #210; R-MONEY-4: done in #75; R-MONEY-5: done in #110; R-MONEY-8: done in #152; R-MONEY-6: done in #113 (drill daily, #155)

### Found, not fixed

- **Unseen at the real Gateway:** a fill, a triggered stop, a sale, a part fill (conformance, Monday). A stop's level is kept only at the broker; a refused order costs 15 s.
- **Supervisor:** nothing registered, nothing starts it, nobody is told what health finds; `messenger.watch` has no caller; the days-without-him count is strict and only as good as the ledger. Also: the raw bars are overwritten (R-PAPER-24); a failed conformance run cannot mend an account the check names.
- **Stale words:** `manifest.toml` says placing "is not built"; `desk/running.py` says "the supervisor: not built"; `desk/gateway.py` "nothing calls it yet". `desk/placing.py` and its test sit at the 400-line cap.

## DATA

Last updated: 14 November 2026 (folds #84-#97, #175, #180, #188, #190, #196, #199, #203, #204, #205, #209).
### Where it is
Twenty lines (22 until SPY and QQQ leave; yardstick VUAG), one archive client, one store, calendars to 2027 (#87).
Research reads all 1,065 through `universe.read` (#84; grid not yet, R-DATA-7). Fast store `desk/bars.py` (#89).
Built: keeper `python -m desk.keeper` (#188, archive half; store filled for Monday, 16 of 22 lines clean;
R-PAPER-23 to confirm on Monday's real closes); `python -m lab.headstart` (#190, 245,593 old five-minute bars
tried in) and `--daily 3LGO` (#209, 2,816 clean bars); `desk.bars --audit` (#199); `desk.snapshot` (#204); four
Sources for old stores (#203). The runner has yet to run and schedule these.
### Next step
Keeper's second half (broker's bars as fallback, R-DATA-9); the six London lines parked for old moves (VUAG
among them); head start's remains (pyarrow pin and parquet readers wait R-RUNNER-24, stooq_raw, old daily bars,
SGLN's off-mark bar refused alone, research-list bars); then data-isa-twins, data-members, data-research-home.
### Done for other lanes
- R-MONEY-1: done in #47; R-MONEY-2: done in #60; R-PAPER-6: done in #175; R-GRID-4: done in #175
### Requests to GRID
- [x] R-DATA-1: done in #73
- [ ] R-DATA-7 (later, 2026-11-13 20:20 UK): a cell reads `universe.read(root, line).bars`, not `store.read`,
  and keeps `History.moves` and `.rescaled`.
- [ ] R-DATA-10 (blocking, 2026-11-13 21:45 UK): `test_lab_batch.py`, `test_lab_cell.py` look SPY and QQQ up
  by name; name lines that stay (AAPL, NVDA).
### Requests to MONEY
- [x] R-DATA-4: each `Line(...)` in its tests states its UK tax.
- [ ] R-DATA-3 (later, 2026-11-13 18:15): the day run reads the archive through `archive.gather` and hands
  `store.prepare` its answers whole, so a refused line parks with its reason.
- [ ] R-DATA-6 (later, 2026-11-13 19:20 UK): scene 5 reads `CLEAN`; `HISTORY` is the same, and goes.
- [ ] R-DATA-12 (later, 2026-11-13 21:45 UK): `day.run` reads "simply holding the market" from `lines.YARDSTICK`
  (VUAG); nothing is bought in the ISA on a line whose `isa` flag is not yes.
- [ ] R-DATA-13 (later, 2026-11-14 12:25 UK): `test_watch.py` line 58 names its source,
  `bars.writing(tmp / "bars.db", bars.Source.ARCHIVE)`, so every round must name one.
### Requests to PAPER
- [x] R-DATA-5: each `Line(...)` in its tests states its UK tax.
- [ ] R-DATA-9 (later, 2026-11-13 20:20 UK): a read-only question for a line's newest five-minute bars at
  `desk/paper.py`, and whether the paper account gets live or delayed data.
- [ ] R-DATA-14 (blocking, 2026-11-14 15:30 UK): wire the door `keeper.saved(home, day)` and the crash watch's
  store `home / keeper.HOT`; make the day's record only once `keeper.target(venue, now)` is past the day for
  every venue, or the door refuses 25 minutes every evening.
- [ ] R-DATA-15 (later, 2026-11-14 15:30 UK): may the keeper ask the Gateway for bars through `paper.dial`, or
  does PAPER build that question (R-DATA-9)? It is the archive's fallback.
### Requests to RUNGS
- [ ] R-DATA-8 (later, 2026-11-13 20:20 UK): a verdict states how many trades were held through a day in
  `History.moves` (about a hundred London bad prints), with and without them.
- [ ] R-DATA-11 (blocking, 2026-11-13 21:45 UK): `test_lab_rung.py` prices a dollar trade on "SPY"; name a US
  line that stays (AAPL).
### Requests to RUNNER
- [ ] R-DATA-16 (blocking, 2026-11-14 16:20 UK): `test_check.py::test_at_most_n_full_checks_run_at_once` is
  flaky on Windows (WinError 32: `check.turn` unlinks its turn file while another thread holds it).
- [ ] R-DATA-17 (blocking, 2026-11-14 16:00 UK): pin `pyarrow==26.0.1`, add it to manifest `allowed_third_party`,
  and add requirements.txt to DATA's lane files (the guard refuses it).
- [ ] R-DATA-18 (later, 2026-11-14 15:30 UK): keeper calls run to 21:40 UK at least, logs kept (stdout,
  `MISSED:` on stderr); schedule `lab.headstart`, `--daily 3LGO`, audit and snapshot.
### Found, not fixed
- **UK tax (NS-05).** Five London products unseen on a contract note; London shares 0.5%, unchecked.
- **Operator:** IB1T (Bitcoin) is not ISA-holdable (crypto notes shut to new ISA purchases from 6 Apr 2026).
- **Research:** today's members only (BT-09); scale changes under the store's belief are UNI-07; WWH, SHC, EDV,
  ROSE read false losses. Member record (#96): one unofficial source; `members.on` raises for FTSE350, ETFS.
- **The store:** nothing fills `Line.real_moves` or `.suspended`; 6 of 13 London lines parked on the real archive.
- **Keeper:** a refresh dying between bars and record leaves a stale record (healed next call); keepers not
  locked apart. **Head start:** SGLN's off-mark bar; stale manifest wording; old daily bars need a fill-only write.

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

Last updated: 14 November 2026.
### Where it is
Rungs proven on made-up prices only: first, luck, folds, trials, deflated Sharpe, plateaus, regimes; built, not yet
called: author's result, promotion, bets, stress, indicator tables. `python -m lab.ladder` (#198) runs set 1 (5 rules
x 22 lines, 330 trials): 48 judged, none passes, 62 wait on data (30 on six parked London lines, 32 on the pound's
missing April 2025 closes). The one verdict reads six rungs (#206): no verdict if folds did not run; a paper candidate
comes from the ladder's line, never a bare PASS. Zero trades on a line under 452 bars "waits on history" (#202).
**No winner on real prices is to be believed yet; no author's or replication's figure is on file.**

### Next step
Open: rungs-trustworthy (wire bets, stress), rungs-indicators (R-RUNGS-6, 12).
**rungs-reproduce is BLOCKED, hand it out no more** (#143, #149, #169, #186, #195): no book is bought (his ruling,
14 Nov); a replication stands in, labelled second hand (#169); best free figures in DECISIONS, none on file. Waits on
R-RUNGS-5, 9, 10, 13, 14 (all open); then `folds`/`regime`/`stress` pass reproductions on; a person reopens each page
before a figure is filed. Ladder wiring left: regime (REG-01), stress (R-RUNGS-11), plateau (settings). `Candidate`
should also refuse a row listing unrun rungs (recommended: when the first real candidate nears). Ruled 14 Nov:
concentration on every report. Unit tests stay at the product's size.
### Done for other lanes
- R-DATA-11, R-RUNNER-5, R-RUNNER-3: done in #186; R-RUNNER-25: done in #202; R-RUNNER-33: done in #206
### Requests to MONEY
- [ ] R-RUNGS-6 (blocking, 01:20): the indicators of `desk/strategy.py` public and by name (STR-14).
- [ ] R-RUNGS-12 (blocking, 07:55): narrows R-RUNGS-6 to a public RSI and Bollinger lower band; keep the private names meanwhile.
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
- [ ] R-RUNGS-15 (blocking, 14 Nov 15:30): the pound's closes for 17-20 April 2025 are missing; 32 dollar cells wait (with R-RUNGS-3).
- [ ] R-RUNGS-16 (blocking, 14 Nov 15:30): six London lines parked for price steps (2MU, 5QQQ, SGLN, VUAG, EQQQ, IDTL), 3LGO one bar: 35 cells wait.

### Found, not fixed
- **Ladder:** rates fetched each run, kept nowhere, the rule written twice beside `desk/command.py` (both end with
  R-RUNGS-3); one run at a time; no settings on rules, no regime weather (REG-01). `test_check.py::test_at_most_n_full_checks_run_at_once`
  failed once in three (a turn file held). **Reproduction:** Bollinger, 50/200 cross, Supertrend have no author's test (ruling owed).
- **Promotion:** fall sees sold shares only; `DEEPEST` belongs to the A-GATE. **Market/stress:** calm-storm alternation
  passes a rider twice as often; "days end at first unjudged trade" lives twice, belongs in `rung.py`. **Bets:** a young
  line (<120 moves) stops it. **Indicators:** `published.py` at its 400-line cap; RSI ratio, band line, carried band unheld.
  Scratch owed removal in `C:/tmp`: repro*, promo*, market*, bets*, rungs*, ind*.
