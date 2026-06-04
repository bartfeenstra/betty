"""
Test utilities for :py:mod:`betty.locale.localizable`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.locale import default_locale
from betty.locale.localizable.plain import Plain
from betty.locale.localizable.static import CountableStaticTranslations

if TYPE_CHECKING:
    from betty.locale.localizable import CountableLocalizable, Localizable

DUMMY_LOCALIZABLE: Localizable = Plain("DUMMY_LOCALIZABLE")
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
