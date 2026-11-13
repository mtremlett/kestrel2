# Scoreboard

One line per session. Converging means scenes going up, lines staying flat or falling,
and the share of fix commits going down.

| date | scenes | desk lines | lab lines | test lines | guards | check | what moved |
|---|---|---|---|---|---|---|---|
| 2026-11-13 | 0 of 7 | 10 | 9 | 268 | 12 of 12 proven | green | Repository created; main protected and proven to refuse a direct push; the one check running on GitHub; twelve guards driven against deliberate violations, one real defect found and fixed; documents written. |
| 2026-11-13 | 0 of 7 | 294 | 9 | 502 | 12 of 12 proven | green | Scenes approved by the operator; written as seven tests, each stopping at a named unbuilt part; the scenes step made a ratchet and driven against six violations; a blind review's findings fixed or recorded; a size rule that blocked tests-first changed by his ruling to count unit tests only, driven red. |
| 2026-11-13 | 1 of 7 | 546 | 9 | 731 | 12 of 12 proven | green | The operator's rulings recorded: sessions merge on a green check, and GitHub now refuses a red merge (driven red on #5); A-GATE written as AG-01 to AG-06 with the thirty-day terms fixed in advance. Scene 1 passes: one price store with one writer, cleaned on entry, and the London and US calendars; a blind review's six blocking findings fixed, twenty-five deliberate breaks each caught. |
| 2026-11-13 | 1 of 7 | 546 | 9 | 847 | 12 of 12 proven | green | Each merge to main now sends the operator one Telegram line: title, scenes count, next objective. A missing secret turns it red, driven on main before the secrets existed; eleven deliberate breaks each caught; blind review, nothing blocking. The first line, for #7, reached his phone. |
| 2026-11-13 | 1 of 7 | 680 | 9 | 1061 | 12 of 12 proven | green | The twenty lines chosen by the operator (two typos confirmed, seven proposed and chosen) and in the master; one client for the free archive; all twenty fetched since 2010: sixteen clean, four parked with named reasons. By his rulings, a London auction price up to 3% outside the day's range stretches it and only the last sixty sessions can park a line; a blind review's blocking finding fixed, and the first fix's own flaw caught on real data. |
| 2026-11-13 | 2 of 7 | 890 | 9 | 1289 | 12 of 12 proven | green | The operator chose the five strategies: five textbook rules at their published settings, long only. One template shows each rule one bar at a time, so none can see a later bar; scene 2 passes. A second implementation written apart agreed on every trade day over sixty walks; a blind review's test gaps fixed, 44 of 45 deliberate breaks caught (the 45th cannot change a decision). He ruled the rehearsal data be lengthened, as none of the five trades in six weeks. |
| 2026-11-13 | 3 of 7 | 968 | 9 | 1388 | 12 of 12 proven | green | The operator chose how big a trade is: at most five holdings, each a fifth of the capital, a leveraged line counted at what it controls, and a stop where its market has fallen 10%. Scene 3 passes: whole shares priced in pounds under the broker's published fees, the sizer and the gate reading one number, leverage a fact on every line. Thirty deliberate breaks each caught; a blind review's blocking finding fixed, the other (five holdings need the book) recorded. |
| 2026-11-13 | 3 of 7 | 968 | 9 | 1451 | 12 of 12 proven | green | The operator asked for a much shorter Telegram line. It now reads "kestrel2 · Phase 2 · step 3 of 6 done · scenes 4/7 (#16)", or "housekeeping" for a change that ticks no step, worked out by comparing the plan's checklists before and after the merge. Eleven deliberate breaks each caught; a blind review's one finding (a test tied to phase 0) fixed. The "🔔 ACTION:" in front is added on his side, not by the desk. |
| 2026-11-13 | 3 of 7 | 968 | 9 | 1481 | 12 of 12 proven | green | By his choice, each Telegram line now carries the week's usage of his plan, read from a line "Weekly usage: 21%" that lane runs write in their pull requests: "kestrel2 · Phase 2 · step 3 of 6 done · scenes 4/7 · usage 21% (#16)". A hand-made pull request shows "usage n/a", never a guess and never a red job. Fourteen deliberate breaks each caught; two lines in one description give n/a, not the first; the first short line, for #17, was delivered. |
| 2026-11-13 | 3 of 7 | 968 | 9 | 1404 | 12 of 12 proven | green | Three lanes set up to run side by side, day and night, by the operator's rulings: MONEY, DATA and LADDER, each with its own objective, book of work, files and sections of the shared documents; the rehearsal data moved to its own file so the money and data lanes never share one. GitHub now merges a branch only when it holds all of main, driven red on #16. CLAUDE.md: unattended lanes decide intended behaviour themselves and record it. The runner lives outside the repository. |
| 2026-11-13 | 4 of 7 | 1096 | 166 | 1941 | 14 of 14 proven | green | Mechanical guards before the lanes run unattended, by the operator's rulings: a lane's branch may change only its own files and no change adds over 300 product lines (two new guards, seventeen cases driven, one defect found in the guard and fixed); outside the repository, the runner now stops at 80% of the plan's week, halts a lane that lands three changes without progress or fixes one file twice, runs a read-only audit at 05:30 (it caught all three planted faults) and sends a line at 07:00. |

