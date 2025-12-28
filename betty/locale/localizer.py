"""
Localizers provide a wide range of localization utilities through a single entry point.
"""

from __future__ import annotations

import gettext
from typing import TYPE_CHECKING, final

from betty.locale import DEFAULT_LOCALE, LocaleLike, ensure_locale
from betty.typing import threadsafe

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from babel import Locale

    from betty.locale.translation import TranslationRepository


@final
class Localizer:
    """
    Localize a variety of data into a specific locale.
    """

    def __init__(self, locale: LocaleLike, translations: gettext.NullTranslations, /):
        self._locale = ensure_locale(locale)
        self._translations = translations

    @property
    def locale(self) -> Locale:
        """
        The locale.
        """
        return self._locale

    @property
    def translations(self) -> gettext.NullTranslations:
        """
        The translations.
        """
        return self._translations


DEFAULT_LOCALIZER = Localizer(DEFAULT_LOCALE, gettext.NullTranslations())


@final
@threadsafe
class LocalizerRepository:
    """
    Exposes the available localizers.
    """

    def __init__(self, translations: TranslationRepository, /):
        self._translations = translations
        self._localizers: MutableMapping[Locale, Localizer] = {}

    def get(self, locale: LocaleLike, /) -> Localizer:
        """
        Get the localizer for the given locale.
        """
        locale = ensure_locale(locale)
        try:
            return self._localizers[locale]
        except KeyError:
            self._localizers[locale] = Localizer(locale, self._translations.get(locale))
            return self._localizers[locale]
