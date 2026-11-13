"""EVERY REQUIREMENT HAS A HOME. His spec (DESK_REQUIREMENTS_V2, 226 rows, ratified 31
October 2026) and the eleven best-in-class additions he took on 13 November (BIC-01 to
BIC-11) are held here as one roster. Each id must have a home: a step in a lane's book or
a phase of docs/PLAN.md, the plan's standing list, or the entry in docs/DECISIONS.md that
dropped or replaced it. An id that loses its home, or is dropped while a step still builds
it, fails the check. Ruled 13 November 2026 (docs/DECISIONS.md).
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ID = re.compile(r"\b[A-Z]{2,4}-\d{2}\b")
#: A checklist step: its first line and the indented lines that carry on from it.
STEP = re.compile(r"^- \[[ x]\] .*(?:\n {6}.*)*", re.MULTILINE)
ENTRY = "## 2026-11-13 — every requirement of his spec has a home"

ROSTER = frozenset(
    """
BIC-01 BIC-02 BIC-03 BIC-04 BIC-05 BIC-06 BIC-07 BIC-08 BIC-09 BIC-10 BIC-11 BT-04
BT-08 BT-09 BT-10 BT-15 CODE-01 CODE-02 CODE-03 CODE-04 CODE-05 CODE-06 CODE-07
CODE-08 CODE-09 DAT-01 DAT-02 DAT-03 DAT-04 DAT-05 DAT-06 DAT-07 DAT-08 DAT-09
DAT-11 DQ-01 DQ-02 DQ-03 DQ-04 DQ-05 DQ-06 DQ-07 DQ-08 DQ-09 DQ-10 DQ-11 DQ-12 DQ-13
EMG-01 EMG-02 EMG-03 EMG-04 EMG-05 EMG-06 FIL-01 FIL-02 FIL-03 FIL-04 FIL-05 FIL-06
FIL-07 FIL-08 GOV-01 GOV-02 GOV-03 GOV-04 GOV-05 GOV-06 GOV-08 GOV-09 GOV-10 GOV-11
GOV-12 GOV-13 GOV-14 LAD-01 LAD-02 LAD-03 LAD-04 LAD-05 LAD-06 LAD-07 LAD-08 LAD-09
LAD-10 LAD-11 LAD-12 LAD-13 LAD-14 LAD-15 LIV-01 LIV-02 LIV-03 LIV-04 LIV-05 LIV-06
LIV-07 LIV-09 MIG-01 MIG-02 MIG-03 MIG-04 MIG-05 MIG-06 MIG-07 MIG-08 MIG-09 MSG-01
MSG-02 MSG-03 MSG-04 MSG-05 MSG-06 MSG-07 MSG-08 MSG-09 MSG-10 MSG-11 MSG-12 MSG-13
NS-01 NS-02 NS-03 NS-04 NS-05 NS-06 NS-07 NS-08 NS-09 NS-10 NS-11 NS-12 NS-13 NS-14
OPS-01 OPS-02 OPS-03 OPS-04 OPS-05 OPS-06 OPS-07 OPS-08 OPS-09 OPS-10 OPS-11 OPS-12
OPS-14 OPS-15 OPS-16 REG-01 REG-02 REG-03 REG-04 REG-05 REG-06 REG-07 REG-08 REG-09
REG-10 REG-11 SIZ-01 SIZ-02 SIZ-03 SIZ-06 SIZ-07 SIZ-08 SIZ-09 SIZ-10 SIZ-11 STP-01
STP-02 STP-03 STP-04 STP-05 STP-06 STP-07 STP-08 STP-09 STP-10 STP-11 STR-01 STR-02
STR-03 STR-04 STR-05 STR-06 STR-07 STR-08 STR-10 STR-11 STR-12 STR-13 STR-14 STR-15
STR-16 STR-17 STR-18 STR-20 TRD-01 TRD-02 TRD-04 TRD-05 TRD-06 TRD-07 TRD-08 TRD-09
TRD-10 TRD-11 TRD-12 TRD-13 TRD-14 TRD-15 TST-01 TST-04 TST-05 TST-06 TST-08 TST-10
TST-11 TST-12 TST-13 TST-15 TST-17 TST-18 TST-19 TST-20 TST-21 TST-22 TST-23 UNI-01
UNI-02 UNI-03 UNI-04 UNI-06 UNI-07 UNI-08 UNI-09
""".split()
)


def _section(text: str, heading: str) -> str:
    """The text under one heading, up to the next heading of the same level."""
    start = text.index(heading)
    level = heading.split(" ", 1)[0] + " "
    end = text.find("\n" + level, start + len(heading))
    return text[start : end if end != -1 else len(text)]


def homes() -> dict[str, set[str]]:
    """Where each kind of home names its ids, read from the plan and the decision."""
    plan = (ROOT / "docs/PLAN.md").read_text(encoding="utf-8")
    entry = _section((ROOT / "docs/DECISIONS.md").read_text(encoding="utf-8"), ENTRY)
    standing = _section(plan, "## The requirements")
    dropped_table = entry.split("**Decided, second", 1)[1].split("**Replaced by", 1)[0]
    replaced = entry.split("**Replaced by", 1)[1].split("**Decided, third", 1)[0]
    return {
        "step": set(ID.findall("\n".join(STEP.findall(plan)))),
        "standing": set(ID.findall(standing.split("**Standing", 1)[1])),
        "dropped": set(re.findall(r"^\| ([A-Z]{2,4}-\d{2}) \|", dropped_table, re.MULTILINE)),
        "replaced": set(ID.findall(replaced)) & ROSTER,  #: not the rulings that replaced them
    }


def test_the_roster_is_the_spec_and_the_additions() -> None:
    assert len(ROSTER) == 237, f"the roster holds {len(ROSTER)} ids, not 226 + 11"


def test_every_requirement_has_a_home() -> None:
    found = homes()
    homeless = sorted(ROSTER - set().union(*found.values()))
    assert not homeless, f"no step, standing line or decision for: {homeless}"


def test_nothing_dropped_or_replaced_is_still_built() -> None:
    found = homes()
    gone = found["dropped"] | found["replaced"]
    both = sorted(gone & (found["step"] | found["standing"]))
    assert not both, f"dropped or replaced, yet still planned or standing: {both}"


def test_every_id_the_plan_names_is_known() -> None:
    found = homes()
    named = found["step"] | found["standing"] | found["dropped"]
    rulings = {f"AG-0{n}" for n in range(1, 7)}  #: the A-GATE's own terms, his ruling
    unknown = sorted(named - ROSTER - rulings)
    assert not unknown, f"ids the spec does not have: {unknown}"
