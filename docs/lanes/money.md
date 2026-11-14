# The money lane

The money lane's own decisions, each a dated `###` entry saying what was decided, the
options, why, and the evidence; newest last. Only this lane's scribe writes here, so no
other lane's pull request touches these lines. Held to a size a session reads whole
(`BUDGET.json`, `max_lines_per_lane_doc`): when it is full, the scribe folds the oldest
settled entries into one short summary entry; git keeps every word.

## Decisions

### 2026-11-13 — how the pretend broker behaves

**Decided**, by the lane as the desk's mentor (no one watching), for scene 4 and after:

1. **A buy fills at the opening price of the day the market is open**, for the whole order.
   The desk decides after a day's close and its order meets the next open. Options were the
   open, the close, or the price the order was sized at. The open is what a market order sent
   overnight gets. The close would be a price the desk had not seen when it sent the order.
   The sized price would make every gap free.
2. **A stop is tested on the day of its buy too**, against that day's whole range. Testing
   it only from the next day would let a buy whose market fell through the stop the same
   afternoon escape the loss. That is an optimistic fill, and the desk's measurements must
   err the other way. A day that opens below a stop sells at the open, not at the stop.
3. **One stop per line.** A second buy of a line held adds its shares to the line's one
   stop, at the newest order's level. The book is to give each line one fifth (his ruling
   on sizing), so a line is one holding, with one protection. The other option, a stop per
   order, could leave two levels on one holding.
4. **A fault hits a symbol's first order that meets a market.** An order sent before the
   open, or on a day its line does not trade, is refused with that reason and leaves the
   fault waiting (the blind review's finding: a fault used up on such an order never
   happened at all). A partial fill gets half, rounded down, and the rest is cancelled. A
   dropped connection means the order never reached the broker. A crash means the broker
   has it, and has filled it, but the desk has no answer.
5. **The desk asks before it sends again**, as with Interactive Brokers: the broker answers
   `report(order_id)` with what it did, or nothing if it never received the id. A repeated
   id is refused with a reason, never filled twice, and still counted as received, so
   scene 4 sees a desk that sends twice.
6. **A position planted by hand has no fill and no stop.** The broker reports it among its
   positions only, as a real account shows a hand trade made elsewhere; scene 6 must find it.

**Evidence.** `tests/unit/test_broker.py` failed first on the unbuilt broker. Thirty
deliberate breaks of `desk/broker.py` were each caught. Among them: the order's own id
used as the execution id, no stop left after a fill, a partial fill filling in full or in
silence, a fault outliving its first order, a disconnected order counted as received, a
crash losing the broker's record, a duplicate filling again, a gapped stop selling at its
level, no stop test on the day of the buy, a fill at the close, and a fault spent on no
market.

### 2026-11-13 — the send path: ask first, gate second, a fill written once

**Decided**, by the lane as the desk's mentor (no one watching), for scene 4:

1. **The desk asks the broker before anything else.** If the broker already has the order's
   id, the desk records what it did and sends nothing. Only an order the broker never
   received goes through the pre-trade gate and is sent. The other option, the gate first,
   would judge an order the broker already holds a second time: after a restart with a
   changed capital it could be refused, and its fills, real at the broker, never written.
   Every order the broker receives still passed the gate on the way.
2. **A dropped connection is a stated answer, not a crash.** The order never arrived, so the
   desk says so in the order's reason and the same id may be sent again; the broker answers
   for it then. A crash after the broker has the order is the desk dying: it stops, and the
   next ask records what the broker did.
3. **The ledger is one file of fills, keyed by the broker's execution id**, written whole and
   swapped in, as the price store is, so a desk that dies mid-write keeps the old one. A
   fill already written is never written again, so asking about an order twice is harmless.
4. **The ledger learns only what the send path is told.** A stop the broker sells overnight is
   not in any order's answer; the book built from the broker (the next step) and the day run
   must collect it, or the ledger and the broker's fills part company.

