"""
Test utilities for :py:mod:`betty.localizable`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from betty.locale import default_locale
from betty.localizables.static import CountableStaticTranslations

if TYPE_CHECKING:
    from betty.localizable import CountableLocalizable

dummy_countable_localizable: Final[CountableLocalizable] = CountableStaticTranslations({
    default_locale: {
        "one": "{count} countable dummy localizable",
        "other": "{count} countable dummy localizables",
    }
})
"""
A dummy countable localizable.
"""
