"""
Lazily ensure the localization of values.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.locale import HasLocaleStr

if TYPE_CHECKING:
    from betty.locale import HasLocale
    from betty.locale.localizable import LocalizableLike
    from betty.locale.localize import Localizer


def ensure_localized(
    localizable: LocalizableLike, *, localizer: Localizer
) -> HasLocale & str:
    """
    Ensure that a localizable-like value is or is made to be localized.
    """
    from betty.locale.localizable import Localizable

    if isinstance(localizable, str):
        return HasLocaleStr(localizable)
    if not isinstance(localizable, Localizable):
        from betty.locale.localizable.static import StaticTranslations

        localizable = StaticTranslations(localizable)
    return localizable.localize(localizer)
