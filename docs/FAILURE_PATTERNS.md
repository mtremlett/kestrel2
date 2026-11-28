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
→ *Caught by:* the only progress number is plan boxes ticked on main per 24 hours, from one
function, and the plan requires a batch adding net lines to name the scene it advances.

**4. The set-aside test.** A test fails, is added to a known-failures list "for now", and
is never fixed. The predecessor carried 2,221.
→ *Caught by:* a guard forbids skip and expected-failure markers. There is no list.

**5. The test that reads the live desk.** A test passes on the operator's machine because it
reads his real data or broker, or runs his PC's own tools (mypy 2.3.0 for the pinned 1.14.1, #2233).
→ *Caught by:* a guard forbids machine-specific paths; `test_the_check_runs_the_pinned_tools`;
and GitHub runs the whole check on a machine with no access to any of it.

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
→ *Caught by:* `test_constants_with_two_homes_never_rise`: a constant name in two modules may fall, never rise.

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
rule into `desk/store.py` and `desk/store_parts.py`, or real prices into `desk/lines.py`: the
store fitted a line at a time (14 Nov: three rule changes in twenty minutes on six lines). Twins:
`desk/keeper.py`'s withdrawal of the days its judge drops (#855; #2088, VUAG 2019); and the writer,
`desk/bars_form.py`, on which source takes a held day (#861, #2361, #2404): the keeper reads a marked
day as unheld, the writer as held, so each re-clean met the gap live. → *Caught by:* the runner's
halt on a lane's second `fix` to a file within ten landed changes; `tests/unit/test_store_rules.py`
(#225) pins every store rule to a fixture row (R-RUNNER-43, #227); the hover names off-IBKR days;
`test_every_withdraw_rule_of_the_keeper_and_the_writer_is_pinned_by_a_row` each mark rule (27 Nov).

**14. The judge fixed from the outside in.** `lab/ladder.py` took four fixes in ten changes
(#402, #419, #405, #410, #427): each review found a new edge in the one 400-line module that
judges, counts, keeps tapes and writes the table; no rung had a golden verdict pinned, so
nothing showed a judgement drift until a reviewer read the code.
→ *Caught by:* the rung registry, the module split, the churn guard. Twin, `lab/ladder_sets.py`
(#1992, 9db3dee8, #2218): 'stopped part-way' reaches the table writer as text, not a typed
result. → *Caught by:* `test_a_stopped_pass_writes_no_table_and_the_survivorship_line_counts_the_uncorrected`.
Twin, `lab/verdict.py` (#2491, O95 I3b, I7): the one rule was written again for each kind of row
(cell, stopped line, basket), each copy short a gate. → *Caught by:* one `verdict.answered`.
→ *Debt:* a typed pass outcome (A2); a golden verdict per rung on the fixture (B5).

**15. The broker the pretend never met.** `desk/conformance.py` is the only code that
cancels, re-sends and trades beside the desk's book at the real broker, so each live run
found a broker behaviour the pretend lacked (orders refused as duplicates, #435; a stop
"triggered" by a cancel and a market sell, 16 Nov). Twin: `desk/history.py` met IBKR's bar
answers one shape at a time (#739 the store's marks, #2053 its Busy text, #2460 a decimal
volume '2831.4' that stopped the greenkeeper's whole run, 28 Nov).
→ *Caught by:* every run keeps its tape (the broker's own words); a step whose sides differ is
a finding (#557); the module split (`desk/conformance_parts.py`); history reads each bar field
once, at entry, refusing an unknown shape in IBKR's words. *Debt:* no table of IBKR's bars.

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

**18. The hand list beside the code.** A rule kept by hand drifts from what the code does: the
trading-path merge hold missed `desk/bars.py`, which the trading day imports (16 November);
conformance was scheduled inside the desk's rounds; a job pointed at a moved function; the hourly
report repeated a state long past. Twins: `lab/basket.py` pairs a basket's sale days to its market
line's bars by its own date lookup (#2217 a holiday, #2353 a stale line); `desk/keeper_live.py`'s
roll kept its own list of spans, so the long store's 15m and 30m never came (O12, 27 Nov).
→ *Caught by:* rounds kept once in the runner; the report reads now; `test_lab_basket.py` plants
edges; the roll copies all spans. *Debt:* trading path from imports; the basket on the one calendar.

**19. Replaced while read (Windows).** A writer replaces a file while a reader holds it
open, and Windows refuses ("Access denied", PermissionError): the store's daily files, a
grid file, the runner's own request list, all on 16 November; and the shared clone's
`.git/config`, rewritten by its own readers (every session start tracked a branch there, 208
sections) until READY's reads failed (19 November).
→ *Caught by:* for `.git/config`, the runner writes it no more (its drive `drive_gitconfig`).
Elsewhere `test_file_replaces_never_rise` holds the replaces at 19. *Debt:* one way to read and
write each shared file, readers and writer under one lock; never a retry or a sleep.

**20. A gate that can never open.** A rule correct where written blocks its purpose where it
runs: the rehearsal barred on any trading date or held line (16 Nov); `desk/running.py` set London
in IBKR paper's dead window; `desk/placing.py` judged an intraday order by a daily one's sessions;
`desk/day.py` sized and capped the zoo by the desk's book (#2036, #2084, #2105; 23 Nov); one line's
missing close stopped the whole day, and `desk/simcity.py` and `desk/simcity_incidents.py`, whose
promises pin a refusal's wording, were fixed with it each time (#1755, #1909, #2168).
→ *Caught by:* #462; the London round's test; zoo-due-session's; `test_day_standing.py`'s round test. *Debt:* a rehearsal beside held lines; until then, the coordinator's go; SimCity's promises match text, not a type.

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
Twin: each SimCity day redid the desk's whole past (`desk/book_parts.py`, `desk/book_parts2.py`,
`desk/orders.py`: files re-read and rewritten, every fill re-priced, astuple): deep 2.8 h (27 Nov).
→ *Caught by:* the ratchet `test_whole_file_reads_never_rise`; `book_parts.read_once` and `add`
(grown, never re-read), `book._summed`; SimCity's reads-per-day and flat-day tests. *Debt:* the
37 growing stores streamed (ladder first, R-RUNNER-432), one line per cell, compacted as written.

**27. The folder guessed from another.** `rates` read the store above the records folder
`desk/command.py` gave it: true live, false in the rehearsal (records two deeper), so Monday read
NO-GO (22 Nov 18:06); conformance, `desk/simcitycmd.py` and the fills replay guessed alike. Twin:
`desk/day_parts.py` read old records by names never written (#1967) and the day's loss from the
last record of any date: Friday's refused every Monday buy (23 Nov). *Debt:* a loss has no date.
→ *Caught by:* each caller names its home; the rates stubs fail when handed a records folder;
`tests/unit/test_day.py` reads the live pre-FX records; #2039 plants Friday's loss on a Monday.
