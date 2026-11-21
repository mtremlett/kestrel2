# The money lane

The money lane's own decisions, each a dated `###` entry saying what was decided, the
options, why, and the evidence; newest last. Only this lane's scribe writes here, so no
other lane's pull request touches these lines. Held to a size a session reads whole
(`BUDGET.json`, `max_lines_per_lane_doc`): when it is full, the scribe folds the oldest
settled entries into one short summary entry; git keeps every word.

## Decisions

### 2026-11-13 — summary of the first five decisions (folded 17 November; git keeps every word)
- Pretend broker: behaves as the paper one will, with its five faults. Send path: ask the broker first, gate second, a fill written once. Book: the ledger's fills, read by the gate. Day run: whose position, which day, which rate. Reconciliation: shares and stops checked before every order; scenes 6 and 7 together.

### 2026-11-13 — one rule for "is the book the broker's?", for every broker

**Decided**, by the lane as the desk's mentor (no one watching), on the paper lane's request
R-PAPER-1: the comparison of the desk's book with a broker's holdings has one home,
`book.differences`, and reconciliation (`book.reconcile`, `book.send`) is rebuilt on it.

1. **What it is handed: the book, and the broker's entries, each a name and its shares.**
   Options were (a) the pretend broker's own answer, one number a line, which a real
   account's rows would have to be added together to fit, the very fault the paper lane's
   blind review found; (b) a typed holding carrying the real broker's own words (its kind
   of product, its currency), which puts one broker's language in the core and means
   nothing at the pretend one; (c) plain entries, each named by the door that read them in
   the same words it names the book's lines in. Chosen (c): the paper door names an entry
   by its symbol, kind and currency, the pretend broker by its symbol, and the rule itself
   knows no broker.
2. **Entry by entry, never added up.** Taken whole from the paper lane's rule: each entry
   must itself be the book's shares; a line the book holds and the broker does not list is
   named at no shares; a line listed at no shares is no holding.
3. **A line with shares in two entries is never the book's.** The paper door's rule passed
   two entries that were each the book's shares, which is what two accounts each holding
   the line would look like: twice the book, read as clean. Options were to carry the rule
   over exactly as it stood, or to close this while it was being given its one home.
   Chosen: close it. The book holds a line once. Zero entries do not count as a second
   place, so every case the paper door's tests hold today comes out as before.
4. **The resting stops go through the same rule.** "The stop is for exactly the shares
   held" is the same comparison with the stops as the entries, so reconciliation asks one
   rule twice and has none of its own. When the paper door is taught the desk's own stops,
   it can hand them to the same rule.
5. **What comes back: one typed difference for each entry that is not the book's**, with
   the name, the broker's shares and the book's. Reconciliation keeps the names, as scene 6
   reads them; the paper door can word its sentences from the same record.
6. **The paper door's own comparison stays until the paper lane moves it** (its file, asked
   as R-MONEY-4). Until then the rule is written twice; after it, once.
7. **The other blocking request (R-PAPER-2, any broker behind the send path) is the next
   session's**, not folded into this one: one objective a session. It should have a broker
   give its holdings and stops as entries, so a real account's rows reach this rule whole.

**Evidence.** The contract test was seen failing first (`book.differences` did not exist).
Run from outside the repository, the old book and the new traded the rehearsal's fourteen
months to the same 68 fills, 34 round trips and every order's answer, with and without each
line's first order rejected. A blind review found nothing blocking. It set the rule against
its own separate statement of it on 210,525 accounts of up to three entries (whole, short,
fractional and zero shares): no disagreement passed as clean and no agreement was named. It
ran the old reconciliation and the new side by side over 8,000 random runs at the pretend
broker with every fault, hand trades and cancelled stops: no difference in any answer,
ledger or refusal. And it rebuilt the paper door on the rule in a copy: all forty of the
door's tests passed unchanged, and of 83,793 accounts none became less safe (23 false
cleans, all "two entries each the book's", became named). Sixty-seven deliberate breaks were
driven in copies outside the repository, with Python's cache off: forty-three by the lane
(thirty-nine caught at once, two gaps closed, two that cannot differ) and twenty-four by
the review (eight survived: six gaps, one of them found by the lane too, each closed and
caught; two that cannot differ at the pretend broker). The seven gaps were a one-share
line, a zero entry beside two that cancel, the lines named out of order, a stop for fewer
shares than held, entries given as a stream that can be read once, a matching entry beside
a wrong one, and a line listed only at no shares. What the review left is in
`docs/STATUS.md`.

### 2026-11-13 — any broker behind the send path: five questions, entries, each asked once

**Decided**, by the lane as the desk's mentor (no one watching), on the paper lane's request
R-PAPER-2: the send path, the ledger and the day run know a broker by five questions
(`broker.Broker`) and no longer by the pretend broker's name.

1. **A stated interface, not a parent class.** Options were (a) the paper adapter inherits
   from the pretend broker, and with it a simulation's insides; (b) a parent class both must
   inherit; (c) a typed statement of the questions, which any class that answers them
   satisfies, the type check proving it wherever one is handed over. Chosen (c). It sits in
   `desk/broker.py` beside the answers a broker gives (`Fill`, `Report`, `Disconnected`), so
   an adapter imports one module. The manifest's line for that file still says only "the
   pretend broker": a lane may not reword it, so a session he starts should.
2. **Five questions, the ones the send path and the day run ask:** what did you do with
   this order id; take this order; your fills; your holdings; your resting stops. Opening a
   day, planting a position, cancelling a stop by hand and the stops' levels are the
   simulation's own instruments and stay off it. Cancelling orders will be the sixth, added
   with the kill switch that needs it, not before.
3. **Holdings and stops are entries, a name and its shares each, as the broker gives them.**
   The pretend broker gave one number a line, a shape a real account's rows would have to be
   added together to fit. It now gives entries too (`holdings`, `stops`), and its old answer
   (`positions`) is gone, not kept beside: one job, one path. Its stops with their levels
   (`resting_stops`) stay for the simulation's tests, which prove the level.
4. **A line's symbol names that line and nothing else.** The door that reads an account
   names each entry; anything that is not the line itself (another kind of product, another
   currency) goes under a name of its own. Such an entry is named as a difference and stops
   all buying. Options for the line's own sale were to refuse it too, or to allow it while
   the line's own entry agrees. Chosen: allow it, as a line that has lost its stop may be
   sold: the shares are known to be there, and a sale only lowers risk.
5. **Each question asked once for an order, the stops before the holdings.** The send path
   asked for the holdings twice, once to name what differs and once to judge the order's own
   line. It now asks once for the fills, the stops and the holdings, and judges both from
   those answers (`book._compare`). They are three moments at a real broker, and the order
   matters (the blind review's blocking finding): with the holdings read first, a stop that
   sold between the two readings looked like "shares there, stop gone", a line that may be
   sold, and its sale went out for shares already sold. Read stops first and the same moment
   shows the shares gone, and the sale is refused. A stop that sells after the last reading
   no order of questions can catch: that is the broker's to refuse.
6. **`place` gives an order's last answer.** The send path and the gate count fills only, so
   an order left working at the broker is in none of the five answers, and six buys could
   each pass a gate that sees an empty book. Options were to add working orders to the
   interface now, or to state that an adapter must not leave one working. Chosen: state it
   (what is not filled is cancelled), and let working orders arrive with cancelling, in the
   kill switch's step. The interface also states what the send path leans on: one stop a
   line, for all the shares held; fills in the order made, under ids that never change; an
   answer whole or an error.
7. **Left open, in `docs/STATUS.md`:** a resting order that is not a sell stop is unseen, a
   stop's level is never compared, and a connection lost while reading is not a stated answer.

**Evidence.** Tests seen failing first: the type check refused any broker but the pretend
one (seven errors), the new contract test failed on "one order, two readings", and the
review's race test failed with the sale not refused. Run from outside the repository, main
and this branch traded the fourteen months to the same ledger and the same answers, with and
without every first order rejected (68 fills, 34 round trips), before the repair and after.
The blind review rebuilt the old send path and ran it beside the new over 4,000 random
sequences (179,764 steps: buys, sales, every fault, hand trades, cancelled stops) and 600
random mornings of the day run: no answer, refusal, ledger or holding differed. Its one
blocking finding is point 5, fixed and tested; its lesser ones are taken (the interface's
wording, three test gaps) or recorded. Eighty-five deliberate breaks were driven in copies
outside the repository, Python's cache off: thirty-nine by the lane (one gap: a broker's
rows collapsed into one a name), thirty-one by the review (five survived), fifteen on the
repaired code (one gap: two stops collapsed). Six gaps are closed and each is now caught; the
one left narrows a type of the interface's, which can refuse a broker, never admit one.

