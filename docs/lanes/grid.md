# The grid lane

The grid lane's own decisions, each a dated `###` entry saying what was decided, the
options, why, and the evidence; newest last. Only this lane's scribe writes here, so no
other lane's pull request touches these lines. Held to a size a session reads whole
(`BUDGET.json`, `max_lines_per_lane_doc`): when it is full, the scribe folds the oldest
settled entries into one short summary entry; git keeps every word.

## Decisions

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
