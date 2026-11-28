"""The eponymous rules' publications: each of the twenty the ladder can judge is held to its
known answers by `proven`, and code that does not give them, or a rule not on file, is refused."""

from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import replace
from decimal import Decimal
from typing import cast

import pytest

from desk import eponymous_keltner_channel_trend
from lab import ladder, published, published_epon, reproduce
from lab.published import Published
from lab.published_epon import EPONYMOUS_PUBLISHED, SECONDARY, TESTED, Printed, Replication, Search

RULE = "keltner_channel_trend"


@pytest.fixture(autouse=True)
def _fresh() -> None:
    published.proven.cache_clear()


def test_each_rule_on_file_is_proven_on_its_cases_and_names_its_source() -> None:
    names = ladder.eponymous()
    assert len(names) == 20 and set(EPONYMOUS_PUBLISHED) == set(names)
    for name in EPONYMOUS_PUBLISHED:
        assert published.proven(name) is EPONYMOUS_PUBLISHED[name]
        assert name not in published.PUBLISHED and EPONYMOUS_PUBLISHED[name].source.strip()
    assert set(TESTED) == set(names)  #: every rule's published test written down, or where looked
    assert [n for n, t in TESTED.items() if t.candidate] == ["connors_rsi2", "faber_tactical"]
    assert TESTED["darvas_box"].said().startswith("no numbers found free (looked: web search")
    with pytest.raises(ValueError, match="no page read and nowhere looked"):
        Printed(Search.NONE, " ")
    with pytest.raises(ValueError, match="no address, market, period or numbers"):
        Printed(Search.SECOND, "https://x", "SPY")  #: no period, no numbers


def test_a_rule_off_file_or_with_other_trades_or_other_code_is_refused_by_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    book = cast(MutableMapping[str, Published], EPONYMOUS_PUBLISHED)
    rule = book[RULE]
    wrong = replace(rule.cases[0], trades=((9, 11),))
    monkeypatch.setitem(book, RULE, replace(rule, cases=(wrong,)))
    with pytest.raises(
        ValueError, match=r"keltner_channel_trend: the desk's engine is not.*\((9, 11)\)"
    ):
        published.proven(RULE)
    monkeypatch.setitem(book, RULE, rule)
    monkeypatch.setattr(eponymous_keltner_channel_trend, "DAYS", 20)
    with pytest.raises(
        ValueError, match=r"keltner_channel_trend: the desk's engine is not.*\(\) where"
    ):
        published.proven(RULE)
    monkeypatch.undo()
    monkeypatch.delitem(book, RULE)
    with pytest.raises(ValueError, match="keltner_channel_trend: no published rule on file"):
        published.proven(RULE)


def test_a_secondary_figure_names_its_source_and_reproduction_lands_inside_the_range(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seconds = {n for n, t in TESTED.items() if t.found is Search.SECOND}
    assert seconds == set(SECONDARY) == {"connors_rsi2"}  #: RSI-2 first, each with its figures
    for name in seconds:
        assert TESTED[name].page in {one.page for one in SECONDARY[name]}
        assert TESTED[name].said().startswith("a secondary replication of the rule as coded: SPY")
    measures = {m.name for m in reproduce.Measure}
    assert all(set(one.figures) <= measures for ones in SECONDARY.values() for one in ones)
    assert published_epon.span("connors_rsi2", "CAGR") == (Decimal("5.0"), Decimal("5.0"))
    rsi2 = SECONDARY["connors_rsi2"][0]
    other = replace(rsi2, figures={"CAGR": Decimal("3.7"), "TRADES": Decimal(149)})
    monkeypatch.setitem(cast(MutableMapping[str, object], SECONDARY), "connors_rsi2", (rsi2, other))
    assert published_epon.span("connors_rsi2", "CAGR") == (Decimal("3.7"), Decimal("5.0"))
    with pytest.raises(ValueError, match="connors_rsi2: no secondary replication prints WINNERS"):
        published_epon.span("connors_rsi2", "WINNERS")
    with pytest.raises(ValueError, match="no address, date, rules or period"):
        replace(rsi2, period=" ")
    with pytest.raises(ValueError, match="prints no number"):
        Replication(rsi2.page, "x", "x", "x", "x", {"CAGR": Decimal("NaN")})
