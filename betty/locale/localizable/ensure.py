"""
Lazily create localizables.
"""

from __future__ import annotations

from betty.locale.localizable import (
    CountableLocalizable,
    CountableLocalizableLike,
    Localizable,
    LocalizableLike,
)


def ensure_localizable(localizable: LocalizableLike) -> Localizable:
    """
    Ensure that a localizable-like value is or is made to be an actual localizable.
    """
    if isinstance(localizable, Localizable):
        return localizable
    if isinstance(localizable, str):
        from betty.locale.localizable.plain import Plain

        return Plain(localizable)
    from betty.locale.localizable.static import StaticTranslations

    return StaticTranslations(localizable)


def ensure_countable_localizable(
    localizable: CountableLocalizableLike,
) -> CountableLocalizable:
    """
    Ensure that a countable-localizable-like value is or is made to be an actual countable localizable.
    """
    if isinstance(localizable, CountableLocalizable):
        return localizable
    from betty.locale.localizable.static import CountableStaticTranslations

    return CountableStaticTranslations(localizable)
