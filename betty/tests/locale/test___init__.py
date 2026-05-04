from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from babel import Locale

from betty.locale import (
    DEFAULT_LOCALE,
    Localized,
    LocalizedStr,
    ResolvableLocale,
    from_language_tag,
    negotiate_has_locales,
    negotiate_locale,
    plural_tags,
    resolve_locale,
    to_language_tag,
)
from betty.locale.error import InvalidLocale, UnknownLocale

if TYPE_CHECKING:
    from collections.abc import Sequence


@pytest.mark.parametrize(
    ("expected", "preferred_locale", "available_locales"),
    [
        (
            Locale("nl"),
            Locale("nl"),
            [Locale("nl")],
        ),
        (
            Locale("nl", "NL"),
            Locale("nl"),
            [Locale("nl", "NL")],
        ),
        (
            Locale("nl"),
            Locale("nl", "NL"),
            [Locale("nl")],
        ),
        (
            Locale("nl", "NL"),
            Locale("nl", "NL"),
            [Locale("nl"), Locale("nl", "BE"), Locale("nl", "NL")],
        ),
        (
            Locale("nl"),
            Locale("nl"),
            [Locale("nl"), Locale("en")],
        ),
        (
            Locale("nl"),
            Locale("nl"),
            [Locale("en"), Locale("nl")],
        ),
        (
            Locale("nl", "NL"),
            Locale("nl", "BE"),
            [Locale("nl", "NL")],
        ),
    ],
)
async def test_negotiate_locale(
    expected: Locale | None,
    preferred_locale: Locale,
    available_locales: Sequence[Locale],
) -> None:
    assert negotiate_locale(preferred_locale, available_locales) == expected


@pytest.mark.parametrize(
    ("expected", "locale"),
    [
        (Locale("nl"), "nl"),
        (Locale("nl", "NL"), "nl-NL"),
        (Locale("nl"), Locale("nl")),
    ],
)
def test_resolve_locale(expected: Locale, locale: ResolvableLocale) -> None:
    assert resolve_locale(locale) == expected


@pytest.mark.parametrize(
    ("expected", "locale"),
    [
        (Locale("nl"), "nl"),
        (Locale("nl", "NL"), "nl-NL"),
    ],
)
def test_from_language_tag(expected: Locale, locale: str) -> None:
    assert from_language_tag(locale) == expected


@pytest.mark.parametrize(
    "locale",
    [
        "",
        "nl_NL",
        "nl--NL",
    ],
)
def test_from_language_tag__with_invalid_locale(locale: str) -> None:
    with pytest.raises(InvalidLocale):
        from_language_tag(locale)


def test_from_language_tag__with_unknown_locale() -> None:
    with pytest.raises(UnknownLocale):
        from_language_tag("myfirstlocale")


@pytest.mark.parametrize(
    ("expected", "locale"),
    [
        ("und", None),
        ("nl", Locale("nl")),
        ("nl-NL", Locale("nl", "NL")),
    ],
)
def test_to_language_tag(expected: str, locale: Locale | None) -> None:
    assert to_language_tag(locale) == expected


def test_plural_tags() -> None:
    assert "other" in plural_tags(DEFAULT_LOCALE)


class TestLocalizedStr:
    def test_locale(self) -> None:
        string = "Hallo, wereld!"
        locale = Locale("nl")
        sut = LocalizedStr(string, locale=locale)
        assert sut == string
        assert sut.locale is locale


@pytest.mark.parametrize(
    ("expected", "preferred_locale", "has_locales"),
    [
        (Locale("nl"), Locale("nl"), [LocalizedStr("", locale=Locale("nl"))]),
        (
            Locale("nl", "NL"),
            Locale("nl"),
            [LocalizedStr("", locale=Locale("nl", "NL"))],
        ),
        (Locale("nl"), Locale("nl", "NL"), [LocalizedStr("", locale=Locale("nl"))]),
        (
            Locale("nl", "NL"),
            Locale("nl", "NL"),
            [
                LocalizedStr("", locale=Locale("nl")),
                LocalizedStr("", locale=Locale("nl", "BE")),
                LocalizedStr("", locale=Locale("nl", "NL")),
            ],
        ),
        (
            Locale("nl"),
            Locale("nl"),
            [
                LocalizedStr("", locale=Locale("nl")),
                LocalizedStr("", locale=Locale("en")),
            ],
        ),
        (
            Locale("nl"),
            Locale("nl"),
            [
                LocalizedStr("", locale=Locale("en")),
                LocalizedStr("", locale=Locale("nl")),
            ],
        ),
        (
            Locale("nl", "NL"),
            Locale("nl", "BE"),
            [LocalizedStr("", locale=Locale("nl", "NL"))],
        ),
        (None, Locale("nl"), []),
    ],
)
async def test_negotiate_has_locales__with_match_should_return_match(
    expected: Locale | None,
    preferred_locale: Locale,
    has_locales: Sequence[Localized],
) -> None:
    actual = negotiate_has_locales(preferred_locale, has_locales)
    if expected is None:
        assert actual is None
    else:
        assert actual is not None
        assert actual.locale == expected


async def test_negotiate_has_locales__without_match_should_return_default() -> None:
    has_locales = [
        LocalizedStr("", locale=Locale("nl")),
        LocalizedStr("", locale=Locale("en")),
        LocalizedStr("", locale=Locale("uk")),
    ]
    actual = negotiate_has_locales(Locale("de"), has_locales)
    assert actual is not None
    assert actual.locale == Locale("nl")
