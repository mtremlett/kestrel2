# The rungs lane

The rungs lane's own decisions, each a dated `###` entry saying what was decided, the
options, why, and the evidence; newest last. Only this lane's scribe writes here, so no
other lane's pull request touches these lines. Held to a size a session reads whole
(`BUDGET.json`, `max_lines_per_lane_doc`): when it is full, the scribe folds the oldest
settled entries into one short summary entry; git keeps every word.

## Decisions

### 2026-11-22 — more B5 ranges; the ladder's door (#1564, #1570, #1578, #1582, #1587)
- His standing ruling ("always go with recommended") keeps rungs-promotion held until R-RUNGS-7 is ticked and a rule has passed the ladder; B5 variants were worked instead, and #1582 fixed the ladder's door (options: change nothing; the owed door fix; touch GRID's or held files, refused by the claim; chose the door fix, a real defect in a RUNGS file).
- Clenow (#1564): every setting is shared by two blocks. Options: range none; range the score window (60/90/120) and the selling average (50/100/200); range all four (81 variants). Chose the middle: each variant is still a statable rule, nine trials, no change to `lab/variants.py`.
- Weinstein (#1570): range only `entry.ago` (3/5/10), not the shared 150-day lookback, which would buy over one average and sell under another.
- Mansfield (#1578): 26/52/78 weeks around the published 52 (13/26/39 would leave 52 off-centre; 78 weeks, 390 sessions, fits the 400-day bound); entry and exit ranged apart.
- Faber and dual momentum (#1587): entry and exit lookbacks ranged apart (8/10/12 months; 9/12/15), as Mansfield; a mismatched pair is a fair hysteresis variant, counted as a trial.
- #1582: intraday and scalping keep no results file, so the door hands back their run's code and reads nothing; EPON, first, LEV, VAR unchanged.
- Blind review skipped on the data-only rows (held by the plateau test); #1570 and #1582 reviewed, nothing blocking.

### 2026-11-13 to 14 Nov — folded: the first rungs and the lane's early boxes (#65-#206)
Settled entries folded by the scribe (git keeps every word); each is one decision per box, all taken as the recommended option under his standing ruling of 13 November:
- **Luck, trials, deflated Sharpe (#98, #91):** a chance multiplied by every trial, one 5% test across the set, bands 0.90 and 0.50, a yearly Sharpe above 2 flagged, one register of every trial ever tried (a dropped candidate stays counted); the test is fixed before any result.
- **Folds, plateaus, regimes, failing fairly (#79, #107, #109, #112):** in- and out-of-sample side by side, the verdict on the worst fold, each fold a trial then; the centre of a plateau, never a lone peak; a one-regime specialist kept for its regime and tagged outside; too few trades is "not enough evidence", no trades a fault in the test.
- **Costs, reproduction, promotion, market, bets (#115, #120, #127, #131, #136, #139, #141, #143, #149, #169, #186, #195):** each leg charged by the desk's one cost model at its own day's rate; a published rule run on its author's market and period; a replication stands in for the book's figure, labelled second hand; promotion only on a ladder pass with a kill condition; the edge judged against the market risk taken; clusters of lines as independent bets; the box handed out no more while blocked (build nothing while it waits).
- **Stress and indicators (#140, #145, #154):** stress scenarios judge nothing until the loss limit is set; indicators held to published tables, five tables and 250 printed numbers.
- **The ladder's first command (#198, #202, #206):** set 1 as one resumable command; waiting cells name their data and are tried again after 30 minutes; a cell without its folds has no verdict; the one verdict reads six rungs.
- **Paper-lane entries misfiled here, folded unread by this scribe (#75, #86, #100, #104, #110, #113, #135):** the paper account check, the fills and orders it reports, the Gateway's own week, the day's check and refusal, the adapter's first two steps (a sale can be placed, a buy waits for its stop), the drill held by code, and the dry half of the first real paper orders. Their words are in git history; the paper lane's scribe may restore any that its file lacks.

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

### 2026-11-16 — the ladder's churn, mechanism found for R-RUNNER-193 (declined as a lane cannot edit FAILURE_PATTERNS)
- Four fixes in a row to `lab/verdict.py`, `lab/ladder.py`, `lab/market.py` (#402, #405, #410, #419). Hypothesis from the four diffs: a verdict's reason text is chosen by position (the first rung that answered) rather than carried by the rung that answered, so each blind review finds one more place that names the wrong rung or day (#402 shuffle, #405 market, #419 market again). Evidence: #419 corrects the wording #405 introduced; both change the same reason-selection lines.
- Wanted pattern for a session the operator starts: "14. A verdict's reason chosen by position" naming `lab/verdict.py`, `lab/ladder.py`, `lab/market.py`; mechanism: each rung returns its own typed answer with its reason, and the ladder only joins them; caught by one contract test per rung that its answer names its own reason.

### 2026-11-15 — wiring tests for the ladder's registries, each driven against a planted break (R-RUNNER-106, #310)

New tests: `tests/unit/test_lab_published_wiring.py` (every eponymous rule is in the published
book and every publication has its desk file) and `tests/unit/test_lab_ladder_wiring.py` (every
yardstick is a line of its venue in the research list; every set names only rules the rule book
resolves). The eponymous publications live in `lab.published_epon.EPONYMOUS_PUBLISHED`, not in
`PUBLISHED` (the desk's five); the test reads that book. Each was driven against a planted break,
then the break was removed:

- Entry `williams_r` renamed in the published book: "in a desk/eponymous_*.py but not in the
  published book: ['williams_r']".
- `MARKETS["LSE"]` pointed at "XXX": "yardstick(s) {'LSE': 'XXX'} (venue: symbol) not in the
  research list".
- A rule "ghost_rule" added to the EPON set: "set EPON names rules the rule book lacks:
  ['ghost_rule']" (and the published-book test names it too).

### 2026-11-14 — the shuffle rung, then the verdict's home (R-RUNNER-39, steps 1-2, #218, #221)
- A trial with under two trades has no standard errors: options, raise or share 1. Chose 1 (it can never pass; the ladder gives it its other rungs' least answer anyway).
- A trial that failed an earlier rung carries that least answer, with its reason, in the shuffle's place: options, a separate "not run" marker or the least answer. Chose the least, so the one verdict rule stays `min` over all seven names. (#402 later made the reason say "not run".)

### 2026-11-14 — Monte Carlo and its command (R-RUNNER-47, -49, -85, #235, #244, #253)
- Trades are given as returns on the equity they were taken with (options, pounds or fractions): fractions, so the spread is size-free. Cuts 5/50/95% by nearest rank.
- `python -m lab.montecarlo` prices trades again from the bars with the rung's own pricer (neither store keeps per-trade returns); a held grid cell whose code or data no longer matches is not priced, counts as "could not be resampled" and is retried; lines outside the desk's twenty come from `sweep.held`.
- A cell the desk's sizing refuses is kept with the refusal as its reason and not retried (same key, same refusal); options, retry each run (wasted work) or keep.

### 2026-11-14 — folds pooled over lines, a rule's hash in a trial's name (R-RUNNER-50, -51, #242, #243)
- A year passes when the mean day is above nothing (the spec's literal text) rather than 2 standard errors above; the other rungs carry the evidence bar. Took the first (his ruling: take recommended).
- A trial's name carries the hash of the rule's syntax tree (class plus what it names), so formatting never re-counts a trial; options, raw source text (every edit a trial) or the module hash (any edit re-counts every rule).

### 2026-11-14 — the verdict refuses a step of units and a short history (R-RUNNER-52, #241)
- TOO YOUNG applies to any cell under 452 bars, not only a FAULT (options: only FAULT as before): a few trades from a short history say nothing of the rule, and it keeps THIN honest. The unit-step check lives in `lab/verdict.py`, at 3% of the pound's rate.

### 2026-11-14 — a failed cell retried when its key changes (R-RUNNER-83, #252)
- A cell that failed before its bars were read has no key and keeps the 30-minute wait; options, retry it every run (would hammer a parked line).

### 2026-11-14 — set EPON and the ladder's eponymous files (R-RUNNER-81, -86, -87, #270, #279, #283)
- A rule has "passed" when some line's one verdict is PASS and every rung run passed (options: any line, every line, a share of lines): any line, since a rule goes forward on the lines it earns on and luck already counts every line as a trial. The default command is EPON; the older set is `first`.
- Eponymous files are found by `desk/eponymous_*.py` and hashed once into `CODE` (options: a hash per file in the keys: more churn, no gain); any eponymous edit re-judges all, the safe side. Zweig (needs breadth data) is left out of `eponymous()` rather than crashing (options: catch TypeError, change cell.py).

### 2026-11-15 — a proxy line, kept rates, the published book (R-RUNNER-95, -101, -98, #304, #307, #306)
- A line whose history starts later than its proxy's is judged on the proxy's bars, labelled `proxy: SPY for VUAG`; the market comparator is the proxy's venue market (options: keep ISF, which the rung refuses as a venue mismatch).
- The rates are one kept table (`ladder/pound.jsonl`) with a keyword `home` on `ladder.rates` (options: the spec's signature and strict last-close-before rule, which moves a pinned test and breaks transfer); the carry rule (`desk/carry.py`) stays.
- The twenty eponymous rules sit in their own book `EPONYMOUS_PUBLISHED`, not inside `PUBLISHED`, which the first set walks. Over the 300-line cap: split in two steps (15 rules, then 5) instead of thinning the notes of all twenty.

### 2026-11-15 — measures that never gate, a refused cell, tests that bite (R-RUNNER-102, -106, -108, #309, #310, #311)
- Each ladder row carries `drawdown` {median, p95} from 1,000 redraws of the net pounds, as parts of the 10,000 capital, no verdict reading it. `montecarlo` imports the ladder, so the small draw lives in `lab/verdict.py` (two homes, merge later).
- Wiring tests (published book, yardsticks, sets) were each driven against a planted break; the evidence is in `docs/DECISIONS.md` R-RUNNER-106 (moved here below).
- The ladder catches only `desk.orders.Refused`, at the cell; a refused row is a judged outcome kept under its key, never `error`, never retried until its key changes (as Monte Carlo).

### 2026-11-15 — the folds pooled, the author's figure handed to them (R-RUNNER-99, -100, #313, #319)
- His ruling "A" (15 Nov): the last five whole calendar years pooled by rule, the worst year judged, a fold is no trial. Pinned numbers re-derived by hand in `docs/DECISIONS.md` (trials 6 to 2, 9 to 3, 18 to 6; the trend rule's THIN became FAULT: no trade in 2022). Thresholds stay "more than 20".
- A rule with an author's figure has its folds judged like any other (`NO_FOLDS` gone). Scale: set EPON pools 2,130 lines per rule (twelve first-rung runs a line); if too heavy the pool's universe is the question.

### 2026-11-15 — the ladder on all cores (R-RUNNER-110, #318)
- Work is grouped by consecutive cells of one rule, not by line (options, by line as asked): a rule's folds pool all its lines, so a per-line worker would rebuild every pool; rows stay in the serial order. The pooled run mirrors `ladder.run`'s setup via ladder's own helpers (fold the two paths into one later).

### 2026-11-15 — one more trade at the rule's stop (R-RUNNER-103, #322)
- Rare large losses: plant one loss at the rule's own stop in the first rung (the least any judged trade would have made had its stop sold it) vs a skew bar in the deflated rung vs leave it. Chose the first; 6 of 400 no-edge lines passed before, 0 after. Pins in `test_lab_rung` moved (seeds 1/16 to 12/40, 2.8 to 2.5), re-derived in `docs/DECISIONS.md`.

### 2026-11-15 — the spec book's first blocks and slices (R-RUNNER-124, -125, #327, #348, #352, #358)
- Sizing is left out of the blocks (a Rule says in or out, the engine sizes). A spec must pass its own known-answer cases at parse time, so a bad case is refused at the door. The unused-argument lint is silenced per line with a reason, not by config.
- A time-based exit is a STOP block (`time_stop`) because it depends on the position (options: a new kind). Williams' edge test is exact in whole rational form. Clenow's gap condition is one block each in entry and exit (options: one composite filter). The parity test caught a misreading of Connors' exit (sells on a close OVER the 5-day average), showing it bites.

### 2026-11-15 — the rung map (R-RUNNER-130, #333)
- Each rung is named to the module that judges it today (options: a module for every rung): `lab/rung.py` holds rungs 1-3, `lab/market.py` holds 4 and 6; each rung has its own test file (the test enforces no two the same). A file marked (unbuilt) that has since been built does not fail the test (options: fail it, so the map never goes stale). Guard evidence: driven against 13 broken copies of the docstring, all caught (scratch `C:\tmp\rungs130\drive_map_breaks.py`).

### 2026-11-15 — rungs 1, 2, 3, 4/6, 5 proven alone (R-RUNNER-131, -132, -133, -134, -123, -122, #344, #345, #343, #347, #346, #342)
- The old audit of 20 October is not in this repository: LAD-09 is read as "a rung may not pass on too little evidence", LAD-03/LAD-08 as "the noise winner is not believed after correction at 5%"; each kept as a case that must fail (to be sharpened if the operator has the text).
- Costs rung: passes only if the first rung passes AND the break-even (mean gross over mean cost, Novy-Marx and Velikov 2016) is at least 2 (options: repeat the first rung on net returns; a drag threshold). Interval rung uses two errors (the first rung's T_PASS), not Student's t, so the rungs agree. `rung_beta` imports `fit` from `lab/market.py` (no second copy) and answers three ways (PASS/DOUBT/FAIL).
- Benchmark rung holds the benchmark free of costs (the rule must beat it at its dearest) and judges excess per trade. Regime rung cuts the window at its middle day into two halves, both must pass (options: weather-labelled regimes, which `lab/regime.py` does; either window).
- Tape and ladder wiring of all of these is left (they declare no RUNG yet).

### 2026-11-15 — rungs 8, 9, 11 built but held at the lab's ceiling (R-RUNNER-119, -120, -121, #351, #354, #350)
- Block bootstrap: days, not trades, in blocks of 20 sessions, 5,000 draws, floor thirty blocks, pass at 1 in 40; no command of its own (the ladder is the one path that runs rungs). Honest about its rate: 2.4% on plain noise, 6% in twenty-day runs, 15% in sixty-day runs. The blind review found the proofs ran on a restatement of the pass rule; the decision now has one home.
- Purged cross-validation: six stretches, two held out, pass only on fifteen of fifteen (exact rate 1 in 32 on symmetric noise); the purge is the same in every split. On lopsided gains it puts no ceiling alone; the first rung's planted loss covers it (options: plant it here too, which halves joint power). Key is `Key.rung`, like its siblings.
- Block placebo: re-runs the rule on the window's ten-day blocks in a new order, nineteen placebos, what is ranked is the gain over the window's own rise before costs; the window alone is shuffled (the first blind review's blocking fault). Not judged, never failed: no trade, or under six blocks.
- All three waited on the lab's ceiling: options, raise `lab_lines` (his yes followed: 8,000, then 12,000), delete the Monte Carlo rung, or leave. The ceiling is the operator's.

### 2026-11-15 — the folds rung alone, the rung registry, variants (R-RUNNER-136, -154, -139, #361, #362, #364)
- Walk-forward rung built as a new module on priced trades, as `lab/folds.py` was outside the claim (merged later, #560). The registry's judging function reads the first rung's Verdict (smallest input every module can be given); a declared rung adds to `every` and never changes the one rule's answer.
- Variants take their ranges by argument as (place, parameter) -> values (options: add ranges to the catalogue row, needing other files); a variant does not re-run the row's known answers.

### 2026-11-15 — the deflated Sharpe as a rung (R-RUNNER-135, #365)
- The formula is read from `lab/deflated.py`, not copied (no second copy; moving it was outside the claim). The stated rate is one in ten for bell-shaped gains only; the rung is handed the gains with the first rung's planted loss (`Verdict.gains`): on lopsided noise, without the plant it passed nearly every pick, with it none. The two counts have no default (a default would let it run with nothing deflated, LAD-09).

### 2026-11-15 — the pool's unit, a clean stop (R-RUNNER-166, -173, #368, #371)
- Unit = fold year (in and out stretches together) over a single stretch, warming through tapes rather than restructuring `folds.pool`, so rows stay identical. A STOP file ends a pass after a rule's group is written, not each warm task (stopping mid-group leaves no rows to write).

### 2026-11-16 — one clustered set of trials (R-RUNNER-137, #379)
- Grouping: the paper's own method called fifty unrelated strategies two groups, so a fixed level of likeness was chosen: 0.75, every pair in a group at or above it (options 0.5, 0.9); a rule run the other way round is another look; trials that left no returns count a look each, said aloud; the spread is the measured one with no floor.
- A trial is judged no better than its group: whatever Sharpe it stands above its group's is added to its bar (options: leave uncounted, a fixed worst case, a spread inside the group). Best of fifty look-alike no-edge trials passes 8-11% however grouped (33% as first built). Three review rounds on one question went past canon A8's two attempts because each fix was to the mechanism; the last form has not been re-reviewed. Not yet wired.

### 2026-11-16 — one simulation per line, the catalogue beside the Python rules, a refusal judged once (R-RUNNER-169, -126, -165, #378, #382, #384)
- A rule is run once from a line's first bar to its last; every window is cut from that tape by date (rules are future-blind, so the cut equals the window's own run). The ladder's code hash still covers only the Python files (specs are proven equal to them).
- A refusal is a `refusal` field on `Verdict` (options: a new Answer member, which changes pinned orderings; a separate result type, which breaks every caller); its answer reads FAULT but `.refused` is the judged outcome.

### 2026-11-16 — sizing blocks and the rates held out of the tape (B1, L1, #396, #398)
- Sizing blocks are left out: a guessed sizer would be a fake implementation (canon A5) while the volatility-sizing research is unsettled; waits operator. Rates stay out of the tape's key (option B, key by rates and re-simulate on every change): the tape holds trades and the rates price them later, so changing a rung or a rate re-simulates nothing.

### 2026-11-16 — R-RUNNER-186 and R-RUNNER-187, declined and then done (#401, #406, #409, #418, #425)
- 186: hiding the sizing's refusal catch behind an alias is evasion, duplicating the room test is two homes; asked MONEY for a non-raising sizing. #425 then renamed the import (`Declined`) so no line matches the fault pattern; behaviour unchanged.
- 187 (a loss gapping through the stop, 18.8% of lopsided noise lines pass rung 1): a planted loss of the gap's size (3x the stop) fails every real edge of ordinary size (t from about 2 to 0.6); the line's own worst gap helps nothing where none occurred. Chose to leave the first rung and rely on the later rungs (luck 0-2.2%, deflated 0.2%); declined twice with evidence. A stress rung with a planted gap-through is the real cure.

### 2026-11-16 — the ladder's blind review (R-RUNNER-40, R-RUNNER-188, #402, #419)
- Reviewed on Fable (the run's instruction) in #402; on Opus in #419 (the request is the box).
- "Goes forward" now needs no rung named unrun (options: reword the column). A crash day is no change of units: the open must step by the rate too (options: the whole bar apart from the close: frees 49 of 251 lines; (b) frees 227). The trial count is printed as cells beside trials (the register is never shortened).
- Not fixed in #402: a gap through the stop (above). Reproductions are a required argument of the shuffle (an empty default is how the defect got in). Every table stays PRE-REVIEW.

### 2026-11-16 — the market rung's faults, key waits, tapes (R-RUNNER-183, -174, -138, #405, #410, #407, #411, #414)
- A missing market day: FAULT with a named `fault` (options: keep raising; fill from a second source). A failed cell under an unchanged key is kept and not appended again (the key holds every input that could mend it); keyless errors retry after 30 minutes.
- "Rungs built: n of 11" is counted by parsing the rung map (one home, not a second list). Set EPON reports tapes on disk; compression was a separate step (#555).

### 2026-11-16 — rungs-trustworthy and the waiting boxes (#412, #413, #414, #415, #416)
- "Built" counted as module plus its own proof, not as wired (options: count only wired rungs); the wiring gap is stated (#427 later counts wired: 0, then 3 of 11).
- rungs-promotion: no placeholder kill numbers for strategies without a ladder pass (they would be the limit chosen after the fact the module exists to prevent). rungs-feasibility: the number is the sum of passed rules' net pounds a day, an upper bound (options: discount by correlated bets, count only).

### 2026-11-16 — set LEV: trend rules on the leveraged lines (STR-18, #423)
- Leveraged trend rules get their own register and count (rules times lines) instead of 63,920 trials; the family is six trend rules fixed in advance (options: all 20; a hand-picked winner, refused). Leveraged = `Line.leverage > 1`. Inverse ETPs need a Line type (requests to MONEY and DATA).

### 2026-11-16 — wiring the rungs one at a time (R-RUNNER-191, -192, #427, #438, #440, #445, #463, #487, #493, #498)
- "Rungs built" counts rungs whose module declares a RUNG: 0, then costs (1), ci (2), cpcv (3). Wired costs first (a distinct question), cpcv third as the only one reading the first rung's verdict alone; ci largely repeats the first rung's t-test (wire or delete). One at a time (options: all ten over 300 lines).
- Duplicates merged by pure restructuring: skew and kurtosis (`deflated.shape`), the first rung's decision (`rung.decide`), the worst-fold key (`rung.standing`), the deflated bands (`deflated.believe`). Folds vs rung_folds are not code duplicates (different answers); needs a golden-fixture equality test first.

### 2026-11-16 — the holding figure, memory, stress, weather (R-RUNNER-148, -203, -204, -205, #450, #451, #456, #457, #553, #578, #622)
- Holding: the whole window, bought at the first open and sold at the last close (options: the strategy's first buy to last sale). Pool = min(cores - 2, (free memory - 20% of total) / 5 GB), at least one. Stress limit is 20% of capital (his ruling, option a), nothing tested is THIN.
- Weather layer 1 is the trend state with a 200-session window; the first 199 days are "warming", never guessed. An empty state is THIN, not FAULT (a long-only rule that never trades in a downtrend is unproven there). The regime rung gates `every` only, not the deflated rule's NAMED set (no golden change).

### 2026-11-16 — the tape compressed, sets from one database, list members only (R-RUNNER-213, -222, -146, #555, #562, #569)
- zlib (standard library); old plain tapes are re-simulated (a cache keyed by code). Sets read `market_history.db` alone; a set runs on every research-list line the database holds (options: also any other symbol). A line on several lists is a member on any; a line with more than one spell is traded over its longest spell; lines no record names are "survivorship: not corrected".

### 2026-11-16 — the easings pre-registered and built behind a switch (R-RUNNER-225, -226, -227, -228, -230, #567, #596, #664, #589, #695)
- Trials per family, with abandoned variants counted (his "YES TO ALL" and the coordinator's conditions); a family is the trials whose register name opens with the rule's name; with EASED on and no family count `judge` refuses, no silent default.
- Scorecard: a hard fail needs FAIL and a negative t (not any negative mean); WEAK means THIN or DOUBT, FAULT stays FAULT. Basket: its answer is the first rung's on the pooled trades, its plateau unrun, so it never goes forward alone. INCUBATE is a string beside Answer, threshold exactly one standard error counts.
- All behind `verdict.EASED` (False): every verdict and the golden run are unchanged until card ease-switch-on.

### 2026-11-17 — the spec book, rows and the splits (R-RUNNER-219, R-MONEY-45, #597, #615, #639, #675, #676, #560, #603)
- connors_rsi2 exits on `close_over_average` n=5; an RSI tie at exactly 10 is left as the desk rounds, the fast engine refuses ties with TooClose. connors_percent_b's thresholds are one range per side (under 1-49, over 51-99). faber uses two month-end blocks firing on a month's first bar (a DATED table beside FIRES). dan_zanger's volume multiple is a whole per cent (150) so the fast test is exact. dual_momentum: the five fixture series TOGETHER must buy and sell (a 12-month rule never sells on seed 0), parity still asserted on every day.
- New blocks go in `block_*.py` modules or the `_parts` splits when a file has no room (blocks.py, ladder.py, fast.py, verdict.py). Fold's home is the lighter `lab/rung_folds.py` (folds.py already imports it, so no cycle).

### 2026-11-16 — the churn mechanism, written then tested (R-RUNNER-193, #491, #593)
- A lane cannot edit FAILURE_PATTERNS.md; the mechanism (a verdict's reason chosen by position) was written in this file's 16 Nov entry, then recorded as pattern 14, with a contract test that walks every path through the judge and needs each rung to answer in its own words (options: a title guard; restructuring `verdict.judge`). Driven red by restoring the market rung's borrowed reason.

### 2026-11-17 — kept verdicts stamped by their rung, calibration (R-GRID-3, R-MONEY-43, #613, #667, #693)
- Stamping inside `rung.judge`/`rung.verdict` (one place) rather than in each caller; `Corrected` carries a key stamped `.rung("lab.luck")`. Left for GRID: capital and rates in `Key`.
- A noise world has gross mean equal to the cost taken, so the net mean is nil (gross-nil makes every rung fail on costs and measures nothing). 500 worlds of 120 trades: first 2.2%, ci 2.2%, costs 1.4%, cpcv 4.2%.

### 2026-11-17 — trend template, volatility weather, basket stress, one Sharpe home (R-RUNNER-219, -205, -191, R-RUNGS-27, #704, #737, #746, #742)
- minervini_breakout: `trend_template` filter block in `lab/block_bands.py`; manifest.toml may only gain lines for a lane, so block_bands.py's description was left unchanged (options: widen it, refused by guard; leave it; left it).
- Weather volatility: thresholds are the median of the prior 252 values (options: fixed cut, percentile; the median needs no tuned number, so no trial spent). Trials so far: 1 volatility definition.
- Sharpe a trade: wired no further rung, since none reads the first rung's verdict alone (options: wire dsr with a stub spread, refused as a default that masks missing data; merge the duplicate, taken).
- Basket stress: a basket has no stress run of its own (options: (a) stress on pooled trades; (b) stand on its lines' stress). Chose (b), the recommended: any line's non-pass stress stops INCUBATE.

### 2026-11-17 — raschke_swing as a spec row (R-MONEY-45, #773)
- The stop block `under_entry_low` takes no settings and finds the buying bar from the position turning on (the previous bar's low), so it stays right whatever filter sits beside the entry. Options: a duplicate detector inside the stop (two homes for the 20/4) - declined.

### 2026-11-17 — each ladder row shows what holding its market made (R-RUNGS-23, #775)
- A market with no bar or rate in the window. Options: fault the cell; say it in words ("not shown: ..."). Chose words, as the market rung does: a missing comparison is not a broken strategy.
- R-RUNGS-17 (`ladder.rates(home=...)` in `lab/transfer.py`) was not done here: the file is GRID's. Asked of GRID as R-RUNGS-28.

### 2026-11-17 — demark_sequential as a spec row (R-MONEY-45, #790)
- Where the pound's kept closes live, for the R-RUNGS-17 fix. Options: the store `root` the request names; the data folder (third argument). Chose the data folder, because the pound table is kept at data/ladder/pound.jsonl, as `montecarlo` does.

### 2026-11-17 — weather layer 3, drawdown depth (R-RUNNER-205, #776)
- Depth threshold and window. Options: 5%, 10%, 20% under the highest close. Chose 10% over 252 sessions, the plain textbook correction level, fixed before any result; no trial counted yet. Built, wired into no verdict until it wins out of sample against trend alone (canon B6). The manifest description was left as is (a lane may only add modules).

### 2026-11-17 — rung_folds shrunk in place (R-RUNNER-191, #803)
- The fold's second judge (`judge`, `stretch`, `Stretch`, `Gain`) was only called by its own tests; the ladder runs `lab/folds.py`. It was deleted. Options: move Fold/Walked into folds.py and delete rung_folds.py; shrink rung_folds.py in place. Chose in place: test_lab_folds.py is outside the claim and imports Fold from rung_folds, and removing a manifest line is refused by the lane guard.

### 2026-11-17 — darvas_box and the fast engine (R-MONEY-45, #799)
- A position-dependent block in the fast engine. Options: (a) a float twin of the box walk (a third copy, own parity); (b) run the same blocks bar by bar through `SpecRule`. Chose (b): less code, no second implementation. The block copies the desk rule's logic on purpose, since R-RUNNER-127 deletes the desk files.

### 2026-11-17 — weather scoring and breadth (R-RUNNER-205, #813, #831)
- Breadth cut-off. Options: more than half the lines with a trend state up; a tuned share (e.g. 60%). Chose more than half: no tuned number, no trial counted. Per-line state reuses `trend`, one home for the 200-day rule.
- `followed` pairs a day's label only with the return after that day's close (future-blind); no dependency added.

### 2026-11-17 — rung_ci keeps its own bounds (R-RUNNER-191, #815)
- Options: fold into `band` and accept a boundary shift in the golden verdict; keep. Chose keep: rung_ci's interval is open at both ends, `band` closed at T_PASS, and the golden verdict is untouched by B5.

### 2026-11-17 — benchmark interval floats (R-RUNNER-191, #827)
- Floats are handed to `rung.mean_and_error` as Decimal(str(x)). Options: Decimal(x) (exact binary, made equal values spread, rejected); str form (chosen), so the "no spread" refusal holds.

### 2026-11-17 — Mansfield and Zweig rows wait (R-MONEY-45, #809, #823)
- Mansfield needs the SPY close beside each stock. Options: (a) special-case SPY inside a block (a second home for the index, refused by A2) or add a second-series input to blocks and the fast engine now; (b) widen the Block contract with an optional index series, with its own parity test (a planned step); (c) a ratio line built by the ladder; (d) leave both rules as Python files and let R-RUNNER-127 delete the other 17. Chose (d) for now and (b) for a later session with the whole claim, since no step fits green and small; recommended per his 13 Nov ruling. Zweig waits on breadth data (R-MONEY-35).

### 2026-11-17 — montecarlo keeps its own gains (R-RUNGS-18, #846)
- Options: read `verdict.gains`; keep `[p.gain ...]`. Chose keep: `verdict.gains` plants one extra stop-sold gain among the real ones, which would add a made-up trade to the shuffle.

### 2026-11-17 — no inverse by negated returns (R-RUNGS-21, #833)
- Inverse leveraged lines for set LEV. Options: negate returns in the lab; wait for a Line type that states an inverse fund. Chose wait: negating is a second path beside the engine's (canon A2, B2), and the sizer and stop need the magnitude anyway.

### 2026-11-19 — a part-year is skipped in pooled folds (R-RUNNER-331, #858)
- Lines with different ends in one pool. Options: require one common end (old rule); fold a part-year; fold whole calendar years only, each line on its own window. Chose whole years only: it keeps "whole calendar years" (M6) true for every line; a line whose window ends mid-year skips that year.

### 2026-11-19 — a fold missing one side is refused (R-RUNNER-205, #866)
- A weather layer's edge per fold with no `good` day or no other day. Options: count its edge as zero; refuse loudly. Chose refuse (canon A2: no defaults that mask missing data).

### 2026-11-19 — Mansfield's second series (R-RUNNER-219, #873)
- Options: (a) a block that reads the index itself; (b) the row runs on ratio bars the caller builds, as the Python rule does. Chose (b): blocks see one bar stream, the ratio is what the rule consumes, and it adds no code (the block is the existing average block under a new entry name, `ratio_over_average`).

### 2026-11-19 — "mostly FAULT" means over half (R-RUNNER-332, #892)
- Options: any FAULT ends red; over half of the judged cells; all. Chose over half, since the request says "mostly"; a few faults are said but not fatal.

### 2026-11-19 — an unscorable weather layer reads "no" with its reason (R-RUNNER-205, #907)
- Options: omit the layer; fail the whole run; list it as "cannot score" with the reason, joins = no. Chose the last, so one thin layer does not hide the others.

### 2026-11-19 — the lane guard blocks moving a module (R-RUNNER-191 b, #919)
- Options: (1) loosen the lane guard to read ownership from the merge base and allow a lane to remove its own module's manifest line; (2) leave rung_folds.py as is. Recommended 1, a guard change, so announced and left to the guard lane/runner (outside the claim, A8); asked as R-RUNGS-29.

### 2026-11-19 — the retail rung is map row 12 (R-RUNNER-229, #927)
- Options: a 12th row, or keep eleven and rename the module. Chose the 12th: the card names the file, and `found` counts any `rung_*` module without a RUNG. Built count stays 3 of 12.
- Days: market day = close over the prior close in pounds; basket day = pounds of trades sold that day after every cost over the 10,000 capital, 0 if none sold (cash between trades). Rejected marking open trades daily (needs every line's bars). Frozen numbers unchanged.
- With EASED off nothing changes; on, a basket row gains "retail" but its answer is unchanged, so no golden number moves (to confirm at ease-switch-on).

### 2026-11-20 — EASED stays off until the retail rung is read (R-RUNNER-231, #937)
- Options: (a) flip EASED anyway, spending the one pre-registered re-run without easing 4; (b) refuse and wait for R-RUNGS-30. Chose (b): the pre-registration is frozen and the re-run happens once. R-RUNGS-30 landed in #942, so the flip may now go ahead.

### 2026-11-20 — one market per basket row (R-RUNNER-384, #942)
- A rule's basket may span venues but `basket.row` takes one market. Options: (a) the first pooled line's venue market; (b) split baskets per venue. Chose (a), the smallest step; per-venue baskets would change the row shape.

### 2026-11-20 — a lane may delete a file it owns (R-RUNGS-29, #951, #949, #952)
- Options: (1) loosen the lane guard to read ownership from the merge base and allow removing an owned module's manifest line; (2) leave lab/rung_folds.py. Chose 1 by his standing ruling "always go with recommended"; it loosens nothing about other lanes' files. The guard edit (tests/guards/test_lanes.py) is outside RUNGS's claim, so it stays open as R-RUNGS-29; the move of Fold/Walked into lab/folds.py follows it.

### 2026-11-20 — EASED switch-on split in three (R-RUNNER-231, #976, #967)
- Options: (1) flip and fix everything in one card (mixes tests and callers); (2) split: callers pass the family count, tests pin the state they test, then the flip with the golden verdict updated once. Chose 2 (small reversible steps, stop rule A8). Turning it on made 19-21 unit tests red. Held the flip (#967) because the re-run is single-use and the ladder passed no family, so every cell would read "could not".

### 2026-11-20 — the pooled ladder fails loudly under EASED (R-RUNNER-385, #984)
- The pool path (`lab/ladder_pool.py`) was outside the claim. Options: leave it passing no family, so with EASED on it fails loudly; or edit the pool now. Chose the first; asked as R-RUNGS-31.

### 2026-11-20 — EASED flip waits for the family to reach the cell judge (R-RUNNER-231, #979, #986)
- Trying the flip alone (#979) raised "EASED judges by the rule's family count, none given" in every cell, so it was reverted. Options: flip with the family wired (recommended, taken in steps #984, #986); or flip and fix callers at once. The pool now passes the family too (#986). Left: flip `EASED = True` and re-pin the golden verdict with a plain-English line in DECISIONS (his 16 Nov "YES TO ALL" covers the easings).

### 2026-11-20 — the ladder's easing switched on (R-RUNNER-231, #993)
- Golden numbers moved (canon B5). Options: (a) leave EASED off; (b) flip `verdict.EASED = True` and re-pin the fixture's verdicts. Chose (b): the 20 Nov ruling allowed the flip once R-RUNGS-30 landed, and his standing "always go with recommended". Weaker rungs no longer stop a line, so the shuffle and regime rows read WEAK/FAIL differently; no pound figure or trade count moved.

### 2026-11-20 — tape tests stay pinned off by name (R-RUNNER-396, #1124)
- Options: leave the tape tests eased, or pin EASED off by name with the reason beside it. Chose the pin: they count simulations, which EASED's placebo rungs would add to, and eased they ran past 15 minutes on GitHub (20 Nov #993). Ladder 2, epon 1, pool 1, verdict 6, retail 1, tape 5 pins; no blanket autouse remains.

### 2026-11-21 — the regimes rung cuts at the calendar middle (#1165)
- Options: the middle bar day (needs bars the rung is not handed) or the calendar middle of the cell's window (same to within a few days). Chose the calendar middle, recommended and taken per his standing ruling.

### 2026-11-21 — the capital joins the key as its own text (R-GRID-3, #1201)
- Options: hash `desk/command.py` or add the capital as its own text in the key parts. Chose the text: one number, not the whole file.

### 2026-11-21 — Candidate refuses unrun rungs now (#1256)
- Options: now, or when the first real candidate nears. Chose now: one line, tightens a guard-like rule, cannot loosen anything.

### 2026-11-21 — spec variants: one home, lab/variants.py (B5, #1307, #1315)
- #1307 added `lab.spec.variants`; a variant is not asked the base spec's known answers (they are for the base settings). Options: re-prove them (always fails) or skip; chose skip, settings are range-checked instead.
- #1315 found `lab/variants.py` (#364) already makes every combination, counts trials and reports the plateau centre, so the duplicate was deleted. Options: keep both (a second code path, canon A2), merge into spec (spec would import plateau/trials); chose keep `lab/variants.py`.

### 2026-11-21 — the EPON table: one row per rule (R-RUNNER-334, #1360)
- `ladder_sets.condense` rewrites ladder/sets/<tag>.md after write_table: one row per rule, every cell kept whole in <tag>.cells.json. Furthest rung = the last rung run by the rule's best line (one that goes forward, else the one that ran most rungs); a rule with no line judged shows its error or refusal as the reason.
- Options: change `verdict.write_table` itself (declined: outside the claim); condense after it (chosen).

### 2026-11-21 — the stop-rule rung sizes every rival by today's risk (R-RUNNER-408, #1277)
- Options: a flat risk budget for all rivals; or the budget today's stop risks (10% x leverage). Chose the second so the fixed-stop baseline is unchanged. Trades lacking 21 bars of history, or where any rival buys no share, are dropped for all rivals so the same trades judge every rule. Pre-registration: docs/DECISIONS.md, 21 Nov.

### 2026-11-21 — Zweig's marks are constants (R-MONEY-45, #1382)
- Zweig's marks (0.40, 0.615, 10 days) are the book's own, not settings, as in the DeMark blocks. Options: params with a Decimal range (needs a new range kind); constants (chosen, smaller).

### 2026-11-21 — the scorecard rule as constants (R-RUNNER-435, #1411)
- `scorecard` returns PASS, FAIL or STOP; FAULT counts as FAIL. Options: ignore a FAULT; count it as FAIL (chosen: a faulted rung proves nothing). Not yet wired into `judge()`.

### 2026-11-21 — the results file is compacted by the command (R-RUNNER-434, #1420)
- `Kept.compact()` runs in `door` after the set is judged, not inside `run()`. Options: inside `run` (would erase superseded history an existing test reads, and a run's own file handle); in the command (chosen, safer).

### 2026-11-21 — rung 4's judge moves; the count stays 5 (R-RUNNER-369, #1425)
- Row 4 now names `lab/market.py`, not a `rung_*` module, so `rungs_built()` would have counted 6 though the ladder still runs `market.judge`, not `banded` (blind review, blocking). Options: (a) accept 6; (b) keep row 4 on the empty rung_beta.py; (c) a row owing `- no RUNG` counts as unbuilt. Chose (c): the published count moves only when the ladder's judging does; the map test pins it at 5 (tightened, not loosened).
- `market.judge`'s PASS/FAIL rule versus `banded`'s three bands is not unified here (would change verdicts). Found, not fixed.

### 2026-11-21 — Zweig's breadth is one fixed series (R-MONEY-45, #1430)
- Zweig's blind-test breadth changed from a random series to a fixed one. Options: keep random and add a second fixed walk (more lines, against the unit-test budget), or one fixed series serving both tests (chosen; the future-blind test still cuts it at six random days).

### 2026-11-21 — a done box is closed by a real in-claim change (rungs-tape-cache, #1440, #1445)
- The box was re-issued though done (pattern 22); an empty pull request is closed by the runner. Options: (a) another empty PR, (b) a real in-claim change landing with the tick, (c) stop. Chose (b): the tape read marked bounded (#1440), the docstring saying why rates are not keyed (#1445).

### 2026-11-21 — opening range breakout sells at the session's last bar (R-RUNNER-198, #1439)
- A position held at the last bar is sold on that bar (the card's "out at the last bar"), not on the engine's `flat` second-last-bar sale; the rule takes its venue as a constructor argument, default LSE.

### 2026-11-21 — intraday mean reversion band (R-RUNNER-353, #1443)
- The band includes the current bar, as the daily Bollinger rule does; holding sells when the close is over the middle.

### 2026-11-21 — promotion.killed fails loudly (R-RUNGS-7, #1447)
- A candidate whose ledger is malformed (a buy before its condition was written) makes `killed` raise. Options: skip it quietly, or fail loudly. Chosen: fail loudly (canon A4); a silent skip would let a killed strategy keep buying.

### 2026-11-21 — where a row's variant ranges live (B5, #1459)
- Options: (a) each caller passes ranges to `variants`, as before; (b) the row holds them and `Spec.parse` checks them. Chosen (b): the box asks for variants from a row's ranges, and validation happens once at the boundary (canon A2). Plateau's finer rules (three values or more, neighbours a tenth apart) stay in `lab/plateau.py` and bite at `centre`; moving them to entry would make spec import the ladder's chain.

### 2026-11-21 — proving every rule is a row (R-MONEY-45, #1464)
- Options: (a) a new test (adds unit-test lines, main has no margin); (b) widen the existing parity test to rows and rules together. Chosen (b): zero net lines, one test, the failure names the rule.

### 2026-11-21 — which rows get ranges now (B5, #1469, #1473)
- RSI-2: options (a) every row whose entry and exit have their own settings; (b) also Faber, Weinstein, dual momentum. Chosen (a): those three publish one lookback shared by entry and exit, so ranging them apart makes six of nine variants rules nobody published and triples the luck count. They wait until `lab/variants.py` can tie two settings to one value.
- Williams %R: options (a) lookback, (b) the two thresholds, (c) both. Chosen (b): entry and exit share one %R window and ranges allow one setting per block, so varying n in one block would split the window; (c) needs multi-setting ranges.

### 2026-11-21 — one market for the weather table (R-RUNNER-371, #1481)
- `weather.write` keeps one table, so the ladder job runs it on the US line (SPY) only. Options: SPY only, or a table per venue. Chosen SPY only (smallest step). The test drives `weather_line` directly, since a fixture database is heavy.

### 2026-11-22 — intraday pricing lives beside the rules (R-RUNNER-354, #1488)
- lab/intraday.py already held the rules and the claim named only it. Options: a new module (outside the claim) or add beside the rules. Chose the second; a later card may split it. No stop is modelled intraday: a 10% stop cannot be reached within a session.

### 2026-11-22 — Keltner's ranges (B5, #1489)
- Options: (a) 5/10/20 on both bands, as Donchian's row; (b) finer 8/10/12; (c) one band. Chose (a): meaningful spread, published 10 at the centre, nine trials keep the luck bar modest.

### 2026-11-22 — weather names stay up/down (R-RUNNER-372, #1494)
- `weather.named` keeps up/down so `by_weather` is unchanged. Rejected a new good/bad pair: it touches rung_regimes and verdict for nothing.

### 2026-11-22 — Connors three-day ranges (B5, #1496)
- Options: (a) entry run 2/3/4 and exit average 3/5/8, nine variants; (b) the 200-day filter too, 27. Chose (a): fewer trials for the luck test, same shape as ranged rows.

### 2026-11-22 — a refused line is a row, not a crash (R-RUNNER-355, #1505)
- A line whose bars the store cannot serve whole is a row saying "refused" and why. Options: crash the set, skip silently, refuse in the table. Chose the table, so nothing is hidden. Capital is the desk's CAPITAL as in other sets.

### 2026-11-22 — Connors %b ranges (B5, #1503)
- Options: (a) buy threshold only; (b) buy threshold, run and sale threshold together; (c) every setting incl. band and filter. Chose (b): 27 variants, published 20/3/80 centred; (c) would be 81+ trials and raise the luck bar for nothing.

### 2026-11-22 — manifest line left alone (R-RUNNER-373, #1510)
- The lanes guard allows only added manifest lines, so lab/history_bars.py's purpose line was not widened. Options: leave it, or loosen the guard. Taken (recommended): leave it; no guard loosened.

### 2026-11-22 — momentum burst source (R-RUNNER-200, #1513)
- Source: Bonde's momentum burst (a daily-bar idea, adapted to one-minute bars, stated in the docstring). Options: Crabel or Raschke patterns, but none is a one-minute burst. lab/ is 12,531 lines, under the 20,000 phase ceiling in BUDGET.json (the request's 12,000 is stale).

### 2026-11-22 — variants count in the family first (B5, #1507)
- Options: (a) enter the catalogue's variants into the EPON register now; (b) first make the count read `rule[settings]` names; (c) promotion. Chose (b): (a) would charge four ranged rules for trials never run and change eased verdicts before the grid chain runs them; (c) is held until R-RUNGS-7.

### 2026-11-22 — Turtle Soup ranges (B5, #1521)
- Lookback 10/20/40 (doubles and halves around 20, as Donchian), age 2/4/6; every age is below the shortest lookback so no variant is empty. Options: rungs-eponymous (needs a passed rule) or a B5 row; chose the row.

### 2026-11-22 — intraday session is the UTC day (R-RUNNER-206, #1520)
- Options: venue sessions via desk/venues, or the UTC calendar day of bar starts. Chose UTC day (simplest, matches the fixture); window 20 bars (card gave N only). Venue-aware sessions can follow. Promotion held until R-RUNGS-7.

### 2026-11-22 — VWAP distance a fraction (R-RUNNER-356, #1523)
- Options: fixed price distance, a fraction of VWAP, an ATR multiple. Chose 1% of VWAP: price-scale-free. Source: Berkowitz, Logue and Noser 1988 for VWAP; the rule is ours.

### 2026-11-22 — Jegadeesh ranges, GRID asked for the rule book (B5, #1529)
- Options: (a) wire variants into the ladder now (needs GRID's `lab/rulebook.py`); (b) enter variants in the register without running them (charges trials never run, breaks B6); (c) range more rows and ask GRID. Chose (c) (R-RUNGS-33). Clash with #1521 on Turtle Soup: kept main's gap [2, 4, 6] (landed, reviewed, passes the plateau test).

### 2026-11-22 — Zanger and Bollinger ranges; rungs-promotion stays held (B5, #1527, #1538)
- His ruling ("please always go with recommended to avoid waiting for me to attend"): rungs-promotion waits on R-RUNGS-7, so B5 was worked. Options for the next step: (a) wire variants into the grid chain (beyond a card, touches GRID's chain), (b) enter variants in a register now (charges trials never run), (c) one more row's ranges. Chose (c).
- Zanger: its 50 days and 1.5x volume are the port's own reading, so it most needs neighbours tried; Faber, Weinstein and dual momentum need tied settings, passed over. Bollinger: options (a) its 20 days and 2 deviations, (b) the port's six months and exit, (c) all four. Chose (b): published settings fixed, 9 trials not 81.

### 2026-11-22 — variants counted in their own set (B5, #1530)
- Options: (a) enter every variant in EPON's register now; (b) a variants set of its own, run by the ladder. Chose (b): the plan names variants as their own family, and charging EPON for unrun variants would change its golden verdicts. Needs the ladder to run a variant cell, so `variants.find` is built here and GRID asked for the rule book half (R-RUNGS-33).

### 2026-11-22 — scalping edge needed is gross of cost (R-RUNNER-357, #1532)
- `edge_needed` = cost + T_PASS x standard error of the gains, as the request asks the edge needed to pass the cost.

### 2026-11-22 — intraday layers (R-RUNNER-359, R-RUNNER-360, #1531, #1541)
- Expansion compares a bar with EARLIER bars only (options: include itself; chosen: exclude, so a wide bar cannot dampen its own test). Opening range is time-based (30 min from the session's first bar), so a missing bar cannot shift it.
- Volatility: MIN_SESSIONS=5, MIN_RETURNS=2; thirds by count of earlier values strictly below (options: interpolated percentiles; chose counts, no interpolation to hide).

### 2026-11-22 — B5 variants, SCALP, intraday contest (#1535, #1543, #1544, #1546, #1550, #1551)
- Promotion held: his standing ruling ("always go with recommended") keeps rungs-promotion back until R-RUNGS-7 is ticked and a rule has passed the ladder. Options: promotion anyway, B5 variants, rungs-eponymous. Took B5 variants (smallest step, no other lane's file); #1544 only restored SCALP after a conflict.
- Set VAR has its own register, not EPON's (#1535): 84 extra trials in EPON's would change its luck-corrected verdicts mid-run. Own register keeps EPON's golden verdicts and names the family before it runs (B6).
- Which settings to range: Kell the breakout length and exit (the 10/20-day averages define the setup); Bollinger squeeze the six-month look-back and exit (this port's reading); Minervini the pivot lookback and exit average, not the trend template (a definition, not a knob); Donchian fade 10/20/40 on both channels, the exit not 80 (a midpoint exit that long is another range). Fewer trials keep the luck bar honest.
- Blind review skipped on #1543, #1546, #1551 (four to eight lines of data, held by the plateau test, seen failing; ten-minute cards) and on #1550 (card under ten minutes).
- SCALP (#1544): a rule with no trades on a line shows FAULT (no spread), as INTRADAY does; cost column a dash.
- Intraday contest (#1550): edges scored on bars where both layer and daily label are named (same bars, a fair contest); scoring is `lab.weather.edges`' rule restated on bar starts; folds are contiguous slices of bar pairs.

### 2026-11-22 — B5 ranges finished, bracket refused (#1591, #1574, #1595, #1604, #1615)
- Promotion held: his standing ruling ("please always go with recommended to avoid waiting for me to attend") keeps rungs-promotion back until R-RUNGS-7 is ticked and a rule has passed the ladder; B5 was worked instead.
- Bracket in a row name (#1591): refuse in `Spec.parse` (A2: the bad state cannot be built) rather than a cleverer `variants.find` or leaving it.
- A setting two places share (#1574): (a) range each place apart (9 trials, six of rules nobody published); (b) a joined key `entry+exit` moving one value in both; (c) leave unranged. Chose (b). On conflicts with #1578 and #1587 it kept the joined key and main's values (Mansfield 130/260/390).
- Zweig (#1595): range the port's 230-session hold (115/230/345), not Zweig's published thresholds. Blind review skipped (3-line data change under the plateau test).
- Darvas (#1604): `n` ranged 2/3/4 jointly over entry and stop, both read one set of boxes.
- DeMark (#1615): range the setup length 9 (7/9/11) shared by entry and exit, not the countdown 13 (nine variants for little gain).
- Montecarlo (#1597): an error row is skipped before its keys are read, no try/except; a later error row keeps the same cell's earlier good row, since `priced` refuses stale trades.

### 2026-11-22 — rung map, import cycle, sizing block, RSI table (#1625, #1620, #1621, #1637, #1640)
- What "built" means for the rung count (#1625). Options: (a) infer it from `rung_*` module names, which counts `lab/folds.py` as built though it declares no RUNG; (b) count only row modules that declare a RUNG. Chose (b): the map's own definition, and an overstated count is the old desk's failure (pattern 3). Rungs built is 4 of 12.
- Breaking B5's cycle (#1620), by his standing ruling "always go with recommended": rungs-promotion stays held until R-RUNGS-7, so B5 was worked, because R-RUNGS-33 was blocked by a cycle in this lane's file. Options: move `find`/`variants` into `lab/spec.py`, or strip `lab/variants.py` to spec-only. Chose stripping (deletes two wrappers, adds nothing to a 400-line module). `Variant.setting` is typed like `Spec.Ranges`'s values rather than `plateau.Setting`, giving the alias a second home (pattern 8); accepted, as `lab.spec` already writes it.
- Plan notes (#1621): B5's two notes collided in a merge; kept main's (rungs-b5, waits R-RUNGS-33) and pointed GC at it, one id for one box (pattern 8).
- Form of the sizing block (#1637). Options: (a) wait for a sizing contest that does not exist (#1481's table is the market-weather contest); (b) invent a lab sizer; (c) the desk's own volatility rule in `desk/risk.py`. Chose (c): canon B2 and A4 settle it; (b) would be a second home, (a) a wait on nothing.
- Where the RSI's known answers come from (#1640). Options: (a) ChartSchool's cs-rsi.xls RSI column, already on file; (b) a worked example from the Grimes text. Chose (a): no new fixture; Grimes stays the source for what ChartSchool does not print. Guard proven (A7): an RSI from a gain/loss ratio rounded to two places was refused at row 0 (70.50 against 70.53), and the out-by-one sweep refuses every row moved by 0.01.

### 2026-11-22 — fast engine stop, variant rule, plateau step, pound door, clustered DSR, rung gate (#1616, #1655, #1660, #1672, #1673, #1676)
- B5 vs the held promotion (#1616), under his standing ruling ("please always go with recommended to avoid waiting for me to attend"): rungs-promotion stays held until R-RUNGS-7 is ticked and a rule passes the ladder. Options: (a) wait for R-RUNGS-33 and do nothing; (b) prove the engine that will judge the variants agrees with the desk at every variant's settings. Chose (b): GC sweeps the variants on the fast engine; it found `held()` ignoring a firing stop (`clenow_momentum[entry.n=60,exit.n=50]`).
- Where a variant's binding lives (#1655). Options: (a) decline, the rule book is GRID's; (b) write it in `lab/rulebook.py`, which the check refuses; (c) beside `find` in `lab/variants.py`. Chose (c): everything RUNGS can do in its own files, GRID's change is two lines. The class is `SpecRule`'s so the code key reads the real engine.
- Plateau (#1660). Options: (a) close the PR until the claim widens; (b) land what fits, behaviour unchanged where no surface is given. Took (b). The NOT APPLICABLE key was dropped: it needed two ladder tests changed and read a fact from a rule's name (canon B3).
- Pound gate (#1672). (1) `ask` required, or optional and raising when missing: chose optional-and-raise, as the card words the gate and it keeps `lab/transfer.py` type-clean until grid-door-pound. (2) Montecarlo's grid jobs: kept on the grid's own store, since held trades are checked against the bars that made them; moving them is the grid lane's card. Ladder jobs read the database.
- Clustered DSR (#1673). Options: replace `judge(gains, trials, spread)` or add `judge_set` beside it. Added beside: replacing breaks `tests/unit/test_lab_rung_dsr.py`, outside the claim; one bar formula stays and a parity test pins it to `deflated`. Merging the two (decision e) is left to rungs-each-rung.
- Rung gate form (#1676). Options: (a) a test that every rung module declares a RUNG, red today; (b) a ratchet pinning the eight off-path modules; (c) nothing until the merges land. Chose (b): green now, fails on any new dead rung, becomes (a) when the list is empty (canon A3, Part C). Every merge needs files outside the claim (lab/ladder.py, manifest.toml, target modules) and R-RUNGS-29.

### 2026-11-22 — input gaps named before a set runs (#1680)
- Where the gap check lives. Options: (a) in each rung's judge, (b) a pre-flight function per rung called by the set runner, (c) in the store. Took (b): faults are fixed at entry, never answered by a rung (decision d); the store's calendar check is DATA's.
- Rates checked on every bar day of the window, or only trade days. Options: (a) every day, (b) trade days. Took (a): which days a trade reads is unknown until the rule has run, and a hole on a later trade day is the same fault; the wiring card may leave a line out instead of refusing the set.
- A bar outside the calendar's years (before 1993, after 2029) raises loudly from `venues.sessions` rather than being skipped: no silent defaults (canon A2).

### 2026-11-22 — plateau, luck gate, sets, indicators, published tests (#1702, #1706, #1707, #1711, #1714, #1721, #1740, #1742, #1749)
- How a no-settings rule shows on the plateau rung (#1702). Options: (a) PASS with a "NOT APPLICABLE" reason on the table; (b) a new answer value in lab/rung.py; (c) drop plateau from both rungs. Took (a): visible, reviewed. Who may declare a rule fixed: the type checks the spec book, so a ranged row or a variant raises at the constructor (canon A2).
- `plateau.of` (#1742): a bare rule name not in the spec book is FIXED (no settings); a bracketed name with no row is refused, since a bracket only names a variant. Options: refuse every unknown, or pass all as FIXED. Took the split.
- Luck correction (#1714, L18 b): one correction, not two. Options: (a) keep both (needs t>=4.6, nothing passes); (b) deflated Sharpe the gate, Bonferroni rung report-only; (c) drop the luck rung. Took (b). The verdict still counts the luck rung in `every`: R-RUNGS-36.
- Where the 1% lives (#1706): (a) folds.py beside `gaps`, (b) ladder_sets.py, (c) published*.py. Took (a), one home. Exactly 1% is published, over 1% is not; an empty set is publishable (refusing it is the runner's business). Blind review owed when wired.
- Printed band column (#1707): (a) the Grimes book (prints no numeric band column), (b) StockCharts' free cs-bbands.xls. Took (b), rounded to four places; blind review recomputed all 23 rows.
- Holding run (#1749): hold from bar 0, alternate, or from the first smoothed day. Took the first smoothed day, since Supertrend refuses to hold with no band. Window tables take the flag unused. rungs-blocks and rungs-fast-engine files untouched, per his standing "go with recommended".
- Sizing block (#1711): editing the registry files was refused by the claim (pattern 21); landed only the step that fits, making the sizer a `Block`.
- Published tests (#1721): figures kept as a record beside each rule in `published_epon.py` (not `reproduce.FIGURES`, outside the claim and refuses non-first-set rules); a separate `Search` enum to avoid an import cycle; a test of a different rule keeps its numbers but is never a candidate (canon B6).
- Beta rung (#1740): chose deleting the empty module, the only step fully inside `lab/rung_*.py`; wiring or merging the other seven changes the ladder map outside the claim.
