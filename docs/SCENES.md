# The scenes — what "working" means

**These need the operator's approval, and change only with it.**

Seven scenes. Together they are one thin path through every part of the desk: data in,
a decision, a size, a stop, an order, a fill, a sale, a reconciled book, a published day.
Each runs on tiny committed fixture data with a fixed clock, so it gives the same answer
on any machine, every time.

They are the scoreboard. "Scenes passing: x of 7" is the only progress number that counts.

---

## Scene 1 — the day's data is clean, or the line is parked

**Given** saved daily bars for the twenty frozen lines, one of them carrying a bad bar
(a price in the wrong unit, a duplicate date and a gap)
**When** the desk prepares for a trading day
**Then** nineteen lines have complete, clean bars up to the last trading day, and the bad
line is parked with a named reason and a date — and the other nineteen still trade.

*Requirements:* DAT-02, DAT-03, DQ-02, DQ-03, DQ-06, DQ-11
*Passes when:* the bad bar is absent from the store, the parked line appears with a reason
and a date, and the nineteen produce decisions in scene 2.

---

## Scene 2 — the decision cannot see the future

**Given** the cleaned bars and the five frozen daily strategies
**When** the desk asks each strategy what to do on a given day
**Then** every line gets a decision, and the decisions for every day up to that day are
identical whether or not the later bars exist at all.

*Requirements:* STR-01, STR-03, STR-04, BT-09
*Passes when:* running the whole history, then running it again with all bars after the
test day deleted, gives the same decisions day for day. This is the one test that catches
a backtest quietly reading tomorrow's price.

---

## Scene 3 — a size and a stop, from one number

**Given** a decision to buy, and one stated amount of money the desk may use
**When** the desk sizes the order
**Then** the size is a whole number of shares, priced in pounds with the currency cost
counted, it never exceeds what the cash allows, and a stop level is set before the order
exists.

*Requirements:* SIZ-01, SIZ-11, STP-01, UNI-09
*Passes when:* the sizer and the send path read the same capital number — proven by
changing that one number and watching both move — and an order with no stop level cannot
be constructed at all.

---

## Scene 4 — the order is sent and the stop rests at the broker

**Given** a sized order with its stop level, and a pretend broker that behaves like the
real one
**When** the desk sends it
**Then** the broker acknowledges, the fill is written down under the broker's own
execution id, and a stop order is left resting at the broker — so it still protects the
position if the desk is switched off.

*Requirements:* TRD-04, TRD-08, STP-02, STP-09, FIL-06
*Passes when:* after a restart mid-send nothing is sent twice; a rejected order, a partial
fill and a disconnection each produce a stated reason, never silence; and every open
position has a resting stop.

---

## Scene 5 — the position is closed

**Given** a position the strategy's own rule now says to sell
**When** the desk runs the next day
**Then** it sells, and the record shows a buy and a sell carrying the broker's own ids,
with the profit or loss after all costs.

*Requirements:* TRD-15, STR-04, NS-05
*Passes when:* a complete round trip exists in the ledger. The first desk ran forty-five
days and never managed one.

---

## Scene 6 — the book is the broker's

**Given** a day's fills
**When** the desk reconciles
**Then** its book matches the broker's positions line by line; and if the broker holds
something different, the day is marked as a mismatch and is never reported as a plain
number.

*Requirements:* TRD-07, TRD-13, NS-06
*Passes when:* a position injected at the broker that the desk does not know about makes
reconciliation fail loudly. The desk's book may never be built from the orders it meant
to send.

---

## Scene 7 — a day that counts, and the same day replayed

**Given** a reconciled day with no halt in force
**When** the desk publishes the day
**Then** the record carries the profit after every cost — commission, spread, slippage,
currency and UK transaction taxes — beside what simply holding the market would have
earned; **and** replaying that same day from the saved data gives an identical record.

*Requirements:* NS-05, NS-06, NS-10, NS-12, BT-04, TST-19, TST-22
*Passes when:* the two records match exactly, a day with a cost line missing is refused,
and ten consecutive days each passing scenes 1 to 7 is FIRST-LIGHT.

---

## What is deliberately not here

These are wanted and come after the scenes pass, not before: the operator's own-account
signals, hourly bars, the market-weather label, shadow books, ratcheting stops,
cross-strategy protective sells, more than twenty lines, and more than five strategies.

Each is a requirement in its own right. None of them holds the gate, because a desk that
cannot complete one honest round trip has nothing to add them to.
