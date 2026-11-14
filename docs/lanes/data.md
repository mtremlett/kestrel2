# The data lane

The data lane's own decisions, each a dated `###` entry saying what was decided, the
options, why, and the evidence; newest last. Only this lane's scribe writes here, so no
other lane's pull request touches these lines. Held to a size a session reads whole
(`BUDGET.json`, `max_lines_per_lane_doc`): when it is full, the scribe folds the oldest
settled entries into one short summary entry; git keeps every word.

## Decisions

### 2026-11-13 — the fourteen months are built; the scenes move onto them in two steps

**Found.** On their own calendars, a London line and a US line do not trade the same days
over fourteen months (Easter Monday, Thanksgiving, the 4th of July and eight more), so
there is no longer one list of days that every line shares. Scene 2 counts its decisions
as five rules times nineteen lines times one list of days; at full length that count is
wrong by design, and scene 2 goes red (driven: 28,925 decisions against 29,545 expected),
though not one decision is missing. Scenes 1 and 3 pass at full length. Scene 2 is the
money lane's file, which this lane may not edit.

**Options.** (a) Give every line the same days, holidays ignored: the store rightly refuses
a bar on a closed day, so the clean lines would park and scene 1 would break. (b) Choose
windows so the two venues happen to have equal counts: a trick to fit one assertion.
(c) Edit scene 2's count from this lane: against the lanes' ownership rule. (d) Build the
fourteen months now, let the scenes keep seeing its last six weeks (which hold no holiday
on either venue), and move them onto the whole of it with a one-line change once scene 2
counts each line's own days.

**Chosen.** (d). The data is in one place, its last six weeks in use; nothing is duplicated; main stays
green; the move is one constant (`SCENES_FROM` in `tests/scenes/rehearsal.py`).

**Evidence**, from a script run outside the repository on the whole fourteen months:
London lines trade 307 sessions and US lines 303, on each venue's own calendar; the store
keeps every clean line whole with no fault, and parks only the spoilt line, for its three
faults (now placed among its last sixty sessions). Each of the five rules buys and sells
on every one of the nineteen clean lines: RSI-2 19 round trips, Bollinger 38, the 20/10
breakout 38, the 50/200 cross 19, Supertrend 57. Deliberate breaks: a London line laid on
US days is refused for 25 August 2025 (a UK bank holiday) and parked for the missing 1
September; a plain weekday calendar faults Christmas, Boxing Day and New Year in London,
and Labor Day and Thanksgiving in the US. The first shape tried, a two-day dip, gave RSI-2
a trade on only 11 lines; a three-day dip gives it all nineteen.

**The cost.** Until the move, the scenes still run on six weeks in which no rule trades.
Scene 2's future-blind loop over all 311 days will take about twenty seconds where it now
takes one; the money lane may cut on fewer days.

### 2026-11-13 — which archive failures park one line, and which stop the fetch

**The question.** When the free archive fails for one line, should the whole morning's fetch stop, or only that line park?

**Options.** (a) Stop everything on any failure: one flaky line would keep all twenty from trading. (b) Park a line on any error at all: a fault in the desk's own code would be hidden as a parked line. (c) Park a line for a failure of the network or of the archive's answer - a dropped connection, a half-delivered answer, a timeout, a missing page, an answer that is not the line asked about or not in its currency - and stop everything for anything else, such as an answer of a shape the desk does not know, which would hit every line alike.

**Chosen.** (c). It is what the north star needs: the clean lines still trade on a morning one line fails, and a fault of the desk is never mistaken for the archive's. The reason is kept with the error's name (a timeout carries no message of its own). A refused line keeps no bars in the store, so nothing from an earlier day can be read as today's.

**Evidence.** Tests seen failing first. Six deliberate breaks, each caught: no handling at all; the answer's refusals not handled; every error handled; old bars left in place; the refusal dated too long ago to park; its reason dropped. A blind review found that a half-delivered answer (`IncompleteRead`) still stopped everything; it was made a failing test and fixed.

### 2026-11-13 — what a frozen feed is, and what the store does with one

**The question.** The archive can go on sending yesterday's bar as if it were today's. How many days of one repeated price make a frozen feed, which bars count, and what becomes of them?

**Options.** (a) Any single day of one price and no volume: thin London lines have such days often (2MU has 441 days with no volume since 2010), so this would park real lines. (b) A run of three: 2MU really has runs of three. (c) A run of five sessions, a trading week, each bar repeating the one before it (its volume too, or with none) or flat at its close with nothing traded; a flat day that traded stays a market. Its bars dropped as untrue and listed, the fault dated by the run's last day, so a run reaching the last sixty sessions parks the line, as any recent fault does.