## The lanes

From 13 November 2026 three lanes run side by side (`docs/PLAN.md`). Each session appends
its one line to its own lane's table, never to another's, so parallel pull requests do not
touch the same lines. A session the operator starts himself appends to the table above.

### MONEY

| date | scenes | desk lines | lab lines | test lines | guards | check | what moved |
|---|---|---|---|---|---|---|---|
| 2026-11-13 | 3 of 7 | 1057 | 9 | 1585 | 12 of 12 proven | green | The pretend broker is built: a buy fills at the next open under the broker's own id and leaves a stop resting at the broker, tested on the day of the buy too; a rejection, a partial fill, a dropped connection and a crash each give a stated reason; the desk can ask what the broker did with an order, so it never sends twice. Its contract test was seen failing first; thirty deliberate breaks each caught; a blind review's one fix taken (a fault used up on no market). Next: the send path, for scene 4. |
| 2026-11-13 | 4 of 7 | 1096 | 166 | 1809 | 12 of 12 proven | green | Scene 4 passes: the desk asks the broker before it sends, so a restart never buys twice; only an order the broker never had passes the gate and is sent; each fill written once under the broker's id; a rejection, a partial fill and a dropped connection each give a stated reason. Contract test seen failing first; eleven deliberate breaks each caught; a blind review, nothing blocking, its test gap fixed. Next: the book built from the broker. |

### DATA

| date | scenes | desk lines | lab lines | test lines | guards | check | what moved |
|---|---|---|---|---|---|---|---|
| 2026-11-13 | 3 of 7 | 968 | 9 | 1524 | 12 of 12 proven | green | The rehearsal data is now fourteen months on each venue's own calendar, and each of the five rules buys and sells on every clean line in it; holidays laid on the wrong calendar were each refused by the store. The scenes still see its last six weeks until the money lane's scene 2 counts two calendars; then the move is one line. |
| 2026-11-13 | 4 of 7 | 1126 | 166 | 1972 | 12 of 12 proven | green | One line the archive refuses is now parked alone, with its reason, and the other lines carry on; the store keeps no bars for it, so none from an earlier day can be read as today's. Tests seen failing first; six deliberate breaks each caught; a blind review's blocking finding (a half-delivered answer stopped everything) fixed. |

### LADDER

| date | scenes | desk lines | lab lines | test lines | guards | check | what moved |
|---|---|---|---|---|---|---|---|
| 2026-11-13 | 3 of 7 | 968 | 166 | 1640 | 12 of 12 proven | green | The ladder's unit of work: one strategy on one line over one window, its trades the desk's own decisions over the line's whole history, days only until costs come, keyed by a fingerprint of the code it reached and every bar it read. Nine contract tests seen failing first; nineteen deliberate breaks driven, two showing blind tests (fixed) and two showing unneeded code (deleted); a blind review, nothing blocking, its test gaps fixed. |
| 2026-11-13 | 4 of 7 | 1096 | 266 | 2042 | 12 of 12 proven | green | The ladder's batch service: many cells run in turn, each result written to disk as it finishes; a bad cell recorded and the rest carried on, a failed cell tried again next time, and a stopped batch taking up where it stopped. Four contract tests seen failing first; sixteen deliberate breaks driven, fifteen caught (the one left, forcing each line to disk, no test can see); a blind review, nothing blocking, its two findings fixed. |
