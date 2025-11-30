"""
Test utilities for :py:mod:`betty.locale.localizable`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.locale.localizable import (
    CountableLocalizable,
    Localizable,
    StaticTranslations,
)
from betty.locale.localized import Localized, LocalizedStr

if TYPE_CHECKING:
    from betty.locale.localizer import Localizer


class _CountedDummyLocalizable(Localizable):
    def __init__(self, count: int):
        self._count = count

    @override
    def localize(self, localizer: Localizer, /) -> Localized & str:
        return LocalizedStr("{count} COUNTABLE_DUMMY_LOCALIZABLE")


class _DummyCountableLocalizable(CountableLocalizable):
    @override
    def count(self, count: int, /) -> Localizable:
        return _CountedDummyLocalizable(count)


DUMMY_LOCALIZABLE: Localizable = StaticTranslations("DUMMY_LOCALIZABLE")
"""
A dummy localizable.
"""

DUMMY_COUNTABLE_LOCALIZABLE: CountableLocalizable = _DummyCountableLocalizable()
"""
A dummy countable localizable.
"""
