# The data lane

The data lane's own decisions, each a dated `###` entry saying what was decided, the
options, why, and the evidence; newest last. Only this lane's scribe writes here, so no
other lane's pull request touches these lines. Held to a size a session reads whole
(`BUDGET.json`, `max_lines_per_lane_doc`): when it is full, the scribe folds the oldest
settled entries into one short summary entry; git keeps every word.

## Decisions

### 2026-11-13 to 14 — the first day's decisions, folded (the oldest settled entries)

Sixteen entries, each settled and built, folded into one; git keeps every word (the file
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
- *The next boxes* (#66): their order, the keeper's road and the store's name.
- *The twins* (#85): VUAG, EQQQ and IDTL in the master with an ISA flag and a retail flag
  on every line, GLD out, the yardstick VUAG.
- *Hours* (#87): every session's open, close, auction and half-day in UTC from one calendar.
- *The fast store* (#89): SQLite in WAL mode, whole rounds, exact decimals, benchmarks held.
- *The lists' members* (#96): S&P 500 and Nasdaq 100 by day since 2010; `on` refuses the rest.
- *Five-minute bars saved for good* (#97): through the daily store's checks, each evening.

### 2026-11-14 — the head start, currency and store rules, folded (#175-#254)

Settled and folded; git keeps every word. The old desk's five-minute bars, and later ibkr_store, Stooq and
mark_the_trend files and the old database's daily rows, are read as a head start into the fast store, daily fill-only
(#175, #236, #238, #245, #254). Currency steps are judged by the day's pound, with recorded splits and London-midnight
dating; a long run of dollar-quoted bars is dropped (#217, #220); the six parked London lines came out clean (#222).
Every rule and constant of `desk/store.py` is pinned by a row of one synthetic table, and that guard was driven red
(#225, #227, #230; R-RUNNER-43, -46). The lane's open boxes were put in working order (#180).

### 2026-11-15 — the head start recognises adjusted prices against the as-traded store (R-RUNNER-90) (#286)

- (1) Dividends are not recorded on Line, so "explained by recorded splits and dividends" is:
  any product of the line's recorded split ratios (or inverses) times a dividend factor within
  0.85 to 1 (old stores cover months; an FX rate 0.66 to 0.81 is never taken as dividends).
  Options: widen the band (risks taking pounds-as-dollars as adjustment), or record dividends
  on Line (another lane's file). Chose the narrow band; a heavier adjustment is still refused,
  by line and day. (2) Bars on an adjusted day are not taken at all rather than converted back
  to raw (conversion would invent as-traded prices from a factor). (3) AGREE stays 0.0001; a
  factor must hold within 0.001 and differ from 1 by more than that. (4) Operator ruling
  "always go with recommended": the red was only the Claim line; claim corrected, no code
  changed. (5) The remaining head-start work is re-cut as a new job, "adjusted vs as-traded
  matching rule for the old daily bars (SMGB split, SGLN off-mark bar)", in a new module such
  as lab/headstart_match.py with its test; PLAN.md's stale "waits: R-RUNNER-24" text needs
  correcting and the DATA lane restarting on data-deep-history or data-two-stores. PLAN.md is
  outside this claim, so the scribe or next session does it.

### 2026-11-15 — the store holds each venue's closes within 39 minutes of its close (R-PAPER-23) (#294)

- the request names `keeper.target`, but that is already the function giving the day a venue
  is readied for (used by the keeper); options: rename it, or name the figure beside it. Chose
  a new constant `HELD`, leaving `target` alone. The test was driven against a deliberate
  break (target turning at 2x SETTLED): three keeper tests failed.
- Decisions (DATA lane ruling, his words "always go with recommended"): data-headstart stays
  held; the lane restarts on data-deep-history or data-two-stores. Options: wait for him, or
  restart on those two. Chose the restart. The head start's remains are re-cut as a new job,
  'adjusted vs as-traded matching rule for the old daily bars, SMGB's split, SGLN's off-mark
  bar' (lab/headstart_match.py plus its test), and PLAN.md's stale 'waits: R-RUNNER-24' text
  needs correcting; both are for a later pull request, outside this claim.

### 2026-11-15 — VUAG's archive gap of May-June 2019 is filled from a checked shelf, never forward-filled (R-RUNNER-104) (#314)

- (1) Real prices from the old desk's Stooq bars via the shelf, vs marking VUAG suspended 23
  May-18 Jun 2019 (it did trade) vs softening the desk's refusal (forbidden). Chose the shelf:
  real, sourced, no special case. (2) With a shelf, discard all frozen filler rather than only
  covered days, so a partial shelf cannot let filler through.

### 2026-11-15 — every line's venue has a calendar and every SimCity world is dated on trading days (R-RUNNER-107) (#315)

- worlds are read through simcity.run (the only public entry) with `_live` swapped for a
  recorder, as test_simcity already does; simcity.py untouched. Planted breaks and their
  failing messages are in docs/DECISIONS.md.

### 2026-11-15 — research refresh command, python -m lab.universe (R-RUNNER-116) (#349)

- "lines refreshed" counts every line the run handled, parked or not (options: only lines that
  gained bars; I chose all handled, so zero means the run handled nothing, which is the fault
  the night job looks for). "Today" is the UTC date.

### 2026-11-15 — a bar with only a bad high or low is kept and repaired (R-RUNNER-175) (#367)

- Second source — the store has no checked second source per day inside the cleaner (shelf
  bars are joined before cleaning and win only by archive priority), so options were (a) wire
  a second source in, (b) clamp. Took (b), the request's stated fallback, with his rule "go
  with recommended"; (a) would grow the store.

### 2026-11-15 — the keeper cleans kept history again when the store rules change (R-RUNNER-182) (#374)

- version = hash of store.py's whole source (options: hand-kept constant; hash of the rules
  only). Chose the hash: no one can forget to bump it; cost is that a docstring edit in
  store.py re-cleans once, which is cheap and safe.

### 2026-11-15 — a missing yardstick day is a named data fault, filled from a second source (R-RUNNER-179) (#376)

- second source = the Stooq matrices (options: market.db five-minute bars, which start Feb
  2026; the Stooq parquet, which needs pyarrow reads) because the matrices hold the day, are
  daily and need only numpy. Without a second source the day is reported, never invented.

### 2026-11-15 — an impossible low is repaired like an impossible high (R-RUNNER-185) (#381)

- Requirement change by his ruling 'get to green' (second source: the old Stooq store proves
  VUAG 2020-03-16 low was 34.72, not 11.64): a one-day low spike with open and close in line
  is a bad print. Options for a recent repair: park the line (as the high repair already does)
  or not; chose to keep the existing behaviour (recent repair parks) so recent trading data
  stays under suspicion; old repairs like VUAG 2020 do not park.

### 2026-11-16 — no change - R-RUNNER-11 waits on a PAPER test edit (closes #422) (#424)

- Option A, loosen the guard for one file: refused (guards are not loosened for convenience).
  Option B, keep the keeper's store named bars.db: refused, it defeats the box. Option C
  (chosen): ask the owner to make test_command.py name the store through the constant
  `desk.keeper.HOT` instead of the literal, which works before and after the rename; then DATA
  re-lands 55977a3.

### 2026-11-16 — the store is two databases, long and short (R-RUNNER-11, first step) (#442)

- the long database is placed beside the short one and named by the writer, not by a setting,
  so that every existing caller (which passes the short database's path) is unchanged; option
  B was a data-folder argument, rejected because it edits other lanes' files. Recommended and
  taken.

### 2026-11-16 — the free collector, once a day: price second opinions, macro series, earnings dates and timestamped news into the one store (R-RUNNER-15) (#460)

- Where to keep it - options: a new database, or tables beside the daily bars; chose tables
  (raw, fact) in market_history.db, since the order was "the one store". Price day - the last
  weekday before today (the 22:15 run sees a settled day). A free tier's holiday gives no
  bars, not a fault.

### 2026-11-16 — no change - R-RUNNER-11 waits on two PAPER test lines (#454)

- Reverted the rename instead of widening my claim, because the lane guard refuses files
  outside the lane (canon A9; no red merge, A1.4).

### 2026-11-16 — the archive's daily answers kept raw and read instead of asked again (R-PAPER-24) (#458)

- key is (line, day) since the daily question is fixed by those; a kept file is never
  refreshed within its day folder (a new day is a new folder). Options: a time-to-live, or
  hash keys; chose the simplest.

### 2026-11-16 — SPY kept from 29 January 1993 as a reference series (R-RUNNER-94) (#303)

- Where to hold reference bars - (a) store.py (would pass its 400-line cap), (b) new module
  desk/reference.py (outside the claim, went red), (c) archive.py, chosen. Calendar: the
  reference series is checked without a calendar (weekday only) rather than extending
  venues.py back to 1993, which is outside my claim; recommended, taken.

### 2026-11-16 — the keeper keeps SPY's history daily after the US close (R-RUNNER-96) (#475)

- A refused reference fetch is told in words but is not a miss (nothing is traded on it;
  options: count it as a miss, which would wake the operator over a research series;
  recommended and taken: not a miss, retried at the next call per his "always go with
  recommended"). Reference bars are kept under the daily store's US folder (desk cannot import
  lab; this is the one store's own folder).

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