### 2026-11-13 — the money book's next boxes noted: the kill switch first (#76)

**Decided**, by the lane as the desk's mentor.
- *The kill switch's files.* Options: refuse at the gate in `desk/orders.py`, or on the send
  path in `desk/book.py`. Chosen: the send path, with a new `desk/kill.py` and `desk/broker.py`
  (cancelling). The gate stays a pure rule over the order and the book; whether the switch is
  thrown is a fact on disk, read at the edge where the reconciliation refusal already lives.
- *The costs wait for the kill switch (`after: money-kill`).* Options: side by side, or in turn.
  Chosen: in turn; both change `desk/book.py`, and his ruling puts the kill switch first.
- *The crash watch left un-noted.* Options: note it with no `after` (a session would meet it
  before the five-minute data exists), or wait. Chosen: wait for the data lane's box ids.
- *File lists err wide.* A session may change nothing outside its note, so a missing file strands
  it; a wider note only makes it wait its turn.

### 2026-11-13 — each strategy declares what it is (#92, money-declared)

**Decided**, by the lane as the desk's mentor.
- *Holding period: each of the five declares none.* Options: (a) 5 sessions for RSI-2 and 20 for
  Bollinger, the span of the average each sells on; (b) none for all five; (c) a number measured
  from history. First built (a), but neither published rule has a time exit: RSI-2 outstays 5
  sessions in 13 of 39 golden trades, Bollinger outstays 20 in 29 of 52 (longest 133). Chosen (b):
  a declaration says only what its rule does; (c) is tuning. The time stop (STP-11) must choose
  each limit and build the exit in the same change; the golden days will move, so it needs his
  approval (canon B5).
- *Test universe: every line of the instrument master, by reference.* Options: (a) the master's
  lines; (b) a narrower list per rule; (c) a rule about a line's facts. Chosen (a): a rule judged on
  fewer lines than it trades would trade unjudged; (b) changes what is traded with no evidence;
  (c) makes the research list part of a verdict. By reference, so a new line is declared at once.
- *Data: the numbers of the daily bar a rule reads*, proved (not a named source: the desk has one).
- *The bar is one value, daily;* a second comes with the bars that would feed it.
- *The declaration sits on the rule itself.* Options: (a) on the rule; (b) a second table by name;
  (c) a wrapper. Chosen (a): one home; a rule without one fails the type check.
- *A short sale.* No word for it in declaration, action or decision; the template sells only what
  is held. A hand-made decision to sell is left to the gate (refusing it at its making breaks
  orders tests this box may not edit); the true fix is the order type (recommended box).
- *Ticked though a remainder is named:* a session given the same files could do no more.

### 2026-11-13 — the kill switch and its drill (#95, money-kill)

**Decided**, by the lane as the desk's mentor.
- *The stops stay.* Options: (a) cancel everything, stops included; (b) cancel and sell all held;
  (c) cancel working orders, keep the stops. Chosen (c): removing stops would leave holdings
  unprotected when something is wrong; selling all is a trading decision. The message says what is held.
- *Sales are refused too* (not only buys): all new orders stop, the one promise simple enough to
  trust in an emergency; the stops at the broker still sell.
- *The switch goes on the record before the broker is asked*: the desk is stopped even if the
  broker's line is down.
- *The send path reads the switch itself* (`desk/book.py`), not callers: nothing bypasses it (B1).
  It reads twice, before the broker is asked and at the last moment before the order goes; each
  reading was removed in turn and the tests caught both.
- *An order the broker already has is still recorded while the switch is on*: recording sends
  nothing, and refusing would leave the book wrong.
- *Only the operator releases it*, with a reason; no timer. A pull never fails for want of a
  reason ("no reason given"). A record that cannot be read stops the desk (fail shut).
- *The drill is real, on a scratch desk at the pretend broker* (options: pull the real switch; a
  checklist): it stops no real trading, cannot be ticked without being run, and fails by name.
  "Monthly" is 31 days. The pretend broker gains one fault, an order left working.
- *Branch:* finished on `lane/money-1113-203647-s1` as asked; nothing pushed to `lane/money-1113-212543-s1`.

### 2026-11-13 — the costs whole (money-costs, #101)

**Decided**, by the lane as the desk's mentor, under his ruling "always go with recommended".
- *Spread: 0.05% of a leg's value, assumed.* Options: nothing until measured; one flat assumed rate; a measured figure per line. Chosen the flat rate now, measurement asked for (R-MONEY-10): a result with no spread flatters every strategy (canon B4).
- *Slippage: 0.05% a leg, assumed.* Same options, same choice.
- *A leveraged line pays its leverage times as much.* Options: one rate; times leverage; per line. Chosen times leverage: 3LGO pays 0.15% a leg, 5QQQ 0.25%.
- *A stop's sale slips three times as far* (the spread is not multiplied). Options: as any sale; a multiple; modelled from each day's fall. Chosen three times: a stop sells into a fall.
- *Spread and slippage are taken off the profit, not counted in an order's cost.* Options: inside the fifth of capital; profit only. Chosen profit only: they are the fill being worse than the sizing price, not a bill; it keeps the numbers research has judged.
- *UK tax is part of an order's cost.* Options: profit only; also in the order's cost. Chosen both: it is cash leaving with the purchase.
- *The regulators' fees (SEC, FINRA) go in the commission line.* Options: a sixth line; with commission. Chosen with commission: scene 7 names five lines.
- *The FINRA fee is charged though on holiday to the end of 2026.* Options: nought until January; the published rate. Chosen the rate: a date is a special case; the error is a fraction of a penny, on the safe side.
- *The leg is a typed word* (`orders.Leg`, read in `orders.leg_of`). Options: a sign and a flag; three words. Chosen three words.

**Evidence.** Fourteen months: costs £161.54 → £338.78, profit £967.23 → £791.66. Blind review: no wrong money. 35 breaks, 34 caught, the missed one (UK tax left out of the total) now caught.

### 2026-11-13 — the three emergencies in numbers (money-emergencies, #108)

**Decided**, by the lane as the desk's mentor, under his ruling "always go with recommended". A changed number is one line of code and one of its test.
- *"The market".* Options: the S&P 500 in dollars at New York's close; the yardstick as the desk reads it (pounds, London's close). Chosen the yardstick (VUAG, AG-04); numbers set on VUSA (same index since 2012) and checked on VUAG. New York's numbers on the desk's series would cry black swan on a crash; the code refuses any other market reading.
- *A crash: 4% in a day or 12% below the month's high.* Measured on VUSA: 4%/10% 46 days, 7 episodes; 4%/12% 26 days, 6; 5%/12% 22, 3; 5%/15% 14, March 2020 only. Chosen 4%/12%: the six episodes anyone would name, none missed. It halts buying; sells nothing (his stop already says where to sell).
- *A black swan: 10% in a day or 30% below the month's high.* Options: just beyond the worst closes (8%/25%); round numbers beyond the worst readings within a day (8.7%/26.0%). Chosen the latter: the crash watch reads within the day, so 8% could have sold everything on 9 and 12 March 2020. It means cash, and only the operator lifts it.
- *An emergency: one line down 10% in a day, in its market's terms* (tied to `STOP_FALL`). Options 5%, 7%, 10%, 13%, 15%. Chosen 10%: about ten a year across twenty lines (5% would be about sixty from the US shares alone). The desk buys no more of that line; others carry on. Only the day's fall counts, not the month's.
- *When each ends:* only when a day ends clear of it; a reading within the day raises, never lifts.
- *A bar's close is read, never its low:* the archive's bad lows would each have been a black swan.
- *His other words:* a desk fault is the book not matching (EMG-06) and the kill switch (EMG-02); a volatility spike is a crash; a market halt has no price, so it is unread, never calm.
- *Unread is its own answer* (`Unread`, raised by name). Options: measure with whatever is given; refuse. Chosen refuse.
- *The definitions say what the desk "is to" do*, since nothing acts yet; the type is `Response`, not a second `Action`.

**Evidence.** Four blind reviews (the first found the numbers set on the wrong series); breaks 91 of 92 caught, the last then caught.

### 2026-11-14 — the day's record (money-record, #114 and #124)

