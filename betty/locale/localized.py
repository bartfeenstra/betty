"""
Describe localized information.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from typing_extensions import override

from betty.locale import (
    UNDETERMINED_LOCALE,
    LocaleLike,
    negotiate_locale,
    to_locale,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class Localized:
    """
    A resource that is localized, e.g. contains information in a specific locale.
    """

    _locale: str

    @property
    def locale(self) -> str:
        """
        The locale the data in this instance is in.
        """
        return self._locale


def negotiate_localizeds(
    preferred_locales: LocaleLike | Sequence[LocaleLike],
    localizeds: Sequence[Localized],
) -> Localized | None:
    """
    Negotiate the preferred localized value from a sequence.
    """
    negotiated_locale_data = negotiate_locale(
        preferred_locales,
        [
            localized.locale
            for localized in localizeds
            if localized.locale is not UNDETERMINED_LOCALE
        ],
    )
    if negotiated_locale_data is not None:
        negotiated_locale = to_locale(negotiated_locale_data)
        for localized in localizeds:
            if localized.locale == negotiated_locale:
                return localized
    for localized in localizeds:
        if localized.locale is UNDETERMINED_LOCALE:
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
    def __new__(cls, localized: str, *, locale: str = UNDETERMINED_LOCALE):
        new = super().__new__(cls, localized)
        new._locale = locale
        return new
