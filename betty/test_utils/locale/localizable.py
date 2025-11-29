"""
Test utilities for :py:mod:`betty.locale.localizable`.
"""

from __future__ import annotations

from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable import (
    CountableLocalizable,
    CountableStaticTranslations,
    Localizable,
    StaticTranslations,
)

DUMMY_LOCALIZABLE: Localizable = StaticTranslations("DUMMY_LOCALIZABLE")
"""
A dummy localizable.
"""

DUMMY_COUNTABLE_LOCALIZABLE: CountableLocalizable = CountableStaticTranslations(
    {
        DEFAULT_LOCALE: {
            "one": "{count} DUMMY_COUNTABLE_LOCALIZABLE",
            "other": "{count} DUMMY_COUNTABLE_LOCALIZABLES",
        }
    }
)
"""
A dummy countable localizable.
"""
