"""simcity_census - THE CENSUS of SimCity: every part of the money path, and the scenarios that
ran it, measured by a profiler that watches the calls made while a scenario is in force."""

from __future__ import annotations

import cProfile
from types import CodeType, ModuleType


def parts(path: tuple[ModuleType, ...]) -> dict[CodeType, str]:
    """THE PARTS: all a module of the money path offers by name, each function and each method
    or property of its classes; not an underscore name, nor a Protocol's wording."""
    found: dict[CodeType, str] = {}
    for module in path:
        for name, thing in vars(module).items():
            own = getattr(thing, "__module__", None) == module.__name__
            if name.startswith("_") or not own or getattr(thing, "_is_protocol", False):
                continue
            members = vars(thing).items() if isinstance(thing, type) else ((name, thing),)
            for inner, member in members:
                for wrapper in ("fget", "__wrapped__"):  #: a property; a class's or static method
                    member = getattr(member, wrapper, member)
                code = getattr(member, "__code__", None)
                if isinstance(code, CodeType) and not inner.startswith("_"):
                    found[code] = f"{module.__name__.rpartition('.')[2]}.{code.co_qualname}"
    return found


class Census:
    """THE CENSUS, MEASURED: the profiler sees every call made while a scenario is in force."""

    def __init__(self, path: tuple[ModuleType, ...]) -> None:
        self._parts = parts(path)
        self.ran: dict[str, set[str]] = {name: set() for name in sorted(self._parts.values())}
        self._profile = cProfile.Profile(subcalls=False, builtins=False)
        self.scenario: str | None = None

    def now(self, scenario: str | None) -> None:
        """From here every call is this scenario's; with none, the watching ends."""
        if self.scenario is not None:
            self._profile.disable()
            for code in (entry.code for entry in self._profile.getstats()):
                if isinstance(code, CodeType) and code in self._parts:
                    self.ran[self._parts[code]].add(self.scenario)
            self._profile.clear()
        self.scenario = scenario
        if scenario is not None:
            self._profile.enable()
