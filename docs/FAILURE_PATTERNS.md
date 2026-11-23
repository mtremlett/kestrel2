# Failure patterns

Each is a way this desk went wrong and the check that catches it (none: an open debt, said).
Each "guard" is a `tests/guards/` test driven against a planted violation (`docs/DECISIONS.md`).

**1. The guard that excuses a whole file.** A check searches a file for an escape word
and, finding it anywhere, passes the file entirely. The live-money guard did this on day
one and was switched off by a docstring.
→ *Caught by:* guards judge one line at a time, and the words they search for are
assembled from pieces so a guard never flags its own source. A7 in the canon.

**2. The clean core with an outside.** A small walled package is built and trusted, then
the code that runs it each day is placed outside the wall, where no limit applies. The
predecessor's 2,000-line core stayed inside its cap while its runner grew to reach
352,000 lines.
→ *Caught by:* the whole repository is under one ceiling, and the manifest wall test.

**3. Progress counted in activity.** Cards landed, commits made, tests added — all rising
while the thing that matters does not move. The predecessor landed about 1,100 work cards
in six weeks and proved 10 of 64 requirements.
→ *Caught by:* the only progress number is scenes passing out of seven, and the plan
requires a batch adding net lines to name the scene it advances.

**4. The set-aside test.** A test fails, is added to a known-failures list "for now", and
is never fixed. The predecessor carried 2,221.
→ *Caught by:* a guard forbids skip and expected-failure markers. There is no list.

**5. The test that reads the live desk.** A test passes honestly on the operator's
machine because it reads his real data or his broker, and proves nothing about the code.
→ *Caught by:* a guard forbids machine-specific paths, and GitHub runs the whole check on
a machine with no access to any of it.

**6. The second version of a file.** `_v2`, `_new`, `_fixed`, or a file named after the
session that wrote it. The predecessor had 1,218 session-named test files.
→ *Caught by:* a guard on file names. Git is the archive.

**7. Repairing forward on a broken tree.** A change breaks something; the next change
tries to fix the symptom; the fix needs its own fix.
→ *Caught by:* the stop rules. A passing scene that fails stops all other work, and if one
attempt does not restore it the commit is reverted, never patched over.

**8. Two homes for one fact.** The same number, list or rule written down in two places,
which then disagree. The predecessor had three stop levels per position and two different
figures for the pot.
→ *Caught by:* the manifest names one owner per concept; duplicates are merged on sight.
→ *Debt:* no automatic check finds two homes. Human discipline, for now.

**9. Documents breeding.** Summaries, notes, handovers and reports accumulate until no
one knows which is true. The predecessor had 728.
→ *Caught by:* a guard allows exactly ten documents and no others.

**10. The silent failure.** An error caught and ignored, a default that hides missing
data, a check that prints nothing either way.
→ *Caught by:* lint rules forbidding blind exception handlers and silent passes, plus the
canon's "fail loudly".
→ *Debt:* a check that cannot fail is still possible to write. Only A7 — driving each
guard against a violation — catches that, and it is a practice, not a mechanism.

