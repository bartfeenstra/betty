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

    def _(self, message: str, /) -> str:
        """
        Like :py:meth:`gettext.gettext`.

        Arguments are identical to those of :py:meth:`gettext.gettext`.
        """
        return self._translations.gettext(message)

    def gettext(self, message: str, /) -> str:
        """
        Like :py:meth:`gettext.gettext`.

        Arguments are identical to those of :py:meth:`gettext.gettext`.
        """
        return self._translations.gettext(message)

    def ngettext(self, message_singular: str, message_plural: str, n: int, /) -> str:
        """
        Like :py:meth:`gettext.ngettext`.

        Arguments are identical to those of :py:meth:`gettext.ngettext`.
        """
        return self._translations.ngettext(message_singular, message_plural, n)

    def pgettext(self, context: str, message: str, /) -> str:
        """
        Like :py:meth:`gettext.pgettext`.

        Arguments are identical to those of :py:meth:`gettext.pgettext`.
        """
        return self._translations.pgettext(context, message)

    def npgettext(
        self, context: str, message_singular: str, message_plural: str, n: int, /
    ) -> str:
        """
        Like :py:meth:`gettext.npgettext`.

        Arguments are identical to those of :py:meth:`gettext.npgettext`.
        """
        return self._translations.npgettext(
            context, message_singular, message_plural, n
        )


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
