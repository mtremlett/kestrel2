"""desk - THE TRADING CORE. Data in, decisions out, orders through one broker door.

Owns: nothing itself. The modules beside it own one thing each, named in manifest.toml.
Does NOT own: research, the ladder, sweeps or verdicts about strategies - those are lab/.

THE WALL: this package imports the standard library and nothing else. It may never
import lab/. tests/guards/test_guards.py fails if it does. That rule exists because the
first desk's clean core was absorbed back into 352,000 lines of everything - not by
anyone editing the core, but by its daily runner being placed outside it.
"""
import os
