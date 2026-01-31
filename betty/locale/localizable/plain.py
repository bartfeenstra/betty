"""
Plain localizables.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.locale import HasLocale, HasLocaleStr, ResolvableLocale, resolve_locale
from betty.locale.localizable import Localizable

if TYPE_CHECKING:
    from babel import Locale
    from ty_extensions import Intersection

    from betty.locale.localize import Localizer


@final
class Plain(Localizable):
    """
    Turns a plain string into a :py:class:`betty.locale.localizable.Localizable` without any actual translations.
    """

    def __init__(self, text: str, locale: ResolvableLocale | None = None, /):
        from betty.assertion import assert_str

        assert_str(minimum_length=1)(text)
        self._text = text
        self._locale = None if locale is None else resolve_locale(locale)

    @property
    def text(self) -> str:
        """
        The plain text.
        """
        return self._text

    @property
    def locale(self) -> Locale | None:
        """
        The locale the text is in.
        """
        return self._locale

    @override
    def localize(self, localizer: Localizer, /) -> Intersection[HasLocale, str]:
        return HasLocaleStr(self._text, locale=self._locale)
