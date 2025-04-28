"""
Provide Locale API errors.
"""

from __future__ import annotations

from babel.core import Locale
from babel.localedata import locale_identifiers

from betty.error import UserFacingError
from betty.locale import to_locale
from betty.locale.localizable import _, do_you_mean, join


class LocaleError(UserFacingError, Exception):
    """
    A locale API error.
    """


class InvalidLocale(LocaleError, ValueError):
    """
    Raised when a value is not a valid locale.
    """

    def __init__(self, invalid_locale: str) -> None:
        super().__init__(
            _('"{invalid_locale}" is not a valid IETF BCP 47 language tag.').format(
                invalid_locale=invalid_locale
            )
        )
        self.invalid_locale = invalid_locale


class LocaleNotFound(LocaleError, ValueError):
    """
    Raised when a locale could not be found.
    """

    def __init__(self, locale: str) -> None:
        locale_chars = {char for char in locale[: locale.find("-")] if char.isalpha()}
        available_locales = sorted(
            to_locale(Locale.parse(identifier))
            for identifier in locale_identifiers()
            if set(identifier[: identifier.find("_")]) & locale_chars
        )
        super().__init__(
            join(
                _("Cannot find locale {locale}.").format(locale=locale),
                do_you_mean(*available_locales),
            )
        )
        self.locale = locale