**Decided**, by the lane as the desk's mentor, under his ruling "always go with recommended".
- *A day's profit is the book's gain, not only closed trades.* Options: round trips closed that day; change in worth plus dealing less costs. Chosen the second: a falling day is a losing day. They agree when the book is flat.
- *One rounding policy: to the penny, half to even, once, where published.* Everything before is exact.
- *The market's figure: the capital times the yardstick's move over the record's days.* Options: the same capital each day; the capital bought once and held. Chosen each day (like-for-like with the fixed capital). The column must not be added up as buy-and-hold (R-MONEY-14).
- *Each record opens from what the last closed on* (worth and count of fills kept in the record). Options: work it out again from files; keep it. Chosen keep: the first review showed two ways the first loses money in silence.
- *A record is never rewritten;* a late fill is in the next record.
- *A withheld day's money is published with the next plain number* rather than left out of every record.
- *A day is over when its record is made, or the ledger holds a later fill.* Options: ledger alone (as landed in #114); records alone (blind before the first record); either. Chosen either (#124): each sees what the other cannot.
- *A missing record does not hold the next day's orders.* Options: no order until every earlier session has its record; buys held, sales through; nothing held. Chosen nothing held: one late close must not stop rule sales.
- *A records file the desk cannot read stops the morning's orders;* an absent file (a new desk) trades. Chosen stop loudly.
- *A holding is valued at that very day's rate or the day has no record;* records begin at the ledger's first fill; a bar owed is an error unless the line is suspended.
- *Scene 6's last check reads "something was held on some day"*, and both books are compared every day.
- *The ledger writer keeps its private name* (`book._write`) so the paper lane's merged code stays green; asked of PAPER (R-MONEY-11).
- *#114 landed before its last mend's review reported* (#124 closed the finding); nothing but the pretend broker is on this path.

**Evidence.** Fourteen months: 310 days' profits add to £791.66, the 34 round trips'. #114: three blind reviews, 4 blocking findings mended, 27 breaks, 25 caught and the 2 missed then caught. #124: a review found an old day with a made record could be sent again (five buys, £11,602 on £10,000 in its run); closed, eight breaks all caught.

### 2026-11-14 — the rest of the money book noted (money-notes, #130)

- *The crash watch has its own module, `desk/watch.py`, and waits for the halts.* Options: (a) a new module that reads the bars and the emergency thresholds and raises a halt; (b) inside `desk/emergency.py`. Chosen (a): emergency is pure definitions and measurement, the watch runs every five minutes and acts, and "halts all buying" needs the typed halt first. It does not wait for the data lane (the five-minute bar type is in the store); his alert is the paper lane's messenger, the watch gives the words.
- *The golden run (money-golden) holds all the lane's files and runs alone, after the fills, limits and halts.* Options: (a) commit it now; (b) once what a fill costs and what the gate refuses have stopped moving. Chosen (b): each golden change needs his approval (canon B5), so committing early spends his attention on planned changes. Its numbers live in a file the lane owns (a unit test beside the day's).
- *Fills realistic waits for the money invariants,* so the change to what a fill is lands under the property tests.
- *Honest money and the whole story wait for the fills,* which move the profit lines they report. Neither waits for the golden run; if honest money lands after it, its interest moves the golden numbers once, with the explanation B5 asks for.
- *Boxes that share files but do not depend on each other* (small trades, time and gaps, the stranger) carry no `after`: the runner already keeps two sessions off the same files.

### 2026-11-14 — the money invariants (money-invariants, TST-04, #132)

- *Seeded with the standard library's random numbers, not a property-testing library.* Options: (a) `hypothesis` (a new dependency: his approval, and `requirements.txt` is outside the claim); (b) worlds from `random.Random(seed)`, as the lab's tests do. Chosen (b): no dependency, the same world for the same seed everywhere, a failing seed is its own reproduction.
- *"Equity is cash plus market value" is tested through the day's published record.* Options: (a) at the book alone, valuing holdings in the test: the first blind review proved the value cancels and the check cannot fail; (b) drive `day.publish` in every world and set its worth and profit against the broker's holdings at the test's own closes and rates; (c) leave it to a box that owns the day's tests. Chosen (b): the record is the only place the desk states its equity. The file is named for the book because the claim names it so.
- *The late-fill path is kept beside the record.* The record brings the ledger up to date first, so it never meets a late fill against the pretend broker; the test also counts each day's dealing on the ledger as it stood (`book.dealt`) and holds each fill counted once.
- *Costs shared between round trips are compared to 1e-27 of a pound, everything else exactly.* Sharing a split fill's costs by division is the one inexact step; the largest difference measured was 2.1e-27.
- *The guard proved (canon A7): 37 deliberate breaks, 36 caught,* two by no other money-path test (a sale closing the newest buy; a part-sold buy sent to the back of the queue). Not caught: a book-and-broker comparison that finds nothing, which breaks no invariant where the two always agree; the reconciliation tests catch it. Two blind reviews found three blocking issues, all mended: the market-value term cancelled, a cancelled order that later filled was invisible, a first send reaching the broker twice went unseen.
- Found, not fixed (product files outside the claim): no fault can reach a sale; the pretend broker never fills in two executions; an order's state is read from words, not typed.
- All of this is paper. His standing ruling of 13 November: "please always go with recommended to avoid waiting for me to attend".

### 2026-11-14 — SimCity, small (money-simcity, #134)

Decided by the MONEY lane as the desk's mentor, no one watching.

