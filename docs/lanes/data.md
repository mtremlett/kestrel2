# The data lane

The data lane's own decisions, each a dated `###` entry saying what was decided, the
options, why, and the evidence; newest last. Only this lane's scribe writes here, so no
other lane's pull request touches these lines. Held to a size a session reads whole
(`BUDGET.json`, `max_lines_per_lane_doc`): when it is full, the scribe folds the oldest
settled entries into one short summary entry; git keeps every word.

## Decisions

### 2026-11-13 to 14 — the first day's decisions, folded (the oldest settled entries)

Sixteen entries (some bullets since dropped), each settled and built, folded into one; git keeps every word (the file
before this fold: `git log -p docs/lanes/data.md`).
- *The fourteen months* (R-MONEY-2): the scenes read the whole rehearsal data, each line
  on its own venue's calendar; the six-week window and the status cut went.
- *Parking.* One refused line is parked alone with its reason and the rest carry on; a
  frozen feed (a week of one bar repeated) is dropped and parks a recent line; a suspension
  recorded on the line is no gap; a one-day crash is kept and parks until recorded, and
  only a hundredfold bar is a wrong unit.
- *The research list:* 1,065 tickers (S&P 500, Nasdaq 100, FTSE 350, 200 most-traded US
  funds) kept apart from the twenty trading lines; being on it makes nothing tradable; a
  refusal parks that ticker alone; research reads the parked fifth by a rule of its own (#80,
  #84).
- *UK tax:* two rates (nil for a fund or exchange-traded product, stamp duty for a UK
  share), a fact on each line, with how far each is confirmed.
- *The twins* (#85): VUAG, EQQQ and IDTL in the master with an ISA flag and a retail flag
  on every line, GLD out, the yardstick VUAG.
- *The fast store* (#89): SQLite in WAL mode, whole rounds, exact decimals, benchmarks held.
- *The lists' members* (#96): S&P 500 and Nasdaq 100 by day since 2010; `on` refuses the rest.

### 2026-11-14 — the head start, currency and store rules, folded (#175-#254)

Settled and folded; git keeps every word. The old desk's five-minute bars, and later ibkr_store, Stooq and
mark_the_trend files and the old database's daily rows, are read as a head start into the fast store, daily fill-only
(#175, #236, #238, #245, #254). Currency steps are judged by the day's pound, with recorded splits and London-midnight
dating; a long run of dollar-quoted bars is dropped (#217, #220); the six parked London lines came out clean (#222).
Every rule and constant of `desk/store.py` is pinned by a row of one synthetic table, and that guard was driven red
(#225, #227, #230; R-RUNNER-43, -46). The lane's open boxes were put in working order (#180).

### 2026-11-15 — adjusted against as-traded closes; the 39-minute close rule, folded (#286, #294)

The head start recognises a store of adjusted prices beside the as-traded one and never writes over raw (R-RUNNER-90, #286).
The store holds each venue's closes within 39 minutes of its close (R-PAPER-23, #294). Details are in git history.

### 2026-11-15 — nine settled store and keeper rules, folded (#314-#381)

VUAG's 2019 gap filled from a checked shelf, never forward-filled (R-RUNNER-104); every venue has a calendar and SimCity worlds are dated on trading days (R-RUNNER-107); `python -m lab.universe` refreshes research (R-RUNNER-116); a bar with only a bad high or low is kept and repaired, and an impossible low likewise (R-RUNNER-175, -185); the keeper cleans kept history again when the store rules change (R-RUNNER-182); a missing yardstick day is a named fault filled from a second source (R-RUNNER-179). Each took its recommended option; git keeps the full entries.

### 2026-11-16 — the first two-database steps and the free collector, folded (#424-#460)
The store became two databases, long and short (#442); the free collector runs once a day, writing second-opinion prices,
macro series, earnings dates and timestamped news into the one store (#460); the archive's daily answers are kept raw and
read instead of asked again (#458). Two no-change sessions (#424, #454) found R-RUNNER-11 waiting on PAPER test lines; it
landed later. Git keeps each full entry.

### 2026-11-16 — SPY kept as a reference series, folded (R-RUNNER-94, -96) (#303, #475)

- Reference bars live in archive.py (store.py would pass 400 lines), checked weekday-only without a calendar; a refused
  reference fetch is told in words, not counted a miss, retried at the next call; kept under the US daily folder.

### 2026-11-16 — the one calendar names market events (R-RUNNER-149) (#453)

- Events are read from the calendar by (venue, day) and refused outside 2026 (options: guess
  recurring dates / refuse; chose refuse, per the calendar's own rule). ECB left out: no venue
  of the desk's is Frankfurt.

### 2026-11-16 — the keeper keeps and reads the daily bars in the long database (R-RUNNER-11, step) (#486)

- - Left the fast store's file name "bars.db" (options: rename now to market_live.db, or
  later). Renaming breaks PAPER's tests (test_command, test_running, test_watch, test_pnl
  write "bars.db" literally) and the claim forbids touching them. Recommended and taken:
  later, once PAPER's tests use `keeper.HOT`. - The keeper writes a line whole
  (`Round.daily`), tagged archive, so an earlier import of lower sources into the long
  database would be replaced at the next refresh. The multi-source rule (IBKR, Yahoo, Stooq,
  recorded disagreements) must come first; it is the next step.

### 2026-11-16 — the store's one rule for two sources and the yardstick fault (R-RUNNER-189, first step) (#500)

- (1) A clash is kept as a recorded fault with the archive's bar standing (options: drop both,
  as `_once` does for a date given twice differently; keep the first source's). Chose the
  second: "Yahoo first", the fault is told and parks the line while recent, and nothing is
  dropped silently. (2) Tolerance 2% on the close, since Stooq's daily bars are split-adjusted
  only and a dividend day is under that; to be tuned only through the pinned constant. (3) No
  double report: a yardstick whose archive refused is already a miss.

### 2026-11-16 — the day's pounds per dollar, kept and readable for any session (R-PAPER-22) (#505)

- the pound is a reference series, not a traded line (options: a twenty-first line in LINES,
  or a separate store; chosen the first-existing mechanism so no new store or module:
  recommended, cheapest). Guard not touched.

### 2026-11-16 — the broker's daily bars as the store's first source, a client of their own (R-RUNNER-189, second step) (#517)

- The contract for London lines is SMART with primary exchange LSEETF (the first try with
  exchange LSE got "no security definition"); US lines go by SMART alone. Options: a per-line
  exchange field on Line (PAPER/DATA master change, larger) or one table by venue (taken,
  smallest).

### 2026-11-16 — the cleaner's bad-high/low repair named settled; R-PAPER-22/23 were already built (R-RUNNER-194) (#518)

- R-RUNNER-194. Options: (a) keep #367's "leave a deep low" - the yardstick parks on a bad
  print; (b) keep #381's "repair a low like a high" and leave a close-shared fall as the
  market's. Chose (b): the north star needs the yardstick unparked, and a real crash (close
  falls with the low) is still kept. No further change to the cleaner's bad-print rule without
  a failing row in test_store_rules.py.

### 2026-11-16 — the head start's jobs write the two databases (R-RUNNER-10) (#520)

- Five-minute imports stay in the short file (bars.files design, #442); moving imported
  intraday history to the long file is a design change, left to a later box. Options: leave,
  or move; chose leave (no behaviour change).

### 2026-11-16 — the broker's daily bars stand first at the store's one writer (R-RUNNER-189) (#521)

- the broker's refusal is not itself a fault and the archive carries on (his order of sources,
  16 Nov); a refused archive with good broker bars does not park the line.

### 2026-11-16 — stooq_store's daily rows enter the history database under their source (R-RUNNER-10, step) (#527)

- removed a separate "adjusted?" check I first wrote: the store's own check already refuses it
  (shown by switching it off), so less code. Options: keep the clearer message / delete; chose
  delete (canon A1.3).

### 2026-11-16 — live session bars from IBKR only; the archive only backfills (R-RUNNER-211) (#530)

- Backfill source: (a) reuse ARCHIVE, which would let the archive overwrite IBKR bars; (b) new
  non-fresh Source.BACKFILL that only fills gaps. Chose (b): his ruling that Yahoo only
  backfills, each bar marked. Pacing: 3 s per ask, 40 asks in ten minutes against the broker's
  60; his 11 s was for the daily history.

### 2026-11-16 — no change - R-RUNNER-12 blocked on files outside the keeper claim (#531)

- Options: (1) add --live/--roll stubs raising NotImplementedError (runner would start them
  and count a miss every minute); (2) change nothing and ask for a wider claim. Chose 2, since
  a started job that always fails is worse than none (canon A5, and the runner starts a job
  only when its flag appears).

### 2026-11-16 — a recovering fall as large as the pound is the market's move (R-RUNNER-178) (#532)

- Options for a short run of dollar-quoted bars among pounds (the old "stray bar" and "month"
  cases): (a) keep dropping them as wrong unit, which also drops real recovering crashes; (b)
  treat any recovering step as the market's. Chose (b), as the request says "a recovering fall
  is the market's move"; hundredfold (pence) strays are still dropped. A step that drifts out
  of 10% of the pound's rate inside 60 sessions is read as a market move. Pattern: every rule
  judging currency by a price ratio (here the only one, _agree) now asks whether the step
  lasts.

### 2026-11-16 — no change - R-RUNNER-12 needs a wider claim (bars.py, new modules); keeper.py at its cap (#535)

- Options: (1) edit outside the claim, which the check refuses; (2) pad keeper.py past 400
  lines, which a guard refuses; (3) land nothing and ask for a wider claim. Chose 3, from the
  canon's stop rules.

### 2026-11-16 — stooq_store_matrix daily arrays into the history database (R-RUNNER-10) (#533)

- a new source name rather than reusing the 5-minute matrices' one, so a line's daily and
  five-minute bars of the matrices are told apart (option: reuse MATRICES; rejected, "already
  in" would then skip wrongly).

### 2026-11-16 — intraday rollup from 1m bars (R-RUNNER-215, step) (#539)

- the bar is a new Candle type (timestamped, with source) since store.Bar is daily only;
  options were widening Bar (touches the store, outside the claim) or a new type; chose the
  new type, to be reconciled when the stores take intraday bars.

### 2026-11-16 — the reference series live in the long database (R-RUNNER-189) (#524)

- marker file kept as a file rather than a table (option: a table in the database; chosen the
  file for the smallest change, since it holds no price).

### 2026-11-16 — rollup.weekly builds weekly bars from daily bars (R-RUNNER-215, step) (#542)

- manifest line for desk/rollup.py left as is (a lane may not edit an existing manifest line;
  guard test_lanes refused it), so it still says "intraday"; the scribe/owner may widen the
  wording.

### 2026-11-16 — every line names its underlying market and source (R-RUNNER-157) (#528)

- Fields default to empty so other Line builders (lab, tests) stay valid; the wiring test, not
  the type, demands them on LINES. Options: required field (touches files outside claim) vs
  default (chosen).

### 2026-11-16 — stooq_raw's daily zips enter the history database under their own source (R-RUNNER-10, step) (#545)

- reused Source.STOOQ_RAW for the daily span (its 5m rows are a different span, so no clash)
  rather than add an enum member outside my claim.

### 2026-11-16 — research bars and the pound enter market_history.db (R-RUNNER-221) (#548)

- the CSV carries no source, so the source is inferred: options (a) all Yahoo, (b) shelf-equal
  bars Stooq, rest Yahoo. Took (b), his "go with recommended" ruling, since the shelf is where
  Stooq fills live.

### 2026-11-16 — spans.py holds one Span per timeframe; bars.py writes and reads any span (R-RUNNER-218) (#547)

- Where a 4h bar starts: (a) UTC multiples of 4h, (b) per-venue session marks. Took (a),
  because bars.py has no venue at write time and desk/rollup.py already builds session-aligned
  bars; 08:00 London is still a mark. A week starts Monday 00:00 UTC.

### 2026-11-16 — stooq_store's hourly bars enter the history database under their own source (R-RUNNER-10, step) (#549)

- the hourly span lives in market_history.db (his 18:32 ruling: history keeps every
  timeframe), option: a separate third file, rejected as a needless extra database.

### 2026-11-16 — Stooq matrices' 15m, 30m and 1h arrays enter the databases (R-RUNNER-10, step) (#566)

- the arrays' hourly stamps are read as hour-end because the first bar of each London day is
  stamped 10:00 on Stooq's clock (options: start-stamped; chosen end-stamped on that
  evidence).

### 2026-11-16 — rollup.merged - a pulled bar wins over a rolled one, a disagreement is a fault (R-RUNNER-215, step) (#571)

- a "disagreement" means any difference in open, high, low, close or volume (options: price-
  only, or with a tolerance; chose exact, the strictest, as the fault is only recorded and the
  pulled bar wins either way).

### 2026-11-16 — dividend-adjusted twins of the reference series (R-RUNGS-9) (#544)

- the twin is a separate Line with a tagged symbol, because the store's key is (venue, symbol,
  span, at) and holds one source per day. Option B was a second source on the same key, which
  the key does not allow. Option A was chosen.

### 2026-11-16 — SGLN's 15 April 2013 close is a recorded real move, so SGLN clears (R-RUNGS-16); R-MONEY-28, R-RUNGS-3, 5, 9, 15 already on main (#582)

- Record SGLN's step in MOVES (the designed place, as for 2MU and 5QQQ) rather than loosen the
  store rule (failure pattern 13: no rule tuning on live lines). Options: record the move
  (chosen: it is real, the bars around it are consistent), or widen the daily-range test
  (rejected: would hide real bad prints on other lines).

### 2026-11-17 — desk/backfill.py fills a missing daily bar for any named line and day (R-RUNNER-224) (#574)

- Yahoo's source name is the existing Source.BACKFILL ("archive, backfilled"), options: a new
  Source.YF, or reuse; reused because it already means the archive's fill of a past day and
  fills only where none is held.

### 2026-11-17 — the calendar's sessions reach back to 1993 (R-RUNGS-5, R-RUNGS-9) (#594)

- whether to widen the hours too (option A) or sessions only (option B, chosen: the 2007 US
  clock rule is wrong before 2007, and store/bars use `KNOWN` as the hours' span). Option A
  needs the older clock rules; do it when an intraday history before 2010 arrives.

### 2026-11-17 — history pull plan, pacing and resume (R-RUNNER-216, step) (#605)

- pacing stays one ask per 11 s (54 per ten minutes, under IBKR's 60); options were a sliding-
  window counter (more code) or the fixed gap (chosen, no extra state).

### 2026-11-17 — desk.keeper --live, one run of one-minute bars for the lines due (R-RUNNER-12, step) (#606)

- due-line rule = lines[(minute*2 + k) mod 20], k=0,1 (options: per-line timers kept on disk,
  or a stateless rota; chose the rota, as it needs no state and matches 2 lines a minute).
  Stale = newest bar ended over two minutes before the run.

### 2026-11-17 — history.run, the paced pull over one conversation (R-RUNNER-216, step) (#621)

- intraday bars fail loudly rather than being stored by day (options: collapse to day / fail
  loudly / widen Bar now; chose fail loudly, as A5 and A2 say, since Bar is outside this
  claim).

### 2026-11-17 — the pound's daily rate back to 1993 (R-RUNGS-3) (#614)

- pre-Dec-2003 pound = FRED DEXUSUK (public, keyless) vs. leaving 1993-2003 SPY days unpriced
  in pounds; chose FRED, kept under its own source label because it is the noon buying rate,
  not a close (a few pips different). Only days before the archive's first pound are filled,
  so the two conventions never mix inside the archive's era. Band widened rather than special-
  casing 2007.

### 2026-11-17 — desk.keeper --roll (R-RUNNER-12, step) (#616)

- roll uses replace-on-key (the live copy is the truth being rolled; options: ignore-if-held,
  which would leave a restated bar stale in history). Chosen: replace, recommended by the one-
  store rule.

### 2026-11-17 — history reads intraday candles (R-RUNNER-216, step) (#627)

- epoch seconds (formatDate 2) chosen over the gateway's local-time text: options were text in
  an unstated zone, or epoch; epoch is unambiguous.

### 2026-11-17 — --live one-minute question from IBKR, pacing counted (R-RUNNER-12, step) (#629)

- bars to ask = since last held (spec), floor 2 minutes, first run one hour; pacing counted by
  the word "pacing" in a refusal's reason.

### 2026-11-17 — the keeper names the lines parked live (data-keeper, step) (#642)

- (1) Parked state is derived from the store at each look, not a record: options were a
  persisted live record (needs a file beyond this claim) or derive; derived, so recovery is
  automatic. (2) 15 minutes late (three bars), as an illiquid line may trade nothing for five
  or ten; too long-quiet lines are parked, the safe side. (3) Printed by the command, not a
  miss, so a venue's miss rule is unchanged.

### 2026-11-17 — no change - data-members remainder waits on a members source (#638)

- Options were (a) invent a FTSE 350 record from memory, (b) record the funds as unchanged
  since 2010, (c) land nothing and name the wait. Chose (c): (a) and (b) would give a study
  survivor-biased lists presented as complete, the exact fault this box exists to remove.

### 2026-11-17 — pulled broker bars written into the history database (R-RUNNER-216, step) (#636)

- a bar off its timeframe's marks raises (fail loudly) rather than being silently shifted.
  Options: shift to the UTC grid, or fail. I chose fail, because session-aligned venue bars
  need the venue's calendar.

### 2026-11-17 — calendars carried to 2030 (data-calendar-years) (#641)

- horizon 2030 (options: 2028 only, 2030, 2035); chose 2030 as the rules are stable and no
  later list is published to test against.

### 2026-11-17 — the archive spared - slow, backing off, cached, refusing_since (data-archive-spared) (#637)

- caching default from KESTREL2_DATA (options: only when callers pass a home / default to the
  environment's folder; chose the latter so every caller is spared with no edit outside my
  claim). Five-minute answers left uncached (stale by the next round).

### 2026-11-17 — 2MU's moves confirmed against Stooq (data-2mu) (#650)

- options (a) record a fifth move, (b) confirm the reason. Chose (b): Stooq contradicts the
  archive's 24 Oct bar, so recording it would admit a wrong price.

### 2026-11-17 — archive obeys Retry-After (data-polite) (#665)

- Retry-After capped at 300 s so a hostile header cannot stall the keeper's slot; options:
  obey uncapped, ignore it; chose capped.

### 2026-11-17 — the keeper measures and shows the source's delay (data-keeper) (#659)

- indicators are not stored copies, they are read from the kept bars (options: store computed
  indicators, or compute on read; chose compute on read: one source of truth, canon A4).

### 2026-11-17 — keeper receipts and stale-line alert (data-kept-hot) (#672)

- Stale = newest daily bar earlier than the venue's last session before the day the venue is
  readied for (so Monday morning owes Friday's close, and the just-closed day is not owed
  until it settles). Options: judge against today's date (false alarms every evening) or this;
  chose this. A receipt is written only when a call did or missed something (192 empty lines a
  day would hide the real ones).

### 2026-11-17 — the history pull knows what the database holds and has a command (R-RUNNER-216, step) (#674)

- depth of one year for every timeframe, 50 asks per run (50 x 11 s stays inside 60 asks per
  ten minutes). Options: per-timeframe depth now (needs a change to history.run's single
  `since`, outside the 100-line step) or one depth now; chose one depth, recommended as the
  smaller step.

### 2026-11-17 — the research store's home, nightly refresh and clear-out (data-research-home) (#679)

- Home = grid/store (where the grid and history import already read; options: a new folder;
  chosen the existing one, one home per concept). The list "reflected" = lists' sizes plus a
  short fingerprint (option: copy the whole list; the fingerprint is enough to tell a change).
  The history database keeps a departed ticker's past bars (a study of the past needs them);
  only the live store files are cleared. Taken on his standing ruling "always go with
  recommended".

### 2026-11-17 — data-polite - no change; parts already on main, limits unmeasured (#678)

- Held data-isa-twins and went on, by his ruling "always go with recommended"; chose not to
  add a speculative rate figure without measurement (options: guess a faster pace; leave 1 s;
  chosen leave, because a wrong guess risks a ban of the only free price source).

### 2026-11-17 — no change - data-keeper's remainder is MONEY's gate on parked_live (#648)

- (1) Do not add a second parked-line store inside the keeper. Options: write a parked file
  the day reads, or let the day call `keeper.parked_live(hot, LINES, now)` on the same store.
  Chose the call: one source of truth, no file to go stale (canon A4). (2) Left LATE at 15
  minutes. Options: tighten to 10, or keep. Kept: the watch's alert is at 20, and IBKR bars
  land within a minute, so 15 already catches real lateness without parking on a slow round.

### 2026-11-17 — archive pace is a courtesy, not a probed limit (data-polite) (#685)

- Measure the archive's limits by burst-probing? Options: (a) probe with bursts until refused;
  (b) keep the fixed 1 s pace and let real refusals drive the backoff and the six-hour alert.
  Chosen (b), recommended: the archive publishes no limit, a probe risks banning this PC's
  address and so the desk's own data, and a measured number would be a test of a third party,
  not repeatable.

### 2026-11-17 — 5QQQ starts on 22 August 2024; its jump was a unit change (data-5qqq) (#681)

- Options: (a) keep the 500 split (wrong, 5x too high); (b) a ratio of 100 (the store's jump
  test cannot confirm it across the 432-session gap); (c) start the line on 22 August 2024.
  Chose (c): the only one the evidence supports, smallest, guessed no ratio. His standing
  ruling: "please always go with recommended".

### 2026-11-17 — SGLN's garbled 2011 handled by a start date (data-sgln) (#694)

- Options: (a) drop only the zero-volume dollar bars by a new rule, (b) start the line after
  the last one. Chose (b): no new store rule (failure pattern 13), the mechanism exists, the
  loss is six months. Under his "always go with recommended" ruling: data-isa-twins held
  (waits on operator), kept to data-sgln.

### 2026-11-17 — 3LGO's history recorded, the rule for enough (data-3lgo, step) (#699)

- Held data-isa-twins as told (his "always go with recommended"). Gaps of 2015: options were
  record them as suspensions, or leave them as an old recorded fault; chose to leave them,
  since no second source confirms a suspension and an old fault does not park. Rule for
  "enough gathered": options were (a) the archive's own bars alone reach the ladder's MIN_BARS
  (452), (b) any fixed count of years; chose (a), one number already in lab.verdict. No store
  code change: the store already unparks a line by itself on the first clean day.

### 2026-11-17 — data-3lgo ticked from #699; a stretched bar's change recorded beside it (data-stretched) (#702)

- Per the runner's ruling taken for him ("always go with recommended"): data-3lgo is ticked
  from #699 rather than held for the daily feed. Stretch note options: (a) list it and park
  the line, which contradicts his 13 Nov ruling; (b) list it with a `noted` flag that parks
  nothing. Chosen (b).

### 2026-11-17 — the keeper's command asks the broker first (R-RUNNER-270) (#701)

- (1) Ask the broker only for lines the archive lacks, not all 22 lines: options all lines
  (about 4 minutes of pacing, would miss the runner's window) / only short lines (chosen,
  recommended). (2) A closed gateway is a Refused in words, not a crash: the archive still
  runs (his ruling: IBKR first, Yahoo fills).

### 2026-11-17 — each timeframe's pull goes back as far as IBKR gives in one ask (R-RUNNER-216, step) (#703)

- reach per timeframe taken from IBKR's published duration limits per bar size (options: one
  reach for all, refused by the broker; per-size reach, chosen as it keeps pacing and the plan
  unchanged).

### 2026-11-19 — a refused line is kept and parked, not wiped (#801, R-RUNNER-309)

Options: wipe as before, or keep and park. Chose keep and park: canon B3, raw data immutable; the park already stops trading it. Withdrawal is a table beside `bar`, not a deleted row or a flag column, so existing stores need no rewrite.

### 2026-11-19 — arrival time is recorded in the receipt (#820, DQ-10, DQ-12)

Options: (a) an arrival column in the store, a schema change on 82 GB-scale data; (b) record it in the receipt at first sight. Took (b): no migration; the receipt is the dated record DQ-12 asks for.

### 2026-11-19 — an unfillable short-timeframe gap is named red (#825, #836)

Options: hide until a source exists, or name it red. Chose red: a gap no source can fill is named red.

### 2026-11-19 — bars and faults: narrow the window now, one file next (#832)

Options: (a) one file per line (built, but breaks tests/unit/test_lab_universe.py outside the claim); (b) keep two files, write both whole before either swap. Took (b) now, (a) next with a wider claim (R-DATA-55).

### 2026-11-19 — rolled short bars need their own source (#842)

Options: (a) add a rollup:<from> source in desk/bars.py and write the rolled bars (a wider claim, R-DATA-56); (b) reuse an existing source label, rejected: each bar must name its true source. Chose (a).

### 2026-11-19 — deep history: split KNOWN rather than widen it (#841, R-DATA-54)

Options: A widen KNOWN to 1993 (hides unknown hours); B split into HOURS_YEARS and SESSION_YEARS. Took B (his 13 Nov ruling: go with recommended). Closes recorded are the archive's, since the store compares the archive's close exactly. Supersedes the two 17 Nov entries above on this.

### 2026-11-19 — five-minute against daily volume: 50%, excess only (#853)

Options: two-sided or excess only. A shortfall is a thin session, already named, so one-sided avoids double-naming. Tolerance 50%.

### 2026-11-19 — the lock holder is named "unknown" (#856, R-RUNNER-329)

Option: a lock-file recording pids; more machinery, declined. SQLite does not report the holder, so the error names the waiter, the file and the seconds.

### 2026-11-19 — one price grid, a ten-thousandth, half-even (#861, R-RUNNER-341)

Options: 4 places, 6 places, significant figures; chose 4, the broker's own form and the pence-to-pound grid. The broker's bar stands in its 30-day window, the archive's beyond it; a day leaving the window takes the archive's volume once, a real change recorded once. Not adopted: tagging broker days with their own source (a wider change to receipts).

### 2026-11-19 — the keeper's fault window is 400 sessions (#863, R-RUNNER-327)

Options: 60 sessions (too short, hides a lasting step the strategies still read), 400 sessions (coverage.NEED, what a rule needs before trading), all history (today's fault). Chose 400; lasting faults dated outside it are named only.

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

### 2026-11-17 — the archive's start moves to 2000; the alert is a line, not a sender (#691, #671)

Daily history (#691): `archive.SINCE` moved from 2010 to 1 January 2000 rather than a second constant (one home for
the number); the grid sweep's window reads it, so it begins 2000 too. Options: leave 2010 with a second constant;
one start (taken). The Stooq head start for 2000-2009 waits for data-consolidated. Alert (#671): `alert(data, now)`
is a pure function of `archive.json` and the clock that returns the operator's line after six hours' refusal; the
runner sends it. Options: send from the archive; return a line (taken, the archive stays free of messaging).

### 2026-11-17 — page depths and the unlisted line (#710, #725)

History pull (R-RUNNER-216): depths follow IBKR's per-bar-size limits (1m a month, 2-15m half a year, 30m-4h two
years, daily and weekly twenty years). Options: one deep ask, which IBKR refuses for small bars; pages (taken). A
page refused after data was had ends the walk quietly with the pages had. A line with no listing is left out of the
pull rather than written in raw broker prices (options: skip, safe and taken; write raw, 100 times too big in pence).

### 2026-11-17 — one unit rule for broker bars (#719, R-RUNNER-279)

`history.in_currency` is the one place broker pence become the line's currency; `history.priced`, `history.daily` and
`backfill._broker` call it; an Unlisted line's broker bars are refused (unit unknown) and judged on the archive alone.
The listing root is `home` if given, else KESTREL2_DATA (options: edit keeper.py to pass home, outside the claim; the
env, taken). `backfill.in_currency` stays as an alias because `test_backfill.py` calls it (R-DATA-49 retires it).

### 2026-11-17 — who sets a unit in the store: traded bars (#721, R-RUNNER-274, -275)

SGLN's 2011 "dollar bars" were flat bars of no volume, and the store let the first one set the unit, then dropped the
real pound bars after. Options: (a) judge backward from the newest bar (rewrites the walk, store at its 400-line
cap); (b) drop all zero-volume flat bars (2MU, 3LGO, IITU hold real untraded quotes and would park); (c) an untraded
bar cannot hold a unit against a traded one, only where it is the other unit (taken: smallest, per "take recommended").
The start date for SGLN went; 5QQQ's stays (pence to pounds over a gap). Debt: one designed backward pass, later.

### 2026-11-17 — the live keeper and its round (#727, #730, R-RUNNER-277, -280)

The live round marks each due line as started (an empty write) so a line with no one-minute history begins from IBKR
(#727; options: mark in `keeper_live`, taken; or catch LookupError in `live.minutes`, outside the claim, recommended if
the claim widens). The live round gets its own deadline, not a shared one (#730; options: shared order only; own
share, taken as the request says). Wiring it into `keeper.keep` is R-DATA-49.

### 2026-11-17 — a refusing archive ends the round (#732, data-archive-spared)

Once the archive refuses and every wait is spent, `gather` leaves the rest of that round unasked, refused with the
reason, so other work goes on (options: keep retrying each line; stop the round, taken). A 404-type answer about one
line still refuses that line alone. Five-minute answers are now cached in KESTREL2_DATA like daily ones.

### 2026-11-17 — the pull asks only timeframes on the store's marks (#739, R-RUNNER-216)

IBKR's 1h, 4h and weekly bars start on the venue's session (a US hour at :30 UTC), off the store's marks, and the
writer refuses them, which would stop every run at one place for ever. Options: (a) drop the bars silently
(forbidden); (b) re-align at write; (c) do not ask, roll up locally (taken: smallest, his 16 Nov ruling).

### 2026-11-17 — a bridge for every line, from five-minute bars (#747, R-RUNGS-16)

`bars.bridged` fills each session of the last 30 days that shelf, archive and broker all lack from held five-minute
bars, lowest priority. Options: 3LGO only; every line (taken: one code path, A2). A day cut short (Gateway down) would
give a partial daily bar rather than a park; accepted, the keeper waits SETTLED after the close. The bridged close is
the last continuous trade, not the closing auction.

### 2026-11-17 — a non-HTTP fault on one vendor no longer fails the collector (#744, R-RUNNER-284)

An OSError on one vendor with others kept exits 0, per the request (non-zero only when no vendor gave anything); it is
still named on stderr.

### 2026-11-17 — IBKR first for every line (#751, R-RUNNER-276)

(1) IBKR and the archive disagree beyond 2%: park the line, or hold IBKR's bar and record the fault (taken, his
"Always prefer IBKR"). (2) Lines the broker was not asked for: leave on the archive till tomorrow, or ask again at every
call (taken; `Kept.unasked`). (3) With no broker passed (tests only) the run line is as before.

### 2026-11-17 — a shelf a hundredth of the archive's is a unit fault (#753, R-RUNNER-272)

(1) No new `desk/units.py`: the desk is at its 80-file ceiling; options raise it (loosening a guard) or fold into
`store.py` (taken). (2) The factor (PENCE) applies only on evidence (5 or more shared sessions, all alike), never by
venue. (3) The shelf file stays as shelved; the store re-judges it on every prepare through the one writer.

### 2026-11-17 — keeper round first; `home` stays optional until PAPER passes it (#759, #769, R-DATA-49)

(1) Make `history.daily`'s `home` required now: turns PAPER's `desk/command.py` red. (2) Leave it optional for ever.
(3) Optional for now, ask PAPER to pass `home` (R-DATA-52), then tighten (taken: the only one that keeps main green and the lane wall).

### 2026-11-17 — 1h, 4h, 1wk rolled to the store's UTC marks (#760, R-RUNNER-216)

(1) Align rolled bars to the store's UTC marks, because the writer refuses off-mark bars (#739) (taken); a US first hour
(14:30) rolls into the 14:00 UTC hour with its one half hour. Re-aligning the writer is bigger and guard-adjacent.
(2) Base: 30m for 1h and 4h, daily for 1wk. A pulled bar always wins over a rolled one.

### 2026-11-17 — one-minute bars reuse `paper._five` with a placeholder start (#757, R-RUNNER-290)

`paper.py` is outside the claim, so `_five` is reused with a five-minute-mark start (only price and volume judged) rather
than given a span parameter. The cleaner end state, splitting `_five` in `paper.py`, is left as an optional tidy.

### 2026-11-17 — the unit rule needs 95% of shared days (#768, R-RUNNER-307)

UNIT_SHARE options: 0.9, 0.95, 0.99. Taken 0.95 (the request's wording; IB1T's 250 of 255 = 98% clears it). Days still
apart are named faults with the upper source's bar standing and do not park the line; the upper source (broker first,
then archive) still decides the unit.

### 2026-11-17 — the store split and the file ceiling (#764, R-RUNNER-288)

`desk/store.py` (400 lines) split: types, move limits and neighbour judging to `desk/store_parts.py`, re-imported so other
lanes' imports are untouched. It raised desk/ to 81 files against a ceiling of 80. (A) raise `product_files` to 81 in
`BUDGET.json` (recommended; loosening a guard, taken under his standing ruling of 13 Nov, announced on the pull request);
(B) merge another desk module, outside the claim. Main now holds the 95-file ceiling (#767).

### 2026-11-17 — the fault is a stderr line (#780, R-RUNNER-216)

A rolled bar disagreeing with a held one: (1) a new faults table, outside the claim; (2) a FAULT line on stderr from the
command (taken: smallest). The held (pulled) bar stays.

### 2026-11-17 — what moved in `lab/universe.py` (#784, R-RUNNER-289)

Moved the reading rule plus `matrix` (Stooq second source) to `lab/universe_parts.py`, not the ticker lists: the lists are
the module's identity and the rule stands alone. Options: lists only (too big a move for callers); rule only (350 lines,
not under 350).

### 2026-11-17 — quality monitor: daily timeframe first (#797, R-RUNNER-217)

Build all timeframes at once (over the 100-line cap) or the daily first, since `backfill.fill` already exists for it
(taken). No blind review was run (session time cap).

### 2026-11-17 — the parked cap is 10% of lines (#795, DAT-03, DQ-01)

Options 5%, 10%, 20%; 10% taken as the middle: 201 of 1,065 research tickers park today and the twenty trading lines should
park far fewer. Longest lookback 200 sessions (`desk/strategy.py`), five years 1,260. Taken under his standing ruling.

### 2026-11-17 — `command.py` is asked, not edited (#778, R-DATA-49)

Last piece of R-DATA-49: change `desk/command.py` myself (outside the lane's files, refused) or ask MONEY and PAPER to pass
`home` first (taken), then make it required.

### 2026-11-17 — quality monitor skips a line with no 30-minute bars (#811, R-RUNNER-217)

Options: skip such a line, or report it red as "no 30m". Chose skip, so the daily job is not red in production until every
timeframe is pulled; coverage per timeframe is the next step. `manifest.toml`'s description of `desk/quality.py` left as it is:
the lane guard forbids a lane editing existing descriptions.

### 2026-11-17 — deep history: store takes the sessions years (#819, R-DATA-54)

Option A, widen `venues.KNOWN` to 1993 and guard `hours()` separately (touches `bars_parts`' meaning, hides unknown hours);
option B, `desk/store.py` uses `venues.SESSION_YEARS`, the name the calendar already has for this. Took B, as the wrong value
arises there. It needs a claim naming `desk/store.py`. Overtaken by the next entry: B alone parks lines.

### 2026-11-17 — deep history: nothing landed without the whole fix (#821, #822)

Options: (a) land the `venues.py` split alone (KNOWN becomes the sessions years, a new HOURS_YEARS for hours, `open_at` None
before 2010); (b) land nothing and name the whole fix. Chose (b): (a) lets 2000-2009 in, and AAPL (2000-09-29), NVDA (2000-04-05,
2004-08-06) and AMD (2008-09-29, -30) would park as a lasting fault until recorded in `real_moves` in `desk/lines.py`
(canon A8, B1: safety before progress). #822 re-checked on main and chose (b) again, adding `desk/bars_parts.py:24`, which reads
`KNOWN` the same way. The whole fix is R-DATA-54.

### 2026-11-19 — a series' adjustment basis is read from its bars' sources (#870, R-RUNNER-217)

Options: add a basis column to the store (outside the claim) or derive the basis from each bar's recorded source (chosen, in
claim). IBKR and IBKR_DAILY form one basis, ARCHIVE and BACKFILL another, each old-desk source its own; a series mixing bases is
a named red fault that `monitor` prints. Restating a mixed series onto IBKR's basis is not built.

### 2026-11-19 — R-DATA-58 declined, the fresh pull kept (#872)

Options: (a) restore the nine US lines from backup/20261117T013018Z, (b) leave the fresh pull and open a question on the volume
basis. Chose (b): the live store already holds every backup day, the 20 differing sessions are fresh pulls with the old values
kept in `correction`, and (a) would put stale over fresh, undone by the next archive round. His ruling, take recommended. Open
question: which daily volume is the consolidated figure (R-DATA-59, waits: operator).

### 2026-11-19 — headstart pass takes its lines as a parameter (#901, R-RUNNER-349)
Options: (a) `whole` reads the line list itself; (b) the command passes `headstart_days.order()` in. Chose (b): the test then
uses one line, and counts are read from the readers' own lines, not a second tally.

### 2026-11-19 — desk/bars.py split along its schema (#905, R-RUNNER-381)
Options: (a) move the readers out; (b) move the Source list and the store's table and statement constants to
`desk/bars_schema.py`. Chose (b): the readers could not move without a circular import. `bars.py` re-exports the names, so
no caller or test outside the claim needed an edit (398 to 349 lines).

### 2026-11-19 — data-ingest: no separate persisted backfill list (#915)
Options: (a) add a backfill list beside the park; (b) keep the park (`keeper.parked_live`), which already bounds it. Chose (b):
keeper.py and bars.py sit at 390 and 398 of 400 lines and the unit tests have no margin. Sealing into compressed files waits
on a benchmark showing SQLite slowing; it passes today.

### 2026-11-20 — a session of today is closed once its closing auction has ended (#935, R-RUNNER-382)
Options: (a) the session's close time (rejected, the auction still prints after it); (b) the closing auction's end
(`venues.hours` `.auction`), the same bound `open_at` uses (chosen). `audit` and `monitor` now take the moment they run.

### 2026-11-20 — the rollup source waits for a claim naming desk/bars_schema.py (#940, R-RUNNER-217)
Options: (a) edit bars_schema.py anyway (the check refuses); (b) reuse an existing Source for the rollup (wrong provenance,
rejected); (c) land nothing and ask for the claim to include desk/bars_schema.py (chosen). Adding the member elsewhere would
make a second home for Source (#930 landed step 1 only).

### 2026-11-20 — no purchase of a breadth feed (#917, R-RUNNER-346, R-MONEY-35)
Options: buy a feed (NYSE, McClellan; spend is his hard line, refused); use unconfirmed scraped symbols (^ADVN/^DECN, no
free download, not re-checkable, rejected); leave the Zweig row out of the catalogue (chosen, as the request itself says).
Waits: operator.

### 2026-11-20 — the quality monitor goes red past the parked cap (#1037, DQ-01)
Options: report the coverage score only, or go red when more than 10% of lines stand parked. Chose red: the box asks for "a cap on the share of lines parked" and DQ-01 makes the desk unfit past it. Insufficient history on a line is reported in the score, not red, since new lines (3LGO) would alarm daily.

### 2026-11-20 — the coverage lookback has one home, the grid's sweeps (#1059)
Options: (a) keep `coverage.LOOKBACK` at a hand-written 200 (rejected: the grid's SWEEPS try settings up to 250, so it would
trade lines with too little history); (b) read the longest setting from `desk/strategy.py` SWEEPS (chosen): a line now needs 500
sessions, twice the longest lookback, before a rule may trade it, and the number is written once.

### 2026-11-20 — free disk is a share, checked at the command (#1098, #1107)
Options: (a) an absolute floor in gigabytes; (b) a 10% free share (chosen): it follows the drive. The check sits in the
`desk.quality` command's entry and in `monitor` through `disk(path.parent)` (#1107 wired what #1098 left uncalled), not inside
the monitor's other checks, so their tests do not depend on the test machine's disk.

### 2026-11-20 — the advances and declines come from our own bars (R-RUNNER-346, #1104)
Options: (a) buy a vendor series (spend, a hard line); (b) derive from the store's own S&P 500 bars (free, survivorship-biased,
chosen on his "go with recommended"); (c) no row. Any verdict using it must state that the list is today's members only.
