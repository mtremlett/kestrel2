# KESTREL2

A small, verifiable quant desk for one retail trader. **Paper and backtest only.**

This repository is public. It holds no prices, no positions, no account records and no
credentials — only code and the tiny synthetic fixtures the tests run on.

## What it is for

One person, one PC, free data. The desk decides what to buy and sell, sends those orders
to a paper account at a broker, keeps its own book honest against the broker's, and says
each day what it did. When it has earned the right, and only then, the operator alone
signs it over to real money in a UK ISA: cash, long only, whole shares, in pounds.

The gates, in order: **FIRST-LIGHT** (the machine works), **A-GATE** (the edge is real),
then scale. Nothing skips a gate.

## Why it was started again

The first attempt ran for a year and reached 438,466 lines of code, 2,054 test files and
2,221 tests set aside as known failures. It still could not be trusted end to end. The
cause was not any one bug. It was that nothing in it could refuse: new files, new checks
and new rules were added faster than anything was ever finished or removed.

So this repository is built the other way round. The machinery that refuses came first,
before a single line of desk code, and it is enforced away from the operator's computer
where it cannot be quietly switched off.

## How anything is verified

    python check.py

That is the only way. The git hook runs it, GitHub runs it, and "done" means it exited 0
and somebody read the output. A second way of being sure is how a desk ends up with two
answers to the same question.

GitHub runs the same command on a clean machine with no access to the operator's PC, his
data or his broker — which is why a test here cannot quietly start depending on live
state and call itself green.

## Getting set up

    python -m venv .venv
    .venv/Scripts/python -m pip install -r requirements.txt
    .venv/Scripts/python check.py

## Where things are

| | |
|---|---|
| `desk/` | the trading core. Imports the standard library and nothing else |
| `lab/` | research and the ladder. Uses the core's own code to judge strategies |
| `tests/guards/` | the rules that refuse. Each one is proven by breaking it |
| `CANON.md` | how work is done here |
| `docs/SCENES.md` | what "working" means, in business language |
| `docs/PLAN.md` | the phases, and where we are |
| `docs/STATUS.md` | what is happening right now, and what is known but not fixed |

## Safety

The desk works in backtest and paper only. It never enables live mode, places a real
order, connects to a real account or reads live credentials. The broker's live-money port
may not even be named in the core except on a line that refuses it, and a guard checks
every line of every file on every change.
