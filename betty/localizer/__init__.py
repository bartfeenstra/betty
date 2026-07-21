"""
Localizers provide a wide range of localization utilities through a single entry point.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from betty.concurrent import Ledger, ThreadSafeLock
from betty.gettext import TranslationsRepository, Translator
from betty.locale import ResolvableLocale, default_locale, resolve_locale
from betty.localized import LocalizedStr
from betty.localizer.coordinate import CoordinateFormatter

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from babel import Locale

    from betty.localizable import ResolvableLocalizable


@final
class Localizer:
    """
    Localize a variety of data into a specific locale.
    """

    def __init__(
        self, locale: ResolvableLocale, /, *, translator: Translator | None = None
    ):
        self.locale: Final[Locale] = resolve_locale(locale)
        """
        The locale.
        """

        self.coordinate: Final[CoordinateFormatter] = CoordinateFormatter()
        """
        The geographic coordinate formatter.
        """

        self.translate: Final[Translator] = translator or Translator()
        """
        The string translator.
        """

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


default_localizer: Final[Localizer] = Localizer(default_locale)


@final
class LocalizerRepository:
    """
    Expose localizers.
    """

    def __init__(self, *, translations: TranslationsRepository | None = None):
        self._translations = translations
        self._ledger = Ledger(ThreadSafeLock())
        self._localizers: MutableMapping[Locale, Localizer] = {}

    async def get(self, locale: ResolvableLocale, /) -> Localizer:
        """
        Get the localizer for the given locale.
        """
        locale = resolve_locale(locale)
        localizer = self._localizers.get(locale, None)
        if localizer is not None:
            return localizer
        async with self._ledger.ledger(str(locale)):
            localizer = self._localizers.get(locale, None)
            if localizer is not None:
                return localizer
            localizer = self._localizers[locale] = Localizer(
                locale,
                translator=Translator(*await self._translations.get(locale))
                if self._translations
                else None,
            )
            return localizer
