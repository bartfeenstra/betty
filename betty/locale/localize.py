"""
Localizers provide a wide range of localization utilities through a single entry point.
"""

from __future__ import annotations

import gettext as gettext_api
from typing import TYPE_CHECKING, Final, final

from betty.locale import LocalizedStr, ResolvableLocale, default_locale, resolve_locale
from betty.typing import threadsafe

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from babel import Locale

    from betty.locale.localizable import ResolvableLocalizable
    from betty.locale.translation import TranslationRepository
    from betty.typing import Intersection as Intersection


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
            from betty.locale.translation import UntranslatedLocale

            try:
                translations = self._translations.get(locale)
            except UntranslatedLocale:
                translations = gettext_api.NullTranslations()
            self._localizers[locale] = Localizer(locale, translations)
            return self._localizers[locale]


def resolve_localized(
    localizable: ResolvableLocalizable, *, localizer: Localizer
) -> LocalizedStr:
    """
    Ensure that a localizable-like value is or is made to be localized.
    """
    from betty.locale.localizable import Localizable

    if isinstance(localizable, str):
        return LocalizedStr(localizable)
    if not isinstance(localizable, Localizable):
        from betty.locale.localizable.static import StaticTranslations

        localizable = StaticTranslations(localizable)
    return localizable.localize(localizer)
