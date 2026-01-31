"""
Localizers provide a wide range of localization utilities through a single entry point.
"""

from __future__ import annotations

import gettext as gettext_api
from typing import TYPE_CHECKING, final

from betty.locale import (
    DEFAULT_LOCALE,
    HasLocale,
    HasLocaleStr,
    ResolvableLocale,
    resolve_locale,
)
from betty.typing import threadsafe

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from babel import Locale
    from ty_extensions import Intersection

    from betty.locale.translation import TranslationRepository


@final
class Localizer:
    """
    Localize a variety of data into a specific locale.
    """

    def __init__(
        self, locale: ResolvableLocale, translations: gettext_api.NullTranslations, /
    ):
        self._locale = resolve_locale(locale)
        self._translations = translations

    @property
    def locale(self) -> Locale:
        """
        The locale.
        """
        return self._locale

    def _(self, message: str, /) -> Intersection[HasLocale, str]:
        """
        Like :py:meth:`gettext.gettext`.

        Arguments are identical to those of :py:meth:`gettext.gettext`.
        """
        return HasLocaleStr(self._translations.gettext(message), locale=self._locale)

    def gettext(self, message: str, /) -> Intersection[HasLocale, str]:
        """
        Like :py:meth:`gettext.gettext`.

        Arguments are identical to those of :py:meth:`gettext.gettext`.
        """
        return HasLocaleStr(self._translations.gettext(message), locale=self._locale)

    def ngettext(
        self, message_singular: str, message_plural: str, n: int, /
    ) -> Intersection[HasLocale, str]:
        """
        Like :py:meth:`gettext.ngettext`.

        Arguments are identical to those of :py:meth:`gettext.ngettext`.
        """
        return HasLocaleStr(
            self._translations.ngettext(message_singular, message_plural, n),
            locale=self._locale,
        )

    def pgettext(self, context: str, message: str, /) -> Intersection[HasLocale, str]:
        """
        Like :py:meth:`gettext.pgettext`.

        Arguments are identical to those of :py:meth:`gettext.pgettext`.
        """
        return HasLocaleStr(
            self._translations.pgettext(context, message), locale=self._locale
        )

    def npgettext(
        self, context: str, message_singular: str, message_plural: str, n: int, /
    ) -> Intersection[HasLocale, str]:
        """
        Like :py:meth:`gettext.npgettext`.

        Arguments are identical to those of :py:meth:`gettext.npgettext`.
        """
        return HasLocaleStr(
            self._translations.npgettext(context, message_singular, message_plural, n),
            locale=self._locale,
        )


DEFAULT_LOCALIZER = Localizer(DEFAULT_LOCALE, gettext_api.NullTranslations())


@final
@threadsafe
class LocalizerRepository:
    """
    Exposes the available localizers.
    """

    def __init__(self, translations: TranslationRepository, /):
        self._translations = translations
        self._localizers: MutableMapping[Locale, Localizer] = {}

    def get(self, locale: ResolvableLocale, /) -> Localizer:
        """
        Get the localizer for the given locale.
        """
        locale = resolve_locale(locale)
        try:
            return self._localizers[locale]
        except KeyError:
            from betty.locale.translation import UntranslatedLocale

            try:
                translations = self._translations.get(locale)
            except UntranslatedLocale:
                translations = gettext_api.NullTranslations()
            self._localizers[locale] = Localizer(locale, translations)
            return self._localizers[locale]