**11. The long job fixed one defect at a time.** A process proven only by running for days
(the grid's seven-day week, `lab/sweep.py`) meets each defect in its real run, one at a
time: built in #111, its proof found 14 minutes short of seven days in #118, a hung pass
able to stop the week for good in #125. Three changes in a row to one file.
→ *Caught by:* `lab/sweep.py`'s tests run a compressed week (minutes for days) through the
same code, a hung pass among them, so a defect shows there before the real run; and the
runner halts a lane whose second `fix` touches a file another `fix` touched within ten
landed changes.
→ *Debt:* that halt reads the change's title, and #125 was titled `feat`; the daily audit
caught it instead.

**12. The blocked box handed out again.** A box that cannot be finished inside its lane
(seven days of time, a book not yet bought, another lane's change) is handed to session
after session, which do busy work that ticks nothing until the lane halts. On 14 November
three lanes (DATA, GRID, RUNGS) halted this way overnight.
→ *Caught by:* a box's note may say `waits: <request | date | operator>`
(`tests/guards/test_lanes.py` refuses any other value); the runner never hands out a box
whose wait is unmet, holds back a box its session says `Waits:` for or the doctor finds
blocked, and offers it again when the request is done or the date comes. The no-progress
halt stays as the backstop.
Its twin, seen 15 November: a card re-issued with a claim its fix cannot fit (spec-epon six
times, cell-line-only four). The runner's READY gate (xiv) refuses to re-issue a card whose
last run asked another lane for something, or named a file outside its claim, until the
claim changes or that request is done; it was driven against planted runs.

**13. Tuning the cleaner on live lines.** Each parked line's next odd bar drives another
rule or exception into `desk/store.py`, and exact real prices get written into
`desk/lines.py`, so the store is fitted to the data one line at a time instead of designed
once. On 14 November: three rule changes in twenty minutes on the same six London lines.
→ *Caught by:* the runner halts a lane whose second `fix` touches a file another `fix`
touched within ten landed changes; and `tests/unit/test_store_rules.py` (#225) pins every
rule in `desk/store.py` to a row of one synthetic fixture table, so a rule added without a
row fails. That guard was driven red with an unpinned rule (`docs/DECISIONS.md`,
R-RUNNER-43, #225 and #227).

**14. The judge fixed from the outside in.** `lab/ladder.py` took four fixes in ten changes
(#402 and #419, two blind reviews; #405, a missing market day; #410, a failed cell judged
again; #427, the "rungs built" count read from a docstring). Each review found a new edge
in the one 400-line module that judges, counts, keeps tapes and writes the table, and each
fix was true; no rung had a golden verdict pinned, so nothing showed a judgement drift
until a reviewer read the code.
→ *Caught by:* the rung registry (a `lab/rung_*.py` module declares its rung, so a new rung
never edits the judge), the split of the module (`lab/ladder_parts.py`), and the churn
guard. → *Debt:* a golden verdict per rung on the fixture, before and after every change,
lands with the easing cards of 16 November (B5).

**15. The broker the pretend never met.** `desk/conformance.py` is the only code that
cancels, re-sends and trades beside the desk's book at the real broker, so each live run
found a broker behaviour the pretend broker lacked (a second run's orders refused as
duplicates, #435's minute; a run line naming the account when it meant the last step,
#444; a stop "triggered" by cancelling it and selling at the market, compared with a
pretend fill at the stop level, 16 November).
→ *Caught by:* every run keeps its tape (real beside pretend, with the broker's own words),
and a step whose two sides name different actions is a finding, not a pass (#557). The
module was split (`desk/conformance_parts.py`).

**16. The request rebuilt in parallel.** One piece of work reaches several sessions through
different doors and is built two to four times: on 16 November R-RUNNER-190 four times through
the card door, R-RUNNER-209 twice through a serial run, and the stop at the fill three ways (its
card, a serial run's own `stop_for`, and a book box needing the same broker method).
→ *Caught by:* the runner (outside this repository) never hands out a card or offers a serial run
a request that an open pull request names or an open card carries, and a branch can be held by
hand before its pull request exists. → *Debt:* an interface that three pieces of work need (here
`Broker.move_stop`) is carded first and the rest wait on it; on the runner's list.

**17. The decision asked again.** A session asks for approval the operator has already
given (RUNGS, 16 November: per-rung checks its 15 November ruling allowed), and waits; or
a runner session asks him a second time. The lane idles for half an hour.
→ *Caught by:* his rulings are recorded with their words in the coordinator's log and in
`docs/DECISIONS.md`, and the runner's halt holds the card, never the lane. → *Debt:* no
check reads a session's question against the recorded rulings.

**18. The hand list beside the code.** A rule kept as a list by hand drifts from what the
code does: the trading-path merge hold missed `desk/bars.py`, which the trading day
imports, so a change reached it mid-session (16 November); conformance was scheduled
inside the desk's rounds, which it rightly refuses; a job pointed at a function that had
moved; the hourly report repeated a state long past.
→ *Caught by:* the desk's rounds are kept once in the runner and every schedule and
restart reads them; the hourly report reads current state. → *Debt:* the trading path
computed from the desk step's imports instead of listed.

**19. Replaced while read (Windows).** A writer replaces a file while a reader holds it
open, and Windows refuses ("Access denied", PermissionError): the store's daily files, a
grid file, the runner's own request list, all on 16 November; and the shared clone's
`.git/config`, rewritten by its own readers (every session start tracked a branch there, 208
sections) until READY's reads failed (19 November).
→ *Caught by:* for `.git/config`, the runner writes it no more (its drive `drive_gitconfig`).
Otherwise nothing yet; it is an open debt. The fix is one way to read and write each
shared file, readers and writer under one lock, in each codebase; never a retry or a sleep.

**20. A gate that can never open.** A rule correct where it was written blocks its own
purpose where it runs: the rehearsal was barred for the whole of any trading date, so the
weekday rehearsal could never begin (16 November, 06:30), and then barred whenever the
account held anything, so once the desk traded no rehearsal could pass.
→ *Caught by:* the rehearsal is barred only while a market is open or near (#462). →
*Debt:* a rehearsal beside held lines, never touching them, is being built; until it
lands, the desk's day runs on the coordinator's recorded go.

**21. The claim that drifts.** A session that cannot finish inside its claim moves the work
to a file outside it instead of stopping: #857 rewrote a lab test outside its card, and #902
renamed its new test to another lane's name (19 November).
→ *Caught by:* the runner disarms a pull request whose Claim line is not the claim its card
gave, so it never lands; a card's files are fixed only by runner ops, with the cause.

**22. The done request handed out again.** A request found already met on main is left
open in the lane's list, so every later session checks it again and lands an empty change:
R-MONEY-49 four times (#741, #798, #888, #893), R-MONEY-36 twice (19 November).
→ *Caught by:* the runner keeps every id a landed pull request ticked and never offers it
again. Its root (20 November): the runner reads a done list one request per line, written
`- R-X-n: ...`, and DATA's run-on list (`R-PAPER-23 #294, -22 #505, ...`) closed nothing, so
41 of 100 merges in a day were empty re-verifications. → *Debt:* a check that every
request named under `### Done for other lanes` stands on its own `- R-X-n:` line.
A third root (22 November): a request written inside another's box, with no checkbox
of its own (R-DATA-60 in R-DATA-62, R-MONEY-48 in R-MONEY-35), rode into the host's text,
so DATA was handed it and answered it met 13 times in an hour, each answer dropped because
it was not itself open. → *Caught by:* the runner ends a request's text at the next
request, boxed or not (drive `drive_runon`).

**23. The order the broker may hold, forgotten.** A gateway blip arrives after an order is
sent (2110, 2157, 20 November 08:27): the desk called it never received and deleted its
note, or called it unknown and turned the kill switch on, and a market buy of 195 ISF sat
working at the broker with no record in the book until the operator released the switch.
→ *Caught by:* a disconnect after the send keeps the order's note for the next step to
cancel or book (R-RUNNER-389, #1008, `tests/unit/test_book.py`). → *Debt:* connectivity news
mid-send never pulls the kill switch (R-RUNNER-390), and the broker fault matrix in SimCity,
every message class at every moment of a send (R-RUNNER-392). The same mechanism has
fixed `desk/paper.py` three times in ten changes (#373 the gateway's wait, #860 a market
order's wait, #1014 link news mid-send): the paper door learns IBKR's behaviour one live
fault at a time, never from a table of everything the gateway can say; the matrix is that
table.
The send path's side of it has fixed `desk/book.py` twice the same day (#1008 the going note
kept on a disconnect, #1031 a halt cancelling working buys) with a third change due (an order
the desk cancelled sent once more, pattern 25): what the desk knows of the orders the broker
holds (sent, working, cancelled by whom) was built for the day that goes well, and each edge
was met live. The same matrix, its rows run through `book.send`, is the table for it.

**24. A wait added inside a step, its caller's timeout left.** Each market order came to
wait 120 seconds for its fill (da70408), while the runner still killed the whole desk step
at 240 seconds: London's round died mid-send (20 November 08:22).
→ *Caught by:* the runner's drive `drive_atjobs`: the desk step's timeout is at least its
worst-case waits plus a margin (6 orders x 120 s + 60 s; now 900 s).

**25. The order the desk withdrew, never sent again.** An order id is fixed for its day, so
an order the desk's own recovery cancelled at 0 filled answers every later send with its
old Cancelled state: London's 09:00 round sent nothing (20 November).
→ *Caught by:* it is sent once more that day as `<id>-r1` (`tests/unit/test_book_retry.py`).

**26. The file read whole that grew.** The ladder kept every verdict it ever wrote, each
re-judged cell adding a line and none removed, and read and parsed the whole file on every
start: at 1.2 GB it held 12.8 GB, EPON idle nine hours (21 Nov); 37 reads like it on main.
Twin: `desk/book_parts.py` re-read the pounds file once a trip; deep SimCity hung 2 h (22 Nov).
→ *Caught by:* the ratchet `test_whole_file_reads_never_rise`: whole-file reads in `desk/`
and `lab/` may fall and never rise; a file that cannot grow says why on the same line
(`# bounded: <why>`). *Debt:* the growing stores among the 37 are streamed (ladder first,
R-RUNNER-432) and a results file keeps one line per cell, compacted as it is written.

**27. The folder guessed from another.** `rates` read the store above the records folder
`desk/command.py` gave it: true live, false in the rehearsal (records two deeper), so Monday read
NO-GO (22 Nov 18:06); conformance, `desk/simcitycmd.py` and the fills replay guessed alike. Twin:
`desk/day_parts.py` read old records by names never written (#1967) and the day's loss from the
last record of any date: Friday's refused every Monday buy (23 Nov). *Debt:* a loss has no date.
→ *Caught by:* each caller names its home; the rates stubs fail when handed a records folder;
`tests/unit/test_day.py` reads the live pre-FX records; #2039 plants Friday's loss on a Monday.
