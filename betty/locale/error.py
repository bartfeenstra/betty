"""
Locale API errors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from babel import Locale
from babel.localedata import locale_identifiers

from betty.exception import HumanFacingException
from betty.locale import to_language_tag
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Paragraph, do_you_mean

if TYPE_CHECKING:
    from collections.abc import Sequence


class LocaleError(HumanFacingException, Exception):
    """
    A locale API error.
    """


@final
class InvalidLocale(LocaleError):
    """
    Raised when a value is not a valid locale.
    """

    def __init__(self, invalid_locale: str, /) -> None:
        super().__init__(
            _('"{invalid_locale}" is not a valid IETF BCP 47 language tag.').format(
                invalid_locale=invalid_locale
            )
        )


@final
class UnknownLocale(LocaleError):
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
            Paragraph(
                _("Locale {locale} is not known by your system.").format(locale=locale),
                do_you_mean(*available_locales),
            )
        )
