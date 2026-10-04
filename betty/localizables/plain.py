"""
Plain localizables.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final, override

from betty.locale import ResolvableLocale, resolve_locale
from betty.localizable import Localizable
from betty.localized import LocalizedStr
from betty.validators.str import is_str

if TYPE_CHECKING:
    from babel import Locale

    from betty.localizer import Localizer


@final
class Plain(Localizable):
    """
    Turns a plain string into a :py:class:`betty.localizable.Localizable` without any actual translations.
    """

    __slots__ = ("locale", "text")

    def __init__(self, text: str, locale: ResolvableLocale | None = None, /):
        self.text: Final[str] = is_str(text, min_len=1)
        """
        The plain text.
        """
        self.locale: Final[Locale | None] = (
            None if locale is None else resolve_locale(locale)
        )
        """
        The locale the text is in.
        """

    @override
    def localize(self, localizer: Localizer, /) -> LocalizedStr:
        return LocalizedStr(self.text, locale=self.locale)
