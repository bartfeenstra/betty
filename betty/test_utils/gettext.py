"""
Test utilities for :py:mod:`betty.gettext`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.gettext import Translations

if TYPE_CHECKING:
    from betty.localized import LocalizedStr


@final
class UntranslatedTranslations(Translations):
    """
    An untranslated translation set that always returns ``None``.
    """

    @override
    def gettext(self, message: str, /) -> LocalizedStr | None:
        return None

    @override
    def ngettext(
        self, message_singular: str, message_plural: str, n: int, /
    ) -> LocalizedStr | None:
        return None

    @override
    def pgettext(self, context: str, message: str, /) -> LocalizedStr | None:
        return None

    @override
    def npgettext(
        self, context: str, message_singular: str, message_plural: str, n: int, /
    ) -> LocalizedStr | None:
        return None