**Evidence.** `tests/unit/test_book.py` failed first on the unbuilt send path; scene 4 now
passes. Eleven deliberate breaks of `desk/book.py` were each caught: never asking the
broker first, gating an order the broker already had (the blind review's one gap), skipping the gate, letting a dropped connection escape, not recording, recording a
fill twice, overwriting the ledger, counting the order's shares as filled, dropping a
reason, a silent disconnection, and a price read back rounded.

### 2026-11-13 — the book: the ledger's fills, read by the gate

**Decided**, by the lane as the desk's mentor (no one watching), for the gate and scene 5:

1. **The book is the ledger's fills added up, line by line.** Never the orders meant, and
   never the broker's own positions: the book is what the desk itself knows, so scene 6 can
   compare the two. A position bought by hand at the broker is not in the book; finding it
   is reconciliation's job, not the gate's.
2. **The send path brings the ledger up to date before the gate looks.** It writes every
   fill the broker made that the ledger lacks (`book.collect`), so a stop sold overnight,
   which is in no order's answer, frees its holding before the next buy is judged. The
   other option, leaving that to the day run, would let a caller that forgot judge a buy
   against a book that still holds the stopped line.
3. **A line's shares, held and ordered, are counted together at the order's price and
   rate** against its one fifth. Options were the price paid, or today's price. Today's is
   what the line is worth now, which is the risk the fifth limits; the price paid would
   also need each fill's exchange rate, which the ledger does not keep. So a line that has
   risen leaves less room for a second buy, and one that has fallen leaves more.
4. **A sixth line is refused; a second buy of a held line is not a new holding.** The
   sizer gives a second buy what is left of the fifth and passes it through the same gate,
   so the rule lives in one place.
5. **A ledger that sells more of a line than it bought is refused loudly**: the desk is long
   only, so such a ledger is broken, and the book says which line.

**Evidence.** `tests/unit/test_book.py` and `tests/unit/test_orders.py` failed first on the
unbuilt book and the one-holding gate. Fifteen deliberate breaks were each caught: no
collect before the gate, an empty book given to the gate, collect writing nothing, the
book counting buys only, a line sold out still counted, the long-only check removed, sales
counted as buys, the five-holding check removed or off by one, a held line counted as a new
holding, held shares ignored or counted twice, the sizer not subtracting what is held, the
sizer skipping the gate, and a full line sized to no shares. A blind review found nothing
blocking: its fix (a stop sold on its buy's own day reached the book only on the next send)
and its test gap (a crashed order's fill must count as a holding) are taken, the second
driven by removing the first collect.

### 2026-11-13 — the day run: whose position, which day, which rate

**Decided**, by the lane as the desk's mentor (no one watching), for scene 5 and after:

1. **A rule's position is the book's, not its own idea.** Options were (a) each rule
   counting its own buys and sells as done, the book only refusing what it cannot do, or
   (b) each rule told, on the day it decides, whether the book holds the line for it. (a)
   leaves a rule whose buy was refused, or whose stop sold, believing it holds: it will not
   buy again while its condition lasts and later says sell to a flat book. Chosen (b)
   (`strategy.today`). The rules' indicators do not depend on what they hold, so the same
   history gives the same bands either way.
2. **A line is one holding, owned by the strategy whose buy opened it** (the strategy in its
   latest buy's order id). Only that strategy's sell sells it, and it sells the whole of
   what the book holds. While a line is held, the other four rules' signals on it are not
   acted on. Of several rules buying one flat line the same day, the first in the
   operator's list of five buys it. The other option, a position per rule within the
   line's fifth, needs a stop per rule, which the broker's one stop a line (decided above)
   does not give.
3. **Sales first, then buys, each sized from the book after the send before it.** A sixth
   line is refused by the gate and kept among the day's answers with its reason, never
   dropped. A line sold that morning, by its rule or by its stop, is not bought again the
   same day: its stop was judged against the whole day before the new order, and could
   sell it twice on one bar.
4. **Only decisions dated the line's venue's session before the day are acted on**, and
   only on a day its venue trades. A line whose bars stop earlier is left alone that day.
5. **The day run is given the day's pounds per unit of each currency, and keeps it**
   (`rates.csv` beside the ledger). Each fill is now dated by the broker, so a round trip
   prices each leg at its own day's kept rate. Options were a rate in the fill (the broker
   does not report one), one rate for the whole run (wrong for a trip that spans a move in
   the pound), or looking it up again later (not the rate of the day). The scenes give 0.79
   every day; a daily rate in the store is asked of the data lane.
6. **A round trip pairs each sale with the buys it closes, oldest first**; a fill split
   between trips shares its commission and conversion by its shares. Spread, slippage and
   UK tax are not yet charged: they belong to the day record (scene 7), where the spread
   and slippage of both legs, the stop's sale included, must be added.
7. **Scene 5 runs on the rehearsal's whole fourteen months** now, since no rule trades in
   the six weeks the other scenes still see. When the data lane moves the scenes onto the
   whole history, scene 5 reads the same data as the others.
8. **Scene 2 counts each line against its own venue's calendar** over the scenes' days:
   five decisions for every session the line's venue traded. Counting each line's own
   bars, the first form tried, could not fail (the blind review's finding).

**Evidence.** The new tests in `test_day`, `test_book`, `test_broker`, `test_orders` and
`test_strategy` failed first on the unbuilt code; scene 5 failed on the six weeks and passes
on the fourteen months. Twenty-five deliberate breaks were driven. Twenty-two were caught at
once: the open's stops not collected, buys sized from a stale book, a line sold that morning
bought again, a stale decision acted on, the book's holding not given to the rules, a sale
leaving its stop or taking all of it, a sale at the close, the gate letting one share too
many be sold, conversion on a pound line or on the wrong amount, a split fill's charges not
shared or its rest forgotten, the wrong day's rate, a sale counted as negative shares, a
fill's day moved, a missing rate not refused, a kept rate repriced, a zero rate, and a line
missing a day in scene 2. One, a pound rate other than 1, was missed because its test met
the "already kept" refusal first; the test now uses a fresh day and catches it. Two were
missed because the code did nothing (an owner check `strategy.today` already makes, and a
filter whose result was overwritten); both are removed.

### 2026-11-13 — reconciliation: before every order, shares and stops; and scenes 6 and 7 together

**Decided**, by the lane as the desk's mentor (no one watching):

1. **The book is checked against the broker's on the send path, before every order**
   (`book.reconcile`, called by `book.send`). Options were (a) once, in the day run after
   the open; (b) on the send path, the one door every order already passes. Chosen (b): a
   hand trade made in the middle of a morning is seen before the next order, and any later
   caller of the send path (the paper lane's) is held by it without being told to. It stays
   out of `orders.gate`, which is pure and is also the rungs lane's; the refusal is the
   same `Refused` the gate raises.
2. **A line differs when its shares differ, or when the stop resting at the broker is not
   for exactly the shares the book holds.** Every share the desk holds has its stop at the
   broker; a holding whose stop was cancelled is the most dangerous quiet state there is,
   so it is named like a wrong position. Shares alone, the scene's own words, would miss it.
3. **While any line differs the desk buys nothing; it sells a line only if that line's
   shares agree.** Options were (a) send nothing at all; (b) stop buying only; (c) stop
   buying, and never sell a line whose shares differ. (a) would hold a rule's sale of a
   sound line for as long as a person takes to look. (b) would sell the book's ten shares
   of a line of which the broker holds four, and leave the desk short. Chosen (c), with the
   blind review's point taken: a line whose shares agree but whose stop is gone may be
   sold, since that is the protective act. Nothing is remembered from day to day: the two
   books are compared afresh each time, and buying starts again once they agree.
4. **The day does not stop.** A refusal on the send path becomes that order's answer, with
   its reason naming the lines, kept with the day's others. The desk dying, or any other
   error, still stops the day.
5. **An order the broker already has is recorded, never refused**, whatever the books say:
   the broker is asked first, as before.
6. **Scenes 6 and 7 pass together.** The plan had reconciliation turn scene 6 by itself. It
   cannot: scene 6 asks that a reconciled day carry a profit, scene 7 reads the same
   record, and a profit is not published without every cost (canon B4). Spread, slippage
   and a sale's own cost are not in the cost model, and UK tax needs a fact on each line
   that the data lane owns. Options were (a) give scene 6 a record with the missing costs
   at nought; (b) take "a reconciled day has a number" out of scene 6; (c) land
   reconciliation under its own contract tests and turn both scenes when the record is
   real. (a) is a made-up number and (b) weakens a scene to count it. Chosen (c). The
   scenes stay at 5 of 7 for this step; the lane's book says what remains.
7. **Scene 6's days.** No rule holds a position at the end of the rehearsal data, on its
   six weeks or its fourteen months, so "the broker holds something" cannot be read after
   the last day. When the record lands, scene 6 will run the fourteen months and set the
   book against the broker's on every day, which asks more of the desk, not less.
8. **The kill switch is the lane's next objective, ahead of the costs.** His ruling of the
   same day, which reached this branch as it was finishing, puts the kill switch first and
   holds the paper lane's orders until it is drilled. Options were the costs next, as the
   scenes' order suggests, or the kill switch next. Chosen the kill switch: it is his word,
   another lane waits on it, and scenes 6 and 7 wait on the data lane's tax fact in any
   case, so the scenes lose nothing by it.

**Evidence.** Two contract tests seen failing first (`book.reconcile` did not exist; the day
sent five buys with a hand-bought line at the broker). Over the fourteen months, with and
without every line's first order rejected, the desk made the same 68 fills and 34 round
trips as before the change: in ordinary running the two books never differ. Thirty-one
deliberate breaks were driven first; twenty-six were caught and five missed, each a gap in
the tests: a line only the book holds, the names in no order, an order the broker already
has refused while the books differ, any error at all kept as an answer, and a cancelled
stop that also emptied the position. Tests were added for each. Thirteen more were then
driven, those five and eight against the review's fix; twelve were caught at once and the
thirteenth (a sale allowed when the broker holds more than the book) after its test was
tightened. The blind review, which ran 400 random runs of its own (20,907 orders, every
fault) without one false mismatch, found nothing blocking; what it left is in
`docs/STATUS.md`.

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
