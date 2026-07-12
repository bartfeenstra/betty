"""
Localizers provide a wide range of localization utilities through a single entry point.
"""

from __future__ import annotations

import gettext as gettext_api
from typing import TYPE_CHECKING, Final, final

from betty.locale import ResolvableLocale, default_locale, resolve_locale
from betty.localized import LocalizedStr
from betty.threading import threadsafe

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from babel import Locale

    from betty.gettext import TranslationRepository
    from betty.localizable import ResolvableLocalizable


@final
class Localizer:
    """
    Localize a variety of data into a specific locale.
    """

    def __init__(
        self, locale: ResolvableLocale, translations: gettext_api.NullTranslations, /
    ):
        self.locale: Final[Locale] = resolve_locale(locale)
        """
        The locale.
        """
        self._translations = translations

    def localize(self, localizable: ResolvableLocalizable, /) -> LocalizedStr:
        """
        Ensure that a localizable-like value is or is made to be localized.
        """
        from betty.localizable import Localizable

        if isinstance(localizable, str):
            return LocalizedStr(localizable)
        if not isinstance(localizable, Localizable):
            from betty.localizables.static import StaticTranslations

            localizable = StaticTranslations(localizable)
        return localizable.localize(self)

    def _(self, message: str, /) -> LocalizedStr:
        """
        Like :py:meth:`gettext.gettext`.

        Arguments are identical to those of :py:meth:`gettext.gettext`.
        """
        return LocalizedStr(self._translations.gettext(message), locale=self.locale)

    def gettext(self, message: str, /) -> LocalizedStr:
        """
        Like :py:meth:`gettext.gettext`.

        Arguments are identical to those of :py:meth:`gettext.gettext`.
        """
        return LocalizedStr(self._translations.gettext(message), locale=self.locale)

    def ngettext(
        self, message_singular: str, message_plural: str, n: int, /
    ) -> LocalizedStr:
        """
        Like :py:meth:`gettext.ngettext`.

        Arguments are identical to those of :py:meth:`gettext.ngettext`.
        """
        return LocalizedStr(
            self._translations.ngettext(message_singular, message_plural, n),
            locale=self.locale,
        )

    def pgettext(self, context: str, message: str, /) -> LocalizedStr:
        """
        Like :py:meth:`gettext.pgettext`.

        Arguments are identical to those of :py:meth:`gettext.pgettext`.
        """
        return LocalizedStr(
            self._translations.pgettext(context, message), locale=self.locale
        )

    def npgettext(
        self, context: str, message_singular: str, message_plural: str, n: int, /
    ) -> LocalizedStr:
        """
        Like :py:meth:`gettext.npgettext`.

        Arguments are identical to those of :py:meth:`gettext.npgettext`.
        """
        return LocalizedStr(
            self._translations.npgettext(context, message_singular, message_plural, n),
            locale=self.locale,
        )


default_localizer: Final[Localizer] = Localizer(
    default_locale, gettext_api.NullTranslations()
)


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
            from betty.gettext import UntranslatedLocale

            try:
                translations = self._translations.get(locale)
            except UntranslatedLocale:
                translations = gettext_api.NullTranslations()
            self._localizers[locale] = Localizer(locale, translations)
            return self._localizers[locale]