**Chosen.** (c). It is what the north star needs: the desk never decides on a price the market did not make, and no line that trades is parked for being quiet. A week with no trade at all is also reason enough not to trade a line. Dropping, not keeping, the bars: kept, they would hand the strategies a calm week that never happened. Whether the archive or the market went quiet, the line waits until a real price arrives.

**Evidence.** The twenty lines from the archive on 13 November: the longest real run is three sessions (2MU, December 2022); after the rule the same four lines park, for their old reasons, and no clean line has a frozen fault. Tests seen failing first. Nine deliberate breaks, each caught: the run made four and six; a traded repeat counted; a flat traded day counted; each kind of repeat removed; a whole repeat with volume let through; the rule switched off; the bars kept. A tenth, dating the fault by the run's first day, cannot change an outcome: the dropped days are also missing sessions, which park the line on their own. A blind review found nothing blocking; its point that a whole repeat, volume too, is a frozen feed was taken; its other points are in `docs/STATUS.md`.

### 2026-11-13 — a suspension is recorded on the line, as a real move is

**The question.** The archive leaves out a day a line did not trade because it was
suspended. The store cannot tell that from a day the archive lost, and parks the line for
sixty sessions. What should a missing session do?

**Options.** (a) Leave it: any missing recent session parks, with no way back out but
waiting sixty sessions. (b) Let a short hole in the middle pass, parking only when the
newest session is missing: a day the archive lost would then be traded through unnoticed,
a default that masks missing data. (c) Record a confirmed suspension on the line in the
instrument master, as a real move is (`Line.suspended`): the store expects no bar that day,
so its absence parks nothing; an unrecorded gap still parks, its reason naming the way out;
a bar the archive gives on a recorded day is refused, for the record and the archive
disagree; a day the venue did not trade cannot be recorded.

**Chosen.** (c). It is what the north star needs: the desk never trades on a history with
an unexplained hole, and a line suspended for a day comes back as soon as the fact is
recorded, not three months later. Facts about a line come from the instrument master. None
of the twenty has a suspension recorded today; none is parked for a gap.

**Evidence.** Tests seen failing first. Four deliberate breaks, each caught: the record
ignored; a bar on a recorded day let in; the reason naming no way out; any day allowed in
the record.

### 2026-11-13 — a one-day crash is kept; only a hundredfold bar is a wrong unit

**The question.** A single day out of line with the days either side was dropped as "a wrong
unit", at any size. On the real archive that dropped 5QQQ's crash of 7 April 2025: a five-times
line down 40% at its low, half of it won back the next day. Which single days may the store
throw away?

**Options.** (a) Leave it: a real crash vanishes from the history, so every test of a rule on
that history looks safer than the market was. (b) Keep an old one and list it, park only a
recent one: a bad print would then stay in the history unparked, as a crash that never was.
(c) Drop a day only when a price sits a hundredfold out of its neighbour (pence among pounds,
the one fault price alone proves), the rule a run of days already followed; keep any other
move and record it as a lasting fault, which parks however old until each close is recorded
on the line (`Line.real_moves`), as a step in the price already did.

**Chosen.** (c). It is what the north star needs: the desk neither forgets a loss the market
really dealt nor trades on a history holding a move nobody has confirmed. One rule now
decides for a single day and for a run. The cost: a bad print of another size, say a tenth,
parks its line until someone looks; no line is parked by it today.

**Evidence.** The twenty lines from the archive on 13 November: before, 5QQQ's 7 April 2025
was dropped as a wrong unit; after, it is kept, its fall and its recovery listed as moves to
record; the same four lines park, and no clean line has a new fault. Tests seen failing first:
a 60% one-day fall, at the first bar, an old one, a recent one and the newest, each kept and
parking, and each back out once its closes are recorded. Seven deliberate breaks, each
caught: the size test removed, made always true, always false, made to read the close alone,
its margin widened, its margin made a single jump, the wrong neighbour measured. A blind
review found nothing blocking; its one finding of the same kind - a crash straight after
days in the wrong unit was dropped with them - was made a failing test and fixed: a run in
the wrong unit now ends at the first day back in the right one. Its other points are in
`docs/STATUS.md`.

### 2026-11-13 — the research list: what is on it, where it lives, and what a refusal does

**The questions.** His ruling named four lists and "about 1,500" tickers, kept apart from
the twenty trading lines, nothing on it traded. Building it raised six questions of intended
behaviour.

**1. How many.** The four lists, as published on 13 November, hold 503, 101, 350 and 200
names, and overlap (86 of the Nasdaq 100 are in the S&P 500). Options: (a) the lists
as ruled, each ticker once: 1,065; (b) pad to 1,500 with names from no list he chose.
**Chosen (a):** the lists are the ruling and the number was an estimate of them. The full
universe of 5,000 and more is already the plan's next size.

