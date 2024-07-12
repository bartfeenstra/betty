"""
Provide the Locale API.
"""

from __future__ import annotations

from typing import Sequence, TypeAlias

from babel import Locale, negotiate_locale as babel_negotiate_locale
from langcodes import Language

from betty import fs

DEFAULT_LOCALE = "en-US"
UNDETERMINED_LOCALE = "und"

_LOCALE_DIRECTORY_PATH = fs.ASSETS_DIRECTORY_PATH / "locale"


class LocaleNotFoundError(RuntimeError):
    """
    Raise when a locale could not be found.
    """

    def __init__(self, locale: str) -> None:
        super().__init__(f'Cannot find locale "{locale}"')
        self.locale = locale


def to_babel_identifier(locale: Localey) -> str:
    """
    Convert a locale or locale metadata to a Babel locale identifier.
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


def to_locale(locale: Localey) -> str:
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


Localey: TypeAlias = str | Locale


def get_data(locale: Localey) -> Locale:
    """
    Get locale metadata.
    """
    if isinstance(locale, Locale):
        return locale
    try:
        return Locale.parse(to_babel_identifier(locale))
    except Exception as e:
        raise LocaleNotFoundError(locale) from e


def get_display_name(
    locale: Localey, display_locale: Localey | None = None
) -> str | None:
    """
    Return a locale's human-readable display name.
    """
    locale_data = get_data(locale)
    return locale_data.get_display_name(
        get_data(display_locale) if display_locale else locale_data
    )


def negotiate_locale(
    preferred_locales: Localey | Sequence[Localey], available_locales: Sequence[Localey]
) -> Locale | None:
    """
    Negotiate the preferred locale from a sequence.
    """
    if isinstance(preferred_locales, (str, Locale)):
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
