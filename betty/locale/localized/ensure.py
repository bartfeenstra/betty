"""
Lazily create localizeds.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from betty.locale.localizable import LocalizableLike
    from betty.locale.localizer import Localizer


def ensure_localized(localizable: LocalizableLike, *, localizer: Localizer) -> str:
    """
    Ensure that a localizable-like value is or is made to be localized.
    """
    from betty.locale.localizable import Localizable

    if isinstance(localizable, str):
        return localizable
    if not isinstance(localizable, Localizable):
        from betty.locale.localizable.static import StaticTranslations

        localizable = StaticTranslations(localizable)
    return localizable.localize(localizer)