**2. Where it lives.** Options: (a) in the instrument master beside the twenty, marked "not
traded": one wrong flag and the desk trades a research ticker; (b) a module in `desk/`;
(c) a module in `lab/`, which `desk/` may never import (the wall guard). **Chosen (c):**
"nothing on it is traded" is then held by the wall, not by a flag. Ten of its tickers are
also trading lines; for those the list hands out the master's own line, so a fact recorded
there (a real move, a suspension) has one home, and a disagreement between the two refuses
to load.

**3. One store folder for each venue.** Thirteen symbols are two companies (BA is Boeing in
New York and BAE Systems in London), and the store names a file by its symbol. Options:
(a) rename one of each pair; (b) change the store's file names, the money lane's reader with
them; (c) keep each venue's tickers in its own folder, the store unchanged. **Chosen (c).**
A parked ticker is returned by its line, which carries its venue, never by symbol alone.

**4. Which funds.** No free, published list of US funds by value traded was found. Options:
(a) a list from memory; (b) a field of 330 well-known funds drawn up by the session, each
fetched from the archive and ranked by its median value traded a day over the sixty sessions
to 12 November, the top 200 taken. **Chosen (b):** the cut is measured, and repeatable. The
200th trades about 87 million dollars a day. Left out of the field: funds that move against
their market (a line's leverage is one or more), funds whose multiple has changed (their
history is on two scales), single-share funds and volatility trackers. Ten funds built to
make two or three times their market's move are in, each with its multiple.

**5. Shares London does not quote in pounds.** The archive refused eight FTSE 350 members
as "not GBP". Five are quoted in dollars and are recorded so, and come back clean. Three
(BCG, MTLN, PEY) are quoted in euros; a line is in pounds or dollars. Options: (a) record
them in pounds, knowingly false, and let them park every day; (b) teach every line euros,
which reaches the money lane's sizing and conversion; (c) leave the three off and say so.
**Chosen (c)**, until research needs them.

**6. A ticker the archive refuses for a day.** The blind review's finding: a throttled or
timed-out answer empties that ticker's file, sixteen years of bars, until the next run.
Options: (a) leave the old bars in place for a refused ticker: yesterday's data would then
read as today's, the fault the desk's store was built to refuse, and the research store
would follow a second rule; (b) stop the whole run at the first refusal: one bad ticker
would cost the other thousand; (c) one rule for every store: a ticker refused today holds
no bars today and is parked with the reason, and the next run, ten minutes, restores it.
**Chosen (c).** A cell on an emptied ticker fails loudly and is retried; nothing stale is
ever studied. It is now a test.

**Evidence.** Membership read from the published pages of the four lists (the S&P 500, the
Nasdaq 100 as of 22 October, the FTSE 100 after 1 October and the FTSE 250 after 20 October
2026). `universe.keep` driven on the real archive for 13 November by a script outside the
repository: every one of the 1,065 answered; 4,097,609 bars; 249 tickers begin after January
2010; 864 clean (625 of 718 US, 239 of 347 London) and 201 parked, each for a one-day move
beyond the store's belief that its line does not record: 406 moves, 31 tickers on the flash
crash of 6 May 2010, 46 in March 2020, 10 on the day after the Brexit vote. Tests seen
failing first. Thirty-one deliberate breaks: twenty-eight caught at once (every venue in one
folder, the parked dropped, a refused ticker's old bars left in place, a list left out, a
multiple changed or lost, a ticker added or removed, and more); two caught once their tests
were added (the master looked up by symbol alone; the two allowed to disagree on currency);
the last, two tickers swapped in order, changes nothing. A blind review found two things
blocking: a parked ticker did not say which venue it was on (fixed: parked by line), and
question 6 (decided, and tested). Its other points are fixed (wording, a silent default for
a missing multiple, the master silently winning a disagreement, eight London currencies) or
listed in `docs/STATUS.md`.

### 2026-11-13 — a line's UK tax: two rates, a fact on the line, and how far each is confirmed

**The questions.** The money lane asked (R-MONEY-1) for what a purchase pays in UK
transaction tax as a fact on each line, the ten London lines confirmed, and one London line
of the rehearsal data that pays it. This entry replaces the sentence above, under the costs,
that the tax "is to be confirmed line by line". Five questions of intended behaviour.

**1. What the fact is.** Options: (a) a kind on the line (share, fund, product) from which
the cost model works out the tax; (b) the rate itself on the line, taken from one table of
rates in the instrument master. **Chosen (b).** The tax does not follow the kind: a share
of a company registered abroad can pay none. The cost model needs a number, and a kind
would be a second fact to keep true. The table has two rates, nil and a UK share's half of
one per cent (`lines.NO_TAX`, `lines.STAMP_DUTY`); a line can state only one of them, and
only a London line can pay, so a wrong figure or a taxed US line cannot be made. A sale pays
none.

