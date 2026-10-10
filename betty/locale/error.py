"""
Locale API errors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from babel import Locale
from babel.localedata import locale_identifiers

from betty.locale import to_language_tag
from betty.localizables.gettext import _
from betty.localizables.markup import Quote, do_you_mean
from betty.user.error import UserFacingError
from betty.validation import Invalid

if TYPE_CHECKING:
    from collections.abc import Sequence


class LocaleError(UserFacingError):
    """
    A locale API error.
    """


@final
class InvalidLocale(Invalid, LocaleError):
    """
    Raised when a value is not a valid locale.
    """

    def __init__(self, invalid_locale: str, /) -> None:
        super().__init__(
            invalid_locale,
            _("{invalid_locale} is not a valid IETF BCP 47 language tag.").format(
                invalid_locale=Quote(invalid_locale)
            ),
        )


@final
class UnknownLocale(Invalid, LocaleError):
    """
    Raised when a locale is not known by the system.
    """

    _AVAILABLE_LOCALES: Final[Sequence[str]] = sorted(
        to_language_tag(Locale.parse(identifier)) for identifier in locale_identifiers()
    )

    def __init__(self, locale: str, /) -> None:
        locale_chars = {char for char in locale[: locale.find("-")] if char.isalpha()}
        available_locales = [
            locale
            for locale in self._AVAILABLE_LOCALES
            if set(locale[: locale.find("_")]) & locale_chars
        ]
        super().__init__(
            locale,
            _("Locale {locale} is not known by your system.").format(locale=locale),
            hint=do_you_mean(*available_locales),
        )
