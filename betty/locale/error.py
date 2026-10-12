"""
Locale API errors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from babel import Locale
from babel.localedata import locale_identifiers

from betty.error import Error
from betty.locale import to_language_tag
from betty.localizables.gettext import _
from betty.localizables.markup import do_you_mean
from betty.validators import InvalidValue

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.location import ResolvableLocation


class LocaleError(Error):
    """
    A locale API error.
    """


@final
class InvalidLocale(InvalidValue[str], LocaleError):
    """
    Raised when a value is not a valid locale.
    """

    _message = _("This is not a valid IETF BCP 47 language tag.")


@final
class UnknownLocale(InvalidValue[str], LocaleError):
    """
    Raised when a locale is not known by the system.
    """

    _available_locales: Final[Sequence[str]] = sorted(
        to_language_tag(Locale.parse(identifier)) for identifier in locale_identifiers()
    )
    _message = _("This locale is not known by your system.")

    def __init__(self, locale: str, /, *, at: ResolvableLocation = ()) -> None:
        locale_chars = {char for char in locale[: locale.find("-")] if char.isalpha()}
        available_locales = [
            locale
            for locale in self._available_locales
            if set(locale[: locale.find("_")]) & locale_chars
        ]
        super().__init__(locale, hint=do_you_mean(*available_locales), at=at)