**2. A line made without it.** Leverage cannot be left out of a line. Options: (a) the
same for the tax: about thirty lines built in the money and paper lanes' tests would stop
working, in files this lane may not edit, and main would be red; (b) nil when not stated,
for good; (c) nil when not stated for now, every real list stating it, and the other lanes
asked to state it in their tests so the default can go. **Chosen (c)** (R-DATA-4,
R-DATA-5). Until then a UK share built by hand from four facts pays nothing, which is the
risk; no list the desk or research reads is built that way.

**3. The ten London lines: nil, and how far confirmed.** As the session knows them:

| line | what it is | why nil | confirmed |
|---|---|---|---|
| SMGB | VanEck Semiconductor fund, Irish | exchange-traded funds are exempt | yes |
| IITU | iShares S&P 500 technology fund, Irish | the same | yes |
| VHYG | Vanguard world high-dividend fund, Irish | the same | yes |
| ISF | iShares FTSE 100 fund, Irish | the same | yes |
| VUSA | Vanguard S&P 500 fund, Irish | the same | yes |
| 3LGO | WisdomTree three-times gold product, debt of an Irish issuer | not a UK company's security | as the law reads |
| 2MU | Leverage Shares two-times Micron product, debt of an Irish issuer | the same | as the law reads |
| 5QQQ | Leverage Shares five-times Nasdaq product, debt of an Irish issuer | the same | as the law reads |
| IB1T | iShares Bitcoin product, debt of a Swiss issuer | the same | as the law reads |
| SGLN | iShares physical gold product, debt of an Irish issuer | the same | as the law reads |

The funds: the Stamp Duty and Stamp Duty Reserve Tax (Exchange Traded Funds) (Exemption)
Regulations 2014 (SI 2014/911), read in the tax office's manual (STSM101065) on 13 November
2026; interactive investor's and Freetrade's pages say the same. The products are not funds,
so those regulations do not name them. Stamp duty reserve tax falls on a UK company's
securities, or ones kept on a UK register, and these are debt of companies outside the UK;
brokers charge none. But no official page or issuer's document saying so of these five was
reached: the prospectuses could not be fetched, and the brokers' cost pages for IB1T do not
mention the tax. Options: (a) nil, recorded as not officially confirmed; (b) half a per
cent until confirmed, most likely false, and it would make the leveraged lines look worse
than they are; (c) stop and ask the operator. **Chosen (a):** it is the best reading, a
mistake costs half a per cent of a purchase on paper only, and it is settled by any real
contract note or by the order preview at his own broker. If one pays, one word on its line
changes.

**4. The research list's London shares.** Options: (a) leave them at nil: 347 UK shares
would be studied free of a tax nearly all of them pay; (b) charge each a UK share's stamp
duty, knowing a minority registered abroad pay none and three or so registered in Ireland
pay 1%; (c) check all 347 this session. **Chosen (b):** it is right for most, errs toward
too much cost for most of the rest, and the exceptions the blind review named from memory
are listed in `docs/STATUS.md` to be checked name by name. Ireland's 1% is a third rate, to
be added to the table when a line needs it.

**5. Which rehearsal line pays.** L01, a London line the rules buy: three times over the
fourteen months (2 October 2024, 22 April and 16 June 2025), £29.66 of stamp duty in all at
the fills' prices. In the six weeks the scenes see today nothing is bought, so the tax is
charged there only once the scenes move (R-MONEY-2).

**Not in the fact:** rounding (the tax office collects to the penny; the day record's one
rounding policy), and the takeover panel's flat levy on a trade over £10,000 in a UK
company's shares, which no trade of £2,000 reaches.

**Evidence.** Tests seen failing first: a line accepted any tax, the research list's London
shares paid nil, and a disagreement with the master on tax went unseen. A script outside the
repository ran the day's trading over the fourteen months before and after: the same buys,
and stamp duty of nil, then £29.66. Seventeen deliberate breaks, driven by a helper with
the Python cache off: fifteen caught (a rate changed, the default changed, each refusal
removed, the twenty lines or the research list given the wrong rate, the disagreement check
blinded); one changes nothing (the twenty lines built without stating the tax, which is the
default of question 2); one no test can see yet (the rehearsal line's tax removed: nothing
reads it until the money lane builds the day's record, and scene 7 will then need it). A
blind review found two things blocking, both wording that claimed more than was proven:
"each confirmed" before this entry existed and beyond what was found for the five products,
and the research list's shares stated as plain fact. Both are reworded and recorded here
and in `docs/STATUS.md`; its other points are taken (a London share quoted in dollars
tested, the default recorded and asked away) or listed there.

### 2026-11-13 — the scenes on the whole fourteen months (R-MONEY-2), and the status cut

The money lane asked (R-MONEY-2, blocking) for the scenes to see all fourteen months of the
rehearsal data: scene 2 already counts each line against its own venue's calendar, and
scene 7 needs days on which the rules trade; none trades in the last six weeks.

**1. Widen the window, or remove it.** Options: (a) set the window's start back to the
first day, one constant, leaving a filter that filters nothing; (b) remove the window, so
the rehearsal data is one thing under one name. **Chosen (b):** less code, and no second
view of the data to drift. `HISTORY`, scene 5's name for the whole of it, stays for now as
a second name for `CLEAN`, because the scenes' file is the money lane's; asked away as
R-DATA-6.

**2. The cost in time.** Scene 2 deletes the later bars at every one of 311 days, not 33:
it takes about 24 seconds, and the scenes step about 47, from 23. Options: (a) accept it;
(b) keep scene 2 alone on a short window. **Chosen (a):** the check stays under two
minutes, and a short window is exactly what hid holidays and trading days from the scenes.
Scenes 6 and 7 will add the day run over the same months, about 24 seconds each (the money
lane's note that the day run decides each line's whole history again every day).

**3. The scenes' days** (`SESSIONS`) are now every day either venue trades, 311 of them:
some are one venue's holiday (Thanksgiving, the UK's bank holidays). Scene 5 already runs
the day's trading over exactly those days and passes; scenes 6 and 7 will meet them too.

