"""The eponymous rules' publications: each of the twenty the ladder can judge is held to its
known answers by `proven`, and code that does not give them, or a rule not on file, is refused."""

from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import replace
from decimal import Decimal
from typing import cast

import pytest

from desk import eponymous_williams_r
from lab import ladder, published
from lab.published import Published
from lab.published_epon import EPONYMOUS_PUBLISHED

RULE = "williams_r"


@pytest.fixture(autouse=True)
def _fresh() -> None:
    published.proven.cache_clear()


def test_each_of_the_twenty_rules_is_proven_on_its_cases_and_names_its_source() -> None:
    names = ladder.eponymous()
    assert len(names) == 20 and set(names) == set(EPONYMOUS_PUBLISHED)
    for name in names:
        assert published.proven(name) is EPONYMOUS_PUBLISHED[name]
        assert name not in published.PUBLISHED and EPONYMOUS_PUBLISHED[name].source.strip()


def test_a_rule_off_file_or_with_other_trades_or_other_code_is_refused_by_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    book = cast(MutableMapping[str, Published], EPONYMOUS_PUBLISHED)
    rule = book[RULE]
    wrong = replace(rule.cases[0], trades=((9, 11),))
    monkeypatch.setitem(book, RULE, replace(rule, cases=(wrong,)))
    with pytest.raises(ValueError, match=r"williams_r: the desk's engine is not.*\(9, 10\)"):
        published.proven(RULE)
    monkeypatch.setitem(book, RULE, rule)
    monkeypatch.setattr(eponymous_williams_r, "BUY_AT", Decimal(-95))
    with pytest.raises(ValueError, match=r"williams_r: the desk's engine is not.*\(\) where"):
        published.proven(RULE)
    monkeypatch.undo()
    monkeypatch.delitem(book, RULE)
    with pytest.raises(ValueError, match="williams_r: no published rule on file"):
        published.proven(RULE)
