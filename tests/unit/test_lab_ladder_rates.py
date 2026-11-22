"""The ladder's rates have one door (his 22 Nov, "paramount"): the pound's closes come from the
caller's source, the history database, and a call with no source is refused, never the archive."""

from __future__ import annotations

import pytest

from desk import archive
from lab import ladder


def test_the_rates_with_no_source_fail_loudly_and_never_ask_the_archive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(archive, "fetch", lambda *_: pytest.fail("the archive was asked"))
    with pytest.raises(TypeError, match="no source of the pound's closes"):
        ladder.rates()
