"""
Describe localized information.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from typing_extensions import override

from betty.locale import negotiate_locale

if TYPE_CHECKING:
    from collections.abc import Sequence

    from babel import Locale


class Localized:
    """
    A resource that is localized, e.g. contains information in a specific locale.
    """

    _locale: Locale | None

    @property
    def locale(self) -> Locale | None:
        """
        The locale the data in this instance is in.
        """
        return self._locale


def negotiate_localizeds(
    preferred_locales: Locale | Sequence[Locale],
    localizeds: Sequence[Localized],
) -> Localized | None:
    """
    Negotiate the preferred localized value from a sequence.
    """
    negotiated_locale = negotiate_locale(
        preferred_locales,
        [localized.locale for localized in localizeds if localized.locale is not None],
    )
    if negotiated_locale is not None:
        for localized in localizeds:
            if localized.locale == negotiated_locale:
                return localized
    for localized in localizeds:
        if localized.locale is None:
            return localized
    with suppress(IndexError):
        return localizeds[0]
    return None


class LocalizedStr(Localized, str):
    """
    A localized string.
    """

    __slots__ = "_locale"

    @override
    def __new__(cls, localized: str, *, locale: Locale | None = None):
        new = super().__new__(cls, localized)
        new._locale = locale
        return new
