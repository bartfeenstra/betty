"""
Provide the Locale API.
"""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import suppress
from typing import TYPE_CHECKING, Any, TypeAlias

from babel import Locale
from babel.core import UnknownLocaleError
from typing_extensions import override

import betty.dirs

if TYPE_CHECKING:
    from collections.abc import Sequence


_LOCALE_DIRECTORY_PATH = betty.dirs.ASSETS_DIRECTORY_PATH / "locale"


DEFAULT_LOCALE = Locale("en", "US")
"""
Betty's default locale (US English).
"""

DEFAULT_LOCALE_TAG = "en-US"
"""
The `IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_ language tag for Betty's default locale (US English).
"""


LocaleLike: TypeAlias = Locale | str
"""
A locale or a locale identifier.
"""


def ensure_locale(locale: LocaleLike, /) -> Locale:
    """
    Ensure that the given value is a locale.

    :raises betty.locale.InvalidLocale: Raised if the given identifier is not a valid locale.
    :raises betty.locale.LocaleNotFoundError: Raised if the given locale cannot be found.
    """
    if isinstance(locale, Locale):
        return locale
    return from_language_tag(locale)


def to_language_tag(locale: Locale | None, /) -> str:
    """
    Formats a locale as an `IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_ language tag.
    """
    if locale is None:
        return "und"
    return "-".join(
        part
        for part in [
            locale.language,
            locale.script,
            locale.territory,
        ]
        if part
    )


def from_language_tag(locale: str, /) -> Locale:
    """
    Get a locale from its `IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_ language tag.

    :raises betty.locale.InvalidLocale: Raised if the given identifier is not a valid locale.
    :raises betty.locale.LocaleNotFoundError: Raised if the given locale cannot be found.
    """
    try:
        return Locale.parse(locale, sep="-")
    except ValueError:
        from betty.locale.error import InvalidLocale

        raise InvalidLocale(locale) from None
    except UnknownLocaleError:
        from betty.locale.error import UnknownLocale

        raise UnknownLocale(locale) from None


def negotiate_locale(
    preferred_locales: Locale | Sequence[Locale],
    available_locales: Sequence[Locale],
    /,
) -> Locale | None:
    """
    Negotiate the preferred locale from a sequence.
    """
    if isinstance(preferred_locales, Locale):
        preferred_locales = [preferred_locales]
    preferred_locale_babel_identifiers = list(map(str, preferred_locales))
    available_locale_babel_identifiers = list(map(str, available_locales))
    negotiated_locale = Locale.negotiate(
        preferred_locale_babel_identifiers, available_locale_babel_identifiers
    )
    if negotiated_locale is not None:
        return negotiated_locale
    return Locale.negotiate(
        [
            (
                babel_identifier.split("_")[0]
                if "_" in babel_identifier
                else babel_identifier
            )
            for babel_identifier in preferred_locale_babel_identifiers
        ],
        available_locale_babel_identifiers,
    )


def plural_tags(locale: Locale) -> Sequence[str]:
    """
    Get a locale's plural tags.
    """
    tags = list(locale.plural_form.tags)
    if "other" not in tags:
        tags.append("other")
    return tags


class HasLocale:
    """
    A resource that has a locale, e.g. contains information in a specific locale.
    """

    def __init__(self, *args: Any, locale: LocaleLike | None = None, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._locale = None if locale is None else ensure_locale(locale)

    @property
    def locale(self) -> Locale | None:
        """
        The locale the data in this instance is in.
        """
        return self._locale


def negotiate_has_locales(
    preferred_locales: Locale | Sequence[Locale],
    has_locales: Sequence[HasLocale],
) -> HasLocale | None:
    """
    Negotiate the preferred value from a sequence.
    """
    negotiated_locale = negotiate_locale(
        preferred_locales,
        [
            has_locale.locale
            for has_locale in has_locales
            if has_locale.locale is not None
        ],
    )
    if negotiated_locale is not None:
        for has_locale in has_locales:
            if has_locale.locale == negotiated_locale:
                return has_locale
    for has_locale in has_locales:
        if has_locale.locale is None:
            return has_locale
    with suppress(IndexError):
        return has_locales[0]
    return None


class HasLocaleStr(HasLocale, str):
    """
    A string that has a locale.
    """

    __slots__ = "_locale"

    @override
    def __new__(cls, string: str, *, locale: Locale | None = None):
        new = super().__new__(cls, string)
        new._locale = locale
        return new

    def __init__(self, string: str, *, locale: Locale | None = None):
        pass
