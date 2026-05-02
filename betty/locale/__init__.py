"""
Provide the Locale API.
"""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import suppress
from functools import lru_cache
from typing import Any, cast, override

from babel import Locale
from babel.core import UnknownLocaleError

import betty.dirs

_LOCALE_DIRECTORY = betty.dirs.BUILTIN_ASSET_DIRECTORY / "locale"


DEFAULT_LOCALE = Locale("en", "US")
"""
Betty's default locale (US English).
"""

DEFAULT_LOCALE_TAG = "en-US"
"""
The `IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_ language tag for Betty's default locale (US English).
"""


type ResolvableLocale = Locale | str
"""
A locale or a locale identifier.
"""


def resolve_locale(locale: ResolvableLocale, /) -> Locale:
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


def from_language_tag(language_tag: str, /) -> Locale:
    """
    Get a locale from its `IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_ language tag.

    :raises betty.locale.InvalidLocale: Raised if the given identifier is not a valid locale.
    :raises betty.locale.LocaleNotFoundError: Raised if the given locale cannot be found.
    """
    locale = _from_language_tag(language_tag)
    if isinstance(locale, Locale):
        return locale
    raise locale


@lru_cache
def _from_language_tag(locale: str, /) -> Locale | Exception:
    try:
        return Locale.parse(locale, sep="-")
    except ValueError:
        from betty.locale.error import InvalidLocale

        return InvalidLocale(locale)
    except UnknownLocaleError:
        from betty.locale.error import UnknownLocale

        return UnknownLocale(locale)


def negotiate_locale(
    preferred_locales: Locale | Sequence[Locale],
    available_locales: Sequence[Locale],
    /,
) -> Locale | None:
    """
    Negotiate the preferred locale from a sequence.
    """
    preferred_locale_babel_identifiers = list(
        map(
            str,
            cast(Sequence[Locale], [preferred_locales])
            if isinstance(preferred_locales, Locale)
            else preferred_locales,
        )
    )
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

    def __init__(
        self, *args: Any, locale: ResolvableLocale | None = None, **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self._locale = None if locale is None else resolve_locale(locale)

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

    __slots__ = ("_locale",)

    @override
    def __new__(cls, string: str, *, locale: Locale | None = None):
        new = super().__new__(cls, string)
        new._locale = locale
        return new

    def __init__(self, string: str, *, locale: Locale | None = None):
        pass
