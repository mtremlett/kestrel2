"""The ladder's wiring: its yardsticks are lines the store writes, its sets name known rules."""

from __future__ import annotations

from lab import ladder, ladder_epon, rulebook, universe


def test_every_yardstick_is_a_line_of_its_venue_in_the_research_list() -> None:
    held = {(line.venue, line.symbol) for line in universe.UNIVERSE}
    missing = {v: s for v, s in ladder.MARKETS.items() if (v, s) not in held}
    assert not missing, f"yardstick(s) {missing} (venue: symbol) not in the research list"


def test_every_set_the_ladder_can_run_names_only_rules_the_rule_book_resolves() -> None:
    book = rulebook.rules()
    for set_name, rules in {
        "set1": {c.strategy for c in ladder.cells()},
        "EPON": set(ladder_epon.eponymous()),
    }.items():
        unknown = sorted(rules - set(book))
        assert not unknown, f"set {set_name} names rules the rule book lacks: {unknown}"
