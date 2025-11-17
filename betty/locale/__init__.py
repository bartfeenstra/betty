"""
Provide the Locale API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias, final

from babel import Locale
from babel import negotiate_locale as babel_negotiate_locale
from babel.core import UnknownLocaleError
from langcodes import Language

import betty
import betty.dirs
from betty.classtools import Singleton
from betty.json.schema import String

if TYPE_CHECKING:
    from collections.abc import Sequence

_LOCALE_DIRECTORY_PATH = betty.dirs.ASSETS_DIRECTORY_PATH / "locale"

NO_LINGUISTIC_CONTENT = "zxx"
UNDETERMINED_LOCALE = "und"
UNCODED_LOCALE = "mis"
MULTIPLE_LOCALES = "mul"
SPECIAL_LOCALES = (
    NO_LINGUISTIC_CONTENT,
    UNDETERMINED_LOCALE,
    UNCODED_LOCALE,
    MULTIPLE_LOCALES,
)

DEFAULT_LOCALE = "en-US"


def merge_locales(*locales: str) -> str:
    """
    Merge locales into a single locale.
    """
    unique_locales = set(locales)
    if len(unique_locales) == 0:
        return NO_LINGUISTIC_CONTENT
    if len(unique_locales) == 1:
        return next(iter(unique_locales))
    # Strip locales without linguistic content.
    if NO_LINGUISTIC_CONTENT in unique_locales:
        return merge_locales(*(unique_locales - {NO_LINGUISTIC_CONTENT}))
    return MULTIPLE_LOCALES


def to_babel_identifier(locale: LocaleLike) -> str:
    """
    Convert a locale or locale metadata to a Babel locale identifier.

    :raises ValueError:
    """
    if isinstance(locale, Locale):
        return str(locale)
    language_data = Language.get(locale)
    return "_".join(
        part
        for part in [
            language_data.language,
            language_data.script,
            language_data.territory,
        ]
        if part
    )


def to_locale(locale: LocaleLike) -> str:
    """
    Ensure that a locale or locale metadata is a locale.
    """
    if isinstance(locale, str):
        return locale
    return "-".join(
        part
        for part in [
            locale.language,
            locale.script,
            locale.territory,
        ]
        if part
    )


LocaleLike: TypeAlias = str | Locale


def get_data(locale: LocaleLike) -> Locale:
    """
    Get locale metadata.

    :raises betty.locale.InvalidLocale: Raised if the given identifier is not a valid locale.
    :raises betty.locale.LocaleNotFoundError: Raised if the given locale cannot be found.
    """
    if isinstance(locale, Locale):
        return locale
    try:
        return Locale.parse(to_babel_identifier(locale))
    except ValueError:
        from betty.locale.error import InvalidLocale

        raise InvalidLocale(locale) from None
    except UnknownLocaleError:
        from betty.locale.error import UnsupportedLocale

        raise UnsupportedLocale(locale) from None


def get_display_name(
    locale: LocaleLike, display_locale: LocaleLike | None = None
) -> str | None:
    """
    Return a locale's human-readable display name.
    """
    locale_data = get_data(locale)
    return locale_data.get_display_name(
        get_data(display_locale) if display_locale else locale_data
    )


def negotiate_locale(
    preferred_locales: LocaleLike | Sequence[LocaleLike],
    available_locales: Sequence[LocaleLike],
) -> Locale | None:
    """
    Negotiate the preferred locale from a sequence.
    """
    if isinstance(preferred_locales, str | Locale):
        preferred_locales = [preferred_locales]
    return _negotiate_locale(
        [to_babel_identifier(locale) for locale in preferred_locales],
        {to_babel_identifier(locale) for locale in available_locales},
        False,
    )


def _negotiate_locale(
    preferred_locale_babel_identifiers: Sequence[str],
    available_locale_babel_identifiers: set[str],
    root: bool,
) -> Locale | None:
    negotiated_locale = babel_negotiate_locale(
        preferred_locale_babel_identifiers, available_locale_babel_identifiers
    )
    if negotiated_locale is not None:
        return Locale.parse(negotiated_locale)
    if not root:
        return _negotiate_locale(
            [
                (
                    babel_identifier.split("_")[0]
                    if "_" in babel_identifier
                    else babel_identifier
                )
                for babel_identifier in preferred_locale_babel_identifiers
            ],
            available_locale_babel_identifiers,
            True,
        )
    return None


@final
class LocaleSchema(Singleton, String):
    """
    The JSON Schema for locales.
    """

    def __init__(self):
        super().__init__(
            def_name="locale",
            title="Locale",
            description="A BCP 47 locale identifier (https://www.ietf.org/rfc/bcp/bcp47.txt).",
        )