**4. The status cut.** By the operator's rule against document bloat the data lane's
section of `docs/STATUS.md` went from 286 lines to 50, in a commit of its own: what is done
was removed (git keeps it, and the book in `docs/PLAN.md` holds each open step), and each
open finding, request and requirement id kept in a line or two.

**Evidence.** Scenes 1 to 5 pass on the fourteen months; 6 and 7 stop, as before, at the
day's record, which is not built. Two deliberate breaks, the Python cache off: every line
laid on London's calendar (scenes 1 and 2 fail), and the data cut back to six weeks (scene 5
fails). No test fails yet if the rehearsal's taxed line (L01) lost its stamp duty: scene 7
will be that test.

**The blind review** found nothing blocking: no scene proves less than before (the spoilt
line's three faults still fall in its last sixty sessions; scene 2 now truly counts two
calendars, eight days only London trades and four only the US), and the second name does no
harm. It ran the day's trading itself with no faults: L01 is bought three times and US
lines are bought, so scene 7's tax and currency costs can be charged, and no fill lands on
a day only one venue trades. Two things it left for the money lane's day record, neither
new: every rule is out of the market by the data's end, so scene 6 as written cannot find a
holding (the money lane's own note of 13 November); and the scenes' first day, 2 September
2024, is the US Labor Day, so the US lines have no bar until the day after.

### 2026-11-13 — research reads the parked fifth by a rule of its own (#80)

**How research reads a ticker the store parks for an unconfirmed move.** Options: (a) leave the
parked fifth out: research loses its most violent names, the ones a leveraged trend strategy lives
on, and every result flatters; (b) read them as they are: a series that jumps a hundredfold (CLDN) or
to a tenth is priced as a gain or loss nobody had; (c) confirm all 406 moves from a second source:
there is none yet; (d) break the history at every unconfirmed move: the crashes of March 2020 and
6 May 2010 vanish and every strategy looks safer than the market was; (e) a rule from the bars alone
that sorts a change of scale from a market's move, each doubt resolved against the strategy. Chosen
(e). It lives in `lab/`, which the desk cannot import, so the store keeps its one rule and still
parks all 201.

**The rule, and which way each doubt falls.** Only a move made wholly between two sessions can be a
change of scale; a move within the day, or a spike that came back, cannot. Of the 33 such, a rise is
never believed unconfirmed (disbelieving a windfall costs a study nothing; counting a false one
flatters it). A fall is disbelieved only on ordinary trading, under 2.5 times the median value traded
of the twenty sessions before: all fifteen such look like changes of scale, none confirmed; the
lightest real fall came on 2.8 times (FANG, 9 March 2020). A fall with no volume to judge by is
believed. The margin is thin and was chosen looking at this list. The one error that flatters a
strategy, a real overnight crash on quiet trading read as a change of scale, is shown by none here.
The desk only buys; a study of short sales would need the opposite rule for a rise.

**What research reads of a ticker with a change of scale.** Options: (a) nothing; (b) only what
follows the last one (ROR would keep 85 of 4,260 bars); (c) the longest run on one scale; (d) every
run as a history of its own, which would make a ticker several lines for the grid. Chosen (c): 11,150
bars unread against 28,702 by (b). The store's bars are not rescaled.

**A bad print within a day is read, not mended.** Options: (a) clip a low or high far outside the
day's open and close: it mends data after the one writer, and a real flash crash looks the same;
(b) read it and name the day. Chosen (b).

**Evidence.** Tests seen failing first; the rule driven over the real list from cached answers by a
script outside the repository; 39 deliberate breaks with Python's cache off, 38 caught at once and the
last (which of two equal runs is read) once its test was added. A blind review's two blocking points
were wording the code did not keep, both corrected. The box stays unticked: the grid does not read
through the rule yet (R-DATA-7), and WWH, SHC, ECHO, MRNA and ROR stand misjudged.

### 2026-11-13 — the data lane's next boxes: the order, the keeper's road, the store's name (#66)

**Which box is first.** Options: (a) the lane objective's parked fifth first; (b) the box that says
"First, by his ruling" (VUAG, EQQQ and IDTL for SPY, QQQ and GLD) first. Chosen (b) with (a) beside
it: his ruling names it first, and their files do not overlap. For that, the parked fifth's tests go
in `tests/unit/test_lab_universe_parked.py` and do not touch `desk/store.py`.

**The keeper's road.** Options: (a) one big keeper box holding all the lane's files, alone;
(b) separate boxes with separate files. Chosen (b): the fast store, then trading hours and half-days,
then five-minute bars into the fast store, then the keeper. Two of the four run side by side, and
the paramount keeper is served sooner than by a lane held to one session.

**Half-days before the keeper.** A keeper that did not know a venue's hours and early closes would
park every line as "late" on a half-day, and could not know when no venue is open (exit 0 at once).

**Five-minute bars ahead of the archive's manners in the order, not in dependence.** Both change
`desk/archive.py`, so they cannot run together; the five-minute box is listed first because his
ruling makes it paramount. "Polite fetching" (DAT-08) waits for "The archive spared".

**The fast store's name.** `desk/bars.py`, not "hot": it becomes the one store for hot and deep data
alike, under the one writer, not a second store beside the first (canon A4). How `desk/store.py`'s
files move onto it is a later step.

**No `after` naming another lane's box.** No other lane's ids were on main and the guard refuses an
`after` naming no box; the one cross-lane dependence is an un-noted box and a request (R-DATA-9).

### 2026-11-13 — the parked fifth's box closed on the rule as it stands (data-parked-fifth, #84)

- **Tick the box, or hold it for the misjudgements.** Options: (a) hold it open until WWH, SHC and the three windfalls are settled from a second source: none exists, so the box would block the research home behind it for good; (b) tune the rule until they come out right: every signal tried (range, a round ratio, a gap in sessions) also catches real crashes (PCG 0.476, ALNY 0.515), and raising 2.5 to catch WWH (2.51) leaves FANG's real crash (2.76) a whisker away, on a number chosen looking at this one list; (c) tick it. Chosen (c): every known error is a false loss or an unread stretch, which makes a strategy look worse, never better, and each is named in the history.
- **A crash wholly won back overnight stays cut at the way back.** Options: (a) read through a one-day excursion that returns (on the one real case, ROSE, that reads three false moves instead of one, the day "returned to" being a stale quote); (b) leave it. Chosen (b).
- **A move made within a day stays named on two days.** Naming it once would be truer for a count, but tests outside the box hold the behaviour and the rungs' request counts trades held through a named day, not days. Left as is.
- **Tests not landed over the size guard.** Options: (a) ask him to loosen the guard, for two hair's-breadth cases; (b) grow the product to make room, which is forbidden in spirit; (c) run them from outside the repository and record the output. Chosen (c): 14 deliberate breaks, 12 caught by the existing tests.

### 2026-11-13 — the ISA twins, the flags and the yardstick (data-isa-twins, first step, #85)

- **Red on the tests-no-bigger-than-the-product guard.** Options: (a) tighten the claimed tests keeping every assertion; (b) add product lines; (c) ask for the guard to be loosened; (d) close the pull request. Chosen (a): (b) grows code to get round a guard, (c) is not needed, (d) throws away finished work.
- **SPY and QQQ cannot leave in this change.** Options: (a) add nothing until other lanes' tests change; (b) add the twins and flags, remove GLD, keep SPY and QQQ flagged as not holdable and ask GRID and RUNGS to stop naming them; (c) edit the other lanes' tests (refused by the claim). Chosen (b); the master holds 22 lines for a while, held by a test that names the two as leaving.
- **IDTL is priced in dollars.** The archive and the exchange quote it in dollars; the pound-priced IDTG is a different, currency-hedged product. Chosen: IDTL as he ruled, in dollars, so a purchase carries the currency cost like a US line.
- **The yardstick is one line, VUAG.** Options: VUAG; VUSA (same index, pays out its dividends); one yardstick per venue. Chosen VUAG: one capital number in pounds, one yardstick in pounds, and its dividends stay in its price, so holding it is the whole of what the market earned (AG-04).
- **What the flags say.** Options: one flag "ISA-ready"; two facts. Chosen two: IB1T shows why (retail yes, ISA no, crypto notes shut to new purchases in an ISA from 6 April 2026).
- **A line nobody has recorded.** Options: default no; default unrecorded; no default. Chosen unrecorded (None): no would call a thousand research tickers unholdable, falsely; no default would break files outside the claim.
- **The constructor's suspension check was reshaped** (same behaviour, same test) to stay inside the lint's complexity limit rather than touch the limit.

### 2026-11-13 — trading hours in the one calendar (data-hours, #87)

- **Summer time by rule, in the calendar.** Options: (a) Python's time-zone database (this PC lacks it; needs `tzdata`, a file outside the claim); (b) each country's rule in the one calendar. Chosen (b): `desk/` stays standard library only, both sides of every change tested.
- **A venue is open from its open to its closing auction, both ends included.** Options: continuous trading only; to the auction. Chosen the second: a five-minute bar is whole only at its end, so the keeper's round at 16:30 and 16:35 London (16:00 New York) collects the day's last bar and the official close.
- **A shut day asked for its hours is refused; a shut moment asked "is it open" answers nothing.** The first is the caller's mistake; the second is the keeper's ordinary question.
- **London's half-days by rule** (last session before Christmas Day, last of the year), not by 24 and 31 December: on a weekend London closes the Friday before. New York has no such carry.
- **Closing auctions as each exchange publishes:** New York's at the bell, London's five minutes after continuous trading ends.

### 2026-11-13 — the one fast store (data-fast-store, #89)

- **One table for both spans, a line keyed by venue and symbol.** Options: a table per line; one table keyed by venue, symbol, span and start. Chosen the second: one model, and thirteen symbols are two companies by venue.
- **Prices as exact text.** Options: floating point; whole ticks (needs every tick size); the decimal's own text. Chosen the text (canon B4), the history benchmark met with room.
- **A daily history is replaced whole; five-minute bars gather.** The archive restates the past for splits and a dropped bad day must go; five-minute bars are forgotten by the archive after sixty days, so nothing is cleared and a bar given again replaces that one bar.
- **A second writer waits up to five seconds, then is refused.** First built as refuse-at-once; review showed the only writer refused when readers merely opened and closed the file. Chosen SQLite's own bounded wait, not a retry in the desk's code.
- **Each round forced to disk (FULL).** NORMAL is faster but a power cut can lose rounds; the benchmark is met eighty times over with FULL.
- **A refused line leaves its round whole** (one bad ticker must not stop all trading); a round SQLite itself drops lands nothing.
- **A store or line never written is an error, not an empty answer** (failure pattern 10).
- **The fastest of five runs is the benchmark's measure,** because one run fails by chance on a busy machine; the numbers live in the test.
- **Evidence (A7):** 107 deliberate breaks over three versions; survivors listed in the pull request, each unobservable in a unit test. Two blind reviews: seven blocking points, all mended.

### 2026-11-13 — the survivors' lists (data-members, first part, #96)

- **Where past members come from.** Options: (a) a paid history of index members (spending is the operator's); (b) the index owners' notices change by change (hundreds of documents); (c) Wikipedia's dated change tables, checked by walking today's list back through them. Chosen (c): free, the walk reaches exactly 500 and 100 in 2010; unofficial, and the module says so. If survivorship ever decides a promotion, a paid history is the question for him then.
- **Where the record lives.** A file outside the repository, or the module's text. Chosen the text (about 100 lines, versioned with the code), with a golden fingerprint so no change or date is altered unnoticed.
- **How a past member is named.** A ticker is not a company (Q was Qwest, is Qnity). Options: match by ticker; carry every ticker change as an event; name each company by its last ticker on the list, and a leaver whose ticker a later member carried with its year of leaving (Q.2011, CB.2016, JCI.2016, ...). Chosen the last: no stranger's bars read as a leaver's, one mechanism.
- **Hand corrections to the source,** each because the walk back contradicted today's list: ticker changes written as a leaver and a joiner made one company (Facebook to META and twenty more); GOOG for GOOGL in April 2014; two mergers followed by the surviving company (ACE took CB, Tyco took JCI; which company's prices the archive keeps under CB and JCI before the mergers is unconfirmed); four early-2010 S&P changes added from news of the day (NRG, Berkshire, Discovery, ONEOK); second share classes of Comcast, Discovery and Liberty written as joining (22 December 2014, inferred, not sourced).
- **Days outside the record** (before 1 January 2010, after 13 November 2026) are refused, never guessed.
- **The year-by-year counts and the record's fingerprint are golden numbers;** they change only by a deliberate, explained edit.

### 2026-11-13 — five-minute bars saved for good (data-five-minute, #97)

- **Where "everything older" lives.** Options: one file with the week read from on top of the older bars; a second archive file that older bars move into. Chosen one file: 5.2 million bars still read a week in 5 ms, and moving bars between two files is the one place a bar could be lost.
- **How much is asked each evening.** The day's bars only, or all 59 days the archive keeps. Chosen all 59: 22 requests either way, a missed evening heals itself, a corrected bar is picked up.
- **A bar the archive restates takes its place if it passes the checks,** so the evening's answer can correct a bar saved while it was forming; a restatement in a wrong unit never gets in.
- **Checks not carried over from daily bars:** a missing bar and a repeated price are no fault (thin lines trade in few spans; 345 of 3LGO's bars were flat); a line late or missing its newest bar is the keeper's to judge.
- **A big move is kept and listed, not dropped,** as the daily store does: the crash watch needs those bars.
- **A wrong unit is judged against the middle price** of the bars held for those days (of the answer itself the first time). Simpler than neighbour rules and not dragged along by a run of bad bars; on the very first save an answer more than half wrong would be judged the wrong way round, and every such bar is listed.
- **The archive's "price of the moment" and a forming bar are not bars yet;** the client leaves them out so a fault list means something.
- **The store's file is `KESTREL2_DATA/bars.db`,** chosen now so the first night's bars are saved where the keeper will look.
- **`archive.gather` no longer has a default question;** every caller already named one.
- **Identical repeats of one bar are kept once without a fault,** or they would repeat for 59 evenings.

### 2026-11-14 — the old desk's five-minute bars as a head start (data-headstart, first step, #175)

- **Which objective first.** Options: (a) the keeper (R-RUNNER-7), as the protocol says; (b) the head start, as the runner's first instruction said. Chose (b): the later, more specific word, resting on his ruling "always go with recommended". The keeper is next.
- **Five-minute before daily.** The archive forgets five-minute bars after sixty days, so the old desk's are the only copy; daily bars can be fetched again any day.
- **What vouches for an old bar.** Options: (a) the old desk's cleaning; (b) the store's checks alone; (c) also that the bar lies inside its day's fresh daily bar (within the 3% the store allows). Chose (c): (b) cannot see a whole history in a wrong unit where nothing fresh is held.
- **London pence.** Options: (a) refuse them (loses seven months of six lines); (b) read a bar as pence only when it fits the day's fresh range as pence and not as pounds; (c) try any factor. Chose (b): the readings are a hundredfold apart; no other factor is tried, so bars a hundred times too small are refused.
- **A line's old bars need proof of their clock.** Options: (a) the daily range alone; (b) also bars already held for some of the same moments, at least half agreeing. Chose (b): the matrices were on Warsaw's clock (1 of 2,184 SPY bars agreed as stamped, 2,170 two hours earlier); aligned sources agreed on 65% to 99.4%, misaligned under 1%. Not tuned further.
- **"Differs"** means any of the four prices further apart than 0.01%; volumes are not compared (vendors count different venues). Bars already held are recorded as the archive's.
- **The parquet stores are not read.** They need a parquet reader, a new dependency (his to approve). Options: (a) add one to `lab/`; (b) convert once outside the repository; (c) leave them. Chose (c): the matrices carry Stooq's bars, IBKR's folder holds 24 tickers.
- **The real store is not changed until this lands and `market.db` exists** (R-RUNNER-10): the store gains a column, so older code could not write to it; the command is one line and safe to repeat.
- **A round that names no source.** Options: (a) ask MONEY to name the archive in its test and wait; (b) a round is the archive's unless an old store is named. Chose (b); the head start names its source every time. R-DATA-13 lets the default go later.
- **data-isa-twins waits** until GRID and RUNGS stop naming SPY and QQQ in their tests (the runner's ruling taken on his standing one); the old stores' consolidation comes first (R-RUNNER-10), nothing to E:, no original deleted.
- **Evidence (A7):** 36 deliberate breaks on scratch copies, 35 caught; the one missed (the order the two old stores are read in) caught since. Blind review: one blocking fault (a read-only open leaves two side files), fixed and tested. `manifest.toml` gains one line registering `lab/headstart.py`; nothing loosened.

### 2026-11-14 — the data lane's open boxes in working order (#180)

- **The keeper before the ISA twins.** Options: (a) twins first, as the book's wording says; (b) the keeper first. Chose (b): the twins wait on other lanes, the keeper is the runner's blocking request and his "paramount" ruling.
- **The head start second:** his ask says "now", and five-minute bars older than sixty days exist nowhere else.
- **The single-line findings (2MU, 5QQQ, SGLN, 3LGO) and the three store findings are chained one after another:** they change the same two files (`desk/lines.py`, `desk/store.py`), so only one could run at a time anyway.
- **data-consolidated carries no "waits: operator".** Options: (a) hold the whole box for his yes; (b) hand it out and let its session stop at the deletion. Chose (b): only deleting the originals is his.
- **data-tiers names a new module, `desk/tiers.py`:** which tier a name is in is one concept and needs one home; the building session may find a better name.
- **Nine boxes left un-noted** rather than guessed at: a note naming the wrong files makes a session fail its check.

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