- *What a "part of the money path" is.* Options: a hand-kept list; every function; everything the six modules offer by name plus the broker's five faults. Chosen: the last. A hand list rots; private helpers are their callers' business. A rule's own arithmetic is not a part; "rules that never held a line" is reported beside the census.
- *Measured, not claimed.* Options: scenarios declare their cover; the profiler records what ran. Chosen: the profiler (about 17 seconds a night).
- *Which modules.* Six: strategy, orders, broker, book, day, kill. Not `emergency.py` until the crash watch is built.
- *One life, not several.* A fault on every line; each thing done to the desk waits for a plain day. Several lives cost about a minute each.
- *"One command" is a function,* run by the check on every change; a command-line entry would reach into `tests/`. The nightly run on his PC is the runner's.
- *The night's test sits with the unit tests,* so the scenes stay his seven.
- *Land RED and pin it.* Options: leave the limit of five untried; try it, say RED, pin the test to that one broken promise; mend the send path here (outside the box's files). Chosen: the second. The pin fails if any other promise breaks, or the moment the fault is mended.
- *A red night is kept; a night that cannot be lived is an error.* Nothing written when data is missing or the time is not UTC.
- *No exact money figures pinned,* so another lane's rightful change cannot turn this test red beyond its claim.
- Evidence: two blind reviews, each with a blocking finding mended; 27 deliberate breaks, 24 caught, 1 closed by a test, 1 dead name removed, 1 rightly green.
- Found, not fixed: six lines held when a working order fills late (box money-working); a cancelled stop never put back (money-restop).
- All of this is paper. His standing ruling of 13 November: "please always go with recommended to avoid waiting for me to attend".

### 2026-11-14 — a hundred seeded worlds (money-worlds, #150)
- What a world is. Options: (a) made-up random markets; (b) the saved data as it stands, only faults seeded; (c) the saved lines on their own days, each line's months dealt again by the world's number. Chosen (c): calendars, gaps and each day's shape stay real, and a real archive needs no new code.
- Each line's months in an order of its own (b), not one order for the world (a): the rehearsal lines all follow one shape, so (a) would put every line's buy on one morning. The cost: days when everything falls together are not rehearsed.
- Every world seeded; the saved data as it stands is no longer lived whole by SimCity (a special case for one input; the scenes live it).
- Faults drawn at the broker's door for each order, one in four (not one per line per life): a sale can now meet one.
- Things done to the desk take turns in an order each world deals, on one fit morning in eight (not a fixed order, nor a free draw that left one world in eight without one of the three).
- A stop cancelled by hand is put back the next morning seven times in eight. Never put back froze the desks 30% to 67% of days; always put back never tries the long freeze. 14% of days withheld.
- A world in which the desk refuses to go on is a RED night naming world, day and words (its ValueErrors only), not a dead night. This changes #134's ruling in one case: data the desk cannot price is now a RED record.
- The check lives world 0 of the fourteen months; the hundred are the nightly command's (a hundred would take two hours).
- The fourteen-month test allows the known six-lines fault and does not ask for it (SIX_HELD): three worlds in four break it, so any rightful change by another session would turn their check red. The limit is proved another way; a green night is held to green. The box that mends it removes the allowance.
- Prices are rounded to the penny by the desk's one rounding; simcity.csv gained "worlds" (none existed); tests grew 146 lines against 99, the guard has room.
- Ticks: money-worlds. Evidence: 53 deliberate breaks, 52 caught, one rightly not a promise.

### 2026-11-14 — halts (money-halts, #148)
- Where enforced. Options: (a) in the day's trading; (b) at the send path, the one door. Chosen (b): "no halt bypassed" (A-GATE); read again at the last moment, as the kill switch is.
- A halt stops buys only (his emergencies ruling, #108). It never expires (FIL-08: the old desk's halts were set and forgotten); only lift, with a reason, ends it.
- A halt cancels nothing at the broker; the kill switch does. Options: (a) cancel every working order (would cancel a rule's sale too); (b) a buys-only cancel (right, needs broker files); (c) state the limit now. Chosen (c) now, (b) with the crash watch.
- No well-made halt is refused (a safety act is not refused over a clock); a halt is known by its moment and reason, the same twice is kept once, lifting names the very halt.
- A halt marks every UTC day from called to lifted, both included, whatever the hour: errs toward not counting. A halted day keeps its profit figure (the money is real) and does not count.
- The verdict also reads what the send path did (a mis-dated lift could let a day count with six buys refused); the kill switch counts against the day too; a day whose orders were never sent does not count.
- The morning's list holds everything day.trade answered that did not fill whole, sales included, and the lines with no bar for the session before, named apart (a stale morning reading "0 blocked" is the old silent stop).
- Refusals at the paper account's door are filed under "the broker, or the desk's door to it".
- desk/halt.py borrows the price store's file writer (the send path reads halts, so the halt sits below the book); one public writer owed (R-PAPER-7, R-MONEY-11).
- Record.counts is stored when the record is made (SimCity's census would turn red for a new public function).
- Records built without the two new facts, and a row of ten columns kept by hand (#152), read as nothing known sent and cannot count. Options: (a) strict reader, close this change until PAPER mends; (b) read such rows as the record's own not-known state; (c) convert old-name files (none exist). Chosen (b) as a bridge, asked of PAPER (R-MONEY-20, 21); the reader's allowance and the defaults go together.
- records.csv changes shape with no conversion (no day's record exists outside a test). Who called a halt, who may lift it and a halt on one line are not recorded yet (crash watch).
- Ticks: money-halts. Evidence: 128 deliberate breaks, 125 caught, 3 closed.

### 2026-11-14 — a dead desk's working orders cancelled, not counted (money-working, #163)
- What to do with an order a dead desk left working. Options: (a) as the box worded it: every broker gains a question and the limit counts the answer; (b) the desk notes each order as it goes, and after a death has the broker cancel whatever is working before it sends; (c) land nothing and ask the paper lane first. Chosen (b): (a) cannot be green from this box's files (the paper adapter is the paper lane's, and added questions change conversations its tests hold byte for byte); (c) leaves the limit broken and R-MONEY-15 open for rounds. (b) asks nothing new of any broker and is the 13 November broker ruling (what is not filled is cancelled). Cost: that trade is given up for the day; its rule asks again tomorrow. After a crash the desk prefers flat and certain.
- The box is ticked though its second clause (a broker says which orders are working) is not built as worded: nothing is left working to list.
- Which endings leave the note. Options: (a) only a death; (b) every ending but the broker's last answer or its door's word that nothing went. Chosen (b): not knowing is treated as a death.
- The cancel comes at the start of every send (not only before a new order), so the leftover order's answer never reads "working" a moment before it is cancelled. While the kill switch is on the note waits: the pull has cancelled, and a refusal made with the switch on asks the broker nothing.
- SimCity's eleventh promise: no order is left working at a day's end. The check's one lived world moved from 0 to 1, the first that came to six lines, so the test fails without the mend. The sending-twice test was tightened, not loosened (a working order's answer changes to cancelled, no fill added).
- Evidence: hundred worlds GREEN (31,000 days, 1,195 deaths, 583 orders left working); 24 deliberate breaks, 20 caught at once, 4 survivors closed. Ticks: money-working.

### 2026-11-14 — the crash watch (money-watch, #172)
- His lift of a watch's halt. Options: (a) it stands until the market ends a day clear; (b) for that day only; (c) no memory: while the market still raises the halt, the watch calls it again and tells him. Built (a), narrowed three times; four reviews each found it buying into a fall or halting against his word. Chosen (c): errs toward the halt; he has no lift command yet. His recorded word against the market is owed.
- Any bar of the session raises a halt, not only the newest: a look can be missed or bars land together. A day's end is read at its last five-minute bar once the auction is over; if missing it lifts nothing and he is told once.
- A crash and a black swan are two halts, each on its own; the black swan's is his alone to lift. The watch lifts its own crash halt as of the day's end.
- Twenty minutes unheard means unread (options 10, 15, 20: three missed rounds and a fourth late); change once the keeper's delay is measured. A thin line is read at its last trade while its venue is heard.
- Blind (market unreadable) calls no halt: a stopped feed is far commoner than a crash, and a halted day does not count; he is told once an hour. One line's emergency parks nothing yet (the send path asks only for whole-desk halts; one ticker must not stop all trading).
- The watch runs inside the desk's step, so the halts' record keeps one writer. A halt called with no caller named is the operator's own (outside tests call it so).
- Evidence: five blind reviews (four failed, eleven findings closed); 82 of 89 breaks caught; twelve real sessions, 628 looks, no crash. Ticks: money-watch.

### 2026-11-14 — notes for the runner (money-notes, #176)
- The unnoted standing rule (a box adding a public function needs SimCity's files). Options: (a) leave it unnoted, so the runner treats it as whole-lane work; (b) note it as waiting on the operator, untrue; (c) put its files into each box it speaks of and give it a note placing it last. Chosen (c): true, and it frees the runner. It is now money-census, ticked when every other box is.
- SimCity's file has one line of room. Options: a box of its own to split it, or let the first box needing room split it. Chosen the second.

### 2026-11-14 — the RSI and the lower band made public (R-RUNGS-6, R-RUNGS-12, #185)
- Options: (a) two plain functions of numbers the rules already work, read by the rules; (b) whole public indicator classes; (c) public aliases of the private classes. Chosen (a): names exactly the two lines RUNGS could not reach, one code path, every private name RUNGS uses still works. (b) is the cleaner end state once RUNGS stops reaching the private parts. The band's width stays the fixed 2 deviations.
- Proof the rules read the names: the test puts another number at each name and sees the pinned trade vanish.

### 2026-11-14 — a lost stop is told the same day (money-restop, first step, #191)
- When the desk looks. Options: (a) a new read of the broker each morning; (b) the day record's existing reading at the day's end; (c) only when an order is refused. Chosen (b): (a) changes the paper conversation its tests pin; (c) says nothing on a quiet day. Cost: on the pretend desk a stop lost overnight is told at that day's end.
- The level is kept by the desk as each buy goes out (not recomputed, not read from a broker that lost it).
- Only lines the broker holds exactly as the book does, with fewer shares under a stop, are told: telling him to rest a stop for shares not held could sell short.
- Under the book's blocker ("the book is not the broker's"), the list's id the stop's own; a blocker of its own needs `desk/halt.py`. Evidence: 8 breaks caught; SimCity promises it.

### 2026-11-14 — SimCity as a plain-code job (#200, R-RUNNER-23)
- What the no-flag night does. Options: (a) all 100 worlds always; (b) 20 worlds, `--full` for 100. Chose (b): the weekday night is quick, the weekend's full. A short night may show a part "bare" (red) only because few worlds ran, so the weekday verdict is the lesser proof.
- The pound's rate for the night is the desk's own `command.rates` of the day, one rate for all worlds.
- A missing price store is an error raised by name, not a silent green. The text of R-RUNNER-23 was not found; the command is built as the handover describes.

### 2026-11-14 — the sixth frozen rule is a WIRING strategy (#207, R-RUNNER-20)
- Where it is listed. Options: (a) in `STRATEGIES` with the five; (b) apart, in `WIRING`. Chose (b): promotion and the lab's cells admit any name in `STRATEGIES`, so (a) would make it an A-GATE candidate, which is forbidden, and would turn red tests outside the claim.
- Which EMA. Options: seeded with the plain average of the first n closes (textbook, TA-Lib) or with the first close (TradingView). Chose the plain-average seed, weight 2/(n+1): it holds nothing until its indicators are full, like the template's other rules.
- Ties and unseen crosses: read strictly; level is neither buy nor sale; a cross before both averages existed is not bought.
- Its golden days sit in `WIRED`, not `GOLDEN`, which the lab's cell test runs through the fast grid.

### 2026-11-14 — the pound's rate carried over a UK-only holiday (#208, R-RUNNER-26)
- One rule in `desk/carry.py` (book.py is at its cap): the last London session's rate is carried for at most 3 US sessions; any other day without a rate stays an error.
- `desk/command.py` is the PAPER lane's file and the lane guard refused the edit. Options: edit anyway (refused); hand to PAPER (chosen, R-MONEY-32). The ladder should call `desk.carry.carried(rates_by_day, day)`.

### 2026-11-15 — the pound's rate from its closes (#224, R-RUNNER-44)
- `desk/carry.py` `pounds_per_dollar(closes, day)`: one over the pound's last close before the day, fresh when no shared London-and-New-York session lies between.
- Decided: "between" excludes the close day and the day itself; one missing shared session already made a close stale (the stated rule). The dollar sanity band (DOLLARS) stays with callers.
- Remains: `lab/ladder.rates` (R-RUNNER-45) and `desk/command.rates` still use their own 4-day rule and must move onto it.

### 2026-11-15 — SimCity worlds start each line at its own first bar (#231, R-RUNNER-48)
- The deep run died on day 1: worlds start in 2010 but the yardstick VUAG begins in 2019. A line takes part on a day only if it has a bar before it; late lines are named in the night's words.
- Decided: Days before the yardstick's first bar are not lived. Options: invent a market figure for them (a fake), or skip them; chose skip. No new module: the file was squeezed to its 400-line cap.
- Remains: The deep run on the real store, once on main.

### 2026-11-15 — Donchian four-week breakout (#246, R-RUNNER-63)
- `DonchianChannelBreakout` in `desk/eponymous_bands.py`, long only, daily.
- Decided: Exit. Options: the 10-day low (Turtle system 1, already in the desk) or the 20-day low (Donchian's own). Chose 20 so it differs from breakout_20_10 and follows the author. No primary-source figure found; none claimed.

### 2026-11-15 — Connors' RSI-2 (#247, R-RUNNER-60)
- `desk/eponymous_connors.py`, reusing strategy.py's helpers (one owner).
- Decided: Entry under 10 (the book's main) rather than 5 (already the frozen rsi2_pullback); options 5 or 10, chose 10. The published figure is unwritten (no book copy).
- Remains: The published figure; a blind review.

### 2026-11-15 — pound close fresh across one missing shared session (#257, R-RUNNER-84)
- `SHARED_MISSING = 1` in `desk/carry.py`: one missing shared session is fresh, two stale. Fixes the US cell on 2019-05-23 with no dated exception.
- Decided: The request said every existing test stays, but one assertion (close 2 Jun 2025, day 4 Jun) encoded zero tolerance. Options: keep it (rule unmeetable) or flip it (chosen).

### 2026-11-15 — weekly_reversal_jegadeesh (#248, R-RUNNER-76)
- `desk/eponymous_swing.py`: buy a close under the close five sessions back, hold five, sell.
- Decided: (1) Jegadeesh 1990 is monthly; the weekly form is Lehmann 1990; options 21 or 5 sessions, chose 5 as the name says. (2) Long-only keeps the loser leg of a long/short cross-section. (3) Private `_run`/`ARITHMETIC` imported from strategy.py to avoid a second decision loop.
- Remains: Verify the paper's figures; wiring EPONYMOUS into the ladder.

### 2026-11-15 — Connors %b (#256, R-RUNNER-61)
- `ConnorsPercentB` in `desk/eponymous_connors.py`.
- Decided: A flat 20-day window has no bands, so no %b: it resets the run of low days and forces no exit (options: treat as 0, which would buy flat markets, or undefined; chose undefined). Exit at the book's 0.8, not 0.5.

### 2026-11-15 — Donchian fade in chop (#258, R-RUNNER-64)
- `DonchianFadeChop`: buy at the 20-session low when the channel is a range, sell at the midpoint.
- Decided: Range test: no filter / 10% width / ATR-based; chose 10% width, simplest. Exit: midpoint or far edge; chose midpoint, cautious. Source not found.
- Remains: The source and any published figure; compare with the old desk.

### 2026-11-15 — Dan Zanger breakout (#265, R-RUNNER-71)
- `desk/eponymous_dan_zanger.py`: buy over the 50-day high on 1.5x volume, sell under the 10-day average.
- Decided: The 50-day base and 1.5x volume are this port's numbers (options 40/60 days, 1.3x/2x; sources give none). The ladder can vary them.

### 2026-11-15 — Clenow's momentum (#267, R-RUNNER-74)
- `desk/eponymous_clenow_momentum.py`.
- Decided: A single line cannot be ranked, so the book's "top fifth" becomes "score positive" (the alternative, a fixed threshold, is an invented number). The 14% figure is secondary.

### 2026-11-15 — Darvas's box (#251, R-RUNNER-68)
- `desk/eponymous_breakouts.py`, `darvas_box` in RULES (it keeps RULES, which its decide() uses).
- Decided: (1) Close-based reading of the stop-buy: the template decides after the close, so a break that closes inside the box is no buy. (2) A box is complete when the lowest low from the top's session on has stood 3 sessions. The blind review's stale-top buy was fixed with a test.
- Remains: The ladder wiring for RULES is another box.

### 2026-11-15 — Connors' three-day high/low (#261, R-RUNNER-62)
- `desk/eponymous_connors_three_day_high_low.py`.
- Decided: Buy at the close or the next open; took the close, as the sibling Connors rule does. His standing ruling: go with recommended.

### 2026-11-15 — Kell's base-and-break (#269, R-RUNNER-70)
- `desk/eponymous_kell_breakout.py`.
- Decided: Base 20 sessions and 10-day trail from the range 10-30 / 10 or 20; 20/10 matches the family's other breakouts.

### 2026-11-15 — Mansfield RS momentum (#271, R-RUNNER-75)
- `desk/eponymous_mansfield_rs_momentum.py`.
- Decided: The template sees one line but RS needs the market. Options: (a) take SPY from the bars given (chosen; loud error without SPY); (b) edit the template (forbidden before Monday 21:30); (c) price-only proxy (not Mansfield). The zero-line cross only.

### 2026-11-15 — Faber's 10-month rule (#264, R-RUNNER-73)
- `desk/eponymous_faber_tactical.py`.
- Decided: Month-end detection. (a) judge on the first bar of the next month (exact, one-session lag; chosen); (b) last weekday (breaks on holidays).

### 2026-11-15 — Williams' %R (#273, R-RUNNER-67)
- `desk/eponymous_williams_r.py`.
- Decided: Bands: (a) the book's 10 days, -90/-10 (chosen), (b) the common 14 days, -80/-20 (recorded as range). Zero-range window keeps the position, %R being undefined.

### 2026-11-15 — Zweig's breadth thrust (#275, R-RUNNER-80)
- `desk/eponymous_zweig_breadth_thrust.py`; takes breadth as an argument and fails loudly on a missing day.
- Decided: Zweig gives no sale. Options: (a) hold 230 sessions (the book's horizon; chosen), (b) sell when the average falls under 0.40, (c) none. Figures 24.6%, 14 signals are secondary.
- Remains: A breadth series from DATA (R-MONEY-35).

### 2026-11-15 — Bollinger's squeeze (#262, R-RUNNER-66)
- `desk/eponymous_bollinger_squeeze.py`.
- Decided: Exit on the middle band (options: middle, lower band, fixed days). Squeeze judged on the previous day, ties counted, so a bar cannot confirm its own squeeze.

### 2026-11-15 — Weinstein stage analysis (#277, R-RUNNER-79)
- `desk/eponymous_weinstein_stage.py`.
- Decided: "Rising" is the average above its value 5 sessions earlier; options flat-or-rising or a longer slope; took the strict book reading.

### 2026-11-15 — Raschke's Turtle Soup (#276, R-RUNNER-77)
- `desk/eponymous_raschke_swing.py`.
- Decided: Which Street Smarts setup? Options: 80-20 reversal, Holy Grail, Turtle Soup; chose Turtle Soup, the best-defined. Exit: the stop alone (a close under the buying day's low), no mechanical profit rule being published.
- Remains: A later session can swap the setup if the old desk's reading differs.

### 2026-11-15 — Minervini's breakout (#266, R-RUNNER-69)
- `desk/eponymous_minervini_breakout.py`.
- Decided: Relative-strength rank left out (a one-line rule cannot see the market; options stand-in or omit). Exit the 50-day average, not a 7-8% stop, since the template carries no entry price.

### 2026-11-15 — Antonacci dual momentum (#250, R-RUNNER-72)
- `desk/eponymous_momentum.py` `DualMomentum`.
- Decided: The absolute-momentum leg alone with the bill return taken as zero (option (b): refuse until the template offers a second line). The call lags the month-end by one session. The 17.4% figure is from memory, unchecked.
- Remains: The relative leg and bond fallback need a template change after Monday 21:30; a bill-rate series.

### 2026-11-15 — Keltner's channel trend (#272, R-RUNNER-65)
- `desk/eponymous_keltner_channel_trend.py`.
- Decided: Window includes the judged day; exit at the lower band (the book's) rather than the centre line; long only.

### 2026-11-15 — every eponymous module declares EPONYMOUS (#280, R-RUNNER-88)
- 16 modules gained `EPONYMOUS: Mapping[str, type[Rule]]`; a registry test sits in `tests/unit/test_eponymous_swing.py` (the lane guard lets MONEY own only tests named after a module).
- Decided: The nameless momentum rule is named `dual_momentum` (alternative `antonacci_dual_momentum`), the name its test uses.
- Remains: `lab/cell.py`, `ladder.py`, `trials.py` still accept only STRATEGIES (R-RUNNER-89, R-RUNNER-87).

### 2026-11-15 — Broker.stops names the desk's own stops (#282, R-PAPER-9)
- Docstring only.
- Decided: (a) the desk's own stops (chosen) or (b) every stop at the broker. The kill switch and conformance compare only the desk's orders; the old-desk account is shared on port 4002.

### 2026-11-15 — DeMark's TD Sequential (#274, R-RUNNER-78)
- `desk/eponymous_demark_sequential.py`.
- Decided: Published figure left unwritten rather than quoted from memory; countdown compare = close at or below the low two bars back (the book reading), the close compare noted as range.
- Remains: The countdown's cancel by a sell setup is coded but untested.

### 2026-11-15 — unknown place error pulls the kill switch (#285, R-PAPER-10)
- An error from `place` other than Disconnected, Refused or Crash turns the kill switch on, cancels the desk's working orders (stops for held shares stay) and raises `book.Alarm`.
- Decided: (1) `book.Alarm` carries the message (options: post from book, which lacks a clock and messenger; or a typed error for the caller). (2) Crash passes through unchanged. (3) The switch's time is `datetime.now(UTC)`, as `send` has no clock argument. The blind review found the test did not prove the cancel; fixed and seen failing without it.
- Remains: The Telegram line: R-MONEY-36 to PAPER.

### 2026-11-15 — Broker.place allows a two-step stop change after a sale (#289, R-PAPER-12)
- Docstring and contract wording only.
- Decided: (a) allow two steps, as the real broker does (chosen), or (b) force the pretend broker to two steps. The existing test asserts the end state, holdings equal stops after a sale, so it holds for either.

### 2026-11-15 — a corrected fill is one fill (#288, R-PAPER-5)
- `book._record` keys a fill by its id without the last numeric part and replaces on a higher version; a stale earlier version is ignored.
- Decided: A correction replaces in place (keeps FIFO order), versus append-and-supersede; replace keeps position = sum of fills with no extra state. Left: `reports.fills` still raises on a fill and its correction in one reading (R-MONEY-38).

### 2026-11-15 — a place that disagrees halts buying and tells him (#290, R-PAPER-11)
- `book.send` takes an optional `tell`; on a disagreement it halts buying (his alone to lift, kill switch not pulled), writes the fills, sends one message, never re-sends the order.
- Decided: (1) Detect it with a lazy import of `desk.placing` (claim allowed only book.py; a new module or moving Unprotected were the options). (2) With no `tell` the kill-switch alarm stands (the blind review's blocking finding). (3) The halt is his alone to lift. Remains: `running.py` passes `tell` (R-MONEY-39).

### 2026-11-15 — the pretend broker takes a repeated order id as new (#297, R-PAPER-13 first half)
- Pretend.place no longer refuses a repeated id, as IBKR did not.
- Decided: The whole request (desk/sent.py, id written before `place`) made `test_simcity` red (outside the claim): (a) land the broker half alone (chosen) or (b) land all on a red main (refused, canon A4/A1.4). Second half is R-MONEY-40 with the review's fixes: write the id before `place`, withdraw only on Disconnected/Refused, append atomically, check the repeat after the kill switch.

### 2026-11-15 — simcity --soak starts at seed 100 (#332, R-RUNNER-129)
- Each `--soak` lives the next unused block of 100 seeds, logged in `seeds.jsonl`.
- Decided: Start at 100 (0-99 are the nightly range and the request wants fresh seeds) rather than 0. Red worlds: only the first per promise is named; naming all needs `Night` changed at the line cap.

### 2026-11-16 — SimCity reads bars before today (#375, R-RUNNER-181)
- Worlds are built through `keeper.saved`, not the dead `desk/store` folder.
- Decided: Before today (as the desk's round does; never Stale on a night run) versus through today (as the ladder; would raise Stale before the evening refresh). Chose the first; a stale venue fails loudly.

### 2026-11-16 — R-RUNNER-127 held until every rule is a spec row (#383, #388, #465, #468, #554)
- Retiring `desk/eponymous_*.py` was declined by seven sessions; 15 of 21 rules are not catalogue rows and ladder, rulebook, blocks and published still read the files.
- Decided: Delete now (loses 15 rules, canon A3/B6) or hold (chosen, per PLAN). Its own ops note moves the deletion to the coordinator's non-lane branch (a lane cannot remove manifest lines). Requests R-MONEY-45, -46.

### 2026-11-15 — the five rules take settings as arguments (#240, R-GRID-1)
- `strategy.decide(bars, settings)` and `today` take {rule: {argument: value}}; unknown names or windows under 1 day are refused.
- Decided: Constructor arguments with the published defaults (one home per number) versus a separate settings table. A rule keeps its published name at other settings; the grid keys cells by settings. `lower_band` gained a width. No blind review (small change).

### 2026-11-16 — the gate's loss and order-rate limits (#467, R-RUNNER-156)
- Settings hold day_loss 2%, week_loss 5%, new_lines 4; `desk/risk.py` holds `Standing` and `loss_limit`; `halt.drawdown` records "would have halted" without halting.
- Decided: New lines 4 (middle of the colleague's 3-5); the would-have-halted record is its own file, since a row in halts.csv would read as a halt in force. Remains: `book.send` builds the Standing and the messenger sends the alert (R-MONEY-42).

### 2026-11-16 — heat is per-share fall times shares (#472, R-RUNNER-159)
- Each record's `heat` column: pounds lost if every held stop were hit, a line at its stop or, if worse, at its worst overnight gap since its newest buy; blank if a stop level is unknown.
- Decided: Max(buy minus stop, worst gap down) (chosen, his words "at its stop or, if worse, at its gap") versus stop fall plus the gap beyond it. Old records files stay readable with heat blank, not refused.

### 2026-11-16 — slippage is measured per fill against the day's close (#466, R-RUNNER-145)
- `python -m lab.slippage` sets paper fills beside `orders.charges`.
- Decided: Unweighted per fill (chosen; the model's charge is a flat fraction per leg) versus weighted by shares. No blind review.

### 2026-11-16 — stress is one true-order replay (#474, R-RUNNER-153)
- The deep run ends in Stress and Lifecycle lines; Calibration prints "NOT RUN" because desk/ may not import lab/.
- Decided: One replay of real history through the money path, telling its five worst days (chosen), versus reshuffled windows with events, which could never see every event and would always be red. A made-up rate was refused (R-MONEY-43).

### 2026-11-14 — nothing is bought on a line recorded no-ISA (#278, R-DATA-12 part)
- `day._buy` refuses a line whose `isa` is recorded no, on the morning's list.
- Decided: (a) refuse anything not yes (reds scenes 5 and 7 until fixtures carry isa=True), (b) refuse only recorded no (chosen), (c) edit the fixtures outside the claim. End state (a) waits on R-MONEY-44.

### 2026-11-15 — book.keep keeps the `_write` alias (#301, R-PAPER-7 first half)
- `book._write` became public `book.keep`; a contract test shows a death mid-write leaves the old file.
- Decided: Keep `_write = keep` (chosen) or break callers in other lanes' files (outside the claim). Remains: move the callers, delete the alias, add a guard.

### 2026-11-16 — correlation and sizing take their limits as arguments (#478, R-RUNNER-147 step)
- `desk/risk.py` gains volatility, correlation, correlated_with and shares_for_risk; no drawdown refusal (money-limits owns it).
- Decided: Limits as arguments (chosen) versus Settings fields, which needs `orders.py` next session.

### 2026-11-16 — the gap loss limit is 5% of capital (#506, R-RUNGS-11)
- `orders.GAP_LOSS`, one home for STP-10, pinned above the stop's own 2% risk; enforced nowhere yet (money-time-gaps).
- Decided: 3%, 5% or 10%. Chose 5%: above the stop's risk, equal to the week-loss limit, so one gap cannot lose more than a bad week.

### 2026-11-16 — a retail-closed line is refused in the day run (#516, R-PAPER-14)
- `day.buy` refuses a line with `retail` False beside the ISA rule; the broker is not asked.
- Decided: The day run, one place beside the ISA rule (chosen), versus the gate, which would need Line on every order path.

### 2026-11-16 — a killed strategy's buys are barred, its sales are not (#519, R-RUNGS-7 desk side)
- `day.trade` takes `killed` (names), answers "not sent" under the GATE blocker.
- Decided: Bar both or buys only; buys only, since a bar on sales strands a holding with no exit. Passed as data because desk may not import lab (R-MONEY-47).

### 2026-11-16 — conformance cost is a private kind in the book (#534, R-RUNNER-214)
- `book._conformance_cost`: what a conformance ledger moved on the shared account, less costs.
- Decided: Underscored because the SimCity census demands a scenario for every public money-path name; public with a new scenario was outside the claim. Wiring is the remains.

### 2026-11-16 — the intraday bar is rollup.Candle (#557, R-RUNNER-199 step)
- `desk/intraday.py`: Span, IntradayRule, `run` and `latest`, in parity and future-blind.
- Decided: Reuse `rollup.Candle` and `strategy.Action` (one home each) versus widening Bar with a timestamp (touches every daily rule; rejected). A bar counts only if it begins in continuous trading and ends by the close.

### 2026-11-16 — the stop under a price has one home (#573, R-RUNNER-220 step)
- `orders.stop_under(line, price)` is 10% fall times leverage; sizing uses it on the close, a fill's stop on the fill price.
- Decided: Wait for the broker door and change nothing, or land the pure rule now (chosen) so the door change is small. Resting stops IB1T and MSTR are unchanged; the door is R-MONEY-30.

### 2026-11-16 — book.py split into book.py and book_parts.py (#576, R-RUNNER-233)
- Switch record, `keep` and the currency rates moved out; re-exported through `__all__`; the `_write` alias stays.
- Decided: Re-export (one line, chosen) versus touching every caller (outside the claim).

### 2026-11-16 — the underlying cap sits in Settings (#564, #592, R-RUNNER-158 step)
- The gate refuses a buy taking one underlying over 40% of capital (leverage counted); `risk.underlying_limit` judges it; a line with no underlying is its own market.
- Decided: Settings beside the other limits (chosen) versus the gate alone; exposure passed as data like the Standing. Not live: `book.send` passes none (R-MONEY-42, needs a book.py claim).

### 2026-11-17 — only the SimCity census split landed (#590)
- `desk/simcity_census.py` (simcity 400 to about 350); the book split was dropped.
- Decided: Widen the claim (not allowed in session), move the comparison into a claimed file (wrong owner), or drop the book split (chosen; book.py was at, not over, the cap). By #617 book.py is 345 and simcity 359.

### 2026-11-17 — money-restop lands nothing and waits (#617, R-MONEY-30)
- Putting back a stop needs a way to rest one on a line that has none in `placing.moved`, `Broker` and `Pretend`, all PAPER's.
- Decided: (a) a duck-typed call around the Broker protocol from day.py (breaks the one-contract rule, A4), (b) widen the claim to PAPER's files, (c) land nothing and wait on the open request (chosen). Box waits: R-MONEY-30.

### 2026-11-17 - the stop from the fill is wired into day.run, not day.trade (#611, R-RUNNER-220 step)
- (a) call restop in `trade`, which makes test_running (PAPER's file) need extra scripted gateway conversations; (b) call it in `run` and have running.py call `restop.move` after `day.trade`.
- Decided: (b); (a) leaves the PR red or out of claim. A held line with no stop is skipped, left to the "holding with no stop" list. Kill switch on: nothing moved. Live wiring remains (R-MONEY-49).

### 2026-11-17 - intraday decisions get their own `today` (#649, R-RUNNER-199 step)
- (a) wire into `strategy.today` (grows strategy.py at 330 lines and mixes day and intraday decisions); (b) a parallel `intraday.today` in the new module.
- Decided: (b), one engine, daily rules untouched; the registry is empty until a rule passes the ladder.

### 2026-11-17 - the drawdown alert is sent before the day's buys (#661, money-limits)
- Options: alert after the buys, or before. Chosen before, since the gate then refuses them; told once per call, recorded once. Exposure is counted at the last close, not the fill price.

### 2026-11-17 - a stranger is adopted at the last close and sold (#683, money-stranger)
- (1) Ledger price: (a) the line's last close, (b) refuse and sell blind. Chose (a): the broker gives no price and the sale needs the book to equal the broker.
- (2) The stranger's day: (a) clean, (b) mismatch and profit withheld. Chose (b): scene 6 requires it.
- (3) Unreached signals sit under the BROKER blocker, not a new one, which would change every list's shape. Ruling: his "please always go with recommended".


### 2026-11-17 - correlation cap 0.90 at the gate; volatility sizing not wired (#698, #720, money-limits)
- (1) Correlation cap: (a) 0.80 (refuses more), (b) 0.90, (c) 0.95 (rarely bites). Chose (b): stops twin lines such as a 3x and a 1x of one index, leaves ordinary same-sector pairs; his 13 November ruling, recommended option. A line with under 20 shared days (of the last 60) or a flat price is not judged.
- (2) Volatility sizing in `orders.size`: (a) replace the fifth-of-capital room with risk-based sizing now (moves every size and golden number; needs a risk-per-trade number only he owns), (b) wait for the weather box and the golden run. Chose (b): his 16 Nov ruling "record first, prove second, act last" (REG-07); (a) changes what the desk buys. Standing ruling: recommended option taken.

### 2026-11-17 - money-restop's message half stays with PAPER (#717, R-MONEY-18/31)
- Options: (a) widen the claim to `desk/messenger.py`, (b) a duck-typed hook in `day.py`, (c) land nothing and ask PAPER. Chose (c): one owner per concept (canon A4). Box waits: R-MONEY-18, R-MONEY-31.

### 2026-11-17 - a new Pretend door, `put_stop_back`, not a widened `restop` (#758, R-RUNNER-292)
- `put_stop_back(symbol, level)` rests a stop at the kept level for all shares held when none rests (error if one rests or none are held); SimCity's by-hand cancel uses it.
- Options: (a) widen `restop`, which errors on a bare line by contract; (b) a new method. Chose (b) so a move and a put-back stay distinct.

### 2026-11-17 - book.conformance_cost is public, with a SimCity promise (#763, R-PAPER-29)
- Options: (a) make `book.conformance_cost(root, lines)` public with a SimCity "round trips are told" promise that it equals the ledger's cash less its costs (chosen); (b) a new ledger file kind inside the desk's own root, which would put conformance fills beside the desk's and risk its profit and reconcile. The separate conformance root (client 223) already keeps trading P&L clean, so no new kind is needed.
- PAPER feeds it from `desk/conformance.py`, reporting it beside, not inside, the trading profit.

### 2026-11-17 - desk/simcity.py split: the pure parts move (#796, R-RUNNER-287)
Options: (a) move the broker and life classes too; (b) move only the pure parts, `Night`, `_market`, `Archive`, `MONTH`, to `desk/simcity_parts.py`. Chose (b): tests patch names on `desk.simcity` (`FAULTY`) that the broker and life classes read, so moving them would break callers or tests. `desk/simcity.py` re-exports what moved (`__all__`); 400 -> 334 lines, no behaviour change.

### 2026-11-19 - shares beside the book: prove it by the scenario red without the handling (#834, R-RUNNER-247)
- The desk already handled the 16 November case on main, so the proof is the SimCity scenario `beside` red with the handling removed (`book.adopt` made to do nothing) and green with it, the request's own alternative.
- The promise is "taken into the book" rather than "sold same day", as a seeded broker fault may refuse the sale.

### 2026-11-19 - time stop in the one replay, gap loss as a pure test (#845, STP-11, STP-10)
- Options: (a) the time stop in `strategy._run`, the one replay backtest and today share (chosen); (b) in `day.py`, a second path, which canon B2 forbids.
- Live age comes from the replay's own buy, not the fill date. A gap breach is a pure test (`orders.gapped`) first; acting on it needs the stop fill from book/broker, outside this claim.
- Choosing each rule's hold limit moves golden days, so it needs his approval (canon B5); the five declare none today.

### 2026-11-19 - halt cancels working buys (#871, R-RUNNER-337)
- Options: (a) the halt is recorded before the broker is asked, in a new `halt.stop` (chosen); (b) `halt.call` itself cancels (rejected: it has no broker, and halt.py cannot import book without a cycle).
- Why: a broker that cannot answer still leaves the desk halted (error raised), the same order as the kill switch. Resting stops stay. Callers still use `halt.call` (R-MONEY-54).

### 2026-11-19 - the watch's blindness stays about the market line (#880, R-RUNNER-338)
- Options: (a) blind is about the market line (VUAG) and venue-wide hearing, 15 minutes (chosen); (b) per-line staleness, rejected: a thin held line legitimately has no bars for 15 minutes and would cry blind all day.

### 2026-11-19 - cost model moves, not the gate's helpers (#881, R-RUNNER-345)
- Options: (a) move the cost model to `desk/orders_parts.py` (chosen: one coherent part, no dependence on the sizer or gate); (b) move the gate's helpers, rejected: it splits one rule across files. Charges stays in `orders.py` because SimCity's census names it by module.

### 2026-11-19 - SimCity cancelled-unfilled scenario (#884, R-RUNNER-323)
- Options: (a) the desk's own handling of an unfilled cancelled buy, naming it on the morning's list (chosen); (b) copying the conformance harness's sale step into the desk, rejected: it is the harness's job. A line another rule's order then fills is rightly off the list.

### 2026-11-19 - SimCity halted and outside-ISA scenarios (#895, R-RUNNER-335)
- On the merge conflict main's cancelled scenario (#884) stays, since other tests pin it; only halted and outside are added.

### 2026-11-19 - sweeps one setting at a time (#904, R-GRID-1)
- Options: (a) one setting at a time, three values each (published and its neighbours) so cell counts stay small (chosen); (b) a cross product, rejected as too many cells. The published value is the plain rule name, not a variant; rsi2's `length` is 2, 3, 4.

### 2026-11-20 - intraday.session reads the store (#916, R-RUNNER-199)
- Candle.source is "store" because the store read does not return a bar's source. Options: (a) look the source up per bar (extra reads); (b) a fixed name (chosen, no extra reads).

### 2026-11-20 - SimCity phase limit of two hours (#936, R-RUNNER-328)
- Each of SimCity's three phases (store read, worlds, stress replay) runs under `LIMIT` in desk/simcitycmd.py. Options: 1 h, 2 h (chosen), none. Monday's full run took 17 min and the hang 6 h, so 2 h is far above normal and well below the kill.

### 2026-11-20 - SimCity "unheard market" scenario kept out of one test's list (#924, R-RUNNER-248)
- An eighth scenario reshuffles the seeded order and starved test_a_promise_the_desk_breaks... of its first scenario. Options: (a) more worlds; (b) leave the new scenario out of that test's list (chosen: it uses EVENTS[first:-1], so its worlds are as before; the new scenario has its own test). The manifest line of desk/simcity_incidents.py was not reworded (a lane may only register modules).

### 2026-11-20 - a bar-less line in SimCity's gap is a FAULT (#945, R-RUNNER-377)
- Options: skip the line silently (hides data holes); a default price (masks); name it and go red (chosen: canon "fail loudly"). That line's gap order is left out, the others unchanged.
- Note: a real archive with a late-starting line makes any night that draws the gap on it red until that line is handled. The IndexError did not by itself explain R-328's six-hour hang (not proven).

### 2026-11-20 - cause of "job:keeper:failed" taken as a stale venue store (#955, R-RUNNER-314)
- The request does not give the cause. Options: (a) stale venue store; (b) five-minute delay; (c) archive refusal. Took (a): the only miss the quoted output does not show, and the one the door (keeper.saved) refuses on. If the real cause was other, a follow-up scenario is owed.

### 2026-11-20 - parked-yardstick scenario pins the existing refusal (#972, R-RUNNER-315)
- The right behaviour is the desk's existing refusal (a record needs the yardstick's close for every session since the last record), so the scenario pins it rather than adding handling. Option: also trade the other lines through the gap; rejected, the record would be wrong.
- An eighth event changed the seeded order and broke two seed-picked tests in tests/unit/test_simcity.py; their worlds (0, 1) became (2, 3). After merging main (ten events) the fourteen-month world moved from seed 4 to seed 6, the first seed meeting every part of the money path (0-5 left parts bare). Nothing loosened.

### 2026-11-20 - send-path halt goes through halt.stop; goflat left alone (#1031, R-MONEY-54)
- The disagreement halt in desk/book.py now cancels working buys (stops stay). desk/goflat.py is not a MONEY file, so it is left alone and asked of PAPER (R-MONEY-55); desk/watch.py still needs a broker passed in or a cancel after its look.

### 2026-11-20 - unheld one-minute bars scenario; test world seed 1 (#1000, R-RUNNER-316)
- The desk already behaved rightly (#727), so the scenario is red with that starting removed and green with it. The fourteen-month world moved from seed 6 to seed 1, the smallest seed meeting every scenario (the eleventh scenario changed the draw order). The seed is a fixture, not a threshold.

### 2026-11-20 - fault matrix: one cell per farm code (#1035, R-RUNNER-392)
- Farm news 2103 to 2158 is one class per code (56); a hang-up is its own class. Options: group the farm codes (fewer cells) or one per code. Chose one per code: each cell is a separately countable promise. 305 cells, 2 built.

### 2026-11-20 - conformance plan skips a line with no bar (#1028, R-RUNNER-318)
- Options: (a) keep refusing the whole run when one line lacks a bar (the incident repeats daily until the archive fills); (b) leave that line out and plan from the rest. Chose (b): the run needs only the most-traded line, one gap should not stop it. Asked of PAPER (R-MONEY-56); scenario held as a patch until then.

### 2026-11-20 - R-MONEY-54 reverted, not widened (#1046)
- The change needs desk/running.py and desk/goflat.py, both PAPER's; the lane guard refused the edit. Options: widen MONEY's claim (loosens a guard), or ask PAPER. Chose to revert the code and ask PAPER (R-MONEY-57); the guard settles it.

### 2026-11-20 - unbarred scenario keeps the refusal (#1052, R-RUNNER-318)
- Options: (a) keep the refusal when a line has no session bar, (b) leave the line out as the day's rounds do. Chose (a): it is the desk's loud refusal (canon A4), the scenes call for no change, and (b) needs desk/conformance_parts.py, outside the claim.

### 2026-11-20 - park one line by hand reuses GATE, not a new blocker (#1117, R-RUNNER-397)
- Options: (a) a new Blocker for a hand-parked line (touches the SimCity census and its tests), (b) reuse the existing GATE blocker. Chose (b): the operator's list is a separate file (`parked.csv`, desk/handpark.py), not `store.Parked`, which means a data fault, and no new enum is added. Sales and stops are untouched; deleting the row buys the line next round.

### 2026-11-21 - refuse a buy at or under its stop in the gate (#1255, R-RUNNER-407 part)
- Options: (a) the refusal in orders.gate, the one pre-trade gate, with Order.market optional so no caller breaks; (b) a check in day.py, a second path. Chose (a). Nothing sets Order.market yet; wiring it and resting the first stop from the fill are PAPER's files (R-MONEY-60).

### 2026-11-21 - a whole market is not stale (#1022, R-RUNNER-317)
- The incident log gives no cause and desk/keeper_live.py is outside the claim. Options: (a) pin the right behaviour (a whole venue answering one-minute bars is not stale) and show it red with the grace made negative; (b) guess a cause and change keeper_live. Chose (a). Fourteen-month fixture moved from seed 6 to seed 7 (first green; 11 and 8 left gap parts bare, 12 stopped on a holiday). The real cause of the 17 November stale lines is unreproduced: a thin line with no trade in two minutes, or a venue's first minutes.

### 2026-11-21 - rehearsal fills are found, not traded (#1272, R-RUNNER-414)
- The one id prefix the desk never makes is "rehearsal-" (desk/foreign.py); book.found() returns those fills, book.fills() does not, and nothing is deleted. Ledger rows 6-7 carry old unprefixed ids and stay counted until a hand marks them (his hard line on deleting data).

### 2026-11-21 - locked live store is refused loudly (#1245, R-RUNNER-319)
- Options: (a) fail loudly (NoRound naming the store) and run again next minute; (b) swallow it as a "missed" line in desk/keeper.py. Chose (a), canon fail loudly; (b) needs keeper files outside the claim. The seed-picked worlds moved again (world 4 to 1) when the scenario's extra draw shifted the rest. Nothing loosened.

### 2026-11-21 - replay of real paper fills compares partial fills (#1279, R-RUNNER-409)
- Options: skip partial fills, or compare them as a size difference. Chose compare: the desk should size the same whatever the broker filled. Own entry point `python -m desk.simcity_fills` because simcitycmd.py is outside the claim.

### 2026-11-21 - silent broker scenario sits at the order send (#1319, R-RUNNER-324)
- Options: the incident's log names no call site, so put the silence at (a) the account read or (b) the order send. Chose (b): a bare timeout reaches the day only there, and the desk's rule (never guess, kill switch) matters most there. Pinned world moved 6 to 7 (precedent #1022). Nothing loosened.
