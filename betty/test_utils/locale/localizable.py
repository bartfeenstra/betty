"""
Test utilities for :py:mod:`betty.localizable`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.locale import default_locale
from betty.localizables.static import CountableStaticTranslations, StaticTranslations

if TYPE_CHECKING:
    from betty.localizable import CountableLocalizable, Localizable

DUMMY_LOCALIZABLE: Localizable = StaticTranslations("DUMMY_LOCALIZABLE")
"""
A dummy localizable.
"""

DUMMY_COUNTABLE_LOCALIZABLE: CountableLocalizable = CountableStaticTranslations({
    default_locale: {
        "one": "{count} DUMMY_COUNTABLE_LOCALIZABLE",
        "other": "{count} DUMMY_COUNTABLE_LOCALIZABLES",
    }
})
"""
A dummy countable localizable.
"""
